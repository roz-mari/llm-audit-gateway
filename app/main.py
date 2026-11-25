import time

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import llm
from app.db import Base, engine, get_db
from app.guard import redact
from app.models import ApiKey, RequestLog
from app.schemas import AskRequest, AskResponse, LogOut
from app.security import require_api_key

# TODO: use Alembic migrations instead
Base.metadata.create_all(engine)

app = FastAPI(title="LLM Audit Gateway")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    prompt, redactions = redact(body.question)
    log = RequestLog(api_key_id=api_key.id, prompt=prompt, redactions=redactions, status="ok")

    start = time.perf_counter()
    try:
        result = llm.ask(prompt)
    except Exception:
        log.status = "error"
        raise HTTPException(status_code=502, detail="LLM provider error")
    else:
        log.answer = result["answer"]
        log.tools_used = result["tools_used"]
        log.total_tokens = result["total_tokens"]
    finally:
        # the log is saved even when the provider fails
        log.latency_ms = int((time.perf_counter() - start) * 1000)
        db.add(log)
        db.commit()

    return AskResponse(answer=log.answer, tools_used=log.tools_used, redactions=redactions)


@app.get("/v1/logs", response_model=list[LogOut])
def get_logs(
    limit: int = 20,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    # each client can only see its own logs
    query = (
        select(RequestLog)
        .where(RequestLog.api_key_id == api_key.id)
        .order_by(RequestLog.id.desc())
        .limit(min(limit, 100))
    )
    return db.scalars(query).all()
