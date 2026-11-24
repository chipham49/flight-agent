# Same-Day Plan: Build and Submit by Tonight

**Goal:** a working flight agent with clear evidence for all 10 criteria, submitted tonight.
**Target score:** ~70–75/100. That's "Good" in most areas: honest, achievable, and well above a basic project.
**Who does what:** Claude Code writes the code. **You** set up the key, run the agent, check results, record the demo and submit.

---

## What we keep and what we cut

| Criterion (pts) | Keep (simple version) | Cut (mention as "next steps") |
|---|---|---|
| 1. Design (10) | Problem + diagram + 3 design reasons in the README | Long design docs |
| 2. Orchestration (15) | 6-step workflow, one state object, preferences memory, max-steps limit | Frameworks, chat memory |
| 3. Tools (10) | Web search, airport lookup (local file), bag-fee lookup (RAG), currency table | Paid flight API, MCP server |
| 4. RAG (10) | 10 airline bag-fee notes, search + top-3 results + citations | Rerank, multi-hop |
| 5. Observability (10) | A trace file per run: each step, tool call, prompt, tokens, time, cost | Langfuse account |
| 6. Evals (15) | 15 test cases, automatic scoring, v1 vs v2 comparison table | GitHub Actions CI |
| 7. Guardrails (10) | Input checks, no-booking rule, "price must appear in a source" check, fallback message | Advanced injection filters |
| 8. Cost (5) | Cost and time measured per run, cache, cheaper model for parsing | Batching |
| 9. Production (10) | Clean folders, `config.yaml`, `.env.example`, README run steps, Dockerfile | Online deploy, web UI |
| 10. Demo (5) | 3-minute screen recording | Slides (optional) |

---

## The agent (one picture)

```
Your trip ─► 1 Check input ─► 2 Understand trip ─► 3 Load preferences
                                                         │
   6 Answer + trace ◄── 5 Add bag fees (RAG) ◄── 4 Search flights (web)
   (top 3, true total,       + validate prices
    sources, warnings)
```

Every run saves a trace to `traces/<run-id>.json`, so you can show exactly what happened.

---

## Timeline (about 6 hours)

### ☐ Hour 1: Setup + core agent
- [ ] **You:** give Claude Code your Anthropic API key through the secure form. Never paste it in chat. Set a **$10 spending limit** at console.anthropic.com.
- [ ] **Claude Code:** builds the folders, config, state object and steps 1–4 and 6.
- [ ] **You:** run one trip, e.g. `python -m flight_agent "LAX to New York, Dec 10"`, and check that you get 3 flights with links.

### ☐ Hour 2: RAG + guardrails
- [ ] **Claude Code:** writes 10 short bag-fee notes (with source links and dates) and adds step 5.
- [ ] **Claude Code:** adds the guardrails: a past date gets rejected, "book it for me" gets refused, a price not found in a source gets dropped, and if search fails you get an honest message.
- [ ] **You:** try 3 tricky inputs and confirm the agent behaves.

### ☐ Hour 3: Observability + cost
- [ ] **Claude Code:** adds the trace file (steps, tool calls, prompts, tokens, seconds, $), a 30-minute cache, and Haiku for the parsing step.
- [ ] **You:** run the same trip twice. The second run should be faster and cheaper. Screenshot both.

### ☐ Hour 4: Evals
- [ ] **Claude Code:** creates 15 test cases and the eval runner, then runs **v1**.
- [ ] Look at the failures together and pick 1–2 fixes.
- [ ] **Claude Code:** applies the fixes, runs **v2**, and creates the comparison table.
- [ ] **You:** spot-check 3 prices on Google Flights and note the result in the README.

### ☐ Hour 5: README + demo
- [ ] **Claude Code:** writes the README with problem, diagram, design reasons, how to run, results tables, limitations and next steps.
- [ ] **You:** record a 3-minute demo:
  1. The problem (20 s)
  2. A live run (60 s)
  3. Open a trace file (40 s)
  4. The v1 vs v2 table (40 s)
  5. What's next (20 s)

### ☐ Hour 6: Buffer + submit
- [ ] Merge everything into `main` with a pull request
- [ ] Check that no API key is in the repo
- [ ] Submit the repo link + demo video

---

## If time runs out, cut in this order
1. Dockerfile
2. Cache
3. The v2 fix (keep the v1 results and explain what you would fix)

**Never cut:** the eval results and the trace files. Together they cover 25 points.
