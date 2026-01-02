import datetime as dt
from typing import List, Optional
from separate_ingestion.adapters.base import BaseAdapter, Change
from separate_ingestion.utils import http_get

CROSSREF_WORK_URL = "https://api.crossref.org/works/{doi}"

class CrossrefAdapter(BaseAdapter):
    name = "crossref"

    def __init__(self, dois: List[str]):
        self.dois = [d.strip() for d in dois if d]

    def fetch_changes(self, since: Optional[dt.datetime]) -> List[Change]:
        changes: List[Change] = []
        for doi in self.dois:
            url = CROSSREF_WORK_URL.format(doi=doi)
            data = http_get(url).json()
            message = data.get("message", {})
            title = (message.get("title") or [""])[0]
            abstract = message.get("abstract")
            venue = (message.get("container-title") or [""])[0]
            year = None
            issued = message.get("issued") or {}
            date_parts = issued.get("date-parts") or []
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
            url2 = message.get("URL")
            payload = {
                "title": title,
                "abstract": abstract,
                "venue": venue,
                "year": year,
                "doi": doi,
                "url": url2,
                "source": "crossref",
                "external_id": doi,
            }
            changes.append(Change(entity="publication", action="update", payload=payload))
        return changes
