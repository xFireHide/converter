import os
import uuid
from moviepy.editor import VideoFileClip

UPLOAD_FOLDER = "static/video_converter/uploads"
CONVERTED_FOLDER = "static/video_converter/converted"
ALLOWED_EXTENSIONS = {
    "mp4",
    "avi",
    "mov",
    "mkv",
    "flv",
    "wmv",
    "webm",
    "mpeg",
    "3gp",
    "ogg",
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


def is_allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_video(file):
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath


def convert_video(input_path, output_format):
    output_filename = f"{uuid.uuid4()}.{output_format}"
    output_path = os.path.join(CONVERTED_FOLDER, output_filename)

    clip = VideoFileClip(input_path)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_filename
