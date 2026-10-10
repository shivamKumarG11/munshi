# 07: Evaluation and evidence

## Metrics (computed by `eval/score.py` against the answer key)
| Metric | Meaning | Why judges care |
| --- | --- | --- |
| **Balances?** (yes/no + gap ₹) | Ledger closing balance == bank statement | The hard finish line |
| **Categorisation accuracy** | % of transactions in the correct account | Core quality |
| **Match accuracy** | % of bank lines linked to the correct document(s) | Core quality |
| **Evidence coverage** | % of posted entries citing a document, rule or owner answer | Trust / audit trail |
| **Unsupported posts** | Entries posted without evidence (should be 0) | Detected by a neatlogs Detection |
| **Traps caught** | Out of 12 planted traps ([06](06-data-plan.md)) | Recovery + verification |
| **Owner questions asked** | Fewer is better, but never at the cost of guessing | Usefulness |
| **Cost per close (₹/$)** | From neatlogs analytics | Business viability → cfo.ai plan |
| **Time per close** | From neatlogs | Usefulness |
| **Peer figures sourced** | % of peer numbers carrying filing id + concept + period (should be 100%) | No made-up benchmarks |
| **Brief faithfulness** | Every number in the brief exists in the ledger (checked in code) | No made-up numbers |

## The v1 → v2 experiment (the core before/after)
**v1 (naive):** one strong model reads everything and categorises everything; no deterministic checks between steps; the brief written straight from model output.

**Expected v1 failures** (to be confirmed by the real run; we don't invent numbers):
- duplicates posted twice → **books don't balance**
- refund booked as revenue
- one-to-many payment unmatched
- categories without evidence
- brief quotes a number that isn't in the ledger
- high cost (strong model everywhere)

**Find the causes with neatlogs:** Detections + Investigate across v1 traces → root causes.

**v2 (the design in [03](03-agent-design.md)):** code checks after every read, dedup, rule-first categorisation, Crustdata for unknown payees, gap hunt, brief computed from the ledger, cheap-first routing.

**Report** (`evidence/results.md`), one table, real numbers only:
| | v1 | v2 |
| --- | --- | --- |
| Balances | ✗ (gap ₹…) | ✅ (₹0) |
| Categorisation accuracy | …% | …% |
| Match accuracy | …% | …% |
| Unsupported posts | … | 0 |
| Traps caught | …/12 | …/12 |
| Cost per close | $… | $… |
| neatlogs trace | link | link |

## Judges' evidence checklist (from the hackathon page) → where it lives
| Judges ask for | Our evidence | Location |
| --- | --- | --- |
| The agent improved (before/after runs with numbers) | v1 vs v2 table + two neatlogs session links | `evidence/results.md` |
| You used neatlogs (links/screenshots) | Session links, detections, evals, cost chart | `evidence/neatlogs/` |
| You used Entire (checkpoints or graph output) | Checkpoint links on key commits, entire-graph output, `entire why` output | `evidence/entire/` |
| You used cfo.ai (business plan) | Munshi business plan export + screenshots; the customer actuals flowing in | `evidence/cfo-ai/` |
| The agent recovers from failures | Trace of a gap hunt (books didn't balance → found the duplicate → ✅) and a blurry-receipt re-read | `evidence/neatlogs/recovery.md` |
| You built in public (#neatHack) | Links to all posts | `evidence/build-in-public.md` |
| Code written during the hackathon | Public repo, commits dated Oct 10–12 | GitHub |

## Honesty rules
- Every number in the README, demo and posts comes from a real run with a trace link.
- Generated data is labelled generated.
- If v2 misses something, we say so in "known limitations".
