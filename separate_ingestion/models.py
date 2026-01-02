from sqlalchemy import Column, Integer, Text, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from separate_ingestion.db import Base


class Publication(Base):
    __tablename__ = "publications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
    abstract = Column(Text)
    venue = Column(Text)
    year = Column(Integer)
    doi = Column(Text)
    arxiv_id = Column(Text)
    url = Column(Text)
    pdf_url = Column(Text)
    source = Column(Text)  # orcid/arxiv/crossref/semantic_scholar
    external_id = Column(Text)  # source-specific ID
    faculty_orcid = Column(Text)  # optional linkage for tests
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

    documents = relationship("Document", back_populates="publication")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey("publications.id"))
    title = Column(Text)
    text_content = Column(Text)
    doc_type = Column(Text)  # e.g., preprint, publication_pdf
    source = Column(Text)  # arxiv/orcid/etc
    source_ref = Column(Text)  # e.g., arXiv ID or DOI
    language = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    publication = relationship("Publication", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    chunk_text = Column(Text)

    document = relationship("Document", back_populates="chunks")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    finished_at = Column(TIMESTAMP)
    status = Column(Text)  # success/failure
    stats = Column(JSON)  # {"new":..., "updated":..., "documents_indexed":..., "errors":...}
    error = Column(Text)
