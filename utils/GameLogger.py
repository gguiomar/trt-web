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
        
        # Initialize log file with metadata
        game_data = {
            'game_id': game_id,
            'user_id': user_id,
            'game_number': game_number,  # 1-10 for tracking progress
            'start_time': datetime.now(timezone.utc).isoformat(),
            'choices': [],  # Will store all intermediate choices
            'final_choice': None,
            'completion_time': None,
            'total_duration': None,
            'success': None
        }
        
        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2)
        
        return game_id, filepath

    def log_choice(self, filepath, data):
        """Log a choice during the game"""
        try:
            with open(filepath, 'r') as f:
                game_data = json.load(f)
            
            if data.get('type') == 'final_choice':
                # Log the final choice
                game_data['final_choice'] = {
                    'chosen_quadrant': data['chosen_quadrant'],
                    'correct': data['correct'],
                    'score': data['score'],
                    'biased_quadrant': data['biased_quadrant']
                }
                game_data['completion_time'] = datetime.now(timezone.utc).isoformat()
                
                # Calculate total duration
                start_time = datetime.fromisoformat(game_data['start_time'])
                end_time = datetime.fromisoformat(game_data['completion_time'])
                game_data['total_duration'] = (end_time - start_time).total_seconds()
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
                # Log intermediate choice
                choice_data = {
                    'round': data['round'],
                    'quadrant': data['quadrant'],
                    'cue_name': data['cue_name'],
                    'color': data['color'],
                    'timestamp': data['client_timestamp'],
                    'choice_number': data.get('choice_number', len(game_data['choices']) + 1),
                    'available_cues': data.get('available_cues', []),
                    'occluded_cues': data.get('occluded_cues', []),
                    'active_cues': data.get('active_cues', []),
                    'total_cues': data.get('total_cues', 0)
                }
                game_data['choices'].append(choice_data)
            
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
