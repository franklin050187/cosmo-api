from shipcomcot import analyze_ship
import json

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/analyze')
def analyze():
    url = request.args.get('url')
    if not url:
            # Create a dictionary with your values
        data = {
        "error": "No URL provided",
        }
        return json.dumps(data)
    else:
        return analyze_ship(url)
    
if __name__ == '__main__':
    app.run(debug=True)
    