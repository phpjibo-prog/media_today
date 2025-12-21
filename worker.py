import os
import yt_dlp
import shutil
import tempfile
from redis import Redis
from rq import Worker, Queue, Connection

# Connect to Railway's Redis instance
# Railway provides REDIS_URL automatically when you add a Redis plugin
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
conn = Redis.from_url(redis_url)

def download_task(url, f_type, quality):
    """The function that actually does the downloading"""
    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    
    opts = {
        'retries': 10,
        'socket_timeout': 60,
        'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
        'quiet': True,
        'http_chunk_size': 10485760,
    }

    if f_type == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        })
    else:
        opts.update({
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if f_type == 'mp3':
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            
            print(f"Success: {file_path}")
            # Note: In a full worker setup, you would upload this to 
            # S3/Cloudinary and return the link, as the worker's disk is temporary.
            return file_path
    except Exception as e:
        print(f"Error: {str(e)}")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return None

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, ['default'])))
        worker.work()
