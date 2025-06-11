#!/usr/bin/env python3
"""
Test script to demonstrate the reset functionality
"""

from utils.DataReset import reset_all_data, reset_statistics_only, get_data_summary

def main():
    print("=" * 60)
    print("VST Application - Reset Functionality Test")
    print("=" * 60)
    print()
    
    # Get current data summary
    print("📊 Current Data Summary:")
    summary = get_data_summary()
    
    print(f"   User Database: {'✓' if summary['user_database']['exists'] else '✗'}")
    print(f"   Game Logs: {summary['game_logs']['count']} files")
    print(f"   Session Files: {summary['session_files']['count']} files")
    print(f"   Statistics Cache: {'✓' if summary['statistics_cache']['exists'] else '✗'}")
    print()
    
    # Example usage (commented out for safety)
    print("🔧 Example Usage:")
    print()
    print("# Reset everything:")
    print("from utils.DataReset import reset_all_data")
    print("result = reset_all_data(verbose=True)")
    print("print(f'Success: {result[\"success\"]}')")
    print()
    print("# Reset only statistics:")
    print("from utils.DataReset import reset_statistics_only")
    print("result = reset_statistics_only(verbose=True)")
    print("print(f'Success: {result[\"success\"]}')")
    print()
    print("# Get data summary:")
    print("from utils.DataReset import get_data_summary")
    print("summary = get_data_summary()")
    print("print(f'Game logs: {summary[\"game_logs\"][\"count\"]}')")
    print()
    
    print("⚠️  To actually reset data, use:")
    print("   python reset_player_data.py")
    print("   python reset_player_data.py --force")
    print("   python reset_player_data.py --stats-only")

if __name__ == '__main__':
    main()
