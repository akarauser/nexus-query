from typing import Literal

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from nexus_query.scripts.rag_system import RagSystem

app = FastAPI()
system = RagSystem()


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2)


@app.get("/")
def read_root() -> Literal["Hello World"]:
    return "Hello World"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/create_documents_add_vector_store")
def create_documents_add_vector_store(pdf_path: str):
    return system._create_documents_add_vector_store(pdf_path)


@app.get("/api/v1/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        system.chat(request.query), media_type="application/x-ndjson"
    )
