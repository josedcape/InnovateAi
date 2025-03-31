import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import logging
import json

from models.agents import get_all_agents, get_agent_by_type
from services.openai_service import (
    create_openai_client, 
    process_query_default, 
    process_query_with_web_search,
    process_query_with_computer_use,
    process_query_with_file_search,
    detect_language
)
from services.tools_service import (
    upload_file_to_vector_store,
    get_available_files,
    get_stored_vector_store_id
)
from utils.audio_utils import save_audio_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "innovate-ai-secret")

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure temp directory for audio files
TEMP_AUDIO_FOLDER = os.path.join(tempfile.gettempdir(), 'innovate_audio')
if not os.path.exists(TEMP_AUDIO_FOLDER):
    os.makedirs(TEMP_AUDIO_FOLDER)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/get_agents')
def get_agents():
    """Return all available agents"""
    return jsonify(get_all_agents())

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    return send_from_directory(tempfile.gettempdir(), filename)

@app.route('/process_speech', methods=['POST'])
def process_speech():
    """Process speech audio from the client"""
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"})
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"success": False, "error": "Empty audio file provided"})
        
        # Get tool type from the request
        tool_type = request.form.get('tool_type', 'default')
        
        # Save audio file
        audio_path = save_audio_file(audio_file)
        
        # Create OpenAI client
        client = create_openai_client()
        
        # Process based on tool type
        if tool_type == 'web_search':
            result = process_query_with_web_search(client, audio_path)
        elif tool_type == 'computer_use':
            result = process_query_with_computer_use(client, audio_path)
        elif tool_type == 'file_search':
            # Check if we have a vector store ID
            vector_store_id = get_stored_vector_store_id()
            result = process_query_with_file_search(client, audio_path, vector_store_id)
        else:
            # Default processing
            result = process_query_default(client, audio_path)
        
        # Clean up the audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary audio file: {str(e)}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Upload a file for vector store indexing"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "Empty file provided"})
        
        # Save file to uploads directory
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create OpenAI client
        client = create_openai_client()
        
        # Upload file to vector store
        file_id, vector_store_id = upload_file_to_vector_store(client, file_path)
        
        return jsonify({
            "success": True, 
            "message": f"File '{filename}' uploaded successfully",
            "file_id": file_id,
            "vector_store_id": vector_store_id
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_files')
def get_files():
    """Get list of files available in the vector store"""
    try:
        # Create OpenAI client
        client = create_openai_client()
        
        # Get files
        files = get_available_files(client)
        
        return jsonify({"success": True, "files": files})
    
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/detect_language', methods=['POST'])
def detect_language_endpoint():
    """Detect language from a text sample using OpenAI"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"success": False, "error": "No text provided"})
        
        text_sample = data['text']
        
        # Create OpenAI client
        client = create_openai_client()
        
        # Detect language
        language = detect_language(client, text_sample)
        
        return jsonify({"success": True, "language": language})
    
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        return jsonify({"success": False, "error": str(e)})