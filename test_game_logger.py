#!/usr/bin/env python3
import os
import json
import uuid
from datetime import datetime
import traceback
import random

class TestGameLogger:
    def __init__(self):
        # Get absolute path
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.debug_log_path = os.path.join(self.base_dir, 'debug_test.log')
        
        print(f"Base directory: {self.base_dir}")
        print(f"Logs directory: {self.logs_dir}")
        
        # Log initialization
        self.debug_log("Starting test run")
        self.debug_log(f"Process running as UID: {os.getuid()}, GID: {os.getgid()}")
        
        # Ensure logs directory exists
        self.create_logs_dir()

    def debug_log(self, message):
        """Write a debug message to the log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        log_message = f"{timestamp} - {message}"
        print(log_message)  # Print to console
        try:
            with open(self.debug_log_path, 'a') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"Error writing to debug log: {e}")

    def create_logs_dir(self):
        """Create and check permissions of logs directory"""
        try:
            os.makedirs(self.logs_dir, mode=0o775, exist_ok=True)
            self.debug_log(f"Created/verified logs directory: {self.logs_dir}")
            
            # Check directory permissions
            stats = os.stat(self.logs_dir)
            mode = oct(stats.st_mode)[-3:]
            self.debug_log(f"Logs directory permissions: {mode}")
            
            # Test write permissions
            test_file = os.path.join(self.logs_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.chmod(test_file, 0o664)
            self.debug_log(f"Successfully wrote test file: {test_file}")
            
            # Clean up test file
            os.remove(test_file)
            self.debug_log("Removed test file")
            
        except Exception as e:
            self.debug_log(f"Error setting up logs directory: {str(e)}")
            self.debug_log(traceback.format_exc())
            raise

    def create_game_log(self):
        """Test creating a game log file"""
        try:
            game_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"game_{game_id}_{timestamp}.json"
            filepath = os.path.join(self.logs_dir, filename)
            
            self.debug_log(f"Creating game log: {filepath}")
            
            # Create sample game data
            log_data = {
                'game_id': game_id,
                'start_time': datetime.utcnow().isoformat(),
                'choices': [],
                'test_data': {
                    'rounds': 5,
                    'biased_quadrant': random.randint(0, 3),
                    'colors': ['RED', 'GREEN']
                }
            }
            
            # Write the file
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            os.chmod(filepath, 0o664)
            
            self.debug_log("Game log created successfully")
            
            # Verify file exists and is readable
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    loaded_data = json.load(f)
                self.debug_log("Successfully verified file is readable and contains valid JSON")
                
                # Check file permissions
                stats = os.stat(filepath)
                mode = oct(stats.st_mode)[-3:]
                self.debug_log(f"File permissions: {mode}")
            
            return filepath
            
        except Exception as e:
            self.debug_log(f"Error creating game log: {str(e)}")
            self.debug_log(traceback.format_exc())
            raise

    def simulate_choices(self, game_log_path):
        """Simulate adding some choices to the game log"""
        try:
            self.debug_log(f"Adding test choices to: {game_log_path}")
            
            # Read existing log
            with open(game_log_path, 'r') as f:
                log_data = json.load(f)
            
            # Add some test choices
            for i in range(3):
                choice = {
                    'round': i,
                    'quadrant': random.randint(0, 3),
                    'color': random.choice(['RED', 'GREEN']),
                    'timestamp': datetime.utcnow().isoformat()
                }
                log_data['choices'].append(choice)
            
            # Write updated log
            with open(game_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.debug_log("Successfully added test choices")
            
        except Exception as e:
            self.debug_log(f"Error adding choices: {str(e)}")
            self.debug_log(traceback.format_exc())
            raise

def main():
    tester = TestGameLogger()
    
    # Test game log creation
    game_log_path = tester.create_game_log()
    
    # Test adding choices
    tester.simulate_choices(game_log_path)
    
    print("\nTest complete! Check debug_test.log for detailed output.")

if __name__ == "__main__":
    main()