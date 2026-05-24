from uuid import uuid5, NAMESPACE_URL

from fastapi import HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http import models as qm
from sqlalchemy.orm import Session

from app.models.document import DocumentChunk
from app.models.enums import DocumentStatus
from app.models.user import User
from app.rag.embeddings import EmbeddingProvider, get_embedding_provider
from app.rag.rerankers import Candidate, Reranker, get_reranker
from app.rag.vector_store import QdrantVectorStore
from app.rbac.access import is_admin, user_company_name
from app.repositories.documents import DocumentRepository
from app.schemas.rag import RagSearchRequest, RagSearchResult
from app.services.audit import AuditService
from app.services.documents import DocumentService


class RagService:
    def __init__(
        self,
        db: Session,
        embeddings: EmbeddingProvider | None = None,
        vector_store: QdrantVectorStore | None = None,
        reranker: Reranker | None = None,
    ):
        self.db = db
        self.repo = DocumentRepository(db)
        self.documents = DocumentService(db)
        self.embeddings = embeddings or get_embedding_provider()
        self.vector_store = vector_store or QdrantVectorStore()
        self.reranker = reranker or get_reranker()
        self.audit = AuditService(db)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    def index_document(self, document_id: int, user: User, force_reindex: bool = False) -> int:
        document = self.repo.get(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.documents.ensure_document_access(document, user)
        if document.indexed_in_vector_db and not force_reindex:
            return len(document.chunks)
        if not document.extracted_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extracted text available")

        self.vector_store.delete_document(document.id)
        texts = self.splitter.split_text(document.extracted_text)
        vectors = self.embeddings.embed_documents(texts)
        chunks: list[DocumentChunk] = []
        points: list[qm.PointStruct] = []
        for idx, (text, vector) in enumerate(zip(texts, vectors, strict=True)):
            chunk_id = str(uuid5(NAMESPACE_URL, f"document:{document.id}:chunk:{idx}"))
            payload = {
                "chunk_id": chunk_id,
                "document_id": document.id,
                "chunk_index": idx,
                "page_number": None,
                "text": text,
                "company_name": document.company_name,
                "document_type": document.document_type.value,
                "title": document.title,
            }
            chunks.append(DocumentChunk(chunk_id=chunk_id, document_id=document.id, chunk_index=idx, text=text))
            points.append(qm.PointStruct(id=chunk_id, vector=vector, payload=payload))

        self.vector_store.upsert(points)
        self.repo.replace_chunks(document, chunks)
        document.indexed_in_vector_db = True
        document.status = DocumentStatus.indexed
        self.audit.log(user_id=user.id, action="rag.index_document", target_type="document", target_id=document.id)
        self.db.commit()
        return len(chunks)

    def remove_document(self, document_id: int, user: User) -> None:
        document = self.repo.get(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.documents.ensure_document_access(document, user)
        self.vector_store.delete_document(document_id)
        document.indexed_in_vector_db = False
        document.chunks.clear()
        self.audit.log(user_id=user.id, action="rag.remove_document", target_type="document", target_id=document.id)
        self.db.commit()

    def search(self, payload: RagSearchRequest, user: User) -> list[RagSearchResult]:
        filters = {
            "company_name": payload.company_name,
            "document_type": payload.document_type.value if payload.document_type else None,
        }
        if not is_admin(user):
            company_name = user_company_name(user)
            if not company_name:
                return []
            filters["company_name"] = company_name
        vector = self.embeddings.embed_query(payload.query)
        raw = self.vector_store.search(vector=vector, top_k=payload.top_k, filters=filters)
        candidates = [
            Candidate(text=(hit.payload or {}).get("text", ""), vector_score=float(hit.score), payload=hit.payload or {})
            for hit in raw
        ]
        ranked = self.reranker.rerank(payload.query, candidates)[: payload.final_k]
        self.audit.log(
            user_id=user.id,
            action="rag.search",
            target_type="rag",
            metadata={"query": payload.query, "filters": filters},
        )
        self.db.commit()
        return [
            RagSearchResult(
                document_id=int(candidate.payload["document_id"]),
                title=candidate.payload["title"],
                company_name=candidate.payload["company_name"],
                document_type=candidate.payload["document_type"],
                chunk_text=candidate.text,
                relevance_score=candidate.vector_score,
                rerank_score=score,
                page_number=candidate.payload.get("page_number"),
            )
            for candidate, score in ranked
        ]
