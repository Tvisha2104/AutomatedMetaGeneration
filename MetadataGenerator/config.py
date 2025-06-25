"""
Configuration settings for the metadata generation system.
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_documents"

OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = {
    '.pdf': 'PDF Document',
    '.docx': 'Word Document',
    '.txt': 'Text Document',
    '.doc': 'Word Document (Legacy)',
    '.rtf': 'Rich Text Format'
}


TESSERACT_CMD = os.getenv('TESSERACT_CMD', 'tesseract')
OCR_LANGUAGES = ['eng']  


SPACY_MODEL = 'en_core_web_sm' 


MAX_KEYWORDS = 10
MAX_ENTITIES = 20
SUMMARY_SENTENCES = 3


LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


MAX_FILE_SIZE = 50 * 1024 * 1024 


PROCESSING_TIMEOUT = 300  
