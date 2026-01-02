from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from separate_ingestion.models import Publication, Document, DocumentChunk


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = max(0, end - overlap)
    return chunks


def upsert_publication(db: Session, pub: Dict[str, Any]) -> int | None:
    """
    Upsert publication:
    - Prefer DOI if present
    - Else use (source, external_id)
    """
    doi = pub.get("doi")
    source = pub.get("source")
    external_id = pub.get("external_id")

    row = None
    if doi:
        row = db.execute(text("SELECT id FROM publications WHERE doi = :doi"), {"doi": doi}).mappings().first()
    if not row and source and external_id:
        row = db.execute(
            text("SELECT id FROM publications WHERE source = :source AND external_id = :external_id"),
            {"source": source, "external_id": external_id},
        ).mappings().first()

    if row:
        pub_id = row["id"]
        db.execute(
            text(
                """
            UPDATE publications SET
              title = COALESCE(:title, title),
              abstract = COALESCE(:abstract, abstract),
              venue = COALESCE(:venue, venue),
              year = COALESCE(:year, year),
              doi = COALESCE(:doi, doi),
              arxiv_id = COALESCE(:arxiv_id, arxiv_id),
              url = COALESCE(:url, url),
              pdf_url = COALESCE(:pdf_url, pdf_url),
              source = COALESCE(:source, source),
              external_id = COALESCE(:external_id, external_id),
              updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """
            ),
            {"id": pub_id, **pub},
        )
        return pub_id
    else:
        db.execute(
            text(
                """
            INSERT INTO publications (title, abstract, venue, year, doi, arxiv_id, url, pdf_url, source, external_id, faculty_orcid, created_at, updated_at)
            VALUES (:title, :abstract, :venue, :year, :doi, :arxiv_id, :url, :pdf_url, :source, :external_id, :faculty_orcid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
            ),
            pub,
        )
        new_id = db.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()["id"]
        return new_id


def index_document(db: Session, doc: Dict[str, Any], publication_id: int | None):
    db.execute(
        text(
            """
        INSERT INTO documents (publication_id, title, text_content, doc_type, source, source_ref, language, created_at)
        VALUES (:publication_id, :title, :text_content, :doc_type, :source, :source_ref, :language, CURRENT_TIMESTAMP)
    """
        ),
        {
            "publication_id": publication_id,
            "title": doc.get("title"),
            "text_content": doc.get("text_content") or "",
            "doc_type": doc.get("doc_type"),
            "source": doc.get("source"),
            "source_ref": doc.get("source_ref"),
            "language": doc.get("language") or "en",
        },
    )
    doc_id = db.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()["id"]

    # Chunk and store (no vector embeddings in this separate test)
    for idx, ch in enumerate(chunk_text(doc.get("text_content") or "")):
        db.execute(
            text(
                """
            INSERT INTO document_chunks (document_id, chunk_index, chunk_text)
            VALUES (:document_id, :chunk_index, :chunk_text)
        """
            ),
            {"document_id": doc_id, "chunk_index": idx, "chunk_text": ch},
        )
    return doc_id
