from pydantic import Field
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    s3_endpoint_url: Optional[str] = Field(alias="S3_ENDPOINT_URL", default=None)
    s3_public_url: Optional[str] = Field(alias="S3_PUBLIC_URL", default=None)
    s3_access_key: str = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(alias="S3_SECRET_KEY")
    s3_bucket_name: str = Field(alias="S3_BUCKET_NAME")
    s3_region: str = Field(alias="S3_REGION", default="us-east-1")

    ig_access_token: str = Field(alias="IG_ACCESS_TOKEN")
    ig_user_id: str = Field(alias="IG_USER_ID")
    fb_page_id: Optional[str] = Field(alias="FB_PAGE_ID", default=None)
    ig_api_version: str = Field(alias="IG_API_VERSION", default="v25.0")
    ig_app_id: Optional[str] = Field(alias="IG_APP_ID", default=None)

    groq_api_key: str = Field(alias="GROQ_API_KEY", default="")

    base_dir: Path = Path(__file__).parent.parent.parent
    src_dir: Path = base_dir / "src"

    template_path: Path = src_dir / "insta_template.mp4"
    output_path: Path = src_dir / "output_video.mp4"
    audio_track_path: Path = src_dir / "core" / "audio_track.mp4"

    hashtags: list[str] = [
        "#ForYou",
        "#Fyp",
        "#Explore",
        "#Reach",
        "#Reelsgrowth",
        "#Boostyourreel",
        "#Trendingnow",
        "#ViralReels",
    ]
    keywords: list[str] = [
        "romantic reminders",
        "intentional relationships",
        "daily love quotes",
        "relationship habits",
        "soulmate bond",
        "healthy love",
        "marriage goals",
        "deep connection",
        "intentional love",
        "relationship growth",
        "romantic aesthetic",
        "daily devotion",
        "partnership goals",
        "love languages",
        "intentional dating",
        "heartfelt messages",
        "romantic mindfulness",
        "love story",
        "soulmate manifestation",
        "couple growth",
    ]


settings = Settings()
