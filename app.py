from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
from redis import Redis
from rq import Queue
# Import your task function from worker.py
from worker import download_task 

app = Flask(__name__)

# Connect to Redis using Railway's environment variable
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
q = Queue('default', connection=redis_conn)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
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

    # Queue the task in Redis
    job = q.enqueue(download_task, url, f_type, quality)
    
    return jsonify({
        "status": "queued",
        "job_id": job.get_id()
    }), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "job_id": job.get_id(),
        "status": job.get_status(),
        "result": job.result # This will be the file path when finished
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
