import os
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    vfx,
    AudioFileClip,
    afx,
    ColorClip,
)
from moviepy.config import change_settings
from src.core.logger import Log
import PIL.Image

# Fix for Pillow 10+ compatibility with MoviePy 1.0.3
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

if os.getenv("IMAGEMAGICK_BINARY"):
    change_settings({"IMAGEMAGICK_BINARY": os.getenv("IMAGEMAGICK_BINARY")})


def add_text_to_video(
    input_video_path,
    output_video_path,
    quote_text,
    font_size,
    color="white",
    audio_path=None,
):
    """
    Overlays a single centered quote on a video template and optionally replaces audio.
    """
    try:
        Log.info(f"Loading template: {input_video_path}")
        if not os.path.exists(str(input_video_path)):
            Log.error(f"Template file not found: {input_video_path}")
            return False

        video = VideoFileClip(str(input_video_path)).fx(
            vfx.colorx, 0.3
        )  # Darken video by 70%

        # Handle Audio Replacement
        if audio_path and os.path.exists(str(audio_path)):
            Log.info(f"Replacing audio with: {audio_path}")
            audio = AudioFileClip(str(audio_path))

            # If audio is shorter than video, loop it
            if audio.duration < video.duration:
                audio = afx.audio_loop(audio, duration=video.duration)
            else:
                # Truncate audio to match video duration
                audio = audio.set_duration(video.duration)

            video = video.set_audio(audio)
        else:
            Log.info("Using original video audio.")

        Log.info("Creating quote clip")

        # Cross-platform font detection for Times New Roman
        font_choices = [
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",  # MacOS
            "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",  # Linux
            "Times-New-Roman",  # ImageMagick Alias
            "DejaVu-Serif",  # Safety fallback
        ]
        selected_font = "Times-New-Roman"
        for f in font_choices:
            if os.path.exists(f) or not f.startswith("/"):
                selected_font = f
                break

        # Centered Quote Text Clip
        quote_clip = (
            TextClip(
                f'"{quote_text}"',
                fontsize=55,
                color=color,
                method="caption",
                font=selected_font,
                size=(int(video.w * 0.9), None),
            )
            .set_duration(video.duration)
            .set_position("center")
        )

        # Header Clip (READ CAPTION) - placed above the quote
        header_clip = (
            TextClip(
                "(READ CAPTION)",
                fontsize=30,
                color=color,
                font=selected_font,
            )
            .set_duration(video.duration)
            .set_position(("center", video.h / 2 - quote_clip.h / 2 - 80))
        )

        Log.info(f"Using font: {selected_font}")
        Log.info("Compositing video...")
        
        # Ensure 9:16 aspect ratio (1080x1920) for Instagram Reels
        target_w, target_h = 1080, 1920
        
        # We always want a 1080x1920 output. 
        # We'll scale and crop the template to "cover" the frame.
        Log.info(f"Ensuring output dimensions: {target_w}x{target_h}")
        
        # Calculate scale to cover the target dimensions
        scale = max(target_w / video.w, target_h / video.h)
        resized_video = video.resize(scale)
        
        # Crop the center to fit target dimensions
        # crop expects (x1, y1, x2, y2) or center=(x,y) + width, height
        video_covered = resized_video.crop(
            x_center=resized_video.w / 2,
            y_center=resized_video.h / 2,
            width=target_w,
            height=target_h
        )

        # Composite everything on a 1080x1920 canvas
        video_with_text = CompositeVideoClip([
            video_covered, 
            quote_clip.set_position("center"), 
            header_clip.set_position(("center", target_h / 2 - quote_clip.h / 2 - 80))
        ], size=(target_w, target_h))

        Log.info(f"Writing output video to: {output_video_path}")
        # Instagram Reel Specifications:
        # - H.264 video codec
        # - AAC audio codec @ 128kbps
        # - moov atom at the front (-movflags +faststart)
        # - 4:2:0 chroma subsampling
        # - threads=1 and preset='ultrafast' for Railway stability
        video_with_text.write_videofile(
            str(output_video_path),
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            verbose=True,
            logger="bar",
            preset="ultrafast",
            ffmpeg_params=[
                "-pix_fmt",
                "yuv420p",  # 4:2:0 chroma subsampling
                "-movflags",
                "+faststart",  # moov atom at the front
                "-b:a",
                "128k",  # 128kbps audio bitrate
                "-ar",
                "44100",  # Standard sample rate (max 48k)
            ],
        )

        # Save a frame as a thumbnail (middle of the video)
        # JPEG Format, sRGB Color Space (PIL default), 9:16 recommended
        thumbnail_path = f"{output_video_path}.jpg"
        Log.info(f"Saving cover frame to: {thumbnail_path}")
        try:
            from PIL import Image

            # get_frame returns an RGB numpy array
            frame = video_with_text.get_frame(1)
            img = Image.fromarray(frame)
            img.convert("RGB").save(
                thumbnail_path, "JPEG", quality=95, icc_profile=None
            )
        except Exception as te:
            Log.warning(
                f"Failed to save thumbnail via PIL: {te}. Trying fallback save_frame."
            )
            video_with_text.save_frame(thumbnail_path, t=video.duration / 2)

        Log.info(
            "Video and thumbnail written with Reel specifications. Closing clips..."
        )
        video.close()
        video_with_text.close()
        Log.info("Video generation completed successfully.")
        return True

    except Exception as e:
        Log.error(f"Failed to generate video: {e}")
        return False


if __name__ == "__main__":
    # Test script
    import sys

    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    from src.config.settings import settings

    add_text_to_video(
        input_video_path=settings.template_path,
        output_video_path=settings.output_path,
        quote_text="Test with external audio",
        font_size=50,
        color="white",
        audio_path=settings.audio_track_path,
    )
