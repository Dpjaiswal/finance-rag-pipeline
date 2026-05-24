from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DocumentStatus, DocumentType


class DocumentRead(BaseModel):
    id: int
    title: str
    company_name: str
    document_type: DocumentType
    uploaded_by_id: int
    created_at: datetime
    file_name: str
    mime_type: str
    file_size: int
    tags: list[str] | None = None
    description: str | None = None
    status: DocumentStatus
    extracted_text_available: bool
    indexed_in_vector_db: bool

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentRead):
    chunk_count: int = 0


class DocumentSearchParams(BaseModel):
    company_name: str | None = None
    document_type: DocumentType | None = None
    uploaded_by: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    title: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
