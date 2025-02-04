import random
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for
import uuid
from flask_session import Session

# Set up base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
SESSION_DIR = os.path.join(BASE_DIR, 'flask_session')

# Ensure directories exist with proper permissions
os.makedirs(LOGS_DIR, mode=0o775, exist_ok=True)
os.makedirs(SESSION_DIR, mode=0o775, exist_ok=True)

app = Flask(__name__)

# Configure filesystem session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_DIR
app.secret_key = 'your_secret_key_here'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Initialize Flask-Session
Session(app)

class GameLogger:
    def __init__(self, base_dir='logs'):
        self.base_dir = os.path.join(BASE_DIR, base_dir)
        os.makedirs(self.base_dir, mode=0o775, exist_ok=True)
    
    def create_game_log(self):
        """Create a new game log file and return its ID"""
        game_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"game_{game_id}_{timestamp}.json"
        filepath = os.path.join(self.base_dir, filename)
        
        # Initialize log file with metadata
        log_data = {
            'game_id': game_id,
            'start_time': datetime.utcnow().isoformat(),
            'choices': []
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        os.chmod(filepath, 0o664)
        
        return game_id, filepath
    
    def log_choice(self, filepath, choice_data):
        """Log a choice to the specific game's log file"""
        try:
            if not os.path.exists(filepath):
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
            os.chmod(filepath, 0o664)
            
            return True
        except Exception as e:
            print(f"Error logging choice: {e}")
            return False

# Initialize the game logger
game_logger = GameLogger()

class VSTtask:
    def __init__(self, n_rounds: int = 5, n_quadrants: int = 4, n_queues: int = 1):
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
        self.rounds = self._generate_rounds()

    def _get_color(self, quadrant: int) -> str:
        if quadrant == self.biased_quadrant:
            return 'RED' if random.random() < 0.9 else 'GREEN'
        return random.choice(['RED', 'GREEN'])

    def _generate_rounds(self):
        while True:
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
                return rounds

    def _validate_rounds(self, rounds):
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
    
    def get_round_data(self, round_num: int):
        return self.rounds[round_num]
    
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
    return render_template('index.html')

@app.route('/start')
def start():
    try:
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
        
        return redirect(url_for('round_page', round_number=0))
    except Exception as e:
        print(f"Error in start route: {e}")
        raise

@app.route('/log_choice', methods=['POST'])
def log_choice():
    try:
        data = request.get_json()
        if data is None:
            return "No data provided", 400
        
        # Get the log filepath from session
        log_filepath = session.get('log_filepath')
        if not log_filepath:
            return "No active game session", 400
        
        # Add game ID to the log data
        data['game_id'] = session.get('game_id')
        
        # Log the choice
        success = game_logger.log_choice(log_filepath, data)
        if not success:
            return "Logging failed", 500
        
        return "OK", 200
    except Exception as e:
        print(f"Error in log_choice route: {e}")
        return str(e), 500

@app.route('/round/<int:round_number>', methods=['GET'])
def round_page(round_number):
    game = session.get('game')
    if not game:
        return redirect(url_for('index'))
    if round_number >= game['n_rounds']:
        return redirect(url_for('final'))
    round_data = game['rounds'][round_number]
    return render_template('round.html', round_number=round_number, round_data=round_data)

@app.route('/final', methods=['GET', 'POST'])
def final():
    game = session.get('game')
    if not game:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            chosen = int(request.form.get('biased_quadrant'))
        except (ValueError, TypeError):
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
            game_logger.log_choice(log_filepath, result_data)
        
        return render_template('result.html', chosen=chosen, correct=correct, 
                             score=score, biased=game['biased_quadrant'])
                             
    return render_template('final.html', n_quadrants=game['n_quadrants'])

if __name__ == '__main__':
    app.run(debug=True)