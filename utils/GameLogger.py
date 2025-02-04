import os
import json
from datetime import datetime
import uuid
import traceback
from .config import LOGS_DIR, debug_log

class GameLogger:
    def __init__(self):
        # Use same directory creation pattern
        self.logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        print(f"GameLogger initialized. Logs directory: {self.logs_dir}", flush=True)

    def create_game_log(self):
        """Create a new game log file using proven pattern"""
        try:
            # Generate unique filename
            game_id = str(uuid.uuid4())
            filename = f"game_{game_id}.json"
            filepath = os.path.join(self.logs_dir, filename)
            
            # Initial game structure
            game_data = {
                'game_id': game_id,
                'start_time': datetime.utcnow().isoformat(),
                'choices': [],
                'metadata': {
                    'file_created': datetime.utcnow().isoformat()
                }
            }
            
            # Use the working file writing pattern
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
                
            print(f"Created game log: {filepath}", flush=True)
            return game_id, filepath
                
        except Exception as e:
            print(f"Error creating game log: {str(e)}", flush=True)
            raise

    def log_choice(self, filepath, choice_data):
        """Log a choice to the game file"""
        try:
            # Read current game data
            with open(filepath, 'r') as f:
                game_data = json.load(f)
            
            # Add timestamp if not present
            if 'timestamp' not in choice_data:
                choice_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Append new choice
            game_data['choices'].append(choice_data)
            
            # Write updated data
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
                
            print(f"Logged choice to: {filepath}", flush=True)
            return True
                
        except Exception as e:
            print(f"Error logging choice: {str(e)}", flush=True)
            return False