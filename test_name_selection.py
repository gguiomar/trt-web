import os
import sqlite3
from utils.UserManager import UserManager

def test_name_selection_logic():
    """Test the name selection logic for users with 10+ hard games"""
    
    print("=== TESTING NAME SELECTION LOGIC ===")
    
    user_manager = UserManager()
    
    # Check users with 10+ hard games
    db_path = os.path.join('logs', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
        print(f"  {user_id}: '{display_name}' - {hard_games} hard games")
        
        # Test the name selection logic
        should_show_name_selection = display_name.startswith("Player_")
        print(f"    Should show name selection: {should_show_name_selection}")
        
        if should_show_name_selection:
            print(f"    ✅ This user would be redirected to name selection")
        else:
            print(f"    ❌ This user already has a custom name")
    
    conn.close()
    
    print(f"\n=== SUMMARY ===")
    qualifying_users = [u for u in users_with_10_plus if u[1].startswith("Player_")]
    print(f"Users qualifying for name selection: {len(qualifying_users)}")
    print(f"Users with custom names: {len(users_with_10_plus) - len(qualifying_users)}")

if __name__ == "__main__":
    test_name_selection_logic()
