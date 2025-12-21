import yt_dlp
import tempfile
import shutil
import os

def download_video(url, f_type, quality):
    tmp_dir = tempfile.mkdtemp(dir='/tmp', prefix='yt_')
    try:
        ydl_opts = {
            'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
        }

        if f_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':quality}]
            })
        else:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}]+bestaudio/best',
                'merge_output_format':'mp4'
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if f_type == 'mp3':
                path = os.path.splitext(path)[0] + '.mp3'

        # You could upload path to cloud storage here
        return {'status': 'done', 'file_path': path}
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
