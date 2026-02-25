"""
PDPA Anonymizer
Anonymizes personally identifiable information for PDPA compliance.
"""
import hashlib
import re


class Anonymizer:
    """
    Data anonymization utility for PDPA compliance.

    Implements:
    - Username hashing (SHA-256)
    - Profile URL removal
    - Phone number masking
    - Email masking
    - PII stripping from review text
    """

    def __init__(self, salt='sentiment_platform_2024'):
        self.salt = salt

    def anonymize_review(self, review):
        """
        Anonymize a review dictionary.

        Args:
            review: dict with 'username', 'text', etc.

        Returns:
            dict: Anonymized review
        """
        anonymized = review.copy()

        # Hash username
        username = review.get('username', '')
        if username:
            anonymized['reviewer_hash'] = self._hash_username(username)
            del anonymized['username']  # Remove original username

        # Remove profile URL if present
        if 'profile_url' in anonymized:
            del anonymized['profile_url']

        # Clean PII from review text
        if 'text' in anonymized:
            anonymized['text'] = self._mask_pii_in_text(anonymized['text'])

        return anonymized

    def _hash_username(self, username):
        """Hash username with SHA-256 + salt."""
        salted = f"{self.salt}:{username}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()[:16]  # Truncated hash

    def _mask_pii_in_text(self, text):
        """Remove/mask PII patterns in review text."""
        # Mask phone numbers
        text = re.sub(r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '[PHONE]', text)
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)

        # Mask email addresses
        text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)

        # Mask Line IDs (common in Thai reviews)
        text = re.sub(r'(?i)line\s*[:=]?\s*@?\w+', '[LINE_ID]', text)

        # Mask Thai national ID patterns (13 digits)
        text = re.sub(r'\b\d{1}-?\d{4}-?\d{5}-?\d{2}-?\d{1}\b', '[ID]', text)

        return text

    def anonymize_batch(self, reviews):
        """Anonymize multiple reviews."""
        return [self.anonymize_review(r) for r in reviews]
