# Example code of how to use the RAG

from rag import Core
import os
from dotenv import load_dotenv

load_dotenv()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LANGUAGE_MODEL = os.getenv("LANGUAGE_MODEL")

rag = Core(EMBEDDING_MODEL, LANGUAGE_MODEL)
rag.add_files("telephone.txt")
print(rag.generate("how to fix telephone in 500 words or less"))
print("-" * 80)
print(rag.generate("now summarize it in 100 words or less"))
