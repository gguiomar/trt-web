import random
import json
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for
import uuid
import logging
import stat


#TODO :split GameLogger and VSTtask into different files, VSTtask should be outside of this repo

# Set up base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure logs directory exists with correct permissions
os.makedirs(LOGS_DIR, mode=0o775, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

class GameLogger:
    def __init__(self, base_dir='logs'):
        self.base_dir = os.path.join(BASE_DIR, base_dir)
        try:
            # Create directory with specific permissions
            os.makedirs(self.base_dir, mode=0o775, exist_ok=True)
            logger.info(f"Game log directory initialized: {self.base_dir}")
            
            # Test write permissions
            test_file = os.path.join(self.base_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            # Set file permissions to 664
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            os.remove(test_file)
            logger.info("Write permissions verified for log directory")
        except Exception as e:
            logger.error(f"Failed to initialize log directory: {e}")
            raise
    
    def create_game_log(self):
        """Create a new game log file and return its ID"""
        try:
            game_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"game_{game_id}_{timestamp}.json"
            
            # Initialize log file with metadata
            log_data = {
                'game_id': game_id,
                'start_time': datetime.utcnow().isoformat(),
                'choices': []
            }
            
            filepath = os.path.join(self.base_dir, filename)
            logger.info(f"Creating new game log: {filepath}")
            
            # Write file with specific permissions
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # Set file permissions to 664
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            
            # Verify the file was created
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Failed to create log file: {filepath}")
                
            logger.info(f"Successfully created game log: {filepath}")
            return game_id, filepath
        except Exception as e:
            logger.error(f"Error creating game log: {e}")
            raise

    def log_choice(self, filepath, choice_data):
        """Log a choice to the specific game's log file"""
        try:
            logger.debug(f"Attempting to log choice to {filepath}: {choice_data}")
            
            if not os.path.exists(filepath):
                logger.error(f"Log file not found: {filepath}")
                return False
            
            # Read existing log
            with open(filepath, 'r') as f:
                log_data = json.load(f)
            
            # Add new choice with timestamp
            choice_data['timestamp'] = datetime.utcnow().isoformat()
            log_data['choices'].append(choice_data)
            
            # Write updated log
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # Ensure file permissions are maintained
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            
            logger.debug("Successfully logged choice")
            return True
        except Exception as e:
            logger.error(f"Error logging choice: {e}")
            return False

# Initialize the game logger
try:
    game_logger = GameLogger()
except Exception as e:
    logger.critical(f"Failed to initialize GameLogger: {e}")
    sys.exit(1)

class VSTtask:
    def __init__(self, n_rounds: int = 5, n_quadrants: int = 4, n_queues: int = 1):
        try:
            logger.debug(f"Initializing VSTtask with rounds={n_rounds}, quadrants={n_quadrants}, queues={n_queues}")
            
            if not 2 <= n_quadrants <= 4:
                raise ValueError("Number of quadrants must be between 2 and 4")
            if n_queues < 1:
                raise ValueError("Number of queues per quadrant must be at least 1")
                
            self.n_rounds = n_rounds
            self.n_quadrants = n_quadrants
            self.n_queues = n_queues
            
            # Setup quadrants and queues
            self.letters = [chr(65 + i) for i in range(n_quadrants * n_queues)]
            self.queue_map = {
                q: self.letters[q*n_queues:(q+1)*n_queues]
                for q in range(n_quadrants)
            }
            
            self.quadrants = list(range(n_quadrants))
            self.biased_quadrant = random.choice(self.quadrants)
            logger.info(f"Biased quadrant set to: {self.biased_quadrant}")
            
            self.rounds = self._generate_rounds()
            logger.debug("VSTtask initialization complete")
        except Exception as e:
            logger.error(f"Error initializing VSTtask: {e}")
            raise

    def _get_color(self, quadrant: int) -> str:
        if quadrant == self.biased_quadrant:
            return 'RED' if random.random() < 0.9 else 'GREEN'
        return random.choice(['RED', 'GREEN'])

    def _generate_rounds(self):
        try:
            logger.debug("Generating rounds")
            attempts = 0
            max_attempts = 1000
            
            while attempts < max_attempts:
                attempts += 1
                rounds = []
                for _ in range(self.n_rounds):
                    round_queues = []
                    for q in self.quadrants:
                        for queue in self.queue_map[q]:
                            round_queues.append({
                                'name': queue,
                                'color': self._get_color(q),
                                'quadrant': q
                            })
                    rounds.append({'queues': round_queues})
                
                if self._validate_rounds([r['queues'] for r in rounds]):
                    logger.info(f"Successfully generated rounds after {attempts} attempts")
                    return rounds
            
            raise RuntimeError(f"Failed to generate valid rounds after {max_attempts} attempts")
        except Exception as e:
            logger.error(f"Error generating rounds: {e}")
            raise

    def _validate_rounds(self, rounds):
        try:
            color_counts = {q: {'RED': 0, 'GREEN': 0} for q in self.quadrants}
            for round_queues in rounds:
                for queue in round_queues:
                    q = queue['quadrant']
                    color = queue['color']
                    color_counts[q][color] += 1
                    
            for q in self.quadrants:
                total = color_counts[q]['RED'] + color_counts[q]['GREEN']
                if total == 0:
                    return False
                red_ratio = color_counts[q]['RED'] / total
                if q == self.biased_quadrant:
                    if red_ratio < 0.8:
                        return False
                elif not (0.35 <= red_ratio <= 0.65):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating rounds: {e}")
            raise
    
    def get_round_data(self, round_num: int):
        try:
            return self.rounds[round_num]
        except IndexError as e:
            logger.error(f"Invalid round number {round_num}: {e}")
            raise
    
    def get_task_description(self) -> str:
        return (
            f"You will play a game with {self.n_rounds} rounds.<br>"
            "In each round you'll see active queues (clickable buttons):<br>"
            "One quadrant has 90% one color / 10% the other<br>"
            "Other quadrants have a 50/50 color distribution<br>"
            "At least one queue is active per round<br>"
            "Active queues disappear after a short duration.<br><br>"
            f"After {self.n_rounds} rounds, identify the biased quadrant.<br>"
            "Correct: +100 points, Wrong: -100 points."
        )

@app.route('/')
def index():
    try:
        logger.debug("Rendering index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        raise

@app.route('/start')
def start():
    try:
        # Log session state before
        logger.debug(f"Session before start: {dict(session)}")
        
        # Create new game log file
        game_id, log_filepath = game_logger.create_game_log()
        
        # Store game ID and log filepath in session
        session['game_id'] = game_id
        session['log_filepath'] = log_filepath
        
        # Initialize game
        n_rounds = 5
        n_quadrants = 4
        n_queues = 1
        task = VSTtask(n_rounds=n_rounds, n_quadrants=n_quadrants, n_queues=n_queues)
        
        session['game'] = {
            'rounds': task.rounds,
            'biased_quadrant': task.biased_quadrant,
            'n_rounds': task.n_rounds,
            'n_quadrants': task.n_quadrants,
            'current_round': 0,
            'task_description': task.get_task_description()
        }
        
        # Log session state after
        logger.debug(f"Session after start: {dict(session)}")
        
        return redirect(url_for('round_page', round_number=0))
    except Exception as e:
        logger.error(f"Error in start route: {e}")
        raise

@app.route('/log_choice', methods=['POST'])
def log_choice():
    try:
        data = request.get_json()
        if data is None:
            logger.error("No data provided in request")
            return "No data provided", 400
        
        # Get the log filepath from session
        log_filepath = session.get('log_filepath')
        if not log_filepath:
            logger.error("No log_filepath in session")
            logger.debug(f"Current session state: {dict(session)}")
            return "No active game session", 400
        
        # Add game ID to the log data
        data['game_id'] = session.get('game_id')
        
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(log_filepath), mode=0o775, exist_ok=True)
        
        # Log the choice
        success = game_logger.log_choice(log_filepath, data)
        if not success:
            logger.error("Failed to log choice")
            return "Logging failed", 500
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in log_choice route: {e}")
        return str(e), 500

@app.route('/round/<int:round_number>', methods=['GET'])
def round_page(round_number):
    try:
        logger.debug(f"Accessing round {round_number}")
        game = session.get('game')
        if not game:
            logger.error("No game in session")
            return redirect(url_for('index'))
        if round_number >= game['n_rounds']:
            logger.debug(f"Round {round_number} exceeds max rounds, redirecting to final")
            return redirect(url_for('final'))
            
        round_data = game['rounds'][round_number]
        logger.debug(f"Rendering round {round_number} with data: {round_data}")
        
        return render_template('round.html', round_number=round_number, round_data=round_data)
    except Exception as e:
        logger.error(f"Error in round_page route: {e}")
        raise

@app.route('/final', methods=['GET', 'POST'])
def final():
    try:
        game = session.get('game')
        if not game:
            logger.error("No game in session at final page")
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                chosen = int(request.form.get('biased_quadrant'))
            except (ValueError, TypeError):
                logger.error("Invalid quadrant choice submitted")
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
                    logger.error("Failed to log final choice")
            else:
                logger.error("No log_filepath in session for final choice")
            
            logger.info(f"Game completed - Chosen: {chosen}, Correct: {correct}, Score: {score}")
            return render_template('result.html', chosen=chosen, correct=correct, 
                                score=score, biased=game['biased_quadrant'])
                                
        return render_template('final.html', n_quadrants=game['n_quadrants'])
    except Exception as e:
        logger.error(f"Error in final route: {e}")
        raise


if __name__ == '__main__':
    # Ensure the log directory exists with correct permissions
    os.makedirs(LOGS_DIR, mode=0o775, exist_ok=True)
    
    # Set up the Flask logger to use our configuration
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
    app.logger.addHandler(logging.FileHandler(os.path.join(BASE_DIR, 'app.log')))
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)
    
    # Try to ensure app.log has correct permissions
    try:
        app_log_path = os.path.join(BASE_DIR, 'app.log')
        if os.path.exists(app_log_path):
            os.chmod(app_log_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
    except Exception as e:
        print(f"Warning: Could not set app.log permissions: {e}")
    
    app.run(debug=True)