import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import ssl

class QueryBridge:
    def __init__(self):
        import nltk
        
        # Handle SSL certificate issues
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        
        # Download NLTK data with error handling
        try:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            print(f"Warning: NLTK download error (will use defaults): {e}")

        try:
            self.stopwords = set(stopwords.words('english'))
        except Exception as e:
            print(f"Warning: Could not load stopwords, using defaults: {e}")
            self.stopwords = set()
            
        self.stopwords.update([
            'how', 'what', 'why', 'when', 'where', 'which',
            'who', 'is', 'are', 'am', 'be', 'do', 'does', 'can', 'will',
            'the', 'a', 'an', 'in', 'on', 'of', 'for', 'to', 'and', 'or'
        ])

    def transform(self, query: str) -> str:
        q = query.lower()
        q = re.sub(r"[^a-z0-9\s]", " ", q)
        tokens = word_tokenize(q)
        keywords = [token for token in tokens if token not in self.stopwords]
        result = " ".join(keywords[:7])
        return result if result.strip() else query
