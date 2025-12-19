# worker.py
import os
import time
from multi_stream_recorder import MultiStreamRecorder
from fingerprint_engine import FingerprintEngine
import mysql.connector

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
    #recorder = MultiStreamRecorder(DB_CONFIG)
    
    # Ensure FingerprintEngine uses the DB_CONFIG properly
    f_engine = FingerprintEngine(
        db_host=DB_CONFIG['host'],
        db_user=DB_CONFIG['user'],
        db_password=DB_CONFIG['password'],
        db_name=DB_CONFIG['database'],
        db_port=DB_CONFIG['port']
    )

    # Start the recorder in a separate thread/background
    #recorder.start()

    while True:
        conn = None
        try:
            print("It has reached while and try block")
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # 1. Fetch one pending track
            cursor.execute("SELECT track_id, track_name, file_path FROM user_tracks WHERE status = 'pending' LIMIT 1")
            track = cursor.fetchone()

            print("It has reached select tracks with pending status")
             print(track_name)
            if track:
                print(f"[WORKER] Found pending track: {track['track_name']}")
                
                if os.path.exists(track['file_path']):
                    # 2. Perform Fingerprinting (Heavy CPU Task)
                    f_engine.fingerprint_file(track['file_path'])
                    
                    # 3. Mark as completed
                    cursor.execute("UPDATE user_tracks SET status = 'completed' WHERE track_id = %s", (track['track_id'],))
                    print(f"[WORKER] Successfully processed: {track['track_name']}")
                else:
                    print(f"[WORKER] File not found: {track['file_path']}")
                    cursor.execute("UPDATE user_tracks SET status = 'failed' WHERE track_id = %s", (track['track_id'],))
                
                conn.commit()
            
            cursor.close()
        except Exception as e:
            print(f"[WORKER ERROR]: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()

        # Sleep to prevent high CPU usage while idle
        time.sleep(10)
if __name__ == '__main__':
    main()
