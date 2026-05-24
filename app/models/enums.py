from enum import StrEnum


class DocumentType(StrEnum):
    invoice = "invoice"
    report = "report"
    contract = "contract"
    agreement = "agreement"


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    indexed = "indexed"
    deleted = "deleted"
    failed = "failed"
