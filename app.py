from flask import Flask, render_template, request, jsonify, send_file, after_this_request
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
            'retries': 10,
            'socket_timeout': 30,
            'continuedl': True,
            'quiet': True,
            'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
            'http_chunk_size': 10485760, # 10MB chunks
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
            # download=True performs the actual download to tmp_dir
            info = ydl.extract_info(url, download=True)
            
            # Get the expected filename from yt-dlp
            downloaded_path = ydl.prepare_filename(info)
            
            # Handle the extension change for MP3 post-processing
            if f_type == 'mp3':
                downloaded_path = os.path.splitext(downloaded_path)[0] + '.mp3'
            
            # Extract just the filename for the browser's save dialog
            video_title = os.path.basename(downloaded_path)

        @after_this_request
        def cleanup(response):
            try:
                # Use a small delay or check if file is closed if needed, 
                # but rmtree usually works well here.
                shutil.rmtree(tmp_dir)
            except Exception as e:
                app.logger.error(f"Cleanup error: {e}")
            return response

        return send_file(
            downloaded_path,
            as_attachment=True,
            download_name=video_title,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
