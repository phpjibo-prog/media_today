from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
import yt_dlp
import os
import tempfile
import shutil
import time

app = Flask(__name__)

def get_ydl_opts(tmp_dir, format_type, quality):
    opts = {
        'retries': 10,
        'socket_timeout': 60, # Increased for cloud stability
        'continuedl': True,
        'quiet': True,
        'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        'http_chunk_size': 10485760, # 10MB chunks
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
        # Ensures mp4 compatibility and matches requested height
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
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
        
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

    # Railway specific: Use /tmp for writeable storage
    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    
    try:
        opts = get_ydl_opts(tmp_dir, f_type, quality)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)
            
            if f_type == 'mp3':
                downloaded_path = os.path.splitext(downloaded_path)[0] + '.mp3'
            
            actual_filename = os.path.basename(downloaded_path)

        # Stream the file and clean up immediately after
        def generate():
            with open(downloaded_path, 'rb') as f:
                yield from f
            # Cleanup once the user has received the data
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

        return Response(
            stream_with_context(generate()),
            headers={
                "Content-Disposition": f"attachment; filename={actual_filename}",
                "Content-Type": "application/octet-stream"
            }
        )

    except Exception as e:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Required for Railway to bind to the correct port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
