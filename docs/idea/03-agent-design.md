# 03: Agent design

## Goal given to the agent
> *"Close {business}'s books for {month}. Done means: every bank transaction is recorded in the ledger with a category and evidence, the ledger balances to the bank statement exactly, and the owner has a brief with every open item listed."*

That finish line is **objective and checkable in code**, which is what makes this a real agent rather than a chatbot.

## Architecture
```
                     ┌──────────────────────────────┐
                     │   CLOSER (coordinator)       │  plans the close, tracks state,
                     │   "is the month done yet?"   │  decides the next step
                     └──────────────┬───────────────┘
        ┌──────────────┬────────────┼─────────────┬──────────────┬─────────────┐
        ▼              ▼            ▼             ▼              ▼             ▼
   READER         CATEGORISER    MATCHER      INVOICER       TAX           BRIEFER
   docs → data    txn → account  txn ↔ doc    un-billed →    net tax due,  morning
   (vision LLM)   (+ Crustdata)  dups/splits  invoice +Dodo  provision     brief
        │              │            │             │              │             │
        └──────────────┴────────────┴──────┬──────┴──────────────┴─────────────┘
                                            ▼
                         LEDGER (plain-text double entry, in Git)
                         + VERIFIER (deterministic: beancount check)
```
Every LLM call and tool call is traced in **neatlogs** (one trace per step, one session per month-close).

## Step 0: research the business (once per business)
```
RESEARCH  name + one-line description
          → Crustdata: industry, size, headcount, location
          → pick 3–5 REAL peers (same industry, similar size) from SEC EDGAR / Companies House
          → pull their filed financials (revenue, cost lines, margins, tax) in code
          → business profile: expected expense categories, "normal" ratios, a default tax profile
          VERIFY: every peer figure carries its source (filing id + concept + period)
```
The profile drives categorisation hints and the "compared with real peers" lines in the brief.

## The close loop (what the coordinator does)
```
1. PLAN      list inputs; estimate work; order: bank first, then docs, then match
2. READ      bank statement → transactions (code parser first; LLM only for odd formats)
             each document → structured fields (cheap vision model)
             VERIFY each doc in code: line items sum to subtotal; subtotal + tax = total;
                    date plausible; not a duplicate of an already-read document
             RECOVER: a check fails → re-read only the failing fields with a stronger model
                      → still failing → "needs help" item for the owner (never guess)
3. CATEGORISE each transaction → account + reason + confidence
             known payee or owner rule → apply rule (no LLM)
             unknown payee → Crustdata company lookup → categorise
             low confidence → ask the owner (batched, one tap each)
4. MATCH     bank txn ↔ document (amount, date window, party, reference)
             handles: one payment for many invoices, partial payments, refunds, duplicates
5. POST      write double-entry transactions to the ledger, each with links to
             source document + bank line + reasoning id (neatlogs trace)
6. VERIFY    run the ledger check (deterministic):
             • every transaction balances (debits = credits)
             • closing bank balance in ledger == closing balance on statement
             ✗ mismatch → enter GAP HUNT
7. GAP HUNT  find the difference: duplicates? missed transaction? wrong sign? split posted twice?
             propose a fix → re-verify → loop until ✅ or escalate with the exact gap
8. INVOICE   timesheets/delivery notes vs invoices issued → un-billed work → draft invoice
             → Dodo payment link (owner approves before sending)
9. COLLECT   unpaid invoices by age → reminder drafts; Dodo webhook "paid" → post receipt
10. TAX      "tax to set aside": an ESTIMATE from the owner's configured assumptions
             (rate on sales, claimable tax on purchases, income-tax provision %),
             shown alongside the result; list expenses without valid documents (not claimable yet)
11. BRIEF    compose the morning brief from ledger facts + peer benchmarks only (no new numbers)
12. CLOSE    commit the month to Git ("Close 2026-09"); export actuals CSV for cfo.ai
             (stretch: write them via the cfo.ai MCP server)
```

## State (survives crashes and pauses)
- `state/{business}/{month}.json`: step reached, items done, open questions, retries.
- The **ledger in Git** is the durable truth; every step that changes it is a commit.
- The agent can stop for owner answers and **resume** exactly where it was.

## Recovery: the failures we expect and handle
| Failure | What Munshi does |
| --- | --- |
| Blurry / rotated receipt | Re-read with a stronger vision model; still unreadable → ask owner for a better photo |
| Totals don't add up on a document | Re-extract the failing fields; if the document itself is wrong, flag it ("vendor's bill has an error") |
| Unknown payee | Crustdata lookup → still unknown → ask owner, remember the answer |
| Books don't balance | Gap hunt (above), never "force" the balance |
| Same bill uploaded twice | Detect by vendor + number + amount; keep one, note the duplicate |
| Model/API timeout or rate limit | Retry with backoff; switch model; resume from state |
| Owner doesn't answer | Close what can be closed; brief lists open items clearly |

## Verification: what is never left to the LLM
- **All arithmetic** (totals, tax, balances) is done in **code**.
- **The balance check** is deterministic (`beancount` ledger validation).
- **Every brief number** is computed from the ledger; the LLM only writes the sentences around the numbers.
- **Every category** must cite evidence (document id, rule, or owner answer); no evidence → not posted.

## Model routing (the $20 LiteLLM budget)
| Task | Model | Why |
| --- | --- | --- |
| Read documents (first pass) | `nova-lite` | Cheap, vision-capable |
| Categorise (bulk) | `claude-haiku` | Cheap, good at short reasoning |
| Re-read failing fields, gap hunt, ambiguous cases | `claude-sonnet-4.6` | Only when cheap models fail checks |
| Brief writing | `claude-haiku` | Short, numbers already computed |
The "cheap first, expensive only on failure" routing is itself a **measured result** in neatlogs (cost per close, before/after).
