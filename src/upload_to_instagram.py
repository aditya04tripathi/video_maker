from instagrapi import Client


def upload_video_to_instagram(username, password, video_path, caption):
    client = Client()
    client.login(username, password)

    media = client.video_upload(video_path, caption)
    print(f"Video uploaded successfully: {media.pk}")
