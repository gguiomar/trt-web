import json
import os
from datetime import datetime, timezone
from .config import LOGS_DIR, debug_log

class GameDataManager:
    def __init__(self):
        self.games_dir = os.path.join(LOGS_DIR, 'games')
        os.makedirs(self.games_dir, mode=0o775, exist_ok=True)
    
    def create_game_file(self, game_id, session_id, user_id, task):
        """Create a new game data file with complete game information"""
        game_data = {
            "game_id": game_id,
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "game_metadata": {
                "biased_quadrant": task.biased_quadrant,
                "n_rounds": task.n_rounds,
                "n_quadrants": task.n_quadrants,
                "current_round": 0,
                "task_description": task.get_task_description()
            },
            "rounds_data": task.rounds,
            "user_choices": [],
            "final_result": None
        }
        
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        try:
            with open(game_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            debug_log(f"Created game data file: {game_id}")
            return game_file
        except Exception as e:
            debug_log(f"Error creating game data file: {str(e)}")
            return None
    
    def get_game_metadata(self, game_id):
        """Get only the game metadata (lightweight)"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return None
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            return game_data.get("game_metadata", {})
            
        except Exception as e:
            debug_log(f"Error getting game metadata: {str(e)}")
            return None
    
    def get_round_data(self, game_id, round_number):
        """Get data for a specific round"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return None
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            rounds_data = game_data.get("rounds_data", [])
            if round_number < len(rounds_data):
                return rounds_data[round_number]
            else:
                debug_log(f"Round {round_number} not found in game {game_id}")
                return None
                
        except Exception as e:
            debug_log(f"Error getting round data: {str(e)}")
            return None
    
    def log_user_choice(self, game_id, choice_data):
        """Log a user choice to the game file"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return False
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            # Add timestamp to choice data
            choice_data['server_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Add choice to user_choices array
            game_data["user_choices"].append(choice_data)
            
            # Update current round if it's a round choice
            if choice_data.get('type') == 'choice':
                current_round = choice_data.get('round', 0)
                game_data["game_metadata"]["current_round"] = current_round + 1
            
            # Save updated game data
            with open(game_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            debug_log(f"Logged user choice for game {game_id}")
            return True
            
        except Exception as e:
            debug_log(f"Error logging user choice: {str(e)}")
            return False
    
    def complete_game(self, game_id, final_result):
        """Mark game as completed and store final result"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return False
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            # Update game status and final result
            game_data["status"] = "completed"
            game_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            game_data["final_result"] = final_result
            
            # Save updated game data
            with open(game_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            debug_log(f"Completed game {game_id} with result: {final_result}")
            return True
            
        except Exception as e:
            debug_log(f"Error completing game: {str(e)}")
            return False
    
    def get_full_game_data(self, game_id):
        """Get complete game data (use sparingly)"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return None
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            return game_data
            
        except Exception as e:
            debug_log(f"Error getting full game data: {str(e)}")
            return None
    
    def update_current_round(self, game_id, round_number):
        """Update the current round number"""
        game_file = os.path.join(self.games_dir, f'game_{game_id}.json')
        
        try:
            if not os.path.exists(game_file):
                debug_log(f"Game file not found: {game_file}")
                return False
            
            with open(game_file, 'r') as f:
                game_data = json.load(f)
            
            game_data["game_metadata"]["current_round"] = round_number
            
            with open(game_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            return True
            
        except Exception as e:
            debug_log(f"Error updating current round: {str(e)}")
            return False
