from flask import Flask, render_template, request, jsonify, send_file, after_this_request
import yt_dlp
import os
import tempfile
import shutil
import re

app = Flask(__name__)

# Helper to generate options
def get_ydl_opts(tmp_dir, format_type, quality):
    opts = {
        'retries': 10,
        'socket_timeout': 30,
        'continuedl': True,
        'quiet': True,
        'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        'http_chunk_size': 10485760, 
    }

    if format_type == 'mp3':
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
    return opts

@app.route('/')
def index():
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
        opts = get_ydl_opts(tmp_dir, f_type, quality)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            # 1. Download the file
            info = ydl.extract_info(url, download=True)
            
            # 2. Get the correct file path
            downloaded_path = ydl.prepare_filename(info)
            
            # 3. Correct extension for MP3
            if f_type == 'mp3':
                downloaded_path = os.path.splitext(downloaded_path)[0] + '.mp3'
            
            # 4. Extract the actual file name for the browser
            actual_filename = os.path.basename(downloaded_path)

        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                print(f"Cleanup error: {e}")
            return response

        return send_file(
            downloaded_path,
            as_attachment=True,
            download_name=actual_filename
        )

    except Exception as e:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
