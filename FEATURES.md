# RhetoriQ Features

**Document purpose:** This file defines the major product features for RhetoriQ in clear product language.  
**Related source-of-truth doc:** `HACKATHON_MVP_SPEC.md`  
**Audience:** teammates, judges, mentors, and AI coding agents

---

## 1. Feature Philosophy

RhetoriQ should not feel like a generic chatbot or a political fact-checker.

It should feel like an **AI-powered civic investigation platform**.

The core product promise is:

> A user can ask about any political story, claim, phrase, or issue, and RhetoriQ will trace how the narrative emerged, evolved, spread, and competed with other narratives — while backing every major claim with clickable evidence.

Every feature should support one of these goals:

1. **Investigate**
   - Help the user ask about any story or click into an emerging narrative.

2. **Trace**
   - Show where the narrative first appeared in the observed dataset and how it spread.

3. **Contextualize**
   - Show related narratives, counter-narratives, source diversity, and the broader narrative family.

4. **Verify**
   - Provide clickable receipts and separate observed facts from AI interpretation.

5. **Stay Responsible**
   - Avoid unsupported accusations, truth scores, or partisan judgments.

---

## 2. Feature Priority Overview

| Priority | Feature | Why It Matters |
|---|---|---|
| P0 | Ask RhetoriQ Investigation Mode | Makes the product useful for any story, not just live alerts |
| P0 | Source-Grounded Investigation Report | Core output of the product |
| P0 | Receipts Mode | Trust layer; every major claim needs clickable evidence |
| P0 | Timeline View | Shows narrative spread in a way judges instantly understand |
| P0 | Interactive Spread Graph | Visualizes relationships and spread paths |
| P1 | Live Narrative Radar | Makes the app feel real-time and proactive |
| P1 | Narrative Family Tree | Shows how stories evolve and mutate |
| P1 | Counter-Narrative Detection | Makes the product balanced and less one-sided |
| P1 | Source Diversity Panel | Replaces simplistic political bias scoring with safer context |
| P1 | Multi-Agent Investigation Room | Makes the AI architecture more impressive and sponsor-friendly |
| P1 | Agent Debate Before Final Report | Adds responsible AI and skepticism |
| P2 | Browser Source Verification | Useful trust booster through Browserbase |
| P2 | Agent Memory / Prior Investigations | Useful through Redis |
| P2 | Speech / Transcript Ingestion | Strong Deepgram extension |
| P2 | Export Investigation Pack | Practical journalist/researcher workflow |
| P3 | Browser Extension | Future product direction |
| P3 | Narrative Lifecycle Stage | Advanced intelligence feature |
| P3 | Geographic Spread Map | Advanced visualization feature |

---

## 3. Product Modes

## 3.1 Ask RhetoriQ Investigation Mode

### Summary

Ask RhetoriQ allows users to type a natural language question about any political story, claim, phrase, event, speech, policy debate, or public issue.

The system turns the prompt into an investigation.

### Example User Prompts

```text
Where did the hidden energy tax narrative come from?
```

```text
Trace the political story behind the TikTok ban.
```

```text
What narratives are forming around immigration this week?
```

```text
Why is everyone suddenly talking about gas stove bans?
```

```text
Find the counter-narratives around this education bill.
```

```text
How did this phrase move from online discussion into mainstream media?
```

### User Flow

1. User enters a natural language prompt.
2. RhetoriQ identifies the topic, phrase, entities, and requested investigation type.
3. RhetoriQ retrieves relevant sources.
4. RhetoriQ clusters sources into narratives and counter-narratives.
5. RhetoriQ builds a timeline, graph, family tree, and source diversity panel.
6. RhetoriQ runs a multi-agent investigation and debate.
7. RhetoriQ produces a final report with clickable receipts.

### UI Requirements

The Ask RhetoriQ input should be highly visible on the homepage.

Suggested placeholder:

```text
Ask about any political story, claim, phrase, or issue...
```

Suggested button:

```text
Investigate
```

After submission, show an investigation loading sequence such as:

```text
Planning investigation...
Retrieving sources...
Building timeline...
Finding counter-narratives...
Checking receipts...
Generating report...
```

### Acceptance Criteria

- User can enter a prompt.
- System returns a structured investigation.
- Report includes timeline, graph, source diversity, counter-narratives, and receipts.
- Output uses cautious language and does not overclaim.

---

## 3.2 Live Narrative Radar

### Summary

Live Narrative Radar surfaces emerging political or civic narratives automatically.

