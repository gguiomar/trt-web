import sqlite3
import json
import os
from datetime import datetime, timezone

class RankingSystem:
    """
    Handles player rankings for the leaderboard system.
    Players are ranked based on their performance in hard games.
    """
    
    # Ranking tiers with their score thresholds
    TIERS = {
        'Novice': 0,
        'Apprentice': 100,
        'Adept': 250,
        'Expert': 500,
        'Master': 1000,
        'Grandmaster': 2000
    }
    
    @classmethod
    def update_user_ranking(cls, db_path, user_id, game_data):
        """
        Update a user's ranking based on their game performance.
        Called after a user completes a hard game.
        
        Args:
            db_path: Path to the SQLite database
            user_id: The user's ID
            game_data: The completed game data
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create rankings table if it doesn't exist
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
        
        # Get current ranking data for user
        cursor.execute('''
            SELECT rank_score, games_played, wins, losses, streak, highest_streak, rank_tier
            FROM user_rankings
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            rank_score, games_played, wins, losses, streak, highest_streak, rank_tier = result
        else:
            # Initialize new user ranking
            rank_score = 0
            games_played = 0
            wins = 0
            losses = 0
            streak = 0
            highest_streak = 0
            rank_tier = 'Novice'
        
        # Determine if the game was won
        game_won = False
        if 'final_result' in game_data and game_data['final_result']:
            if game_data['final_result'].get('correct', False):
                game_won = True
        
        # Update ranking data
        games_played += 1
        
        # Update win/loss record and use actual game scores
        if game_won:
            wins += 1
            streak += 1
            # Use actual game score (+100 for win)
            rank_score += 100
        else:
            losses += 1
            # Use actual game score (-100 for loss)
            rank_score -= 100
            # Reset streak on loss
            streak = 0
        
        # Ensure score doesn't go below 0
        rank_score = max(0, rank_score)
        
        # Update highest streak if current streak is higher
        highest_streak = max(highest_streak, streak)
        
        # Determine rank tier based on score
        new_tier = 'Novice'
        for tier, threshold in cls.TIERS.items():
            if rank_score >= threshold:
                new_tier = tier
        
        # Update database
        cursor.execute('''
            INSERT OR REPLACE INTO user_rankings
            (user_id, rank_score, games_played, wins, losses, streak, highest_streak, rank_tier, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, rank_score, games_played, wins, losses, streak, highest_streak, 
            new_tier, datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'user_id': user_id,
            'rank_score': rank_score,
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'streak': streak,
            'highest_streak': highest_streak,
            'rank_tier': new_tier
        }
    
    @classmethod
    def calculate_user_ranking_from_history(cls, db_path, user_id, logs_dir):
        """
        Calculate a user's complete ranking from their game history.
        This is used for retroactive ranking calculation.
        
        Args:
            db_path: Path to the SQLite database
            user_id: The user's ID
            logs_dir: Directory containing game log files
            
        Returns:
            Dictionary with calculated ranking data or None if no games found
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get user's actual total score and hard games from users table
        cursor.execute('''
            SELECT total_score, hard_games_completed 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        user_result = cursor.fetchone()
        if not user_result:
            conn.close()
            return None
            
        total_score, hard_games_completed = user_result
        
        # Find all hard game files for this user to count wins/losses
        game_files = []
        
        # Check main logs directory
        if os.path.exists(logs_dir):
            for filename in os.listdir(logs_dir):
                if filename.startswith('game_') and filename.endswith('.json'):
                    filepath = os.path.join(logs_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            game_data = json.load(f)
                            # Check if this game belongs to the user and is a hard game
                            if (game_data.get('user_id') == user_id and 
                                game_data.get('game_mode') == 'hard' and
                                game_data.get('final_result')):
                                game_files.append((filepath, game_data))
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
                            # Check if this game belongs to the user and is a hard game
                            if (game_data.get('user_id') == user_id and 
                                game_data.get('game_mode') == 'hard' and
                                game_data.get('final_result')):
                                game_files.append((filepath, game_data))
                    except Exception as e:
                        print(f"Error reading {filepath}: {str(e)}")
        
        if not game_files:
            conn.close()
            return None
        
        # Sort games by completion time
        game_files.sort(key=lambda x: x[1].get('completion_time', ''))
        
        # Count wins and losses, calculate streaks
        games_played = len(game_files)
        wins = 0
        losses = 0
        streak = 0
        highest_streak = 0
        
        for filepath, game_data in game_files:
            # Determine if the game was won
            game_won = False
            if game_data.get('final_result', {}).get('correct', False):
                game_won = True
            
            # Update win/loss record
            if game_won:
                wins += 1
                streak += 1
                highest_streak = max(highest_streak, streak)
            else:
                losses += 1
                streak = 0
        
        # Use the actual total_score from users table as rank_score
        rank_score = max(0, total_score)  # Ensure score doesn't go below 0
        
        # Determine rank tier based on score
        rank_tier = 'Novice'
        for tier, threshold in cls.TIERS.items():
            if rank_score >= threshold:
                rank_tier = tier
        
        # Create rankings table if it doesn't exist
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
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_rankings
            (user_id, rank_score, games_played, wins, losses, streak, highest_streak, rank_tier, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, rank_score, games_played, wins, losses, streak, highest_streak, 
            rank_tier, datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'user_id': user_id,
            'rank_score': rank_score,
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'streak': streak,
            'highest_streak': highest_streak,
            'rank_tier': rank_tier
        }
    
    @classmethod
    def update_all_qualified_players(cls, db_path, logs_dir):
        """
        Update rankings for all players who qualify for the leaderboard.
        This scans all users with 10+ hard games and names, and ensures their rankings are up to date.
        
        Args:
            db_path: Path to the SQLite database
            logs_dir: Directory containing game log files
            
        Returns:
            Dictionary with update results
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find all users who qualify for the leaderboard (10+ hard games and have names)
        cursor.execute('''
            SELECT user_id, display_name, hard_games_completed
            FROM users 
            WHERE hard_games_completed >= 10 
            AND display_name IS NOT NULL 
            AND display_name != ''
            AND NOT display_name LIKE 'Player_%'
        ''')
        
        qualified_users = cursor.fetchall()
        conn.close()
        
        updated_count = 0
        failed_count = 0
        results = []
        
        for user_id, display_name, hard_games in qualified_users:
            try:
                # Calculate ranking from complete game history
                ranking_data = cls.calculate_user_ranking_from_history(db_path, user_id, logs_dir)
                
                if ranking_data:
                    results.append({
                        'user_id': user_id,
                        'display_name': display_name,
                        'hard_games_completed': hard_games,
                        'ranking_data': ranking_data,
                        'status': 'updated'
                    })
                    updated_count += 1
                else:
                    results.append({
                        'user_id': user_id,
                        'display_name': display_name,
                        'hard_games_completed': hard_games,
                        'ranking_data': None,
                        'status': 'no_games_found'
                    })
                    
            except Exception as e:
                results.append({
                    'user_id': user_id,
                    'display_name': display_name,
                    'hard_games_completed': hard_games,
                    'error': str(e),
                    'status': 'failed'
                })
                failed_count += 1
        
        return {
            'total_qualified': len(qualified_users),
            'updated_count': updated_count,
            'failed_count': failed_count,
            'results': results
        }
    
    @classmethod
    def get_user_ranking(cls, db_path, user_id):
        """
        Get a user's current ranking data.
        
        Args:
            db_path: Path to the SQLite database
            user_id: The user's ID
            
        Returns:
            Dictionary with ranking data or None if user has no ranking
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rank_score, games_played, wins, losses, streak, highest_streak, rank_tier, last_updated
            FROM user_rankings
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            rank_score, games_played, wins, losses, streak, highest_streak, rank_tier, last_updated = result
            
            return {
                'user_id': user_id,
                'rank_score': rank_score,
                'games_played': games_played,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / games_played * 100) if games_played > 0 else 0,
                'streak': streak,
                'highest_streak': highest_streak,
                'rank_tier': rank_tier,
                'last_updated': last_updated
            }
        
        return None
    
    @classmethod
    def get_leaderboard(cls, db_path, limit=20):
        """
        Get the current leaderboard of top players.
        
        Args:
            db_path: Path to the SQLite database
            limit: Maximum number of players to return
            
        Returns:
            List of dictionaries with player ranking data
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.user_id, COALESCE(u.display_name, ''), r.rank_score, r.games_played, r.wins, 
                   r.losses, r.streak, r.highest_streak, r.rank_tier
            FROM user_rankings r
            LEFT JOIN users u ON r.user_id = u.user_id
            ORDER BY r.rank_score DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, row in enumerate(results):
            user_id, display_name, rank_score, games_played, wins, losses, streak, highest_streak, rank_tier = row
            
            # Use display name if available, otherwise use anonymized ID
            name = display_name if display_name else f"Player_{user_id[-6:]}"
            
            leaderboard.append({
                'rank': i + 1,
                'user_id': user_id,
                'name': name,
                'score': rank_score,
                'games_played': games_played,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / games_played * 100) if games_played > 0 else 0,
                'streak': streak,
                'highest_streak': highest_streak,
                'tier': rank_tier
            })
        
        return leaderboard
