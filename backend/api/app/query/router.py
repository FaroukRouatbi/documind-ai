from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import get_contextvars

from app.core.config import API_V1_PREFIX
from app.core.database import get_tenant_db
from app.core.security import get_current_user
from app.documents.repository import DocumentRepository
from app.generation.prompts import NO_ANSWER_RESPONSE
from app.generation.service import GenerationService
from app.query.dependencies import get_generation_service, get_retrieval_service
from app.query.schemas import Citation, QueryRequest, QueryResponse
from app.retrieval.service import RetrievalService

router = APIRouter(prefix=API_V1_PREFIX, tags=["query"])


@router.post("/query", response_model=QueryResponse, summary="Ask a question about your documents")
async def query_documents(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    retrieval: RetrievalService = Depends(get_retrieval_service),
    generation: GenerationService = Depends(get_generation_service),
    session: AsyncSession = Depends(get_tenant_db),
) -> QueryResponse:
    """
    Answers a question using only the authenticated tenant's documents.
    Retrieval and generation are tenant-scoped via row-level security.
    """
    chunks = await retrieval.retrieve(request.query, k=request.k)

    if not chunks:
        return QueryResponse(
            query_id=get_contextvars().get("correlation_id", ""),
            answer=NO_ANSWER_RESPONSE,
            citations=[],
            truncated=False,
            blocked=False,
        )

    answer = await generation.generate_answer(request.query, chunks)

    cited_ids = set(answer.citations)
    cited_chunks = [c for c in chunks if c.id in cited_ids]

    doc_repo = DocumentRepository(session)
    documents = await doc_repo.get_by_ids([c.document_id for c in cited_chunks])
    filenames = {d.id: d.filename for d in documents}

    citations = [
        Citation(
            chunk_id=c.id,
            document_id=c.document_id,
            filename=filenames[c.document_id],
            heading_path=c.heading_path,
            content=c.content,
        )
        for c in cited_chunks
        if c.document_id in filenames
    ]

    return QueryResponse(
        query_id=get_contextvars().get("correlation_id", ""),
        answer=answer.text,
        citations=citations,
        truncated=answer.stop_reason == "max_tokens",
        blocked=answer.guardrail_intervened,
    )
