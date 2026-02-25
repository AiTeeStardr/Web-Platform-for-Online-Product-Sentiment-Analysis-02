"""
Text Preprocessor for Thai NLP
Pipeline: Text Cleaning → Emoji Conversion → Tokenization → Stop Word Removal
"""
import re
try:
    import emoji
except ImportError:
    emoji = None

try:
    from pythainlp.tokenize import word_tokenize
    from pythainlp.corpus import thai_stopwords
    HAS_PYTHAINLP = True
except ImportError:
    HAS_PYTHAINLP = False


# Thai emoji-to-text mappings (common sentiment-bearing emojis)
EMOJI_THAI_MAP = {
    '😀': 'ยิ้ม', '😁': 'ยิ้มกว้าง', '😂': 'หัวเราะ', '🤣': 'ขำมาก',
    '😃': 'ยิ้ม', '😄': 'ดีใจ', '😅': 'เหงื่อตก', '😆': 'หัวเราะ',
    '😍': 'หลงรัก', '🥰': 'น่ารัก', '😘': 'จูบ', '😊': 'อิ่มใจ',
    '😎': 'เท่', '🤩': 'ตื่นเต้น', '😇': 'ดีใจ',
    '😢': 'เศร้า', '😭': 'ร้องไห้', '😡': 'โกรธ', '🤬': 'โกรธมาก',
    '😤': 'หงุดหงิด', '😠': 'โมโห', '😩': 'เหนื่อย', '😫': 'ทนไม่ไหว',
    '👍': 'ดี', '👎': 'ไม่ดี', '❤️': 'รัก', '💔': 'เสียใจ',
    '🔥': 'เยี่ยม', '💯': 'สุดยอด', '⭐': 'ดาว', '✨': 'สวย',
    '💩': 'แย่', '🤢': 'คลื่นไส้', '🤮': 'แย่มาก',
    '👏': 'ปรบมือ', '🙏': 'ขอบคุณ', '💪': 'แข็งแรง',
    '😑': 'เบื่อ', '😒': 'ไม่พอใจ', '🙄': 'เบื่อ', '😏': 'เหยียด',
    '🥺': 'น่าสงสาร', '😱': 'ตกใจ', '😰': 'กังวล',
}


class TextPreprocessor:
    """Thai text preprocessing pipeline."""

    def __init__(self, tokenizer_engine='newmm'):
        self.tokenizer_engine = tokenizer_engine
        self.stopwords = set()
        if HAS_PYTHAINLP:
            self.stopwords = thai_stopwords()

    def preprocess(self, text):
        """
        Full preprocessing pipeline.

        Returns:
            dict: {
                'original': str,
                'cleaned_text': str,
                'tokens': list,
                'emojis_found': list
            }
        """
        original = text

        # Step 1: Emoji-to-text conversion (before text cleaning)
        text, emojis_found = self._convert_emojis(text)

        # Step 2: Text cleaning
        text = self._clean_text(text)

        # Step 3: Tokenization
        tokens = self._tokenize(text)

        # Step 4: Stop word removal
        tokens = self._remove_stopwords(tokens)

        return {
            'original': original,
            'cleaned_text': text,
            'tokens': tokens,
            'emojis_found': emojis_found
        }

    def _convert_emojis(self, text):
        """Convert emojis to Thai text descriptions."""
        emojis_found = []

        # Try using custom mapping first
        for emo, thai_text in EMOJI_THAI_MAP.items():
            if emo in text:
                emojis_found.append({'emoji': emo, 'text': thai_text})
                text = text.replace(emo, f' {thai_text} ')

        # Fallback: use emoji library to get descriptions
        if emoji:
            remaining_emojis = []
            result_text = []
            for char in text:
                if emoji.is_emoji(char):
                    desc = emoji.demojize(char, delimiters=('', ''))
                    remaining_emojis.append({'emoji': char, 'text': desc})
                    result_text.append(f' {desc} ')
                else:
                    result_text.append(char)
            text = ''.join(result_text)
            emojis_found.extend(remaining_emojis)

        return text, emojis_found

    def _clean_text(self, text):
        """Clean text: remove HTML, URLs, special chars, normalize."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)

        # Remove email addresses (PDPA compliance)
        text = re.sub(r'\S+@\S+\.\S+', '', text)

        # Remove phone numbers (PDPA compliance)
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '', text)
        text = re.sub(r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '', text)

        # Keep Thai characters, numbers, spaces, and basic punctuation
        text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s.,!?()]+', ' ', text)

        # Normalize repeated characters (e.g., สวยยยยย → สวย)
        text = re.sub(r'(.)\1{3,}', r'\1\1', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _tokenize(self, text):
        """Tokenize Thai text using PyThaiNLP."""
        if not text:
            return []

        if HAS_PYTHAINLP:
            tokens = word_tokenize(text, engine=self.tokenizer_engine)
        else:
            # Fallback: simple whitespace tokenization
            tokens = text.split()

        # Remove whitespace-only tokens
        tokens = [t.strip() for t in tokens if t.strip()]
        return tokens

    def _remove_stopwords(self, tokens):
        """Remove Thai stop words."""
        if not self.stopwords:
            return tokens
        return [t for t in tokens if t not in self.stopwords and len(t) > 1]

    def batch_preprocess(self, texts):
        """Preprocess multiple texts."""
        return [self.preprocess(text) for text in texts]
