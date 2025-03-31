import os
import json
import logging
from openai import OpenAI
import speech_recognition as sr
from .speech_service import text_to_speech
import tempfile

# Configure logging
logger = logging.getLogger(__name__)

def create_openai_client():
    """Create and return an OpenAI client"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("No OpenAI API key found")
        raise ValueError("OpenAI API key is required")
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    return OpenAI(api_key=api_key)

def transcribe_audio(client, audio_path):
    """Transcribe audio file using OpenAI Whisper API"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        logger.debug(f"Transcription: {transcription.text}")
        return transcription.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise

def detect_language(client, text_sample):
    """Detect language from text sample"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a language detection tool. Analyze the provided text and return only the ISO language code (e.g., 'en', 'es', 'fr', 'de', 'ja', etc.) of the most likely language. Return only the language code, nothing else."},
                {"role": "user", "content": text_sample}
            ],
            max_tokens=10
        )
        
        detected_lang = response.choices[0].message.content.strip().lower()
        logger.debug(f"Detected language: {detected_lang}")
        return detected_lang
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        return "en"  # Default to English on error

def process_query_default(client, audio_path):
    """Process a query using standard conversation capabilities"""
    try:
        # Transcribe audio
        transcript = transcribe_audio(client, audio_path)
        
        # Detect language
        language = detect_language(client, transcript)
        
        # Process with OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are INNOVATE AI, a helpful, professional, and friendly AI assistant for a software development and marketing digital agency called INNOVATE. You provide concise, accurate responses. Keep your responses under 150 words unless detailed explanation is necessary."},
                {"role": "user", "content": transcript}
            ]
        )
        
        response_text = response.choices[0].message.content
        
        # Generate speech from response
        audio_path = text_to_speech(response_text, language)
        
        return {
            "success": True,
            "transcript": transcript,
            "response": response_text,
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        }
    except Exception as e:
        logger.error(f"Error in default query processing: {str(e)}")
        return {"success": False, "error": str(e)}

def process_query_with_web_search(client, audio_path):
    """Process a query using web search capabilities"""
    try:
        # Transcribe audio
        transcript = transcribe_audio(client, audio_path)
        
        # Detect language
        language = detect_language(client, transcript)
        
        # Process with OpenAI's web search capability
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are INNOVATE AI's Web Search Agent, a helpful assistant that can search the web for current information. You always cite your sources with links at the end of your response."},
                {"role": "user", "content": transcript}
            ],
            tools=[{
                "type": "web_search",
            }],
            tool_choice="auto"
        )
        
        # Handle tool calls
        message = response.choices[0].message
        tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else None
        
        if tool_calls:
            # Execute web search
            messages = [{"role": "system", "content": "You are INNOVATE AI's Web Search Agent, a helpful assistant that can search the web for current information. You always cite your sources with links at the end of your response."},
                      {"role": "user", "content": transcript},
                      message]
            
            for tool_call in tool_calls:
                # For web_search tools, we don't need to handle the function execution
                # OpenAI does this automatically with tool_outputs in the next request
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "web_search",
                    "content": "Automatic web search results provided by OpenAI"
                })
            
            # Get final response with the search results integrated
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            response_text = final_response.choices[0].message.content
        else:
            response_text = message.content
        
        # Generate speech from response
        audio_path = text_to_speech(response_text, language)
        
        return {
            "success": True,
            "transcript": transcript,
            "response": response_text,
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        }
    except Exception as e:
        logger.error(f"Error in web search query processing: {str(e)}")
        return {"success": False, "error": str(e)}

def process_query_with_computer_use(client, audio_path):
    """Process a query using computer use capabilities"""
    try:
        # Transcribe audio
        transcript = transcribe_audio(client, audio_path)
        
        # Detect language
        language = detect_language(client, transcript)
        
        # Process with OpenAI using the computer use agent capabilities
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are INNOVATE AI's Computer Use Agent, capable of providing detailed guidance on using computers, software, and digital technologies. You explain technical concepts in a clear, accessible way."},
                {"role": "user", "content": transcript}
            ]
        )
        
        response_text = response.choices[0].message.content
        
        # Generate speech from response
        audio_path = text_to_speech(response_text, language)
        
        return {
            "success": True,
            "transcript": transcript,
            "response": response_text,
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        }
    except Exception as e:
        logger.error(f"Error in computer use query processing: {str(e)}")
        return {"success": False, "error": str(e)}

def process_query_with_file_search(client, audio_path, vector_store_id=None):
    """Process a query using file search capabilities"""
    try:
        # Transcribe audio
        transcript = transcribe_audio(client, audio_path)
        
        # Detect language
        language = detect_language(client, transcript)
        
        # If no vector store ID provided, check if we have any files
        if not vector_store_id:
            from .tools_service import get_stored_vector_store_id
            vector_store_id = get_stored_vector_store_id()
        
        if not vector_store_id:
            # No files available
            response_text = "I don't have any files to search through. Please upload documents first using the file upload function."
        else:
            # Process with OpenAI's file search capability
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are INNOVATE AI's File Search Agent, able to search through uploaded documents to find specific information. You provide direct answers from the documents and cite the source files."},
                    {"role": "user", "content": transcript}
                ],
                tools=[{
                    "type": "file_search",
                    "file_search": {
                        "vector_store_id": vector_store_id
                    }
                }],
                tool_choice="auto"
            )
            
            # Handle tool calls
            message = response.choices[0].message
            tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else None
            
            if tool_calls:
                # Execute file search
                messages = [{"role": "system", "content": "You are INNOVATE AI's File Search Agent, able to search through uploaded documents to find specific information. You provide direct answers from the documents and cite the source files."},
                          {"role": "user", "content": transcript},
                          message]
                
                for tool_call in tool_calls:
                    # For file_search tools, OpenAI handles the search results
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "file_search",
                        "content": "Automatic file search results provided by OpenAI"
                    })
                
                # Get final response with the search results integrated
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                
                response_text = final_response.choices[0].message.content
            else:
                response_text = message.content
        
        # Generate speech from response
        audio_path = text_to_speech(response_text, language)
        
        return {
            "success": True,
            "transcript": transcript,
            "response": response_text,
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        }
    except Exception as e:
        logger.error(f"Error in file search query processing: {str(e)}")
        return {"success": False, "error": str(e)}