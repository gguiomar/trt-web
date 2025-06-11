#!/usr/bin/env python3
# Alternative shebang for conda environment:
# #!/home/vst/miniconda3/envs/vst/bin/python
"""
Reset Player Data Script
========================

This script completely removes all player data from the VST application:
- User database (profiles, progress, game records)
- Game log files
- Active sessions
- Statistics cache

Usage:
    python reset_player_data.py
    python reset_player_data.py --force
    python reset_player_data.py --stats-only
"""

import os
import sys
import glob
import argparse
from datetime import datetime

def confirm_reset():
    """Ask user for confirmation before proceeding"""
    print("⚠️  WARNING: This will permanently delete ALL player data!")
    print("   - User profiles and progress")
    print("   - All game session logs")
    print("   - Active player sessions")
    print("   - Statistics cache")
    print()
    
    response = input("Are you sure you want to continue? Type 'DELETE' to confirm: ")
    return response.strip() == 'DELETE'

def delete_user_database():
    """Delete the SQLite user database"""
    db_path = os.path.join('logs', 'users.db')
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"✓ Deleted user database: {db_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to delete user database: {e}")
            return False
    else:
        print(f"ℹ️  User database not found: {db_path}")
        return True

def delete_game_logs():
    """Delete all game log JSON files"""
    logs_pattern = os.path.join('logs', 'game_*.json')
    game_files = glob.glob(logs_pattern)
    
    deleted_count = 0
    failed_count = 0
    
    for file_path in game_files:
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception as e:
            print(f"✗ Failed to delete {file_path}: {e}")
            failed_count += 1
    
    if deleted_count > 0:
        print(f"✓ Deleted {deleted_count} game log files")
    else:
        print("ℹ️  No game log files found")
    
    if failed_count > 0:
        print(f"✗ Failed to delete {failed_count} game log files")
    
    return failed_count == 0

def delete_session_files():
    """Delete all Flask session files"""
    session_dir = 'flask_session'
    
    if not os.path.exists(session_dir):
        print(f"ℹ️  Session directory not found: {session_dir}")
        return True
    
    session_files = glob.glob(os.path.join(session_dir, '*'))
    deleted_count = 0
    failed_count = 0
    
    for file_path in session_files:
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete session file {file_path}: {e}")
                failed_count += 1
    
    if deleted_count > 0:
        print(f"✓ Deleted {deleted_count} session files")
    else:
        print("ℹ️  No session files found")
    
    if failed_count > 0:
        print(f"✗ Failed to delete {failed_count} session files")
    
    return failed_count == 0

def delete_statistics_cache():
    """Delete the statistics cache file"""
    stats_path = os.path.join('static', 'stats.json')
    
    if os.path.exists(stats_path):
        try:
            os.remove(stats_path)
            print(f"✓ Deleted statistics cache: {stats_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to delete statistics cache: {e}")
            return False
    else:
        print(f"ℹ️  Statistics cache not found: {stats_path}")
        return True

def reset_all_player_data():
    """Reset all player data"""
    print("🧹 Starting complete player data reset...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    # Delete user database
    success &= delete_user_database()
    
    # Delete game logs
    success &= delete_game_logs()
    
    # Delete session files
    success &= delete_session_files()
    
    # Delete statistics cache
    success &= delete_statistics_cache()
    
    print()
    if success:
        print("🎉 Player data reset completed successfully!")
        print("   All user data, game logs, sessions, and statistics have been removed.")
    else:
        print("⚠️  Player data reset completed with some errors.")
        print("   Check the output above for details.")
    
    return success

def reset_statistics_only():
    """Reset only the statistics cache"""
    print("📊 Resetting statistics cache only...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = delete_statistics_cache()
    
    print()
    if success:
        print("🎉 Statistics reset completed successfully!")
    else:
        print("⚠️  Statistics reset failed.")
    
    return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Reset VST application player data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_player_data.py              # Interactive reset with confirmation
  python reset_player_data.py --force      # Reset without confirmation
  python reset_player_data.py --stats-only # Reset only statistics cache
        """
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Skip confirmation prompt and proceed directly'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true', 
        help='Reset only statistics cache, keep user data'
    )
    
    args = parser.parse_args()
    
    # Change to script directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("VST Application - Player Data Reset")
    print("=" * 60)
    print()
    
    if args.stats_only:
        # Reset only statistics
        if not args.force:
            response = input("Reset statistics cache? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
        
        success = reset_statistics_only()
    else:
        # Full reset
        if not args.force:
            if not confirm_reset():
                print("Operation cancelled.")
                return
        
        success = reset_all_player_data()
    
    print()
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
