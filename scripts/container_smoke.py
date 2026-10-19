"""Run inside the isolated demo container; uses only synthetic invoice bytes."""

import errno
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
TOKEN = os.environ["DOCUMENT_API_TOKEN"]
BOUNDARY = "portfolio-synthetic-boundary"


def request(path, data=None, authenticated=True):
    headers = {}
    if authenticated:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if data is not None:
        headers["Content-Type"] = f"multipart/form-data; boundary={BOUNDARY}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def multipart(parts):
    body = bytearray()
    for field, filename, content in parts:
        body.extend(
            (
                f"--{BOUNDARY}\r\n"
                f'Content-Disposition: form-data; name="{field}"; '
                f'filename="{filename}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
        )
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{BOUNDARY}--\r\n".encode())
    return bytes(body)


assert os.getuid() == 10001, "Container must run as the configured non-root user"
for attempt in range(60):
    try:
        status, health = request("/health", authenticated=False)
        assert status == 200 and health["external_ai"] is False
        break
    except urllib.error.URLError:
        time.sleep(0.5)
else:
    raise AssertionError("Container API did not start")

probe = Path("/app/should-not-be-writable")
try:
    probe.write_text("synthetic probe")
except OSError as error:
    assert error.errno == errno.EROFS, error
else:
    probe.unlink()
    raise AssertionError("Root filesystem unexpectedly writable")

invoice = b"Invoice: DEMO-CONTAINER\nDate: 2026-01-01\nTotal: USD 42.50\nDEMO ONLY"
body = multipart([("file", "invoice.txt", invoice)])
assert request("/v1/extract", body, authenticated=False)[0] == 401
status, result = request("/v1/extract", body)
assert status == 200, result
assert result["extraction"]["fields"]["invoice_id"] == "DEMO-CONTAINER"
assert result["extraction"]["fields"]["total"] == "42.50"
status, result = request(
    "/v1/batch",
    multipart([("files", "good.txt", invoice), ("files", "bad.exe", b"demo")]),
)
assert status == 207, result
assert [item["status"] for item in result["results"]] == ["ok", "error"]
print("PASS: non-root read-only container, auth, real TXT conversion and partial batch")
