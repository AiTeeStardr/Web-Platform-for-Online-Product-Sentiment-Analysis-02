"""
Aspect Extractor for ABSA
Extracts product aspects from Thai review text using keyword matching
with context window approach.
"""
from app.config import Config


class AspectExtractor:
    """
    Extract aspects (features) from review text.

    Uses predefined aspect keyword dictionaries with a context window
    to capture aspect-related sentences/segments.
    """

    def __init__(self, aspects=None, context_window=3):
        """
        Args:
            aspects: Dict of {aspect_name: [keywords]}
            context_window: Number of tokens around keyword to capture context
        """
        self.aspects = aspects or Config.ASPECTS
        self.context_window = context_window

        # Build reverse lookup: keyword → aspect
        self.keyword_to_aspect = {}
        for aspect, keywords in self.aspects.items():
            for kw in keywords:
                self.keyword_to_aspect[kw.lower()] = aspect

    def extract_aspects(self, tokens, original_text=''):
        """
        Extract aspects from tokenized text.

        Args:
            tokens: List of tokens from preprocessor
            original_text: Original text for context extraction

        Returns:
            List[dict]: [{
                'aspect': str,
                'keywords_found': list,
                'context_tokens': list,
                'position': int
            }]
        """
        found_aspects = {}

        for i, token in enumerate(tokens):
            token_lower = token.lower()

            # Check against all aspect keywords
            aspect = self._match_keyword(token_lower)
            if aspect:
                if aspect not in found_aspects:
                    found_aspects[aspect] = {
                        'aspect': aspect,
                        'keywords_found': [],
                        'context_tokens': [],
                        'positions': []
                    }

                found_aspects[aspect]['keywords_found'].append(token)
                found_aspects[aspect]['positions'].append(i)

                # Capture context window
                start = max(0, i - self.context_window)
                end = min(len(tokens), i + self.context_window + 1)
                context = tokens[start:end]
                found_aspects[aspect]['context_tokens'].extend(context)

        # Deduplicate context tokens
        for aspect_data in found_aspects.values():
            aspect_data['context_tokens'] = list(set(aspect_data['context_tokens']))
            aspect_data['keywords_found'] = list(set(aspect_data['keywords_found']))

        return list(found_aspects.values())

    def _match_keyword(self, token):
        """Match a token against aspect keywords."""
        # Direct match
        if token in self.keyword_to_aspect:
            return self.keyword_to_aspect[token]

        # Partial match (for compound words)
        for keyword, aspect in self.keyword_to_aspect.items():
            if len(keyword) >= 3 and (keyword in token or token in keyword):
                return aspect

        return None

    def get_aspect_segments(self, text, tokens):
        """
        Split text into aspect-related segments.

        Returns a dict mapping each aspect to the relevant text segments.
        """
        aspects = self.extract_aspects(tokens, text)
        segments = {}

        for aspect_info in aspects:
            aspect = aspect_info['aspect']
            segments[aspect] = ' '.join(aspect_info['context_tokens'])

        return segments

    def get_available_aspects(self):
        """Get list of all defined aspects."""
        return list(self.aspects.keys())

    def get_aspect_keywords(self, aspect_name):
        """Get keywords for a specific aspect."""
        return self.aspects.get(aspect_name, [])
