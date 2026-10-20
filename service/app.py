import asyncio
import hashlib
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse

MAX_FILE = 2 * 1024 * 1024
MAX_BATCH = 5
ALLOWED = {".txt", ".md", ".html", ".csv", ".json", ".pdf", ".docx", ".xlsx"}
slots = asyncio.Semaphore(2)
app = FastAPI(title="Document Intelligence", version="0.1.0")


@app.middleware("http")
async def upload_limits(request, call_next):
    if request.url.path in {"/v1/extract", "/v1/batch"}:
        try:
            length = int(request.headers.get("content-length", ""))
        except ValueError:
            return JSONResponse(
                {"detail": "Content-Length is required"}, status_code=411
            )
        if length < 0 or length > MAX_BATCH * MAX_FILE + 65536:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
    return await call_next(request)


def require_token(authorization: str = Header(default="")):
    expected = os.environ.get("DOCUMENT_API_TOKEN", "")
    if len(expected) < 16:
        raise HTTPException(
            503, "Configure a dedicated DOCUMENT_API_TOKEN of at least 16 characters"
        )
    if not secrets.compare_digest(
        authorization.encode(), f"Bearer {expected}".encode()
    ):
        raise HTTPException(401, "Invalid bearer token")


async def convert_upload(file: UploadFile) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(415, "Unsupported file extension")
    content = await file.read(MAX_FILE + 1)
    if not content:
        raise HTTPException(422, "Empty document")
    if len(content) > MAX_FILE:
        raise HTTPException(413, "Document exceeds 2 MiB")
    digest = hashlib.sha256(content).hexdigest()
    async with slots:
        with tempfile.TemporaryDirectory(prefix="document-convert-") as folder:
            path = Path(folder) / f"input{suffix}"
            path.write_bytes(content)
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "service.worker",
                str(path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=20)
            except TimeoutError as error:
                if process.returncode is None:
                    process.kill()
                await process.wait()
                raise HTTPException(504, "Conversion timed out") from error
            except BaseException:
                if process.returncode is None:
                    process.kill()
                await process.wait()
                raise
            if process.returncode != 0:
                raise HTTPException(422, "Document conversion failed")
            try:
                result = json.loads(stdout)
            except ValueError as error:
                raise HTTPException(422, "Invalid converter output") from error
    return {"sha256": digest, "size_bytes": len(content), **result}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-conversion", "external_ai": False}


@app.post("/v1/extract", dependencies=[Depends(require_token)])
async def extract(file: UploadFile = File(...)):
    try:
        return await convert_upload(file)
    finally:
        await file.close()


@app.post("/v1/batch", dependencies=[Depends(require_token)])
async def batch(files: list[UploadFile] = File(...)):
    try:
        if not 1 <= len(files) <= MAX_BATCH:
            raise HTTPException(400, "Batch must contain 1-5 documents")
        results = []
        for position, file in enumerate(files):
            try:
                results.append(
                    {
                        "position": position,
                        "status": "ok",
                        "result": await convert_upload(file),
                    }
                )
            except HTTPException as error:
                results.append(
                    {
                        "position": position,
                        "status": "error",
                        "code": error.status_code,
                        "error": error.detail,
                    }
                )
        return JSONResponse(
            {"results": results},
            status_code=207 if any(r["status"] == "error" for r in results) else 200,
        )
    finally:
        for file in files:
            await file.close()
