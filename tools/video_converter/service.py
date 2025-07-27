import os
import subprocess
import uuid
from imageio_ffmpeg import get_ffmpeg_exe

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

    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True)

    return output_filename
