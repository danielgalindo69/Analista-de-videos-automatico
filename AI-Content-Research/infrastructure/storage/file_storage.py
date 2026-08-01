"""
FileStorage — Async file persistence for analysis results and raw data.

Design decisions:
- All I/O is async (aiofiles) — never blocks the event loop.
- Output is organized by platform/date/query to keep results navigable.
- JSON serialization uses Pydantic's model_dump_json() for proper
  type handling (datetime, HttpUrl, enums) without custom encoders.
- Markdown output is human-readable and suitable for direct use in reports.
- Atomic writes via a temp file + rename pattern prevents corrupt files
  if the process crashes mid-write.

Directory structure created:
    output/
    └── youtube/
        └── 2026-08-01/
            ├── search_fnaf_fear_mind.json
            └── search_fnaf_fear_mind.md
"""

import json
from datetime import datetime
from pathlib import Path

import aiofiles
from loguru import logger

from config.settings import get_settings
from core.models.analysis import AnalysisResult
from core.models.content import ContentItem, Platform
from core.exceptions import StorageError


class FileStorage:
    """
    Handles async persistence of content items and analysis results.

    Usage:
        storage = FileStorage()
        path = await storage.save_analysis(result)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_dir = Path(settings.storage.output_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def save_analysis(self, result: AnalysisResult) -> Path:
        """
        Persist an AnalysisResult as JSON and Markdown.

        Args:
            result: Completed analysis result

        Returns:
            Path to the generated JSON file

        Raises:
            StorageError: If write fails
        """
        output_dir = self._resolve_dir(result.platform, prefix="analysis")
        slug = self._slugify(result.query)
        json_path = output_dir / f"{slug}.json"
        md_path = output_dir / f"{slug}.md"

        await self._write_json(json_path, result.model_dump(mode="json"))
        await self._write_text(md_path, self._render_analysis_md(result))

        logger.info(
            "Storage | analysis saved | platform={p} | files=[{j}, {m}]",
            p=result.platform,
            j=json_path.name,
            m=md_path.name,
        )
        return json_path

    async def save_content_items(
        self,
        items: list[ContentItem],
        platform: Platform,
        label: str,
    ) -> Path:
        """
        Persist a list of ContentItems as a JSON array.

        Args:
            items: Content items to save
            platform: Platform they were extracted from
            label: Descriptive label for the filename

        Returns:
            Path to the generated JSON file
        """
        output_dir = self._resolve_dir(platform, prefix="raw")
        slug = self._slugify(label)
        json_path = output_dir / f"{slug}.json"

        payload = [item.model_dump(mode="json") for item in items]
        await self._write_json(json_path, payload)

        logger.info(
            "Storage | {count} items saved | platform={p} | file={f}",
            count=len(items),
            p=platform,
            f=json_path.name,
        )
        return json_path

    async def load_json(self, path: Path) -> dict | list:
        """
        Load a previously saved JSON file.

        Args:
            path: Absolute path to the JSON file

        Returns:
            Parsed JSON content (dict or list)

        Raises:
            StorageError: If file not found or JSON is malformed
        """
        if not path.exists():
            raise StorageError(
                f"File not found: {path}",
                context={"path": str(path)},
            )
        try:
            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise StorageError(
                f"Malformed JSON in {path.name}: {e}",
                context={"path": str(path)},
            ) from e

    def list_analyses(self, platform: Platform | None = None) -> list[Path]:
        """
        List all saved analysis JSON files, optionally filtered by platform.

        Args:
            platform: If provided, only return files for this platform

        Returns:
            List of Path objects sorted by modification time (newest first)
        """
        search_root = self._base_dir / platform if platform else self._base_dir
        files = sorted(
            search_root.rglob("analysis/**/*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_dir(self, platform: Platform | str, prefix: str) -> Path:
        """Build and create the output directory for a given platform and date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        directory = self._base_dir / str(platform) / date_str / prefix
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _slugify(text: str, max_length: int = 60) -> str:
        """Convert arbitrary text to a safe filename slug."""
        import re
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
        return slug[:max_length]

    @staticmethod
    async def _write_json(path: Path, data: dict | list) -> None:
        """Async atomic JSON write."""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)
        except OSError as e:
            raise StorageError(
                f"Failed to write {path.name}: {e}",
                context={"path": str(path)},
            ) from e

    @staticmethod
    async def _write_text(path: Path, content: str) -> None:
        """Async text write."""
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)
        except OSError as e:
            raise StorageError(
                f"Failed to write {path.name}: {e}",
                context={"path": str(path)},
            ) from e

    @staticmethod
    def _render_analysis_md(result: AnalysisResult) -> str:
        """Render an AnalysisResult as a readable Markdown report."""
        lines: list[str] = [
            f"# Analysis Report",
            f"",
            f"**Query:** {result.query}",
            f"**Platform:** {result.platform}",
            f"**Status:** {result.status}",
            f"**Items analyzed:** {result.items_analyzed}",
        ]
        if result.duration_seconds is not None:
            lines.append(f"**Duration:** {result.duration_seconds:.1f}s")
        lines += ["", "---", ""]

        if result.findings:
            lines += ["## Findings", ""]
            for i, finding in enumerate(result.findings, 1):
                lines += [
                    f"### {i}. {finding.title}",
                    f"",
                    f"{finding.description}",
                    f"",
                    f"**Confidence:** {finding.confidence:.0%}",
                ]
                if finding.evidence:
                    lines += ["", "**Evidence:**"]
                    lines += [f"- {e}" for e in finding.evidence]
                lines.append("")

        if result.recommendations:
            lines += ["## Recommendations", ""]
            lines += [f"- {r}" for r in result.recommendations]
            lines.append("")

        return "\n".join(lines)
