from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # allow cross-origin from your frontend origin

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    description = data.get('description', '')
    # Placeholder ML logic: very simple heuristics + randomness for demo.
    # Replace with real ML logic as desired.
    keywords = {
        'plumb': 'plumbing',
        'leak': 'plumbing',
        'bug': 'pest_control',
        'electr': 'electrical',
        'light': 'electrical',
        'clean': 'hygiene_cleanliness',
        'door': 'carpentry'
    }
    tags = set()
    desc_lower = description.lower()
    for k, v in keywords.items():
        if k in desc_lower:
            tags.add(v)

    if not tags:
        tags.add('general_maintenance')

    # priority score: base + keyword multipliers + small noise
    base = 3.0
    score = base + len(tags) * 2.0 + random.random() * 3.0
    score = round(score, 2)

    return jsonify({ 'priority_score': score, 'tags': list(tags) })

if __name__ == "__main__":
    # run on 0.0.0.0 so EC2 can receive requests
    app.run(host="0.0.0.0", port=5000)
