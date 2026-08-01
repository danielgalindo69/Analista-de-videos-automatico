"""
PromptRegistry — Loads and caches prompt templates from .md files.

Design decisions:
- Templates are .md files, not Python strings. This separates prompt content
  from code, making them editable without touching Python files and
  trackable in git as plain text diffs.
- lru_cache on _load_template() means each file is read from disk exactly once
  per process — zero repeated I/O.
- format_map() is used instead of str.format() to avoid KeyErrors when the
  template contains curly braces not intended as variables.
- The registry resolves paths relative to this file's location, so it works
  regardless of the working directory the process is started from.

Directory layout expected:
    prompts/
    ├── registry.py          ← this file
    └── templates/
        ├── system_base.md
        ├── youtube/
        │   ├── extract_metadata.md
        │   └── analyze_trends.md
        └── ...

Usage:
    from prompts.registry import PromptRegistry
    registry = PromptRegistry()

    # Load raw template
    system_prompt = registry.get("system_base")

    # Load with variable substitution
    prompt = registry.get("youtube/extract_metadata", title="FNAF Fear's Mind")
"""

from functools import lru_cache
from pathlib import Path

from loguru import logger

from core.exceptions import PromptNotFoundError


_TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptRegistry:
    """
    Loads, caches, and renders prompt templates from the templates/ directory.
    Thread-safe: lru_cache is used for caching, reads are stateless.
    """

    def get(self, name: str, **variables: str) -> str:
        """
        Load a prompt template by name and optionally render variables.

        Args:
            name: Template name relative to templates/.
                  Use forward slashes for subdirectories.
                  Omit the .md extension.
                  Examples: "system_base", "youtube/extract_metadata"
            **variables: Key-value pairs to substitute in the template.
                         Uses str.format_map() — only replaces {key} patterns
                         that match provided variables.

        Returns:
            Rendered prompt string

        Raises:
            PromptNotFoundError: If the template file does not exist
        """
        raw = self._load_template(name)
        if not variables:
            return raw
        return self._render(raw, variables)

    def list_templates(self) -> list[str]:
        """
        Return all available template names relative to templates/.
        Useful for CLI diagnostics.
        """
        templates = []
        for path in _TEMPLATES_DIR.rglob("*.md"):
            # Convert to forward-slash name without extension
            relative = path.relative_to(_TEMPLATES_DIR)
            name = str(relative.with_suffix("")).replace("\\", "/")
            templates.append(name)
        return sorted(templates)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    @lru_cache(maxsize=128)
    def _load_template(name: str) -> str:
        """
        Read and cache a template file from disk.
        Called once per unique name per process lifetime.
        """
        path = _TEMPLATES_DIR / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(prompt_name=name)
        content = path.read_text(encoding="utf-8").strip()
        logger.debug("PromptRegistry | loaded template '{name}'", name=name)
        return content

    @staticmethod
    def _render(template: str, variables: dict[str, str]) -> str:
        """
        Substitute variables into the template using format_map.
        Missing keys in the template are left as-is (no KeyError).
        """
        class _SafeMap(dict):
            def __missing__(self, key: str) -> str:
                return "{" + key + "}"

        return template.format_map(_SafeMap(variables))
