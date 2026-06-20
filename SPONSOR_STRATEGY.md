# RhetoriQ Sponsor Strategy

**Document purpose:** Map RhetoriQ to the hackathon sponsor ecosystem and define how each sponsor integration should support the product.  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`, `DATA_SCHEMA.md`, `AGENT_SYSTEM.md`, `AGENT_PROMPTS.md`  
**Audience:** sponsor integration owner, teammates, judges, mentors, and AI coding agents.

---

## 1. Sponsor Strategy Summary

RhetoriQ should not randomly add sponsor tools just to say we used them.

The goal is to use sponsor technology in ways that are **native to the product**.

RhetoriQ’s sponsor story should be:

> RhetoriQ uses Redis as the real-time narrative memory and retrieval layer, Anthropic as the investigation and debate engine, Fetch AI to expose the product as a discoverable civic intelligence agent, Arize to evaluate and monitor source grounding, Browserbase to verify evidence pages, and optional tools like Deepgram, Sentry, Band, and Orkes to expand reliability, multimodal ingestion, and multi-agent workflows.

The best sponsor integrations are the ones that directly support:

1. **Investigation**
2. **Retrieval**
3. **Evidence verification**
4. **Agent coordination**
5. **Source grounding**
6. **Trust and reliability**
7. **Civic/social impact**

---

## 2. Sponsor Priority Ranking

| Priority | Sponsor | Fit | Why |
|---|---|---:|---|
| P0 | Anthropic | 10/10 | Core investigation, reasoning, agent debate, report generation |
| P0 | Redis | 10/10 | Vector search, semantic cache, phrase counters, agent memory |
| P1 | Fetch AI | 9/10 | Discoverable civic intelligence agent through Agentverse / ASI:One |
| P1 | Arize | 8.5/10 | AI observability, evals, hallucination/source-grounding checks |
| P1 | Browserbase | 8.5/10 | Source-page verification and evidence collection |
| P1/P2 | Band | 7.5/10 | Multi-agent room and context sharing |
| P2 | Deepgram | 7.5/10 | Speech/transcript ingestion for debates, speeches, hearings |
| P2 | Sentry | 7/10 | Reliability and error monitoring |
| P2 | Orkes | 6.5/10 | Workflow orchestration for investigation pipeline |
| P3 | Interaction Co / Poke | 6/10 | Miniapp interface for Ask RhetoriQ |
| P3 | Simular | 5.5/10 | Build/test accelerator, not core product feature |
| P3 | Cognition / Devin | 5/10 | Build accelerator, not core product feature |
| P3 | Pika | 5/10 | Optional civic explainer videos |
| P3 | Midjourney | 4.5/10 | Optional visual assets only |
| P4 | Annapurna Labs | Unknown | Could fit infrastructure depending on final track |
| P4 | Context | Unknown | Could fit if focused on context/memory |
| P4 | The Token Company | Unknown | Wait for details |
| P4 | PaleBlueDot AI | Unknown | Wait for details |
| P4 | Overshoot AI | Unknown | Wait for details |
| P4 | Fieldguide | Unknown | Wait for details |
| P4 | QNX | 2/10 | Likely embedded/automotive; weak fit |
| P4 | Ultimate Bots | 2/10 | Robotics/physical AI; weak fit |

---

## 3. Primary Sponsor Stack

The strongest sponsor stack for RhetoriQ is:

```text
Anthropic + Redis + Fetch AI + Arize + Browserbase
```

Optional add-ons:

```text
Band + Deepgram + Sentry + Orkes
```

This gives RhetoriQ a clean product story where each sponsor is a **stage gate**, not a plugin. Each step must complete before the next can run.

```text
User prompt
        ↓
[REDIS] assembles context packet
  (vector search + prior memory + phrase stats)
        ↓
[ANTHROPIC] agents reason over that context
  (Planner → Analyst → Skeptic → Final Report)
        ↓
[BROWSERBASE] verifies the sources Anthropic cited
  (visits live pages, extracts metadata, flags mismatches)
        ↓
[ARIZE] evaluates whether the verified report is still overclaiming
  (runs grounding eval; if score fails, triggers Skeptic revision loop)
        ↓
[SENTRY] catches any failures in that chain
        ↓
