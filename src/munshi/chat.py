"""Ask Munshi: answers questions about a closed month using ONLY that month's books and facts."""

import json
from pathlib import Path

from munshi import llm, tracing

SYSTEM = """You are Munshi, a careful chartered accountant for a small business.
Answer the owner's question using ONLY the closed books below (entries, facts, actions).
- Quote rupee figures exactly as they appear in the data; do not invent or estimate new numbers,
  except simple arithmetic on figures in the data (show it briefly).
- If the data does not contain the answer, say so plainly.
- Tax figures are estimates from the owner's configured assumptions; say "estimate" when you use them.
- Reply in 1-3 short sentences, plain language, no markdown headings."""


def _context(run_dir: Path) -> str:
    facts = json.loads((run_dir / "facts.json").read_text(encoding="utf-8"))
    entries = json.loads((run_dir / "entries.json").read_text(encoding="utf-8"))
    actions = json.loads((run_dir / "actions.json").read_text(encoding="utf-8"))
    compact_entries = [{"date": e["date"], "payee": e["payee"], "account": e["account"], "amount": e["amount"],
                        "tax": e["tax"], "why": e["narration"][:120], "decided_by": e["decided_by"],
                        "documents": e["document_ids"]} for e in entries]
    slim_facts = {k: v for k, v in facts.items() if k not in ("actions",)}
    return json.dumps({"facts": slim_facts, "entries": compact_entries, "actions": actions}, default=str)


@tracing.span("AGENT", name="ask_munshi")
def answer(question: str, run_dir: Path, history: list[dict] | None = None) -> str:
    convo = "".join(f"\nOwner: {h['q']}\nMunshi: {h['a']}" for h in (history or [])[-4:])
    prompt = f"Closed books (JSON):\n{_context(run_dir)}\n\nEarlier conversation:{convo or ' none'}\n\nOwner: {question}"
    return llm.ask_text("cheap", SYSTEM, prompt)