Instead of waiting for a user prompt, the dashboard shows narrative spikes and unusual spread patterns.

### Narrative Card Fields

Each radar card should include:

- narrative title
- short summary
- canonical phrase
- related phrases
- spike score
- source count
- first observed time
- latest observed time
- confidence
- source diversity preview
- “Investigate” button

### Example Card

```text
Hidden Energy Tax
Spike Score: 7.4x
Sources: 26
First observed: 9:14 AM
Status: Amplifying
Source mix: local blogs, advocacy posts, national news
```

### User Flow

1. User opens dashboard.
2. User sees trending or emerging narrative cards.
3. User clicks “Investigate.”
4. User lands on the investigation page.

### Acceptance Criteria

- Dashboard shows at least 3 narrative cards.
- Each card links to an investigation page.
- Each card has enough metadata to feel real.
- At least one card should connect to the full demo narrative.

---

## 4. Core Investigation Features

## 4.1 Source-Grounded Investigation Report

### Summary

The investigation report is the main output of RhetoriQ.

It should read like a concise civic intelligence brief, not like a generic chatbot answer.

### Required Sections

Every report should include:

1. **Executive Summary**
   - Short explanation of the narrative and why it matters.

2. **User Question or Detected Spike**
   - The prompt or radar event that triggered the investigation.

3. **First Observed Source**
   - Earliest source in the observed dataset.
   - Must say “first observed in our dataset,” not absolute origin.

4. **Narrative Family Placement**
   - Parent narrative and related child narratives.

5. **Counter-Narratives**
   - Competing frames or opposing interpretations.

6. **Timeline of Spread**
   - Key chronological events.

7. **Source Diversity Summary**
   - Source type distribution and ecosystem context.

8. **Spread Pattern**
   - Example labels:
     - grassroots
     - reactive amplification
     - top-down
     - influencer-driven
     - potentially coordinated
     - insufficient evidence

9. **Agent Debate Summary**
   - What the Analyst Agent argued.
   - What the Skeptic Agent challenged.
   - What the final decision was.

10. **Confidence and Limitations**
    - Confidence score and caveats.

11. **Recommended Human Checks**
    - What a journalist/researcher should verify next.

12. **Receipts**
    - Clickable evidence for every major claim.

### Acceptance Criteria

- Report is source-grounded.
- Report includes uncertainty.
- Report avoids definitive accusations.
- Every major claim maps to at least one receipt.
- Report separates observed facts from interpretation.

---

## 4.2 Receipts Mode

### Summary

Receipts Mode is the trust layer of RhetoriQ.

Every major AI-generated claim should have supporting evidence that the user can inspect.

### What Counts as a Receipt

A receipt should include:

- claim ID
- claim text
- source title
- source name
- source type
- clickable URL
- timestamp / publication date
- quote or snippet
- support reason

### Example

```text
Claim:
“The phrase appeared in three sources within two hours.”

Receipts:
1. Local Blog A — 9:14 AM — https://example.com/a
2. Community Post B — 10:02 AM — https://example.com/b
3. News Outlet C — 10:47 AM — https://example.com/c
```

### UI Requirements

Each claim in the report should have a “Show receipts” option.

Clicking it should expand evidence cards.

Evidence cards should include clickable links.

### Acceptance Criteria

- Receipts are visible from the report.
- Links are clickable.
- Each receipt explains why it supports the claim.
- Unsupported AI claims should be removed or marked as unsupported.

---

## 4.3 Timeline View

### Summary

The timeline shows how the narrative spread over time.

This is one of the most important demo visuals because it makes the investigation easy to understand.

### Timeline Entry Fields

Each timeline item should include:

- timestamp
- source name
- source type
- title
- snippet
- clickable URL
- role in spread
- narrative branch
- whether it supports main narrative or counter-narrative

### Example Timeline

```text
9:14 AM — Local Blog A — first observed phrase use
10:02 AM — Community Post B — repeated same phrase
10:47 AM — News Outlet C — related framing appears
1:20 PM — Public Speech Transcript — phrase appears in public remarks
```

### UI Requirements

- Chronological vertical timeline.
- Different icons or labels for source types.
- Highlight first observed source.
- Highlight major amplification moments.

### Acceptance Criteria

- Timeline is readable in under 10 seconds.
- First observed source is obvious.
- Clickable links are available.
- Main narrative and counter-narrative events can be distinguished.

---

## 4.4 Interactive Spread Graph

