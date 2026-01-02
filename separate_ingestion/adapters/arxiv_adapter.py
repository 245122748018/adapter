import datetime as dt
from typing import List, Optional
from xml.etree import ElementTree as ET
from separate_ingestion.adapters.base import BaseAdapter, Change
from separate_ingestion.utils import http_get

ARXIV_API = "http://export.arxiv.org/api/query"

def parse_arxiv_feed(xml_text: str):
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("atom:entry", ns):
        id_text = entry.find("atom:id", ns).text
        title = entry.find("atom:title", ns).text
        summary = entry.find("atom:summary", ns).text
        links = entry.findall("atom:link", ns)
        pdf_url = None
        for l in links:
            if l.attrib.get("type") == "application/pdf":
                pdf_url = l.attrib.get("href")
        year = None
        published = entry.find("atom:published", ns).text
        if published:
            year = int(published[:4])
        arxiv_id = id_text.split("/")[-1]
        entries.append({"arxiv_id": arxiv_id, "title": title, "summary": summary, "pdf_url": pdf_url, "year": year})
    return entries

class ArxivAdapter(BaseAdapter):
    name = "arxiv"

    def __init__(self, query_authors: List[str], max_results: int = 25):
        self.query_authors = query_authors
        self.max_results = max_results

    def fetch_changes(self, since: Optional[dt.datetime]) -> List[Change]:
        changes: List[Change] = []
        for author in self.query_authors:
            params = {"search_query": f'au:{author}', "start": 0, "max_results": self.max_results}
            xml = http_get(ARXIV_API, params=params).text
            entries = parse_arxiv_feed(xml)
            for e in entries:
                payload_pub = {
                    "title": e["title"],
                    "abstract": e["summary"],
                    "venue": "arXiv",
                    "year": e["year"],
                    "doi": None,
                    "arxiv_id": e["arxiv_id"],
                    "url": f"https://arxiv.org/abs/{e['arxiv_id']}",
                    "pdf_url": e["pdf_url"],
                    "source": "arxiv",
                    "external_id": e["arxiv_id"],
                }
                changes.append(Change(entity="publication", action="insert", payload=payload_pub))
                payload_doc = {
                    "doc_type": "preprint",
                    "source": "arxiv",
                    "source_ref": e["arxiv_id"],
                    "title": e["title"],
                    "text_content": e["summary"] or "",
                    "language": "en",
                    "metadata": {"title": e["title"], "doc_type": "preprint", "url": f"https://arxiv.org/abs/{e['arxiv_id']}"},
                }
                changes.append(Change(entity="document", action="insert", payload=payload_doc))
        return changes