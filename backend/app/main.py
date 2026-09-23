import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, PyMongoError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from . import admin, assessment, auth, catalog, mixed
from .config import settings
from .db import SessionLocal
from .models import Attempt, AuthToken, RateBucket, Session


def sweep():
    with SessionLocal() as db:
        for attempt in db.scalars(select(Attempt).where(Attempt.status == "active", Attempt.expires_at <= time.time())):
            assessment.finish(db, attempt)
        for model in (Session, AuthToken, RateBucket):
            db.execute(delete(model).where(model.expires_at < time.time()))
        db.commit()


@asynccontextmanager
async def lifespan(app):
    if settings().database_url.startswith("mongodb"):
        from .mongo import ensure_indexes

        try:
            await asyncio.to_thread(ensure_indexes)
        except PyMongoError:
            raise RuntimeError("Atlas is unavailable. Check credentials and Network Access rules.") from None

    async def expire_loop():
        while True:
            try:
                await asyncio.to_thread(sweep)
            except PyMongoError as exc:
                logging.error("Atlas expiry sweep unavailable: %s", type(exc).__name__)
            except Exception:
                logging.exception("Attempt expiry sweep failed")
            await asyncio.sleep(15)

    task = asyncio.create_task(expire_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="PrepFaang API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security(request: Request, call_next):
    origin = request.headers.get("origin")
    unsafe = request.method not in ("GET", "HEAD", "OPTIONS")
    if unsafe and (
        (origin and origin != settings().frontend_origin) or request.headers.get("sec-fetch-site") == "cross-site"
    ):
        return JSONResponse({"error": {"code": 403, "message": "Untrusted request origin."}}, status_code=403)
    length = request.headers.get("content-length", "0")
    if not length.isdigit() or int(length) > 2100000:
        return JSONResponse({"error": {"code": 413, "message": "Request is too large."}}, status_code=413)
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin",
            "Cache-Control": "no-store",
        }
    )
    if settings().app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse(
        {"error": {"code": exc.status_code, "message": str(exc.detail)}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": 422,
                "message": "; ".join(f"{'.'.join(map(str, e['loc'][1:]))}: {e['msg']}" for e in exc.errors()),
            }
        },
        status_code=422,
    )


@app.exception_handler(IntegrityError)
@app.exception_handler(DuplicateKeyError)
async def conflict(request, exc):
    return JSONResponse(
        {"error": {"code": 409, "message": "This record already exists or conflicts with related data."}},
        status_code=409,
    )


@app.exception_handler(PyMongoError)
async def mongo_error(request, exc):
    # Driver errors can include connection details. Never return or log their text.
    conflict = exc.has_error_label("TransientTransactionError") or getattr(exc, "code", None) == 112
    return JSONResponse(
        {
            "error": {
                "code": 409 if conflict else 503,
                "message": "Another change is in progress. Please retry."
                if conflict
                else "Database unavailable. Please check the Atlas connection.",
            }
        },
        status_code=409 if conflict else 503,
    )


@app.exception_handler(Exception)
async def unexpected(request, exc):
    logging.error("Unhandled API error", exc_info=exc)
    return JSONResponse({"error": {"code": 500, "message": "Something went wrong. Please retry."}}, status_code=500)


for router in (auth.router, catalog.router, assessment.router, admin.router, mixed.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": settings().app_env}
