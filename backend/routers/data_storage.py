from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(tags=["Data Storage"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Pydantic schemas
class DocumentChunkBase(BaseModel):
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: Optional[dict] = None


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[dict] = None


class DocumentChunkResponse(DocumentChunkBase):
    id: UUID

    class Config:
        orm_mode = True


# Dependency for JWT authentication
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Placeholder for actual JWT validation logic
    # Replace with your authentication service logic
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return token


# Routes
@router.get("/", response_model=List[DocumentChunkResponse])
def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    chunks = db.query(DocumentChunk).all()
    return chunks


@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found",
        )
    return chunk


@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_chunk = DocumentChunk(**chunk.dict())
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk


@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found",
        )
    for key, value in chunk_update.dict(exclude_unset=True).items():
        setattr(db_chunk, key, value)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk


@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found",
        )
    db.delete(db_chunk)
    db.commit()