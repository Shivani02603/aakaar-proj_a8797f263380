from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database.models import Document, User
from database.config import get_db
from backend.services.document_management_service import (
    create_document,
    get_documents,
    delete_document_by_id,
)
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(tags=["Document Management"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Pydantic Schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int
    status: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    created_at: str
    processed_at: Optional[str]


# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


# Routes
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF document.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_size = len(await file.read())
    document = create_document(
        db=db,
        user_id=user.id,
        filename=file.filename,
        file_size=file_size,
        status="uploaded",
    )
    return document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all documents for the authenticated user.
    """
    documents = get_documents(db=db, user_id=user.id)
    return documents


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_by_id(db=db, document_id=document_id)
    return {"detail": "Document deleted successfully"}