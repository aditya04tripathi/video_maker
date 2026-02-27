"""
Celery task: Reel Upload Pipeline.

Extracts the core business logic from scripts/scheduled_reel_post.py into a
Celery task that can be scheduled via Beat or invoked on demand.

The task performs:
1. AI quote generation via Groq
2. Video rendering via MoviePy
3. Upload to MinIO (S3-compatible storage)
4. Instagram Graph API container creation + publish
"""

import os
import time

from celery import Task
from celery.utils.log import get_task_logger

from src.celery_app import celery_app
from src.config.settings import settings
from src.core.logger import Log
from src.core.video_generator import add_text_to_video
from src.services.groq_client import GroqQuoteGenerator
from src.core.seo import SEOManager
from src.services.storage import MinIOClient
from src.services.instagram import InstagramGraphClient


logger = get_task_logger(__name__)


def _generate_video(quote: str) -> str:
    """
    Generate a new video with the given quote overlaid on the template.

    Returns:
        The reminder body text for caption composition.

    Raises:
        RuntimeError: If video generation fails.
    """
    Log.info("Starting video generation pipeline...")

    reminder_body = (
        "You are my everything. "
        "I'm still falling in love with you "
        "and won't stop loving you, ilysm."
    )

    success = add_text_to_video(
        input_video_path=settings.template_path,
        output_video_path=settings.output_path,
        quote_text=quote,
        font_size=55,
        color="white",
        audio_path=settings.audio_track_path,
    )

    if not success:
        raise RuntimeError("Video generation failed during rendering")

    Log.info("Video generation completed successfully.")
    return reminder_body


def _log_video_diagnostics() -> None:
    """Log video file dimensions, duration, and aspect ratio for debugging."""
    try:
        from moviepy.editor import VideoFileClip

        with VideoFileClip(str(settings.output_path)) as clip:
            Log.info(
                f"Video Diagnostics: Duration={clip.duration}s, "
                f"Resolution={clip.w}x{clip.h}, FPS={clip.fps}"
            )
            if clip.duration < 3:
                Log.warning(
                    "Video duration is less than 3 seconds. Instagram might reject it."
                )
            aspect = clip.w / clip.h
            if abs(aspect - 9 / 16) > 0.01:
                Log.warning(
                    f"Video aspect ratio ({aspect:.2f}) is not 9:16. "
                    "Instagram might reject it."
                )
    except Exception as exc:
        Log.warning(f"Could not log video diagnostics: {exc}")


def _upload_to_instagram(caption: str) -> str:
    """
    Upload the rendered video to Instagram via URL-based or binary fallback.

    Returns:
        The permalink of the published reel.

    Raises:
        RuntimeError: If both upload methods and publishing fail.
    """
    Log.info("Initializing Instagram Graph Client...")
    ig_client = InstagramGraphClient()
    storage_client = MinIOClient()
    container_id = None
    timestamp = int(time.time())

    # --- Attempt URL-based upload via MinIO presigned URL ---
    try:
        file_name = f"reel_{timestamp}.mp4"
        Log.info(f"Uploading video to MinIO for public URL: {file_name}")

        if storage_client.upload_file(str(settings.output_path), file_name):
            video_url = storage_client.get_presigned_url(file_name)

            # Upload cover image if it exists
            cover_url = None
            thumbnail_local = f"{settings.output_path}.jpg"
            if os.path.exists(thumbnail_local):
                thumbnail_name = f"cover_{timestamp}.jpg"
                if storage_client.upload_file(thumbnail_local, thumbnail_name):
                    cover_url = storage_client.get_presigned_url(thumbnail_name)

            Log.info("Creating Instagram media container via URL...")
            container_id = ig_client.upload_reel(
                video_url, caption, cover_url=cover_url
            )

            if container_id:
                Log.success(f"Container created successfully: {container_id}")
    except Exception as exc:
        Log.error(f"URL-based upload preparation failed: {exc}")

    # --- Fallback to binary upload ---
    if not container_id:
        Log.warning(
            "URL upload failed or skipped. Attempting binary upload fallback..."
        )
        container_id = ig_client.upload_reel_binary(
            str(settings.output_path),
            caption,
            cover_url=None,
        )

    if not container_id:
        raise RuntimeError("Failed to create Instagram container via any method")

    # --- Wait for processing and publish ---
    Log.info("Waiting for media processing and publishing...")
    permalink = ig_client.wait_and_publish(container_id)

    if not permalink:
        raise RuntimeError("Failed to publish reel after processing")

    return permalink


@celery_app.task(
    bind=True,
    name="src.tasks.reel_upload.upload_reel",
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def upload_reel(self: Task) -> dict:
    """
    Full reel upload pipeline as a Celery task.

    Pipeline:
        1. Generate romantic quote via Groq
        2. Render video with quote overlay
        3. Build SEO-optimized caption
        4. Upload to Instagram (URL-based → binary fallback)
        5. Publish and return permalink

    Returns:
        dict with task result metadata.

    Retries:
        Up to 2 retries with 60s delay on transient failures.
    """
    task_id = self.request.id
    Log.info("=== Starting Scheduled Reel Post Job ===")
    Log.info(f"Task ID: {task_id}")

    try:
        # 1. Generate quote
        Log.info("Requesting romantic quote and engaging body from Groq...")
        try:
            generator = GroqQuoteGenerator()
            groq_quote = generator.generate_quote()
            engaging_caption = generator.generate_engaging_caption(groq_quote)
        except Exception as exc:
            Log.warning(f"Groq generation failed: {exc}. Using fallback content.")
            groq_quote = "Every day I love you more than yesterday."
            engaging_caption = None

        # 2. Render video
        reminder_text = _generate_video(groq_quote)
        _log_video_diagnostics()

        # 3. Build caption
        caption = SEOManager.generate_caption(
            keywords=settings.keywords,
            hashtags=settings.hashtags,
            quote=groq_quote,
            reminder_body=reminder_text,
            engaging_body=engaging_caption,
        )

        # 4. Upload and publish
        permalink = _upload_to_instagram(caption)

        Log.info(f"SUCCESS: Reel published! Permalink: {permalink}")

        return {
            "status": "published",
            "permalink": permalink,
            "quote": groq_quote,
            "task_id": task_id,
        }

    except Exception as exc:
        Log.error(f"Job Failed: {exc}")

        # Retry on transient failures
        if self.request.retries < self.max_retries:
            Log.warning(
                f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})..."
            )
            raise self.retry(exc=exc)

        # Final failure
        return {
            "status": "failed",
            "error": str(exc),
            "task_id": task_id,
        }
