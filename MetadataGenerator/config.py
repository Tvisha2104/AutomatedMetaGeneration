"""
Configuration settings for the metadata generation system.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_documents"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported file formats
SUPPORTED_FORMATS = {
    '.pdf': 'PDF Document',
    '.docx': 'Word Document',
    '.txt': 'Text Document',
    '.doc': 'Word Document (Legacy)',
    '.rtf': 'Rich Text Format'
}

# OCR Configuration
TESSERACT_CMD = os.getenv('TESSERACT_CMD', 'tesseract')
OCR_LANGUAGES = ['eng']  # Default to English, can be extended

# spaCy Model Configuration
SPACY_MODEL = 'en_core_web_sm'  # Default English model

# Metadata Generation Settings
MAX_KEYWORDS = 10
MAX_ENTITIES = 20
SUMMARY_SENTENCES = 3

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Processing timeouts (in seconds)
PROCESSING_TIMEOUT = 300  # 5 minutes
