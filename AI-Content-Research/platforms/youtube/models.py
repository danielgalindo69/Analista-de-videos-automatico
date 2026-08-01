"""
YouTube-specific data models.

Design decision: YouTubeVideo inherits from ContentItem to maintain compatibility
with all core interfaces (BasePlatform, BaseAnalyzer, Storage).
YouTube-specific fields (views, likes, duration, tags) are stored in `metadata`
and exposed via typed property getters for clean developer experience.
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from core.models.content import ContentItem, ContentType, Platform


class YouTubeVideo(ContentItem):
    """
    Represents a single YouTube video with typed accessors for YouTube metadata.
    """

    def __init__(self, **data) -> None:
        data.setdefault("platform", Platform.YOUTUBE)
        data.setdefault("content_type", ContentType.VIDEO)
        super().__init__(**data)

    @property
    def view_count(self) -> int:
        return self.metadata.get("view_count", 0)

    @property
    def like_count(self) -> int | None:
        return self.metadata.get("like_count")

    @property
    def duration_seconds(self) -> int:
        return self.metadata.get("duration_seconds", 0)

    @property
    def is_short(self) -> bool:
        return self.metadata.get("is_short", False)

    @property
    def tags(self) -> list[str]:
        return self.metadata.get("tags", [])

    @property
    def comment_count(self) -> int | None:
        return self.metadata.get("comment_count")


class YouTubeChannel(BaseModel):
    """
    Represents a YouTube Channel and its aggregate statistics.
    """

    channel_id: str
    name: str
    url: HttpUrl
    subscribers_count: int = 0
    subscribers_text: str = ""
    video_count: int = 0
    description: str = ""
    avatar_url: str | None = None
    banner_url: str | None = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    recent_videos: list[YouTubeVideo] = Field(default_factory=list)


class YouTubeSearchFilter(BaseModel):
    """
    Filters for YouTube search queries.
    """

    query: str
    max_results: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="relevance", description="relevance | date | view_count | rating")
    upload_date: str | None = Field(default=None, description="hour | today | week | month | year")
