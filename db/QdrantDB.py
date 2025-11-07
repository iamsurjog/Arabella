from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Optional, Dict, Any

class QdrantDB:
    def __init__(
        self,
        path: str = "./vector_db",
        collection_name: str = "nodes",
        vector_size: int = 768
    ):
        self.client = QdrantClient(path=path)
        self.collection = collection_name
        self.vector_size = vector_size
        
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                ),
            )

    def upsert_points(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None
    ):
        """Upsert points into collection"""
        if payloads is None:
            payloads = [{}] * len(ids)
        
        points = []
        for i, (id_val, v, p) in enumerate(zip(ids, vectors, payloads)):
            point_id = abs(hash(id_val)) % (2**31)
            point = PointStruct(
                id=point_id,
                vector=np.array(v).astype(np.float32).tolist(),
                payload=p
            )
            points.append(point)
        
        self.client.upsert(collection_name=self.collection, points=points)

    def query(
        self,
        vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.0
    ) -> List[Any]:
        """Query collection and return results"""
        results = self.client.search(
            collection_name=self.collection,
            query_vector=np.array(vector).astype(np.float32).tolist(),
            limit=limit,
            score_threshold=score_threshold
        )
        return results

    def delete_collection(self):
        """Delete entire collection"""
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(collection_name=self.collection)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata"""
        try:
            return self.client.get_collection(self.collection)
        except:
            return {"status": "collection not found"}

    def clear_collection(self):
        """Clear all points from collection"""
        self.delete_collection()
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            ),
        )
