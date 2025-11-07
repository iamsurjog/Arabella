from db.QdrantDB import QdrantDB
from db.KuzuDB import KuzuDB
from rag import GraphRAG

def initialize_system():
    """Initialize all database systems"""
    print("=" * 50)
    print("Initializing Arabella System")
    print("=" * 50)
    
    try:
        # Initialize vector DB
        print("\n[1/3] Initializing Qdrant Vector DB...")
        vector_db = QdrantDB(
            path="./vector_db",
            collection_name="nodes",
            vector_size=768
        )
        info = vector_db.get_collection_info()
        print(f"✓ Qdrant initialized: {info}")
        
        # Initialize graph DB
        print("\n[2/3] Initializing KuzuDB Graph DB...")
        graph_db = KuzuDB("./kuzu_db")
        graph_db.test()
        print("✓ KuzuDB initialized")
        
        # Initialize Graph-RAG
        print("\n[3/3] Initializing Graph-RAG Pipeline...")
        rag = GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path="./kuzu_db",
            qdrant_path="./vector_db"
        )
        print("✓ Graph-RAG pipeline initialized")
        
        print("\n" + "=" * 50)
        print("System ready for operation!")
        print("=" * 50)
        return True
    
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        return False

if __name__ == "__main__":
    initialize_system()
