# RhetoriQ Agent System

**Document purpose:** Define the multi-agent investigation architecture for RhetoriQ.  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`, `DATA_SCHEMA.md`  
**Audience:** AI/agent engineers, backend engineers, sponsor integration owners, judges, mentors, and AI coding agents.

---

## 1. Agent System Summary

RhetoriQ is not a single chatbot. It is a multi-agent civic investigation system.

The goal of the agent system is to transform either:

1. a user’s natural language question, or
2. a live detected narrative spike,

into a source-grounded investigation report with:

- relevant sources
- timeline of spread
- narrative family tree
- counter-narratives
- source diversity analysis
- graph of relationships
- agent debate
- confidence and limitations
- clickable receipts for every major claim

The agent system should behave like a small investigation team:

```text
User prompt or live spike
        ↓
Query Planner Agent
        ↓
Retriever Agent
        ↓
Timeline Agent
        ↓
Graph Agent
        ↓
Narrative Family Agent
        ↓
Counter-Narrative Agent
        ↓
Source Diversity Agent
        ↓
Analyst Agent
        ↓
Skeptic Agent
        ↓
Receipts Agent
        ↓
Safety / Grounding Agent
        ↓
Final Report
```

The most important design principle:

> RhetoriQ agents should not just generate answers. They should investigate, challenge, verify, and cite evidence.

---

## 2. Why Multi-Agent?

RhetoriQ uses a multi-agent system because the task is too sensitive and complex for one generic LLM response.

Political narrative investigation requires:

- retrieval
- timeline reasoning
- graph reasoning
- narrative classification
- counter-narrative detection
- uncertainty handling
- source grounding
- claim verification
- cautious language

A single model call can easily overclaim. The multi-agent system reduces that risk by separating responsibilities.

### Benefits

1. **Better product quality**
   - Each agent has a focused job.

2. **Better safety**
   - The Skeptic Agent and Safety/Grounding Agent challenge unsupported claims.

3. **Better explainability**
   - Users can see how the investigation was built.

4. **Better sponsor alignment**
   - Fetch AI and Band naturally fit multi-agent workflows.
   - Anthropic powers reasoning and report generation.
   - Arize can monitor each agent step.
   - Redis can provide memory and retrieval.
   - Browserbase can verify sources.

5. **Better demo**
   - The “Agent Debate” panel is memorable and shows responsible AI.

---

## 3. Agent List

RhetoriQ should support these agents:

| Agent | Purpose | Priority |
|---|---|---|
| Query Planner Agent | Converts user prompt into investigation plan | P0 |
| Retriever Agent | Finds relevant documents and evidence | P0 |
| Analyst Agent | Drafts investigation report | P0 |
| Receipts Agent | Maps report claims to clickable evidence | P0 |
| Safety / Grounding Agent | Removes unsupported or unsafe claims | P0 |
| Timeline Agent | Builds chronological spread timeline | P1 |
| Graph Agent | Builds source/document relationship graph | P1 |
| Narrative Family Agent | Builds narrative family tree | P1 |
| Counter-Narrative Agent | Finds competing frames | P1 |
| Source Diversity Agent | Summarizes source ecosystem | P1 |
| Skeptic Agent | Challenges overclaims before final report | P1 |
| Radar Agent | Detects live narrative spikes | P1/P2 depending on scope |

---

## 4. Shared Agent Rules

All agents must follow these rules:

1. Use only retrieved or provided evidence.
2. Do not fabricate sources.
3. Do not fabricate URLs.
4. Do not claim absolute origin.
5. Use “first observed in our dataset.”
6. Distinguish observed facts from inference.
7. Avoid defamatory language.
8. Avoid unsupported accusations.
9. Avoid declaring political content true or false unless that is explicitly supported by verified external evidence.
10. Prefer cautious language.
11. Include uncertainty.
12. Preserve clickable source links.
13. Every major claim in the final report must have receipts.
14. If evidence is insufficient, say so.
15. If source diversity labels are uncertain, mark them as unknown.

---

## 5. Agent I/O Contract

Each agent should receive structured input and return structured output.

### Standard Agent Input

```json
{
  "query": {},
  "investigation_plan": {},
  "documents": [],
  "sources": [],
  "narrative_clusters": [],
  "counter_narratives": [],
  "timeline": [],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "source_diversity": {},
  "prior_agent_outputs": [],
  "safety_rules": []
}
```

### Standard Agent Output

```json
{
  "agent_role": "analyst_agent",
  "status": "completed",
  "summary": "Short human-readable summary of what this agent did.",
  "output": {},
  "cited_document_ids": [],
  "cited_receipt_ids": [],
  "warnings": [],
  "confidence_score": 0.75,
  "confidence_label": "medium"
}
```

### Error Output

```json
{
  "agent_role": "retriever_agent",
  "status": "failed",
  "summary": "Could not retrieve enough relevant sources.",
  "output": {},
  "warnings": [
    "Insufficient source coverage."
  ],
  "confidence_score": 0.0,
  "confidence_label": "low"
}
```

---

## 6. Agent Definitions

## 6.1 Radar Agent

### Purpose

The Radar Agent monitors source streams and identifies emerging narrative spikes.

It powers Live Narrative Radar.

### Inputs

- recent documents
- phrase counts
- entity counts
- historical baseline
- Redis counters
- prior narrative clusters

### Outputs

- candidate narrative spikes
- canonical phrase
- related phrases
- spike score
- first observed document
- status estimate
- confidence

### Output Shape

```json
{
  "candidate_spikes": [
    {
      "canonical_phrase": "hidden energy tax",
      "related_phrases": ["utility bill surcharge", "green mandate costs"],
      "spike_score": 7.4,
      "first_observed_doc_id": "doc_001",
      "source_count": 26,
      "status": "amplifying",
      "confidence_score": 0.71,
      "confidence_label": "medium"
    }
  ]
}
```

### Rules

- Do not call a spike “coordinated.”
- Only report that a phrase or concept is increasing.
- Leave interpretation to later agents.

---

## 6.2 Query Planner Agent

### Purpose

The Query Planner Agent converts a user’s natural language question into a structured investigation plan.

### Example Input

```text
Where did the hidden energy tax narrative come from?
```

### Responsibilities

- identify topic
- identify canonical phrase
- extract entities
- infer user intent
- decide search queries
- decide semantic queries
- decide output requirements
- include safety notes

### Output Shape

```json
{
  "topic": "energy policy",
  "canonical_phrase": "hidden energy tax",
  "intent": "trace_origin_and_spread",
  "entities": ["energy", "tax", "policy"],
  "search_queries": [
    "\"hidden energy tax\"",
    "\"energy tax\" \"working families\""
  ],
  "semantic_queries": [
    "political framing around energy policy as hidden household tax"
  ],
  "requested_outputs": [
    "timeline",
    "family_tree",
    "counter_narratives",
    "source_diversity",
    "graph",
    "report",
    "receipts"
  ],
  "safety_notes": [
    "Use first observed in our dataset.",
    "Do not claim absolute origin.",
    "Avoid unsupported coordination claims."
  ]
}
```

### Rules

- Do not answer the user directly.
- Only produce an investigation plan.
- Include safety notes for political content.
- Prefer broad enough queries to retrieve counter-narratives.

---

## 6.3 Retriever Agent

### Purpose

The Retriever Agent finds relevant documents for the investigation.

### Responsibilities

- run keyword search
- run semantic search
- retrieve from Redis vector index
- retrieve prior investigations from memory
- deduplicate near-identical documents
- preserve source metadata and URLs

### Inputs

- investigation plan
- documents or source index
- Redis vector search
- prior investigations

### Outputs

- relevant documents
- possible duplicates
- missing-data warnings
- retrieval confidence

### Output Shape

```json
{
  "retrieved_document_ids": ["doc_001", "doc_002", "doc_003"],
  "high_relevance_document_ids": ["doc_001", "doc_002"],
  "possible_duplicate_pairs": [
    {
      "doc_a": "doc_002",
      "doc_b": "doc_005",
      "similarity": 0.93
    }
  ],
  "retrieval_notes": [
    "Retrieved documents include main narrative and counter-narrative examples."
  ],
  "warnings": [
    "Dataset may not include earlier social posts."
  ],
  "confidence_score": 0.78,
  "confidence_label": "medium"
}
```

### Rules

- Preserve source URLs.
- Do not summarize beyond what the documents support.
- Mark low evidence coverage clearly.

---

## 6.4 Timeline Agent

### Purpose

The Timeline Agent builds a chronological sequence showing how the narrative spread.

### Responsibilities

- sort documents by timestamp
- identify first observed source
- identify early amplification
- identify mainstream pickup
- identify official/transcript mentions
- identify counter-narrative appearances

### Outputs

- timeline events
- first observed source
- timeline limitations
- confidence

### Output Shape

```json
{
  "timeline_events": [
    {
      "id": "event_001",
      "document_id": "doc_001",
      "timestamp": "2026-06-20T09:14:00Z",
      "event_type": "first_observed",
      "narrative_side": "main",
      "explanation": "Earliest observed use of the canonical phrase in the dataset."
    }
  ],
  "first_observed_doc_id": "doc_001",
  "limitations": [
    "First observed source may not be the true origin."
  ],
  "confidence_score": 0.82,
  "confidence_label": "high"
}
```

### Rules

- Always say “first observed.”
- Do not imply absolute origin.
- If timestamps are missing, downgrade confidence.

---

## 6.5 Graph Agent

### Purpose

The Graph Agent builds the narrative spread graph.

### Responsibilities

- create document/source/narrative nodes
- create edges between related documents
- identify relationship types
- score relationship strength
- link edges to receipts where possible

### Edge Types

- semantic similarity
- exact phrase reuse
- shared entity
- source link
- reposting
- quote reuse
- temporal sequence
- counter-narrative relationship
- family-child relationship

### Output Shape

```json
{
  "nodes": [
    {
      "id": "node_doc_001",
      "label": "Local Energy Watch",
      "node_type": "document",
      "ref_id": "doc_001"
    }
  ],
  "edges": [
    {
      "id": "edge_001",
      "source_node_id": "node_doc_001",
      "target_node_id": "node_doc_002",
      "edge_type": "exact_phrase_reuse",
      "weight": 0.82,
      "evidence_text": "Both documents use the phrase 'hidden energy tax'."
    }
  ],
  "graph_summary": "The graph suggests early local/blog discussion followed by broader media pickup.",
  "confidence_score": 0.74,
  "confidence_label": "medium"
}
```

### Rules

- Edge explanations must be evidence-based.
- Do not infer hidden coordination from edges alone.
- Graph should remain readable for the demo.

---

## 6.6 Narrative Family Agent

### Purpose

The Narrative Family Agent groups related narratives into parent-child relationships.

### Responsibilities

- identify parent narrative frame
- identify child narrative clusters
- identify related phrases
- explain how the current narrative fits into the broader family

### Output Shape

```json
{
  "family": {
    "title": "Climate Policy Cost Narrative",
    "parent_frame": "climate policy as household cost burden",
    "child_narratives": [
      "hidden energy tax",
      "utility bill surcharge",
      "green mandate costs",
      "war on appliances"
    ],
    "summary": "The hidden energy tax narrative is part of a broader family that frames climate and energy policy through household cost and government overreach."
  },
  "confidence_score": 0.70,
  "confidence_label": "medium"
}
```

### Rules

- Do not overfit unrelated phrases into one family.
- Explain uncertainty if family grouping is weak.
- Treat family tree as semantic framing, not proof of coordination.

---

## 6.7 Counter-Narrative Agent

### Purpose

The Counter-Narrative Agent identifies competing or opposing frames.

### Responsibilities

- find documents that frame the same issue differently
- identify counter-phrases
- compare growth and source types
- summarize both sides neutrally

### Output Shape

```json
{
  "counter_narratives": [
    {
      "title": "Long-Term Energy Savings Narrative",
      "summary": "A counter-frame arguing that the policy funds infrastructure and lowers long-term costs.",
      "related_phrases": ["long-term savings", "grid modernization", "infrastructure investment"],
      "document_ids": ["doc_010", "doc_011"],
      "first_observed_doc_id": "doc_010",
      "confidence_score": 0.68,
      "confidence_label": "medium"
    }
  ],
  "notes": [
    "Counter-narratives appear later than the main narrative in this dataset."
  ]
}
```

### Rules

- Do not decide which side is true.
- Represent counter-narratives fairly.
- If no counter-narrative is found, say so.

---

## 6.8 Source Diversity Agent

### Purpose

The Source Diversity Agent summarizes what kinds of sources are involved.

### Responsibilities

- count source types
- summarize local vs national
- summarize official vs unofficial
- summarize independent vs advocacy
- summarize original reporting vs reposting
- summarize ideology labels only if available

### Output Shape

```json
{
  "source_diversity": {
    "total_sources": 26,
    "ideology_distribution": {
      "left": 4,
      "center": 6,
      "right": 7,
      "unknown": 9
    },
    "geographic_distribution": {
      "local": 8,
      "state": 2,
      "national": 10,
      "international": 1,
      "unknown": 5
    },
    "source_type_distribution": {
      "blog": 4,
      "local_news": 8,
      "national_news": 6,
      "official_statement": 3,
      "community_post": 5
    }
  },
  "notes": [
    "Source diversity describes the observed dataset, not the entire media ecosystem."
  ],
  "limitations": [
    "Ideology labels are incomplete and should not be treated as truth labels."
  ]
}
```

### Rules

- Do not assign ideology if unavailable.
- Do not call sources good or bad.
- Frame this as context, not judgment.

---

## 6.9 Analyst Agent

### Purpose

The Analyst Agent drafts the main investigation report.

### Responsibilities

- synthesize evidence
- summarize narrative
- explain timeline
- explain family tree
- include counter-narratives
- include source diversity
- propose spread pattern
- include confidence and caveats

### Output Shape

```json
{
  "draft_report": {
    "title": "Hidden Energy Tax Narrative Investigation",
    "executive_summary": "In the observed dataset, the phrase first appears in local commentary before spreading to community posts and broader media coverage.",
    "spread_pattern": "reactive_amplification",
    "observed_facts": [],
    "reasonable_inferences": [],
    "uncertainties": [],
    "limitations": [],
    "recommended_human_checks": []
  },
  "claims": [
    {
      "claim_text": "The phrase first appears in the observed dataset in a local blog post at 9:14 AM.",
      "claim_type": "observed_fact",
      "required_evidence": true
    }
  ]
}
```

### Rules

- Draft claims must be evidence-grounded.
- Use cautious language.
- Include uncertainties.
- Do not publish directly; output must go to Skeptic Agent and Receipts Agent.

---

## 6.10 Skeptic Agent

### Purpose

The Skeptic Agent challenges the Analyst Agent’s draft.

### Responsibilities

- identify overclaims
- identify weak evidence
- identify missing caveats
- identify unsupported coordination claims
- recommend softer language
- flag claims that need receipts

### Output Shape

```json
{
  "overclaims_found": [
    {
      "claim": "The narrative was coordinated by advocacy groups.",
      "problem": "Evidence does not establish intent or coordination.",
      "recommended_revision": "The pattern shows signals consistent with coordinated amplification, but evidence is insufficient for a definitive conclusion."
    }
  ],
  "missing_caveats": [
    "Dataset may not include earlier sources."
  ],
  "claims_to_remove": [
    "Specific actors intentionally coordinated the narrative."
  ],
  "claims_to_soften": [
    "The narrative appears coordinated."
  ],
  "confidence_score": 0.76,
  "confidence_label": "medium"
}
```

### Rules

- Be strict.
- Prefer removing unsafe claims.
- Do not add new unsupported claims.
- Focus on evidence quality and political-safety risk.

---

## 6.11 Receipts Agent

### Purpose

The Receipts Agent ensures every major report claim has clickable evidence.

### Responsibilities

- identify major claims
- map claims to source documents
- extract quotes/snippets
- preserve URLs
- mark unsupported claims
- generate receipt objects

### Output Shape

```json
{
  "claims": [
    {
      "id": "claim_001",
      "claim_text": "The phrase first appears in the observed dataset in a Local Energy Watch article at 9:14 AM.",
      "support_status": "supported",
      "receipt_ids": ["receipt_001"]
    }
  ],
  "receipts": [
    {
      "id": "receipt_001",
      "claim_id": "claim_001",
      "document_id": "doc_001",
      "source_name": "Local Energy Watch",
      "url": "https://example.com/local-energy-watch",
      "published_at": "2026-06-20T09:14:00Z",
      "quote_or_snippet": "Critics are calling the proposal a hidden energy tax...",
      "support_reason": "Earliest observed source in the dataset using the phrase."
    }
  ],
  "unsupported_claims": [
    "The campaign was intentionally coordinated."
  ]
}
```

### Rules

- Every major claim needs receipts.
- If no receipt exists, mark the claim unsupported.
- Unsupported claims should not appear as confident statements in final report.
- Links must remain clickable in UI.

---

## 6.12 Safety / Grounding Agent

### Purpose

The Safety / Grounding Agent performs the final review before publication.

### Responsibilities

- verify that claims are supported
- verify receipts exist
- verify no defamatory/unsupported accusation exists
- verify uncertainty is included
- verify “first observed” language is used
- verify counter-narratives are represented fairly
- verify source diversity is contextual, not judgmental

### Output Shape

```json
{
  "passed": true,
  "issues_found": [],
  "required_revisions": [],
  "final_safety_notes": [
    "Report uses cautious language.",
    "Report includes receipts and uncertainty.",
    "Report does not claim absolute origin or definitive coordination."
  ]
}
```

### If Failed

```json
{
  "passed": false,
  "issues_found": [
    "Report claims coordination without enough evidence."
  ],
  "required_revisions": [
    "Replace 'coordinated campaign' with 'signals consistent with coordinated amplification'."
  ],
  "final_safety_notes": []
}
```

### Rules

- This agent has veto power.
- Unsafe report drafts should be revised before display.
- Final report should not publish if it fails grounding checks.

---

## 7. Agent Debate Flow

The Agent Debate happens after the Analyst Agent creates a draft and before the final report is shown.

### Debate Participants

Required:

- Analyst Agent
- Skeptic Agent
- Receipts Agent
- Safety / Grounding Agent

Optional:

- Counter-Narrative Agent
- Source Diversity Agent
- Graph Agent

### Debate Steps

```text
1. Analyst Agent proposes interpretation.
2. Skeptic Agent challenges overclaims.
3. Receipts Agent checks which claims have evidence.
4. Counter-Narrative Agent checks whether competing frames are missing.
5. Source Diversity Agent checks whether source context is overstated.
6. Safety / Grounding Agent decides what language is safe.
7. Final report is revised.
```

### Example Debate

```text
Analyst Agent:
“This appears to show possible coordinated amplification.”

