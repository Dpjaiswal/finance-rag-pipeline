from pathlib import Path

from fastapi import HTTPException, status


class TextExtractionService:
    def extract(self, path: Path, mime_type: str) -> str:
        if mime_type == "application/pdf":
            return self._extract_pdf(path)
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_docx(path)
        if mime_type == "text/plain":
            return path.read_text(encoding="utf-8", errors="ignore")
        return ""

    def _extract_pdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PDF extraction dependency missing") from exc
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _extract_docx(self, path: Path) -> str:
        try:
            from docx import Document as DocxDocument
        except ImportError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DOCX extraction dependency missing") from exc
        document = DocxDocument(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
