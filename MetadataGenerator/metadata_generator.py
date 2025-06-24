"""
Metadata generation module that combines all processing components.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import mimetypes

from text_extractor import TextExtractor
from semantic_analyzer import SemanticAnalyzer
from utils import get_file_info, validate_file
from config import SUPPORTED_FORMATS

class MetadataGenerator:
    """
    Main metadata generation class that orchestrates the entire process.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.text_extractor = TextExtractor()
        self.semantic_analyzer = SemanticAnalyzer()
    
    def generate_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing all generated metadata
        """
        self.logger.info(f"Starting metadata generation for: {file_path}")
        
        # Initialize metadata structure
        metadata = {
            'document_info': {},
            'extraction_info': {},
            'content_analysis': {},
            'processing_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'success': False,
                'errors': []
            }
        }
        
        try:
            # Validate file
            if not validate_file(file_path):
                error_msg = f"File validation failed for: {file_path}"
                metadata['processing_info']['errors'].append(error_msg)
                self.logger.error(error_msg)
                return metadata
            
            # Get basic file information
            metadata['document_info'] = self._generate_document_info(file_path)
            
            # Extract text content
            extraction_result = self.text_extractor.extract_text(file_path)
            metadata['extraction_info'] = extraction_result
            
            if not extraction_result['success']:
                error_msg = f"Text extraction failed: {extraction_result.get('error', 'Unknown error')}"
                metadata['processing_info']['errors'].append(error_msg)
                self.logger.error(error_msg)
                return metadata
            
            # Perform semantic analysis
            if extraction_result['text']:
                semantic_analysis = self.semantic_analyzer.analyze_text(extraction_result['text'])
                metadata['content_analysis'] = semantic_analysis
                
                # Generate derived metadata
                metadata['derived_metadata'] = self._generate_derived_metadata(
                    metadata['document_info'],
                    extraction_result,
                    semantic_analysis
                )
            else:
                self.logger.warning("No text content available for semantic analysis")
                metadata['content_analysis'] = self.semantic_analyzer._empty_analysis()
                metadata['derived_metadata'] = {}
            
            metadata['processing_info']['success'] = True
            self.logger.info(f"Metadata generation completed successfully for: {file_path}")
            
        except Exception as e:
            error_msg = f"Error generating metadata: {str(e)}"
            metadata['processing_info']['errors'].append(error_msg)
            self.logger.error(error_msg, exc_info=True)
        
        return metadata
    
    def _generate_document_info(self, file_path: Path) -> Dict[str, Any]:
        """Generate basic document information."""
        file_info = get_file_info(file_path)
        
        # Determine document type
        file_extension = file_path.suffix.lower()
        document_type = SUPPORTED_FORMATS.get(file_extension, 'Unknown Document')
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        document_info = {
            **file_info,
            'document_type': document_type,
            'mime_type': mime_type or 'application/octet-stream',
            'file_path': str(file_path.absolute()),
            'file_stem': file_path.stem
        }
        
        return document_info
    
    def _generate_derived_metadata(self, document_info: Dict[str, Any], 
                                 extraction_info: Dict[str, Any],
                                 content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate derived metadata combining all analysis results."""
        
        # Determine document title
        title = self._extract_title(document_info, content_analysis)
        
        # Classify document category
        category = self._classify_document(content_analysis)
        
        # Generate description
        description = self._generate_description(content_analysis)
        
        # Extract primary language
        language = content_analysis.get('language', 'en')
        
        # Quality assessment
        quality_score = self._assess_document_quality(extraction_info, content_analysis)
        
        derived_metadata = {
            'title': title,
            'description': description,
            'category': category,
            'primary_language': language,
            'quality_score': quality_score,
            'complexity_level': self._assess_complexity(content_analysis),
            'main_topics': content_analysis.get('topics', [])[:5],
            'key_entities': [entity['text'] for entity in content_analysis.get('entities', [])[:10]],
            'top_keywords': [kw['word'] for kw in content_analysis.get('keywords', [])[:10]],
            'content_type': self._determine_content_type(content_analysis),
            'estimated_reading_time': self._estimate_reading_time(extraction_info.get('word_count', 0))
        }
        
        return derived_metadata
    
    def _extract_title(self, document_info: Dict[str, Any], 
                      content_analysis: Dict[str, Any]) -> str:
        """Extract or generate document title."""
        # First try the filename without extension
        filename_title = document_info.get('file_stem', '')
        if filename_title and len(filename_title) > 3:
            # Clean up filename
            title = filename_title.replace('_', ' ').replace('-', ' ')
            title = ' '.join(word.capitalize() for word in title.split())
            return title
        
        # Try to extract from summary
        summary = content_analysis.get('summary', '')
        if summary:
            # Take first sentence as title
            first_sentence = summary.split('.')[0].strip()
            if len(first_sentence) < 100:
                return first_sentence
        
        # Try keywords
        keywords = content_analysis.get('keywords', [])
        if keywords:
            top_keywords = [kw['word'].capitalize() for kw in keywords[:3]]
            return ' '.join(top_keywords)
        
        # Fallback
        return document_info.get('filename', 'Untitled Document')
    
    def _classify_document(self, content_analysis: Dict[str, Any]) -> str:
        """Classify document into a category."""
        entities = content_analysis.get('entities', [])
        keywords = [kw['word'].lower() for kw in content_analysis.get('keywords', [])]
        
        # Simple rule-based classification
        if any('ORG' in entity['label'] for entity in entities):
            return 'Business/Corporate'
        elif any('PERSON' in entity['label'] for entity in entities):
            return 'Biographical/Personal'
        elif any(word in keywords for word in ['research', 'study', 'analysis', 'method']):
            return 'Academic/Research'
        elif any(word in keywords for word in ['report', 'summary', 'overview']):
            return 'Report/Documentation'
        elif any(word in keywords for word in ['legal', 'law', 'contract', 'agreement']):
            return 'Legal/Regulatory'
        elif any(word in keywords for word in ['technical', 'system', 'software', 'computer']):
            return 'Technical/IT'
        else:
            return 'General Document'
    
    def _generate_description(self, content_analysis: Dict[str, Any]) -> str:
        """Generate document description."""
        summary = content_analysis.get('summary', '')
        if summary and len(summary) > 20:
            return summary
        
        # Fallback: create description from keywords and topics
        keywords = [kw['word'] for kw in content_analysis.get('keywords', [])[:5]]
        topics = content_analysis.get('topics', [])[:3]
        
        if keywords or topics:
            desc_parts = []
            if topics:
                desc_parts.append(f"This document discusses {', '.join(topics)}.")
            if keywords:
                desc_parts.append(f"Key themes include {', '.join(keywords)}.")
            return ' '.join(desc_parts)
        
        return "Document content analysis completed."
    
    def _assess_document_quality(self, extraction_info: Dict[str, Any], 
                               content_analysis: Dict[str, Any]) -> float:
        """Assess document quality on a scale of 0-100."""
        score = 100.0
        
        # Penalize if text extraction failed
        if not extraction_info.get('success', False):
            score -= 50
        
        # Consider text length
        word_count = extraction_info.get('word_count', 0)
        if word_count < 50:
            score -= 30
        elif word_count < 100:
            score -= 15
        
        # Consider readability
        readability = content_analysis.get('readability_score', 0)
        if readability < 30:
            score -= 20
        elif readability > 80:
            score += 10
        
        # Consider content richness
        keywords_count = len(content_analysis.get('keywords', []))
        entities_count = len(content_analysis.get('entities', []))
        
        if keywords_count < 3:
            score -= 15
        if entities_count == 0:
            score -= 10
        
        return max(0, min(100, round(score, 1)))
    
    def _assess_complexity(self, content_analysis: Dict[str, Any]) -> str:
        """Assess document complexity level."""
        readability = content_analysis.get('readability_score', 50)
        text_stats = content_analysis.get('text_statistics', {})
        avg_words_per_sentence = text_stats.get('average_words_per_sentence', 15)
        
        if readability > 70 and avg_words_per_sentence < 15:
            return 'Simple'
        elif readability > 50 and avg_words_per_sentence < 20:
            return 'Moderate'
        elif readability > 30:
            return 'Complex'
        else:
            return 'Very Complex'
    
    def _determine_content_type(self, content_analysis: Dict[str, Any]) -> str:
        """Determine the type of content."""
        entities = content_analysis.get('entities', [])
        keywords = [kw['word'].lower() for kw in content_analysis.get('keywords', [])]
        
        # Check for specific content indicators
        if any('DATE' in entity['label'] for entity in entities):
            if any(word in keywords for word in ['meeting', 'agenda', 'schedule']):
                return 'Meeting/Event'
            elif any(word in keywords for word in ['report', 'quarterly', 'annual']):
                return 'Report'
        
        if any('MONEY' in entity['label'] for entity in entities):
            return 'Financial'
        
        if any(word in keywords for word in ['instruction', 'manual', 'guide', 'how']):
            return 'Instructional'
        
        return 'Informational'
    
    def _estimate_reading_time(self, word_count: int) -> str:
        """Estimate reading time based on word count."""
        # Average reading speed: 200-250 words per minute
        if word_count == 0:
            return "0 minutes"
        
        minutes = max(1, round(word_count / 225))
        
        if minutes == 1:
            return "1 minute"
        elif minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours}h {remaining_minutes}m"
