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
        """Create a new game log file with proper JSON structure"""
        try:
            game_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            filename = f"game_{game_id}.json"
            filepath = os.path.join(LOGS_DIR, filename)
            
            # Create initial game structure
            game_data = {
                'game_id': game_id,
                'start_time': timestamp.isoformat() + "Z",
                'choices': [],
                'metadata': {
                    'file_created': timestamp.isoformat() + "Z"
                }
            }
            
            # Write the initial structure atomically
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
                
            return game_id, filepath
                
        except Exception as e:
            print(f"Error creating game log: {str(e)}", flush=True)
            raise

    def log_choice(self, filepath, choice_data):
        """Log a choice by updating the game's JSON file"""
        try:
            # Read current game data
            with open(filepath, 'r') as f:
                game_data = json.load(f)
            
            # Add timestamp if not present
            if 'timestamp' not in choice_data:
                choice_data['timestamp'] = datetime.utcnow().isoformat() + "Z"
            
            # Append new choice
            game_data['choices'].append(choice_data)
            
            # Write back entire file atomically
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
                
            return True
                
        except Exception as e:
            print(f"Error logging choice: {str(e)}", flush=True)
            return False




