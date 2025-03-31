import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
# setup a secret key, required by sessions
app.secret_key = os.environ.get("SESSION_SECRET") or "innovate_ai_secret_key"
# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')
FILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'files')
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(FILE_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Import services after app is created
from services.openai_service import (
    create_openai_client, 
    transcribe_audio, 
    detect_language,
    process_query_default,
    process_query_with_web_search,
    process_query_with_computer_use,
    process_query_with_file_search
)
from services.speech_service import text_to_speech
from services.tools_service import (
    upload_file_to_vector_store,
    get_available_files,
    get_stored_vector_store_id
)
from models.agents import get_all_agents, AgentType
from utils.audio_utils import save_audio_file


with app.app_context():
    # Import the models here to ensure tables are created
    import models  # noqa: F401
    db.create_all()


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Return all available agents"""
    agents = get_all_agents()
    return jsonify([agent.to_dict() for agent in agents])


@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    return send_from_directory(AUDIO_FOLDER, filename)


@app.route('/api/speech', methods=['POST'])
def process_speech():
    """Process speech audio from the client"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400
    
    # Get the agent type from the request
    agent_type_str = request.form.get('agent_type', 'default')
    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        agent_type = AgentType.DEFAULT
    
    # Save the audio file
    audio_path = save_audio_file(audio_file)
    
    # Create OpenAI client
    client = create_openai_client()
    
    # Process based on agent type
    try:
        if agent_type == AgentType.WEB_SEARCH:
            # Process with web search
            transcript, response = process_query_with_web_search(client, audio_path)
        elif agent_type == AgentType.COMPUTER_USE:
            # Process with computer use
            transcript, response = process_query_with_computer_use(client, audio_path)
        elif agent_type == AgentType.FILE_SEARCH:
            # Get vector store ID if available
            vector_store_id = get_stored_vector_store_id()
            # Process with file search
            transcript, response = process_query_with_file_search(client, audio_path, vector_store_id)
        else:
            # Default processing
            transcript, response = process_query_default(client, audio_path)
        
        # Convert response text to speech
        # Detect language for better TTS
        detected_lang = detect_language(client, response)
        
        # Generate speech with appropriate language
        audio_path = text_to_speech(response, language=detected_lang)
        
        # Extract just the filename from the path
        audio_filename = os.path.basename(audio_path)
        
        return jsonify({
            'transcript': transcript,
            'response': response,
            'audio_url': f'/audio/{audio_filename}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    """Upload a file for vector store indexing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(FILE_UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Create OpenAI client
    client = create_openai_client()
    
    try:
        # Upload file to vector store
        file_id, vector_store_id = upload_file_to_vector_store(client, filepath)
        
        return jsonify({
            'success': True,
            'message': f'File uploaded successfully: {filename}',
            'file_id': file_id,
            'vector_store_id': vector_store_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of files available in the vector store"""
    # Create OpenAI client
    client = create_openai_client()
    
    try:
        # Get vector store ID if available
        vector_store_id = get_stored_vector_store_id()
        if not vector_store_id:
            return jsonify({'files': [], 'message': 'No vector store initialized yet'})
        
        # Get available files
        files = get_available_files(client, vector_store_id)
        return jsonify({
            'files': files,
            'vector_store_id': vector_store_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/detect-language', methods=['POST'])
def detect_language_endpoint():
    """Detect language from a text sample using OpenAI"""
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'No text provided'}), 400
    
    text = request.json['text']
    
    # Create OpenAI client
    client = create_openai_client()
    
    try:
        detected_lang = detect_language(client, text)
        return jsonify({'language': detected_lang})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)