### Summary

The spread graph visualizes relationships between sources, documents, narratives, and counter-narratives.

### Node Types

Nodes can represent:

- documents
- outlets
- speakers
- communities
- organizations
- parent narratives
- child narratives
- counter-narratives

### Edge Types

Edges can represent:

- semantic similarity
- exact phrase reuse
- shared entities
- source linking
- reposting
- quote reuse
- temporal sequence
- counter-narrative relationship

### Example Edge

```json
{
  "source": "doc_001",
  "target": "doc_002",
  "edge_type": "phrase_reuse",
  "weight": 0.82,
  "evidence": "Both sources use the phrase 'hidden energy tax'."
}
```

### UI Requirements

- Nodes should be clickable.
- Clicking a node shows source metadata and snippet.
- Different node types should be visually distinguishable.
- The likely spread path should be highlighted.

### Acceptance Criteria

- Graph renders for the demo narrative.
- Nodes and edges are understandable.
- Clicking nodes reveals source evidence.
- Graph supports the story shown in the timeline and report.

---

## 5. Narrative Context Features

## 5.1 Narrative Family Tree

### Summary

The Narrative Family Tree shows how related political narratives evolve from broader frames.

Instead of treating every phrase as isolated, RhetoriQ groups narratives into parent-child relationships.

### Example

```text
Climate Policy Cost Narrative
├── hidden energy tax
├── gas stove ban
├── war on appliances
├── green mandate costs
└── utility bill surcharge
```

### What the Family Tree Should Show

- parent narrative
- child narratives
- related phrases
- first observed examples
- fastest-growing branch
- most mainstreamed branch
- active vs declining branches

### UI Requirements

- Tree view or graph view.
- Parent narrative at top.
- Child narratives as expandable branches.
- Clicking a branch opens sources and timeline.

### Acceptance Criteria

- At least one demo narrative has a family tree.
- Family tree explains narrative evolution clearly.
- Users can see how the current story relates to older or broader frames.

---

## 5.2 Counter-Narrative Detection

### Summary

Counter-Narrative Detection identifies opposing, competing, or corrective frames around a story.

This prevents RhetoriQ from feeling one-sided.

### Example

Main narrative:

```text
The bill is a hidden energy tax on working families.
```

Counter-narrative:

```text
The bill funds infrastructure and lowers long-term household costs.
```

### What to Show

- main narrative
- counter-narrative
- sources pushing each side
- first observed time for each side
- growth rate for each side
- common phrases for each side
- representative source snippets

### UI Requirements

A side-by-side comparison works well:

```text
Main Narrative              Counter-Narrative
------------------------------------------------
hidden energy tax            long-term savings
working families             infrastructure investment
higher bills                 lower future costs
```

### Acceptance Criteria

- At least one counter-narrative appears in the demo.
- Counter-narrative has source evidence.
- Report includes both sides.
- RhetoriQ does not claim which side is “true” unless externally verified.

---

## 5.3 Bias / Source Diversity Panel

### Summary

The Source Diversity Panel shows what kinds of sources are participating in a narrative.

It should avoid simplistic political bias scoring.

The safer framing is:

> RhetoriQ measures source diversity and spread patterns, not truthfulness or moral correctness.

### Dimensions to Show

If available, show:

- left / center / right / unknown
- local vs national
- official vs unofficial
- independent vs advocacy
- original reporting vs reposting
- news article vs opinion vs transcript vs community post
- source diversity over time

### Example Output

```json
{
  "ideology_distribution": {
    "left": 4,
    "center": 6,
    "right": 7,
    "unknown": 9
  },
  "geographic_distribution": {
    "local": 8,
    "national": 10,
    "international": 1,
    "unknown": 7
  },
  "institutional_distribution": {
    "official": 3,
    "unofficial": 19,
    "advocacy": 4
  },
  "content_type_distribution": {
    "original_reporting": 6,
    "reposting": 9,
    "opinion": 5,
    "transcript": 2,
    "community_post": 4
  }
}
```

### UI Requirements

- Use bar charts, small cards, or simple breakdown lists.
- Include a disclaimer:
  - “Source categories are contextual and may be incomplete.”
- Avoid calling sources “good” or “bad.”

### Acceptance Criteria

- Source diversity panel appears on investigation page.
- It includes at least 3 dimensions.
- It is framed as context, not judgment.
- It does not overclaim ideological classification.

---

## 6. Multi-Agent Features

## 6.1 Multi-Agent Investigation Room

