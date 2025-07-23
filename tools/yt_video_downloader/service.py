from pytube import YouTube, Playlist
import os


def download_video(url, output_dir):
    yt = YouTube(url)
    stream = yt.streams.filter(
        progressive=True, file_extension="mp4"
    ).get_highest_resolution()
    filename = stream.default_filename
    stream.download(output_path=output_dir)
    return filename


def download_playlist(url, output_dir):
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
