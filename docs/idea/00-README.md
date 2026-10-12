# Munshi: your business's personal CA (idea pack, for review)

> **Update (build): cfo.ai was dropped from the build (its signup requires a payment card). References to it below are from the original plan.**
>
> **Status:** DRAFT v3 FOR REVIEW · 2026-10-11 · nothing built yet · **solo build**
> **Hackathon:** neatHack ([../../hackathon.md](../../hackathon.md)) · submissions Mon Oct 12, 7:00–11:55 PM IST

## One line
**Munshi is an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.**

*Every business has a CA it can't afford to call every day; Munshi is the one you can.*

## What it does
Munshi works like a **CA firm with a portfolio of clients**, all of them **real businesses using public data**:

1. **Onboard + research:** for each new client, Munshi researches the business itself: what it does, how it makes money, its size, headcount and hiring, its peers (Crustdata, SEC EDGAR, Companies House, the company's own filings). From that it sets up the chart of accounts, a tax profile and "what normal looks like".
2. **Review the real numbers:** checks the business's filed financials hold together (every identity verified in code), works out the real tax picture, benchmarks against peers it picked itself, and flags what's unusual, then drafts the questions a CA would ask the owner.
3. **Close the month:** from a pile of documents and a bank statement: read, categorise, match, chase missing paperwork, invoice un-billed work (Dodo links), estimate tax, and only declare the month closed when **the books balance to the bank to the last rupee**.
4. **Brief + plan:** a morning brief per client, and verified actuals pushed into **cfo.ai**, so the owner's AI CFO plans on real numbers.

Every number is computed in code, cited to its source, and explainable: **books as code**, with an Entire audit trail.

## What changed in v2 (from your review)
| Decision | Effect |
| --- | --- |
| Name: **Munshi** | ✅ |
| **Solo** build | Build plan rewritten for one person + Orchestrator parallel coding agents ([10](10-build-plan.md)) |
| **Public data only; real, large and multiple businesses; the agent researches them** | Portfolio of 5–7 real companies (EDGAR + Companies House) + one month-close demo business ([06](06-data-plan.md)) |
| **cfo.ai feed + Entire ledger audit trail + Orchestrator + Dodo** | All in scope ([05](05-sponsors.md)) |
| **No Postgres** | cfo.ai fed by actuals **CSV upload** (core), **MCP server** (stretch); local state in files/SQLite |
| **External review (v3)** | Hero story = one month close; real peers' filings inside it; integrations tiered; tax = estimate with visible assumptions ([14](14-review-decisions.md)) |
| **Every sponsor to the fullest** | Each sponsor has a load-bearing role ([05](05-sponsors.md)) |

## Why this can win
| Criterion (weight) | Why Munshi scores |
| --- | --- |
| The agent (30%) | Research → review → close → act, across many real businesses; hard objective finish lines (identities hold; books balance); constant recovery |
| neatlogs + Entire + cfo.ai (25%) | Each is load-bearing: remove any one and a real user loses something ([05](05-sponsors.md)) |
| Demo (20%) | A real public company reviewed live + a messy month closed live (books off → gap hunt → ✅) |
| Building in public (15%) | Post plan in [11](11-building-in-public.md); Entire Dispatches → posts |
| Usefulness & originality (10%) | Every business needs a CA; **books as code** with an AI audit trail is new |

## The idea pack
| # | File | What's inside |
| --- | --- | --- |
| 01 | [01-problem-and-pitch.md](01-problem-and-pitch.md) | The problem in plain words, the pitch, who it's for |
| 02 | [02-product.md](02-product.md) | What the owner / CA sees; features; out of scope |
| 03 | [03-agent-design.md](03-agent-design.md) | Research, review and close loops; state, recovery, verification, model routing |
| 04 | [04-books-as-code.md](04-books-as-code.md) | Plain-text double-entry ledger in Git; every line explainable (Entire) |
| 05 | [05-sponsors.md](05-sponsors.md) | **Every sponsor used to the fullest, meaningfully** |
| 06 | [06-data-plan.md](06-data-plan.md) | Real public data: client portfolio, sources, traps, answer keys |
| 07 | [07-evaluation-and-evidence.md](07-evaluation-and-evidence.md) | Metrics, v1 → v2 experiment, judge evidence checklist |
| 08 | [08-business-model.md](08-business-model.md) | Customer, pricing, unit economics, go-to-market |
| 09 | [09-demo-script.md](09-demo-script.md) | The 3-minute video, shot by shot |
| 10 | [10-build-plan.md](10-build-plan.md) | Solo hour-by-hour plan with Orchestrator; cut lines |
| 11 | [11-building-in-public.md](11-building-in-public.md) | What to post, when |
| 12 | [12-tech-stack-and-repo.md](12-tech-stack-and-repo.md) | Stack, repo layout, environment variables |
| 13 | [13-risks-and-open-questions.md](13-risks-and-open-questions.md) | Risks, mitigations, remaining decisions |
| 14 | [14-review-decisions.md](14-review-decisions.md) | External review: what we accepted and why |

## Ground rule: meaningful, no matter what
> **"If we removed it, would a real business owner lose something?"** If not, it's decoration, and it gets cut.
