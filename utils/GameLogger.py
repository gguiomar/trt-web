import os
import json
import uuid
from datetime import datetime, timezone

class GameLogger:
    def __init__(self, logs_dir='logs'):
        self.logs_dir = logs_dir
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

    def create_game_log(self, user_id=None, game_number=None):
        """Create a new game log file with unique ID"""
        game_id = str(uuid.uuid4())
        filename = f"game_{game_id}.json"
        filepath = os.path.join(self.logs_dir, filename)
        
        # Initialize log file with simple structure
        game_data = {
            'game_id': game_id,
            'user_id': user_id,
            'game_number': game_number,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'rounds': [],  # Will store round-by-round data in simple format
            'final_choice': None,
            'completion_time': None,
            'success': None
        }
        
        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2)
        
        return game_id, filepath

    def save_game_data(self, filepath, game_data):
        """Save complete game data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving game data: {str(e)}")
            return False
    
    def load_game_data(self, filepath):
        """Load game data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game data: {str(e)}")
            return None

    def log_choice(self, filepath, data):
        """Log a choice during the game in simple format"""
        try:
            with open(filepath, 'r') as f:
                game_data = json.load(f)
            
            if data.get('type') == 'final_choice':
                # Log the final choice
                game_data['final_choice'] = {
                    'chosen_cue': data.get('chosen_cue', data.get('chosen_quadrant')),
                    'correct': data['correct'],
                    'score': data['score'],
                    'biased_cue': data.get('biased_cue', data.get('biased_quadrant'))
                }
                game_data['completion_time'] = datetime.now(timezone.utc).isoformat()
                game_data['success'] = data['correct']
                
                # Record game completion in user database if user_id exists
                if game_data.get('user_id'):
                    try:
                        from utils.UserManager import UserManager
                        user_manager = UserManager()
                        user_manager.record_game_completion(
                            game_data['user_id'], 
                            game_data['game_id'], 
                            data['score']
                        )
                    except Exception as e:
                        print(f"Error recording game completion for user: {str(e)}")
            else:
                # Log round choice in simple format
                round_data = {
                    'round': data['round'],
                    'available_cues': data.get('available_cues', []),  # Use from frontend
                    'chosen_cue': data.get('chosen_cue', data.get('cue_name')),
                    'color': data['color'],
                    'quadrant': data.get('quadrant'),
                    'timestamp': data['client_timestamp']
                }
                
                if 'rounds' not in game_data:
                    game_data['rounds'] = []
                
                game_data['rounds'].append(round_data)
            
            # Save updated game data
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            # Trigger statistics update
            from utils.StatsCalculator import StatsCalculator
            StatsCalculator.update_statistics(self.logs_dir)
            
            return True
        except Exception as e:
            print(f"Error logging choice: {str(e)}")
            return False