User sees report (or Fetch AI exposes it as a discoverable agent)
```

The sequential dependency is the story. Redis must run before Anthropic can run. Browserbase must run before Arize evaluates. Arize must run before the user sees the report. This is what makes the integration genuinely deep instead of five APIs bolted together.

---

## 4. P0 Sponsors

## 4.1 Anthropic

### Fit

**10/10**

Anthropic is one of the most important sponsor integrations because RhetoriQ’s core product is an AI investigation workflow.

### What Anthropic Should Power

Anthropic should power:

- natural language query understanding
- investigation planning
- narrative synthesis
- analyst report generation
- skeptic review
- safety review
- agent debate
- final report generation

### RhetoriQ Features Powered

- Ask RhetoriQ Investigation Mode
- Multi-Agent Investigation Room
- Agent Debate Before Final Report
- Source-Grounded Investigation Report
- Receipts Mode support
- Safety / Grounding Agent
- Counter-Narrative summaries
- Narrative Family Tree summaries

### Agent Roles Anthropic Can Power

Four agents is the right number. Do not add more without a clear reason.

- **Planner Agent** — adaptive retrieval planner (see note below)
- **Analyst Agent** — drafts findings from retrieved evidence
- **Skeptic Agent** — challenges the Analyst's draft for overclaims
- **Final Report Agent** — writes the output after Skeptic approval

The Planner Agent must do something dynamic, not just decompose a query into a fixed list. A static query list is a system prompt, not an agent. A judge will see through it.

**What makes the Planner a real agent:**

Before generating retrieval queries, the Planner checks Redis memory for prior investigations on the same topic.

- If memory exists: output `"mode": "narrow"` — focus retrieval on sources newer than the prior investigation date, skip already-covered claims.
- If no memory exists: output `"mode": "broad"` — retrieve across all source types and time ranges.

This adaptive behavior based on memory state is what makes it an agent rather than a prompt template.

### MVP Implementation

Use Anthropic to:

1. Check Redis for prior memory, then plan retrieval mode accordingly.
2. Draft the investigation report from the Redis context packet.
3. Run the Skeptic Agent pass to catch overclaims before the report is finalized.
4. Generate the final source-grounded report after Skeptic approval.

### Best Demo Moment

Show the agent debate:

```text
Analyst Agent:
“This may indicate coordinated amplification.”

Skeptic Agent:
“The evidence is not strong enough to claim coordination. Use cautious language.”

Final Report:
“Signals are consistent with coordinated amplification, but evidence is insufficient for a definitive claim.”
```

### Sponsor Demo Line

> Anthropic powers RhetoriQ’s investigation agents — they reason over evidence, debate uncertainty, and generate careful source-grounded civic intelligence reports.

### Why Judges/Sponsors Should Care

This is a strong Anthropic use case because it is:

- reasoning-heavy
- source-grounded
- safety-sensitive
- socially impactful
- more advanced than a simple chatbot

### Risks

- Model may hallucinate.
- Model may overclaim political conclusions.
- Model may produce unsupported coordination language.

### Mitigation

- Require structured JSON.
- Use Receipts Agent.
- Use Skeptic Agent.
- Use Safety / Grounding Agent.
- Use Arize evals.
- Use low temperature for report generation.

---

## 4.2 Redis

### Fit

**10/10**

Redis is a perfect fit because RhetoriQ needs real-time memory, vector search, semantic cache, and fast narrative lookup.

### What Redis Should Power

Redis should power:

- vector search over documents
- semantic search over prior investigations
- semantic caching for repeated or similar queries
- phrase spike counters
- narrative memory
- source memory
- agent memory
- fast dashboard cards

### RhetoriQ Features Powered

- Ask RhetoriQ retrieval
- Live Narrative Radar
- Narrative Spike Detection
- Narrative Memory
- Prior Investigation Recall
- Semantic Cache
- Receipts lookup
- Fast evidence retrieval

### MVP Implementation

Use Redis for at least two of these:

1. **Vector search**
   - Store document embeddings.
   - Retrieve semantically similar documents for a user prompt.

2. **Semantic cache**
   - Cache report results for similar queries.
   - Avoid repeated LLM calls for near-duplicate investigations.

3. **Phrase counters**
   - Count phrase mentions in time windows.
   - Compute spike scores.

4. **Agent memory**
   - Store prior narrative clusters and reports.

### Context Packet Architecture

Redis does not just retrieve documents — it **assembles a structured context packet** before any LLM call happens. This is the key architectural story for a Redis judge.

```text
User prompt
        ↓
Redis: embed prompt → vector search → top N documents
Redis: check memory → prior investigation summaries for this topic
Redis: read sorted set → phrase spike stats for matching terms
        ↓
Assemble context packet (before Claude is called):
{
  "retrieved_sources": ["src_001", "src_002", "src_003"],
  "prior_memories": ["mem_001"],
  "phrase_stats": {
    "hidden energy tax": {"spike_score": 4.2, "first_seen": "2024-10-01"},
    "energy price manipulation": {"spike_score": 2.1, "first_seen": "2024-11-03"}
  }
}
        ↓
