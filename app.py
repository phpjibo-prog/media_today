from flask import Flask, render_template, request, jsonify, Response
from werkzeug.wsgi import FileWrapper
import yt_dlp
import os
import tempfile
import shutil
import re

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

    # 2. Use a unique subfolder per request to prevent filename conflicts
    request_id = re.sub(r'\D', '', str(os.urandom(4).hex())) 
    save_path = os.path.join(DOWNLOAD_FOLDER, request_id)
    os.makedirs(save_path)

    simple_name = "download_file" 
    
    try:
        ydl_opts = {
            'outtmpl': f'{save_path}/{simple_name}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
        }

        if f_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'download')
            video_title = f"{sanitize_filename(original_title)}.{'mp3' if f_type == 'mp3' else 'mp4'}"
            downloaded_path = os.path.join(save_path, f"{simple_name}.{'mp3' if f_type == 'mp3' else 'mp4'}")

        if not os.path.exists(downloaded_path):
            raise FileNotFoundError(f"File not found at {downloaded_path}")

        # 3. Stream to browser WITHOUT deleting the file afterward
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
        # Note: We are no longer deleting save_path here so you can debug failed downloads
        return jsonify({'error': str(e)}), 400
        
if __name__ == '__main__':
    app.run(debug=True)
