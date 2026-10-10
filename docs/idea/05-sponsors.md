# 05: Every sponsor, used meaningfully

**The test for each one:** *if we removed it, what would a real user (or we, as the company) lose?* If the answer is "nothing", we don't do it.

Each section covers: **role in the product** → **exact features used** → **what breaks without it** → **evidence for judges** → **fallback**.

---

## 1. neatlogs (required): Munshi's quality control and cost meter
**Role:** a bookkeeper you can't check is worthless. neatlogs is how **we** know every close was correct, find out why it wasn't, and prove it got better. It is also where our **cost per customer** comes from.

| neatlogs feature | How Munshi uses it (meaningfully) |
| --- | --- |
| **Python SDK + `wrap()`** | Every LLM call (LiteLLM, OpenAI-compatible client) traced automatically |
| **Custom spans / span kinds (TOOL)** | Every tool step traced: bank parse, Crustdata lookup, ledger write, `bean-check`, Dodo call |
| **Sessions** | **One session = one month-close** for one business: the whole close as a replayable story |
| **Workflow names** | `read`, `categorise`, `match`, `gap_hunt`, `invoice`, `tax`, `brief` as separate workflows → per-stage cost and failure rates |
| **Tags** | `business_id`, `month`, `agent_version=v1/v2`, `model` → filter and compare versions |
| **End-user identity** | The business is the end user → **cost per customer per month**, the number our business plan needs |
| **PII redaction** | Financial documents carry names, account numbers, addresses → redact before they leave our process. A real need for a finance product |
| **Detections** | Rules that flag bad closes automatically, e.g. "posted without evidence", "balance gap after gap hunt", "category confidence < 0.6", "brief mentions a number not in the ledger" |
| **Evals (AI evaluators)** | A rubric judge scores categorisation reasoning ("does the cited evidence support this category?") on sampled traces |
| **Experiments / prompt templates** | Prompt versions for the categoriser and reader; v1 vs v2 compared on the same test month |
| **Investigate + Fixes** | When v1 fails, ask Neat AI *why* across many traces → root cause → fix |
| **Alerts** | Alert when a production close fails verification, so a human CA steps in |
| **MCP server** | Our coding agent (Claude Code) reads Munshi's traces and detections directly while we fix bugs |
| **Analytics API (cost / KPIs)** | Pull **real cost per close** → feeds Munshi's own **cfo.ai** business plan (the loop below) |

**Without it:** we'd ship an accountant we can't audit, couldn't price the product (unknown cost per customer), and couldn't prove any improvement.
**Evidence:** v1 vs v2 trace links with the numbers ([07](07-evaluation-and-evidence.md)); a trace where a step failed and recovery happened (gap hunt); detections firing; cost-per-close chart.
**Fallback:** none needed. SDK + sessions + tags are low-risk; Detections/Evals are configured in the dashboard.

---

## 2. Entire (required): an audit trail for the code *and* for the books
**Role, twice over:**
1. **How we build Munshi:** every commit carries the AI session that produced it.
2. **Inside the product:** the books-as-code audit trail ([04](04-books-as-code.md)).

| Entire feature | Use |
| --- | --- |
| **Checkpoints (Claude Code integration)** | Every commit in the Munshi repo links to the coding session: prompt, transcript, tool calls, token usage |
| **entire-graph plugin** | Our coding agent navigates the codebase via the graph (faster, fewer tokens) as the repo grows across 7+ modules |
| **`entire why` / `entire blame`** | Explain why a piece of Munshi's code exists (show in the demo on the gap-hunt fix) |
| **Agent Integration Protocol → `entire-agent-munshi`** *(headline stretch)* | **Munshi's own sessions become checkpoints on the ledger repo** → `entire why ledger/2026-09.beancount:142` explains a bookkeeping entry |
| **Dispatches (`entire dispatch`)** | Turn recent agent work into a markdown update → our building-in-public posts |
| **`entire review`** | Multi-agent review of the branch before submission |
| **Mirror on entire.io** | Repo mirrored so judges can browse checkpoints on entire.io |

