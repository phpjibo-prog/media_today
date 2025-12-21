from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Configure download options
def get_ydl_opts(format_type, quality):
    opts = {
        'retries': 10,
        'socket_timeout': 30,
        'continuedl': True,
        'quiet': True,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    if format_type == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality, # '320' or '128'
            }],
        })
    else:
        # For video, we target specific height and ensure mp4 container
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

# Note: In a production app, you'd stream the file back to the user.
# For this demo, we handle the logic for selecting the right format.
@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    f_type = data.get('format') # 'mp3' or 'mp4'
    quality = data.get('quality')

    try:
        opts = get_ydl_opts(f_type, quality)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return jsonify({'message': 'Download started on server!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
