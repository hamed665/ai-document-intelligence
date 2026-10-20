# Engineering contributions — Hamed Minaei

**Project:** Document Intelligence API  
**Role:** REST API design, bounded converter integration, structured extraction rules, batch semantics, container isolation and regression testing  
**Portfolio:** https://github.com/hamed665

I developed this portfolio edition as an extension of Microsoft MarkItDown. The original foundation, copyright, license notices and Git ancestry are preserved. The work described below is my added integration and application development.

## My implementation

Authenticated extraction API, conservative invoice fields, ordered partial-success batches and isolated Docker execution.

**Primary code:** `service/`, `tests-service/`, service packaging, API container configuration and CI.

## Review the work

- [Implementation pull request](https://github.com/hamed665/ai-document-intelligence/pull/1): inspect the actual added code and reviewable history.
- [Testing instructions](README.md#testing): reproduce the relevant checks.
- **Verification evidence:** 11 API/field tests with real TXT/DOCX conversion; 21 inherited core/OCR/MCP jobs; actual non-root, read-only, no-network container smoke.
- **Demonstration:** Local authenticated API and repeatable CI container scenario; no hosted API.

## Engineering boundary

Structured fields use deterministic rules. Broad API format quality, hostile-parser/load behavior, complete Compose deployment and optional cloud-model quality remain unverified.

This is a portfolio preview. The test evidence describes the checks performed and does not establish production readiness.

## Foundation and attribution

Microsoft MarkItDown supplies the original project foundation. My contribution is the extension and integration scope above; I do not claim original authorship of the upstream platform, SDKs or conversion libraries. See [Attribution](README.md#attribution), the retained root license and the project's dependency-license notes for exact provenance and applicable terms.
