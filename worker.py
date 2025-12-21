import os
from redis import Redis
from rq import Worker, Queue

# Use the Redis URL provided by Railway
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)

listen = ['default']

if __name__ == '__main__':
    # Pass the connection directly to Worker
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(queues)
    worker.work()
