import os
import json
from datetime import datetime
from collections import defaultdict

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

class StatsCalculator:
    STATS_FILE = 'static/stats.json'

    @classmethod
    def update_statistics(cls, logs_dir):
        """Calculate and update statistics from all game logs"""
        try:
            # Collect all game data from multiple directories
            games_data = []
            
            # Check main logs directory
            main_logs_dir = logs_dir
            if os.path.exists(main_logs_dir):
                for filename in os.listdir(main_logs_dir):
                    if filename.startswith('game_') and filename.endswith('.json'):
                        filepath = os.path.join(main_logs_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                game_data = json.load(f)
                                # Include games that have completion_time (completed games)
                                if game_data.get('completion_time'):
                                    games_data.append(game_data)
                        except Exception as e:
                            print(f"Error reading {filepath}: {str(e)}")
            
            # Check games subdirectory
            games_subdir = os.path.join(logs_dir, 'games')
            if os.path.exists(games_subdir):
                for filename in os.listdir(games_subdir):
                    if filename.startswith('game_') and filename.endswith('.json'):
                        filepath = os.path.join(games_subdir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                game_data = json.load(f)
                                # Include games that have final results or are marked as completed
                                if (game_data.get('final_result') is not None or 
                                    game_data.get('completion_time') or
                                    (game_data.get('status') != 'active' and len(game_data.get('user_choices', [])) > 0)):
                                    games_data.append(game_data)
                        except Exception as e:
                            print(f"Error reading {filepath}: {str(e)}")

            if not games_data:
                print("No completed games found for statistics")
                return

            # Calculate statistics
            stats = {
                'total_games': len(games_data),
                'success_rate': cls._calculate_success_rate(games_data),
                'average_duration': cls._calculate_average_duration(games_data),
                'performance_distribution': cls._calculate_performance_distribution(games_data),
                'learning_curve': cls._calculate_learning_curve(games_data),
                'last_updated': datetime.utcnow().isoformat()
            }

            # Save statistics
            os.makedirs(os.path.dirname(cls.STATS_FILE), exist_ok=True)
            with open(cls.STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)

        except Exception as e:
            print(f"Error updating statistics: {str(e)}")

    @staticmethod
    def _calculate_success_rate(games_data):
        """Calculate overall success rate"""
        successes = sum(1 for game in games_data 
                       if game.get('final_result', {}).get('correct', False))
        return (successes / len(games_data)) * 100 if games_data else 0

    @staticmethod
    def _calculate_average_duration(games_data):
        """Calculate average game duration in seconds"""
        durations = []
        for game in games_data:
            start_time = game.get('start_time')
            completion_time = game.get('completion_time')
            if start_time and completion_time:
                try:
                    from datetime import datetime
                    # Handle both formats: with Z and with +00:00
                    start_clean = start_time.replace('Z', '+00:00') if start_time.endswith('Z') else start_time
                    end_clean = completion_time.replace('Z', '+00:00') if completion_time.endswith('Z') else completion_time
                    
                    start = datetime.fromisoformat(start_clean)
                    end = datetime.fromisoformat(end_clean)
                    duration = (end - start).total_seconds()
                    if duration > 0:  # Only include positive durations
                        durations.append(duration)
                except Exception as e:
                    print(f"Error parsing timestamps: start={start_time}, end={completion_time}, error={e}")
                    pass
        return sum(durations) / len(durations) if durations else 0

    @staticmethod
    def _calculate_performance_distribution(games_data):
        """Calculate distribution of performance scores"""
        scores = [game.get('final_result', {}).get('score', 0) for game in games_data 
                 if game.get('final_result')]
        if not scores:
            return {'bins': [-100, -50, 0, 50, 100], 'counts': [0, 0, 0, 0]}
        bins = [-100, -50, 0, 50, 100]
        hist, _ = np.histogram(scores, bins=bins)
        return {
            'bins': bins,
            'counts': hist.tolist()
        }

    @staticmethod
    def _calculate_learning_curve(games_data):
        """Calculate learning curve (success rate over time)"""
        # Sort games by start time
        sorted_games = sorted(games_data, key=lambda x: x['start_time'])
        
        # Calculate rolling success rate
        window_size = 10  # Smaller window size for more data points
        success_rates = []
        
        for i in range(0, len(sorted_games), window_size):
            window = sorted_games[i:i+window_size]
            rate = sum(1 for game in window 
                      if game.get('final_result', {}).get('correct', False)) / len(window)
            success_rates.append(rate * 100)
        
        return {
            'window_size': window_size,
            'rates': success_rates
        }

    @classmethod
    def get_current_stats(cls):
        """Get current statistics from file"""
        try:
            with open(cls.STATS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
