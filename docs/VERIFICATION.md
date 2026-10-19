# Verification — 2026-10-19

Upstream baseline: 4cc9fa17653d695d64fb9eee5b33d4de55ff84e8, committed 2026-10-03. MIT / Copyright Microsoft Corporation retained.

Baseline: installed the local upstream MarkItDown package using uv and executed `markitdown --help` and conversion of a fictional TXT invoice. Output preserved the invoice fields as expected; no optional cloud model was configured.

Extension: 11 API/field tests pass on Python 3.12.14, including real subprocess conversions of TXT and an in-memory synthetic DOCX. Ruff checks and the upstream Black 23.7.0 formatting convention are applied to new service files. pip-audit reports no known vulnerabilities in the installed environment.

A Starlette TestClient warning recommends future migration from httpx to httpx2. Tests currently pass; this deprecation is not hidden.

Not verified: Docker build/runtime (no local Docker daemon), PDF/XLSX/HTML/CSV/JSON API fixture coverage, adversarial parser isolation, worker exhaustion/production load, OCR, model extraction, external hosting, and the full original Microsoft test matrix. No real document, API key, production database or customer information was used.
