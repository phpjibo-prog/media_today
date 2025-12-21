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
    
    try:
        ydl_opts = {
            'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
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
            downloaded_path = ydl.prepare_filename(info)
            if f_type == 'mp3':
                downloaded_path = os.path.splitext(downloaded_path)[0] + '.mp3'
            
            video_title = os.path.basename(downloaded_path)

        # Create a generator to stream the file and then clean up
        # Create a generator to stream the file and then clean up
        def generate():
            try:
                with open(downloaded_path, 'rb') as f:
                    # Python 3.7 compatible chunk reading
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            finally:
                # This 'finally' block ensures cleanup even if the user cancels the download
                try:
                    if os.path.exists(tmp_dir):
                        shutil.rmtree(tmp_dir)
                        print(f"Railway Cleanup successful: {tmp_dir}")
                except Exception as cleanup_err:
                    print(f"Cleanup error: {cleanup_err}")

        return Response(
            generate(),
            mimetype='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename=\"{video_title}\"",
                "Content-Length": os.path.getsize(downloaded_path) # Helps the browser show a progress bar
            }
        )

    except Exception as e:
        # If something fails BEFORE the generator starts, clean up here
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
