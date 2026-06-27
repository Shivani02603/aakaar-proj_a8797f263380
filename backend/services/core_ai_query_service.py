import uuid
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, ChatMessage, ChatSession
from database.config import get_db
from openai import OpenAI
from pydantic import BaseModel


class CoreAIQueryService:
    def __init__(self, db: Session):
        self.db = db

    def create_chat_session(self, user_id: uuid.UUID, document_id: uuid.UUID, title: str) -> ChatSession:
        try:
            new_session = ChatSession(
                id=uuid.uuid4(),
                user_id=user_id,
                document_id=document_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(new_session)
            self.db.commit()
            self.db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create chat session") from e

    def get_chat_session_by_id(self, session_id: uuid.UUID) -> ChatSession:
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session

    def list_chat_sessions(self, user_id: uuid.UUID) -> List[ChatSession]:
        sessions = self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
        return sessions

    def delete_chat_session(self, session_id: uuid.UUID) -> None:
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        try:
            self.db.delete(session)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete chat session") from e

    def query_ai(self, user_query: str, document_id: uuid.UUID) -> Dict[str, Any]:
        try:
            # Retrieve top-5 most relevant chunks based on embeddings
            chunks = (
                self.db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.embedding.distance(user_query))  # Assuming distance method exists
                .limit(5)
                .all()
            )

            if not chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found")

            # Prepare content for LLM query
            context = "\n\n".join([chunk.content for chunk in chunks])
            citations = [{"chunk_index": chunk.chunk_index, "content": chunk.content} for chunk in chunks]

            # Query the LLM (e.g., GPT-4 or Gemini 2.0 Flash)
            llm = OpenAI()  # Replace with actual LLM initialization
            response = llm.generate_answer(prompt=f"Context:\n{context}\n\nQuestion:\n{user_query}")

            return {
                "answer": response,
                "citations": citations
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Failed to query AI") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail="An error occurred while querying AI") from e