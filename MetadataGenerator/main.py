"""
Main command-line interface for the metadata generation system.
"""

import argparse
import sys
from pathlib import Path
import json
from typing import Dict

from document_processor import DocumentProcessor
from config import SUPPORTED_FORMATS, OUTPUT_DIR
from utils import setup_logging

def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Automated Document Metadata Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py file document.pdf
  python main.py directory /path/to/documents
  python main.py files doc1.pdf doc2.docx doc3.txt
  python main.py file document.pdf --output custom_metadata.json
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Processing mode')
    
    # Single file processing
    file_parser = subparsers.add_parser('file', help='Process a single file')
    file_parser.add_argument('filepath', type=str, help='Path to the document file')
    file_parser.add_argument('--output', '-o', type=str, help='Output JSON file path')
    
    # Directory processing
    dir_parser = subparsers.add_parser('directory', help='Process all files in a directory')
    dir_parser.add_argument('dirpath', type=str, help='Path to the directory')
    dir_parser.add_argument('--recursive', '-r', action='store_true', 
                           help='Process subdirectories recursively')
    
    # Multiple files processing
    files_parser = subparsers.add_parser('files', help='Process multiple specific files')
    files_parser.add_argument('filepaths', nargs='+', type=str, 
                             help='Paths to the document files')
    
    # List supported formats
    list_parser = subparsers.add_parser('formats', help='List supported file formats')
    
    # Common arguments
    for sub_parser in [file_parser, dir_parser, files_parser]:
        sub_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                               default='INFO', help='Logging level')
        sub_parser.add_argument('--verbose', '-v', action='store_true', 
                               help='Enable verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Handle formats listing
    if args.command == 'formats':
        print("Supported file formats:")
        for ext, desc in SUPPORTED_FORMATS.items():
            print(f"  {ext:<6} - {desc}")
        return 0
    
    # Set up logging
    log_level = args.log_level if hasattr(args, 'log_level') else 'INFO'
    logger = setup_logging(log_level)
    
    # Initialize processor
    processor = DocumentProcessor(log_level)
    
    try:
        if args.command == 'file':
            return process_single_file(processor, args, logger)
        elif args.command == 'directory':
            return process_directory(processor, args, logger)
        elif args.command == 'files':
            return process_multiple_files(processor, args, logger)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

def process_single_file(processor: DocumentProcessor, args, logger) -> int:
    """Process a single file."""
    file_path = Path(args.filepath)
    
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return 1
    
    if not processor.validate_file_format(file_path):
        logger.error(f"Unsupported file format: {file_path.suffix}")
        logger.info("Use 'python main.py formats' to see supported formats")
        return 1
    
    # Determine output path
    output_path = None
    if args.output:
        output_path = Path(args.output)
    
    logger.info(f"Processing file: {file_path}")
    
    # Process the file
    metadata = processor.process_single_document(file_path, output_path)
    
    # Print results
    if args.verbose:
        print_metadata_summary(metadata)
    
    # Print statistics
    stats = processor.get_processing_stats()
    logger.info(f"Processing complete. Success: {stats['successful']}, Failed: {stats['failed']}")
    
    return 0 if stats['successful'] > 0 else 1

def process_directory(processor: DocumentProcessor, args, logger) -> int:
    """Process all files in a directory."""
    dir_path = Path(args.dirpath)
    
    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory does not exist: {dir_path}")
        return 1
    
    logger.info(f"Processing directory: {dir_path}")
    logger.info(f"Recursive: {args.recursive}")
    
    # Process the directory
    results = processor.process_directory(dir_path, args.recursive)
    
    # Print results
    if args.verbose and results:
        print(f"\nProcessed {len(results)} files:")
        for metadata in results[:5]:  # Show first 5
            print_metadata_summary(metadata)
        if len(results) > 5:
            print(f"... and {len(results) - 5} more files")
    
    # Print statistics
    stats = processor.get_processing_stats()
    logger.info(f"Directory processing complete. Success: {stats['successful']}, Failed: {stats['failed']}")
    
    if stats['errors'] and args.verbose:
        print("\nErrors encountered:")
        for error in stats['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
    
    return 0 if stats['successful'] > 0 else 1

def process_multiple_files(processor: DocumentProcessor, args, logger) -> int:
    """Process multiple specific files."""
    file_paths = [Path(fp) for fp in args.filepaths]
    
    # Validate files
    valid_files = []
    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            continue
        if not processor.validate_file_format(file_path):
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            continue
        valid_files.append(file_path)
    
    if not valid_files:
        logger.error("No valid files to process")
        return 1
    
    logger.info(f"Processing {len(valid_files)} files")
    
    # Process the files
    results = processor.process_file_list(valid_files)
    
    # Print results
    if args.verbose and results:
        print(f"\nProcessed {len(results)} files:")
        for metadata in results:
            print_metadata_summary(metadata)
    
    # Print statistics
    stats = processor.get_processing_stats()
    logger.info(f"Multiple files processing complete. Success: {stats['successful']}, Failed: {stats['failed']}")
    
    return 0 if stats['successful'] > 0 else 1

def print_metadata_summary(metadata: Dict) -> None:
    """Print a summary of generated metadata."""
    doc_info = metadata.get('document_info', {})
    derived = metadata.get('derived_metadata', {})
    extraction = metadata.get('extraction_info', {})
    processing = metadata.get('processing_info', {})
    
    print(f"\n{'='*50}")
    print(f"File: {doc_info.get('filename', 'Unknown')}")
    print(f"Success: {processing.get('success', False)}")
    
    if processing.get('success'):
        print(f"Title: {derived.get('title', 'N/A')}")
        print(f"Category: {derived.get('category', 'N/A')}")
        print(f"Quality Score: {derived.get('quality_score', 0)}")
        print(f"Word Count: {extraction.get('word_count', 0)}")
        print(f"Reading Time: {derived.get('estimated_reading_time', 'N/A')}")
        
        keywords = derived.get('top_keywords', [])
        if keywords:
            print(f"Top Keywords: {', '.join(keywords[:5])}")
    else:
        errors = processing.get('errors', [])
        if errors:
            print(f"Errors: {'; '.join(errors)}")

if __name__ == "__main__":
    sys.exit(main())
