import os
import json
import sqlite3
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
    def update_statistics(cls, logs_dir, force_update=False):
        """Calculate and update statistics from all game logs"""
        try:
            # Check if we should update (cooldown of 5 minutes unless forced)
            if not force_update and os.path.exists(cls.STATS_FILE):
                try:
                    with open(cls.STATS_FILE, 'r') as f:
                        existing_stats = json.load(f)
                        last_updated = existing_stats.get('last_updated')
                        if last_updated:
                            from datetime import timedelta
                            last_update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            now = datetime.utcnow()
                            if (now - last_update_time) < timedelta(minutes=1):
                                print("Statistics update skipped - cooldown period active")
                                return True
                except Exception as e:
                    print(f"Error checking last update time: {str(e)}")
                    # Continue with update if we can't check the timestamp
            
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
            
            print(f"Statistics updated successfully: {stats['total_games']} games processed")
            return True

        except Exception as e:
            print(f"Error updating statistics: {str(e)}")
            return False

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
        
        if HAS_NUMPY:
            hist, _ = np.histogram(scores, bins=bins)
            return {
                'bins': bins,
                'counts': hist.tolist()
            }
        else:
            # Manual histogram calculation if numpy is not available
            counts = [0] * (len(bins) - 1)
            for score in scores:
                for i in range(len(bins) - 1):
                    if bins[i] <= score < bins[i + 1]:
                        counts[i] += 1
                        break
                    elif score >= bins[-1]:  # Handle edge case for maximum value
                        counts[-1] += 1
                        break
            return {
                'bins': bins,
                'counts': counts
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
            
    @classmethod
    def get_combined_leaderboard(cls):
        """Get combined leaderboard with both human players and LLMs"""
        # Get human players from database
        human_players = []
        
        try:
            from utils.config import BASE_DIR
            import os
            
            db_path = os.path.join(BASE_DIR, 'logs', 'users.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create rankings table if it doesn't exist (for safety)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_rankings (
                    user_id TEXT PRIMARY KEY,
                    rank_score REAL DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    highest_streak INTEGER DEFAULT 0,
                    rank_tier TEXT DEFAULT 'Novice',
                    last_updated TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Get top human players from rankings (they already have 10+ hard games to be in rankings)
            cursor.execute('''
                SELECT r.user_id, COALESCE(u.display_name, ''), r.rank_score, r.rank_tier, 
                       r.games_played, r.wins, r.losses, r.streak
                FROM user_rankings r
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.rank_score DESC
                LIMIT 20
            ''')
            
            for row in cursor.fetchall():
                user_id, display_name, rank_score, rank_tier, games_played, wins, losses, streak = row
                
                # Use display name if available, otherwise use anonymized ID
                name = display_name if display_name else f"Player_{user_id[-6:]}"
                
                human_players.append({
                    'user_id': user_id,
                    'name': name,
                    'score': rank_score,
                    'tier': rank_tier,
                    'games_played': games_played,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': (wins / games_played) * 100 if games_played > 0 else 0,
                    'streak': streak,
                    'type': 'human'
                })
            
            conn.close()
        except Exception as e:
            print(f"Error getting human players: {str(e)}")
        
        # Get LLM data from the existing leaderboard
        llm_players = []
        
        # Data from the original LLM leaderboard
        llm_data = [
            { 'rank': 1, 'model': 'Qwen_78_Instruct', 'score': 0.35 },
            { 'rank': 2, 'model': 'Centaur_88', 'score': 0.33 },
            { 'rank': 3, 'model': 'gpt40_mini', 'score': 0.30 },
            { 'rank': 4, 'model': 'gpt40', 'score': 0.26 },
            { 'rank': 5, 'model': 'Qwen_3B_Instruct', 'score': 0.23 },
            { 'rank': 6, 'model': 'Qwen_3B', 'score': 0.21 },
            { 'rank': 7, 'model': 'Qwen_1B', 'score': 0.19 },
            { 'rank': 8, 'model': 'Qwen_7B', 'score': 0.17 },
            { 'rank': 9, 'model': 'Deepseek_R1_7B_Qwen', 'score': 0.15 },
            { 'rank': 10, 'model': 'Deepseek_R1_1B_Owen', 'score': 0.11 },
            { 'rank': 11, 'model': 'Owen_1B_Instruct', 'score': 0.09 },
            { 'rank': 12, 'model': 'Deepseek_R1_8B_Llama', 'score': 0.05 }
        ]
        
        # Convert LLM scores to be comparable with human scores
        # Assuming human scores range from 0-2000 and LLM scores from 0-1
        for llm in llm_data:
            # Scale LLM scores to human range (0-1 → 0-2000)
            scaled_score = llm['score'] * 2000
            
            # Determine tier based on scaled score
            tier = 'Novice'
            tier_thresholds = {
                'Novice': 0,
                'Apprentice': 100,
                'Adept': 250,
                'Expert': 500,
                'Master': 1000,
                'Grandmaster': 2000
            }
            
            for t, threshold in tier_thresholds.items():
                if scaled_score >= threshold:
                    tier = t
            
            llm_players.append({
                'user_id': f"llm_{llm['model'].lower()}",
                'name': f"🤖 {llm['model']}",
                'score': scaled_score,
                'tier': tier,
                'games_played': 100,  # Placeholder
                'wins': int(llm['score'] * 100),  # Approximate
                'losses': 100 - int(llm['score'] * 100),
                'win_rate': llm['score'] * 100,
                'streak': 0,  # Placeholder
                'type': 'llm'
            })
        
        # Combine and sort by win rate
        combined = human_players + llm_players
        combined.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Add ranks
        for i, player in enumerate(combined):
            player['rank'] = i + 1
        
        return combined
