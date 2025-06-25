Still editing
# AutomatedMetaGeneration

A Python-based system for extracting text and generating comprehensive metadata from various document formats (PDF, DOCX, TXT) using text extraction, semantic analysis, and NLP techniques.

The Automated Metadata Generation System is designed to process documents and produce structured metadata, including document information, text extraction details, semantic content analysis, and derived metadata such as titles, categories, and quality scores. It supports multiple file formats and includes a command-line interface (CLI) for batch processing, along with a proof-of-concept Jupyter notebook for demonstration.

Features
Text Extraction: Extracts text from TXT, PDF, and DOCX files using libraries like PyPDF2, pdfplumber, and python-docx, with OCR support (via Pillow and pytesseract) when available.
Semantic Analysis: Performs NLP-based analysis using spaCy to extract keywords, named entities, summaries, topics, sentiment, and readability scores.
Metadata Generation: Generates comprehensive metadata including document info (size, type, hash), content analysis, and derived fields (title, category, description, complexity).
Batch Processing: Supports processing single files, directories (recursively or non-recursively), and multiple files via CLI.
Quality Assessment: Evaluates document quality based on text extraction success, word count, readability, and content richness.
Output: Saves metadata as JSON files with customizable output paths.
Logging: Provides detailed logging to track processing status and errors.

File Structure
config.py: Configuration settings.
document_processor.py: Main processing orchestrator.
metadata_generator.py: Metadata generation logic.
semantic_analyzer.py: NLP-based semantic analysis.
text_extractor.py: Text extraction from documents.
utils.py: Utility functions (e.g., file hashing, logging).
main.py: CLI entry point.
metadata_poc.ipynb: Proof-of-concept notebook.
sample_documents/: Directory for sample files.
output/: Directory for generated metadata JSON files.
metadata_generation.log: Log file.


