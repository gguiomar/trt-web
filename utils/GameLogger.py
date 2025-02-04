import os
import json
from datetime import datetime
import uuid
import traceback
from .config import LOGS_DIR, debug_log

class GameLogger:
    def __init__(self):
        debug_log("Initializing GameLogger")
        try:
            os.makedirs(LOGS_DIR, mode=0o775, exist_ok=True)
            debug_log(f"GameLogger directory verified: {LOGS_DIR}")
        except Exception as e:
            debug_log(f"Error in GameLogger init: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def create_game_log(self):
        """Create a new game log file with same approach as choice logs"""
        try:
            game_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().timestamp()
            filename = f"game_{timestamp}_{game_id}.json"
            filepath = os.path.join(LOGS_DIR, filename)
            
            # Initialize log file - keep it simple like choice logs
            log_data = {
                'game_id': game_id,
                'timestamp': datetime.utcnow().isoformat(),
                'choices': []
            }
            
            # Write using the same approach as choice logs
            with open(filepath, 'w') as f:
                json.dump(log_data, f)
                
            return game_id, filepath
                
        except Exception as e:
            print(f"Error creating game log: {str(e)}", flush=True)
            raise

    def log_choice(self, filepath, choice_data):
        """Log a choice with proper error handling"""
        try:
            debug_log(f"Attempting to log choice to: {filepath}")
            
            if not os.path.exists(filepath):
                debug_log(f"Log file not found: {filepath}")
                return False
            
            # Read existing log
            with open(filepath, 'r') as f:
                log_data = json.load(f)
            
            # Add new choice with timestamp
            choice_data['timestamp'] = datetime.utcnow().isoformat()
            log_data['choices'].append(choice_data)
            
            # Write updated log
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            os.chmod(filepath, 0o664)
            
            debug_log("Choice logged successfully")
            return True
            
        except Exception as e:
            debug_log(f"Error logging choice: {str(e)}\n{traceback.format_exc()}")
            return False