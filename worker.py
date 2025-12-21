import os
from redis import Redis
from rq import Worker, Queue

# Get the Redis URL from environment
redis_url = os.environ.get('REDIS_URL')
if not redis_url:
    raise RuntimeError("REDIS_URL environment variable not set")

redis_conn = Redis.from_url(redis_url)

listen = ['default']

if __name__ == '__main__':
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(queues)
    worker.work()
