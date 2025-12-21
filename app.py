from flask import Flask, render_template, request, jsonify, Response
from werkzeug.wsgi import FileWrapper
import yt_dlp
import os
import tempfile
import shutil
import re

app = Flask(__name__)

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

    tmp_dir = tempfile.mkdtemp()
    # Force a simple filename to avoid [Errno 2] issues
    simple_name = "download_file" 
    
    try:
        ydl_opts = {
            # We fix the filename here so we don't have to guess it later
            'outtmpl': f'{tmp_dir}/{simple_name}.%(ext)s',
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
            # The actual title for the user's browser
            original_title = info.get('title', 'download')
            video_title = f"{sanitize_filename(original_title)}.{'mp3' if f_type == 'mp3' else 'mp4'}"
            
            # The path where the file actually sits on the server
            downloaded_path = os.path.join(tmp_dir, f"{simple_name}.{'mp3' if f_type == 'mp3' else 'mp4'}")

        if not os.path.exists(downloaded_path):
            raise FileNotFoundError(f"File not found at {downloaded_path}")

        def generate():
            try:
                with open(downloaded_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    shutil.rmtree(tmp_dir)
                    print(f"Cleanup successful: {tmp_dir}")
                except:
                    pass

        return Response(
            generate(),
            mimetype='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename=\"{video_title}\"",
                "Content-Length": os.path.getsize(downloaded_path)
            }
        )

    except Exception as e:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return jsonify({'error': str(e)}), 400
        
if __name__ == '__main__':
    app.run(debug=True)
