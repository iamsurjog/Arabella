import os
import logging
from typing import List, Optional, Dict, Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class QdrantDB:
    def __init__(
        self,
        path: str = "./vector_db",
        collection_name: str = "nodes",
        vector_size: int = 768
    ):
        self.collection = collection_name
        self.vector_size = vector_size
        self._remote = False

        # Try to open a local (file-backed) Qdrant instance first.
        try:
            self.client = QdrantClient(path=path)
        except Exception as e:
            msg = str(e)
            # Detect the typical storage-lock message and attempt to fall back
            # to a Qdrant server if available.
            if "already accessed" in msg or "already used" in msg or "Storage folder" in msg:
                fallback_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
                logger.warning(
                    "Local Qdrant storage at '%s' appears locked. Falling back to Qdrant server at %s.\n" \
                    "Original error: %s",
                    path,
                    fallback_url,
                    msg,
                )
                try:
                    self.client = QdrantClient(url=fallback_url)
                    self._remote = True
                except Exception as e2:
                    # Re-raise an informative error including both exceptions.
                    raise RuntimeError(
                        f"Failed to open local Qdrant storage ({msg}) and also failed to connect to Qdrant server at {fallback_url}: {e2}.\n"
                        "If you need concurrent local access, run a Qdrant server and set QDRANT_URL, or stop the other process using the folder."
                    )
            else:
                # Unknown error, surface it.
                raise

        # Ensure collection exists
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
