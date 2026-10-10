# 14: External review: what we accepted, what we didn't (2026-10-11)

An outside review (another AI agent) read v2. Each point was judged on its merits, not accepted automatically.

| # | Review point | Verdict | What changed |
| --- | --- | --- | --- |
| 1 | "Pick one story: cut the public-company portfolio" | **Partly agree** | The **hero story is now one business's month close**. But real large-business data was an explicit requirement, so it isn't cut; it moves **inside** the story: Munshi researches the business and benchmarks it against **real peers' filed financials** (EDGAR / Companies House). The full multi-company "review mode" becomes a stretch goal |
| 2 | "Shrink the demo to one reliable loop" | **Agree** | Core loop: bank CSV + documents → categorise → match → planted mismatch → gap hunt → verified balance, with an answer key |
| 3 | "Be precise: the bank statement is generated" | **Agree** (already labelled) | Stated even more plainly: real documents, generated bank statement, real peer financials. We never call it "a real business's close" |
| 4 | "Cut integrations that don't prove the core" | **Partly agree** | Required sponsors (neatlogs, Entire, cfo.ai plan) stay core. Others are **tiered**: cheap and meaningful ones (Crustdata lookup, Dodo payment link) are SHOULD; risky ones (Dodo webhooks, AWS hosting, cfo.ai MCP sync, `entire-agent-munshi`) are STRETCH with fallbacks. Postgres was already removed in v2 (the review read the v1 sponsor file) |
| 5 | "Rework the tax claims" | **Agree** | "What you owe in tax" becomes **"tax to set aside: an estimate from your configured assumptions"**, and the assumptions are shown on screen. No filing, no jurisdiction rules claimed |
| 6 | "Shorten the demo script" | **Agree** | Script rebuilt around the recovery moment; sponsors shown briefly with real evidence ([09](09-demo-script.md)) |

**New pitch:** *"Munshi is an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number."*