Skeptic Agent:
“The evidence is not strong enough to call it coordinated. We only have repeated language and a short time window.”

Receipts Agent:
“The exact phrase reuse is supported by three sources. The intent claim is unsupported.”

Counter-Narrative Agent:
“There is a competing narrative about long-term savings that should be included.”

Safety / Grounding Agent:
“Use cautious language and include limitations.”

Final Decision:
“The pattern shows signals consistent with coordinated amplification, but the evidence is insufficient to make a definitive claim.”
```

---

## 8. Final Report Generation Flow

The final report should be generated only after agent debate and receipts verification.

### Flow

```text
InvestigationQuery
        ↓
InvestigationPlan
        ↓
Retrieved Documents
        ↓
Timeline + Graph + Family Tree + Counter-Narratives + Source Diversity
        ↓
Analyst Draft
        ↓
Skeptic Review
        ↓
Receipts Mapping
        ↓
Safety / Grounding Review
        ↓
Final Report
```

### Final Report Must Include

- title
- user question or detected spike
- executive summary
- first observed source
- narrative family
- counter-narratives
- timeline summary
- source diversity summary
- spread pattern
- agent debate summary
- observed facts
- reasonable inferences
- uncertainties
- rejected or unsupported claims
- limitations
- recommended human checks
- receipts

---

## 9. Agent Memory

Redis can be used for agent memory.

### Memory Types

1. **Narrative memory**
   - prior narrative clusters
   - related phrases
   - family tree relationships

2. **Investigation memory**
   - prior user investigations
   - prior reports
   - prior receipts

3. **Semantic cache**
   - repeated or similar queries
   - cached retrieval results
   - cached report outputs

4. **Source memory**
   - known source metadata
   - known source type labels
   - known source reliability/context notes, if available

### Rules

- Agent memory should improve retrieval and consistency.
- Agent memory should not override current evidence.
- If prior memory is used, disclose that it came from prior investigations.
- Do not store sensitive personal information.

---

## 10. Sponsor Integration Mapping

## 10.1 Anthropic

Anthropic powers:

- Query Planner Agent
- Analyst Agent
- Skeptic Agent
- Receipts Agent
- Safety / Grounding Agent
- final report generation

### Sponsor Demo Line

```text
Anthropic powers the agents that reason over evidence, challenge overclaims, and generate the final source-grounded civic intelligence report.
```

---

## 10.2 Redis

Redis powers:

- vector retrieval for Retriever Agent
- semantic cache
- phrase spike counters for Radar Agent
- narrative memory
- prior investigation memory

### Sponsor Demo Line

```text
Redis acts as RhetoriQ’s real-time narrative memory layer: vector search, semantic cache, spike counters, and agent memory.
```

---

## 10.3 Fetch AI

Fetch AI can expose RhetoriQ as a discoverable agent.

Possible agent:

```text
RhetoriQ Narrative Investigator Agent
```

Capabilities:

- accept a political story prompt
- return top evidence
- return narrative summary
- return report link
- expose query through Agentverse / ASI:One

### Sponsor Demo Line

```text
Fetch AI lets us package RhetoriQ as a discoverable civic intelligence agent that users can query directly.
```

---

## 10.4 Band

Band can support:

- shared multi-agent rooms
- context exchange
- collaborative debate
- visible investigation room

### Sponsor Demo Line

```text
Band helps us coordinate a room of specialized agents that investigate, debate, and verify political narratives.
```

---

## 10.5 Arize

Arize monitors:

- agent traces
- retrieval quality
- report quality
- source grounding
- hallucination risk
- unsupported claims

### Sponsor Demo Line

```text
Arize tracks our agent pipeline and evaluates whether report claims are grounded in retrieved evidence.
```

---

## 10.6 Browserbase

Browserbase supports:

- source-page verification
- title/date/author extraction
- source evidence checking
- provenance capture

### Sponsor Demo Line

```text
Browserbase lets our agent verify source pages and collect evidence behind the receipts.
```

---

## 11. Minimal Hackathon Implementation

If time is limited, implement the agent system in simplified form.

### Minimum Agent Set

1. Query Planner Agent
2. Retriever Agent
3. Analyst Agent
4. Skeptic Agent
5. Receipts Agent
6. Safety / Grounding Agent

### Simulated Agents Are Acceptable

For a hackathon, it is acceptable to simulate some agents as structured function calls or prompt sections, as long as the output is clear and honest.

Example:

```text
One Anthropic call can produce multiple agent sections:
- Analyst draft
- Skeptic critique
- Receipts check
- Safety decision
```

This is acceptable for demo purposes if the UI and report clearly show the multi-step reasoning structure.

---

## 12. Implementation Options

## 12.1 Simple Custom Workflow

Best for hackathon reliability.

```python
plan = query_planner(user_query)
docs = retriever(plan)
timeline = timeline_agent(docs)
graph = graph_agent(docs)
family = narrative_family_agent(docs)
counter = counter_narrative_agent(docs)
diversity = source_diversity_agent(docs)
draft = analyst_agent(...)
debate = skeptic_and_receipts_review(draft, docs)
final = safety_grounding_agent(debate)
```

Pros:

- easiest to control
- easiest to debug
- easiest to demo

Cons:

- less “agent platform” native

---

## 12.2 LangGraph-Style Workflow

Good if the team wants explicit agent nodes.

```text
Query Planner Node
Retriever Node
Timeline Node
Graph Node
Family Node
Counter-Narrative Node
Diversity Node
Analyst Node
Skeptic Node
Receipts Node
Safety Node
Final Report Node
```

Pros:

- clean graph structure
- easier to explain as multi-agent
- useful for complex branching

Cons:

- more setup

---

## 12.3 Fetch / Band Native Workflow

Good if sponsor criteria reward agent registration or multi-agent rooms.

Pros:

- strong sponsor fit
- discoverable agent story
- visible agent collaboration

Cons:

- tool setup may take time
- may be less reliable than custom workflow

---

## 13. Agent State Machine

Each investigation can be represented as a state machine.

```text
created
  ↓
