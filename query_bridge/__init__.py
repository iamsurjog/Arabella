import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class QueryBridge:
    def __init__(self):
        import nltk
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)

        self.stopwords = set(stopwords.words('english'))
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
