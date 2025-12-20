from yt_dlp import YoutubeDL

def get_youtube_formats(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_formats = []
    audio_formats = []

    for f in info.get("formats", []):
        data = {
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "url": f.get("url")
        }

        if f.get("vcodec") != "none":
            data.update({
                "resolution": f.get("resolution"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec")
            })
            video_formats.append(data)
        else:
            data.update({
                "abr": f.get("abr"),
                "acodec": f.get("acodec")
            })
            audio_formats.append(data)

    return video_formats, audio_formats
