"""
Semantic analysis module using spaCy for NLP processing.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re
from collections import Counter

# Import spaCy with error handling
try:
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available. Install spaCy and download en_core_web_sm model.")

from config import SPACY_MODEL, MAX_KEYWORDS, MAX_ENTITIES, SUMMARY_SENTENCES

class SemanticAnalyzer:
    """
    Semantic analysis class for extracting meaningful information from text.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nlp = None
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(SPACY_MODEL)
                self.logger.info(f"Loaded spaCy model: {SPACY_MODEL}")
            except OSError:
                self.logger.error(f"Could not load spaCy model: {SPACY_MODEL}")
                self.logger.error("Install it with: python -m spacy download en_core_web_sm")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive semantic analysis on text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not text or not text.strip():
            return self._empty_analysis()
        
        analysis = {
            'keywords': [],
            'entities': [],
            'summary': '',
            'language': 'en',
            'sentiment': 'neutral',
            'topics': [],
            'readability_score': 0.0,
            'text_statistics': self._calculate_text_statistics(text)
        }
        
        try:
            if self.nlp is not None:
                # Process text with spaCy
                doc = self.nlp(text)
                
                # Extract keywords
                analysis['keywords'] = self._extract_keywords(doc)
                
                # Extract named entities
                analysis['entities'] = self._extract_entities(doc)
                
                # Generate summary
                analysis['summary'] = self._generate_summary(text, doc)
                
                # Extract topics
                analysis['topics'] = self._extract_topics(doc)
                
                # Calculate readability
                analysis['readability_score'] = self._calculate_readability(text)
                
                # Basic sentiment analysis (if available in model)
                analysis['sentiment'] = self._analyze_sentiment(doc)
                
            else:
                # Fallback analysis without spaCy
                analysis = self._fallback_analysis(text)
                
            self.logger.info("Semantic analysis completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in semantic analysis: {str(e)}")
            return self._fallback_analysis(text)
        
        return analysis
    
    def _extract_keywords(self, doc) -> List[Dict[str, Any]]:
        """Extract keywords from spaCy document."""
        # Get important tokens (exclude stop words, punctuation, spaces)
        important_tokens = []
        
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                not token.is_space and 
                len(token.text) > 2 and
                token.pos_ in ['NOUN', 'ADJ', 'VERB', 'PROPN']):
                important_tokens.append(token.lemma_.lower())
        
        # Count frequency and get top keywords
        keyword_counts = Counter(important_tokens)
        keywords = []
        
        for word, count in keyword_counts.most_common(MAX_KEYWORDS):
            keywords.append({
                'word': word,
                'frequency': count,
                'relevance_score': count / len(important_tokens) if important_tokens else 0
            })
        
        return keywords
    
    def _extract_entities(self, doc) -> List[Dict[str, Any]]:
        """Extract named entities from spaCy document."""
        entities = []
        seen_entities = set()
        
        for ent in doc.ents:
            # Avoid duplicates
            entity_key = (ent.text.lower(), ent.label_)
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'description': spacy.explain(ent.label_) or ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': getattr(ent, 'score', 1.0)
                })
        
        # Sort by confidence and return top entities
        entities.sort(key=lambda x: x['confidence'], reverse=True)
        return entities[:MAX_ENTITIES]
    
    def _generate_summary(self, text: str, doc) -> str:
        """Generate a simple extractive summary."""
        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
        
        if len(sentences) <= SUMMARY_SENTENCES:
            return ' '.join(sentences)
        
        # Simple scoring based on sentence length and keyword presence
        sentence_scores = []
        
        # Get keywords for scoring
        keywords = set(token.lemma_.lower() for token in doc 
                      if not token.is_stop and not token.is_punct and len(token.text) > 2)
        
        for sent in sentences:
            score = 0
            sent_words = sent.lower().split()
            
            # Score based on keyword presence
            for word in sent_words:
                if word in keywords:
                    score += 1
            
            # Normalize by sentence length
            score = score / len(sent_words) if sent_words else 0
            sentence_scores.append((sent, score))
        
        # Sort by score and take top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [sent for sent, score in sentence_scores[:SUMMARY_SENTENCES]]
        
        return ' '.join(top_sentences)
    
    def _extract_topics(self, doc) -> List[str]:
        """Extract potential topics from the document."""
        # Simple topic extraction based on noun phrases
        topics = set()
        
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3 and not chunk.root.is_stop:
                topics.add(chunk.text.strip())
        
        # Also add important single nouns
        for token in doc:
            if (token.pos_ == 'NOUN' and 
                not token.is_stop and 
                len(token.text) > 3):
                topics.add(token.text)
        
        return list(topics)[:10]  # Return top 10 topics
    
    def _analyze_sentiment(self, doc) -> str:
        """Basic sentiment analysis."""
        # This is a simplified sentiment analysis
        # For production, consider using specialized sentiment models
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing']
        
        text_lower = doc.text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate a simple readability score."""
        # Simplified Flesch Reading Ease approximation
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        syllables = sum(self._count_syllables(word) for word in words)
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllables / len(words)
        
        # Simplified readability score (0-100, higher is easier)
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _count_syllables(self, word: str) -> int:
        """Simple syllable counting."""
        word = word.lower()
        vowels = 'aeiouy'
        syllables = 0
        prev_char_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_char_was_vowel:
                    syllables += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False
        
        # Handle silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        return max(1, syllables)
    
    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate basic text statistics."""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        paragraphs = text.split('\n\n')
        
        return {
            'sentence_count': len([s for s in sentences if s.strip()]),
            'word_count': len(words),
            'character_count': len(text),
            'character_count_no_spaces': len(text.replace(' ', '')),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'average_words_per_sentence': len(words) / max(1, len([s for s in sentences if s.strip()])),
            'average_characters_per_word': len(text.replace(' ', '')) / max(1, len(words))
        }
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis when spaCy is not available."""
        words = text.lower().split()
        
        # Simple keyword extraction
        word_counts = Counter(word for word in words 
                            if len(word) > 3 and word not in STOP_WORDS)
        
        keywords = [{'word': word, 'frequency': count, 'relevance_score': count/len(words)} 
                   for word, count in word_counts.most_common(MAX_KEYWORDS)]
        
        # Simple summary (first few sentences)
        sentences = re.split(r'[.!?]+', text)
        summary = '. '.join(sentences[:SUMMARY_SENTENCES]).strip()
        
        return {
            'keywords': keywords,
            'entities': [],
            'summary': summary,
            'language': 'en',
            'sentiment': 'neutral',
            'topics': list(word_counts.keys())[:10],
            'readability_score': self._calculate_readability(text),
            'text_statistics': self._calculate_text_statistics(text)
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'keywords': [],
            'entities': [],
            'summary': '',
            'language': 'en',
            'sentiment': 'neutral',
            'topics': [],
            'readability_score': 0.0,
            'text_statistics': {
                'sentence_count': 0,
                'word_count': 0,
                'character_count': 0,
                'character_count_no_spaces': 0,
                'paragraph_count': 0,
                'average_words_per_sentence': 0,
                'average_characters_per_word': 0
            }
        }
