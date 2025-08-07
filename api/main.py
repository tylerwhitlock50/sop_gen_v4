from __future__ import annotations

from fastapi import FastAPI

from api.services.sop_service.conversation_builder import conversation_router


app = FastAPI(title="SOP Service API")
app.include_router(conversation_router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


