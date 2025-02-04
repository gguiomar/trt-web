from flask import Flask, jsonify, request
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'test_logs')
os.makedirs(LOGS_DIR, exist_ok=True)

@app.route('/')
def index():
    return '''
    <h1>Test Logger</h1>
    <form action="/create_log" method="get">
        <button type="submit">Create New Log File</button>
    </form>
    <br>
    <form action="/add_entry" method="post">
        <input type="text" name="message" placeholder="Enter a message">
        <button type="submit">Add Log Entry</button>
    </form>
    <br>
    <div id="logs">
        <h2>Existing Logs:</h2>
        <ul>
        {% for log in logs %}
            <li>{{ log }}</li>
        {% endfor %}
        </ul>
    </div>
    '''

@app.route('/create_log')
def create_log():
    try:
        # Generate unique filename
        log_id = str(uuid.uuid4())
        filename = f"log_{log_id}.json"
        filepath = os.path.join(LOGS_DIR, filename)
        
        # Initial log structure
        log_data = {
            'log_id': log_id,
            'created_at': datetime.utcnow().isoformat(),
            'entries': []
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
            
        return jsonify({
            'status': 'success',
            'message': f'Created log file: {filename}',
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/add_entry', methods=['POST'])
def add_entry():
    try:
        message = request.form.get('message', 'No message provided')
        
        # Find most recent log file
        log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
        if not log_files:
            return jsonify({
                'status': 'error',
                'message': 'No log file exists. Create one first.'
            }), 400
            
        latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(LOGS_DIR, x)))
        filepath = os.path.join(LOGS_DIR, latest_log)
        
        # Read current log
        with open(filepath, 'r') as f:
            log_data = json.load(f)
        
        # Add new entry
        log_data['entries'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'message': message
        })
        
        # Write updated log
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
            
        return jsonify({
            'status': 'success',
            'message': 'Added entry to log',
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add debug prints
@app.before_request
def before_request():
    print(f"Processing request: {request.method} {request.path}", flush=True)

@app.after_request
def after_request(response):
    print(f"Request completed with status: {response.status}", flush=True)
    return response

if __name__ == '__main__':
    print(f"Test logs will be saved to: {LOGS_DIR}", flush=True)
    # Changed host and port for remote access
    app.run(host='0.0.0.0', port=8080, debug=True)