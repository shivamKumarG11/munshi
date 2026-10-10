"""Crustdata: resolve a cryptic payee to a real company (name, domain, industries, description).

Lookup order: by domain (precise) → by name (ambiguous; take the best match that has a description).
Every lookup is cached on disk: credits are finite and the same payee shows up every month.
"""

import json

import httpx

from munshi import tracing
from munshi.config import ROOT, settings

CACHE = ROOT / "state" / "crustdata_cache.json"
URL = "https://api.crustdata.com/company"


def _headers() -> dict:
    return {"authorization": f"Bearer {settings.crustdata_api_key}",
            "content-type": "application/json", "x-api-version": "2025-11-01"}


def _summary(company: dict) -> dict:
    data = company.get("company_data") or {}
    info = data.get("basic_info") or {}
    return {
        "name": info.get("name"),
        "domain": info.get("primary_domain"),
        "industries": info.get("industries") or [],
        "description": (info.get("description") or "")[:400],
        "employee_count_range": info.get("employee_count_range"),
        "confidence": company.get("confidence_score"),
        "crustdata_company_id": data.get("crustdata_company_id"),
    }


def _best(response: list) -> dict | None:
    candidates = [_summary(c) for m in response or [] for c in m.get("matches") or []]
    with_text = [c for c in candidates if c["description"]]
    return (with_text or candidates or [None])[0]


@tracing.span("TOOL", name="crustdata_resolve_company")
def resolve(name: str, domain: str | None = None) -> dict | None:
    key = f"{(domain or '').lower()}|{name.strip().lower()}"
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if key in cache:
        return cache[key]
    if not settings.crustdata_api_key:
        return None
    result = None
    if domain:
        r = httpx.post(f"{URL}/enrich", headers=_headers(), json={"domains": [domain]}, timeout=40)
        if r.status_code == 200:
            result = _best(r.json())
    if result is None or not result["description"]:
        r = httpx.post(f"{URL}/identify", headers=_headers(), json={"names": [name]}, timeout=40)
        if r.status_code == 200:
            result = _best(r.json()) or result
    if result:
        result["query"] = {"name": name, "domain": domain}
    cache[key] = result
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return result
