from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from tasks import download_video

app = Flask(__name__)
redis_conn = Redis()
q = Queue(connection=redis_conn)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    f_type = data.get('format')
    quality = data.get('quality')

    # Push job to worker queue
    job = q.enqueue(download_video, url, f_type, quality)
    
    return jsonify({'job_id': job.get_id(), 'status': 'queued'})
