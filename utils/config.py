import os

# Set up base directory (using absolute path)
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Go up one level from utils
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
SESSION_DIR = os.path.join(BASE_DIR, 'flask_session')
DEBUG_LOG = os.path.join(BASE_DIR, 'flask_debug.log')

def debug_log(message):
    """Write debug messages with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    log_message = f"{timestamp} - {message}"
    try:
        with open(DEBUG_LOG, 'a') as f:
            f.write(log_message + '\n')
    except Exception as e:
        print(f"Error writing to debug log: {e}")

# Create necessary directories
for directory in [LOGS_DIR, SESSION_DIR]:
    os.makedirs(directory, mode=0o775, exist_ok=True)