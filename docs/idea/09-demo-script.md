# 09: Demo script (≤ 3:00), v3: built around the recovery moment

The rules require covering **neatlogs, Entire and cfo.ai: architecture, implementation, runtime, reasoning and result for each.** The agent's recovery is the star; sponsors are shown briefly, with real evidence.

| Time | Screen | Voice-over (draft) |
| --- | --- | --- |
| **0:00–0:12** | A bank CSV + a pile of real receipts and bills | "Every business has a CA it can't afford to call every day. This is month-end. Meet Munshi." |
| **0:12–0:30** | Setup: Munshi researches the business; shows 4 **real peer companies** and their filed ratios | "First Munshi researches the business and finds real peers from their public filings, so it knows what normal looks like." |
| **0:30–1:20** | **Close run, live**: reading → categorising → matching → **balance check ✗: off by ₹14,750** → gap hunt → *"bill uploaded twice, posted twice"* → fix → **✅ ₹0** | "It reads, categorises and matches every transaction. Then it checks the books against the bank. They're off. Munshi doesn't fudge it: it hunts the gap, finds a duplicate bill, fixes it and re-checks. Balanced to the rupee." |
| **1:20–1:45** | **neatlogs**: session replay of this close, open on the gap-hunt step; cost of the close | "Every step is traced in neatlogs. Here's the gap hunt, decision by decision, and what this close cost." |
| **1:45–2:05** | **neatlogs before/after**: v1 vs v2 table (real numbers) + detection "posted without evidence" count | "Version one didn't balance and posted entries without evidence. neatlogs caught it, showed us why, and after the fix, here are the numbers." |
| **2:05–2:25** | **Entire**: checkpoint on the fix commit (the coding session that read the neatlogs traces) + graph output | "The fix was written by our coding agent reading those traces. Entire saved that session on the commit, so the why behind the code is kept." |
| **2:25–2:45** | **cfo.ai**: the business's closed actuals in cfo.ai; Munshi's own business plan (cost per close from neatlogs → margin) | "Verified books go into cfo.ai, so the owner plans on real numbers. And we priced Munshi itself in cfo.ai, on costs neatlogs measured." |
| **2:45–3:00** | The brief (tax to set aside shown **with its assumptions**; one Dodo payment-link invoice if built) | "Books closed, gaps explained, tax to set aside estimated from your settings. Munshi: every number, proven." |

## Rules for recording
- Only **real** numbers from `evidence/results.md` on screen.
- Say "real receipts and invoices; bank statement generated from them" once, plainly.
- Captions on; ≤ 3:00; 1080p; backup recording of the close run.
- Upload (YouTube unlisted / Loom); test the link in a private window.
