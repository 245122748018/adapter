import requests
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class HttpError(Exception):
    pass


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception_type((requests.exceptions.RequestException, HttpError)),
)

def http_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 20,
) -> requests.Response:
    resp = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
    if resp.status_code >= 400:
        raise HttpError(f"GET {url} failed: {resp.status_code} {resp.text[:200]}")
    return resp


def safe_get(d: Dict[str, Any], path: str, default=None):
    cur = d
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur
