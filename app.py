from flask import Flask, render_template, request, send_from_directory
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def ydl_options(format_type):
    base_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s_%(id)s.%(ext)s",
        "retries": 20,
        "fragment_retries": 20,
        "socket_timeout": 30,
        "continuedl": True,
        "concurrent_fragment_downloads": 1,
        "noplaylist": True,
        "quiet": True,
    }

    formats = {
        "mp3_320": {
            **base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        },
        "mp3_128": {
            **base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
        },
        "1080p": {**base_opts, "format": "bv*[height<=1080]+ba/b", "merge_output_format": "mp4"},
        "720p":  {**base_opts, "format": "bv*[height<=720]+ba/b",  "merge_output_format": "mp4"},
        "360p":  {**base_opts, "format": "bv*[height<=360]+ba/b",  "merge_output_format": "mp4"},
        "240p":  {**base_opts, "format": "bv*[height<=240]+ba/b",  "merge_output_format": "mp4"},
        "144p":  {**base_opts, "format": "bv*[height<=144]+ba/b",  "merge_output_format": "mp4"},
    }

    return formats[format_type]


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        return render_template("index.html", url=url)
    return render_template("index.html")


@app.route("/download/<format_type>")
def download(format_type):
    url = request.args.get("url")
    with yt_dlp.YoutubeDL(ydl_options(format_type)) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if format_type.startswith("mp3"):
            filename = filename.rsplit(".", 1)[0] + ".mp3"

    return send_from_directory(DOWNLOAD_DIR, os.path.basename(filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
