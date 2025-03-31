"""
Utility functions for video processing
"""
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_video_duration(video_path):
    """
    Get the duration of a video file using ffprobe/ffmpeg
    Returns the duration in seconds or None if an error occurs
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
        
        # Run ffprobe to get duration
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error getting video duration: {result.stderr}")
            return None
        
        # Parse the duration as a float
        duration = float(result.stdout.strip())
        return duration
    
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return None