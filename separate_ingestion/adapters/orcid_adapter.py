import datetime as dt
from typing import List, Optional
from separate_ingestion.adapters.base import BaseAdapter, Change
from separate_ingestion.utils import http_get, safe_get

ORCID_WORKS_URL = "https://pub.orcid.org/v3.0/{orcid}/works"


class OrcidAdapter(BaseAdapter):
    name = "orcid"

    def __init__(self, orcids: List[str]):
        self.orcids = orcids

    def fetch_changes(self, since: Optional[dt.datetime]) -> List[Change]:
        changes: List[Change] = []
        for oid in self.orcids:
            url = ORCID_WORKS_URL.format(orcid=oid)
            resp = http_get(url, headers={"Accept": "application/json"}).json()
            group = safe_get(resp, "group", [])
            for g in group:
                work_summary = safe_get(g, "work-summary", [])
                for w in work_summary:
                    title = safe_get(w, "title.title.value")
                    year = safe_get(w, "publication-date.year.value")
                    ext_ids = safe_get(w, "external-ids.external-id", [])
                    doi = None
                    arxiv_id = None
                    url2 = safe_get(w, "url.value")
                    for eid in ext_ids:
                        if safe_get(eid, "external-id-type") == "doi":
                            doi = safe_get(eid, "external-id-value")
                        if safe_get(eid, "external-id-type") == "arxiv":
                            arxiv_id = safe_get(eid, "external-id-value")

                    payload = {
                        "faculty_orcid": oid,
                        "title": title,
                        "abstract": None,
                        "venue": safe_get(w, "journal-title.value"),
                        "year": int(year) if year else None,
                        "doi": doi,
                        "arxiv_id": arxiv_id,
                        "url": url2,
                        "pdf_url": None,
                        "source": "orcid",
                        "external_id": safe_get(w, "put-code"),
                    }
                    changes.append(Change(entity="publication", action="insert", payload=payload))
        return changes
