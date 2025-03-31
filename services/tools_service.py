"""
Service functions for OpenAI tools (file search, vector store, etc.)
"""
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File to store vector store ID
VECTOR_STORE_FILE = 'vector_store_id.json'


def get_stored_vector_store_id():
    """Retrieve stored vector store ID from file if exists"""
    try:
        if os.path.exists(VECTOR_STORE_FILE):
            with open(VECTOR_STORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('vector_store_id')
    except Exception as e:
        logger.error(f"Error retrieving vector store ID: {e}")
    
    return None


def save_vector_store_id(vector_store_id):
    """Save vector store ID to file for persistence"""
    try:
        with open(VECTOR_STORE_FILE, 'w') as f:
            json.dump({'vector_store_id': vector_store_id}, f)
    except Exception as e:
        logger.error(f"Error saving vector store ID: {e}")


def upload_file_to_vector_store(client, file_path):
    """
    Upload a file to OpenAI's vector store for file search
    Returns: (file_id, vector_store_id)
    """
    try:
        # First, check if we already have a vector store ID
        vector_store_id = get_stored_vector_store_id()
        
        # Upload file to OpenAI Files
        with open(file_path, 'rb') as file:
            file_obj = client.files.create(
                file=file,
                purpose="assistants"
            )
        
        file_id = file_obj.id
        
        # If we don't have a vector store ID, create a new one
        if not vector_store_id:
            # Create a vector store for the file (vector collection)
            vector_store = client.beta.vector_stores.create(
                name="INNOVATE AI Document Store",
                expires_after=30 * 24 * 60 * 60  # 30 days in seconds
            )
            vector_store_id = vector_store.id
            save_vector_store_id(vector_store_id)
        
        # Add the file to the vector store
        file_vector = client.beta.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=[file_id]
        )
        
        # Check file batch status
        batch_id = file_vector.id
        batch_status = client.beta.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            file_batch_id=batch_id
        )
        
        logger.info(f"File batch status: {batch_status.status}")
        
        return file_id, vector_store_id
    except Exception as e:
        logger.error(f"Error uploading file to vector store: {e}")
        raise Exception(f"Failed to upload file: {e}")


def get_file_status_in_vector_store(client, vector_store_id, file_id):
    """Get the status of a file in the vector store"""
    try:
        file_batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        # Check all batches for the file
        for batch in file_batches.data:
            batch_info = client.beta.vector_stores.file_batches.retrieve(
                vector_store_id=vector_store_id,
                file_batch_id=batch.id
            )
            
            if file_id in batch_info.file_ids:
                return {
                    'batch_id': batch.id,
                    'status': batch_info.status
                }
        
        return None
    except Exception as e:
        logger.error(f"Error checking file status: {e}")
        return None


def get_available_files(client, vector_store_id=None):
    """
    Get list of files available in the vector store
    """
    if not vector_store_id:
        vector_store_id = get_stored_vector_store_id()
        
    if not vector_store_id:
        return []
    
    try:
        # Get all file batches from the vector store
        file_batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        file_ids = []
        for batch in file_batches.data:
            batch_info = client.beta.vector_stores.file_batches.retrieve(
                vector_store_id=vector_store_id,
                file_batch_id=batch.id
            )
            
            # Only include completed files
            if batch_info.status == "completed":
                file_ids.extend(batch_info.file_ids)
        
        # Get file details
        files = []
        for file_id in file_ids:
            try:
                file_info = client.files.retrieve(file_id)
                files.append({
                    'id': file_info.id,
                    'filename': file_info.filename,
                    'created_at': file_info.created_at,
                    'bytes': file_info.bytes,
                    'status': file_info.status
                })
            except Exception as file_error:
                logger.error(f"Error retrieving file {file_id}: {file_error}")
        
        return files
    except Exception as e:
        logger.error(f"Error getting available files: {e}")
        return []


def delete_file_from_vector_store(client, vector_store_id, file_id):
    """
    Delete a file from the vector store and OpenAI File API
    """
    try:
        # First, remove the file from all batches in the vector store
        file_batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        for batch in file_batches.data:
            batch_info = client.beta.vector_stores.file_batches.retrieve(
                vector_store_id=vector_store_id,
                file_batch_id=batch.id
            )
            
            if file_id in batch_info.file_ids:
                # Remove file from batch
                client.beta.vector_stores.file_batches.delete(
                    vector_store_id=vector_store_id,
                    file_batch_id=batch.id,
                    file_ids=[file_id]
                )
        
        # Now delete the file from OpenAI
        client.files.delete(file_id)
        
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise Exception(f"Failed to delete file: {e}")