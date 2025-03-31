import os
import json
import logging
import tempfile

# Configure logging
logger = logging.getLogger(__name__)

# Constants
VECTOR_STORE_FILE = 'vector_store_id.json'

def get_stored_vector_store_id():
    """Retrieve stored vector store ID from file if exists"""
    try:
        file_path = os.path.join(tempfile.gettempdir(), VECTOR_STORE_FILE)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get('vector_store_id')
        
        return None
    except Exception as e:
        logger.error(f"Error retrieving vector store ID: {str(e)}")
        return None

def save_vector_store_id(vector_store_id):
    """Save vector store ID to file for persistence"""
    try:
        file_path = os.path.join(tempfile.gettempdir(), VECTOR_STORE_FILE)
        
        with open(file_path, 'w') as f:
            json.dump({'vector_store_id': vector_store_id}, f)
        
        logger.debug(f"Saved vector store ID: {vector_store_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving vector store ID: {str(e)}")
        return False

def upload_file_to_vector_store(client, file_path):
    """
    Upload a file to OpenAI's vector store for file search
    Returns: (file_id, vector_store_id)
    """
    try:
        # First, upload file to OpenAI
        with open(file_path, 'rb') as file:
            file_response = client.files.create(
                file=file,
                purpose="assistants"
            )
        
        file_id = file_response.id
        logger.debug(f"File uploaded with ID: {file_id}")
        
        # Get or create vector store
        vector_store_id = get_stored_vector_store_id()
        
        if not vector_store_id:
            # Create a new vector store
            vector_store_response = client.beta.vector_stores.create(
                name="INNOVATE AI Document Store"
            )
            
            vector_store_id = vector_store_response.id
            logger.debug(f"Created new vector store with ID: {vector_store_id}")
            
            # Save vector store ID for future use
            save_vector_store_id(vector_store_id)
        
        # Add file to vector store
        file_vector_response = client.beta.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=[file_id]
        )
        
        batch_id = file_vector_response.id
        logger.debug(f"Added file to vector store, batch ID: {batch_id}")
        
        return file_id, vector_store_id
    except Exception as e:
        logger.error(f"Error uploading file to vector store: {str(e)}")
        raise

def get_file_status_in_vector_store(client, vector_store_id, file_id):
    """Get the status of a file in the vector store"""
    try:
        # Get file information
        file_info = client.files.retrieve(file_id)
        
        # Check for batch status in vector store
        batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        for batch in batches.data:
            # Check if this batch contains our file
            file_ids = getattr(batch, 'file_ids', [])
            if file_id in file_ids:
                return {
                    'file_id': file_id,
                    'filename': file_info.filename,
                    'size_bytes': file_info.bytes,
                    'created_at': file_info.created_at,
                    'status': batch.status,
                    'batch_id': batch.id
                }
        
        return None
    except Exception as e:
        logger.error(f"Error getting file status: {str(e)}")
        return None

def get_available_files(client, vector_store_id=None):
    """
    Get list of files available in the vector store
    """
    try:
        # If vector store ID not provided, get from stored value
        if not vector_store_id:
            vector_store_id = get_stored_vector_store_id()
        
        if not vector_store_id:
            # No vector store available
            return []
        
        # Get files from vector store
        files_list = []
        batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        for batch in batches.data:
            # Only consider completed batches
            if batch.status == 'completed':
                # Get file IDs in this batch
                file_ids = getattr(batch, 'file_ids', [])
                
                # Get file details for each file
                for file_id in file_ids:
                    try:
                        file_info = client.files.retrieve(file_id)
                        
                        files_list.append({
                            'file_id': file_id,
                            'filename': file_info.filename,
                            'size_bytes': file_info.bytes,
                            'created_at': file_info.created_at,
                            'batch_id': batch.id
                        })
                    except Exception as e:
                        logger.warning(f"Error retrieving file {file_id}: {str(e)}")
        
        return files_list
    except Exception as e:
        logger.error(f"Error getting available files: {str(e)}")
        return []

def delete_file_from_vector_store(client, vector_store_id, file_id):
    """
    Delete a file from the vector store and OpenAI File API
    """
    try:
        # First, get the batch containing this file
        batches = client.beta.vector_stores.file_batches.list(
            vector_store_id=vector_store_id
        )
        
        batch_id = None
        for batch in batches.data:
            file_ids = getattr(batch, 'file_ids', [])
            if file_id in file_ids:
                batch_id = batch.id
                break
        
        if batch_id:
            # Delete file from vector store
            client.beta.vector_stores.file_batches.cancel(
                vector_store_id=vector_store_id,
                file_batch_id=batch_id
            )
            
            logger.debug(f"Cancelled batch {batch_id} in vector store")
        
        # Delete file from OpenAI Files API
        client.files.delete(file_id)
        logger.debug(f"Deleted file {file_id} from OpenAI Files API")
        
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False