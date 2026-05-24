from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.core.config import get_settings


class QdrantVectorStore:
    def __init__(self):
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url, api_key=self.settings.qdrant_api_key)
        self.collection = self.settings.qdrant_collection

    def ensure_collection(self) -> None:
        collections = {c.name for c in self.client.get_collections().collections}
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(
                    size=self.settings.embedding_dimension,
                    distance=qm.Distance.COSINE,
                ),
            )

    def upsert(self, points: list[qm.PointStruct]) -> None:
        self.ensure_collection()
        self.client.upsert(collection_name=self.collection, points=points)

    def delete_document(self, document_id: int) -> None:
        self.ensure_collection()
        self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[qm.FieldCondition(key="document_id", match=qm.MatchValue(value=document_id))]
                )
            ),
        )

    def search(self, *, vector: list[float], top_k: int, filters: dict | None = None):
        self.ensure_collection()
        must: list[qm.Condition] = []
        for key, value in (filters or {}).items():
            if value is not None:
                must.append(qm.FieldCondition(key=key, match=qm.MatchValue(value=str(value))))
        query_filter = qm.Filter(must=must) if must else None
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
