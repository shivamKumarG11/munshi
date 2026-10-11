# Results: v1 → v2

All runs: neatHack's LiteLLM models (Nova Lite, Claude Haiku, Claude Sonnet 4.6), traced in neatlogs.

## 1. Closing the month (Studio Kaveri, Sep 2026: generated month, 21 bank lines, 9 documents, 12 planted traps)
| Metric | v1 (naive) | v2 (Munshi) |
| --- | --- | --- |
| Books balance to the bank | ✗ off by ₹9,050 | ✅ ₹0 (after gap hunt) |
| Categorisation accuracy | 90.5% | **100%** |
| Exact entries (account + amount + no duplicates) | 81% | **100%** |
| Duplicate postings | 1 | **0** |
| Traps caught | 2 / 12 | **12 / 12** |
| Net GST correct (₹50,017.30) | ✗ (₹48,487.30) | ✅ |
| Brief states the true profit (₹58,367) | ✗ (said ₹98,685) | ✅ |
| Model calls / tokens | 23 / 13,061 (all Sonnet) | 21 / **9,274** (Haiku/Nova, Sonnet once) |
| Time | 40 s | 50 s (includes SEC research) |
| neatlogs session | `close-studio-kaveri-2026-09-v1-023643` | `close-studio-kaveri-2026-09-v2-023726` |

Outputs: [`runs/close-v1/`](runs/close-v1/), [`runs/close-v2/`](runs/close-v2/) (brief, ledger, entries, facts, score).

### The recovery moment (v2 log)
```
[verify] ✗ Books don't balance: ledger vs bank gap ₹-9050.00
[gap_hunt] duplicate_post on B07: IMG_cloudnest_invoice_copy.pdf is the same file as cloudnest-hosting-sep.pdf, uploaded twice; keep one
[gap_hunt] amount_mismatch on B17: vendor's bill PWS-1177 prints total ₹6100.0, but its lines add to ₹5900.0; the bank paid the correct amount, so book the bank figure and flag the vendor
[verify] ✅ Books balance to the bank: ₹0 difference
```

## 2. Reading REAL documents (SROIE: 40 real scanned receipts, expert labels)
| Reader | Company | Date | Total | Notes |
| --- | --- | --- | --- | --- |
| v1: one vision call, plain prompt | 52.5% | 100% | 87.5% | |
| v2 first attempt | 40.0% | 62.5% | 52.5% | **regression found by the benchmark**: crashed on dates like `15/01/2019`, added branch names, read pre-rounding totals |
| **v2 after fix** | **70.0%** | 95.0% | **90.0%** | robust date parsing, tighter field instructions; Sonnet re-read on failed checks |

Honest note: v2 is better on company and total, slightly worse on date (95% vs 100%).
Details per receipt: [`runs/benchmark/`](runs/benchmark/).
