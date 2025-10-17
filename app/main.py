from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, AliasChoices
import logging
from typing import Any, Dict, List, Optional
import asyncio
import time
from app.graph.meeting_prep_graph import build_meeting_prep_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SummarizeRequest(BaseModel):
    transcript: str = Field(validation_alias=AliasChoices("transcript", "trasncript"))


app = FastAPI(title="Briefly Backend", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# health check endpoint
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# ---- Inlined API endpoints (previously in app/api/routes.py) ----

class AgentRequest(BaseModel):
    goal: str
    inputs: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class StepResult(BaseModel):
    name: str
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    latencyMs: int


class AgentResponse(BaseModel):
    result: Any
    steps: List[StepResult]
    usage: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

# build state graph
graph_app = build_meeting_prep_graph()

@app.post("/summarize", response_model=AgentResponse)
async def summarize(req: SummarizeRequest) -> AgentResponse:
    start = time.perf_counter()
    state = {"transcript": req.transcript}
    try:
        # final state object
        result_state = await graph_app.ainvoke(state)

        # calaculate latency
        latency = int((time.perf_counter() - start) * 1000)

        # steps for diagnotics
        steps = [
            StepResult(name="graph_execute", ok=True, latencyMs=latency, data={"nodes": list(result_state.keys())})
        ]
        return AgentResponse(result={"summary": result_state.get("summary", ""), "classification": result_state.get("classification", {})}, steps=steps)
    except Exception as e:
        latency = int((time.perf_counter() - start) * 1000)
        logger.exception("Graph execution failed")
        steps = [StepResult(name="graph_execute", ok=False, latencyMs=latency, error=str(e))]
        return AgentResponse(result="", steps=steps, errors=[str(e)])


if __name__ == "__main__":
    # For local development convenience
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

