"""
Intent Patterns Utility

Centralized intent recognition patterns and prompts for user input classification.
Extracted from intent_recognition_node.py to comply with PocketFlow 150-line limit.
"""

from typing import Dict, List, Any, Optional
import re


class IntentPatterns:
    """Centralized intent recognition patterns and utilities"""
    
    # Intent types
    INTENT_NEW_QUERY = "new_query"
    INTENT_FORMAT_REQUEST = "format_request"
    
    # Format request keywords
    FORMAT_KEYWORDS = [
        "format", "make", "convert", "change", "turn", "transform",
        "bullet", "list", "table", "outline", "summary", "points",
        "organize", "structure", "arrange", "rewrite", "rephrase"
    ]
    
    # Query keywords (theological/biblical)
    QUERY_KEYWORDS = [
        "what", "who", "where", "when", "why", "how", "explain",
        "tell", "describe", "define", "meaning", "interpretation",
        "biblical", "scripture", "verse", "passage", "theology",
        "doctrine", "hermeneutics", "exegesis", "commentary"
    ]
    
    # Format command patterns
    FORMAT_PATTERNS = [
        r"format\s+(the\s+)?(previous\s+)?(response|answer|text)",
        r"make\s+(that|this|it)\s+into\s+",
        r"convert\s+(to|into)\s+",
        r"turn\s+(that|this|it)\s+into\s+",
        r"organize\s+(as|into)\s+",
        r"structure\s+(as|like)\s+",
        r"rewrite\s+(as|in)\s+",
        r"change\s+(to|into)\s+"
    ]
    
    # Examples for training
    INTENT_EXAMPLES = {
        INTENT_NEW_QUERY: [
            "What is biblical hermeneutics?",
            "Explain John 3:16",
            "Who was Paul in the Bible?",
            "What does justification mean in theology?",
            "Tell me about the Trinity",
            "How do we interpret parables?",
            "What is the meaning of grace?",
            "Describe the book of Romans"
        ],
        INTENT_FORMAT_REQUEST: [
            "Format the previous response as bullet points",
            "Make that into a table",
            "Convert to an outline",
            "Turn this into a numbered list",
            "Organize as bullet points",
            "Structure as a summary",
            "Rewrite in paragraph form",
            "Change to a table format"
        ]
    }
    
    @staticmethod
    def build_intent_prompt(message: str) -> str:
        """Build prompt for intent classification using OpenAI"""
        return f"""Classify the user's input as either a new query requiring information search or a formatting command.

User input: "{message}"

Return YAML format:
intent: new_query|format_request
confidence: 0.0-1.0

Examples:
- "What is biblical hermeneutics?" → intent: new_query
- "Format the previous response as bullet points" → intent: format_request
- "Make that into a table" → intent: format_request
- "Explain John 3:16" → intent: new_query

Classification:"""
    
    @staticmethod
    def quick_intent_classification(message: str) -> Dict[str, Any]:
        """
        Quick pattern-based intent classification (fallback if LLM unavailable)
        Returns dict with intent and confidence
        """
        message_lower = message.lower().strip()
        
        # Check for format patterns
        for pattern in IntentPatterns.FORMAT_PATTERNS:
            if re.search(pattern, message_lower):
                return {
                    'intent': IntentPatterns.INTENT_FORMAT_REQUEST,
                    'confidence': 0.8,
                    'method': 'pattern_match'
                }
        
        # Check for format keywords
        format_keyword_count = sum(1 for keyword in IntentPatterns.FORMAT_KEYWORDS 
                                 if keyword in message_lower)
        
        # Check for query keywords
        query_keyword_count = sum(1 for keyword in IntentPatterns.QUERY_KEYWORDS 
                                if keyword in message_lower)
        
        # Determine intent based on keyword counts
        if format_keyword_count > query_keyword_count and format_keyword_count > 0:
            confidence = min(0.7, 0.5 + (format_keyword_count * 0.1))
            return {
                'intent': IntentPatterns.INTENT_FORMAT_REQUEST,
                'confidence': confidence,
                'method': 'keyword_count'
            }
        
        # Default to new query
        confidence = 0.6 if query_keyword_count > 0 else 0.5
        return {
            'intent': IntentPatterns.INTENT_NEW_QUERY,
            'confidence': confidence,
            'method': 'default_fallback'
        }
    
    @staticmethod
    def get_training_examples() -> List[Dict[str, str]]:
        """Get training examples for intent classification"""
        examples = []
        
        for intent, example_texts in IntentPatterns.INTENT_EXAMPLES.items():
            for text in example_texts:
                examples.append({
                    'text': text,
                    'intent': intent
                })
        
        return examples
    
    @staticmethod
    def validate_intent(intent: str) -> bool:
        """Validate that intent is one of the recognized types"""
        return intent in [IntentPatterns.INTENT_NEW_QUERY, IntentPatterns.INTENT_FORMAT_REQUEST]
    
    @staticmethod
    def get_confidence_threshold() -> float:
        """Get minimum confidence threshold for intent classification"""
        return 0.3
    
    @staticmethod
    def is_high_confidence(confidence: float) -> bool:
        """Check if confidence is high enough for reliable classification"""
        return confidence >= 0.7
    
    @staticmethod
    def analyze_message_features(message: str) -> Dict[str, Any]:
        """Analyze message features for intent classification debugging"""
        message_lower = message.lower().strip()
        
        # Count different types of keywords
        format_keywords_found = [kw for kw in IntentPatterns.FORMAT_KEYWORDS if kw in message_lower]
        query_keywords_found = [kw for kw in IntentPatterns.QUERY_KEYWORDS if kw in message_lower]
        
        # Check for patterns
        format_patterns_found = []
        for pattern in IntentPatterns.FORMAT_PATTERNS:
            if re.search(pattern, message_lower):
                format_patterns_found.append(pattern)
        
        return {
            'message_length': len(message),
            'word_count': len(message.split()),
            'format_keywords_found': format_keywords_found,
            'query_keywords_found': query_keywords_found,
            'format_patterns_found': format_patterns_found,
            'has_question_mark': '?' in message,
            'starts_with_question_word': any(message_lower.startswith(qw) for qw in ['what', 'who', 'where', 'when', 'why', 'how']),
            'contains_format_verbs': any(verb in message_lower for verb in ['format', 'make', 'convert', 'change', 'turn'])
        }