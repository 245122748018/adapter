from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import datetime as dt


@dataclass
class Change:
    entity: str  # "publication" | "document"
    action: str  # "insert" | "update"
    payload: Dict[str, Any]


class BaseAdapter:
    name: str

    def fetch_changes(self, since: Optional[dt.datetime]) -> List[Change]:
        raise NotImplementedError
