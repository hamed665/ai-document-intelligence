# Verification — 2026-10-19

Upstream baseline: 4cc9fa17653d695d64fb9eee5b33d4de55ff84e8, committed 2026-10-03. MIT / Copyright Microsoft Corporation retained.

Baseline: installed the local upstream MarkItDown package using uv and executed `markitdown --help` and conversion of a fictional TXT invoice. Output preserved the invoice fields as expected; no optional cloud model was configured.

Extension: 11 API/field tests pass on Python 3.12.14, including real subprocess conversions of TXT and an in-memory synthetic DOCX. Ruff checks and the upstream Black 23.7.0 formatting convention are applied to new service files. pip-audit reports no known vulnerabilities in the installed environment.

A Starlette TestClient warning recommends future migration from httpx to httpx2. Tests currently pass; this deprecation is not hidden.

Not verified: Docker build/runtime (no local Docker daemon), PDF/XLSX/HTML/CSV/JSON API fixture coverage, adversarial parser isolation, worker exhaustion/production load, OCR, model extraction, external hosting, and the full original Microsoft test matrix. No real document, API key, production database or customer information was used.

## Inspected CI results

Document API run 39254167313 and pre-commit run 39254167304 passed. The full inherited matrix run 39254167449 completed with 20 passing jobs and one failure: ocr-tests (windows-11-vs2026-arm, 3.12) failed while building/installing PyMuPDF, before tests began (metadata-generation-failed; mupdfwrap.py Visual Studio build exited 1). The full matrix is therefore not green. Linux OCR, Windows x64 OCR, core and MCP jobs passed. Do not represent Windows ARM OCR as supported by this verification.


## Windows ARM toolchain investigation — 2026-10-20

The second matrix run 39303164708 again passed 20 jobs, but Windows ARM OCR installation failed. Its full log shows PyMuPDF **2.0** building bundled **MuPDF 1.28.5**; these are separate version numbers. The build uses Visual Studio 2026 but legacy MuPDF solution/toolset settings, and fails in Windows SDK winnt.h with missing `_CountOneBits64`, followed by missing libtesseract.lib. This is not an API test assertion failure.

PyMuPDF's authoritative setup.py documents `PYMUPDF_SETUP_MUPDF_VS_UPGRADE=1` to upgrade its VS2019 project files for newer Visual Studio installations. The OCR installation step now enables that supported option only on the Windows ARM runner. No dependency is downgraded, test skipped, assertion removed, or failure ignored. The full matrix must confirm whether this resolves the native build; until then Windows ARM OCR remains unverified.

References: https://github.com/pymupdf/PyMuPDF/blob/main/setup.py ; https://github.com/actions/runner-images/issues/11684 . PyMuPDF's separate AGPL/commercial licensing still applies to the inherited optional OCR plugin. It is not installed by the isolated REST API runtime and this CI change does not grant redistribution or commercial rights for it.
