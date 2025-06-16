from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
import traceback
import os

# Import our custom modules
from utils.config import SESSION_DIR, debug_log, LOGS_DIR
from utils.GameLogger import GameLogger
from utils.UserManager import UserManager
from utils.VSTtask import VSTtask, VSTtaskEasy, VSTtaskHard
from utils.StatsCalculator import StatsCalculator
from datetime import datetime, timezone

app = Flask(__name__)

# Configure filesystem session
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=SESSION_DIR,
    SECRET_KEY='your_secret_key_here_change_in_production',
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
    SESSION_USE_SIGNER=True,
    SESSION_KEY_PREFIX='vst_session:',
    SESSION_FILE_THRESHOLD=500
)

# Initialize Flask-Session
Session(app)

# Initialize the loggers and user manager
game_logger = GameLogger()
user_manager = UserManager()

# Add this function to your app.py
def test_session_state():
    """Test session functionality and return diagnostic info"""
    test_results = {
        "session_exists": False,
        "session_dir_exists": False,
        "session_dir_writable": False,
        "session_file_details": None,
        "current_session_data": None,
        "game_log_details": None
    }
    
    # Test 1: Check if session exists and has data
    test_results["session_exists"] = bool(session)
    if session:
        test_results["current_session_data"] = dict(session)
        debug_log(f"Current session data: {dict(session)}")
    
    # Test 2: Check session directory
    test_results["session_dir_exists"] = os.path.exists(SESSION_DIR)
    if test_results["session_dir_exists"]:
        try:
            test_file = os.path.join(SESSION_DIR, "test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            test_results["session_dir_writable"] = True
        except Exception as e:
            debug_log(f"Session directory write test failed: {str(e)}")
    
    # Test 3: Check session files
    if session.get('game_id'):
        try:
            session_files = [f for f in os.listdir(SESSION_DIR) if f.startswith('sess')]
            test_results["session_file_details"] = {
                "files_found": len(session_files),
                "files": session_files
            }
        except Exception as e:
            debug_log(f"Error listing session files: {str(e)}")
        
        # Test 4: Check game log file
        log_filepath = session.get('log_filepath')
        if log_filepath:
            try:
                test_results["game_log_details"] = {
                    "exists": os.path.exists(log_filepath),
                    "path": log_filepath,
                    "permissions": oct(os.stat(log_filepath).st_mode)[-3:] if os.path.exists(log_filepath) else None,
                    "directory_writable": os.access(os.path.dirname(log_filepath), os.W_OK)
                }
            except Exception as e:
                debug_log(f"Error checking log file: {str(e)}")
    
    debug_log(f"Session test results: {test_results}")
    return test_results


@app.route('/introduction')
def introduction():
    return render_template('introduction.html')

@app.route('/play')
def play():
    debug_log("Accessing play page - simplified version")
    
    # Simple cleanup - just clear any old game data
    session.pop('game', None)
    session.pop('game_id', None)
    session.pop('log_filepath', None)
    session.pop('current_game_number', None)
    
    debug_log(f"Current session state after cleanup: {dict(session)}")
    
    # Get or create user and their progress
    user_info = user_manager.get_or_create_user()
    progress = user_manager.get_user_game_progress(user_info['user_id'])
    
    # Store user info in session
    session['user_id'] = user_info['user_id']
    session['user_progress'] = progress
    session.modified = True
    
    return render_template('play.html', user_progress=progress)

@app.route('/human-statistics')
def human_statistics():
    stats = StatsCalculator.get_current_stats()
    if not stats:
        # Return default values if no statistics are available
        stats = {
            'total_games': 0,
            'success_rate': 0,
            'average_duration': 0,
            'performance_distribution': {'bins': [], 'counts': []},
            'learning_curve': {'window_size': 0, 'rates': []}
        }
    
    # Convert average duration from seconds to minutes:seconds format
    avg_duration_mins = int(stats['average_duration'] // 60)
    avg_duration_secs = int(stats['average_duration'] % 60)
    formatted_duration = f"{avg_duration_mins}:{avg_duration_secs:02d}"
    
    return render_template('human_statistics.html',
                         total_games=stats['total_games'],
                         success_rate=f"{stats['success_rate']:.1f}",
                         avg_duration=formatted_duration,
                         performance_dist=stats['performance_distribution'],
                         learning_curve=stats['learning_curve'])

@app.route('/llm-leaderboard')
def llm_leaderboard():
    return render_template('llm_leaderboard.html')

@app.route('/statistics')
def statistics():
    stats = StatsCalculator.get_current_stats()
    if not stats:
        # Return default values if no statistics are available
        stats = {
            'total_games': 0,
            'success_rate': 0,
            'average_duration': 0,
            'performance_distribution': {'bins': [], 'counts': []},
            'learning_curve': {'window_size': 0, 'rates': []}
        }
    
    # Convert average duration from seconds to minutes:seconds format
    avg_duration_mins = int(stats['average_duration'] // 60)
    avg_duration_secs = int(stats['average_duration'] % 60)
    formatted_duration = f"{avg_duration_mins}:{avg_duration_secs:02d}"
    
    return render_template('statistics.html',
                         total_games=stats['total_games'],
                         success_rate=f"{stats['success_rate']:.1f}",
                         avg_duration=formatted_duration,
                         performance_dist=stats['performance_distribution'],
                         learning_curve=stats['learning_curve'])

@app.route('/research-notes')
def research_notes():
    return render_template('research_notes.html')

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/')
def index():
    debug_log("Accessing index page")
    debug_log(f"Current session state: {dict(session)}")
    return redirect(url_for('introduction'))

@app.route('/test_session')
def test_session():
    """Test route to diagnose session issues"""
    debug_log("Testing session functionality")
    
    # Test results dictionary
    test_results = {
        "session_exists": False,
        "session_dir_exists": False,
        "session_dir_writable": False,
        "session_file_details": None,
        "current_session_data": None,
        "game_log_details": None
    }
    
    # Test 1: Check if session exists and has data
    test_results["session_exists"] = bool(session)
    if session:
        test_results["current_session_data"] = dict(session)
        debug_log(f"Current session data: {dict(session)}")
    
    # Test 2: Check session directory
    test_results["session_dir_exists"] = os.path.exists(SESSION_DIR)
    if test_results["session_dir_exists"]:
        try:
            test_file = os.path.join(SESSION_DIR, "test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            test_results["session_dir_writable"] = True
        except Exception as e:
            debug_log(f"Session directory write test failed: {str(e)}")
    
    # Test 3: Check session files
    if session.get('game_id'):
        try:
            session_files = [f for f in os.listdir(SESSION_DIR) if f.startswith('sess')]
            test_results["session_file_details"] = {
                "files_found": len(session_files),
                "files": session_files
            }
        except Exception as e:
            debug_log(f"Error listing session files: {str(e)}")
        
        # Test 4: Check game log file
        log_filepath = session.get('log_filepath')
        if log_filepath:
            try:
                test_results["game_log_details"] = {
                    "exists": os.path.exists(log_filepath),
                    "path": log_filepath,
                    "permissions": oct(os.stat(log_filepath).st_mode)[-3:] if os.path.exists(log_filepath) else None,
                    "directory_writable": os.access(os.path.dirname(log_filepath), os.W_OK)
                }
            except Exception as e:
                debug_log(f"Error checking log file: {str(e)}")
    
    debug_log(f"Session test results: {test_results}")
    return jsonify(test_results)

@app.route('/start')
def start():
    try:
        debug_log("Starting new game - simplified version")
        
        # Clear ALL existing game state
        session.pop('game_id', None)
        session.pop('log_filepath', None)
        session.pop('current_game_number', None)
        session.pop('game', None)
        
        # Get user info from session
        user_id = session.get('user_id')
        if not user_id:
            user_info = user_manager.get_or_create_user()
            user_id = user_info['user_id']
            session['user_id'] = user_id
        
        # Get user's current game progress
        progress = user_manager.get_user_game_progress(user_id)
        current_game_number = progress['games_completed'] + 1
        session['user_progress'] = progress
        
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log(user_id, current_game_number)
        
        # Initialize game with random number of rounds
        task = VSTtask(n_quadrants=4, n_queues=1) 
        
        # Validate round count
        if len(task.rounds) != task.n_rounds:
            debug_log(f"Warning: Round count mismatch! Expected {task.n_rounds}, got {len(task.rounds)}")
            task.n_rounds = len(task.rounds)
        
        # Store simplified game data (no game_rounds in logs)
        game_data = {
            'game_id': game_id,
            'user_id': user_id,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'biased_cue': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'rounds': [],  # Simple logging format
            'final_choice': None,
            'completion_time': None,
            'success': None
        }
        
        # Save initial game data to JSON file
        game_logger.save_game_data(log_filepath, game_data)
        
        # Store game rounds in session for gameplay (not in logs)
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        session['current_game_number'] = current_game_number
        session['game_rounds'] = task.rounds  # Store in session for gameplay
        session.modified = True
        
        debug_log(f"Started simple game: ID={game_id}, rounds={task.n_rounds}, biased_quadrant={task.biased_quadrant}")
        
        return redirect(url_for('round_page', round_number=0))
        
    except Exception as e:
        debug_log(f"Error in start route: {str(e)}\n{traceback.format_exc()}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/start/easy')
def start_easy():
    try:
        debug_log("Starting new EASY game")
        
        # Clear ALL existing game state
        session.pop('game_id', None)
        session.pop('log_filepath', None)
        session.pop('current_game_number', None)
        session.pop('game', None)
        
        # Get user info from session
        user_id = session.get('user_id')
        if not user_id:
            user_info = user_manager.get_or_create_user()
            user_id = user_info['user_id']
            session['user_id'] = user_id
        
        # Get user's current game progress
        progress = user_manager.get_user_game_progress(user_id)
        current_game_number = progress['games_completed'] + 1
        session['user_progress'] = progress
        
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log(user_id, current_game_number)
        
        # Initialize EASY game (no occlusions, with validation)
        task = VSTtaskEasy(n_quadrants=4, n_queues=1) 
        
        # Validate round count
        if len(task.rounds) != task.n_rounds:
            debug_log(f"Warning: Round count mismatch! Expected {task.n_rounds}, got {len(task.rounds)}")
            task.n_rounds = len(task.rounds)
        
        # Store simplified game data (no game_rounds in logs)
        game_data = {
            'game_id': game_id,
            'user_id': user_id,
            'game_mode': 'easy',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'biased_cue': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'rounds': [],  # Simple logging format
            'final_choice': None,
            'completion_time': None,
            'success': None
        }
        
        # Save initial game data to JSON file
        game_logger.save_game_data(log_filepath, game_data)
        
        # Store game rounds in session for gameplay (not in logs)
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        session['current_game_number'] = current_game_number
        session['game_rounds'] = task.rounds  # Store in session for gameplay
        session.modified = True
        
        debug_log(f"Started EASY game: ID={game_id}, rounds={task.n_rounds}, biased_quadrant={task.biased_quadrant}")
        
        return redirect(url_for('round_page', round_number=0))
        
    except Exception as e:
        debug_log(f"Error in start_easy route: {str(e)}\n{traceback.format_exc()}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/start/hard')
def start_hard():
    try:
        debug_log("Starting new HARD game")
        
        # Clear ALL existing game state
        session.pop('game_id', None)
        session.pop('log_filepath', None)
        session.pop('current_game_number', None)
        session.pop('game', None)
        
        # Get user info from session
        user_id = session.get('user_id')
        if not user_id:
            user_info = user_manager.get_or_create_user()
            user_id = user_info['user_id']
            session['user_id'] = user_id
        
        # Get user's current game progress
        progress = user_manager.get_user_game_progress(user_id)
        current_game_number = progress['games_completed'] + 1
        session['user_progress'] = progress
        
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log(user_id, current_game_number)
        
        # Initialize HARD game (with occlusions, no validation)
        task = VSTtaskHard(n_quadrants=4, n_queues=1) 
        
        # Validate round count
        if len(task.rounds) != task.n_rounds:
            debug_log(f"Warning: Round count mismatch! Expected {task.n_rounds}, got {len(task.rounds)}")
            task.n_rounds = len(task.rounds)
        
        # Store simplified game data (no game_rounds in logs)
        game_data = {
            'game_id': game_id,
            'user_id': user_id,
            'game_mode': 'hard',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'biased_cue': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'rounds': [],  # Simple logging format
            'final_choice': None,
            'completion_time': None,
            'success': None
        }
        
        # Save initial game data to JSON file
        game_logger.save_game_data(log_filepath, game_data)
        
        # Store game rounds in session for gameplay (not in logs)
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        session['current_game_number'] = current_game_number
        session['game_rounds'] = task.rounds  # Store in session for gameplay
        session.modified = True
        
        debug_log(f"Started HARD game: ID={game_id}, rounds={task.n_rounds}, biased_quadrant={task.biased_quadrant}")
        
        return redirect(url_for('round_page', round_number=0))
        
    except Exception as e:
        debug_log(f"Error in start_hard route: {str(e)}\n{traceback.format_exc()}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/log_choice', methods=['POST'])
def log_choice():
    try:
        data = request.get_json()
        if data is None:
            return "No data provided", 400
            
        # Get game_id from session
        game_id = session.get('game_id')
        log_filepath = session.get('log_filepath')
        
        if not game_id or not log_filepath:
            return "No active game session", 400
        
        # Simple logging - just append to the JSON file
        data['game_id'] = game_id
        success = game_logger.log_choice(log_filepath, data)
        
        if not success:
            debug_log("Failed to log choice")
            return "Logging failed", 500
        
        debug_log(f"Successfully logged choice for game {game_id}")
        return "OK", 200
        
    except Exception as e:
        debug_log(f"Error in log_choice: {str(e)}")
        return str(e), 500

@app.route('/round/<int:round_number>', methods=['GET'])
def round_page(round_number):
    debug_log(f"Accessing round {round_number} - simplified version")
    try:
        # Get game info from session
        game_id = session.get('game_id')
        log_filepath = session.get('log_filepath')
        
        if not game_id or not log_filepath:
            debug_log("No game_id or log_filepath in session")
            debug_log(f"Current session: {dict(session)}")
            session.clear()
            return redirect(url_for('index'))
        
        # Load game data from JSON file
        game_data = game_logger.load_game_data(log_filepath)
        if not game_data:
            debug_log(f"Could not load game data from {log_filepath}")
            session.clear()
            return redirect(url_for('index'))
        
        # Check if round number exceeds max rounds
        n_rounds = game_data.get('n_rounds', 0)
        if round_number >= n_rounds:
            debug_log(f"Round number {round_number} exceeds max rounds {n_rounds}, redirecting to final")
            return redirect(url_for('final'))
        
        # Get specific round data from session (for gameplay)
        game_rounds = session.get('game_rounds', [])
        if round_number >= len(game_rounds):
            debug_log(f"Round {round_number} not found in session game_rounds array (length: {len(game_rounds)}), redirecting to final")
            return redirect(url_for('final'))
        
        round_data = game_rounds[round_number]
        
        # Handle backward compatibility: convert "queues" to "cues" if needed
        if 'queues' in round_data and 'cues' not in round_data:
            round_data['cues'] = round_data['queues']
        user_progress = session.get('user_progress', {'games_completed': 0, 'total_score': 0})
        
        debug_log(f"Successfully loaded round {round_number} from JSON file")
        return render_template('round.html', round_number=round_number, round_data=round_data, user_progress=user_progress)
            
    except Exception as e:
        debug_log(f"Error in round_page route: {str(e)}\n{traceback.format_exc()}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/final', methods=['GET', 'POST'])
def final():
    debug_log("Processing final route - simplified version")
    try:
        # Get game info from session
        game_id = session.get('game_id')
        log_filepath = session.get('log_filepath')
        
        debug_log(f"Final route - game_id: {game_id}, log_filepath: {log_filepath}")
        debug_log(f"Final route - session contents: {dict(session)}")
        
        if not game_id or not log_filepath:
            debug_log("No game_id or log_filepath in session at final page")
            debug_log(f"Current session: {dict(session)}")
            return redirect(url_for('introduction'))  # Go to introduction instead of index
        
        # Load game data from JSON file
        game_data = game_logger.load_game_data(log_filepath)
        if not game_data:
            debug_log(f"Could not load game data from {log_filepath}")
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                chosen = int(request.form.get('biased_quadrant'))
            except (ValueError, TypeError):
                debug_log("Invalid quadrant choice submitted")
                chosen = -1
                
            biased_quadrant = game_data.get('biased_cue', game_data.get('biased_quadrant'))
            correct = (chosen == biased_quadrant)
            score = 100 if correct else -100
            
            # Log the final result
            result_data = {
                'type': 'final_choice',
                'chosen_quadrant': chosen,
                'correct': correct,
                'score': score,
                'biased_quadrant': biased_quadrant,
                'client_timestamp': datetime.now(timezone.utc).isoformat()
            }
            game_logger.log_choice(log_filepath, result_data)
            
            # Record game completion in user database
            user_id = session.get('user_id')
            if user_id:
                user_manager.record_game_completion(user_id, game_id, score)
                debug_log(f"Recorded game completion for user {user_id}: score {score}")
            
            debug_log(f"Game completed - Chosen: {chosen}, Correct: {correct}, Score: {score}")
            user_progress = session.get('user_progress', {'games_completed': 0, 'total_score': 0})
            return render_template('result.html', chosen=chosen, correct=correct, 
                                score=score, biased=biased_quadrant, user_progress=user_progress)
                                
        user_progress = session.get('user_progress', {'games_completed': 0, 'total_score': 0})
        n_quadrants = game_data.get('n_quadrants', 4)
        return render_template('final.html', n_quadrants=n_quadrants, user_progress=user_progress)
        
    except Exception as e:
        debug_log(f"Error in final route: {str(e)}\n{traceback.format_exc()}")
        return redirect(url_for('index'))



@app.route('/api/user_progress', methods=['GET'])
def get_user_progress():
    try:
        # If we're in an active game, use the session-stored progress
        # This prevents the progress bar from jumping to 100% during a game
        if session.get('game_id') and session.get('user_progress'):
            progress = session['user_progress']
            user_id = session.get('user_id')
        else:
            # If no active game, get fresh progress from database
            user_info = user_manager.get_or_create_user()
            progress = user_manager.get_user_game_progress(user_info['user_id'])
            user_id = user_info['user_id']
        
        return jsonify({
            'user_id': user_id,
            'progress': progress,
            'status': 'success'
        })
    except Exception as e:
        debug_log(f"Error getting user progress: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_round_status', methods=['GET'])
def check_round_status():
    try:
        round_number = int(request.args.get('round', 0))
        
        # Get game info from session
        game_id = session.get('game_id')
        log_filepath = session.get('log_filepath')
        
        if not game_id or not log_filepath:
            debug_log("No game session found for round status check")
            return jsonify({'should_end': True, 'reason': 'no_session'})
        
        # Load game data from JSON file
        game_data = game_logger.load_game_data(log_filepath)
        if not game_data:
            debug_log("Could not load game data for round status check")
            return jsonify({'should_end': True, 'reason': 'no_game_data'})
        
        n_rounds = game_data.get('n_rounds', 0)
        rounds_length = len(game_data.get('rounds', []))
        
        debug_log(f"Checking round {round_number} against max {n_rounds}, rounds array length: {rounds_length}")
        
        # Check both n_rounds and actual rounds array length
        should_end = round_number >= n_rounds or round_number >= rounds_length
        
        if should_end:
            reason = 'max_rounds_reached' if round_number >= n_rounds else 'rounds_array_exhausted'
        else:
            reason = 'continue'
        
        return jsonify({
            'should_end': should_end,
            'current_round': round_number,
            'max_rounds': n_rounds,
            'actual_rounds_length': rounds_length,
            'reason': reason
        })
    except Exception as e:
        debug_log(f"Error checking round status: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'should_end': True, 'reason': 'error', 'error': str(e)}), 500

@app.route('/api/update_statistics', methods=['POST'])
def update_statistics():
    """Manually trigger statistics update"""
    try:
        debug_log("Manually updating statistics")
        import subprocess
        
        # Use conda environment to run statistics update
        conda_cmd = [
            'bash', '-c',
            'source /home/vst/miniconda3/etc/profile.d/conda.sh && '
            'conda activate vst && '
            'python -c "from utils.StatsCalculator import StatsCalculator; StatsCalculator.update_statistics(\\"logs\\")"'
        ]
        
        result = subprocess.run(conda_cmd, capture_output=True, text=True, cwd='/var/www/vst')
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': 'Statistics updated successfully'})
        else:
            debug_log(f"Statistics update failed: {result.stderr}")
            return jsonify({'status': 'error', 'message': f'Update failed: {result.stderr}'}), 500
    except Exception as e:
        debug_log(f"Error updating statistics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/game_analysis')
def game_analysis():
    """Show detailed game analysis"""
    try:
        import subprocess
        
        # Use conda environment to run game analysis
        conda_cmd = [
            'bash', '-c',
            'source /home/vst/miniconda3/etc/profile.d/conda.sh && '
            'conda activate vst && '
            'python analyze_games.py'
        ]
        
        result = subprocess.run(conda_cmd, capture_output=True, text=True, cwd='/var/www/vst')
        return jsonify({
            'status': 'success',
            'output': result.stdout,
            'error': result.stderr if result.stderr else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/submit_final_choice', methods=['POST'])
def submit_final_choice():
    """Handle final choice submission via AJAX"""
    try:
        data = request.get_json()
        if not data or 'biased_quadrant' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid data provided'}), 400
        
        # Get game info from session
        game_id = session.get('game_id')
        log_filepath = session.get('log_filepath')
        
        if not game_id or not log_filepath:
            return jsonify({'status': 'error', 'message': 'No active game session'}), 400
        
        # Load game data from JSON file
        game_data = game_logger.load_game_data(log_filepath)
        if not game_data:
            return jsonify({'status': 'error', 'message': 'Could not load game data'}), 400
        
        try:
            chosen = int(data['biased_quadrant'])
        except (ValueError, TypeError):
            chosen = -1
        
        biased_quadrant = game_data.get('biased_cue', game_data.get('biased_quadrant'))
        correct = (chosen == biased_quadrant)
        score = 100 if correct else -100
        
        # Create comprehensive final result data
        final_result = {
            'chosen_cue': chosen,
            'correct': correct,
            'score': score,
            'biased_cue': biased_quadrant,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Log the final result with proper structure
        result_data = {
            'type': 'final_choice',
            'chosen_cue': chosen,
            'correct': correct,
            'score': score,
            'biased_cue': biased_quadrant,
            'client_timestamp': datetime.now(timezone.utc).isoformat()
        }
        game_logger.log_choice(log_filepath, result_data)
        
        # Update game data with final result and mark as completed
        game_data['final_result'] = final_result
        game_data['status'] = 'completed'
        game_data['completion_time'] = datetime.now(timezone.utc).isoformat()
        
        # Save updated game data
        game_logger.save_game_data(log_filepath, game_data)
        
        # Record game completion in user database
        user_id = session.get('user_id')
        if user_id:
            user_manager.record_game_completion(user_id, game_id, score)
            debug_log(f"Recorded game completion for user {user_id}: score {score}")
        
        debug_log(f"Game completed via AJAX - Chosen: {chosen}, Correct: {correct}, Score: {score}")
        
        return jsonify({
            'status': 'success',
            'chosen': chosen,
            'correct': correct,
            'score': score,
            'biased_quadrant': biased_quadrant
        })
        
    except Exception as e:
        debug_log(f"Error in submit_final_choice: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/result')
def result():
    """Display game result"""
    try:
        chosen = int(request.args.get('chosen', -1))
        correct = request.args.get('correct', 'false').lower() == 'true'
        score = int(request.args.get('score', 0))
        biased = int(request.args.get('biased', -1))
        
        debug_log(f"Result route - chosen: {chosen}, correct: {correct}, score: {score}, biased: {biased}")
        
        user_progress = session.get('user_progress', {'games_completed': 0, 'total_score': 0})
        
        return render_template('result.html', 
                             chosen=chosen, 
                             correct=correct, 
                             score=score, 
                             biased=biased, 
                             user_progress=user_progress,
                             chr=chr)  # Add chr function to template context
    except Exception as e:
        debug_log(f"Error in result route: {str(e)}\n{traceback.format_exc()}")
        return redirect(url_for('index'))


if __name__ == '__main__':
    debug_log("Starting Flask application")
    try:
        app.run(
            host='127.0.0.1',  # Local host only
            port=5001,         # Port 5001 to avoid conflict with AirTunes
            debug=True         # Set to False in production
        )
    except Exception as e:
        debug_log(f"Error starting Flask app: {str(e)}\n{traceback.format_exc()}")
        raise
