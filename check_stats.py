import sqlite3
import os

# Connect to the database
db_path = 'logs/users.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all human players with rankings
cursor.execute('''
    SELECT r.user_id, COALESCE(u.display_name, ''), r.rank_score, r.rank_tier, 
           r.games_played, r.wins, r.losses, r.streak
    FROM user_rankings r
    JOIN users u ON r.user_id = u.user_id
    ORDER BY r.rank_score DESC
''')

print("Human Players Leaderboard:")
for row in cursor.fetchall():
    user_id, name, score, tier, games, wins, losses, streak = row
    win_rate = (wins / games * 100) if games > 0 else 0
    display_name = name if name else f"Player_{user_id[-6:]}"
    print(f"{display_name}: Score={score}, Tier={tier}, Games={games}, Win Rate={win_rate:.1f}%")

conn.close()
