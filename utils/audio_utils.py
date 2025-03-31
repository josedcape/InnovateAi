"""
Utility functions for audio processing
"""
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Audio folder path
AUDIO_FOLDER = os.path.join('uploads', 'audio')


def save_audio_file(audio_file):
    """
    Save audio file to temporary location and return path
    """
    try:
        # Ensure the directory exists
        os.makedirs(AUDIO_FOLDER, exist_ok=True)
        
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.webm"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        
        # Save the file
        audio_file.save(filepath)
        
        return filepath
    except Exception as e:
        logger.error(f"Error saving audio file: {e}")
        raise Exception(f"Failed to save audio file: {e}")