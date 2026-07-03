"""Database module for KYC data - saves to cache JSON files."""

import json
import os
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

def create_table():
    """Create cache directory if it doesn't exist."""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Created cache directory: {cache_dir}")

def insert_kyc(data):
    """
    Insert KYC data into cache as a JSON file.
    
    Args:
        data: Dictionary containing KYC information with keys:
              - kyc_data: OCR extracted data (front/back)
              - front_file: Front image filename
              - back_file: Back image filename
              - form_data: (optional) Form submission data
    """
    try:
        create_table()  # Ensure cache dir exists
        
        # Generate unique ID and timestamp
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract relevant data
        kyc_data = data.get('kyc_data', {})
        front_file = data.get('front_file', '')
        back_file = data.get('back_file', '')
        form_data = data.get('form_data', {})
        
        # Create cache entry
        cache_entry = {
            'timestamp': timestamp,
            'unique_id': unique_id,
            'front_image': front_file,
            'back_image': back_file,
            'extracted_data': kyc_data,
            'form_data': form_data if form_data else None
        }
        
        # Save to JSON file
        cache_file = os.path.join('cache', f'kyc_{unique_id}.json')
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f, ensure_ascii=False, indent=2)
        
        logger.info(f"KYC data saved to cache: {cache_file}")
        return cache_file
        
    except Exception as e:
        logger.error(f"Error inserting KYC data: {e}")
        raise
