from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from twilio.rest import Client
# configure from env vars
TWILIO_SID = "AC75717d7a940c9730f04ecefb655db77b"
TWILIO_AUTH = "d6a92d2db778da4eb778091db94a8b99"
TWILIO_FROM = "+12173953031"
client = Client(TWILIO_SID, TWILIO_AUTH)

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

@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json()
    to = data.get('to')
    body = data.get('body')
    if not to or not body:
        return jsonify({"error":"bad request"}), 400
    msg = client.messages.create(body=body, from_=TWILIO_FROM, to=to)
    return jsonify({"sid": msg.sid})

if __name__ == "__main__":
    # run on 0.0.0.0 so EC2 can receive requests
    app.run(host="0.0.0.0", port=5000)
