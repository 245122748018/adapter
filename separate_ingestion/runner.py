import datetime as dt
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from separate_ingestion.adapters.base import BaseAdapter, Change
from separate_ingestion.pipeline import upsert_publication, index_document


def run_adapter(db: Session, adapter: BaseAdapter, since: Optional[dt.datetime] = None) -> Dict[str, Any]:
    started = dt.datetime.utcnow()
    stats = {"new": 0, "updated": 0, "documents_indexed": 0, "errors": 0}
    changes: List[Change] = []
    error_msg = None
    try:
        changes = adapter.fetch_changes(since)
        for ch in changes:
            if ch.entity == "publication":
                pub_id = upsert_publication(db, ch.payload)
                if pub_id:
                    if ch.action == "insert":
                        stats["new"] += 1
                    else:
                        stats["updated"] += 1
            elif ch.entity == "document":
                # Try to link to publication by arXiv ID if available
                pub_id = None
                ref = ch.payload.get("source_ref")
                if ch.payload.get("source") == "arxiv" and ref:
                    row = db.execute(text("SELECT id FROM publications WHERE arxiv_id = :aid"), {"aid": ref}).mappings().first()
                    if row:
                        pub_id = row["id"]
                index_document(db, ch.payload, pub_id)
                stats["documents_indexed"] += 1
        status = "success"
    except Exception as e:
        status = "failure"
        error_msg = str(e)[:1000]
        stats["errors"] += 1

    finished = dt.datetime.utcnow()
    db.execute(
        text(
            """
        INSERT INTO ingestion_runs (source_name, started_at, finished_at, status, stats, error)
        VALUES (:source_name, :started_at, :finished_at, :status, :stats, :error)
    """
        ),
        {
            "source_name": getattr(adapter, "name", "unknown"),
            "started_at": started,
            "finished_at": finished,
            "status": status,
            "stats": stats,
            "error": error_msg,
        },
    )
    return {"status": status, "stats": stats, "error": error_msg, "count": len(changes)}
