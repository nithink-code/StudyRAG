from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, SearchRequest
import os
import time

class QdrantStorage:
    def __init__(self, collection_name="docs", dim=1536, max_retries=3):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")
        
        # Retry connection logic
        last_error = None
        for attempt in range(max_retries):
            try:
                # Increased timeout and added prefer_grpc=False for better HTTP compatibility
                self.client = QdrantClient(
                    url=url, 
                    api_key=api_key, 
                    timeout=60,
                    prefer_grpc=False  # Use HTTP instead of gRPC for better compatibility
                )
                self.collection_name = collection_name
                
                # Verify connection by checking if collection exists
                if not self.client.collection_exists(collection_name):
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
                    )
                
                # If we get here, connection is successful
                return
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Wait before retrying (exponential backoff)
                    time.sleep(2 ** attempt)
                    continue
                else:
                    # All retries failed
                    raise ConnectionError(
                        f"Failed to connect to Qdrant after {max_retries} attempts. "
                        f"Last error: {str(e)}. "
                        f"Please check your QDRANT_URL and network connection."
                    ) from e
    
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
    
    def delete_by_source(self, source_id: str):
        """Delete all points with a specific source_id from the collection."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Delete points where payload.source matches source_id
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source_id)
                    )
                ]
            )
        )
    
    def clear_collection(self):
        """Delete all points from the collection."""
        # Delete the collection and recreate it
        self.client.delete_collection(collection_name=self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
    
    def get_all_sources(self):
        """Get a list of all unique source documents in the collection."""
        try:
            # Scroll through all points to get unique sources
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            sources = set()
            for point in points:
                payload = getattr(point, "payload", None) or {}
                source = payload.get("source", "")
                if source:
                    sources.add(source)
            
            return list(sources)
        except Exception:
            return []



