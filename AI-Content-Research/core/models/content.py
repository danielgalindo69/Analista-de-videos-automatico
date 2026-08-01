"""
Content data models.

ContentItem is the universal unit of content across all platforms.
Platform-specific fields live in the `metadata` dict to avoid
creating a separate model per platform at this stage.
"""

from datetime import datetime
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass
from pydantic import BaseModel, Field, HttpUrl


class Platform(StrEnum):
    """Supported platforms. Extend as new platform modules are added."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITCH = "twitch"
    KICK = "kick"
    STEAM = "steam"
    REDDIT = "reddit"
    X = "x"
    GOOGLE_TRENDS = "google_trends"
    GITHUB = "github"
    UNKNOWN = "unknown"


class ContentType(StrEnum):
    VIDEO = "video"
    POST = "post"
    CHANNEL = "channel"
    PROFILE = "profile"
    COMMENT = "comment"
    TREND = "trend"
    GAME = "game"
    REPOSITORY = "repository"


class ContentItem(BaseModel):
    """
    Universal content unit shared across all platforms.

    Design decision: `metadata` is an open dict for platform-specific fields
    (e.g., view_count, like_count, duration) rather than forcing every platform
    to fit a rigid schema. Platform extractors populate metadata; analyzers
    read from it using typed accessor methods in their own models.
    """

    id: str = Field(description="Platform-native unique identifier")
    platform: Platform
    content_type: ContentType
    title: str | None = None
    url: HttpUrl | None = None
    author_id: str | None = None
    author_name: str | None = None
    published_at: datetime | None = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    raw_text: str | None = Field(default=None, description="Full extracted text content")
    metadata: dict = Field(
        default_factory=dict,
        description="Platform-specific fields (views, likes, duration, etc.)",
    )

    def get_meta(self, key: str, default=None):
        """Safe accessor for metadata fields."""
        return self.metadata.get(key, default)
