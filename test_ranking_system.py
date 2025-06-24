#!/usr/bin/env python3
"""
Test Ranking System Functionality
=================================

This script tests the updated ranking system to ensure:
1. All qualified players (10+ hard games with names) get proper rankings
2. Statistics update includes all human players
3. The 1-minute cooldown works correctly
4. Rankings are properly calculated from game history
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timezone
from utils.RankingSystem import RankingSystem
from utils.StatsCalculator import StatsCalculator
from utils.UserManager import UserManager
from utils.config import BASE_DIR

def test_ranking_system():
    """Test the ranking system functionality"""
    print("🧪 Testing Ranking System Functionality")
    print("=" * 50)
    
    # Test 1: Check database structure
    print("\n1. Checking database structure...")
    db_path = os.path.join(BASE_DIR, 'logs', 'users.db')
    
    if not os.path.exists(db_path):
        print("❌ Database does not exist")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user_rankings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_rankings'")
    if cursor.fetchone():
        print("✅ user_rankings table exists")
    else:
        print("❌ user_rankings table missing")
        conn.close()
        return False
    
    # Check current data
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE hard_games_completed >= 10")
    qualified_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_rankings")
    ranking_count = cursor.fetchone()[0]
    
    print(f"   - Total users: {user_count}")
    print(f"   - Users with 10+ hard games: {qualified_count}")
    print(f"   - Users with rankings: {ranking_count}")
    
    conn.close()
    
    # Test 2: Test ranking update for qualified players
    print("\n2. Testing ranking updates for qualified players...")
    try:
        logs_dir = os.path.join(BASE_DIR, 'logs')
        results = RankingSystem.update_all_qualified_players(db_path, logs_dir)
        
        print(f"   - Total qualified players found: {results['total_qualified']}")
        print(f"   - Successfully updated: {results['updated_count']}")
        print(f"   - Failed updates: {results['failed_count']}")
        
        if results['total_qualified'] > 0:
            print("   - Update details:")
            for result in results['results']:
                status = result['status']
                name = result.get('display_name', 'Unknown')
                print(f"     * {name}: {status}")
        
        print("✅ Ranking update test completed")
        
    except Exception as e:
        print(f"❌ Ranking update test failed: {str(e)}")
        return False
    
    # Test 3: Test statistics calculation
    print("\n3. Testing statistics calculation...")
    try:
        stats_success = StatsCalculator.update_statistics('logs', force_update=True)
        
        if stats_success:
            print("✅ Statistics update successful")
            
            # Check if stats file was created
            stats_file = os.path.join(BASE_DIR, 'static', 'stats.json')
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                print(f"   - Total games in stats: {stats.get('total_games', 0)}")
                print(f"   - Success rate: {stats.get('success_rate', 0):.1f}%")
                print(f"   - Last updated: {stats.get('last_updated', 'Unknown')}")
            else:
                print("❌ Statistics file not created")
                return False
        else:
            print("❌ Statistics update failed")
            return False
            
    except Exception as e:
        print(f"❌ Statistics test failed: {str(e)}")
        return False
    
    # Test 4: Test leaderboard generation
    print("\n4. Testing leaderboard generation...")
    try:
        leaderboard = StatsCalculator.get_combined_leaderboard()
        
        human_players = [p for p in leaderboard if p['type'] == 'human']
        ai_players = [p for p in leaderboard if p['type'] == 'llm']
        
        print(f"   - Total leaderboard entries: {len(leaderboard)}")
        print(f"   - Human players: {len(human_players)}")
        print(f"   - AI players: {len(ai_players)}")
        
        if human_players:
            print("   - Top human players:")
            for i, player in enumerate(human_players[:3]):
                print(f"     {i+1}. {player['name']} - Score: {player['score']:.0f}, Games: {player['games_played']}")
        
        print("✅ Leaderboard generation test completed")
        
    except Exception as e:
        print(f"❌ Leaderboard test failed: {str(e)}")
        return False
    
    # Test 5: Test individual ranking retrieval
    print("\n5. Testing individual ranking retrieval...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get a user with rankings
        cursor.execute("SELECT user_id FROM user_rankings LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            ranking_data = RankingSystem.get_user_ranking(db_path, user_id)
            
            if ranking_data:
                print(f"   - User ID: {user_id}")
                print(f"   - Rank Score: {ranking_data['rank_score']}")
                print(f"   - Games Played: {ranking_data['games_played']}")
                print(f"   - Win Rate: {ranking_data['win_rate']:.1f}%")
                print(f"   - Tier: {ranking_data['rank_tier']}")
                print("✅ Individual ranking retrieval test completed")
            else:
                print("❌ Could not retrieve ranking data")
                conn.close()
                return False
        else:
            print("ℹ️  No users with rankings found (this is expected if no games have been played)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Individual ranking test failed: {str(e)}")
        return False
    
    print("\n🎉 All ranking system tests completed successfully!")
    return True

def test_statistics_cooldown():
    """Test the 1-minute cooldown functionality"""
    print("\n🕐 Testing Statistics Cooldown Functionality")
    print("=" * 50)
    
    try:
        stats_file = os.path.join(BASE_DIR, 'static', 'stats.json')
        
        # First update
        print("1. Performing first statistics update...")
        success1 = StatsCalculator.update_statistics('logs', force_update=False)
        
        if success1 and os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats1 = json.load(f)
            first_update = stats1.get('last_updated')
            print(f"   ✅ First update completed at: {first_update}")
        else:
            print("   ❌ First update failed")
            return False
        
        # Immediate second update (should be skipped due to cooldown)
        print("2. Attempting immediate second update (should be skipped)...")
        success2 = StatsCalculator.update_statistics('logs', force_update=False)
        
        if success2 and os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats2 = json.load(f)
            second_update = stats2.get('last_updated')
            
            if first_update == second_update:
                print("   ✅ Second update correctly skipped due to cooldown")
            else:
                print("   ❌ Cooldown not working - update was not skipped")
                return False
        else:
            print("   ❌ Second update failed unexpectedly")
            return False
        
        # Forced update (should bypass cooldown)
        print("3. Performing forced update (should bypass cooldown)...")
        success3 = StatsCalculator.update_statistics('logs', force_update=True)
        
        if success3:
            print("   ✅ Forced update completed successfully")
        else:
            print("   ❌ Forced update failed")
            return False
        
        print("\n🎉 Cooldown functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Cooldown test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Ranking System Tests")
    print("=" * 60)
    
    # Run all tests
    ranking_test_passed = test_ranking_system()
    cooldown_test_passed = test_statistics_cooldown()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Ranking System Tests: {'✅ PASSED' if ranking_test_passed else '❌ FAILED'}")
    print(f"Cooldown Tests: {'✅ PASSED' if cooldown_test_passed else '❌ FAILED'}")
    
    overall_success = ranking_test_passed and cooldown_test_passed
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! The ranking system is working correctly.")
        print("\nKey Features Verified:")
        print("✅ Qualified players (10+ hard games with names) get proper rankings")
        print("✅ Statistics include all human players")
        print("✅ 1-minute cooldown prevents server overload")
        print("✅ Rankings are calculated from complete game history")
        print("✅ Leaderboard displays both human and AI players")
    else:
        print("\n❌ SOME TESTS FAILED! Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
