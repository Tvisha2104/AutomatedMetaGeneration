

import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

def setup_logging(level: str = 'INFO') -> logging.Logger:
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('metadata_generation.log')
        ]
    )
    return logging.getLogger(__name__)

def calculate_file_hash(file_path: Path) -> str:
   
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {file_path}: {str(e)}")
        return ""

def validate_file(file_path: Path, max_size: int = 50 * 1024 * 1024) -> bool:
    
    if not file_path.exists():
        logging.error(f"File does not exist: {file_path}")
        return False
    
    if not file_path.is_file():
        logging.error(f"Path is not a file: {file_path}")
        return False
    
    file_size = file_path.stat().st_size
    if file_size > max_size:
        logging.error(f"File too large: {file_size} bytes > {max_size} bytes")
        return False
    
    return True

def save_metadata(metadata: Dict[str, Any], output_path: Path) -> bool:
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        logging.info(f"Metadata saved to: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving metadata to {output_path}: {str(e)}")
        return False

def load_metadata(file_path: Path) -> Optional[Dict[str, Any]]:
  
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading metadata from {file_path}: {str(e)}")
        return None

def get_file_info(file_path: Path) -> Dict[str, Any]:

    try:
        stat = file_path.stat()
        return {
            'filename': file_path.name,
            'file_extension': file_path.suffix.lower(),
            'file_size_bytes': stat.st_size,
            'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'file_hash': calculate_file_hash(file_path)
        }
    except Exception as e:
        logging.error(f"Error getting file info for {file_path}: {str(e)}")
        return {}

def clean_text(text: str) -> str:

    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char.isspace())
    
    return text.strip()
