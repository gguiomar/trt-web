import json
import os
from datetime import datetime, timezone
from .config import LOGS_DIR, debug_log

class SessionMetadataLogger:
    def __init__(self):
        self.sessions_dir = os.path.join(LOGS_DIR, 'sessions')
        self.games_dir = os.path.join(LOGS_DIR, 'games')
        
        # Create directories if they don't exist
        os.makedirs(self.sessions_dir, mode=0o775, exist_ok=True)
        os.makedirs(self.games_dir, mode=0o775, exist_ok=True)
    
    def create_session(self, session_id, user_id):
        """Create a new session metadata entry"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "games": [],
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        session_file = os.path.join(self.sessions_dir, f'session_{session_id}.json')
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            debug_log(f"Created session metadata: {session_id}")
            return session_file
        except Exception as e:
            debug_log(f"Error creating session metadata: {str(e)}")
            return None
    
    def log_game_start(self, session_id, game_id, user_id):
        """Log the start of a new game in the session"""
        session_file = os.path.join(self.sessions_dir, f'session_{session_id}.json')
        
        try:
            # Load existing session data
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
            else:
                # Create new session if it doesn't exist
                session_data = self.create_session(session_id, user_id)
                if not session_data:
                    return False
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
            
            # Add new game entry
            game_entry = {
                "game_id": game_id,
                "game_file": f"logs/games/game_{game_id}.json",
                "status": "active",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None
            }
            
            session_data["games"].append(game_entry)
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            # Save updated session data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            debug_log(f"Logged game start: {game_id} in session {session_id}")
            return True
            
        except Exception as e:
            debug_log(f"Error logging game start: {str(e)}")
            return False
    
    def log_game_end(self, session_id, game_id, score):
        """Log the completion of a game"""
        session_file = os.path.join(self.sessions_dir, f'session_{session_id}.json')
        
        try:
            if not os.path.exists(session_file):
                debug_log(f"Session file not found: {session_file}")
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Find and update the game entry
            for game in session_data["games"]:
                if game["game_id"] == game_id:
                    game["status"] = "completed"
                    game["completed_at"] = datetime.now(timezone.utc).isoformat()
                    game["score"] = score
                    break
            
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            # Save updated session data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            debug_log(f"Logged game completion: {game_id} with score {score}")
            return True
            
        except Exception as e:
            debug_log(f"Error logging game end: {str(e)}")
            return False
    
    def get_session_games(self, session_id):
        """Get all games for a session"""
        session_file = os.path.join(self.sessions_dir, f'session_{session_id}.json')
        
        try:
            if not os.path.exists(session_file):
                return []
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            return session_data.get("games", [])
            
        except Exception as e:
            debug_log(f"Error getting session games: {str(e)}")
            return []
    
    def update_activity(self, session_id):
        """Update last activity timestamp for a session"""
        session_file = os.path.join(self.sessions_dir, f'session_{session_id}.json')
        
        try:
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return True
            
        except Exception as e:
            debug_log(f"Error updating session activity: {str(e)}")
            return False
