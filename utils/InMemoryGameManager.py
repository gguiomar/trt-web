import json
import os
import threading
from datetime import datetime, timezone
from .config import LOGS_DIR, debug_log

class InMemoryGameManager:
    def __init__(self):
        self.active_games = {}  # game_id -> complete_game_data
        self.games_dir = os.path.join(LOGS_DIR, 'games')
        os.makedirs(self.games_dir, mode=0o775, exist_ok=True)
    
    def create_game(self, game_id, session_id, user_id, task):
        """Create a new game and store in RAM"""
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
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "final_result": None
        }
        
        self.active_games[game_id] = game_data
        debug_log(f"Created game {game_id} in RAM")
        return True
    
    def get_game_metadata(self, game_id):
        """Get only the game metadata (lightweight)"""
        game_data = self.active_games.get(game_id)
        if not game_data:
            debug_log(f"Game {game_id} not found in RAM")
            return None
        
        return game_data.get("game_metadata", {})
    
    def get_round_data(self, game_id, round_number):
        """Get data for a specific round"""
        game_data = self.active_games.get(game_id)
        if not game_data:
            debug_log(f"Game {game_id} not found in RAM")
            return None
        
        rounds_data = game_data.get("rounds_data", [])
        if round_number < len(rounds_data):
            return rounds_data[round_number]
        else:
            debug_log(f"Round {round_number} not found in game {game_id}")
            return None
    
    def log_user_choice(self, game_id, choice_data):
        """Log a user choice to RAM (instant)"""
        game_data = self.active_games.get(game_id)
        if not game_data:
            debug_log(f"Game {game_id} not found in RAM for choice logging")
            return False
        
        # Add timestamp to choice data
        choice_data['server_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add choice to user_choices array in RAM
        game_data["user_choices"].append(choice_data)
        
        # Update current round if it's a round choice
        if choice_data.get('type') == 'choice':
            current_round = choice_data.get('round', 0)
            game_data["game_metadata"]["current_round"] = current_round + 1
        
        # Update last activity
        game_data["last_activity"] = datetime.now(timezone.utc).isoformat()
        
        debug_log(f"Logged user choice for game {game_id} in RAM")
        return True
    
    def update_current_round(self, game_id, round_number):
        """Update the current round number in RAM"""
        game_data = self.active_games.get(game_id)
        if not game_data:
            debug_log(f"Game {game_id} not found in RAM")
            return False
        
        game_data["game_metadata"]["current_round"] = round_number
        game_data["last_activity"] = datetime.now(timezone.utc).isoformat()
        return True
    
    def _save_game_background(self, game_data):
        """Save game data to disk in background thread"""
        try:
            game_id = game_data['game_id']
            filepath = os.path.join(self.games_dir, f'complete_game_{game_id}.json')
            
            self._write_json_file(filepath, game_data)
            debug_log(f"Background saved game {game_id} to disk")
            
        except Exception as e:
            debug_log(f"Error background saving game: {str(e)}")
    
    def _write_json_file(self, filepath, data):
        """Helper method to write JSON file (runs in thread pool)"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def complete_game(self, game_id, final_result):
        """Complete game: trigger background save and remove from RAM"""
        game_data = self.active_games.get(game_id)
        if not game_data:
            debug_log(f"Game {game_id} not found in RAM for completion")
            return False
        
        # Update game status and final result
        game_data["status"] = "completed"
        game_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        game_data["final_result"] = final_result
        
        # Create a copy for background saving
        game_data_copy = game_data.copy()
        
        # Trigger background save (fire and forget)
        thread = threading.Thread(target=self._save_game_background, args=(game_data_copy,))
        thread.daemon = True
        thread.start()
        
        # Immediately remove from RAM
        del self.active_games[game_id]
        
        debug_log(f"Completed game {game_id}: triggered background save and removed from RAM")
        return True
    
    def get_active_games_count(self):
        """Get number of active games in RAM"""
        return len(self.active_games)
    
    def cleanup_old_games(self, hours=24):
        """Clean up old games from RAM (safety mechanism)"""
        cutoff = datetime.now(timezone.utc)
        cutoff_str = cutoff.replace(hour=cutoff.hour - hours).isoformat()
        
        games_to_remove = []
        for game_id, game_data in self.active_games.items():
            if game_data.get('last_activity', '') < cutoff_str:
                games_to_remove.append(game_id)
        
        for game_id in games_to_remove:
            # Save before removing
            game_data = self.active_games[game_id]
            game_data['status'] = 'timeout_cleanup'
            
            # Save in background thread
            thread = threading.Thread(target=self._save_game_background, args=(game_data.copy(),))
            thread.daemon = True
            thread.start()
            
            del self.active_games[game_id]
            debug_log(f"Cleaned up old game {game_id} from RAM")
        
        return len(games_to_remove)
    
    def get_game_exists(self, game_id):
        """Check if game exists in RAM"""
        return game_id in self.active_games
