import os
import json
from datetime import datetime
import numpy as np
from collections import defaultdict

class StatsCalculator:
    STATS_FILE = 'static/stats.json'

    @classmethod
    def update_statistics(cls, logs_dir):
        """Calculate and update statistics from all game logs"""
        try:
            # Collect all game data
            games_data = []
            for filename in os.listdir(logs_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(logs_dir, filename), 'r') as f:
                        game_data = json.load(f)
                        if game_data.get('completion_time'):  # Only include completed games
                            games_data.append(game_data)

            if not games_data:
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
        successes = sum(1 for game in games_data if game.get('success', False))
        return (successes / len(games_data)) * 100 if games_data else 0

    @staticmethod
    def _calculate_average_duration(games_data):
        """Calculate average game duration"""
        durations = [game.get('total_duration', 0) for game in games_data]
        return np.mean(durations) if durations else 0

    @staticmethod
    def _calculate_performance_distribution(games_data):
        """Calculate distribution of performance scores"""
        scores = [game.get('final_choice', {}).get('score', 0) for game in games_data]
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
        window_size = 50  # Number of games to average over
        success_rates = []
        
        for i in range(0, len(sorted_games), window_size):
            window = sorted_games[i:i+window_size]
            rate = sum(1 for game in window if game.get('success', False)) / len(window)
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