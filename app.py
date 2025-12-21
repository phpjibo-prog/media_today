from flask import Flask, render_template, request, jsonify
from redis import Redis
from rq import Queue
from tasks import download_video

app = Flask(__name__)

# Redis connection (Railway will provide REDIS_URL)
redis_conn = Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
q = Queue(connection=redis_conn)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    from yt_dlp import YoutubeDL
    url = request.json.get('url')
    try:
        with YoutubeDL({'quiet': True}) as ydl:
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

    # Push job to worker queue
    job = q.enqueue(download_video, url, f_type, quality)
    
    return jsonify({'job_id': job.get_id(), 'status': 'queued'})

@app.route('/status/<job_id>')
def job_status(job_id):
    from rq.job import Job
    job = Job.fetch(job_id, connection=redis_conn)
    if job.is_finished:
        return jsonify({'status': 'finished', 'result': job.result})
    elif job.is_failed:
        return jsonify({'status': 'failed', 'error': str(job.exc_info)})
    else:
        return jsonify({'status': 'queued'})

if __name__ == '__main__':
    import os
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
