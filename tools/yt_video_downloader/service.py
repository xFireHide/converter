from pytube import YouTube, Playlist
from urllib.parse import urlparse, parse_qs
import os


def sanitize_url(url: str) -> str:
    """Return a canonical YouTube URL."""
    url = url.strip()

    if not url:
        return url

    # Ensure the URL includes a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # Transform youtu.be links to youtube.com/watch
    if parsed.netloc.endswith("youtu.be"):
        video_id = parsed.path.lstrip("/")
        url = f"https://www.youtube.com/watch?v={video_id}"
        return url

    # Convert shorts links to standard watch links
    if "/shorts/" in parsed.path:
        parts = parsed.path.split("/shorts/")
        if len(parts) > 1 and parts[1]:
            video_id = parts[1].split("/")[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
            return url

    return url


def download_video(url, output_dir):
    url = sanitize_url(url)
    yt = YouTube(url)
    stream = yt.streams.filter(
        progressive=True, file_extension="mp4"
    ).get_highest_resolution()
    filename = stream.default_filename
    stream.download(output_path=output_dir)
    return filename


def download_playlist(url, output_dir):
    url = sanitize_url(url)
    pl = Playlist(url)
    downloaded_files = []
    for video_url in pl.video_urls:
        try:
            filename = download_video(video_url, output_dir)
            downloaded_files.append(filename)
        except Exception as e:
            print(f"Erro ao baixar {video_url}: {e}")
    return downloaded_files


def handle_download(url, output_dir):
    url = sanitize_url(url)
    # Decide se é vídeo ou playlist
    if "playlist" in url:
        return download_playlist(url, output_dir)
    elif "watch" in url:
        return [download_video(url, output_dir)]
    else:
        # Pega playlists encurtadas ou formatos alternativos
        try:
            pl = Playlist(url)
            if pl.video_urls:
                return download_playlist(url, output_dir)
        except:
            pass
        # Tenta baixar como vídeo normal
        return [download_video(url, output_dir)]
