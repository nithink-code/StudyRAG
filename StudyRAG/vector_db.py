from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, SearchRequest
import os

class QdrantStorage:
    def __init__(self, collection_name="docs",dim=1536):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")
        
        self.client = QdrantClient(url=url, api_key=api_key, timeout=30)
        self.collection_name = collection_name
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
    
    def upsert(self, ids, vectors, payloads):
        # Insert or update points in the collection
        # Point structure is used for qdrant client to upsert points
        points=[PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(ids))]
        self.client.upsert(self.collection_name, points=points)

    # Search for 5 most similar vectors to the query vector
    def search(self, query_vector, top_k: int = 5):
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            with_payload=True,
            limit=top_k
        ).points

        context=[]
        sources=set()

        for r in results:
            payload = getattr(r, "payload", None) or {}
            text = payload.get("text", "")
            source = payload.get("source", "")
            if text:
                context.append(text)
                sources.add(source)
        
        return {"contexts": context, "sources": list(sources)}




