# Entire evidence

- **Entire enabled on this repo** (`.entire/settings.json`, Claude Code hooks in `.claude/settings.json`),
  logged in to entire.io; checkpoints sync to `origin`.
- **entire-graph** installed (v0.4.0) and activated for coding agents (`entire graph init-agents` →
  `AGENTS.md`, `CLAUDE.md`, `.entire/graph-agent.md`), so the next coding sessions navigate Munshi via the graph.
- Graph outputs from this repo:
  - [`graph-search-gap-hunt.txt`](graph-search-gap-hunt.txt): plain-language search "where does munshi repair
    gaps between the ledger and the bank" → `ledger.find_gaps` / `ledger.repair` ranked first
  - [`graph-impact-repair.txt`](graph-impact-repair.txt): blast radius of changing `repair`
  - [`graph-stats.txt`](graph-stats.txt)

## Books as code
Munshi commits each closed month to the business's own ledger repository (`ledgers/<business>/`):
`2026-09.beancount` + `2026-09.facts.json`, commit message `Close 2026-09: balanced`. Every ledger entry
carries `bank_txn`, `documents`, `decided_by` and `confidence` metadata: the same "why is this line
here?" idea Entire applies to code, applied to accounting.

## Note on checkpoints
The first build session started before Entire was installed, so its early commits have no checkpoints.
Sessions run from inside the repo after `entire enable` are captured automatically.
