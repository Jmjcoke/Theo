"""
Theological document metadata system for Gordon C. Olson moral government theology.
Provides document categorization and authority weighting for RAG responses.
"""

from typing import Dict, List, Optional, Tuple
import re

class TheologicalMetadata:
    """Manages theological document metadata and authority hierarchy"""
    
    # Authority levels for source weighting
    AUTHORITY_LEVELS = {
        'GORDON_OLSON_PRIMARY': 10,      # Gordon C. Olson's main theological works
        'GORDON_OLSON_SECONDARY': 9,     # Olson's supporting materials  
        'MORAL_GOVERNMENT_ALLIED': 8,    # Other moral government theologians
        'HERMENEUTICS_REFERENCE': 7,     # Hermeneutical methodology sources
        'SUPPORTING_MATERIAL': 6,        # General supporting theological material
        'BIBLICAL_TEXT': 5,              # Scripture (as contextual support after theological grounding)
        'UNKNOWN': 1                     # Unclassified sources
    }
    
    # Document classification patterns
    CLASSIFICATION_PATTERNS = {
        'GORDON_OLSON_PRIMARY': [
            r'gordon.*olson',
            r'olson.*gordon', 
            r'truth.*shall.*set.*free',
            r'essentials.*salvation',
            r'foreknowledge.*god'
        ],
        'BIBLICAL_TEXT': [
            r'\b(genesis|exodus|leviticus|numbers|deuteronomy)\b',
            r'\b(matthew|mark|luke|john)\b',
            r'\b(romans|corinthians|galatians|ephesians|philippians|colossians)\b',
            r'\b(thessalonians|timothy|titus|philemon|hebrews|james|peter|jude)\b',
            r'\b(revelation|acts|psalms|proverbs|ecclesiastes|isaiah|jeremiah)\b',
            r'\bjohn\.json\b',
            r'\bcorinthians\.json\b'
        ],
        'HERMENEUTICS_REFERENCE': [
            r'hermeneutic',
            r'interpretation',
            r'biblical.*method',
            r'exegesis'
        ]
    }
    
    # Moral government theology keywords for content weighting
    MORAL_GOVERNMENT_KEYWORDS = [
        'moral government', 'moral agency', 'human responsibility', 
        'free will', 'libertarian freedom', 'natural ability',
        'governmental theory', 'moral obligation', 'conditional election',
        'universal atonement', 'prevenient grace', 'resistible grace',
        'moral law', 'divine government', 'justice and mercy'
    ]
    
    # Anti-Reformed/Calvinist detection patterns
    REFORMED_REJECTION_PATTERNS = [
        r'\btotal depravity\b', r'\bunconditional election\b',
        r'\blimited atonement\b', r'\birresistible grace\b', 
        r'\bperseverance.*saints\b', r'\baugustinian\b',
        r'\bcalvinist\b', r'\breformed.*theology\b',
        r'\boriginal sin\b.*\binability\b', r'\bpredestination\b.*\bunconditional\b'
    ]
    
    @classmethod
    def classify_document(cls, filename: str, content_sample: str = "") -> Tuple[str, int, Dict[str, any]]:
        """
        Classify document and return category, authority level, and metadata
        
        Args:
            filename: Document filename
            content_sample: Sample of document content for analysis
            
        Returns:
            Tuple of (category, authority_level, metadata_dict)
        """
        filename_lower = filename.lower()
        content_lower = content_sample.lower()
        
        # Check Gordon C. Olson primary sources
        for pattern in cls.CLASSIFICATION_PATTERNS['GORDON_OLSON_PRIMARY']:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return ('GORDON_OLSON_PRIMARY', cls.AUTHORITY_LEVELS['GORDON_OLSON_PRIMARY'], {
                    'author': 'Gordon C. Olson',
                    'theological_system': 'Moral Government Theology',
                    'authority_notes': 'Primary theological authority for moral government doctrine',
                    'hermeneutical_priority': 'highest'
                })
        
        # Check biblical texts
        for pattern in cls.CLASSIFICATION_PATTERNS['BIBLICAL_TEXT']:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return ('BIBLICAL_TEXT', cls.AUTHORITY_LEVELS['BIBLICAL_TEXT'], {
                    'type': 'Scripture',
                    'theological_system': 'Biblical Text',
                    'authority_notes': 'Scripture as contextual support for theological doctrine',
                    'hermeneutical_priority': 'contextual_support'
                })
        
        # Check hermeneutics references
        for pattern in cls.CLASSIFICATION_PATTERNS['HERMENEUTICS_REFERENCE']:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return ('HERMENEUTICS_REFERENCE', cls.AUTHORITY_LEVELS['HERMENEUTICS_REFERENCE'], {
                    'type': 'Hermeneutical Methodology',
                    'theological_system': 'Interpretive Framework',
                    'authority_notes': 'Methodological guidance for biblical interpretation',
                    'hermeneutical_priority': 'methodology'
                })
        
        # Content analysis for moral government alignment
        moral_gov_score = sum(1 for keyword in cls.MORAL_GOVERNMENT_KEYWORDS 
                             if keyword in content_lower)
        
        reformed_flags = sum(1 for pattern in cls.REFORMED_REJECTION_PATTERNS
                           if re.search(pattern, content_lower, re.IGNORECASE))
        
        if moral_gov_score >= 3 and reformed_flags == 0:
            return ('MORAL_GOVERNMENT_ALLIED', cls.AUTHORITY_LEVELS['MORAL_GOVERNMENT_ALLIED'], {
                'theological_system': 'Moral Government Aligned',
                'authority_notes': f'Content aligns with moral government theology ({moral_gov_score} keywords)',
                'hermeneutical_priority': 'allied'
            })
        
        # Default classification
        return ('SUPPORTING_MATERIAL', cls.AUTHORITY_LEVELS['SUPPORTING_MATERIAL'], {
            'theological_system': 'General',
            'authority_notes': 'Supporting material - verify alignment with moral government theology',
            'hermeneutical_priority': 'supporting'
        })
    
    @classmethod
    def weight_search_results(cls, search_results: List[Dict]) -> List[Dict]:
        """
        Apply theological authority weighting to search results
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            Weighted and reordered search results with authority metadata
        """
        weighted_results = []
        
        for result in search_results:
            filename = result.get('document_title', result.get('title', ''))
            content = result.get('content', '')
            
            category, authority, metadata = cls.classify_document(filename, content)
            
            # Add theological metadata to result
            result['theological_category'] = category
            result['authority_level'] = authority
            result['theological_metadata'] = metadata
            
            # Calculate combined relevance score
            base_relevance = float(result.get('relevance', 0.0))
            authority_weight = authority / 10.0  # Normalize to 0-1
            
            # Boost Gordon C. Olson sources significantly
            if category == 'GORDON_OLSON_PRIMARY':
                authority_weight *= 1.5
            
            result['combined_relevance'] = base_relevance * 0.7 + authority_weight * 0.3
            weighted_results.append(result)
        
        # Sort by combined relevance (authority + semantic relevance)
        weighted_results.sort(key=lambda x: x['combined_relevance'], reverse=True)
        
        return weighted_results
    
    @classmethod
    def detect_theological_conflicts(cls, content: str) -> List[str]:
        """
        Detect potential Reformed/Calvinist contamination in content
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of detected theological conflict warnings
        """
        warnings = []
        content_lower = content.lower()
        
        for pattern in cls.REFORMED_REJECTION_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                warnings.append(f"Reformed/Calvinist concept detected: {pattern}")
        
        return warnings
    
    @classmethod
    def generate_source_citation(cls, result: Dict, source_num: int) -> str:
        """
        Generate properly formatted source citation with theological metadata
        
        Args:
            result: Search result dictionary with theological metadata
            source_num: Source number for citation
            
        Returns:
            Formatted citation string
        """
        category = result.get('theological_category', 'UNKNOWN')
        metadata = result.get('theological_metadata', {})
        title = result.get('document_title', result.get('title', 'Unknown Document'))
        
        citation_base = f"[Source {source_num}]"
        
        if category == 'GORDON_OLSON_PRIMARY':
            return f"{citation_base} **Gordon C. Olson** - {title} (PRIMARY AUTHORITY)"
        elif category == 'BIBLICAL_TEXT':
            return f"{citation_base} **Scripture** - {title} (Biblical Authority)"
        elif category == 'HERMENEUTICS_REFERENCE':
            return f"{citation_base} **Hermeneutical Reference** - {title}"
        else:
            return f"{citation_base} {title} ({metadata.get('theological_system', 'General')})"