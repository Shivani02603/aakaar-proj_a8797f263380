import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database.models import Document, DocumentChunk
from database.config import get_db
from openai import OpenAI
from pydantic import BaseModel

# Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"

class DocumentProcessingService:
    def __init__(self, db: Session):
        self.db = db

    def create_document_chunk(self, document_id: uuid.UUID, chunk_index: int, content: str, embedding: List[float], metadata: dict) -> DocumentChunk:
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            metadata=metadata,
            created_at=datetime.utcnow()
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def get_document_chunk_by_id(self, chunk_id: uuid.UUID) -> DocumentChunk:
        chunk = self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found")
        return chunk

    def list_document_chunks(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        return chunks

    def update_document_chunk(self, chunk_id: uuid.UUID, content: Optional[str] = None, embedding: Optional[List[float]] = None, metadata: Optional[dict] = None) -> DocumentChunk:
        chunk = self.get_document_chunk_by_id(chunk_id)
        if content:
            chunk.content = content
        if embedding:
            chunk.embedding = embedding
        if metadata:
            chunk.metadata = metadata
        chunk.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def delete_document_chunk(self, chunk_id: uuid.UUID) -> None:
        chunk = self.get_document_chunk_by_id(chunk_id)
        self.db.delete(chunk)
        self.db.commit()

    def process_document(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Extract text from the document (assuming a function extract_text_from_pdf exists)
        text = self.extract_text_from_pdf(document.filename)

        # Split text into chunks
        chunks = self.split_text_into_chunks(text)

        # Generate embeddings and save chunks
        processed_chunks = []
        for index, chunk in enumerate(chunks):
            embedding = self.generate_embedding(chunk)
            metadata = {"source": document.filename, "chunk_index": index}
            processed_chunk = self.create_document_chunk(document_id, index, chunk, embedding, metadata)
            processed_chunks.append(processed_chunk)

        # Update document status
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)

        return processed_chunks

    def extract_text_from_pdf(self, filename: str) -> str:
        # Placeholder for PDF text extraction logic
        # Replace with actual implementation
        raise NotImplementedError("PDF text extraction logic not implemented")

    def split_text_into_chunks(self, text: str) -> List[str]:
        tokens = text.split()
        chunks = []
        for i in range(0, len(tokens), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = tokens[i:i + CHUNK_SIZE]
            chunks.append(" ".join(chunk))
        return chunks

    def generate_embedding(self, text: str) -> List[float]:
        try:
            response = OpenAI().embedding(text, model=EMBEDDING_MODEL)
            return response["data"]["embedding"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")