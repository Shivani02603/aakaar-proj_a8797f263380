from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from ai.routes import process_query
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(tags=["Core AI / Query"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query to process")


class ChunkCitation(BaseModel):
    chunk_id: UUID = Field(..., description="ID of the document chunk")
    content: str = Field(..., description="Content of the chunk")
    metadata: dict = Field(..., description="Metadata associated with the chunk")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer to the query")
    citations: List[ChunkCitation] = Field(..., description="List of cited chunks")


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def ai_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Process a user query using AI and return the answer with citations.
    """
    try:
        # Process the query using the core AI query service
        answer, citations = await process_query(query_request.query, db)

        # Format the response
        response = QueryResponse(
            answer=answer,
            citations=[
                ChunkCitation(
                    chunk_id=citation["chunk_id"],
                    content=citation["content"],
                    metadata=citation["metadata"],
                )
                for citation in citations
            ],
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the query.",
        )