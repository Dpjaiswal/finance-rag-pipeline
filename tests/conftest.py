import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from app.api.deps import get_db  # noqa: E402
from app.db.session import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.rbac import Permission, Role  # noqa: E402
from app.models.user import User  # noqa: E402
from app.rbac.permissions import PermissionCode  # noqa: E402
from app.core.security import hash_password  # noqa: E402


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def db_session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_test_data(db)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_test_data(db: Session) -> None:
    company_a = Company(name="Acme Finance")
    company_b = Company(name="Globex Capital")
    db.add_all([company_a, company_b])
    db.flush()

    permissions = {code.value: Permission(code=code.value, description=code.value) for code in PermissionCode}
    db.add_all(permissions.values())
    db.flush()

    admin = Role(name="Admin", permissions=list(permissions.values()))
    analyst = Role(
        name="Financial Analyst",
        permissions=[
            permissions["documents:upload"],
            permissions["documents:view"],
            permissions["documents:search"],
            permissions["documents:delete"],
            permissions["rag:index"],
            permissions["rag:remove"],
            permissions["rag:search"],
            permissions["rag:context"],
        ],
    )
    client_role = Role(name="Client", permissions=[permissions["documents:view"], permissions["rag:context"]])
    db.add_all([admin, analyst, client_role])
    db.flush()

    db.add_all(
        [
            User(
                full_name="Admin",
                email="admin@example.com",
                password_hash=hash_password("Admin123!"),
                company_id=company_a.id,
                roles=[admin],
            ),
            User(
                full_name="Analyst",
                email="analyst@example.com",
                password_hash=hash_password("Analyst123!"),
                company_id=company_a.id,
                roles=[analyst],
            ),
            User(
                full_name="Client",
                email="client@example.com",
                password_hash=hash_password("Client123!"),
                company_id=company_b.id,
                roles=[client_role],
            ),
        ]
    )
    db.commit()


def auth_header(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
