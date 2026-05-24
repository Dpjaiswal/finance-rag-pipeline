from pydantic import BaseModel, Field

from app.models.enums import DocumentType


class IndexDocumentRequest(BaseModel):
    document_id: int
    force_reindex: bool = False


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    company_name: str | None = None
    document_type: DocumentType | None = None
    top_k: int = Field(default=20, ge=1, le=50)
    final_k: int = Field(default=5, ge=1, le=20)


class RagSearchResult(BaseModel):
    document_id: int
    title: str
    company_name: str
    document_type: str
    chunk_text: str
    relevance_score: float
    rerank_score: float
    page_number: int | None = None


class RagSearchResponse(BaseModel):
    query: str
    results: list[RagSearchResult]


class DocumentContextResponse(BaseModel):
    document_id: int
    title: str
    chunks: list[dict]
