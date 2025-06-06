import os
import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from flask import request
from utils.config import BASE_DIR

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
                browser TEXT
            )
        ''')
        
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
            # Create new user
            cursor.execute('''
                INSERT INTO users (user_id, ip_hash, user_agent_hash, first_visit, last_visit, 
                                 games_completed, total_score, device_type, browser)
                VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
            ''', (user_id, ip_hash, ua_hash, current_time, current_time, device_type, browser))
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
            
            conn.commit()
        
        conn.close()
    
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
                    'browser': user_info[8]
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
