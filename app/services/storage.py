import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.root = self.settings.storage_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def validate(self, file: UploadFile, size: int) -> None:
        if file.content_type not in self.settings.allowed_mime_types:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if size > max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

    def save(self, *, data: bytes, filename: str, company_id: int) -> str:
        digest = hashlib.sha256(data).hexdigest()[:16]
        safe_suffix = Path(filename).suffix.lower()
        key = f"company-{company_id}/{uuid4().hex}-{digest}{safe_suffix}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def path_for(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if self.root.resolve() not in path.parents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage key")
        return path

    def delete(self, storage_key: str) -> None:
        path = self.path_for(storage_key)
        if path.exists():
            path.unlink()
