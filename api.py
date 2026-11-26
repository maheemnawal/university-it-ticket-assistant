from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import service

app = FastAPI(title="Ticket Assistant")


class AnalyzeRequest(BaseModel):
    ticket: str
    prompt_version: Literal["v1", "v2"] = "v2"
    simulate_failure: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "mode": service.mode()}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        return service.analyze(req.ticket, req.prompt_version, req.simulate_failure)
    except service.EmptyTicket as e:
        raise HTTPException(400, str(e))
    except service.InvalidModelOutput as e:
        raise HTTPException(502, str(e))
    except service.BackendUnavailable as e:
        raise HTTPException(503, str(e))
