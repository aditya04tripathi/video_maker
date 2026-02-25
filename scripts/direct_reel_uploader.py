import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.core.logger import Log
from src.services.instagram import InstagramGraphClient

# ==========================================
# CONFIGURATION - EDIT THESE VALUES
# ==========================================
VIDEO_URL = "https://loremipsum.video/vt/powerpoint-1.mp4"
CAPTION = """--- TEST UPLOAD ---"""
COVER_URL = None  # Set to a public URL if needed, else None
DRY_RUN = False    # Set to False to actually publish
# ==========================================

def main():
    try:
        Log.info("=== Starting Direct Reel Upload Job ===")
        Log.info(f"Video URL: {VIDEO_URL}")
        Log.info(f"Caption: {CAPTION[:50]}...")
        
        if COVER_URL:
            Log.info(f"Cover URL: {COVER_URL}")

        if DRY_RUN:
            Log.info("DRY RUN MODE: Skipping actual upload.")
            Log.info("DRY RUN COMPLETED SUCCESSFULLY.")
            return

        # 1. Initialize Instagram Graph Client
        Log.info("Initializing Instagram Graph Client...")
        ig_client = InstagramGraphClient()

        # 2. Upload Reel via URL
        Log.info("Starting URL-based upload to Instagram...")
        container_id = ig_client.upload_reel(
            video_url=VIDEO_URL,
            caption=CAPTION,
            cover_url=COVER_URL
        )

        Log.success(container_id)

        if not container_id:
            raise Exception("Failed to create Instagram media container via URL")

        for i in range(30):
            status = ig_client.check_status(container_id)
            Log.info(f"Container status ({i+1}/30): {status}")
            if status == "FINISHED":
                break
            time.sleep(10)

        Log.info(f"Media container created (ID: {container_id}). Waiting for processing...")
        media_id = ig_client.publish_media(container_id)

        if media_id:
            Log.info(f"SUCCESS: Reel published! Media ID: {media_id}")
        else:
            raise Exception("Failed to publish Reel after processing")

    except Exception as e:
        Log.error(f"Upload Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
