from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


def add_text_to_video(input_video_path, output_video_path, text, font_size, color):
    video = VideoFileClip(input_video_path)

    text_clip = TextClip(
        text,
        fontsize=font_size,
        font="/Users/aditya/Desktop/video_maker/src/Rubik-Regular.otf",
        color=color,
        method="caption",
        size=video.size,
        bg_color="#00000075"
    ).set_duration(video.duration)
    video_with_text = CompositeVideoClip([video, text_clip])

    video_with_text.write_videofile(
        output_video_path, codec="libx264", audio_codec="aac")
