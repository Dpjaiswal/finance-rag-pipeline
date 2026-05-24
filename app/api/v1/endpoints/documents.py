import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.enums import DocumentType
from app.models.user import User
from app.rbac.permissions import PermissionCode
from app.repositories.documents import DocumentRepository
from app.schemas.common import MessageResponse, Page
from app.schemas.document import DocumentDetail, DocumentRead
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=201)
async def upload_document(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: DocumentType = Form(...),
    tags: str | None = Form(default=None),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.documents_upload)),
) -> DocumentRead:
    parsed_tags = None
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="tags must be a JSON list") from exc
    document = await DocumentService(db).upload(
        file=file,
        title=title,
        company_name=company_name,
        document_type=document_type,
        tags=parsed_tags,
        description=description,
        user=current_user,
    )
    return document


@router.get("", response_model=Page[DocumentRead])
def list_documents(
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.documents_view)),
) -> Page[DocumentRead]:
    items, total = DocumentRepository(db).search(
        user=current_user,
        company_name=company_name,
        document_type=document_type,
        uploaded_by=uploaded_by,
        date_from=date_from,
        date_to=date_to,
        title=title,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return Page(items=items, total=total, page=page, size=size)


@router.get("/search", response_model=Page[DocumentRead])
def metadata_search(
    company_name: str | None = None,
    document_type: DocumentType | None = None,
    uploaded_by: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    title: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.documents_search)),
) -> Page[DocumentRead]:
    items, total = DocumentRepository(db).search(
        user=current_user,
        company_name=company_name,
        document_type=document_type,
        uploaded_by=uploaded_by,
        date_from=date_from,
        date_to=date_to,
        title=title,
        page=page,
        size=size,
    )
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.documents_view)),
) -> DocumentDetail:
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    DocumentService(db).ensure_document_access(document, current_user)
    detail = DocumentDetail.model_validate(document)
    detail.chunk_count = len(document.chunks)
    return detail


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.documents_delete)),
) -> MessageResponse:
    DocumentService(db).delete(document_id, current_user)
    return MessageResponse(message="Document deleted")
