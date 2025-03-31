"""
Service functions for interacting with OpenAI API
"""
import os
import openai
import speech_recognition as sr
from openai import OpenAI
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def create_openai_client():
    """Create and return an OpenAI client"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
    
    return OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(client, audio_path):
    """Transcribe audio file using OpenAI Whisper API"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcription.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise Exception(f"Failed to transcribe audio: {e}")


def detect_language(client, text_sample):
    """Detect language from text sample"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are a language detection expert. Identify the language of the text and respond with only the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish, etc.)"
                },
                {
                    "role": "user",
                    "content": text_sample[:100]  # Use just the first 100 chars for efficiency
                }
            ],
            max_tokens=10,
            temperature=0.3,
        )
        
        # Extract language code from the response
        language_code = response.choices[0].message.content.strip().lower()
        
        # Validate the language code (basic check)
        if len(language_code) > 5:  # If the response is longer than expected
            return "en"  # Default to English
        
        return language_code
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return "en"  # Default to English on failure


def process_query_default(client, input_data, is_text=False):
    """Process a query using standard conversation capabilities"""
    try:
        # Handle text input
        if is_text:
            transcript = input_data  # Already have the text
        else:
            # Transcribe audio to text
            transcript = transcribe_audio(client, input_data)
        
        # Process with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are INNOVATE AI, a helpful AI assistant for a digital software and marketing agency. You provide concise, accurate, and helpful responses."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            temperature=0.7,
        )
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with default agent: {e}")
        raise Exception(f"Failed to process query: {e}")


def process_query_with_web_search(client, input_data, is_text=False):
    """Process a query using web search capabilities"""
    try:
        # Handle text input
        if is_text:
            transcript = input_data  # Already have the text
        else:
            # Transcribe audio to text
            transcript = transcribe_audio(client, input_data)
        
        # Process with web search assistant
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are INNOVATE AI, a helpful AI assistant with web search capabilities. "
                    "This means you have the ability to search the internet for the latest information to provide accurate and up-to-date responses. "
                    "Be concise but thorough in your answers."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            tools=[{"type": "web_search"}],  # Enable web search capability
            temperature=0.7,
        )
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with web search: {e}")
        raise Exception(f"Failed to process query with web search: {e}")


def process_query_with_computer_use(client, input_data, is_text=False):
    """Process a query using computer use capabilities"""
    try:
        # Handle text input
        if is_text:
            transcript = input_data  # Already have the text
        else:
            # Transcribe audio to text
            transcript = transcribe_audio(client, input_data)
        
        # Process with computer use assistant
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are INNOVATE AI, an AI assistant with computer use capabilities. "
                    "You can assist with tasks related to computer usage, such as file organization, "
                    "basic system operations, and software recommendations. "
                    "Provide helpful guidance on computer-related tasks."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            tools=[{"type": "code_interpreter"}],  # Enable code interpreter as a substitute for computer use
            temperature=0.7,
        )
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with computer use: {e}")
        raise Exception(f"Failed to process query with computer use: {e}")


def process_query_with_file_search(client, input_data, vector_store_id=None, is_text=False):
    """Process a query using file search capabilities"""
    try:
        # Handle text input
        if is_text:
            transcript = input_data  # Already have the text
        else:
            # Transcribe audio to text
            transcript = transcribe_audio(client, input_data)
        
        if not vector_store_id:
            return transcript, "I don't have any files to search through yet. Please upload some files first."
        
        # Process with file search assistant
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are INNOVATE AI, an AI assistant with file search capabilities. "
                    "You can search through uploaded documents to find relevant information. "
                    "When referencing information from files, mention the source document."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            tools=[{"type": "file_search", "file_search": {"vector_store_ids": [vector_store_id]}}],
            temperature=0.7,
        )
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with file search: {e}")
        raise Exception(f"Failed to process query with file search: {e}")