Anthropic agents receive the packet — not raw documents
```

Redis is the orchestration layer that assembles intelligence. Claude reasons over the assembled packet. Neither step substitutes for the other.

### Strongest Redis Architecture

```text
Documents → embeddings → Redis vector index
User prompt → embedding → Redis semantic search → retrieved_sources
Narrative phrases → Redis counters/sorted sets → phrase_stats
Prior reports → Redis agent memory → prior_memories
All three → assembled context packet → Anthropic agents
Final report → Redis semantic cache (skip LLM for duplicate queries)
```

### Sponsor Demo Line

> Redis is RhetoriQ’s real-time narrative memory layer: it assembles a structured context packet — retrieved sources, prior memories, and phrase spike stats — before Anthropic agents ever see the data.

### Why Judges/Sponsors Should Care

This is a strong Redis use case because it maps directly to their AI app workshop concepts:

- vector search
- semantic caching
- agent memory
- low-latency retrieval

### Risks

- Redis integration may take time.
- Vector search setup may fail during demo.
- Data may be too small to show real value.

### Mitigation

- Use a seeded dataset.
- Precompute embeddings.
- Show before/after semantic retrieval.
- Cache at least one investigation.
- Have static fallback JSON.

---

## 5. P1 Sponsors

## 5.1 Fetch AI

### Fit

**9/10**

Fetch AI is one of the strongest sponsor opportunities because RhetoriQ can be packaged as a discoverable civic intelligence agent.

### What Fetch AI Should Power

Fetch AI should power:

- Agentverse registration
- ASI:One discoverability
- external query access
- civic intelligence agent interface
- optional Chat Protocol support
- optional Payment Protocol support

### RhetoriQ Feature Powered

- Ask RhetoriQ as a discoverable agent

### Agent Concept

```text
RhetoriQ Narrative Investigator Agent
```

### Agent Capabilities

The Fetch agent should accept prompts like:

```text
Investigate the hidden energy tax narrative.
```

```text
Trace the story behind the TikTok ban.
```

```text
What political narratives are emerging around immigration?
```

And return:

- short summary
- top evidence
- first observed source
- confidence
- report link
- clickable source links if supported

### MVP Implementation

Minimum:

1. Register a RhetoriQ agent.
2. Give it a description.
3. Make it accept a prompt.
4. Return a summary and report URL.

Better:

1. Agent calls backend `/api/investigate`.
2. Backend returns report.
3. Agent returns summary, confidence, and link.

### Sponsor Demo Line

> Fetch AI lets us expose RhetoriQ as a discoverable civic intelligence agent that users can query directly through the agent ecosystem.

### Why Judges/Sponsors Should Care

This makes RhetoriQ more than a web app. It becomes an agentic service.

### Risks

- Agent registration/setup may be unfamiliar.
- API integration may be difficult under time pressure.

### Mitigation

- Make the web app work first.
- Register a simplified agent second.
- Return pre-generated demo report if full backend integration is not ready.

---

## 5.2 Arize

### Fit

**8.5/10**

Arize is highly relevant because RhetoriQ deals with sensitive civic/political information, where hallucination and overclaiming are major risks.

### What Arize Should Power

Arize should power:

- agent trace logging
- retrieval quality tracking
- final report evaluation
- source-grounding checks
- hallucination risk evaluation
- receipt coverage evaluation
- overclaim detection
- prompt/output monitoring

### RhetoriQ Features Powered

- Receipts Mode
- Safety / Grounding Agent
- Agent Debate
- Source-Grounded Investigation Report
- Trust and evaluation layer

### MVP Implementation

Arize must do more than log and display. The eval result must feed back into the pipeline. A “grounding badge” that is always green is decoration. The loop below makes Arize provably improve the output.

**The Arize feedback loop:**

```text
Step 1 — Analyst Agent drafts report
Step 2 — Arize eval runs on draft:
  Grounding: 0.68 / 1.0
  Overclaim: HIGH (“coordination” not supported by evidence)
Step 3 — Eval result is passed back to Skeptic Agent
Step 4 — Skeptic Agent revises the draft:
  “Soften ‘coordinated amplification’ to ‘patterns consistent with amplification’”
Step 5 — Arize eval runs again on revised report:
  Grounding: 0.91 / 1.0
  Overclaim: LOW
