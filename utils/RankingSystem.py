import sqlite3
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
        
        # Update win/loss record
        if game_won:
            wins += 1
            streak += 1
            # Award points for win (base points + streak bonus)
            points_gained = 25 + (5 * streak)
            rank_score += points_gained
        else:
            losses += 1
            # Lose points for loss (more points lost for higher ranks)
            tier_multiplier = list(cls.TIERS.keys()).index(rank_tier) + 1
            points_lost = 10 * tier_multiplier
            rank_score = max(0, rank_score - points_lost)
            # Reset streak on loss
            streak = 0
        
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