planning
  ↓
retrieving
  ↓
analyzing_timeline
  ↓
building_graph
  ↓
finding_family
  ↓
finding_counter_narratives
  ↓
analyzing_source_diversity
  ↓
drafting_report
  ↓
debating
  ↓
checking_receipts
  ↓
safety_review
  ↓
completed
```

Failure states:

```text
failed_retrieval
failed_report_generation
failed_safety_check
insufficient_evidence
```

---

## 14. Investigation Status Object

Use this object to show progress in the UI.

```json
{
  "investigation_id": "query_001",
  "status": "checking_receipts",
  "steps": [
    {
      "name": "Planning investigation",
      "status": "completed"
    },
    {
      "name": "Retrieving sources",
      "status": "completed"
    },
    {
      "name": "Building timeline",
      "status": "completed"
    },
    {
      "name": "Finding counter-narratives",
      "status": "completed"
    },
    {
      "name": "Debating evidence",
      "status": "running"
    },
    {
      "name": "Checking receipts",
      "status": "pending"
    }
  ]
}
```

---

## 15. Final Report Safety Checklist

Before displaying a final report, confirm:

- [ ] Report says “first observed in our dataset.”
- [ ] Report does not claim absolute origin.
- [ ] Report does not claim definitive coordination unless evidence is extremely strong.
- [ ] Report does not label content fake/propaganda without external verification.
- [ ] Every major claim has receipts.
- [ ] Unsupported claims are removed or marked unsupported.
- [ ] Counter-narratives are included if available.
- [ ] Source diversity is framed as context, not truth.
- [ ] Limitations are included.
- [ ] Human review checks are included.
- [ ] Links are clickable.
- [ ] Agent debate summary is visible.

---

## 16. Example End-to-End Agent Run

### User Query

```text
Where did the hidden energy tax narrative come from?
```

### Query Planner Agent

```text
Identify canonical phrase: hidden energy tax.
Search related phrases: utility bill surcharge, green mandate costs.
Need outputs: timeline, graph, family tree, counter-narratives, source diversity, report, receipts.
```

### Retriever Agent

```text
Found 26 related documents.
High relevance: 11.
Counter-narrative candidates: 5.
```

### Timeline Agent

```text
First observed in dataset: Local Energy Watch at 9:14 AM.
Early amplification: Community Post B at 10:02 AM.
Mainstream pickup: News Outlet C at 10:47 AM.
Official mention: Public transcript at 1:20 PM.
```

### Narrative Family Agent

```text
Parent family: Climate Policy Cost Narrative.
Child narratives: hidden energy tax, utility bill surcharge, green mandate costs, war on appliances.
```

### Counter-Narrative Agent

```text
Counter-narrative: long-term energy savings / infrastructure investment.
```

### Source Diversity Agent

```text
Sources include local blogs, community posts, national news, official statements, and advocacy content.
Ideology labels are incomplete.
```

### Analyst Agent

```text
Draft interpretation: reactive amplification with possible coordination signals.
```

### Skeptic Agent

```text
Coordination claim is too strong. Evidence supports similar wording and rapid spread, but not intent.
```

### Receipts Agent

```text
Mapped 7 major claims to receipts.
Removed 1 unsupported claim.
```

### Safety / Grounding Agent

```text
Final report passed after softening coordination language.
```

### Final Output

```text
The phrase first appears in the observed dataset in local commentary before spreading to community and news sources. The pattern is consistent with reactive amplification and includes some signals of coordinated messaging, but evidence is insufficient for a definitive coordination claim.
```

---

## 17. Agent System Success Criteria

The agent system is successful if:

1. A user prompt becomes a structured investigation.
2. Retrieved evidence supports the report.
3. Timeline and graph are generated.
4. Counter-narratives are included.
5. Source diversity is included.
6. Agents debate the evidence.
7. Unsafe or unsupported claims are softened or removed.
8. Every major claim has receipts.
9. The final report is clear, cautious, and useful.
10. Judges understand this is more than a chatbot.

---

## 18. Next Related File

After this file, create:

```text
AGENT_PROMPTS.md
```

That file should contain the actual prompts for:

- Query Planner Agent
- Retriever Agent
- Timeline Agent
- Graph Agent
- Narrative Family Agent
- Counter-Narrative Agent
- Source Diversity Agent
- Analyst Agent
- Skeptic Agent
- Receipts Agent
- Safety / Grounding Agent
- Final Report Generator
