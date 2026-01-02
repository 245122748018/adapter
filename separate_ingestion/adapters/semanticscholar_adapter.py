import os
import datetime as dt
from typing import List, Optional
from separate_ingestion.adapters.base import BaseAdapter, Change
from separate_ingestion.utils import http_get

BASE = "https://api.semanticscholar.org/graph/v1/paper/"
FIELDS = "title,year,venue,externalIds,url,authors,referenceCount,citationCount"

class SemanticScholarAdapter(BaseAdapter):
    name = "semantic_scholar"

    def __init__(self, paper_ids: List[str]):
        self.paper_ids = paper_ids

    def fetch_changes(self, since: Optional[dt.datetime]) -> List[Change]:
        changes: List[Change] = []
        headers = {}
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key
        for pid in self.paper_ids:
            url = f"{BASE}{pid}"
            item = http_get(url, params={"fields": FIELDS}, headers=headers).json()
            title = item.get("title")
            year = item.get("year")
            venue = item.get("venue")
            url2 = item.get("url")
            exids = item.get("externalIds", {})
            doi = exids.get("DOI")
            payload = {
                "title": title,
                "abstract": None,
                "venue": venue,
                "year": year,
                "doi": doi,
                "url": url2,
                "source": "semantic_scholar",
                "external_id": item.get("paperId"),
            }
            changes.append(Change(entity="publication", action="update", payload=payload))
        return changes
