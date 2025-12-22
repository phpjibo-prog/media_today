from flask import Flask, render_template, request, jsonify, Response
from werkzeug.wsgi import FileWrapper
import yt_dlp
import os
import tempfile
import shutil
import re
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
def sanitize_filename(name):
    """Removes characters that aren't allowed in filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route('/')
def index():
    # This renders your index.html file
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    f_type = data.get('format')
    quality = data.get('quality')

    request_id = re.sub(r'\D', '', str(os.urandom(4).hex())) 
    save_path = os.path.join(DOWNLOAD_FOLDER, request_id)
    os.makedirs(save_path)

    simple_name = "download_file" 
    ext = 'mp3' if f_type == 'mp3' else 'mp4'
    downloaded_path = os.path.join(save_path, f"{simple_name}.{ext}")
    
    try:
        ydl_opts = {
            'outtmpl': f'{save_path}/{simple_name}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'cookiefile': 'cookies.txt',
        }

        if f_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(quality),
                }],
            })
        else:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]/best',
                'merge_output_format': 'mp4',
            })


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'download')
            video_title = f"{sanitize_filename(original_title)}.{ext}"

        # --- FIX: WAIT FOR FILE ---
        # Sometimes ffmpeg takes a second to finalize the file after yt-dlp finishes
        retries = 10
        while not os.path.exists(downloaded_path) and retries > 0:
            time.sleep(1)
            retries -= 1

        if not os.path.exists(downloaded_path):
            # Fallback check: see if it saved with a different extension (like .m4a or .webm)
            files = os.listdir(save_path)
            if files:
                downloaded_path = os.path.join(save_path, files[0])
            else:
                raise FileNotFoundError(f"File not found at {downloaded_path}")
        # ---------------------------

        def generate():
            with open(downloaded_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        return Response(
            generate(),
            mimetype='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename=\"{video_title}\"",
                "Content-Length": os.path.getsize(downloaded_path)
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 400
        
if __name__ == '__main__':
    app.run(debug=True)
