import sys
import os
import time
import argparse


# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.core.logger import Log
from src.core.video_generator import add_text_to_video
from src.services.groq_client import GroqQuoteGenerator
from src.core.seo import SEOManager
from src.services.storage import MinIOClient
from src.services.instagram import InstagramGraphClient


def generate_video(quote):
    """Generate a new video with dynamic quote only"""
    Log.info("Starting video generation pipeline...")

    # 1. Prepare Reminder Text for Caption
    # We offload this from the video to the caption for better SEO
    reminder_body = (
        "You are my everything. "
        "I'm still falling in love with you "
        "and won't stop loving you, ilysm."
    )

    # 2. Add centered quote to template
    success = add_text_to_video(
        input_video_path=settings.template_path,
        output_video_path=settings.output_path,
        quote_text=quote,
        font_size=55,
        color="white",
        audio_path=settings.audio_track_path,
    )

    if not success:
        raise Exception("Video generation failed")

    Log.info("Video generation completed successfully.")
    return reminder_body


def main():
    parser = argparse.ArgumentParser(description="Automated Instagram Reel Publisher")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run video generation only, skip upload/publish",
    )
    args = parser.parse_args()

    try:
        Log.info("=== Starting Scheduled Reel Post Job ===")
        if args.dry_run:
            Log.info("DRY RUN MODE: Upload and publishing will be skipped.")

        # 1. Generate Romantic Quote and engaging body via Groq
        Log.info("Requesting romantic quote and engaging body from Groq...")
        try:
            generator = GroqQuoteGenerator()
            groq_quote = generator.generate_quote()
            engaging_caption = generator.generate_engaging_caption(groq_quote)
        except Exception as e:
            Log.warning(f"Groq generation failed: {e}. Using fallback content.")
            groq_quote = "Every day I love you more than yesterday."
            engaging_caption = None

        # 2. Generate Video with dynamic quote
        reminder_text = generate_video(groq_quote)

        # Log video diagnostics
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(str(settings.output_path)) as clip:
                Log.info(f"Video Diagnostics: Duration={clip.duration}s, Resolution={clip.w}x{clip.h}, FPS={clip.fps}")
                if clip.duration < 3:
                    Log.warning("Video duration is less than 3 seconds. Instagram might reject it.")
                if clip.w / clip.h != 9/16 and abs(clip.w / clip.h - 9/16) > 0.01:
                    Log.warning(f"Video aspect ratio ({clip.w/clip.h:.2f}) is not 9:16. Instagram might reject it.")
        except Exception as de:
            Log.warning(f"Could not log video diagnostics: {de}")

        # 3. Prepare Metadata
        keywords = settings.keywords
        hashtags = settings.hashtags
        caption = SEOManager.generate_caption(
            keywords=keywords,
            hashtags=hashtags,
            quote=groq_quote,
            reminder_body=reminder_text,
            engaging_body=engaging_caption,
        )

        if args.dry_run:
            Log.info("DRY RUN: Metadata generated.")
            Log.info(f"Caption: {caption[:100]}...")
            Log.info("DRY RUN COMPLETED SUCCESSFULLY.")
            return

        # 4. Upload to Instagram
        Log.info("Initializing Instagram Graph Client...")
        ig_client = InstagramGraphClient()

        # Prepare for upload (Hosting on MinIO for URL-based upload)
        # URL-based upload is more stable for larger files and matches direct_reel_uploader behavior
        container_id = None
        storage_client = MinIOClient()
        
        try:
            timestamp = int(time.time())
            
            # Upload Video
            file_name = f"reel_{timestamp}.mp4"
            Log.info(f"Uploading video to MinIO for public URL: {file_name}")
            if storage_client.upload_file(str(settings.output_path), file_name):
                video_url = storage_client.get_presigned_url(file_name)
                
                # Upload Cover if exists
                cover_url = None
                thumbnail_local = f"{settings.output_path}.jpg"
                if os.path.exists(thumbnail_local):
                    thumbnail_name = f"cover_{timestamp}.jpg"
                    if storage_client.upload_file(thumbnail_local, thumbnail_name):
                        cover_url = storage_client.get_presigned_url(thumbnail_name)
                
                # Create Container via URL
                Log.info("Creating Instagram media container via URL...")
                container_id = ig_client.upload_reel(video_url, caption, cover_url=cover_url)
                
                if container_id:
                    Log.success(f"Container created successfully: {container_id}")
            
        except Exception as e:
            Log.error(f"URL-based upload preparation failed: {e}")

        # Fallback to Binary Upload only if URL-based fails
        if not container_id:
            Log.warning("URL upload failed or skipped. Attempting Binary Upload fallback...")
            container_id = ig_client.upload_reel_binary(
                str(settings.output_path),
                caption,
                cover_url=None, # Binary upload usually doesn't handle cover URLs as well in this client
            )

        if not container_id:
            raise Exception("Failed to create Instagram container via any method")

        Log.info("Waiting for media processing and publishing...")
        permalink = ig_client.wait_and_publish(container_id)

        if permalink:
            Log.info(f"SUCCESS: Reel published! Permalink: {permalink}")
        else:
            raise Exception("Failed to publish Reel after processing")

    except Exception as e:
        Log.error(f"Job Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
