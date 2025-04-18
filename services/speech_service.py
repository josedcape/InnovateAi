"""
Service functions for text-to-speech conversion
"""
import os
import uuid
import logging
import requests
import base64
from gtts import gTTS

# Google Cloud TTS client
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud credentials file path
GOOGLE_CREDENTIALS_FILE = os.path.join('credentials', 'botidinamix-g.json')
if os.path.exists(GOOGLE_CREDENTIALS_FILE):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS_FILE
    logger.info(f"Using Google Cloud credentials from {GOOGLE_CREDENTIALS_FILE}")

# Google Cloud API Key - Using this as fallback
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Audio folder path
AUDIO_FOLDER = os.path.join('uploads', 'audio')


def get_google_tts_enhanced(text, language='en', voice='en-US-Neural2-F', speed=1.0):
    """
    Convert text to speech using Google Cloud Text-to-Speech API
    This uses the actual Google Cloud TTS API if API key is available
    Returns the path to the generated audio file
    """
    if not GOOGLE_API_KEY:
        logger.warning("Google API key not set. Falling back to gTTS.")
        return None
    
    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}"
        
        payload = {
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": language,
                "name": voice
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speed
            }
        }
        
        # Map simple language codes to Google's language-region format if needed
        if len(language) == 2:
            if language == 'en':
                payload["voice"]["languageCode"] = "en-US"
            elif language == 'es':
                payload["voice"]["languageCode"] = "es-ES"
            elif language == 'fr':
                payload["voice"]["languageCode"] = "fr-FR"
            elif language == 'de':
                payload["voice"]["languageCode"] = "de-DE"
            elif language == 'it':
                payload["voice"]["languageCode"] = "it-IT"
            elif language == 'ja':
                payload["voice"]["languageCode"] = "ja-JP"
            elif language == 'ko':
                payload["voice"]["languageCode"] = "ko-KR"
            elif language == 'pt':
                payload["voice"]["languageCode"] = "pt-BR"
            elif language == 'ru':
                payload["voice"]["languageCode"] = "ru-RU"
            elif language == 'zh':
                payload["voice"]["languageCode"] = "cmn-CN"
        
        # Select appropriate voice based on language
        if payload["voice"]["languageCode"].startswith("en"):
            payload["voice"]["name"] = "en-US-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("es"):
            payload["voice"]["name"] = "es-ES-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("fr"):
            payload["voice"]["name"] = "fr-FR-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("de"):
            payload["voice"]["name"] = "de-DE-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("it"):
            payload["voice"]["name"] = "it-IT-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("ja"):
            payload["voice"]["name"] = "ja-JP-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("ko"):
            payload["voice"]["name"] = "ko-KR-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("pt"):
            payload["voice"]["name"] = "pt-BR-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("ru"):
            payload["voice"]["name"] = "ru-RU-Neural2-F"
        elif payload["voice"]["languageCode"].startswith("cmn"):
            payload["voice"]["name"] = "cmn-CN-Neural2-F"
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            audio_content = response.json().get("audioContent")
            if audio_content:
                # Create a unique filename
                filename = f"{uuid.uuid4()}.mp3"
                file_path = os.path.join(AUDIO_FOLDER, filename)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write audio content to file
                import base64
                with open(file_path, "wb") as audio_file:
                    audio_file.write(base64.b64decode(audio_content))
                
                return file_path
        
        logger.error(f"Google TTS API error: {response.status_code} - {response.text}")
        return None
    
    except Exception as e:
        logger.error(f"Error using Google Cloud TTS: {e}")
        return None


def text_to_speech_gtts(text, lang='en'):
    """
    Convert text to speech using gTTS library (offline/free version)
    Returns the path to the generated audio file
    """
    try:
        # Verify that we have text to speak
        if not text or text.strip() == '':
            logger.error("Empty text provided for speech conversion")
            # Use default error message instead of failing
            text = "Lo siento, hubo un problema al generar una respuesta de voz."
        
        # Create a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(AUDIO_FOLDER, filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang=lang)
        tts.save(file_path)
        
        return file_path
    
    except Exception as e:
        logger.error(f"Error using gTTS: {e}")
        # Create a fallback error message audio instead of raising exception
        try:
            error_filename = f"error_{uuid.uuid4()}.mp3"
            error_file_path = os.path.join(AUDIO_FOLDER, error_filename)
            os.makedirs(os.path.dirname(error_file_path), exist_ok=True)
            
            error_tts = gTTS(text="Lo siento, hubo un problema al convertir el texto a voz.", lang=lang)
            error_tts.save(error_file_path)
            return error_file_path
        except:
            # If even the error message fails, then we raise the original exception
            raise Exception(f"Failed to convert text to speech: {e}")