**Without it:** the fixes found via neatlogs would have no recorded "why"; the ledger audit trail (the product's trust story) would be weaker.
**Evidence:** checkpoint links on key commits (especially the v1→v2 fix); entire-graph output in `evidence/entire/`; `entire why` on a ledger line (if the integration lands).
**Fallback:** if `entire-agent-munshi` is too heavy, the ledger audit trail uses Git commits + neatlogs trace links + saved session transcripts (see [04](04-books-as-code.md)).

### The neatlogs ↔ Entire fix loop (show this in the demo)
```
neatlogs detection fires on v1 ("posted without evidence" ×14)
  → Investigate: root cause = categoriser ignores the document when payee is known
  → Claude Code reads the traces via neatlogs MCP, fixes the code
  → Entire checkpoint records that session on the fix commit
  → v2 run: detection count 14 → 0 (neatlogs)
```
That's "find the failure in neatlogs, fix it with your coding agent, verify with neatlogs", exactly the workflow both sponsors sell.

---

## 3. cfo.ai (required): where Munshi's books go to become a plan, and how we plan Munshi itself
**Role, twice over:**
1. **For our customers (product integration):** a CA keeps the books correct; a CFO plans with them. **Munshi's closed books flow into cfo.ai**, so Ari works from real, verified actuals instead of a stale spreadsheet. The owner's brief includes Ari's answer ("runway 9.5 months").
2. **For us (the required business plan):** Munshi's own pricing, costs, revenue and runway are modelled in cfo.ai, using **real cost per close from neatlogs**.

| cfo.ai capability (documented) | Use |
| --- | --- |
| **CSV / file upload** (documented as a first-class way in) | **CORE:** Munshi exports each closed month's actuals (P&L by account, cash) as a CSV → uploaded into the owner's cfo.ai workspace |
| **MCP server** (`https://api.cfo.ai/mcp`, tools like `inspect_table_blocks`, `edit_table_blocks`, `inspect_scenarios`) | **STRETCH:** Munshi writes actuals into the model directly and reads back runway for the brief. During the build, our coding agent uses the same MCP server to set up the business-plan model |
| **Scenarios** | Owner asks "what if I hire one more person?" → a cfo.ai scenario on top of Munshi's actuals |
| **Deterministic maths + lineage** | Same principle as Munshi ("the LLM never does the maths"), the shared philosophy we pitch |
| **Munshi's own model** | Pricing tiers, Dodo fees, LLM cost per close (neatlogs), AWS cost, customers, runway; scenarios: 50 / 500 / 5,000 businesses |

**Without it:** the owner gets correct books but no forward view; and we'd have no credible business plan.
**Evidence:** cfo.ai model screenshots/export in `evidence/cfo-ai/`; the brief showing the cfo.ai runway line; the plan showing cost per close sourced from neatlogs.
**Fallback:** the CSV path is the core and needs no auth from our backend; MCP is the upgrade. The business plan is built in the cfo.ai app either way. (No Postgres: removed in review.)
**Note:** sign up at cfo.ai/neathacks today; card required; **cancel the subscription immediately** (Settings → Billing).

---

## 4. Dodo Payments: getting the owner paid, and getting us paid
**Role, twice over:**
1. **Inside the agent:** when Munshi raises an invoice, it attaches a **Dodo payment link / checkout session**. When the client pays, the **Dodo webhook** fires and Munshi **posts the receipt to the ledger and marks the invoice paid automatically**. Collections and reconciliation close themselves.
2. **Our own billing:** Munshi is sold as a subscription with usage: **Meters + Usage Events** for "documents processed" (or **credit-based billing**: prepaid document credits). Dodo is the **merchant of record**, handling sales tax on *our* sales: fitting for a tax product.

| Dodo feature | Use |
| --- | --- |
| Checkout sessions / payment links | Pay button on every invoice Munshi drafts |
| Webhooks (payment succeeded/failed) | Auto-post receipts; trigger reminders on failure; **"the world changes while the agent works"** |
| Customers | Client records synced with Munshi's ledger parties |
| Meters + Usage Events / Credit entitlements | Bill Munshi customers per document processed |
| Subscriptions | Base plan per business |
| Test mode | Everything in the demo runs in Dodo test mode |

**Without it:** invoices would be PDFs with bank details and manual matching, and we'd have no way to charge for Munshi.
**Evidence:** a test-mode payment on a Munshi invoice → webhook → ledger entry appears (show live in the demo); meter usage for the demo business.
**Fallback:** if webhooks can't reach us, poll the payments API; the demo still shows the loop.

---

## 5. Crustdata: knowing who you paid
**Role:** bank narrations are cryptic (`RZP*ACMETECH 88213`, `NEFT-ZENITH SOLU`). Munshi resolves them to **real companies** to categorise correctly, and builds a vendor/client record (legal name, industry, location) that makes invoices go to the right legal entity.

| Crustdata API | Use |
| --- | --- |
| Company identify (name/domain → company) | Resolve the payee from a narration or invoice header |
| Company enrich | Industry/type → category hint (a SaaS vendor → Software; a co-working company → Rent) |
| Search/autocomplete | Fuzzy match on messy names |

**Without it:** more "who is this?" questions to the owner and more wrong categories.
**Evidence:** traces showing a Crustdata lookup turning an unknown payee into a correct category; accuracy with vs without lookup.
**Budget:** 5,000 credits; cache every lookup; only call for unknown payees.

---

## 6. AWS: where Munshi lives
**Tier: STRETCH** (build last). **Role:** a real product needs to be **always on**: to receive Dodo webhooks and to run scheduled closes.

| AWS piece (within the hackathon limits) | Use |
| --- | --- |
| **EC2** (t3.small, us-east-1, Hackathon_VPC, one instance) | Munshi API + Streamlit app + Dodo webhook endpoint |
| **Lambda** (optional) | Lightweight webhook receiver / scheduled daily close trigger |
| Load balancer (optional) | HTTPS endpoint for webhooks |

**Without it:** no webhooks (so payments are polled instead of pushed) and no scheduled close. The core demo runs locally.
**Limits to respect:** $25 total; one EC2 instance; EBS ≤ 50 GB; stop resources after the demo. **No Bedrock**: models go through LiteLLM.

---

## 7. LiteLLM key (Nova + Claude): the brains, on a budget
Model routing in [03-agent-design.md](03-agent-design.md): `nova-lite` → `claude-haiku` → `claude-sonnet-4.6` only on failure. The $20 budget forces exactly the cost discipline a real product needs, and neatlogs proves it.

---

## 8. Orchestrator.inc: how we build fast (optional, meaningful for us)
Run **parallel coding agents in isolated git worktrees** with `ao` (e.g. one on the reader, one on Dodo + webhooks, one on the Streamlit UI). Each agent's sessions are captured by **Entire** and its test runs traced by **neatlogs**. Real speed-up for a 40-hour build, not a logo.
**Skip if** setup costs more than an hour.

## 9. TheVibeFounder: the story
Munshi is the **back office for the one-person company**: the founder who ships with agents still has to do books, invoices and tax. Munshi is the agent for that. This is the narrative for posts and the demo intro.

---

## Summary: what breaks if we remove each one
| Remove… | …and the user loses |
| --- | --- |
| neatlogs | Trust (no audit of AI decisions), our pricing (unknown cost per customer), proof of improvement |
| Entire | The "why" behind every code change, and the books' audit trail |
| cfo.ai | The forward view (runway, scenarios) built on verified books, and our business plan |
| Dodo | Pay-by-link invoices, automatic reconciliation, our revenue |
| Crustdata | Correct categories for cryptic payees; correct legal entities on invoices |
| AWS | Webhooks, scheduled closes, the database cfo.ai reads |
| LiteLLM | The models (and the cost discipline) |
