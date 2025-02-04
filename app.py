from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import traceback

# Import our custom modules
from utils.config import SESSION_DIR, debug_log
from utils.GameLogger import GameLogger
from utils.VSTtask import VSTtask

app = Flask(__name__)

# Configure filesystem session
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=SESSION_DIR,
    SECRET_KEY='your_secret_key_here',
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=1800  # 30 minutes
)

# Initialize Flask-Session
Session(app)

# Initialize the game logger
game_logger = GameLogger()


# Add these imports to your app.py
from flask import jsonify
import os

# Add this new route to test session functionality
@app.route('/test_session')
def test_session():
    debug_log("Testing session functionality")
    
    # Test 1: Session Creation
    test_results = {
        "session_exists": False,
        "session_dir_exists": False,
        "session_dir_writable": False,
        "session_file_details": None,
        "current_session_data": None,
        "game_log_details": None
    }
    
    # Check if session exists
    if session:
        test_results["session_exists"] = True
        test_results["current_session_data"] = dict(session)
    
    # Check session directory
    if os.path.exists(SESSION_DIR):
        test_results["session_dir_exists"] = True
        try:
            test_file = os.path.join(SESSION_DIR, "test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            test_results["session_dir_writable"] = True
        except Exception as e:
            debug_log(f"Session directory write test failed: {str(e)}")
    
    # Check session file if game_id exists
    if session.get('game_id'):
        session_files = [f for f in os.listdir(SESSION_DIR) if f.startswith('sess')]
        test_results["session_file_details"] = {
            "files_found": len(session_files),
            "files": session_files
        }
        
        # Check game log file
        log_filepath = session.get('log_filepath')
        if log_filepath:
            test_results["game_log_details"] = {
                "exists": os.path.exists(log_filepath),
                "path": log_filepath,
                "permissions": oct(os.stat(log_filepath).st_mode)[-3:] if os.path.exists(log_filepath) else None
            }
    
    debug_log(f"Session test results: {test_results}")
    return jsonify(test_results)

# Add this decorator to the start route to log more session details
@app.route('/start')
def start():
    debug_log("Starting new game")
    try:
        # Log initial session state
        debug_log(f"Initial session state: {dict(session)}")
        
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log()
        debug_log(f"Created game log - ID: {game_id}, Path: {log_filepath}")
        
        # Store and verify session data
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        session.modified = True  # Explicitly mark session as modified
        debug_log(f"Updated session state: {dict(session)}")
        
        # Initialize game
        task = VSTtask(n_rounds=5, n_quadrants=4, n_queues=1)
        session['game'] = {
            'rounds': task.rounds,
            'biased_quadrant': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'current_round': 0,
            'task_description': task.get_task_description()
        }
        session.modified = True  # Mark as modified again after game initialization
        
        debug_log(f"Final session state before redirect: {dict(session)}")
        return redirect(url_for('round_page', round_number=0))
    except Exception as e:
        debug_log(f"Error in start route: {str(e)}\n{traceback.format_exc()}")
        raise


@app.route('/')
def index():
    debug_log("Accessing index page")
    return render_template('index.html')

@app.route('/start')
def start():
    debug_log("Starting new game")
    try:
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log()
        debug_log(f"Created game log - ID: {game_id}, Path: {log_filepath}")
        
        # Store absolute filepath in session
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        debug_log("Stored game info in session")
        
        # Initialize game
        task = VSTtask(n_rounds=5, n_quadrants=4, n_queues=1)
        session['game'] = {
            'rounds': task.rounds,
            'biased_quadrant': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'current_round': 0,
            'task_description': task.get_task_description()
        }
        
        debug_log("Game initialized, redirecting to first round")
        return redirect(url_for('round_page', round_number=0))
    except Exception as e:
        debug_log(f"Error in start route: {str(e)}\n{traceback.format_exc()}")
        raise

@app.route('/log_choice', methods=['POST'])
def log_choice():
    debug_log("Processing log_choice request")
    try:
        data = request.get_json()
        if data is None:
            debug_log("No data provided in request")
            return "No data provided", 400
        
        log_filepath = session.get('log_filepath')
        if not log_filepath:
            debug_log("No log_filepath in session")
            debug_log(f"Current session: {dict(session)}")
            return "No active game session", 400
        
        data['game_id'] = session.get('game_id')
        debug_log(f"Attempting to log choice with filepath: {log_filepath}")
        
        success = game_logger.log_choice(log_filepath, data)
        if not success:
            debug_log("Failed to log choice")
            return "Logging failed", 500
        
        return "OK", 200
    except Exception as e:
        debug_log(f"Error in log_choice route: {str(e)}\n{traceback.format_exc()}")
        return str(e), 500

@app.route('/round/<int:round_number>', methods=['GET'])
def round_page(round_number):
    debug_log(f"Accessing round {round_number}")
    try:
        game = session.get('game')
        if not game:
            debug_log("No game in session")
            return redirect(url_for('index'))
        if round_number >= game['n_rounds']:
            debug_log("Round number exceeds max rounds")
            return redirect(url_for('final'))
            
        round_data = game['rounds'][round_number]
        return render_template('round.html', round_number=round_number, round_data=round_data)
    except Exception as e:
        debug_log(f"Error in round_page route: {str(e)}\n{traceback.format_exc()}")
        raise

@app.route('/final', methods=['GET', 'POST'])
def final():
    debug_log("Processing final route")
    try:
        game = session.get('game')
        if not game:
            debug_log("No game in session at final page")
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                chosen = int(request.form.get('biased_quadrant'))
            except (ValueError, TypeError):
                debug_log("Invalid quadrant choice submitted")
                chosen = -1
                
            correct = (chosen == game['biased_quadrant'])
            score = 100 if correct else -100
            
            # Log the final result
            log_filepath = session.get('log_filepath')
            if log_filepath:
                result_data = {
                    'type': 'final_choice',
                    'chosen_quadrant': chosen,
                    'correct': correct,
                    'score': score,
                    'biased_quadrant': game['biased_quadrant']
                }
                success = game_logger.log_choice(log_filepath, result_data)
                if not success:
                    debug_log("Failed to log final choice")
            else:
                debug_log("No log_filepath in session for final choice")
            
            debug_log(f"Game completed - Chosen: {chosen}, Correct: {correct}, Score: {score}")
            return render_template('result.html', chosen=chosen, correct=correct, 
                                score=score, biased=game['biased_quadrant'])
                                
        return render_template('final.html', n_quadrants=game['n_quadrants'])
    except Exception as e:
        debug_log(f"Error in final route: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == '__main__':
    debug_log("Starting Flask application")
    try:
        app.run(debug=True)
    except Exception as e:
        debug_log(f"Error starting Flask app: {str(e)}\n{traceback.format_exc()}")
        raise