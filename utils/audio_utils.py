import os
import tempfile
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

def save_audio_file(audio_file):
    """
    Save audio file to temporary location and return path
    """
    try:
        # Create a unique filename for the audio file
        filename = f"audio_{uuid.uuid4().hex}.wav"
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # Save the audio file
        audio_file.save(file_path)
        
        logger.debug(f"Saved audio file to: {file_path}")
        
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving audio file: {str(e)}")
        raise