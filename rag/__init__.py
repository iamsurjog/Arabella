class Rag:
    def __init__(self, embedding_model, language_model) -> None:
        self.embedding_model = embedding_model
        self.language_model = language_model
