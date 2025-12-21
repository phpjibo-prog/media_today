from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    f_type = data.get('format')
    quality = data.get('quality')

    # Create a temporary directory for this specific download
    tmp_dir = tempfile.mkdtemp()
    
    try:
        # Configuration for yt-dlp
        ydl_opts = {
            'retries': 10,
            'socket_timeout': 30,
            'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
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
            # Video logic: select specific height and ensure mp4
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If it was an MP3, the extension in 'filename' might still be .webm/.m4a
            # We need to ensure we point to the converted .mp3 file
            if f_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        # Send the file to the browser
        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    # Cleaning up files is tricky after send_file, 
    # normally handled by a background task or a 'finally' block with a delay.

if __name__ == '__main__':
    app.run(debug=True, port=5000)
