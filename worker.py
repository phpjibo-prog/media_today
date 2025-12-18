# worker.py
import os
import time
from multi_stream_recorder import MultiStreamRecorder

# Database Configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', ''),
    'user': os.environ.get('MYSQLUSER', ''),
    'password': os.environ.get('MYSQLPASSWORD', ''),
    'database': os.environ.get('MYSQLDATABASE', ''), 
    'port': int(os.environ.get('MYSQLPORT', 3306))
}

def main():
    print("--- Starting Background Audio Worker ---")
    
    # Initialize the recorder
    recorder = MultiStreamRecorder(DB_CONFIG)
    
    # Start the loop directly (do not use .start() as a thread, 
    # just run the _loop logic in the main process)
    try:
        # We call the internal loop directly so the process stays alive
        recorder._loop()
    except KeyboardInterrupt:
        print("Worker stopping...")
        recorder.stop()
    except Exception as e:
        print(f"CRITICAL WORKER ERROR: {e}")
        # Wait a bit before crashing so we don't spam restarts
        time.sleep(10)
        raise e

if __name__ == '__main__':
    main()