Step 6 — Report passes to user
```

Show the before/after scores in the UI. That single delta proves Arize changed the output, not just observed it. A judge who sees a score go from 0.68 to 0.91 after a Skeptic revision understands immediately.

**What to log per trace:**

- user query
- Redis context packet (retrieved sources, prior memories, phrase stats)
- Analyst Agent draft
- Arize eval result on draft (grounding score, overclaim flag, specific claim)
- Skeptic Agent revision
- Arize eval result on revision
- final report passed to user

### Suggested Eval Metrics

| Metric | Meaning |
|---|---|
| Source Grounding Score | Are claims supported by provided evidence? |
| Receipt Coverage Score | Do claims have receipts? |
| Overclaiming Risk | Does report go beyond evidence? |
| Uncertainty Quality | Does report include caveats? |
| Political Safety Risk | Does report make unsafe accusations? |
| Counter-Narrative Quality | Are competing frames represented? |
| Defamation Risk | Does report accuse people/groups without support? |

### Sponsor Demo Line

> Arize evaluates each civic intelligence report for source grounding before it reaches the user. When a report overclaims, the eval score is sent back to the Skeptic Agent for revision — and Arize evaluates the revision again. The before/after scores are visible in the UI.

### Why Judges/Sponsors Should Care

This shows responsible AI that actually loops, not just flashy AI that logs.

### Risks

- Feedback loop adds latency.
- May add complexity to the agent chain.

### Mitigation

- Run the loop on one flagged claim per report, not all claims.
- Show at least one real before/after delta in the demo.
- The UI badge should show the **revised** score, not just a static pass/fail.

---

## 5.3 Browserbase

### Fit

**8.5/10**

Browserbase helps RhetoriQ verify sources and collect evidence from pages.

### What Browserbase Should Power

Browserbase should power:

- source page visits
- title extraction
- timestamp extraction
- author extraction
- snippet verification
- receipt verification
- evidence provenance

### RhetoriQ Features Powered

- Receipts Mode
- Source Verification
- Browser-verified evidence
- Trust/provenance trail

### MVP Implementation

Use Browserbase to:

1. Open the source URL cited by the Analyst Agent.
2. Extract live title, date, and snippet from the page.
3. Compare against the stored document metadata.
4. Set a verification status on the receipt.

**Do not filter for URLs that will verify cleanly.** Let Browserbase find failures. Failure states are more convincing than an all-green result, because a judge who sees only green checks assumes the demo was pre-arranged.

### Verification Status Values

```text
browser_verified: true    — live page matches stored metadata
source_updated: true      — live title/snippet differs from stored version
source_unavailable: true  — page returned 404 or is paywalled
```

### UI Display

Show all three states honestly in Receipts Mode:

```text
✓ Verified from source page          (browser_verified)
⚠ Source updated since ingestion     (source_updated — show diff)
✗ Source no longer available         (source_unavailable — show ingestion timestamp)
```

A judge who sees "Source updated since ingestion" with a diff believes the system is real. A judge who sees only green checkmarks does not.

### Why Failure States Are A Feature

If your corpus was pulled weeks ago, some pages will have changed or disappeared. This is not a bug — it is evidence that the verification system is live. Showing a mismatch honestly, with the ingestion timestamp preserved, demonstrates a more trustworthy product than one that hides it.

### Sponsor Demo Line

> Browserbase visits the live source pages behind every receipt. When a page has changed or disappeared since ingestion, RhetoriQ flags it — which is more honest than pretending scraped text is always current.

### Why Judges/Sponsors Should Care

This is a visible agentic workflow that handles real-world messiness:

```text
Analyst cites source → Browserbase visits live page → compares to stored data
→ shows match, mismatch, or unavailable → receipt reflects reality
```

### Risks

- Some websites block scraping.
- Page loading may be slow during demo.

### Mitigation

- Verify 3–5 sources per report, not all sources.
- Accept and display all three status outcomes — do not retry to force green.
- Show the ingestion timestamp on unavailable receipts so the provenance is still clear.

---

## 5.4 Band

### Fit

**7.5/10**

Band is a strong fit if their track rewards multi-agent apps where agents coordinate in shared rooms.

### What Band Should Power

Band can power:

- Multi-Agent Investigation Room
- shared context between agents
- agent debate
- multi-agent collaboration
- visible investigation process

### RhetoriQ Features Powered

- Multi-Agent Investigation Room
- Agent Debate Before Final Report
- Agent trace view
- Collaborative civic investigation

### MVP Implementation

Represent agents like:

- Query Planner Agent
- Retriever Agent
- Analyst Agent
- Skeptic Agent
- Receipts Agent
- Safety Agent

Have them share a room/context and produce a final report.

### Sponsor Demo Line

> Band helps RhetoriQ coordinate a room of specialized agents that investigate, debate, verify, and safely summarize political narratives.

### Why Judges/Sponsors Should Care

This is a true multi-agent project, not a simple single-agent chat app.

### Risks

- Tool setup may be hard.
- Native Band integration may be optional.

### Mitigation

- Build internal multi-agent architecture first.
- Integrate Band if workshop/tooling is fast.
- At minimum, show the agent room concept clearly in UI.

---

## 6. P2 Sponsors

## 6.1 Deepgram

### Fit

**7.5/10**

Deepgram is a strong extension if RhetoriQ includes audio/speech sources.

### What Deepgram Should Power

Deepgram should power:

- speech-to-text for speeches
- debates
- hearings
- town halls
- podcasts
- public remarks
- livestream clips

### RhetoriQ Features Powered

- Speech / Transcript Ingestion
- Political Speech Pickup Detection
- Online-to-speech narrative tracing
- Transcript receipts

### MVP Implementation

Use Deepgram to transcribe one audio clip or demo speech file.

Then:

1. Extract phrases.
2. Match transcript phrases to narrative cluster.
3. Add transcript to timeline.
4. Show it as an “official mention” or “speech mention.”

### Sponsor Demo Line

> Deepgram lets RhetoriQ detect when online narratives move into spoken political media such as speeches, debates, hearings, or podcasts.

### Why Judges/Sponsors Should Care

This makes RhetoriQ multimodal and more civic-media complete.

### Risks

- Audio adds complexity.
- Transcription may take time.
- Not necessary for core product.

### Mitigation

- Keep as optional.
- Use one short preselected audio clip.
- Store transcript fallback.

---

## 6.2 Sentry

### Fit

**7/10**

Sentry is not the flashiest sponsor integration, but it gives the project reliability polish.

### What Sentry Should Power

Sentry should monitor:

- frontend errors
- backend errors
- failed investigations
- failed source retrieval
- failed agent calls
- failed receipt generation

### RhetoriQ Features Powered

- Reliability monitoring
- Production readiness
- Demo debugging

### MVP Implementation

Add Sentry to:

- frontend app
- backend API

Log custom context:

- investigation ID
- agent role
- failure step
- source URL if retrieval failed

### Sponsor Demo Line

> Sentry gives RhetoriQ production-style monitoring so failures in the ingestion, agent, and report pipeline are visible instead of silent.

### Why Judges/Sponsors Should Care

It shows engineering maturity.

### Risks

- Not as visible in demo.
- May not help core judging unless sponsor-specific.

### Mitigation

- Add simple monitoring quickly.
- Show one screenshot/dashboard if needed.
- Do not prioritize above core product.

---

## 6.3 Orkes

### Fit

**6.5/10**

Orkes may fit if their challenge focuses on workflow orchestration.

### What Orkes Should Power

Orkes could orchestrate:

```text
detect spike
  ↓
