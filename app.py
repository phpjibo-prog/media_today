from flask import Flask, render_template, request, jsonify, send_file, after_this_request
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)

# Helper to generate options
def get_ydl_opts(tmp_dir, format_type, quality):
    opts = {
        'retries': 10,
        'socket_timeout': 60, # Increased for cloud
        'continuedl': True,
        'quiet': True,
        # Use /tmp as it's the most reliable writeable path on Railway
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
            # Best mp4 available under/at quality
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]',
            'merge_output_format': 'mp4',
        })
    return opts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    f_type = data.get('format')
    quality = data.get('quality')

    # Force the temporary directory to be inside /tmp for Linux/Railway compatibility
    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    
    try:
        opts = get_ydl_opts(tmp_dir, f_type, quality)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)
            
            if f_type == 'mp3':
                downloaded_path = os.path.splitext(downloaded_path)[0] + '.mp3'
            
            actual_filename = os.path.basename(downloaded_path)

        # IMPORTANT: send_file can fail if the file is deleted before it finishes streaming.
        # We use a response generator to ensure cleanup happens AFTER the download.
        def generate():
            with open(downloaded_path, 'rb') as f:
                yield from f
            # Cleanup once the generator is exhausted
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

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
    # Railway provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
