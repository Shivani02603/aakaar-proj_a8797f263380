from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document, DocumentChunk
from database.config import get_db
from backend.services.document_processing_service import (
    extract_text_from_pdf,
    split_text_into_chunks,
    generate_embeddings,
)
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime

router = APIRouter(tags=["Document Processing"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class DocumentProcessingRequest(BaseModel):
    document_id: UUID


class DocumentProcessingResponse(BaseModel):
    document_id: UUID
    status: str
    processed_at: datetime


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict
    created_at: datetime


def get_current_user(token: str = Depends(oauth2_scheme)) -> UUID:
    # Mock implementation for user authentication
    # Replace with actual JWT decoding and user validation logic
    try:
        user_id = UUID(token)  # Assuming token is the user_id for simplicity
        return user_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


@router.post("/process", response_model=DocumentProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    # Fetch the document
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized to process this document")

    # Extract text from the document
    try:
        extracted_text = extract_text_from_pdf(document.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

    # Split text into chunks
    try:
        chunks = split_text_into_chunks(extracted_text, chunk_size=1000, overlap=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error splitting text into chunks: {str(e)}")

    # Generate embeddings for each chunk
    try:
        for index, chunk in enumerate(chunks):
            embedding = generate_embeddings(chunk)
            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                metadata={},
                created_at=datetime.utcnow(),
            )
            db.add(document_chunk)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

    # Update document status
    document.status = "processed"
    document.processed_at = datetime.utcnow()
    db.commit()

    return DocumentProcessingResponse(
        document_id=document.id,
        status=document.status,
        processed_at=document.processed_at,
    )


@router.get("/chunks/{document_id}", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    # Fetch the document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized to access this document")

    # Fetch chunks
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    return [
        DocumentChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            created_at=chunk.created_at,
        )
        for chunk in chunks
    ]