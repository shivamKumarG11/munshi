# 12: Tech stack and repo layout

## Stack
| Layer | Choice | Why |
| --- | --- | --- |
| Language | **Python 3.12** | Best for PDFs, vision calls, beancount, Streamlit |
| LLM client | `openai` SDK → LiteLLM (`https://litellm.vision.aivar.app/v1`) | One OpenAI-compatible key for Nova + Claude |
| Tracing | `neatlogs` SDK (`neatlogs.init`, `neatlogs.wrap`, custom spans, sessions, tags) | Required; quality + cost |
| Ledger | **beancount** (+ `bean-check`) in a Git repo | Plain-text double entry, deterministic validation |
| Docs | `pdfplumber` / `pypdfium2` (PDF → text/images), Pillow | Text first; vision only when needed |
| Agent loop | Plain Python coordinator + specialist functions (no heavy framework) | Easy to trace, easy to debug in 40 h |
| Data store | JSON state files + SQLite; the ledger itself lives in Git | No database server needed (Postgres removed in review) |
| Payments | Dodo Payments API (test mode) + webhook endpoint (FastAPI) | Invoices + auto-reconciliation + our billing |
| Company data | Crustdata REST API | Payee resolution |
| UI | **Streamlit** | Fast; good enough for the demo |
| Hosting | Local for the core demo; AWS EC2 t3.small (us-east-1, Hackathon_VPC) as stretch | Webhooks, always-on |
| Dev tooling | Claude Code + **Entire** (checkpoints, graph) + neatlogs MCP; optional Orchestrator `ao` | Required + fast |

## Repo layout
```
munshi/
├── README.md                    # problem, demo, architecture, sponsors, results, limitations
├── hackathon.md                 # build log (neatHack skill format)
├── munshi/
│   ├── coordinator.py           # the close loop + state machine
│   ├── reader.py                # documents + bank statement → structured data
│   ├── categoriser.py           # rules → Crustdata → LLM, with evidence
│   ├── matcher.py               # txn ↔ document; dedup; one-to-many; partials
│   ├── ledger.py                # beancount writer + bean-check + gap hunt
│   ├── invoicer.py              # un-billed work → invoice → Dodo link
│   ├── collections.py           # ageing, reminders, Dodo webhook handling
│   ├── tax.py                   # net indirect tax, provision, non-claimable list
│   ├── briefer.py               # morning brief from ledger facts
│   ├── integrations/
│   │   ├── llm.py               # LiteLLM client + routing (wrapped by neatlogs)
│   │   ├── crustdata.py
│   │   ├── dodo.py
│   │   ├── peers.py             # SEC EDGAR + Companies House peer financials
│   │   └── cfoai.py             # actuals CSV export (MCP sync = stretch)
│   └── tracing.py               # neatlogs init, sessions, tags, spans
├── app/streamlit_app.py         # inbox · close run · books · actions · brief
├── server/webhooks.py           # FastAPI: Dodo webhooks
├── data/
│   ├── raw/                     # real documents (anonymised)
│   ├── generated/               # bank statement, timesheets (labelled generated)
│   └── answer_key/              # correct ledger + expected results
├── ledgers/studio-kaveri/       # the business's books-as-code repo (git)
├── eval/score.py                # metrics vs answer key
├── evidence/
│   ├── results.md               # v1 vs v2 table with trace links
│   ├── neatlogs/  entire/  cfo-ai/
│   └── build-in-public.md
├── entire-agent-munshi/         # (stretch) Entire Agent Integration Protocol executable
└── .env.example                 # never commit real keys
```

## Environment variables (`.env`, git-ignored)
```
LITELLM_API_KEY=
LITELLM_BASE_URL=https://litellm.vision.aivar.app/v1
NEATLOGS_API_KEY=
CRUSTDATA_API_KEY=
DODO_API_KEY=            # test mode
DODO_WEBHOOK_SECRET=
SEC_USER_AGENT=          # "Munshi <your-email>" (required by SEC EDGAR)
COMPANIES_HOUSE_API_KEY=
```

## Coding rules for the build
- Arithmetic only in code; LLM outputs are validated (pydantic) before use.
- Every external call goes through `integrations/` and is traced.
- Every posted ledger entry carries `document`, `bank_ref`, `decided_by` and `trace` metadata.
- Keep the neatHack build log (`hackathon.md`) updated after each session (official neatHack skill).
