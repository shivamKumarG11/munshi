# 10: Build plan (solo, v3)

**Deadline:** Mon Oct 12, submissions 7:00–~11:55 PM IST (final cutoff on Discord). **Target: submit by 8:00 PM.**

## Tiers
| CORE (no demo without it) | SHOULD (cheap, meaningful) | STRETCH (only if core is solid) |
| --- | --- | --- |
| Reader: bank CSV + documents, code checks | Crustdata payee lookup | Multi-company review mode |
| Categoriser with evidence + owner questions | Peer benchmarks (EDGAR / Companies House) | Dodo webhook → auto-post payment |
| Matcher: duplicates, one-to-many, partials | Draft invoice + Dodo payment link (test mode) | cfo.ai MCP sync |
| beancount ledger + balance check + **gap hunt** | Missing-bill / overdue drafts | `entire-agent-munshi` |
| Tax-to-set-aside estimate (assumptions shown) + brief | Streamlit polish | AWS deploy |
| neatlogs: sessions, workflows, tags, detections | neatlogs evals + alerts | Ask-anything chat |
| Test month + answer key + scorer; **v1 vs v2 runs** | | |
| cfo.ai business plan + actuals CSV upload | | |
| Entire checkpoints on every commit + graph output | | |

## Working solo: Orchestrator
Run **2–3 coding agents in parallel** with Orchestrator (`ao`), each in its own git worktree and module, while you review and merge:

| Worktree | Agent works on |
| --- | --- |
| `core` | reader → categoriser → matcher → ledger → gap hunt |
| `data` | test-month generator, answer key, `eval/score.py` |
| `edges` | Streamlit screens, peers (EDGAR), Crustdata, Dodo link |

Entire captures every agent's sessions; neatlogs traces every test run. **If Orchestrator setup takes more than ~45 minutes, drop it** and work in one worktree.

## Timeline (IST)
### Phase 0: setup + spikes (~2 h)
- [ ] Public repo; **Entire enabled** from the first commit; entire-graph installed
- [ ] neatlogs project + key; hello-world trace
- [ ] LiteLLM key; test `nova-lite` + `claude-haiku`
- [ ] Spikes (≤30 min each, go/no-go): beancount + `bean-check` · SROIE/CORD + DocILE access · EDGAR companyfacts fetch · cfo.ai signup (cancel the subscription right away) + CSV upload · Dodo test key · Orchestrator
- [ ] **X post #1**

### Phase 1: data (~3 h)
- [ ] Real documents assembled; bank statement + timesheet generated; 12 traps; answer key; scorer

### Phase 2: v1 (~4 h)
- [ ] Naive end-to-end pipeline, fully traced (`agent_version=v1`)
- [ ] **Run v1 → save numbers + trace links** → X post #2

### Phase 3: v2 (~6 h)
- [ ] neatlogs Detections + Investigate on v1 → root causes
- [ ] Code checks, dedup, rule-first categoriser, gap hunt, ledger-computed brief, cheap-first routing
- [ ] **Run v2 → `evidence/results.md`** → X post #3
- [ ] **Sleep 4–5 h**

### Phase 4: SHOULD items (~4 h)
- [ ] Research step: Crustdata + EDGAR peers → profile + benchmarks in the brief
- [ ] Dodo payment link on the drafted invoice
- [ ] Streamlit: setup, close run, books, brief
- [ ] Actuals CSV → cfo.ai

### Phase 5: business + evidence (~2.5 h)
- [ ] Munshi business plan in cfo.ai (cost per close from neatlogs)
- [ ] `evidence/` complete; README; `entire review`

### Phase 6: demo + submit (~3 h)
- [ ] Record ([09](09-demo-script.md)), upload, test link
- [ ] **7:00 PM**: Submit on X; check Discord for the cutoff

## Cut order if behind
STRETCH → Streamlit polish → Dodo link → peer benchmarks. **Never cut:** gap hunt, v1/v2 evidence, cfo.ai plan, Entire checkpoints, the video.
