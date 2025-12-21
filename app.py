from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import shutil
import re

app = Flask(__name__)

def sanitize_filename(name):
    """Remove invalid filename characters."""
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
    f_type = data.get('format')  # 'mp3' or 'mp4'
    quality = data.get('quality')

    # Use Railway-friendly /tmp for temp files
    tmp_dir = tempfile.mkdtemp(dir='/tmp', prefix='yt_')

    try:
        ydl_opts = {
            'retries': 10,
            'socket_timeout': 30,
            'continuedl': True,
            'quiet': True,
            'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
            'http_chunk_size': 10485760,  # 10MB chunks
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

        # Send file and delete temp folder immediately after
        response = send_file(
            downloaded_path,
            as_attachment=True,
            download_name=video_title,
            mimetype='application/octet-stream'
        )
        # Cleanup temp folder after response
        def remove_temp_folder(response):
            try:
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception as e:
                app.logger.error(f"Temp cleanup failed: {e}")
            return response

        response.call_on_close(remove_temp_folder)
        return response

    except Exception as e:
        # Ensure cleanup on error
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
