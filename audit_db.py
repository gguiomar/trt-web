import os
import sqlite3
import json

# Connect to the database
db_path = os.path.join('logs', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== USER DATA AUDIT ===")

# Check users with their game completion data
cursor.execute("""
    SELECT user_id, display_name, games_completed, hard_games_completed, total_score 
    FROM users 
    ORDER BY games_completed DESC
""")
users = cursor.fetchall()

print(f"\nFound {len(users)} users:")
for user in users:
    user_id, display_name, games_completed, hard_games_completed, total_score = user
    print(f"  {user_id}: {display_name} - Games: {games_completed}, Hard: {hard_games_completed}, Score: {total_score}")

# Check user_games table
cursor.execute("SELECT COUNT(*) FROM user_games")
total_games = cursor.fetchone()[0]
print(f"\nTotal games in user_games table: {total_games}")

# Check for hard games in user_games (we need to cross-reference with game logs)
cursor.execute("""
    SELECT user_id, COUNT(*) as game_count, SUM(score) as total_score
    FROM user_games 
    GROUP BY user_id 
    ORDER BY game_count DESC
""")
game_stats = cursor.fetchall()

print(f"\nGame completion stats from user_games:")
for stat in game_stats:
    user_id, game_count, total_score = stat
    print(f"  {user_id}: {game_count} games, total score: {total_score}")

# Check user_rankings table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_rankings'")
rankings_exists = cursor.fetchone()

if rankings_exists:
    cursor.execute("SELECT COUNT(*) FROM user_rankings")
    rankings_count = cursor.fetchone()[0]
    print(f"\nUser rankings entries: {rankings_count}")
    
    if rankings_count > 0:
        cursor.execute("""
            SELECT user_id, rank_score, games_played, wins, losses, rank_tier
            FROM user_rankings 
            ORDER BY rank_score DESC
        """)
        rankings = cursor.fetchall()
        print("Top rankings:")
        for ranking in rankings[:10]:
            user_id, rank_score, games_played, wins, losses, rank_tier = ranking
            print(f"  {user_id}: {rank_score} pts, {games_played} games, {wins}W-{losses}L, {rank_tier}")
else:
    print("\nuser_rankings table does not exist")

conn.close()

print("\n=== GAME LOGS AUDIT ===")

# Check game logs to count hard games
logs_dir = 'logs'
hard_games_by_user = {}
total_game_files = 0

if os.path.exists(logs_dir):
    for filename in os.listdir(logs_dir):
        if filename.startswith('game_') and filename.endswith('.json'):
            total_game_files += 1
            filepath = os.path.join(logs_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    game_data = json.load(f)
                    user_id = game_data.get('user_id')
                    game_mode = game_data.get('game_mode', 'normal')
                    
                    if user_id:
                        if user_id not in hard_games_by_user:
                            hard_games_by_user[user_id] = {'total': 0, 'hard': 0, 'easy': 0, 'normal': 0}
                        
                        hard_games_by_user[user_id]['total'] += 1
                        hard_games_by_user[user_id][game_mode] += 1
                        
            except Exception as e:
                print(f"Error reading {filepath}: {str(e)}")

print(f"Found {total_game_files} game log files")
print(f"Hard games by user (from logs):")
for user_id, counts in hard_games_by_user.items():
    if counts['hard'] > 0:
        print(f"  {user_id}: {counts['hard']} hard, {counts['easy']} easy, {counts['normal']} normal, {counts['total']} total")

# Check games subdirectory too
games_subdir = os.path.join(logs_dir, 'games')
if os.path.exists(games_subdir):
    subdir_files = 0
    for filename in os.listdir(games_subdir):
        if filename.startswith('game_') and filename.endswith('.json'):
            subdir_files += 1
    print(f"Found {subdir_files} additional game files in games subdirectory")
