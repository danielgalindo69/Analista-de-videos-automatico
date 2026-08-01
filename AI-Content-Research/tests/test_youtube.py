"""
Unit and integration tests for YouTube Researcher module (Phase 2).
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
from platforms.youtube.models import YouTubeVideo, YouTubeChannel
from platforms.youtube.extractors.search_extractor import parse_view_count, parse_duration_seconds
from platforms.youtube.youtube_platform import YouTubePlatform
from analysis.youtube.title_analyzer import YouTubeTitleAnalyzer
from analysis.youtube.trend_analyzer import YouTubeTrendAnalyzer
from core.models import Platform, ContentType, AnalysisRequest, TaskType


def test_view_count_parsing():
    assert parse_view_count("1.5M views") == 1_500_000
    assert parse_view_count("450K vistas") == 450_000
    assert parse_view_count("1,234 views") == 1234
    assert parse_view_count("10B views") == 10_000_000_000
    print("[OK] view_count_parsing passed")


def test_duration_parsing():
    assert parse_duration_seconds("10:45") == 645
    assert parse_duration_seconds("1:02:15") == 3735
    assert parse_duration_seconds("0:45") == 45
    print("[OK] duration_parsing passed")


def test_youtube_video_model():
    video = YouTubeVideo(
        id="test_id_123",
        platform=Platform.YOUTUBE,
        content_type=ContentType.VIDEO,
        title="Five Nights at Freddy's Secret Lore Explained",
        url="https://www.youtube.com/watch?v=test_id_123",
        author_name="Game Lore Channel",
        metadata={
            "view_count": 2_500_000,
            "like_count": 150_000,
            "duration_seconds": 1200,
            "duration_text": "20:00",
            "is_short": False,
            "tags": ["fnaf", "horror", "lore"],
        },
    )
    assert video.id == "test_id_123"
    assert video.view_count == 2_500_000
    assert video.like_count == 150_000
    assert video.duration_seconds == 1200
    assert video.is_short is False
    assert "fnaf" in video.tags
    print("[OK] youtube_video_model passed")


def test_youtube_platform_init():
    platform = YouTubePlatform()
    assert platform.platform_name == "YouTube"
    print("[OK] youtube_platform_init passed")


if __name__ == "__main__":
    test_view_count_parsing()
    test_duration_parsing()
    test_youtube_video_model()
    test_youtube_platform_init()
    print("\nALL PHASE 2 UNIT TESTS PASSED SUCCESSFULLY!")
