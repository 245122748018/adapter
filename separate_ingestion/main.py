from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from separate_ingestion.db import get_db, engine
from separate_ingestion.models import Base
from separate_ingestion.runner import run_adapter
from separate_ingestion.adapters.orcid_adapter import OrcidAdapter
from separate_ingestion.adapters.arxiv_adapter import ArxivAdapter
from separate_ingestion.adapters.crossref_adapter import CrossrefAdapter
from separate_ingestion.adapters.semanticscholar_adapter import SemanticScholarAdapter

app = FastAPI(title="Separate Ingestion Test Service")
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/publications")
def list_publications(db: Session = Depends(get_db)):
    rows = db.execute(text(
        """
        SELECT id, title, venue, year, doi, arxiv_id, url, source, external_id
        FROM publications
        ORDER BY year DESC, title
        """
    )).mappings().all()
    return [dict(r) for r in rows]

@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    rows = db.execute(text(
        """
        SELECT d.id, d.publication_id, d.title, d.doc_type, d.source, d.source_ref, LENGTH(d.text_content) AS text_len
        FROM documents d
        ORDER BY d.id DESC
        """
    )).mappings().all()
    return [dict(r) for r in rows]

@app.get("/ingestion_runs")
def list_runs(db: Session = Depends(get_db)):
    rows = db.execute(text(
        """
        SELECT id, source_name, started_at, finished_at, status, stats, error
        FROM ingestion_runs
        ORDER BY id DESC
        """
    )).mappings().all()
    return [dict(r) for r in rows]

@app.post("/run/orcid")
def run_orcid(orcids: list[str] = Query(...), db: Session = Depends(get_db)):
    adapter = OrcidAdapter(orcids)
    result = run_adapter(db, adapter, since=None)
    return result

@app.post("/run/arxiv")
def run_arxiv(authors: list[str] = Query(...), max_results: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    adapter = ArxivAdapter(authors, max_results=max_results)
    result = run_adapter(db, adapter, since=None)
    return result

@app.post("/run/crossref")
def run_crossref(dois: list[str] = Query(...), db: Session = Depends(get_db)):
    adapter = CrossrefAdapter(dois)
    result = run_adapter(db, adapter, since=None)
    return result

@app.post("/run/semantic_scholar")
def run_semantic_scholar(paper_ids: list[str] = Query(...), db: Session = Depends(get_db)):
    adapter = SemanticScholarAdapter(paper_ids)
    result = run_adapter(db, adapter, since=None)
    return result