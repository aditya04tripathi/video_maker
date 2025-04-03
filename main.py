from datetime import datetime
from dotenv import load_dotenv
import os

from src.gen_video import add_text_to_video
from src.upload_to_instagram import upload_video_to_instagram

load_dotenv()

username = os.getenv("IG_UNAME")
password = os.getenv("IG_PASSW")

base_dir = os.path.dirname(os.path.abspath(__file__))
hashtags = [
    "#love", "#romance", "#couplegoals", "#relationshipgoals", "#inlove",
    "#foreverlove", "#soulmates", "#lovequotes", "#romantic", "#trueLove",
    "#passion", "#affection", "#lovestory", "#togetherforever", "#heart",
    "#loveislove", "#happiness", "#cuteCouple", "#lovebirds", "#adorable",
    "#kisses", "#hugs", "#sweetheart", "#valentine", "#couplelife"
]
template_path = f"{base_dir}/src/insta_template.mp4"
output_path = f"{base_dir}/src/output_video.mp4"
date = datetime.now().strftime('%A, %B %d %Y')
caption = f"""I love you so much, my love ❤️✨

{" " + " ".join(hashtags)}
"""
add_text_to_video(
    template_path,
    output_path,
    f"Remember <3\nIt's {date}\nYou are my everything\nI'm still falling in love with you\nand won't stop loving you, ilysm",
    f"{base_dir}/src/Rubik-Regular.otf",
    50,
    "white"
)

upload_video_to_instagram(username, password, output_path, caption)
