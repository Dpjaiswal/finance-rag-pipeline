from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document, DocumentChunk
from app.models.enums import DocumentStatus, DocumentType
from app.models.user import User
from app.rbac.access import is_admin


class DocumentRepository:
    sortable = {"created_at": Document.created_at, "title": Document.title, "company_name": Document.company_name}

    def __init__(self, db: Session):
        self.db = db

    def get(self, document_id: int) -> Document | None:
        return self.db.scalar(
            select(Document)
            .where(Document.id == document_id, Document.deleted_at.is_(None))
            .options(selectinload(Document.chunks))
        )

    def add(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)
        return document

    def search(
        self,
        *,
        user: User,
        company_name: str | None = None,
        document_type: DocumentType | None = None,
        uploaded_by: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        title: str | None = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Document], int]:
        stmt: Select = select(Document).where(Document.deleted_at.is_(None))
        if not is_admin(user):
            stmt = stmt.where(Document.company_id == user.company_id)
        if company_name:
            stmt = stmt.where(Document.company_name.ilike(f"%{company_name}%"))
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if uploaded_by:
            stmt = stmt.where(Document.uploaded_by_id == uploaded_by)
        if date_from:
            stmt = stmt.where(Document.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Document.created_at <= date_to)
        if title:
            stmt = stmt.where(Document.title.ilike(f"%{title}%"))

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        sort_col = self.sortable.get(sort_by, Document.created_at)
        stmt = stmt.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        return list(self.db.scalars(stmt)), total

    def replace_chunks(self, document: Document, chunks: list[DocumentChunk]) -> None:
        document.chunks.clear()
        self.db.flush()
        for chunk in chunks:
            document.chunks.append(chunk)

    def soft_delete(self, document: Document) -> None:
        document.deleted_at = datetime.utcnow()
        document.status = DocumentStatus.deleted
