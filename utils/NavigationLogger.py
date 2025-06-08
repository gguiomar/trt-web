import os
import sqlite3
from datetime import datetime, timezone
from utils.config import BASE_DIR

class NavigationLogger:
    def __init__(self):
        self.db_path = os.path.join(BASE_DIR, 'logs', 'users.db')
    
    def init_user_session(self, user_id, user_metadata):
        """Initialize a new navigation session for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        try:
            cursor.execute('''
                INSERT INTO navigation_sessions (user_id, session_start, device_type, browser)
                VALUES (?, ?, ?, ?)
            ''', (user_id, current_time, user_metadata.get('device_type'), user_metadata.get('browser')))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return f"session_{session_id}_{current_time}"
        except Exception as e:
            print(f"Error creating navigation session: {str(e)}")
            conn.close()
            return None
    
    def log_page_visit(self, user_id, page_data):
        """Log a page visit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the most recent session for this user
            cursor.execute('''
                SELECT id FROM navigation_sessions 
                WHERE user_id = ? AND session_end IS NULL 
                ORDER BY session_start DESC 
                LIMIT 1
            ''', (user_id,))
            
            session_result = cursor.fetchone()
            if not session_result:
                conn.close()
                return False
            
            session_id = session_result[0]
            current_time = datetime.now(timezone.utc).isoformat()
            
            # Update time_on_page for the previous page visit in this session
            cursor.execute('''
                SELECT id, timestamp FROM page_visits 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (session_id,))
            
            prev_visit = cursor.fetchone()
            if prev_visit:
                prev_id, prev_timestamp = prev_visit
                prev_time = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                current_time_obj = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                time_diff = (current_time_obj - prev_time).total_seconds()
                
                cursor.execute('''
                    UPDATE page_visits 
                    SET time_on_page = ? 
                    WHERE id = ?
                ''', (time_diff, prev_id))
            
            # Insert new page visit
            cursor.execute('''
                INSERT INTO page_visits (session_id, page, url, timestamp, entry_method)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, page_data.get('page'), page_data.get('url'), 
                  current_time, page_data.get('entry_method', 'direct')))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error logging page visit: {str(e)}")
            conn.close()
            return False
    
    def log_interaction(self, user_id, interaction_data):
        """Log user interaction (click, scroll, link click, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the most recent session and page visit for this user
            cursor.execute('''
                SELECT ns.id, pv.id 
                FROM navigation_sessions ns
                LEFT JOIN page_visits pv ON ns.id = pv.session_id
                WHERE ns.user_id = ? AND ns.session_end IS NULL
                ORDER BY ns.session_start DESC, pv.timestamp DESC
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result or not result[1]:  # No session or no page visit
                conn.close()
                return False
            
            session_id, page_visit_id = result
            current_time = datetime.now(timezone.utc).isoformat()
            
            # Extract coordinates
            coordinates = interaction_data.get('coordinates', {})
            coord_x = coordinates.get('x') if coordinates else None
            coord_y = coordinates.get('y') if coordinates else None
            
            # Insert interaction
            cursor.execute('''
                INSERT INTO interactions (
                    session_id, page_visit_id, type, timestamp, element_type, 
                    element_id, element_class, coordinates_x, coordinates_y, 
                    scroll_position, link_text, link_href, link_target, is_external
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, page_visit_id, interaction_data.get('type'), current_time,
                interaction_data.get('element_type'), interaction_data.get('element_id'),
                interaction_data.get('element_class'), coord_x, coord_y,
                interaction_data.get('scroll_position'), interaction_data.get('link_text'),
                interaction_data.get('link_href'), interaction_data.get('link_target'),
                interaction_data.get('is_external', False)
            ))
            
            # Update scroll depth for page visit if it's a scroll event
            if interaction_data.get('type') == 'scroll':
                scroll_depth = interaction_data.get('scroll_depth', 0)
                cursor.execute('''
                    UPDATE page_visits 
                    SET scroll_depth = MAX(scroll_depth, ?)
                    WHERE id = ?
                ''', (scroll_depth, page_visit_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error logging interaction: {str(e)}")
            conn.close()
            return False
    
    def end_session(self, user_id):
        """End the current navigation session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            
            # Get the most recent open session
            cursor.execute('''
                SELECT id, session_start FROM navigation_sessions 
                WHERE user_id = ? AND session_end IS NULL 
                ORDER BY session_start DESC 
                LIMIT 1
            ''', (user_id,))
            
            session_result = cursor.fetchone()
            if not session_result:
                conn.close()
                return False
            
            session_id, session_start = session_result
            
            # Calculate total duration
            start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            total_duration = (end_time - start_time).total_seconds()
            
            # Update the last page visit's time_on_page
            cursor.execute('''
                SELECT id, timestamp FROM page_visits 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (session_id,))
            
            last_visit = cursor.fetchone()
            if last_visit:
                last_id, last_timestamp = last_visit
                last_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                time_diff = (end_time - last_time).total_seconds()
                
                cursor.execute('''
                    UPDATE page_visits 
                    SET time_on_page = ? 
                    WHERE id = ?
                ''', (time_diff, last_id))
            
            # End the session
            cursor.execute('''
                UPDATE navigation_sessions 
                SET session_end = ?, total_duration = ?
                WHERE id = ?
            ''', (current_time, total_duration, session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error ending session: {str(e)}")
            conn.close()
            return False