### Summary

RhetoriQ should use multiple specialized agents that collaborate on an investigation.

This makes the AI system more explainable and sponsor-friendly.

### Agents

#### 1. Radar Agent

Detects emerging spikes and narrative clusters.

#### 2. Query Planner Agent

Turns a user prompt into an investigation plan.

#### 3. Retriever Agent

Finds relevant articles, posts, transcripts, and documents.

#### 4. Timeline Agent

Orders sources chronologically and identifies first observed appearances.

#### 5. Graph Agent

Builds the spread graph and explains source relationships.

#### 6. Narrative Family Agent

Groups related narratives into parent-child relationships.

#### 7. Counter-Narrative Agent

Finds opposing or competing frames.

#### 8. Source Diversity Agent

Summarizes source types, source variety, and ecosystem context.

#### 9. Analyst Agent

Writes the first draft of the investigation report.

#### 10. Skeptic Agent

Challenges overclaims and weak evidence.

#### 11. Receipts Agent

Ensures every major claim has clickable evidence.

#### 12. Safety / Grounding Agent

Checks for unsupported claims, defamatory language, overconfidence, and missing uncertainty.

### UI Requirement

The full agent system does not need to be shown in extreme detail. A simple “Investigation Room” panel can show:

- agents involved
- status
- short output from each agent
- final decision

### Acceptance Criteria

- Multi-agent roles are reflected in the backend or simulated clearly.
- Final report includes agent debate summary.
- Skeptic and Receipts agents visibly improve report quality.

---

## 6.2 Agent Debate Before Final Report

### Summary

Before generating the final report, the agents should debate the evidence.

The goal is to reduce overclaiming.

### Example Debate

```text
Analyst Agent:
“This appears to show possible coordinated amplification.”

Skeptic Agent:
“The evidence is not strong enough to call it coordinated. We only have repeated language and a short time window.”

Receipts Agent:
“The exact phrase reuse is supported by three sources. The claim about coordination should be softened.”

Counter-Narrative Agent:
“There is a competing narrative that appeared around the same time and should be included.”

Final Decision:
“Use cautious language: signals consistent with coordinated amplification, but insufficient evidence for a definitive conclusion.”
```

### Debate Output Should Include

- analyst claim
- skeptic critique
- receipts check
- counter-narrative note
- safety/grounding decision
- final phrasing decision

### Acceptance Criteria

- Report includes a visible debate summary.
- Skeptic Agent can soften or reject claims.
- Receipts Agent can flag unsupported claims.
- Final report is more cautious than the first analyst draft.

---

## 7. Trust and Safety Features

## 7.1 Observed Facts vs Inference

Every report should separate:

```text
Observed Facts
Reasonable Inferences
Uncertainties
Rejected / Unsupported Claims
Recommended Human Checks
```

### Why This Matters

Political analysis can be sensitive. RhetoriQ should help users reason from evidence instead of presenting speculation as certainty.

---

## 7.2 Confidence and Limitations

Each report should include:

- confidence score
- confidence label
- reason for confidence
- limitations
- missing data caveats

Example:

```text
Confidence: Medium

Why:
- The phrase appears across multiple source types.
- Several sources use unusually similar wording.
- Timeline is consistent with reactive amplification.

Limitations:
- Dataset may not include deleted posts.
- Earlier sources may exist outside the observed dataset.
- Similar phrasing may come from a shared public press release.
```

---

## 7.3 Human Review Recommendation

RhetoriQ should always recommend what humans should check next.

Examples:

- verify source timestamps
- check whether sources cite each other
- inspect possible press releases
- compare against official transcripts
- look for earlier appearances outside the dataset
- review deleted or archived posts if available

---

## 8. Sponsor-Aligned Features

## 8.1 Anthropic-Powered Investigation

Anthropic should power:

- query understanding
- analyst agent
- skeptic agent
- final report generation
- cautious civic reasoning

### Feature Tie-In

This powers Ask RhetoriQ, agent debate, report writing, and safety language.

---

## 8.2 Redis Narrative Memory

Redis should power:

- vector search over documents
- semantic cache
- narrative memory
- phrase spike counters
- prior investigation retrieval

### Feature Tie-In

This supports fast investigation and prevents repeated expensive LLM calls.

---

## 8.3 Fetch AI Discoverable Agent

Fetch AI should expose RhetoriQ as a discoverable civic intelligence agent.

User can query:

```text
Investigate the hidden energy tax narrative.
```

