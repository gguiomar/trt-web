"""
Data Reset Utility Module
========================

This module provides functions to reset various types of player data
in the VST application. Can be imported and used by other scripts.

Usage:
    from utils.DataReset import reset_all_data, reset_statistics_only
    
    # Reset everything
    success = reset_all_data()
    
    # Reset only statistics
    success = reset_statistics_only()
"""

import os
import glob
from datetime import datetime

def delete_user_database(base_dir='.'):
    """
    Delete the SQLite user database
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        
    Returns:
        bool: True if successful, False otherwise
    """
    db_path = os.path.join(base_dir, 'logs', 'users.db')
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            return True
        except Exception:
            return False
    return True

def delete_game_logs(base_dir='.'):
    """
    Delete all game log JSON files
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        
    Returns:
        tuple: (success: bool, deleted_count: int, failed_count: int)
    """
    logs_pattern = os.path.join(base_dir, 'logs', 'game_*.json')
    game_files = glob.glob(logs_pattern)
    
    deleted_count = 0
    failed_count = 0
    
    for file_path in game_files:
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception:
            failed_count += 1
    
    return failed_count == 0, deleted_count, failed_count

def delete_session_files(base_dir='.'):
    """
    Delete all Flask session files
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        
    Returns:
        tuple: (success: bool, deleted_count: int, failed_count: int)
    """
    session_dir = os.path.join(base_dir, 'flask_session')
    
    if not os.path.exists(session_dir):
        return True, 0, 0
    
    session_files = glob.glob(os.path.join(session_dir, '*'))
    deleted_count = 0
    failed_count = 0
    
    for file_path in session_files:
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception:
                failed_count += 1
    
    return failed_count == 0, deleted_count, failed_count

def delete_statistics_cache(base_dir='.'):
    """
    Delete the statistics cache file
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        
    Returns:
        bool: True if successful, False otherwise
    """
    stats_path = os.path.join(base_dir, 'static', 'stats.json')
    
    if os.path.exists(stats_path):
        try:
            os.remove(stats_path)
            return True
        except Exception:
            return False
    return True

def reset_all_data(base_dir='.', verbose=False):
    """
    Reset all player data including users, games, sessions, and statistics
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        verbose (bool): Print detailed output (default: False)
        
    Returns:
        dict: Results dictionary with success status and details
    """
    results = {
        'success': True,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_database': False,
        'game_logs': {'success': False, 'deleted': 0, 'failed': 0},
        'session_files': {'success': False, 'deleted': 0, 'failed': 0},
        'statistics_cache': False
    }
    
    if verbose:
        print("🧹 Starting complete player data reset...")
        print(f"📅 Timestamp: {results['timestamp']}")
        print()
    
    # Delete user database
    results['user_database'] = delete_user_database(base_dir)
    if verbose:
        status = "✓" if results['user_database'] else "✗"
        print(f"{status} User database")
    
    # Delete game logs
    success, deleted, failed = delete_game_logs(base_dir)
    results['game_logs'] = {'success': success, 'deleted': deleted, 'failed': failed}
    if verbose:
        status = "✓" if success else "✗"
        print(f"{status} Game logs ({deleted} deleted, {failed} failed)")
    
    # Delete session files
    success, deleted, failed = delete_session_files(base_dir)
    results['session_files'] = {'success': success, 'deleted': deleted, 'failed': failed}
    if verbose:
        status = "✓" if success else "✗"
        print(f"{status} Session files ({deleted} deleted, {failed} failed)")
    
    # Delete statistics cache
    results['statistics_cache'] = delete_statistics_cache(base_dir)
    if verbose:
        status = "✓" if results['statistics_cache'] else "✗"
        print(f"{status} Statistics cache")
    
    # Overall success
    results['success'] = (
        results['user_database'] and
        results['game_logs']['success'] and
        results['session_files']['success'] and
        results['statistics_cache']
    )
    
    if verbose:
        print()
        if results['success']:
            print("🎉 Player data reset completed successfully!")
        else:
            print("⚠️  Player data reset completed with some errors.")
    
    return results

def reset_statistics_only(base_dir='.', verbose=False):
    """
    Reset only the statistics cache, keeping all user data
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        verbose (bool): Print detailed output (default: False)
        
    Returns:
        dict: Results dictionary with success status and details
    """
    results = {
        'success': False,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'statistics_cache': False
    }
    
    if verbose:
        print("📊 Resetting statistics cache only...")
        print(f"📅 Timestamp: {results['timestamp']}")
        print()
    
    results['statistics_cache'] = delete_statistics_cache(base_dir)
    results['success'] = results['statistics_cache']
    
    if verbose:
        status = "✓" if results['statistics_cache'] else "✗"
        print(f"{status} Statistics cache")
        print()
        if results['success']:
            print("🎉 Statistics reset completed successfully!")
        else:
            print("⚠️  Statistics reset failed.")
    
    return results

def get_data_summary(base_dir='.'):
    """
    Get a summary of current data that would be affected by reset
    
    Args:
        base_dir (str): Base directory path (default: current directory)
        
    Returns:
        dict: Summary of data files and counts
    """
    summary = {
        'user_database': {
            'exists': False,
            'path': os.path.join(base_dir, 'logs', 'users.db')
        },
        'game_logs': {
            'count': 0,
            'files': []
        },
        'session_files': {
            'count': 0,
            'files': []
        },
        'statistics_cache': {
            'exists': False,
            'path': os.path.join(base_dir, 'static', 'stats.json')
        }
    }
    
    # Check user database
    summary['user_database']['exists'] = os.path.exists(summary['user_database']['path'])
    
    # Check game logs
    logs_pattern = os.path.join(base_dir, 'logs', 'game_*.json')
    game_files = glob.glob(logs_pattern)
    summary['game_logs']['count'] = len(game_files)
    summary['game_logs']['files'] = [os.path.basename(f) for f in game_files]
    
    # Check session files
    session_dir = os.path.join(base_dir, 'flask_session')
    if os.path.exists(session_dir):
        session_files = [f for f in os.listdir(session_dir) if os.path.isfile(os.path.join(session_dir, f))]
        summary['session_files']['count'] = len(session_files)
        summary['session_files']['files'] = session_files
    
    # Check statistics cache
    summary['statistics_cache']['exists'] = os.path.exists(summary['statistics_cache']['path'])
    
    return summary
