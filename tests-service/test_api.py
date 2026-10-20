from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from service.app import MAX_FILE, app
from service.extraction import extract_invoice

TOKEN = "synthetic-test-token-only"
INVOICE = Path("examples/invoice.txt").read_bytes()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DOCUMENT_API_TOKEN", TOKEN)
    with TestClient(app) as test_client:
        yield test_client


def auth():
    return {"Authorization": f"Bearer {TOKEN}"}


def test_health_without_auth(client):
    assert client.get("/health").json()["external_ai"] is False


def test_authentication_and_fail_closed(client, monkeypatch):
    assert (
        client.post("/v1/extract", files={"file": ("demo.txt", INVOICE)}).status_code
        == 401
    )
    monkeypatch.delenv("DOCUMENT_API_TOKEN")
    assert (
        client.post("/v1/extract", files={"file": ("demo.txt", INVOICE)}).status_code
        == 503
    )


def test_real_markitdown_conversion_and_structured_fields(client):
    response = client.post(
        "/v1/extract", headers=auth(), files={"file": ("invoice.txt", INVOICE)}
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["extraction"]["fields"] == {
        "invoice_id": "DEMO-001",
        "date": "2026-01-01",
        "currency": "USD",
        "total": "42.50",
    }
    assert "DEMO ONLY" in result["markdown"]
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize(
    "filename,body,status",
    [
        ("bad.exe", b"demo", 415),
        ("empty.txt", b"", 422),
        ("large.txt", b"x" * (MAX_FILE + 1), 413),
    ],
)
def test_file_validation(client, filename, body, status):
    assert (
        client.post(
            "/v1/extract", headers=auth(), files={"file": (filename, body)}
        ).status_code
        == status
    )


def test_partial_batch_is_explicit_and_ordered(client):
    response = client.post(
        "/v1/batch",
        headers=auth(),
        files=[("files", ("good.txt", INVOICE)), ("files", ("bad.exe", b"bad"))],
    )
    assert response.status_code == 207
    assert [r["status"] for r in response.json()["results"]] == ["ok", "error"]
    assert [r["position"] for r in response.json()["results"]] == [0, 1]


def test_batch_count_limit(client):
    files = [("files", (f"{i}.txt", b"demo")) for i in range(6)]
    assert client.post("/v1/batch", headers=auth(), files=files).status_code == 400


def test_ambiguous_and_invalid_invoice_fields_are_not_invented():
    result = extract_invoice("Invoice: A\nInvoice: B\nDate: 2026-02-30\nNo total")
    assert all(value is None for value in result["fields"].values())
    assert len(result["warnings"]) == 4


def test_docx_conversion_uses_real_converter(client):
    import io
    import zipfile

    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',  # noqa: E501 - canonical XML fixture
        )
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',  # noqa: E501 - canonical XML fixture
        )
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Invoice: DEMO-DOCX</w:t></w:r></w:p></w:body></w:document>',  # noqa: E501 - canonical XML fixture
        )
    result = client.post(
        "/v1/extract", headers=auth(), files={"file": ("demo.docx", content.getvalue())}
    )
    assert result.status_code == 200, result.text
    assert result.json()["extraction"]["fields"]["invoice_id"] == "DEMO-DOCX"


def test_partial_or_malformed_amount_is_not_silently_truncated():
    assert extract_invoice("Total: USD 42.12345")["fields"]["total"] is None
    assert extract_invoice("Total: USD 1,234.50")["fields"]["total"] is None
