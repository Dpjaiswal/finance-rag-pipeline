from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentType
from app.models.user import User
from app.rbac.access import is_admin, user_company_name
from app.repositories.documents import DocumentRepository
from app.services.audit import AuditService
from app.services.extraction import TextExtractionService
from app.services.storage import StorageService


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)
        self.storage = StorageService()
        self.extractor = TextExtractionService()
        self.audit = AuditService(db)

    def ensure_document_access(self, document: Document, user: User) -> None:
        if is_admin(user):
            return
        if document.company_id != user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document is outside your tenant scope")

    async def upload(
        self,
        *,
        file: UploadFile,
        title: str,
        company_name: str,
        document_type: DocumentType,
        tags: list[str] | None,
        description: str | None,
        user: User,
    ) -> Document:
        if not user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")
        if not is_admin(user) and company_name != user_company_name(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot upload for another company")
        data = await file.read()
        self.storage.validate(file, len(data))
        storage_key = self.storage.save(data=data, filename=file.filename or "document", company_id=user.company_id)
        path = self.storage.path_for(storage_key)
        text = self.extractor.extract(path, file.content_type or "")
        document = Document(
            title=title,
            company_id=user.company_id,
            company_name=company_name,
            document_type=document_type,
            uploaded_by_id=user.id,
            file_name=file.filename or "document",
            storage_key=storage_key,
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(data),
            tags=tags,
            description=description,
            extracted_text=text,
            extracted_text_available=bool(text.strip()),
        )
        self.repo.add(document)
        self.audit.log(user_id=user.id, action="document.upload", target_type="document", target_id=document.id)
        self.db.commit()
        return document

    def delete(self, document_id: int, user: User) -> None:
        document = self.repo.get(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.ensure_document_access(document, user)
        self.repo.soft_delete(document)
        self.storage.delete(document.storage_key)
        self.audit.log(user_id=user.id, action="document.delete", target_type="document", target_id=document.id)
        self.db.commit()
