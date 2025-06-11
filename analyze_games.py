#!/usr/bin/env python3
"""
Comprehensive Game Analysis Tool for VST
Analyzes all game logs and provides detailed statistics
"""

import os
import json
import glob
from datetime import datetime, timezone
from collections import defaultdict, Counter
import statistics

class GameAnalyzer:
    def __init__(self):
        self.logs_dir = 'logs'
        self.games_dir = 'logs/games'
        
    def analyze_all_games(self):
        """Analyze all game logs and return comprehensive statistics"""
        print("🎮 VST Game Analysis Report")
        print("=" * 50)
        
        # Collect all game data
        all_games = []
        active_games = []
        completed_games = []
        
        # Check main logs directory
        main_logs = glob.glob(os.path.join(self.logs_dir, 'game_*.json'))
        print(f"📁 Found {len(main_logs)} game files in main logs directory")
        
        # Check games subdirectory
        games_logs = glob.glob(os.path.join(self.games_dir, 'game_*.json'))
        print(f"📁 Found {len(games_logs)} game files in games subdirectory")
        
        # Process all game files
        for game_file in main_logs + games_logs:
            try:
                with open(game_file, 'r') as f:
                    game_data = json.load(f)
                    all_games.append(game_data)
                    
                    # Categorize games
                    if game_data.get('status') == 'active' and not game_data.get('final_result'):
                        active_games.append(game_data)
                    else:
                        completed_games.append(game_data)
                        
            except Exception as e:
                print(f"⚠️  Error reading {game_file}: {str(e)}")
        
        print(f"\n📊 Game Summary:")
        print(f"   Total games found: {len(all_games)}")
        print(f"   Active games: {len(active_games)}")
        print(f"   Completed games: {len(completed_games)}")
        
        # Analyze users
        self.analyze_users(all_games)
        
        # Analyze game sessions
        self.analyze_sessions(all_games)
        
        # Analyze performance
        self.analyze_performance(completed_games)
        
        # Analyze game structure
        self.analyze_game_structure(all_games)
        
        return {
            'total_games': len(all_games),
            'active_games': len(active_games),
            'completed_games': len(completed_games),
            'all_games': all_games,
            'completed_games': completed_games
        }
    
    def analyze_users(self, games):
        """Analyze user statistics"""
        print(f"\n👥 User Analysis:")
        
        user_games = defaultdict(list)
        for game in games:
            user_id = game.get('user_id', 'unknown')
            user_games[user_id].append(game)
        
        print(f"   Unique users: {len(user_games)}")
        
        for user_id, user_game_list in user_games.items():
            print(f"   User {user_id}: {len(user_game_list)} games")
    
    def analyze_sessions(self, games):
        """Analyze session duration and timing"""
        print(f"\n⏱️  Session Analysis:")
        
        session_data = []
        for game in games:
            created_at = game.get('created_at')
            if created_at:
                try:
                    # Parse timestamp
                    if created_at.endswith('+00:00'):
                        dt = datetime.fromisoformat(created_at.replace('+00:00', ''))
                    else:
                        dt = datetime.fromisoformat(created_at)
                    session_data.append(dt)
                except:
                    pass
        
        if session_data:
            session_data.sort()
            print(f"   First game: {session_data[0].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Last game: {session_data[-1].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Calculate session gaps
            gaps = []
            for i in range(1, len(session_data)):
                gap = (session_data[i] - session_data[i-1]).total_seconds() / 60  # minutes
                gaps.append(gap)
            
            if gaps:
                print(f"   Average time between games: {statistics.mean(gaps):.1f} minutes")
                print(f"   Median time between games: {statistics.median(gaps):.1f} minutes")
    
    def analyze_performance(self, completed_games):
        """Analyze game performance"""
        print(f"\n🎯 Performance Analysis:")
        
        if not completed_games:
            print("   No completed games found for performance analysis")
            return
        
        scores = []
        success_count = 0
        
        for game in completed_games:
            final_result = game.get('final_result')
            if final_result:
                score = final_result.get('score', 0)
                scores.append(score)
                if final_result.get('correct', False):
                    success_count += 1
        
        if scores:
            print(f"   Games with final scores: {len(scores)}")
            print(f"   Success rate: {(success_count/len(scores)*100):.1f}%")
            print(f"   Average score: {statistics.mean(scores):.1f}")
            print(f"   Score distribution: {Counter(scores)}")
    
    def analyze_game_structure(self, games):
        """Analyze game structure (rounds, quadrants, etc.)"""
        print(f"\n🎲 Game Structure Analysis:")
        
        round_counts = []
        quadrant_counts = []
        biased_quadrants = []
        
        for game in games:
            # Check different possible locations for round count
            n_rounds = (game.get('n_rounds') or 
                       game.get('game_metadata', {}).get('n_rounds') or 
                       len(game.get('rounds', [])) or
                       len(game.get('rounds_data', [])))
            
            if n_rounds:
                round_counts.append(n_rounds)
            
            # Check quadrant count
            n_quadrants = (game.get('n_quadrants') or 
                          game.get('game_metadata', {}).get('n_quadrants'))
            if n_quadrants:
                quadrant_counts.append(n_quadrants)
            
            # Check biased quadrant
            biased_q = (game.get('biased_quadrant') or 
                       game.get('game_metadata', {}).get('biased_quadrant'))
            if biased_q is not None:
                biased_quadrants.append(biased_q)
        
        if round_counts:
            print(f"   Round counts: {Counter(round_counts)}")
            print(f"   Average rounds per game: {statistics.mean(round_counts):.1f}")
        
        if quadrant_counts:
            print(f"   Quadrant counts: {Counter(quadrant_counts)}")
        
        if biased_quadrants:
            print(f"   Biased quadrant distribution: {Counter(biased_quadrants)}")
    
    def update_statistics_file(self, analysis_data):
        """Update the statistics file with current data"""
        print(f"\n📈 Updating Statistics File...")
        
        completed_games = analysis_data['completed_games']
        
        if not completed_games:
            print("   No completed games to calculate statistics from")
            return
        
        # Calculate statistics
        success_count = 0
        scores = []
        durations = []
        
        for game in completed_games:
            final_result = game.get('final_result')
            if final_result:
                if final_result.get('correct', False):
                    success_count += 1
                scores.append(final_result.get('score', 0))
        
        success_rate = (success_count / len(completed_games) * 100) if completed_games else 0
        
        # Create updated statistics
        stats = {
            'total_games': len(completed_games),
            'success_rate': success_rate,
            'average_duration': statistics.mean(durations) if durations else 0,
            'performance_distribution': {
                'bins': [-100, -50, 0, 50, 100],
                'counts': [scores.count(-100), scores.count(-50), scores.count(0), scores.count(50), scores.count(100)]
            },
            'learning_curve': {
                'window_size': 10,
                'rates': [success_rate]  # Simplified for now
            },
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Save statistics
        os.makedirs('static', exist_ok=True)
        with open('static/stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"   ✅ Statistics updated: {len(completed_games)} games, {success_rate:.1f}% success rate")

def main():
    analyzer = GameAnalyzer()
    analysis_data = analyzer.analyze_all_games()
    analyzer.update_statistics_file(analysis_data)
    
    print(f"\n🎉 Analysis Complete!")
    print(f"   Run this script anytime to get updated statistics")
    print(f"   Usage: python analyze_games.py")

if __name__ == "__main__":
    main()
