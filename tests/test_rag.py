from app.rag.rerankers import Candidate
from app.schemas.rag import RagSearchRequest
from app.services.rag import RagService
from tests.conftest import auth_header
from tests.test_documents import upload_txt


class FakeEmbeddings:
    def embed_query(self, text):
        return [1.0, 0.0, 0.0]

    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class FakeVectorStore:
    def __init__(self):
        self.points = []

    def delete_document(self, document_id):
        self.points = [point for point in self.points if point.payload["document_id"] != document_id]

    def upsert(self, points):
        self.points.extend(points)

    def search(self, *, vector, top_k, filters=None):
        class Hit:
            def __init__(self, payload):
                self.payload = payload
                self.score = 0.9

        return [Hit(point.payload) for point in self.points[:top_k]]


def test_index_document_endpoint_with_mocked_rag(client, monkeypatch):
    headers = auth_header(client, "analyst@example.com", "Analyst123!")
    document_id = upload_txt(client, headers).json()["id"]
    fake_store = FakeVectorStore()

    def fake_init(self, db, embeddings=None, vector_store=None, reranker=None):
        self.db = db
        from app.repositories.documents import DocumentRepository
        from app.services.documents import DocumentService
        from app.services.audit import AuditService
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from app.rag.rerankers import FallbackFinancialReranker

        self.repo = DocumentRepository(db)
        self.documents = DocumentService(db)
        self.embeddings = FakeEmbeddings()
        self.vector_store = fake_store
        self.reranker = FallbackFinancialReranker()
        self.audit = AuditService(db)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    monkeypatch.setattr(RagService, "__init__", fake_init)
    response = client.post("/api/v1/rag/index-document", json={"document_id": document_id}, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["chunks_indexed"] == 1


def test_fallback_reranker_prefers_financial_overlap():
    from app.rag.rerankers import FallbackFinancialReranker

    ranked = FallbackFinancialReranker().rerank(
        "high debt ratio risk",
        [
            Candidate("unrelated contract language", 0.8, {}),
            Candidate("debt ratio covenant risk increased", 0.75, {}),
        ],
    )
    assert ranked[0][0].text.startswith("debt ratio")