The agent returns:

- summary
- top sources
- report link
- confidence
- receipts

---

## 8.4 Arize Source-Grounding Evaluation

Arize should track:

- agent traces
- final report
- evidence used
- unsupported claims
- source-grounding score
- whether receipts exist

### Feature Tie-In

This supports responsible AI and judge trust.

---

## 8.5 Browserbase Source Verification

Browserbase should support:

- opening source pages
- extracting metadata
- validating source URLs
- capturing snippets
- verifying evidence before report generation

### Feature Tie-In

This strengthens Receipts Mode.

---

## 8.6 Band Multi-Agent Rooms

Band can support:

- shared agent context
- collaborative investigation rooms
- agent debate

### Feature Tie-In

This strengthens the Multi-Agent Investigation Room.

---

## 8.7 Deepgram Speech / Transcript Ingestion

Deepgram can support:

- speech transcription
- debate/hearing/town hall ingestion
- matching spoken phrases to online narratives

### Feature Tie-In

This adds a strong civic media extension.

---

## 9. Future Features

These are not required for the MVP but are strong future directions.

## 9.1 Browser Extension

User reads an article and clicks:

```text
Trace this narrative
```

RhetoriQ opens a side panel showing:

- related narratives
- first observed source
- spread timeline
- source diversity
- receipts

## 9.2 Export Investigation Pack

One-click export for journalists and researchers:

- PDF report
- CSV source table
- graph image
- timeline
- receipts
- JSON data

## 9.3 Narrative Lifecycle Stage

Classify narratives as:

- emerging
- amplifying
- mainstreaming
- institutionalized
- declining
- resurfacing

## 9.4 Geographic Spread Map

Show how a narrative moves geographically:

- local
- state
- national
- international

## 9.5 Narrative Similarity Search

User pastes a claim, and RhetoriQ finds older similar narratives.

## 9.6 Quote Reuse Detector

Detect near-identical phrasing across multiple sources.

## 9.7 Press Release Matching

Compare news articles and posts against official press releases or advocacy statements.

## 9.8 Public API

Provide endpoints such as:

```text
GET /narratives/trending
POST /investigate
GET /narratives/{id}/timeline
GET /narratives/{id}/graph
GET /reports/{id}
```

---

## 10. MVP Feature Checklist

### P0 Must-Have

- [ ] Ask RhetoriQ prompt input
- [ ] Investigation result page
- [ ] Source-grounded report
- [ ] Receipts Mode with clickable links
- [ ] Timeline view
- [ ] Spread graph
- [ ] Seeded dataset

### P1 Strong Differentiators

- [ ] Live Narrative Radar
- [ ] Narrative Family Tree
- [ ] Counter-Narrative Detection
- [ ] Source Diversity Panel
- [ ] Multi-Agent Investigation Room
- [ ] Agent Debate Summary

### P2 Sponsor Depth

- [ ] Redis vector search
- [ ] Redis semantic cache
- [ ] Anthropic report generation
- [ ] Arize eval/tracing
- [ ] Browserbase source verification
- [ ] Fetch AI agent
- [ ] Band multi-agent room
- [ ] Sentry monitoring
- [ ] Deepgram speech ingestion

### P3 Future Polish

- [ ] Browser extension
- [ ] Export pack
- [ ] Lifecycle stage
- [ ] Geographic map
- [ ] Press release matching
- [ ] Public API

---

## 11. Feature Success Criteria

RhetoriQ’s features are successful if a user can say:

1. “I can ask about any political story.”
2. “I can see where the narrative started in the observed data.”
3. “I can see how it spread.”
4. “I can see related and counter-narratives.”
5. “I can understand what kinds of sources are involved.”
6. “I can verify the AI report through clickable receipts.”
7. “I can see the AI challenged itself before finalizing the report.”
8. “I understand the product is for civic investigation, not partisan truth-scoring.”

---

## 12. Final Product Framing

RhetoriQ combines:

- natural language investigation
- live narrative monitoring
- narrative family trees
- counter-narrative mapping
- source diversity analysis
- multi-agent debate
- receipts-backed AI reporting

The product should be described as:

> **A source-grounded civic narrative investigation platform.**

Not:

> **A fake-news detector.**

Not:

> **A political truth engine.**

Not:

> **A partisan bias judge.**

The strongest demo message is:

> **RhetoriQ lets users ask about any political story, traces how the narrative evolved and spread, and backs every AI claim with clickable evidence.**
