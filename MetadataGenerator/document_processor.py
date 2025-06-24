"""
Main document processing orchestrator module.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from metadata_generator import MetadataGenerator
from utils import setup_logging, save_metadata, validate_file
from config import SUPPORTED_FORMATS, OUTPUT_DIR, MAX_FILE_SIZE

class DocumentProcessor:
    """
    Main document processor that handles multiple files and batch processing.
    """
    
    def __init__(self, log_level: str = 'INFO'):
        self.logger = setup_logging(log_level)
        self.metadata_generator = MetadataGenerator()
        self.processing_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
    
    def process_single_document(self, file_path: Path, 
                               output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Process a single document and generate metadata.
        
        Args:
            file_path: Path to the document file
            output_path: Optional custom output path for metadata JSON
            
        Returns:
            Generated metadata dictionary
        """
        self.logger.info(f"Processing document: {file_path}")
        
        try:
            # Validate input file
            if not validate_file(file_path, MAX_FILE_SIZE):
                raise ValueError(f"File validation failed: {file_path}")
            
            # Check if file format is supported
            file_extension = file_path.suffix.lower()
            if file_extension not in SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Generate metadata
            metadata = self.metadata_generator.generate_metadata(file_path)
            
            # Determine output path
            if output_path is None:
                output_filename = f"{file_path.stem}_metadata.json"
                output_path = OUTPUT_DIR / output_filename
            
            # Save metadata
            if save_metadata(metadata, output_path):
                self.logger.info(f"Metadata saved to: {output_path}")
                self.processing_stats['successful'] += 1
            else:
                self.processing_stats['failed'] += 1
                self.processing_stats['errors'].append(f"Failed to save metadata for {file_path}")
            
            self.processing_stats['total_files'] += 1
            return metadata
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.logger.error(error_msg)
            self.processing_stats['failed'] += 1
            self.processing_stats['errors'].append(error_msg)
            
            # Return error metadata
            return {
                'document_info': {'filename': file_path.name if file_path.exists() else str(file_path)},
                'processing_info': {
                    'success': False,
                    'error': error_msg,
                    'timestamp': None
                }
            }
    
    def process_directory(self, directory_path: Path, 
                         recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Process all supported documents in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            
        Returns:
            List of metadata dictionaries for all processed files
        """
        self.logger.info(f"Processing directory: {directory_path}")
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Invalid directory path: {directory_path}")
        
        # Find all supported files
        files_to_process = []
        
        if recursive:
            for ext in SUPPORTED_FORMATS.keys():
                files_to_process.extend(directory_path.rglob(f"*{ext}"))
        else:
            for ext in SUPPORTED_FORMATS.keys():
                files_to_process.extend(directory_path.glob(f"*{ext}"))
        
        self.logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process each file
        results = []
        for file_path in files_to_process:
            try:
                metadata = self.process_single_document(file_path)
                results.append(metadata)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                continue
        
        # Save batch processing summary
        self._save_batch_summary(directory_path, results)
        
        return results
    
    def process_file_list(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Process a list of specific files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of metadata dictionaries
        """
        self.logger.info(f"Processing {len(file_paths)} files")
        
        results = []
        for file_path in file_paths:
            try:
                metadata = self.process_single_document(file_path)
                results.append(metadata)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                continue
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
    
    def _save_batch_summary(self, directory_path: Path, results: List[Dict[str, Any]]) -> None:
        """Save batch processing summary."""
        summary = {
            'batch_info': {
                'directory': str(directory_path),
                'processed_files': len(results),
                'successful_files': len([r for r in results if r.get('processing_info', {}).get('success', False)]),
                'failed_files': len([r for r in results if not r.get('processing_info', {}).get('success', False)]),
                'processing_stats': self.processing_stats
            },
            'file_summaries': []
        }
        
        # Add summary for each file
        for result in results:
            doc_info = result.get('document_info', {})
            processing_info = result.get('processing_info', {})
            derived_metadata = result.get('derived_metadata', {})
            
            file_summary = {
                'filename': doc_info.get('filename', 'Unknown'),
                'file_size_mb': doc_info.get('file_size_mb', 0),
                'success': processing_info.get('success', False),
                'title': derived_metadata.get('title', 'N/A'),
                'category': derived_metadata.get('category', 'N/A'),
                'quality_score': derived_metadata.get('quality_score', 0),
                'word_count': result.get('extraction_info', {}).get('word_count', 0)
            }
            summary['file_summaries'].append(file_summary)
        
        # Save summary
        summary_path = OUTPUT_DIR / f"batch_summary_{directory_path.name}.json"
        save_metadata(summary, summary_path)
        self.logger.info(f"Batch summary saved to: {summary_path}")

    def get_supported_formats(self) -> Dict[str, str]:
        """Get dictionary of supported file formats."""
        return SUPPORTED_FORMATS.copy()
    
    def validate_file_format(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in SUPPORTED_FORMATS
