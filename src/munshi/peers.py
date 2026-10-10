"""Research step: real peer companies from SEC EDGAR filings, and their key ratios.

Every figure carries its source (CIK, XBRL concept, fiscal year, filing accession) so the brief can
cite it. Nothing here is estimated by an LLM.
"""

import json
import re
import statistics
import time
from decimal import Decimal

import httpx

from munshi import tracing
from munshi.config import ROOT, settings

CACHE = ROOT / "state" / "edgar"
REVENUE = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
           "RevenueFromContractWithCustomerIncludingAssessedTax"]
OPERATING = ["OperatingIncomeLoss"]
PRETAX = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]
TAX = ["IncomeTaxExpenseBenefit"]


def _get(url: str) -> httpx.Response:
    if not settings.sec_user_agent:
        raise RuntimeError("SEC_USER_AGENT missing in .env")
    time.sleep(0.15)  # stay well under SEC's 10 requests/second
    r = httpx.get(url, headers={"User-Agent": settings.sec_user_agent}, timeout=40)
    r.raise_for_status()
    return r


@tracing.span("TOOL", name="edgar_companies_by_industry")
def companies_by_sic(sic: str, limit: int = 40) -> list[dict]:
    feed = _get(f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC={sic}&type=10-K"
                f"&dateb=&owner=include&count={limit}&output=atom").text
    # The feed's name fields are unreliable; the official name comes from the company facts later.
    return [{"cik": c, "name": ""} for c in dict.fromkeys(re.findall(r"<cik>(\d+)</cik>", feed))]


def _latest_annual(facts: dict, concepts: list[str], min_fy: int) -> dict | None:
    for concept in concepts:
        units = facts.get("facts", {}).get("us-gaap", {}).get(concept, {}).get("units", {}).get("USD", [])
        annual = [u for u in units if u.get("form") == "10-K" and u.get("fp") == "FY"
                  and u.get("fy", 0) >= min_fy and u.get("start") and u.get("end")]
        # full-year periods only (start→end ≈ 1 year)
        annual = [u for u in annual if 330 <= _days(u["start"], u["end"]) <= 400]
        if annual:
            best = max(annual, key=lambda u: (u["end"], u.get("filed", "")))
            return {"value": Decimal(str(best["val"])), "concept": concept, "period_end": best["end"],
                    "fy": best["fy"], "accession": best.get("accn")}
    return None


def _days(start: str, end: str) -> int:
    from datetime import date
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


@tracing.span("TOOL", name="edgar_company_ratios")
def company_ratios(cik: str, name: str, min_fy: int = 2024) -> dict | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{cik}.json"
    if path.exists():
        facts = json.loads(path.read_text(encoding="utf-8"))
    else:
        try:
            facts = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json").json()
        except httpx.HTTPStatusError:
            return None
        path.write_text(json.dumps(facts), encoding="utf-8")
    rev = _latest_annual(facts, REVENUE, min_fy)
    op = _latest_annual(facts, OPERATING, min_fy)
    if not rev or not op or rev["value"] <= 0:
        return None
    pretax, tax = _latest_annual(facts, PRETAX, min_fy), _latest_annual(facts, TAX, min_fy)
    out = {"cik": cik, "name": facts.get("entityName", name), "revenue_usd": str(rev["value"]),
           "operating_margin": round(float(op["value"] / rev["value"]), 4),
           "sources": {"revenue": rev, "operating_income": op}}
    if pretax and tax and pretax["value"] > 0:
        out["effective_tax_rate"] = round(float(tax["value"] / pretax["value"]), 4)
        out["sources"].update({"pretax_income": pretax, "income_tax": tax})
    return json.loads(json.dumps(out, default=str))


@tracing.span("AGENT", name="research_peers")
def research(industry_sics: list[str], max_peers: int = 6) -> dict:
    """Find real filers in the business's industry, keep those with clean recent annual data."""
    peers = []
    for sic in industry_sics:
        for c in companies_by_sic(sic):
            if len(peers) >= max_peers:
                break
            ratios = company_ratios(c["cik"], c["name"])
            if ratios and -1 < ratios["operating_margin"] < 1:
                ratios["sic"] = sic
                peers.append(ratios)
    margins = [p["operating_margin"] for p in peers]
    taxes = [p["effective_tax_rate"] for p in peers if "effective_tax_rate" in p and 0 <= p["effective_tax_rate"] <= 0.6]
    return {
        "industry_sics": industry_sics,
        "peers": peers,
        "median_operating_margin": round(statistics.median(margins), 4) if margins else None,
        "median_effective_tax_rate": round(statistics.median(taxes), 4) if taxes else None,
        "source": "SEC EDGAR XBRL company facts (10-K, full fiscal years >= 2024)",
    }
