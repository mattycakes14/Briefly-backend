from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.routes import router as api_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SummarizeRequest(BaseModel):
    transcript: str


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

# takes transcription as input and returns summary
@app.post("/summarize")
def summarize(request: SummarizeRequest) -> dict[str, str]:
    logger.info(f"Summarizing request: {request}")
    return {"status": "ok"}

# Mount API routes under /api
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    # For local development convenience
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

