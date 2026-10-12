"""Munshi's own business plan inputs, built from MEASURED usage (runs/evidence/close-v2/run.json).

Outputs:
  evidence/business-plan/business_plan_inputs.csv   month-by-month model (18 months, two scenarios)
  evidence/business-plan/business_plan.md           the plan in plain words, with every assumption visible

Model prices are public list prices per million tokens (USD), stated as assumptions; the neatlogs
dashboard shows the actual cost of each traced close.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/evidence/close-v2/run.json"
OUT = ROOT / "evidence/business-plan"

USD_INR = 84.0
PRICE_PER_M = {  # (input, output) USD per million tokens, list-price assumptions
    "nova-lite": (0.06, 0.24), "claude-haiku": (1.0, 5.0), "claude-sonnet-4.6": (3.0, 15.0),
}
PLANS = {"Solo": 999, "Business": 2999}
MIX = {"Solo": 0.7, "Business": 0.3}
SCENARIOS = {"Base": {"start": 20, "monthly_growth": 0.15}, "Growth": {"start": 40, "monthly_growth": 0.25}}
CRUSTDATA_INR_PER_CLOSE = 8.0       # ~2 lookups per close, cached across months
INFRA_INR_PER_CUSTOMER = 40.0       # hosting share
PAYMENT_FEE = 0.04                  # Dodo merchant-of-record fee assumption (share of revenue)
FIXED_MONTHLY_INR = {"founder stipends (2)": 120000, "tools & hosting base": 8000, "marketing": 25000}
STARTING_CASH_INR = 1500000
MONTHS = 18


def cost_per_close() -> tuple[float, dict]:
    run = json.loads(RUN.read_text(encoding="utf-8"))
    usd = 0.0
    detail = {}
    for model, u in run["llm_usage"].items():
        pin, pout = PRICE_PER_M.get(model, (3.0, 15.0))
        c = u["prompt"] / 1e6 * pin + u["completion"] / 1e6 * pout
        detail[model] = {**u, "usd": round(c, 4)}
        usd += c
    return usd * USD_INR, detail


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    llm_inr, detail = cost_per_close()
    # A real business has ~3x the demo's transactions; scale model cost per close accordingly.
    llm_inr_real = llm_inr * 3
    cogs_per_customer = llm_inr_real + CRUSTDATA_INR_PER_CLOSE + INFRA_INR_PER_CUSTOMER
    arpu = sum(PLANS[p] * MIX[p] for p in PLANS)
    rows = []
    summary = {}
    for name, sc in SCENARIOS.items():
        cash, customers, breakeven = STARTING_CASH_INR, sc["start"], None
        for month in range(1, MONTHS + 1):
            revenue = customers * arpu
            cogs = customers * cogs_per_customer + revenue * PAYMENT_FEE
            fixed = sum(FIXED_MONTHLY_INR.values())
            profit = revenue - cogs - fixed
            cash += profit
            if breakeven is None and profit >= 0:
                breakeven = month
            rows.append({"scenario": name, "month": month, "customers": round(customers),
                         "revenue_inr": round(revenue), "cogs_inr": round(cogs), "gross_margin": round((revenue - cogs) / revenue, 3),
                         "fixed_costs_inr": fixed, "operating_profit_inr": round(profit), "ending_cash_inr": round(cash)})
            customers *= 1 + sc["monthly_growth"]
        summary[name] = {"breakeven_month": breakeven, "month18_customers": rows[-1]["customers"],
                         "month18_cash": rows[-1]["ending_cash_inr"]}
    with open(OUT / "business_plan_inputs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    gm = (arpu - cogs_per_customer - arpu * PAYMENT_FEE) / arpu
    md = f"""# Munshi: business plan

**Built from measured usage**: the model tokens of the traced v2 evidence close (`runs/evidence/close-v2/run.json`),
priced at public list prices (assumption). The neatlogs dashboard shows the actual cost per traced close.

## Unit economics (per customer per month)
| Item | ₹ |
| --- | --- |
| LLM cost of the demo close (measured tokens × list price) | {llm_inr:,.2f} |
| LLM cost scaled ×3 for a real business month (assumption) | {llm_inr_real:,.2f} |
| Crustdata lookups (cached) | {CRUSTDATA_INR_PER_CLOSE:,.2f} |
| Infra share | {INFRA_INR_PER_CUSTOMER:,.2f} |
| **COGS per customer** | **{cogs_per_customer:,.2f}** |
| ARPU (70% Solo ₹999, 30% Business ₹2,999) | {arpu:,.2f} |
| Payment / merchant-of-record fee (Dodo, {PAYMENT_FEE:.0%}) | {arpu * PAYMENT_FEE:,.2f} |
| **Gross margin** | **{gm:.1%}** |

Model usage detail: `{json.dumps(detail)}`

## Pricing
Solo ₹999/month (1 business, 150 documents) · Business ₹2,999/month (600 documents, invoicing + collections) ·
₹5 per extra document (Dodo usage meter). Billed through Dodo Payments as merchant of record.

## Scenarios ({MONTHS} months, starting cash ₹{STARTING_CASH_INR:,})
Fixed costs ₹{sum(FIXED_MONTHLY_INR.values()):,}/month: {", ".join(f"{k} ₹{v:,}" for k, v in FIXED_MONTHLY_INR.items())}.
| Scenario | Start customers | Monthly growth | Break-even month | Customers at month {MONTHS} | Cash at month {MONTHS} |
| --- | --- | --- | --- | --- | --- |
""" + "\n".join(f"| {n} | {SCENARIOS[n]['start']} | {SCENARIOS[n]['monthly_growth']:.0%} | {s['breakeven_month']} | {s['month18_customers']:,} | ₹{s['month18_cash']:,} |"
                for n, s in summary.items()) + """

Full month-by-month table: `business_plan_inputs.csv`.
"""
    (OUT / "business_plan.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
