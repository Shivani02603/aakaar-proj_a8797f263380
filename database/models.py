import os
import uuid
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    TIMESTAMP,
    JSON,
    ARRAY,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL_ENV = "DATABASE_URL"
Base = declarative_base()

# Database engine and session setup
engine = create_engine(
    os.environ[DATABASE_URL_ENV],
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)

    documents = relationship("Document", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

# Document model
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    processed_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="documents")
    document_chunks = relationship("DocumentChunk", back_populates="document")
    chat_sessions = relationship("ChatSession", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"

# DocumentChunk model
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)

    document = relationship("Document", back_populates="document_chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, chunk_index={self.chunk_index})>"

# ChatSession model
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessage", back_populates="chat_session")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"

# ChatMessage model
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    chunk_ids = Column(ARRAY(String), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)

    chat_session = relationship("ChatSession", back_populates="chat_messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>"