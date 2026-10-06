"""HTTP routes only. The physics lives in app.pipeline."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.models import QCSERequest, QCSEResponse
from app.pipeline import ConfinementError, compute_qcse

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
VENDOR_DIR = Path(os.environ.get("VENDOR_DIR", "/opt/vendor"))

app = FastAPI(
    title="Quantum-confined Stark effect",
    description="Energy levels and wavefunctions of a 1D finite well in a uniform field.",
    version="0.1.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Turn FastAPI's structured validation errors into one plain message."""
    parts = []
    for error in exc.errors():
        field = ".".join(str(p) for p in error.get("loc", ()) if p != "body") or "request"
        parts.append(f"{field}: {error.get('msg', 'invalid value')}")
    return JSONResponse(status_code=422, content={"detail": "Invalid input. " + "; ".join(parts)})


@app.post("/api/qcse")
def qcse(request: QCSERequest) -> QCSEResponse:
    """Return the tilted potential and the lowest two confined states."""
    try:
        return compute_qcse(request)
    except ConfinementError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


app.mount("/vendor", StaticFiles(directory=VENDOR_DIR), name="vendor")
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
