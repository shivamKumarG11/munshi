# 13: Risks, mitigations and decisions needed

## Risks
| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | **Scope too big for 40 h** | High | High | Strict MUST/SHOULD/COULD ([10](10-build-plan.md)); the core (read → categorise → match → balance → brief) first |
| 2 | **DocILE needs registration / slow access** | Medium | Medium | SROIE/CORD (open) + team's real SaaS invoices |
| 3 | **cfo.ai MCP auth from our backend** (OAuth in the browser) | Medium | Medium | Core path is CSV upload (documented as first-class); MCP sync is a stretch |
| 4 | **`entire-agent-munshi` takes too long** | Medium | Low | It's a COULD; fallback audit trail = Git + trace links + transcripts ([04](04-books-as-code.md)) |
| 5 | **$20 model budget runs out** | Medium | High | Cheap-first routing; cache reads; test on a 20-transaction subset before full runs |
| 6 | **Vision extraction quality on photos** | Medium | Medium | Re-read with Sonnet on failed checks; ask the owner; keep photo traps few |
| 7 | **Dodo webhooks can't reach local machine** | Medium | Low | EC2 deploy, or poll the payments API |
| 8 | **AWS access link expires (24 h)** | Medium | Low | Reveal and save credentials early; ask on Discord for a fresh link |
| 9 | **Judges see "accounting software, done before"** | Low | Medium | Lead with the agent (closes the month by itself, balances to the rupee) and books-as-code; show the gap hunt |
| 10 | **Tax looks country-specific** | Low | Low | Generic engine (collected − paid, provision, claimable or not); India profile only for the demo's rupees |

## Decisions (resolved 2026-10-11)
| Decision | Answer |
| --- | --- |
| Name | **Munshi** |
| Team | **Solo** (+ Orchestrator parallel coding agents) |
| Data | **Public only**: real documents (DocILE/SROIE/CORD), real peer financials (EDGAR/Companies House), generated bank statement (labelled) |
| Integrations | cfo.ai feed, Entire ledger audit trail (stretch), Orchestrator, Dodo; **no Postgres**; every sponsor meaningfully |
| External review | Accepted in part, see [14](14-review-decisions.md) |

## Still open
1. **Demo business:** "Studio Kaveri" (Bengaluru design/dev agency), OK?
2. **UI:** Streamlit (recommended for solo) OK?

## Next step on approval
Scaffold the repo with Entire + neatlogs from the first commit, run the Phase 0 spikes, and report go/no-go on each.
