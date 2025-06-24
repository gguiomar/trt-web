import os
import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from flask import request, session
from utils.config import BASE_DIR, debug_log

class UserManager:
    def __init__(self):
        self.db_path = os.path.join(BASE_DIR, 'logs', 'users.db')
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database for user management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                ip_hash TEXT,
                user_agent_hash TEXT,
                first_visit TEXT,
                last_visit TEXT,
                games_completed INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                device_type TEXT,
                browser TEXT,
                display_name TEXT DEFAULT NULL,
                persistent_token TEXT DEFAULT NULL,
                hard_games_completed INTEGER DEFAULT 0
            )
        ''')
        
        # We don't need to check for hard_games_completed column anymore
        # since it's already included in the CREATE TABLE statement above
        conn.commit()
        
        # Create user_games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                game_id TEXT,
                game_number INTEGER,
                score INTEGER,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create navigation tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS navigation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_start TIMESTAMP NOT NULL,
                session_end TIMESTAMP,
                total_duration REAL,
                device_type TEXT,
                browser TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS page_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                page TEXT NOT NULL,
                url TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                entry_method TEXT,
                time_on_page REAL,
                scroll_depth REAL DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES navigation_sessions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                page_visit_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                element_type TEXT,
                element_id TEXT,
                element_class TEXT,
                coordinates_x INTEGER,
                coordinates_y INTEGER,
                scroll_position REAL,
                link_text TEXT,
                link_href TEXT,
                link_target TEXT,
                is_external BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES navigation_sessions (id),
                FOREIGN KEY (page_visit_id) REFERENCES page_visits (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_user_id(self, ip_address, user_agent):
        """Generate a consistent user ID based on IP and User-Agent"""
        # Create a hash from IP and User-Agent
        combined = f"{ip_address}:{user_agent}"
        user_hash = hashlib.sha256(combined.encode()).hexdigest()
        return f"user_{user_hash[:16]}"
    
    def get_device_info(self, user_agent):
        """Extract device type and browser from User-Agent"""
        user_agent_lower = user_agent.lower()
        
        # Determine device type
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            device_type = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
        
        # Determine browser
        if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
            browser = 'chrome'
        elif 'firefox' in user_agent_lower:
            browser = 'firefox'
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            browser = 'safari'
        elif 'edg' in user_agent_lower:
            browser = 'edge'
        else:
            browser = 'other'
        
        return device_type, browser
    
    def get_or_create_user(self, ip_address=None, user_agent=None):
        """Get existing user or create new one"""
        if not ip_address:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
        if not user_agent:
            user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Hash sensitive data
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
        ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()
        
        user_id = self.generate_user_id(ip_address, user_agent)
        device_type, browser = self.get_device_info(user_agent)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        if user:
            # Update last visit
            cursor.execute(
                'UPDATE users SET last_visit = ? WHERE user_id = ?',
                (current_time, user_id)
            )
            returning_user = True
        else:
            # Create new user with a default display name
            default_display_name = f"Player_{user_id[-6:]}"
            cursor.execute('''
                INSERT INTO users (user_id, ip_hash, user_agent_hash, first_visit, last_visit, 
                                 games_completed, total_score, device_type, browser, display_name)
                VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
            ''', (user_id, ip_hash, ua_hash, current_time, current_time, device_type, browser, default_display_name))
            returning_user = False
        
        conn.commit()
        conn.close()
        
        return {
            'user_id': user_id,
            'ip_hash': ip_hash,
            'user_agent_hash': ua_hash,
            'returning_user': returning_user,
            'device_type': device_type,
            'browser': browser
        }
    
    def get_user_game_progress(self, user_id):
        """Get user's game progress (how many games completed out of 10)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT games_completed, total_score FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            games_completed, total_score = result
            cycle_number = games_completed // 10 + 1
            games_in_current_cycle = games_completed % 10
            
            conn.close()
            
            return {
                'games_completed': games_in_current_cycle,
                'total_score': total_score,  # Use accumulated total score
                'cycle_number': cycle_number
            }
        
        conn.close()
        return {'games_completed': 0, 'total_score': 0, 'cycle_number': 1}
    
    def record_game_completion(self, user_id, game_id, score):
        """Record a completed game for the user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if this game_id has already been recorded to prevent duplicates
        cursor.execute('SELECT COUNT(*) FROM user_games WHERE game_id = ?', (game_id,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            # Game already recorded, skip to prevent duplicate
            conn.close()
            return
        
        # Get current progress
        cursor.execute('SELECT games_completed FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            current_games = result[0]
            game_number = (current_games % 10) + 1
            
            # Insert game record
            cursor.execute('''
                INSERT INTO user_games (user_id, game_id, game_number, score, completed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, game_id, game_number, score, datetime.now(timezone.utc).isoformat()))
            
            # Update user totals
            cursor.execute('''
                UPDATE users 
                SET games_completed = games_completed + 1, 
                    total_score = total_score + ?
                WHERE user_id = ?
            ''', (score, user_id))
            
            # Check if this was a hard game and update hard_games_completed if it was
            game_mode = session.get('game_mode')
            if game_mode == 'hard':
                # Make sure the column exists before updating
                try:
                    cursor.execute('''
                        UPDATE users 
                        SET hard_games_completed = COALESCE(hard_games_completed, 0) + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                except sqlite3.OperationalError:
                    # Column doesn't exist, add it and then update
                    cursor.execute("ALTER TABLE users ADD COLUMN hard_games_completed INTEGER DEFAULT 0")
                    cursor.execute('''
                        UPDATE users 
                        SET hard_games_completed = 1
                        WHERE user_id = ?
                    ''', (user_id,))
            
            conn.commit()
        
        conn.close()
        
        # Update user ranking if they've completed at least 10 hard games
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT hard_games_completed FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            hard_games = result[0] if result else 0
        except sqlite3.OperationalError:
            # Column doesn't exist
            hard_games = 0
        
        conn.close()
        
        if hard_games >= 10:
            # Check if user has a custom name (qualified for leaderboard)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT display_name FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            display_name = result[0] if result else ""
            conn.close()
            
            # Only update ranking if user has custom name (not default Player_ name)
            if display_name and not display_name.startswith("Player_"):
                # Use complete history calculation instead of incremental update
                from utils.RankingSystem import RankingSystem
                logs_dir = os.path.dirname(self.db_path)
                RankingSystem.calculate_user_ranking_from_history(self.db_path, user_id, logs_dir)
    
    def get_user_stats(self, user_id):
        """Get comprehensive user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_info = cursor.fetchone()
        
        # Get recent games
        cursor.execute('''
            SELECT game_id, game_number, score, completed_at 
            FROM user_games 
            WHERE user_id = ? 
            ORDER BY completed_at DESC 
            LIMIT 10
        ''', (user_id,))
        recent_games = cursor.fetchall()
        
        conn.close()
        
        if user_info:
            return {
                'user_info': {
                    'user_id': user_info[0],
                    'first_visit': user_info[3],
                    'last_visit': user_info[4],
                    'games_completed': user_info[5],
                    'total_score': user_info[6],
                    'device_type': user_info[7],
                    'browser': user_info[8],
                    'display_name': user_info[9],
                    'hard_games_completed': user_info[11] if len(user_info) > 11 else 0
                },
                'recent_games': [
                    {
                        'game_id': game[0],
                        'game_number': game[1],
                        'score': game[2],
                        'completed_at': game[3]
                    } for game in recent_games
                ]
            }
        return None
        
    def update_player_name(self, user_id, display_name):
        """Update a user's display name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE users SET display_name = ? WHERE user_id = ?',
            (display_name, user_id)
        )
        
        conn.commit()
        conn.close()
        
    def get_user_by_token(self, token):
        """Get user by persistent token"""
        if not token:
            return None
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, display_name FROM users WHERE persistent_token = ?', (token,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'display_name': result[1]
            }
        return None
        
    def set_user_token(self, user_id):
        """Generate and set a persistent token for a user"""
        import secrets
        token = secrets.token_hex(16)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE users SET persistent_token = ? WHERE user_id = ?',
            (token, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return token
        
    def get_hard_games_completed(self, user_id):
        """Get the number of hard games completed by a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT hard_games_completed FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            return result[0] if result else 0
        except sqlite3.OperationalError:
            # Column doesn't exist
            cursor.execute("ALTER TABLE users ADD COLUMN hard_games_completed INTEGER DEFAULT 0")
            conn.commit()
            conn.close()
            return 0
