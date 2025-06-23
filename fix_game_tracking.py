import os
import sqlite3
import json
from datetime import datetime, timezone

def fix_hard_games_tracking():
    """Fix the hard_games_completed tracking by recalculating from game logs"""
    
    print("=== FIXING HARD GAMES TRACKING ===")
    
    # Connect to database
    db_path = os.path.join('logs', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count hard games from logs
    logs_dir = 'logs'
    hard_games_by_user = {}
    
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            if filename.startswith('game_') and filename.endswith('.json'):
                filepath = os.path.join(logs_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        game_data = json.load(f)
                        user_id = game_data.get('user_id')
                        game_mode = game_data.get('game_mode', 'normal')
                        
                        if user_id and game_mode == 'hard':
                            if user_id not in hard_games_by_user:
                                hard_games_by_user[user_id] = 0
                            hard_games_by_user[user_id] += 1
                            
                except Exception as e:
                    print(f"Error reading {filepath}: {str(e)}")
    
    # Update database with correct hard game counts
    for user_id, hard_count in hard_games_by_user.items():
        cursor.execute(
            'UPDATE users SET hard_games_completed = ? WHERE user_id = ?',
            (hard_count, user_id)
        )
        print(f"Updated {user_id}: {hard_count} hard games")
    
    conn.commit()
    conn.close()
    print("Hard games tracking fixed!")

def fix_user_rankings():
    """Fix user rankings by recalculating from game logs"""
    
    print("\n=== FIXING USER RANKINGS ===")
    
    db_path = os.path.join('logs', 'users.db')
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
    
    # Clear existing rankings
    cursor.execute('DELETE FROM user_rankings')
    
    # Collect game results by user
    logs_dir = 'logs'
    user_games = {}
    
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            if filename.startswith('game_') and filename.endswith('.json'):
                filepath = os.path.join(logs_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        game_data = json.load(f)
                        user_id = game_data.get('user_id')
                        game_mode = game_data.get('game_mode', 'normal')
                        
                        # Only count hard games for rankings
                        if user_id and game_mode == 'hard':
                            if user_id not in user_games:
                                user_games[user_id] = []
                            
                            # Determine if game was won
                            won = False
                            if 'final_result' in game_data and game_data['final_result']:
                                won = game_data['final_result'].get('correct', False)
                            
                            user_games[user_id].append({
                                'won': won,
                                'start_time': game_data.get('start_time', '')
                            })
                            
                except Exception as e:
                    print(f"Error reading {filepath}: {str(e)}")
    
    # Calculate rankings for each user
    TIERS = {
        'Novice': 0,
        'Apprentice': 100,
        'Adept': 250,
        'Expert': 500,
        'Master': 1000,
        'Grandmaster': 2000
    }
    
    for user_id, games in user_games.items():
        if len(games) >= 10:  # Only rank users with 10+ hard games
            # Sort games by start time
            games.sort(key=lambda x: x['start_time'])
            
            rank_score = 0
            wins = 0
            losses = 0
            current_streak = 0
            highest_streak = 0
            
            for game in games:
                if game['won']:
                    wins += 1
                    current_streak += 1
                    # Award points for win (base points + streak bonus)
                    points_gained = 25 + (5 * current_streak)
                    rank_score += points_gained
                    highest_streak = max(highest_streak, current_streak)
                else:
                    losses += 1
                    current_streak = 0
                    # Lose points for loss
                    rank_score = max(0, rank_score - 10)
            
            # Determine tier
            tier = 'Novice'
            for t, threshold in TIERS.items():
                if rank_score >= threshold:
                    tier = t
            
            # Insert ranking
            cursor.execute('''
                INSERT INTO user_rankings
                (user_id, rank_score, games_played, wins, losses, streak, highest_streak, rank_tier, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, rank_score, len(games), wins, losses, current_streak, 
                highest_streak, tier, datetime.now(timezone.utc).isoformat()
            ))
            
            print(f"Ranked {user_id}: {rank_score} pts, {wins}W-{losses}L, {tier}")
    
    conn.commit()
    conn.close()
    print("User rankings fixed!")

def fix_name_selection_logic():
    """Fix the name selection logic in app.py"""
    
    print("\n=== FIXING NAME SELECTION LOGIC ===")
    
    # The fix will be applied to app.py directly
    print("Name selection logic needs to be updated in app.py")
    print("Current logic checks for NULL/empty display names")
    print("Should check for default 'Player_' names instead")

if __name__ == "__main__":
    fix_hard_games_tracking()
    fix_user_rankings()
    fix_name_selection_logic()
    
    print("\n=== VERIFICATION ===")
    
    # Verify the fixes
    db_path = os.path.join('logs', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check updated hard games
    cursor.execute("""
        SELECT user_id, display_name, hard_games_completed 
        FROM users 
        WHERE hard_games_completed >= 10
        ORDER BY hard_games_completed DESC
    """)
    users_with_10_plus = cursor.fetchall()
    
    print(f"\nUsers with 10+ hard games:")
    for user in users_with_10_plus:
        user_id, display_name, hard_games = user
        print(f"  {user_id}: {display_name} - {hard_games} hard games")
    
    # Check rankings
    cursor.execute("""
        SELECT user_id, rank_score, games_played, wins, losses, rank_tier
        FROM user_rankings 
        ORDER BY rank_score DESC
    """)
    rankings = cursor.fetchall()
    
    print(f"\nTop rankings:")
    for ranking in rankings:
        user_id, rank_score, games_played, wins, losses, rank_tier = ranking
        print(f"  {user_id}: {rank_score} pts, {games_played} games, {wins}W-{losses}L, {rank_tier}")
    
    conn.close()
