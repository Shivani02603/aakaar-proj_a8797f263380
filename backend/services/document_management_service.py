import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database.models import Document, User
from database.config import get_db


class DocumentManagementService:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, user_id: uuid.UUID, filename: str, file_size: int, status: str = "pending") -> Document:
        """
        Create a new document entry in the database.
        """
        new_document = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            status=status,
            created_at=datetime.utcnow(),
            processed_at=None
        )
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)
        return new_document

    def get_document_by_id(self, document_id: uuid.UUID) -> Document:
        """
        Retrieve a document by its ID.
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    def list_documents(self, user_id: uuid.UUID) -> List[Document]:
        """
        List all documents for a specific user.
        """
        documents = self.db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document_status(self, document_id: uuid.UUID, status: str) -> Document:
        """
        Update the status of a document.
        """
        document = self.get_document_by_id(document_id)
        document.status = status
        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: uuid.UUID) -> None:
        """
        Delete a document by its ID.
        """
        document = self.get_document_by_id(document_id)
        self.db.delete(document)
        self.db.commit()

# Standalone functions for dependency injection or direct usage
def create_document(db: Session, user_id: uuid.UUID, filename: str, file_size: int, status: str = "pending") -> Document:
    service = DocumentManagementService(db)
    return service.create_document(user_id, filename, file_size, status)

def get_document_by_id(db: Session, document_id: uuid.UUID) -> Document:
    service = DocumentManagementService(db)
    return service.get_document_by_id(document_id)

def list_documents(db: Session, user_id: uuid.UUID) -> List[Document]:
    service = DocumentManagementService(db)
    return service.list_documents(user_id)

def update_document_status(db: Session, document_id: uuid.UUID, status: str) -> Document:
    service = DocumentManagementService(db)
    return service.update_document_status(document_id, status)

def delete_document(db: Session, document_id: uuid.UUID) -> None:
    service = DocumentManagementService(db)
    service.delete_document(document_id)