retrieve evidence
  ↓
verify sources
  ↓
build graph
  ↓
agent debate
  ↓
generate report
  ↓
evaluate grounding
  ↓
publish
```

### RhetoriQ Features Powered

- Investigation workflow
- Agent orchestration
- Report pipeline
- Long-running investigation state

### MVP Implementation

If easy, define a workflow with these steps:

1. Query planning
2. Retrieval
3. Timeline
4. Graph
5. Agent debate
6. Receipts
7. Safety review
8. Final report

### Sponsor Demo Line

> Orkes orchestrates RhetoriQ’s investigation workflow from detection to source verification to final report generation.

### Risks

- Workflow setup may take time.
- The app can work without Orkes.

### Mitigation

- Use only if sponsor challenge strongly rewards it.
- Otherwise keep workflow in backend code.

---

## 7. P3 Sponsors

## 7.1 Interaction Co / Poke

### Fit

**6/10**

Interaction Co / Poke could fit if RhetoriQ is packaged as a miniapp.

### What It Could Power

- Ask RhetoriQ miniapp
- lightweight investigation interface
- agentic tool integration

### MVP Idea

Miniapp prompt:

```text
Ask about any political narrative...
```

Output:

- summary
- first observed source
- top receipts
- full report link

### Sponsor Demo Line

> Interaction Co / Poke lets us package Ask RhetoriQ as a lightweight miniapp users can access without opening the full dashboard.

### Risk

This is not core. Build only if the sponsor track looks valuable and the integration is fast.

---

## 7.2 Pika

### Fit

**5/10**

Pika can support creative storytelling but is not core to RhetoriQ.

### Possible Use

Generate a short civic explainer video from a narrative report.

Example:

```text
"How the hidden energy tax narrative spread in 60 seconds"
```

### Sponsor Demo Line

> Pika helps convert RhetoriQ investigations into shareable civic-literacy explainers.

### Risk

This could distract from the serious civic investigation product.

### Mitigation

Frame it as public education, not persuasion.

---

## 7.3 Midjourney

### Fit

**4.5/10**

Midjourney can help with visuals but should not be central.

### Possible Use

- landing page imagery
- abstract narrative-spread visuals
- presentation assets

### Avoid

- fake political images
- realistic images of public figures
- misleading campaign-style visuals

### Sponsor Demo Line

> Midjourney helped generate non-misleading visual assets for explaining narrative spread.

---

## 7.4 Simular

### Fit

**5.5/10 as product feature, 8/10 as build tool**

Simular may be better used to help build/test the project rather than as a core product feature.

### Possible Use

- agent-assisted coding
- UI testing
- click-through testing
- bug finding

### Sponsor Demo Line

> Simular helped accelerate development and test the RhetoriQ app through an autonomous build-test-fix loop.

### Risk

This may not count as a product integration unless the sponsor track values build workflows.

---

## 7.5 Cognition / Devin

### Fit

**5/10 as product feature, 8/10 as build tool**

Cognition/Devin is probably more useful as an engineering assistant than a core product integration.

### Possible Use

- generate code
- fix bugs
- create tests
- improve reliability

### Sponsor Demo Line

> Cognition/Devin accelerated development of RhetoriQ’s investigation workflow and UI.

---

## 7.6 Claude Code (Anthropic)

### Fit

**8/10 as build tool**

Claude Code is the right tool for building the Skeptic Agent prompts, the Arize eval functions, and the Redis context packet assembly logic — all three are subtle enough to benefit from iterative AI-assisted drafting and testing.

### What Claude Code Should Build

Use Claude Code during the hackathon to:

- Draft and iterate on all four agent prompts (Planner, Analyst, Skeptic, Final Report).
- Write the Arize eval functions for grounding and overclaim detection.
- Build the Redis context packet assembly logic.
- Write the Browserbase receipt verification and status comparison logic.

### How to Demonstrate Claude Code Usage

**Do not rely on a log file as the primary proof.**

The Anthropic prize criteria requires showing the project was "built with Claude Code." The judges will ask you to show this, not read a document. The strongest proof is a live demonstration at the sponsor table:

1. Open your terminal with Claude Code during the demo or at the sponsor table.
2. Show a real prompt you used during the build — for example, iterating on the Skeptic Agent prompt or writing the Arize eval function.
3. Say: "This is what we used to build and refine the Skeptic Agent. Here is one of the sessions."

A commit history showing Claude Code suggestions at key implementation points is a good secondary proof. A static log file is a backup, not the primary evidence.

### Sponsor Demo Line

> We built the agent prompts, Arize eval functions, and Redis context assembly logic with Claude Code — and we can show you the sessions at the sponsor table.

### Risk

- Log file alone is not convincing.
- If Claude Code was used minimally, judges will notice.

### Mitigation

- Actually use Claude Code throughout the build, not just at the end.
- Keep terminal history or session output for the three most important uses.
- At the Anthropic sponsor table, open Claude Code and demonstrate it rather than pointing to a document.

---

## 8. Unknown / Coming Soon Sponsors

Some sponsor workshops are listed as “coming soon.” Do not force integrations until final challenge details are released.

## 8.1 Annapurna Labs

### Fit

Unknown, potentially infrastructure-focused.

Possible angles:

- scalable AI systems
- cloud infrastructure
- low-latency processing
- real-time data pipelines

### How RhetoriQ Could Fit

If Annapurna rewards scalable AI infrastructure, emphasize:

- real-time narrative monitoring
- low-latency retrieval
- event-driven architecture
- efficient inference workflow
- production deployment vision

### Current Recommendation

Wait for track details.

---

## 8.2 Context

### Fit

Unknown, potentially high if related to context engineering or memory.

Possible angles:

- long-context investigation
- source context management
- agent memory
- retrieval context optimization

### Current Recommendation

Monitor track release. Could become very relevant.

---

## 8.3 The Token Company

### Fit

Unknown.

Possible angles:

- verified access
- provenance
- tokenized reports
- paid civic intelligence agent
- source authenticity

### Current Recommendation

Do not force unless challenge supports it.

---

## 8.4 PaleBlueDot AI

### Fit

Unknown.

Possible angles:

- public-good AI
- social-impact intelligence
- civic or environmental monitoring
- geospatial narrative spread

### Current Recommendation

Wait for details.

---

## 8.5 Overshoot AI

### Fit

Unknown.

Current recommendation:

Wait for details.

---

## 8.6 Fieldguide

### Fit

Unknown, possibly audit/compliance.

Possible angles:

- evidence audit trails
- report provenance
- source verification
- compliance-style investigation records

### Current Recommendation

Could be relevant if Fieldguide’s track rewards auditability or evidence workflows.

---

## 9. Sponsors To Probably Skip

## 9.1 QNX

### Fit

**2/10**

QNX is likely embedded/automotive/real-time systems oriented.

RhetoriQ is a civic AI web platform, so the connection is weak.

### Recommendation

Skip unless QNX announces a software/AI challenge that unexpectedly fits.

---

## 9.2 Ultimate Bots

### Fit

**2/10**

Ultimate Bots is about robotics/physical AI and humanoid policies.

RhetoriQ does not naturally involve robotics.

### Recommendation

Skip.

---

## 10. Best Track Submission Strategy

Submit RhetoriQ to:

1. **Ddoski’s World**
   - Primary track.
   - Strongest social-impact/civic-tech fit.

2. **Most Technical Hack**
   - If graph, Redis, multi-agent workflow, and report pipeline are polished.

3. **Best UI/UX**
   - If timeline, family tree, graph, receipts, and report UI are clean.

4. **Fetch AI**
   - If Agentverse / ASI:One integration works.

5. **Redis**
   - If vector search, semantic cache, phrase counters, or memory are clearly implemented.

6. **Anthropic**
   - If the agent system and report generation are central and safe.

7. **Arize**
   - If evals/traces are working.

8. **Browserbase**
   - If source verification is visible.

9. **Band**
   - If multi-agent room is implemented.

10. **Deepgram**
   - If speech/transcript ingestion is implemented.

11. **Sentry**
   - If monitoring is added.

12. **SkyDeck**
   - If pitching startup potential: journalists, researchers, NGOs, civic orgs.

---

## 11. Sponsor Integration Depth Plan

## 11.1 Minimum Strong Sponsor Set

If the team is short on time, do this:

```text
Anthropic + Redis + Arize
```

Why:

- Anthropic powers core report.
- Redis powers core retrieval/memory.
- Arize proves responsible AI/evaluation.

## 11.2 Best Balanced Sponsor Set

Target this:

```text
Anthropic + Redis + Fetch AI + Arize + Browserbase
```

Why:

- Covers AI reasoning, memory, agent distribution, trust/evals, evidence verification.

## 11.3 Maximum Stretch Sponsor Set

If the team is moving fast:

```text
Anthropic + Redis + Fetch AI + Arize + Browserbase + Band + Deepgram + Sentry
```

Why:

- Adds multi-agent rooms, speech ingestion, and reliability monitoring.

---

## 12. Sponsor Demo Lines

Use these in the final pitch.

### Anthropic

> Anthropic powers the investigation agents that reason over sources, challenge overclaims, and generate the final source-grounded civic intelligence report.

### Redis

> Redis acts as RhetoriQ’s real-time narrative memory layer, powering vector search, semantic cache, phrase spike counters, and agent memory.

### Fetch AI

> Fetch AI lets us package RhetoriQ as a discoverable civic intelligence agent that users can query directly through the agent ecosystem.

### Arize

> Arize evaluates whether each report is grounded in retrieved evidence and helps catch hallucinations or unsupported claims.

### Browserbase

> Browserbase lets our agent verify source pages and collect evidence for clickable receipts.

### Band

> Band helps coordinate a room of specialized agents that investigate, debate, verify, and safely summarize a political narrative.

### Deepgram

> Deepgram lets RhetoriQ detect when online narratives move into spoken political media like speeches, debates, and hearings.

### Sentry

> Sentry gives us production-style monitoring for failures across the ingestion, agent, and report pipeline.

### Orkes

> Orkes can orchestrate the full investigation workflow from query to retrieval to source verification to final report.

---

## 13. Sponsor Feature Mapping

| RhetoriQ Feature | Best Sponsor Fit |
|---|---|
| Ask RhetoriQ | Anthropic, Redis, Fetch AI |
| Live Narrative Radar | Redis, Anthropic |
| Narrative Spike Detection | Redis |
| Narrative Family Tree | Anthropic, Redis |
| Counter-Narrative Detection | Anthropic, Redis |
| Receipts Mode | Browserbase, Arize, Anthropic |
| Source Diversity Panel | Anthropic, Arize |
| Multi-Agent Room | Fetch AI, Band, Anthropic |
| Agent Debate | Anthropic, Band, Arize |
| Source Verification | Browserbase |
| Speech/Transcript Ingestion | Deepgram |
| Error Monitoring | Sentry |
| Workflow Orchestration | Orkes |
| Public Agent Access | Fetch AI |
| Demo/Build Acceleration | Simular, Cognition |
| Civic Explainer Video | Pika |

---

## 14. Product Pitch With Sponsor Stack

Use this as a polished sponsor-aware pitch:

```text
RhetoriQ is an AI narrative detective for civic and political information. Users can ask about any political story or click a live narrative spike, and RhetoriQ traces how the story emerged, evolved, spread, and competed with counter-narratives. Redis powers the real-time narrative memory, vector search, semantic cache, and phrase spike counters. Anthropic powers the multi-agent investigation, debate, and report generation. Browserbase verifies source pages for clickable receipts. Arize evaluates source grounding and hallucination risk. Fetch AI exposes RhetoriQ as a discoverable civic intelligence agent that users can query directly.
```

---

## 15. Sponsor Risk Management

### Risk: Too many sponsor integrations

Problem:

```text
The app feels like sponsor-sticker soup.
```

Solution:

```text
Use 3–5 deeply and explain exactly why each matters.
```

### Risk: Sponsor feature breaks demo

Problem:

```text
A live integration fails during judging.
```

Solution:

```text
Have static fallback data and pre-generated reports.
```

### Risk: Integration is shallow

Problem:

```text
We mention a sponsor but it does not affect the product.
```

Solution:

```text
Only claim sponsor usage where it powers a visible feature.
```

### Risk: Sponsor use distracts from civic impact

Problem:

```text
Judges remember tools, not the problem.
```

Solution:

```text
Lead with civic narrative investigation. Mention tools after product value is clear.
```

---

## 16. Sponsor Implementation Checklist

### Anthropic

- [ ] Query Planner Agent works.
- [ ] Analyst Agent produces draft report.
- [ ] Skeptic Agent softens overclaims.
- [ ] Final Report Generator works.
- [ ] Output is structured JSON.

### Redis

- [ ] Documents are embedded or indexed.
- [ ] Vector/semantic search works.
- [ ] Phrase counters or spike scores work.
- [ ] Semantic cache or memory exists.
- [ ] Dashboard can retrieve narrative cards.

### Fetch AI

- [ ] RhetoriQ agent is registered.
- [ ] Agent accepts a user prompt.
- [ ] Agent returns report summary.
- [ ] Agent returns report link.

### Arize

- [ ] Agent traces are logged (query, context packet, Analyst draft, Skeptic revision, final report).
- [ ] Grounding eval runs on Analyst draft and returns a score.
- [ ] Overclaim flag triggers Skeptic Agent revision when score is below threshold.
- [ ] Grounding eval runs again on Skeptic revision.
- [ ] Before/after scores are visible in the UI or demo.

### Browserbase

- [ ] At least 3–5 source URLs are visited per report.
- [ ] Live title/date/snippet is extracted and compared to stored metadata.
- [ ] Receipt status is set: `browser_verified`, `source_updated`, or `source_unavailable`.
- [ ] All three status states are displayed honestly in Receipts Mode UI.
- [ ] Ingestion timestamp is shown on unavailable receipts.

### Band

- [ ] Multi-agent room is created or simulated.
- [ ] Agents exchange context.
- [ ] Debate output appears in UI.

### Deepgram

- [ ] Audio clip is transcribed.
- [ ] Transcript is added to dataset.
- [ ] Transcript appears in timeline.

### Sentry

- [ ] Frontend is instrumented.
- [ ] Backend is instrumented.
- [ ] Errors include investigation context.

### Orkes

- [ ] Investigation workflow is modeled.
- [ ] Workflow steps match pipeline.
- [ ] Status can be shown in UI or logs.

---

## 17. Recommended Priority During Build

Build in this exact order:

1. Core product demo with seeded data.
2. Anthropic report generation.
3. Redis retrieval/memory.
4. Receipts Mode.
5. Arize eval/tracing.
6. Browserbase source verification.
7. Fetch AI discoverable agent.
8. Band multi-agent room.
9. Sentry.
10. Deepgram.
11. Orkes.
12. Pika/Midjourney/other optional polish.

Why?

Because a working civic investigation product matters more than many shallow integrations.

---

## 18. Final Recommendation

The sponsor strategy should be:

```text
Go deep on Anthropic + Redis + Fetch AI + Arize + Browserbase.
Add Band, Deepgram, and Sentry only if core demo is stable.
Do not force unrelated sponsors.
```

The best sponsor-aligned product message is:

> RhetoriQ combines real-time narrative memory, source-grounded AI investigation, agent debate, evidence verification, and discoverable agent access to help people understand how political stories emerge and spread.

This sponsor strategy makes RhetoriQ competitive for:

- Ddoski’s World
- Most Technical Hack
- Best UI/UX
- Fetch AI
- Redis
- Anthropic
- Arize
- Browserbase
- Band
- Deepgram
- Sentry
- SkyDeck
