import os
import json
from datetime import datetime
import uuid

def test_file_permissions():
    print("\n=== Testing File Permissions ===")
    
    # Get current directory and process info
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    print(f"Running as user ID: {os.getuid()}")
    print(f"Running as group ID: {os.getgid()}")
    
    # Create logs directory
    logs_dir = os.path.join(current_dir, 'logs')
    print(f"\nTrying to create/access logs directory: {logs_dir}")
    
    try:
        os.makedirs(logs_dir, mode=0o775, exist_ok=True)
        print("✓ Created/verified logs directory")
        
        # Test write permissions with a simple file
        test_file = os.path.join(logs_dir, 'test.txt')
        print(f"\nTrying to write test file: {test_file}")
        with open(test_file, 'w') as f:
            f.write('test')
        print("✓ Wrote test file successfully")
        
        # Read the test file
        print("Trying to read test file")
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"✓ Read test file successfully: content='{content}'")
        
        # Remove test file
        os.remove(test_file)
        print("✓ Removed test file successfully")
        
        # Create a JSON log file
        game_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        json_filename = f"game_{game_id}_{timestamp}.json"
        json_filepath = os.path.join(logs_dir, json_filename)
        
        print(f"\nTrying to create JSON log file: {json_filepath}")
        log_data = {
            'game_id': game_id,
            'timestamp': datetime.utcnow().isoformat(),
            'test_data': 'This is a test log entry'
        }
        
        with open(json_filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        print("✓ Created JSON log file successfully")
        
        # Read the JSON file back
        print("Trying to read JSON file")
        with open(json_filepath, 'r') as f:
            loaded_data = json.load(f)
        print(f"✓ Read JSON file successfully: {loaded_data}")
        
        # Show file permissions
        stats = os.stat(json_filepath)
        print(f"\nFile permissions:")
        print(f"Mode: {oct(stats.st_mode)[-3:]}")
        print(f"UID: {stats.st_uid}")
        print(f"GID: {stats.st_gid}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_file_permissions()