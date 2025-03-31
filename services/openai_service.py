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
                    "content": "Eres INNOVATE AI, un asistente de IA avanzado para una agencia de software y marketing digital. "
                    "Proporcionas respuestas concisas, precisas y útiles. Hablas el mismo idioma que el usuario, adaptándote "
                    "a su forma de comunicación. Eres respetuoso y profesional en todo momento. Para preguntas en español, "
                    "respondes en español, y para preguntas en otros idiomas, respondes en el idioma correspondiente cuando sea posible."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            temperature=0.7,
            max_tokens=800,
        )
        
        # Handle empty response or null content
        if not response or not response.choices or not response.choices[0].message.content:
            return transcript, "Lo siento, no pude generar una respuesta. Por favor intenta reformular tu pregunta."
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with default agent: {e}")
        raise Exception(f"Failed to process query: {e}")


def process_query_with_web_search(client, input_data, is_text=False):
    """Process a query using web search capabilities with GPT-4o-search-preview"""
    try:
        # Handle text input
        if is_text:
            transcript = input_data  # Already have the text
        else:
            # Transcribe audio to text
            transcript = transcribe_audio(client, input_data)
        
        # Process using the new web search model
        try:
            # Try using the new gpt-4o-search-preview model which has integrated web search
            # Based on official OpenAI API docs, we need to use it this way
            response = client.chat.completions.create(
                model="gpt-4o-search-preview",
                web_search_options={
                    "user_location": {
                        "type": "approximate",
                        "approximate": {
                            "country": "ES",
                            "city": "Madrid",
                            "region": "Madrid",
                        }
                    }
                },
                messages=[
                    {
                        "role": "system",
                        "content": "Eres INNOVATE AI, un asistente de IA con capacidades de búsqueda web. "
                        "Tienes la capacidad de buscar en internet para proporcionar información actualizada y precisa. "
                        "Debes ser conciso pero completo en tus respuestas. Prioriza fuentes confiables y actualizada. "
                        "Habla en el mismo idioma que el usuario. Si te preguntan en español, responde en español."
                    },
                    {
                        "role": "user",
                        "content": f"Busca información actualizada sobre: {transcript}"
                    }
                ],
                # No se utiliza temperature aquí porque el modelo gpt-4o-search-preview no lo soporta
            )
            
            # Handle empty response
            if not response or not response.choices or not response.choices[0].message.content:
                return transcript, "Lo siento, no pude encontrar información sobre ese tema. Por favor intenta con otra búsqueda."
                
            return transcript, response.choices[0].message.content
            
        except Exception as search_error:
            # Log the error but continue with fallback
            logger.warning(f"New search model failed: {search_error}, falling back to tools approach")
            
            # Fallback to the tools approach
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system",
                        "content": "Eres INNOVATE AI, un asistente de IA con capacidades de búsqueda web. "
                        "Tienes la capacidad de buscar en internet para proporcionar información actualizada y precisa. "
                        "Debes ser conciso pero completo en tus respuestas. Si no puedes buscar en la web o no tienes "
                        "acceso a la información solicitada, explica claramente que no puedes acceder a esa información "
                        "en este momento, pero ofrece alternativas de lo que podrías hacer por el usuario."
                    },
                    {
                        "role": "user",
                        "content": transcript
                    }
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information on a given query. Use this when you need to find up-to-date information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string", 
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }],
                tool_choice="auto",
                temperature=0.7,
                max_tokens=800,
            )
            
            # Handle tool calls in a safer way
            tool_call_info = ""
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                try:
                    # Extract function name and arguments without trying to serialize the entire function object
                    tool_call = response.choices[0].message.tool_calls[0]
                    tool_info = {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                    tool_call_info = "\n\nIntento de búsqueda: " + json.dumps(tool_info)
                    logger.info(f"Tool call info: {tool_call_info}")
                except Exception as tool_error:
                    logger.error(f"Error extracting tool call info: {tool_error}")
            
            # Handle empty response
            if not response or not response.choices or not response.choices[0].message.content:
                return transcript, f"Lo siento, no pude encontrar información sobre ese tema. Por favor intenta con otra búsqueda.{tool_call_info}"
                
            return transcript, response.choices[0].message.content
            
    except Exception as e:
        logger.error(f"Error processing query with web search: {e}")
        # Si transcript no está definido en este punto, es por un error muy temprano
        if 'transcript' not in locals():
            transcript = "Error de procesamiento"
        return transcript, "Lo siento, hubo un problema con la búsqueda web. Por favor intenta nuevamente con una consulta diferente."


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
                    "content": "Eres INNOVATE AI, un asistente de IA con capacidades de uso de computadora. "
                    "Puedes ayudar con tareas relacionadas con el uso de computadoras, como organización de archivos, "
                    "operaciones básicas del sistema y recomendaciones de software. "
                    "Si te piden abrir una página web o ejecutar un programa específico, explica amablemente que eres "
                    "un asistente virtual y no puedes controlar directamente la computadora del usuario, pero puedes "
                    "proporcionar instrucciones paso a paso sobre cómo hacerlo."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "code_interpreter",
                    "description": "Execute code or analyze data. Use this to help users with computational tasks."
                }
            }],
            tool_choice="auto",
            temperature=0.7,
            max_tokens=800,
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
            return transcript, "No tengo archivos disponibles para buscar. Por favor, sube algunos archivos primero."
        
        # Process with file search assistant
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "Eres INNOVATE AI, un asistente de IA con capacidades de búsqueda en archivos. "
                    "Puedes buscar en documentos subidos para encontrar información relevante. "
                    "Cuando hagas referencia a información de los archivos, menciona el documento fuente. "
                    "Adaptate al idioma del usuario, respondiendo en español si te preguntan en español."
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "file_search",
                    "description": "Search through uploaded files to find relevant information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vector_store_ids": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "The IDs of the vector stores to search through."
                            }
                        },
                        "required": ["vector_store_ids"]
                    }
                }
            }],
            tool_choice={
                "type": "function",
                "function": {
                    "name": "file_search"
                }
            },
            temperature=0.7,
            max_tokens=800,
        )
        
        return transcript, response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing query with file search: {e}")
        raise Exception(f"Failed to process query with file search: {e}")