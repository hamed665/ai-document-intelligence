# Document Intelligence API

A bounded local document-processing service by Hamed Minaei, built on Microsoft's MarkItDown library. Converts uploaded files to Markdown, extracts conservative structured invoice fields, and supports ordered batch results.

**Status: tested local API preview, not production-ready.** No external AI service, OCR provider, customer document or production environment is connected. “Structured extraction” here means deterministic rules, not an LLM.

## Architecture

| Component | Role |
| --- | --- |
| `packages/markitdown` | Original Microsoft conversion library, retained unchanged |
| `service/app.py` | Authenticated REST endpoints, input limits, bounded concurrency and temporary files |
| `service/worker.py` | Per-document conversion subprocess with CPU/output limits and timeout handling |
| `service/extraction.py` | Invoice ID/date/currency/total extraction; missing or ambiguous fields stay null |
| `tests-service` | Real TXT/DOCX conversion, API validation and batch regression tests |

`POST /v1/extract` returns Markdown, title, SHA-256, size and `invoice.v1` fields. `POST /v1/batch` accepts 1–5 files, preserves input order and returns HTTP 207 when some items fail. `GET /health` is public. `/docs` exposes the API schema.

## Features

- Real MarkItDown conversion in a separate local process; plugins are disabled.
- Strict extension allowlist, 2 MiB per-file limit and bounded total request size.
- Two conversion slots, a twenty-second wall timeout, fifteen-second worker CPU limit and bounded Markdown output.
- Dedicated bearer-token requirement; missing/short configuration fails closed.
- Rule extraction with explicit warnings for absent/ambiguous invoice fields; malformed amounts are never silently truncated.
- Ordered partial-success batches and automatic temporary-file cleanup.
- Frozen dependency lock, automated API tests and CI; optional isolated Docker configuration.

TXT and a synthetic DOCX are covered by actual conversion tests. PDF/XLSX/HTML/CSV/JSON support is delegated to installed MarkItDown converters and has not received equivalent API fixture coverage. Scanned-document OCR and LLM extraction are not configured.

## Installation

Requires Linux, Python 3.12 and uv. The worker uses POSIX resource limits.

```bash
uv sync --locked --group dev
uv run pytest tests-service
```

Generate a fresh local token with `openssl rand -hex 32`, set it as `DOCUMENT_API_TOKEN` in your shell, then run:

```bash
uv run uvicorn service.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. Use only the fictional `examples/invoice.txt` while reviewing this portfolio.

## Configuration

`.env.example` documents the sole required variable, `DOCUMENT_API_TOKEN` (at least sixteen characters; use a fresh high-entropy value). The service reads shell environment variables; it does not automatically load the example file. No production key is required or permitted for the demo.

```bash
curl -H "Authorization: Bearer $DOCUMENT_API_TOKEN" -F file=@examples/invoice.txt http://127.0.0.1:8000/v1/extract
curl -H "Authorization: Bearer $DOCUMENT_API_TOKEN" -F files=@examples/invoice.txt -F files=@examples/invoice.txt http://127.0.0.1:8000/v1/batch
```

Optional container command: `docker compose -f compose.api.yml up --build`. It binds localhost, uses an internal Docker network, a non-root user, read-only root filesystem, temporary storage and container resource limits. Docker is unavailable in the development environment, so this configuration is not claimed as runtime-verified.

## Security

Uploaded names are never used as filesystem paths. The service accepts multipart uploads only, never URLs; files use generated temporary paths and are removed after processing. Plugins and optional cloud AI are disabled. Tokens use constant-time comparison and document contents are not logged by the added code. Chunked uploads without Content-Length are rejected; the application also enforces actual per-file bytes read.

A subprocess is not a complete security sandbox. Container isolation, parser patching, request-rate controls, TLS, operational logging/retention and hostile-document testing remain release requirements. Markdown output is untrusted content and must be escaped or sanitized by any renderer. No antivirus or full document sanitization is provided.

Initial `pip-audit` reported no known package vulnerabilities; this does not assess OS/container vulnerabilities or all malicious-file risks. The service is not approved for real customer documents.

## Testing

```bash
uv run pytest tests-service
uv run ruff check service tests-service
uvx black==23.7.0 --check service tests-service
uv run pip-audit --path .venv/lib/python3.12/site-packages
```

Eleven tests cover real conversion, structured fields, missing/ambiguous values, malformed amounts, authentication, disabled configuration, unsupported/empty/oversized files, batch bounds and mixed results. The original Microsoft test suites remain separate; they are not represented as having passed locally. See [verification](docs/VERIFICATION.md).

## Demo

The fictional input returns invoice ID `DEMO-001`, date `2026-01-01`, currency `USD` and total string `42.50`. The API never charges or pays an invoice, contacts a customer, or submits information to an external model. No hosted deployment is claimed.

## Attribution

Based on [microsoft/markitdown](https://github.com/microsoft/markitdown), baseline `4cc9fa17653d695d64fb9eee5b33d4de55ff84e8`. The original MIT license, Microsoft copyright and complete Git history are retained. Original converter packages are unchanged; the original README is preserved in `docs/UPSTREAM_README.md`.

Hamed Minaei's additions: `service/`, `tests-service/`, root service packaging/lock, synthetic invoice, API container configuration, API CI and documentation. See [NOTICE](NOTICE). No Microsoft endorsement is implied.
