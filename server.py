from flask import Flask, request, jsonify
from flask_cors import CORS
from database import (
    insert_document,
    update_field,
    move_to_collection,
    hash_existing_resident_passwords,
    authenticate_resident,
    get_documents,
    add_resident,
    delete_resident
)
import json
from bson import ObjectId
from datetime import datetime
from ai import issue_tag, compute_priority

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze_issue():
    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({'error': 'Missing issue description'}), 400

    description = data['description']
    try:
        tags = issue_tag(description)
        priority_score = compute_priority(tags)
        return jsonify({
            'tags': tags,
            'priority_score': round(priority_score, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)

app.json_encoder = JSONEncoder

@app.route('/api/insert_document', methods=['POST'])
def insert_document_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        collection = request.args.get('collection', 'Issues')
        
        issue_id = insert_document(data, collection)
        if issue_id:
            return jsonify({
                'success': True,
                'message': 'Issue inserted successfully',
                'issue_id': issue_id
            }), 201
        else:
            return jsonify({'error': 'Failed to insert issue'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_field', methods=['POST'])
def update_field_route():
    try:
        data = request.get_json()
        if not data or 'issue_id' not in data or 'field_name' not in data or 'new_value' not in data:
            return jsonify({'error': 'issue_id, field_name and new_value are required'}), 400
        
        issue_id = data['issue_id']
        field_name = data['field_name']
        new_value = data['new_value']
        collection_name = data.get('collection_name', 'Issues')
        
        success = update_field(issue_id, field_name, new_value, collection_name)
        if success:
            return jsonify({
                'success': True,
                'message': f'Field {field_name} updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update field or issue not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/move_to_collection', methods=['POST'])
def move_to_collection_route():
    try:
        data = request.get_json()
        if not data or 'issue_id' not in data:
            return jsonify({'error': 'issue_id is required'}), 400
        
        issue_id = data['issue_id']
        source_collection = data.get('source_collection', 'Issues')
        target_collection = data.get('target_collection', 'Resolved')
        
        success = move_to_collection(issue_id, source_collection, target_collection)
        if success:
            return jsonify({
                'success': True,
                'message': f'Issue moved from {source_collection} to {target_collection}'
            })
        else:
            return jsonify({'error': 'Failed to move issue or issue not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hash_existing_resident_passwords', methods=['POST'])
def hash_existing_resident_passwords_route():
    try:
        hash_existing_resident_passwords()
        return jsonify({
            'success': True,
            'message': 'Password hashing completed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/authenticate_resident', methods=['POST'])
def authenticate_resident_route():
    try:
        data = request.get_json()
        if not data or 'regno' not in data or 'password' not in data:
            return jsonify({'error': 'regno and password are required'}), 400
        
        regno = data['regno']
        password = data['password']
        
        is_authenticated = authenticate_resident(regno, password)
        if is_authenticated:
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'authenticated': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials',
                'authenticated': False
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_documents', methods=['GET'])
def get_documents_route():
    try:
        collection_name = request.args.get('collection_name')
        filter_field = request.args.get('filter_field')
        filter_value = request.args.get('filter_value')
        
        if not collection_name:
            return jsonify({'error': 'collection_name parameter is required'}), 400

        if filter_value is not None:
            if filter_value.isdigit():
                filter_value = int(filter_value)
            elif '.' in filter_value and filter_value.replace('.', '').isdigit():
                filter_value = float(filter_value)
        
        documents = get_documents(collection_name, filter_field, filter_value)
        return jsonify({
            'success': True,
            'documents': documents,
            'count': len(documents)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_resident', methods=['POST'])
def add_resident_route():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'regno' not in data or 'password' not in data:
            return jsonify({'error': 'name, regno, and password are required'}), 400
        
        name = data['name']
        regno = data['regno']
        password = data['password']
        
        success = add_resident(name, regno, password)
        if success:
            return jsonify({
                'success': True,
                'message': 'Resident added successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to add resident or resident already exists'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_resident', methods=['POST'])
def delete_resident_route():
    try:
        data = request.get_json()
        if not data or 'regno' not in data:
            return jsonify({'error': 'regno is required'}), 400
        
        regno = data['regno']
        success = delete_resident(regno)
        if success:
            return jsonify({
                'success': True,
                'message': 'Resident deleted successfully'
            })
        else:
            return jsonify({'error': 'Resident not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Flask backend is running'
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Fixter API Backend',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/insert_issue_to_mongo': 'Insert issue to mongo',
            'POST /api/update_field': 'Update field',
            'POST /api/move_to_collection': 'Move to collection',
            'POST /api/hash_existing_resident_passwords': 'Hash existing resident passwords',
            'POST /api/authenticate_resident': 'Authenticate resident',
            'GET /api/get_documents': 'Get documents',
            'POST /api/add_resident': 'Add resident',
            'POST /api/delete_resident': 'Delete resident',
            'GET /api/health': 'Health check'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
