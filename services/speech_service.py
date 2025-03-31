import os
import tempfile
import uuid
import logging
from gtts import gTTS
import requests
import json
import base64

# Configure logging
logger = logging.getLogger(__name__)

def get_google_tts_enhanced(text, language='en', voice='en-US-Neural2-F', speed=1.0):
    """
    Convert text to speech using Google Cloud Text-to-Speech API
    This uses the actual Google Cloud TTS API if API key is available
    Returns the path to the generated audio file
    """
    try:
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not api_key:
            logger.warning("No Google API key found, falling back to basic gTTS")
            return text_to_speech_gtts(text, language)
        
        # Generate a unique filename
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
        # Prepare request to Google Cloud TTS API
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language,
                "name": voice,
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speed,
                "pitch": 0.0,
                "volumeGainDb": 0.0,
                "effectsProfileId": ["telephony-class-application"]
            }
        }
        
        # Make API request
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            # Process response
            response_data = response.json()
            audio_content = response_data.get('audioContent')
            
            if audio_content:
                # Decode base64 audio content and save to file
                with open(output_path, 'wb') as audio_file:
                    audio_file.write(base64.b64decode(audio_content))
                
                logger.debug(f"Enhanced TTS audio saved to: {output_path}")
                return output_path
            else:
                logger.error("No audio content in response")
                return text_to_speech_gtts(text, language)
        else:
            logger.error(f"Google Cloud TTS API error: {response.status_code} - {response.text}")
            return text_to_speech_gtts(text, language)
    
    except Exception as e:
        logger.error(f"Error in enhanced TTS: {str(e)}")
        return text_to_speech_gtts(text, language)

def text_to_speech_gtts(text, lang='en'):
    """
    Convert text to speech using gTTS library (offline/free version)
    Returns the path to the generated audio file
    """
    try:
        # Generate a unique filename
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
        # Create gTTS object
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to file
        tts.save(output_path)
        
        logger.debug(f"Basic TTS audio saved to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error in basic TTS: {str(e)}")
        raise

def text_to_speech(text, language='en', voice=None):
    """
    Main entry point for text-to-speech conversion
    Tries enhanced Google Cloud TTS first, falls back to gTTS
    """
    try:
        # Default voice based on language
        if not voice:
            if language.startswith('en'):
                voice = 'en-US-Neural2-F'
            elif language.startswith('es'):
                voice = 'es-US-Neural2-B'
            elif language.startswith('fr'):
                voice = 'fr-FR-Neural2-A'
            elif language.startswith('de'):
                voice = 'de-DE-Neural2-B'
            elif language.startswith('ja'):
                voice = 'ja-JP-Neural2-B'
            else:
                voice = 'en-US-Neural2-F'  # Default to English if language not recognized
        
        # Try enhanced TTS first
        return get_google_tts_enhanced(text, language, voice)
    
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        # Last resort fallback
        return text_to_speech_gtts(text, language.split('-')[0])