def get_google_cloud_tts(text, language='en', voice=None):
    """
    Convert text to speech using Google Cloud Text-to-Speech client library
    This uses the Google Cloud credentials file
    Returns the path to the generated audio file
    """
    if not GOOGLE_TTS_AVAILABLE or not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        logger.warning("Google Cloud credentials not found or library not available")
        return None
    
    try:
        # Initialize the client
        client = texttospeech.TextToSpeechClient()
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Map simple language codes to Google's language-region format if needed
        voice_language = language
        if len(language) == 2:
            if language == 'en':
                voice_language = "en-US"
            elif language == 'es':
                voice_language = "es-ES"
            elif language == 'fr':
                voice_language = "fr-FR"
            elif language == 'de':
                voice_language = "de-DE"
            elif language == 'it':
                voice_language = "it-IT"
            elif language == 'ja':
                voice_language = "ja-JP"
            elif language == 'ko':
                voice_language = "ko-KR"
            elif language == 'pt':
                voice_language = "pt-BR"
            elif language == 'ru':
                voice_language = "ru-RU"
            elif language == 'zh':
                voice_language = "cmn-CN"
        
        # Select voice based on language
        voice_name = voice if voice else f"{voice_language}-Neural2-F"
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_language,
            name=voice_name
        )
        
        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Create a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(AUDIO_FOLDER, filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the response to the output file
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"Successfully created speech file: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error using Google Cloud TTS client: {e}")
        return None


def text_to_speech(text, language='en', voice=None):
    """
    Main entry point for text-to-speech conversion
    Tries different TTS methods in order of preference:
    We're starting with gTTS since we're having issues with Google Cloud
    1. gTTS (primary method for now)
    2. Google Cloud TTS client (using credentials file)
    3. Google Cloud TTS REST API (using API key)
    """
    # Check if text is empty or None
    if not text or text.strip() == '':
        logger.error("Empty text provided to text_to_speech")
        text = "Lo siento, hubo un problema al generar una respuesta."
    
    # Start with gTTS because we're having issues with Google Cloud TTS
    try:
        logger.info(f"Converting text to speech using gTTS: {text[:50]}...")
        tts_file_path = text_to_speech_gtts(text, lang=language)
        if tts_file_path:
            return tts_file_path
    except Exception as e:
        logger.warning(f"Could not use gTTS: {e}")
    
    # If gTTS fails, try Google Cloud options
    tts_file_path = None
    
    # Try Google Cloud TTS client (credentials-based)
    try:
        tts_file_path = get_google_cloud_tts(text, language=language, voice=voice)
        if tts_file_path:
            return tts_file_path
    except Exception as e:
        logger.warning(f"Could not use Google Cloud TTS client: {e}")
    
    # If that fails, try the REST API with API key
    if GOOGLE_API_KEY:
        try:
            voice_to_use = voice if voice else 'en-US-Neural2-F'
            tts_file_path = get_google_tts_enhanced(text, language=language, voice=voice_to_use)
            if tts_file_path:
                return tts_file_path
        except Exception as e:
            logger.warning(f"Could not use Google TTS API: {e}")
    
    # If we got here, all methods failed - create a static message
    logger.error("All TTS methods failed")
    
    # Create a static error audio file if none exists
    error_path = os.path.join(AUDIO_FOLDER, "error_message.mp3")
    if not os.path.exists(error_path):
        try:
            os.makedirs(os.path.dirname(error_path), exist_ok=True)
            error_tts = gTTS(text="Lo siento, hubo un problema con la síntesis de voz.", lang="es")
            error_tts.save(error_path)
        except:
            # If even this fails, we'll return None and let the caller handle it
            return None
    
    return error_path