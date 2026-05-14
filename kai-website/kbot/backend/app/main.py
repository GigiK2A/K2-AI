"""FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import session, message, upload, report, checkout, generate_pdf, status, webhook
from .settings import CORS_ORIGINS

app = FastAPI(title="K2-AI K-BOT backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(session.router, prefix="/api/kbot", tags=["session"])
app.include_router(message.router, prefix="/api/kbot", tags=["message"])
app.include_router(upload.router, prefix="/api/kbot", tags=["upload"])
app.include_router(report.router, prefix="/api/kbot", tags=["report"])
app.include_router(checkout.router, prefix="/api/kbot", tags=["checkout"])
app.include_router(generate_pdf.router, prefix="/api/kbot", tags=["pdf"])
app.include_router(status.router, prefix="/api/kbot", tags=["status"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
