# 04: Books as code (the original idea)

## The insight
The biggest reason nobody trusts AI with their books: **"Why did it put this there?"**

Accountants and auditors need an **audit trail**: every number traced to a source document and a decision. Software engineers solved the same problem for code with **Git**, and **Entire** extends it to AI agents: every line of code can be traced to the AI session (prompt, reasoning, tool calls) that wrote it.

**Munshi applies that idea to accounting:**

> **The business's books are a plain-text ledger in a Git repository. Every entry Munshi writes is a commit, linked to the source document and to the AI session that decided it. Ask "why?" about any line and get the full answer.**

## What the ledger looks like
Plain-text double-entry accounting (the **beancount** format, an established open-source standard):

```beancount
2026-09-12 * "Figma" "Design software, Sep"
  document: "docs/2026-09/figma-inv-4821.pdf"
  bank_ref: "HDFC 12/09 RZP*FIGMA 4821"
  decided_by: "munshi categoriser, rule: owner-rule-007 (Figma = Software)"
  trace: "https://app.neatlogs.com/…/trace/…"
  Expenses:Software          1,250.00 INR
  Expenses:Tax:InputCredit     225.00 INR
  Assets:Bank:HDFC          -1,475.00 INR
```
- **Human-readable**: an accountant can open it in any text editor.
- **Machine-checkable**: `bean-check` verifies every transaction balances and balance assertions hold.
- **Versioned**: `git log ledger/2026-09.beancount` shows every change and who or what made it.

## "Why is this number here?"
Three layers of answer, from any line in the books:
1. **The document**: the bill/receipt the line came from (link).
2. **The decision**: the agent's reasoning, the rule or owner answer used (the **neatlogs trace**).
3. **The change history**: which close run wrote it, what was corrected later (**Git + Entire**).

### With Entire (the ambitious version)
Entire lets you add your own agent through its **Agent Integration Protocol** (an `entire-agent-<name>` executable speaking JSON over stdin/stdout). If we build `entire-agent-munshi`, **Munshi's own sessions become Entire checkpoints** on the ledger repo, so:

```bash
entire why ledger/2026-09.beancount:142
# → commit "Close 2026-09: categorise 46 transactions"
# → Munshi session: prompt, the receipt it read, the Crustdata lookup, its reasoning
```
That's an **AI bookkeeping audit trail using Entire's own tooling**, a use of Entire nobody else at the hackathon will think of. It's also exactly what an auditor wants.

**Feasibility:** the protocol needs a handful of subcommands (`info`, `detect`, `get-session-id`, `get-session-dir`, hooks, transcript). Entire publishes an `external-agents` skill and examples (cloned in `data/02-entire/github/external-agents`). **We spike this in the first hours; if it's too heavy, we fall back** to: ledger in Git + commit messages carrying the neatlogs trace link + Munshi's session transcript saved next to each close commit. The "why?" feature still works; it just isn't served by `entire why`.

## Why this matters to a real business (not just judges)
- **Trust:** the owner (and their CA, and any auditor or tax officer) can verify every AI decision.
- **Corrections are safe:** fix a wrong category → it's a commit; the history shows what changed and why.
- **No lock-in:** the books are an open text format, not trapped in an app.
- **Handoff to a human CA is trivial:** give them the repo.
