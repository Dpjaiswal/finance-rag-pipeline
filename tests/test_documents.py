from io import BytesIO

from tests.conftest import auth_header


def upload_txt(client, headers, company_name="Acme Finance"):
    return client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "Q4 Debt Report", "company_name": company_name, "document_type": "report", "tags": '["q4"]'},
        files={"file": ("report.txt", BytesIO(b"Debt ratio increased while cash flow decreased."), "text/plain")},
    )


def test_document_upload_and_metadata_search(client):
    headers = auth_header(client, "analyst@example.com", "Analyst123!")
    upload = upload_txt(client, headers)
    assert upload.status_code == 201, upload.text
    response = client.get("/api/v1/documents/search?title=Debt", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_tenant_isolation_on_document_listing(client):
    analyst_headers = auth_header(client, "analyst@example.com", "Analyst123!")
    client_headers = auth_header(client, "client@example.com", "Client123!")
    assert upload_txt(client, analyst_headers).status_code == 201
    response = client.get("/api/v1/documents", headers=client_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_client_cannot_delete_without_permission(client):
    analyst_headers = auth_header(client, "analyst@example.com", "Analyst123!")
    client_headers = auth_header(client, "client@example.com", "Client123!")
    document_id = upload_txt(client, analyst_headers).json()["id"]
    response = client.delete(f"/api/v1/documents/{document_id}", headers=client_headers)
    assert response.status_code == 403
