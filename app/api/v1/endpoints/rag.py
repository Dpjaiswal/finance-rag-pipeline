from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import User
from app.rbac.permissions import PermissionCode
from app.repositories.documents import DocumentRepository
from app.schemas.common import MessageResponse
from app.schemas.rag import DocumentContextResponse, IndexDocumentRequest, RagSearchRequest, RagSearchResponse
from app.services.documents import DocumentService
from app.services.rag import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index-document", response_model=dict)
def index_document(
    payload: IndexDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.rag_index)),
) -> dict:
    count = RagService(db).index_document(payload.document_id, current_user, payload.force_reindex)
    return {"document_id": payload.document_id, "chunks_indexed": count}


@router.delete("/remove-document/{document_id}", response_model=MessageResponse)
def remove_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.rag_remove)),
) -> MessageResponse:
    RagService(db).remove_document(document_id, current_user)
    return MessageResponse(message="Document removed from vector index")


@router.post("/search", response_model=RagSearchResponse)
def semantic_search(
    payload: RagSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.rag_search)),
) -> RagSearchResponse:
    return RagSearchResponse(query=payload.query, results=RagService(db).search(payload, current_user))


@router.get("/context/{document_id}", response_model=DocumentContextResponse)
def document_context(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.rag_context)),
) -> DocumentContextResponse:
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    DocumentService(db).ensure_document_access(document, current_user)
    return DocumentContextResponse(
        document_id=document.id,
        title=document.title,
        chunks=[
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "text": chunk.text,
            }
            for chunk in document.chunks
        ],
    )
