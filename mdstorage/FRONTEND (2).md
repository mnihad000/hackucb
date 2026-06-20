# RhetoriQ Frontend Spec

**Document purpose:** Define the frontend architecture, pages, components, UI states, and implementation plan for RhetoriQ.  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`, `DATA_SCHEMA.md`, `BUILD_PLAN.md`, `ETHICS_AND_SAFETY.md`  
**Audience:** frontend owner, full-stack teammate, AI coding agents, UI/UX helpers, judges reviewing product polish.

---

## 1. Frontend Goal

The frontend must make RhetoriQ instantly understandable.

A judge should understand this within 30 seconds:

> **RhetoriQ lets users ask about any political story, traces how the narrative evolved and spread, and backs every AI claim with clickable evidence.**

The frontend should not feel like:

- a generic chatbot...
- a raw data dashboard
- an architecture demo
- a political bias scoreboard
- a fake-news detector

It should feel like:

- a polished civic intelligence product
- an investigation workspace
- a source-grounded report viewer
- a narrative spread visualization tool
- an AI analyst with receipts

---

## 2. Core Frontend Principles

## 2.1 Lead With Product, Not Infrastructure

Do not show Kafka/Flink/vector DB/agent architecture first.

The UI should lead with:

1. user question
2. narrative spike
3. timeline
4. graph
5. family tree
6. counter-narratives
7. source diversity
8. agent debate
9. receipts

## 2.2 Make Evidence Visible

The most important trust feature is **Receipts Mode**.

Every major claim in the report should be expandable into clickable evidence.

Users should never feel like the AI is asking for blind trust.

## 2.3 Keep Political Claims Cautious

The frontend must reinforce ethical language:

- “first observed in our dataset”
- “signals consistent with”
- “requires human review”
- “source diversity, not truth score”
- “evidence-backed report”

Avoid UI language like:

- “fake”
- “propaganda”
- “truth score”
- “confirmed astroturf”
- “bias score”
- “manipulation detected”

## 2.4 Make the Demo Story Obvious

The demo narrative should be visually clear:

```text
hidden energy tax
  ↓
local/community source
  ↓
blogs/news pickup
  ↓
national coverage
  ↓
official transcript mention
  ↓
counter-narrative appears
```

The frontend should help tell this story without needing too much explanation.

---

## 3. Recommended Frontend Stack

Recommended:

```text
React + TypeScript + Vite or Next.js
Tailwind CSS
shadcn/ui or custom clean components
React Flow / Cytoscape.js / vis-network for graph
Recharts for simple charts
```

Preferred for hackathon speed:

```text
Vite + React + TypeScript + Tailwind + React Flow + Recharts
```

Why:

- fast setup
- simple routing
- easy component structure
- graph support
- polished enough for demo

---

## 4. Frontend Routes

## 4.1 `/`

Homepage / dashboard.

Purpose:

- explain product quickly
- show Ask RhetoriQ input
- show Live Narrative Radar cards
- show recent/seeded investigations
- let user enter the main demo flow

Sections:

1. hero
2. Ask RhetoriQ search box
3. live narrative radar
4. example prompts
5. recent investigations
6. sponsor/tech badges, subtle
7. ethical trust strip

---

## 4.2 `/investigation/:id`

Full investigation workspace.

Purpose:

- show one complete narrative investigation
- render all product differentiators
- be the main demo page

Sections:

1. investigation header
2. executive summary
3. timeline
4. narrative family tree
5. counter-narratives
6. source diversity
7. spread graph
8. agent debate
9. final report
10. receipts mode
11. limitations/human checks

---

## 4.3 `/report/:id` Optional

Report-focused page.

Purpose:

- clean shareable report view
- useful for Devpost screenshots
- optional if time allows

---

## 5. Homepage Layout

The homepage should immediately communicate value.

## 5.1 Hero Section

Suggested title:

```text
Trace how political stories spread.
```

Suggested subtitle:

```text
RhetoriQ is an AI narrative detective that investigates political stories, maps how they evolve, and backs every claim with clickable evidence.
```

Primary CTA:

```text
Ask RhetoriQ
```

Secondary CTA:

```text
View Live Narrative Radar
```

Trust line:

```text
Source-grounded. Nonpartisan by design. Built for human review.
```

---

## 5.2 Ask RhetoriQ Input

This should be the biggest interaction on the homepage.

Placeholder:

```text
Ask about any political story, claim, phrase, or issue...
```

Example prompts under input:

```text
Where did the hidden energy tax narrative come from?
```

```text
Trace the story behind the TikTok ban.
```

```text
What narratives are forming around immigration this week?
```

```text
Find counter-narratives around this education policy.
```

Button:

```text
Investigate
```

Behavior:

- on submit, call `/api/investigate`
- if unavailable, route to seeded `/api/demo-investigation`
- show loading investigation steps

---

## 5.3 Live Narrative Radar

Cards for detected or seeded narratives.

Each card should show:

- title
- short summary
- spike score
- source count
- first observed
- status
- confidence
- source mix
- investigate button

Example card:

```text
Hidden Energy Tax
Spike: 7.4x
Sources: 26
First observed: 9:14 AM
Status: Amplifying
Source mix: local blogs, community posts, national news
Confidence: Medium
```

Card CTA:

```text
Investigate
```

---

## 5.4 Trust Strip

A small strip explaining what RhetoriQ does and does not do.

Example:

```text
RhetoriQ does not assign truth scores. It traces first observed sources, maps spread patterns, shows counter-narratives, and provides receipts for human review.
```

---

## 6. Investigation Page Layout

The investigation page is the most important page.

Recommended layout:

```text
Investigation Header
  ↓
Executive Summary Card
  ↓
Timeline + Source Diversity side-by-side
  ↓
Narrative Family Tree + Counter-Narratives
  ↓
Interactive Spread Graph
  ↓
Agent Debate
  ↓
Full Report
  ↓
Receipts Mode
  ↓
Limitations + Human Checks
```

For hackathon demo, prioritize clarity over density.

---

## 7. Investigation Header

Purpose:

- show what the user asked
- show investigation status
- show confidence
- show that the system is source-grounded

Fields:

- title
- user question
- generated timestamp
- confidence label
- number of sources
- number of receipts
- first observed source
- source-grounding badge

Example:

```text
Hidden Energy Tax Narrative Investigation

User asked:
“Where did the hidden energy tax narrative come from?”

Confidence: Medium
Sources analyzed: 26
Receipts: 9
First observed in dataset: Local Energy Watch, 9:14 AM
```

Badges:

```text
Source-grounded
Receipts available
Human review recommended
```

---

## 8. Executive Summary Card

Purpose:

- provide the quick answer
- set safe framing

Should include:

- 3–5 sentence summary
- first observed source
- spread pattern
- uncertainty

Example:

```text
In the observed dataset, the phrase “hidden energy tax” first appears in a local energy politics blog at 9:14 AM before spreading to community posts, local news, and later national political coverage. Several sources reuse similar wording, which is consistent with rapid amplification. However, the evidence is insufficient to conclude intentional coordination. Human review should verify whether sources cite a shared statement or earlier source outside the dataset.
```

---

## 9. Timeline Component

## 9.1 Purpose

Show how the narrative spread over time.

## 9.2 Props

```ts
type TimelineProps = {
  events: TimelineEvent[];
};
```

## 9.3 Timeline Event Fields

Display:

- timestamp
- source name
- source type
- title
- snippet
- role in spread
- clickable source link

## 9.4 Event Labels

Possible labels:

```text
First observed
Early amplification
Mainstream pickup
Official mention
Counter-narrative
Related context
```

## 9.5 UI Behavior

- vertical timeline
- first observed event highlighted
- counter-narrative events visually distinct
- source links clickable
- clicking event can scroll to receipt/source panel

## 9.6 Empty State

If timeline unavailable:

```text
Timeline unavailable because source timestamps are missing or incomplete.
```

---

## 10. Narrative Family Tree Component

## 10.1 Purpose

Show how the current talking point belongs to a broader narrative family.

## 10.2 Example

```text
Climate Policy Cost Narrative
├── hidden energy tax
├── utility bill surcharge
├── green mandate costs
└── war on appliances
```

## 10.3 Props

```ts
type NarrativeFamilyTreeProps = {
  family: NarrativeFamily;
  activeClusterId: string;
};
```

## 10.4 UI Requirements

Show:

- parent narrative
- child narratives
- active child highlighted
- related phrases
- growth status
- short explanation

## 10.5 Good Label

```text
Narrative Family
```

## 10.6 Helper Text

```text
Political stories often evolve from broader frames. This tree shows related narrative branches, not proof of coordination.
```

---

## 11. Counter-Narratives Component

## 11.1 Purpose

Show competing or opposing frames.

## 11.2 Layout

Best layout:

```text
Main Narrative              Counter-Narrative
------------------------------------------------
hidden energy tax            long-term energy savings
working families             infrastructure investment
higher bills                 future cost reduction
```

## 11.3 Props

```ts
type CounterNarrativesProps = {
  mainNarrative: NarrativeCluster;
  counterNarratives: CounterNarrative[];
};
```

## 11.4 UI Requirements

For each counter-narrative, show:

- title
- summary
- canonical phrase
- source count
- first observed time
- related phrases
- representative documents

## 11.5 Safety Note

Include:

```text
RhetoriQ maps competing frames. It does not decide which frame is true.
```

---

## 12. Source Diversity Panel

## 12.1 Purpose

Show what types of sources are involved without creating a simplistic bias score.

## 12.2 Display Dimensions

Show at least 3:

- source type distribution
- local/state/national/international
- official/unofficial/advocacy/independent
- original reporting/reposting/opinion/transcript/community post
- left/center/right/unknown only if provided

## 12.3 Props

```ts
type SourceDiversityProps = {
  diversity: SourceDiversityPanel;
};
```

## 12.4 UI Recommendation

Use cards or simple bars:

```text
Source Types
- Local news: 8
- National news: 6
- Community posts: 5
- Official statements: 3
- Blogs: 4
```

## 12.5 Required Caveat

```text
Source diversity provides context about the observed dataset. It is not a truth score or moral judgment.
```

---

## 13. Spread Graph Component

## 13.1 Purpose

Show relationships between documents, sources, narratives, and counter-narratives.

## 13.2 Recommended Library

Use one:

```text
React Flow
Cytoscape.js
vis-network
Sigma.js
```

For hackathon speed, use React Flow.

## 13.3 Props

```ts
type SpreadGraphProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};
```

## 13.4 Node Types

Display different node types:

- document
- source
- narrative
- narrative family
- counter-narrative
- phrase
- entity

## 13.5 Edge Types

Show edge labels or tooltips:

- exact phrase reuse
- semantic similarity
- shared entity
- temporal sequence
- counter-narrative relationship
- family-child relationship

## 13.6 Interaction

Clicking a node should show:

- title/label
- source type
- timestamp
- snippet
- URL
- importance explanation

Clicking an edge should show:

- relationship type
- evidence text
- weight/confidence
- related receipts if available

## 13.7 Graph Rule

Keep the graph small for demo.

Ideal demo graph:

```text
8–15 nodes
8–20 edges
```

Too many nodes will confuse judges.

---

## 14. Agent Debate Component

## 14.1 Purpose

Show that the AI challenged itself before producing the final report.

This is a major responsible-AI feature.

## 14.2 Props

```ts
type AgentDebateProps = {
  debate: AgentDebate;
};
```

## 14.3 Display Sections

Show:

- Analyst Agent position
- Skeptic Agent response
- Receipts Agent check
- Counter-Narrative note
- Safety/Grounding decision
- final language decision
- rejected claims
- softened claims

## 14.4 Example UI Text

```text
Analyst Agent:
The short time window and repeated wording may indicate coordinated amplification.

Skeptic Agent:
Evidence is not strong enough to claim coordination. Similar wording may come from a common press release or shared reaction.

Receipts Agent:
The phrase reuse claim is supported by three sources. The intent claim is unsupported.

Final Decision:
Use cautious language: “signals consistent with coordinated amplification,” not “coordinated campaign.”
```

## 14.5 Safety Note

```text
This summarizes agent outputs, not hidden chain-of-thought.
```

---

## 15. Report Component

## 15.1 Purpose

Render the final source-grounded investigation report.

## 15.2 Props

```ts
type ReportProps = {
  report: InvestigationReport;
  claims: ReportClaim[];
  receipts: Receipt[];
};
```

## 15.3 Required Sections

- executive summary
- first observed source
- narrative family summary
- counter-narrative summary
- timeline summary
- source diversity summary
- spread pattern
- agent debate summary
- observed facts
- reasonable inferences
- uncertainties
- rejected/unsupported claims
- limitations
- recommended human checks

## 15.4 Required Language

Use:

```text
First observed in our dataset
```

Not:

```text
Origin
```

or:

```text
Started at
```

unless qualified.

---

## 16. Receipts Component

## 16.1 Purpose

Let users verify every major AI-generated claim.

This is one of the most important components.

## 16.2 Props

```ts
type ReceiptsProps = {
  claims: ReportClaim[];
  receipts: Receipt[];
};
```

## 16.3 UI Structure

Recommended:

```text
Claim 1
  Status: Supported
  Confidence: High
  Show receipts
    - Source title
    - Source name
    - Published at
    - Snippet
    - Why this supports the claim
    - Open source link
```

## 16.4 Receipt Card Fields

Show:

- source title
- source name
- source type
- published date
- quote/snippet
- support reason
- browser verified badge if true
- clickable source URL

## 16.5 Required Link Behavior

If `url` exists:

```text
Open source
```

should be clickable.

If no URL:

```text
No public URL available
```

or:

```text
Seeded demo source
```

## 16.6 Claim Support Status

Show:

- supported
- partially supported
- unsupported
- contradicted
- needs human review

Unsupported claims should not be presented as confident findings.

---

## 17. Loading / Progress States

When a user submits Ask RhetoriQ, show investigation progress.

Suggested steps:

```text
Planning investigation...
Retrieving sources...
Building timeline...
Finding counter-narratives...
Mapping narrative family...
Analyzing source diversity...
Debating evidence...
Checking receipts...
Generating final report...
```

If backend has real status, update dynamically.

If not, simulate with timed steps for demo polish.

---

## 18. Error States

## 18.1 Investigation Failed

Message:

```text
RhetoriQ could not complete this investigation. Showing the demo investigation instead.
```

Action:

```text
View demo investigation
```

## 18.2 No Sources Found

Message:

```text
RhetoriQ did not find enough relevant sources to produce a grounded report.
```

Show:

- suggested broader query
- example prompts
- explanation that insufficient evidence is safer than hallucination

## 18.3 Graph Failed

Message:

```text
Graph unavailable. Timeline and receipts are still available.
```

Do not let graph failure break the whole page.

## 18.4 Receipts Missing

Message:

```text
This claim is not supported by enough evidence and should not be treated as a finding.
```

---

## 19. Empty States

## 19.1 No Counter-Narratives

```text
No clear counter-narrative was found in the observed dataset.
```

## 19.2 No Source Diversity Labels

```text
Source diversity metadata is incomplete. Unknown labels are shown instead of inferred labels.
```

## 19.3 No Family Tree

```text
RhetoriQ could not confidently place this narrative into a broader family.
```

These empty states are better than hallucinating.

---

## 20. Data Types Needed In Frontend

Use shared types from `DATA_SCHEMA.md`.

Minimum frontend types:

```ts
type InvestigationPageData = {
  query: InvestigationQuery;
  report: InvestigationReport;
  cluster: NarrativeCluster;
  family?: NarrativeFamily;
  counter_narratives: CounterNarrative[];
  timeline: TimelineEvent[];
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  source_diversity?: SourceDiversityPanel;
  agent_debate?: AgentDebate;
  claims: ReportClaim[];
  receipts: Receipt[];
  documents: Document[];
  sources: Source[];
};
```

---

## 21. Frontend Folder Structure

Recommended:

```text
frontend/
  src/
    app/
      App.tsx
      routes.tsx

    pages/
      DashboardPage.tsx
      InvestigationPage.tsx
      ReportPage.tsx

    components/
      layout/
        Header.tsx
        Shell.tsx
        Section.tsx

      dashboard/
        Hero.tsx
        AskRhetoriQ.tsx
        NarrativeRadar.tsx
        NarrativeCard.tsx
        ExamplePrompts.tsx
        TrustStrip.tsx

      investigation/
        InvestigationHeader.tsx
        ExecutiveSummary.tsx
        Timeline.tsx
        SpreadGraph.tsx
        NarrativeFamilyTree.tsx
        CounterNarratives.tsx
        SourceDiversity.tsx
        AgentDebate.tsx
        Report.tsx
        Receipts.tsx
        HumanChecks.tsx

      ui/
        Badge.tsx
        Card.tsx
        Button.tsx
        LoadingSteps.tsx
        EmptyState.tsx
        ErrorState.tsx

    lib/
      api.ts
      formatters.ts
      demoFallback.ts
      constants.ts

    types/
      rhetoriq.ts
```

If using Next.js:

```text
app/
  page.tsx
  investigation/[id]/page.tsx
components/
lib/
types/
```

---

## 22. API Client

Create a simple API wrapper.

```ts
export async function getDemoInvestigation(): Promise<InvestigationPageData> {
  const res = await fetch("/api/demo-investigation");
  if (!res.ok) throw new Error("Failed to load demo investigation");
  return res.json();
}

export async function investigate(queryText: string): Promise<InvestigationPageData> {
  const res = await fetch("/api/investigate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query_text: queryText }),
  });

  if (!res.ok) {
    return getDemoInvestigation();
  }

  return res.json();
}
```

Frontend should always have a fallback path.

---

## 23. Visual Design Direction

## 23.1 Mood

RhetoriQ should feel:

- serious
- modern
- investigative
- trustworthy
- civic
- technical but accessible

Avoid:

- meme aesthetics
- partisan colors
- dark conspiracy-board vibes
- scary “threat detected” UI
- fake-news detector style

## 23.2 Color Direction

Use a neutral, polished palette.

Suggested feel:

- dark navy / charcoal background
- off-white cards
- subtle accent color
- calm blue/purple/teal accents
- red/orange only for warnings, not political claims

Do not use red/blue as political left/right unless clearly labeled and necessary.

## 23.3 Typography

Use clean typography.

Suggested:

- Inter
- Geist
- system sans-serif

## 23.4 Visual Hierarchy

Most important elements:

1. Ask RhetoriQ input
2. executive summary
3. timeline
4. receipts
5. graph
6. agent debate
7. sponsor badges

Do not make sponsor badges louder than product value.

---

## 24. Copy Guidelines

## 24.1 Good Copy

Use:

```text
First observed in our dataset
```

```text
Source-grounded report
```

```text
Clickable receipts
```

```text
Counter-narratives
```

```text
Source diversity
```

```text
Signals consistent with
```

```text
Human review recommended
```

## 24.2 Bad Copy

Avoid:

```text
Fake news detected
```

```text
Propaganda score
```

```text
Truth rating
```

```text
Confirmed manipulation
```

```text
Astroturf campaign found
```

```text
Bias score
```

---

## 25. Main Demo Flow For Frontend

The frontend demo should follow this click path:

```text
1. Open homepage.
2. Point to Ask RhetoriQ.
3. Type or use example: “Where did the hidden energy tax narrative come from?”
4. Click Investigate.
5. Show loading steps.
6. Land on investigation page.
7. Show executive summary.
8. Show timeline.
9. Show narrative family tree.
10. Show counter-narratives.
11. Show source diversity.
12. Show spread graph.
13. Show agent debate.
14. Open receipts for one claim.
15. Emphasize clickable evidence.
```

The most important click:

```text
Open a receipt and click the source link.
```

That proves the product is evidence-backed.

---

## 26. Frontend MVP Checklist

## P0 Must-Have

- [ ] Homepage loads.
- [ ] Ask RhetoriQ input exists.
- [ ] Narrative radar cards exist.
- [ ] Investigation page exists.
- [ ] Executive summary renders.
- [ ] Timeline renders.
- [ ] Report renders.
- [ ] Receipts render.
- [ ] Receipt links are clickable.
- [ ] Loading state exists.
- [ ] Fallback demo data works.

## P1 Differentiators

- [ ] Narrative family tree renders.
- [ ] Counter-narrative panel renders.
- [ ] Source diversity panel renders.
- [ ] Spread graph renders.
- [ ] Agent debate renders.
- [ ] Unsupported/rejected claims section exists.
- [ ] Human review section exists.

## P2 Polish

- [ ] Graph nodes are clickable.
- [ ] Timeline items are clickable.
- [ ] Smooth loading transitions.
- [ ] Trust badges.
- [ ] Sponsor integration labels.
- [ ] Responsive layout.
- [ ] Screenshots look good.
- [ ] Devpost-ready visuals.

---

## 27. Component Build Order

Build components in this order:

```text
1. App shell / layout
2. Dashboard page
3. Ask RhetoriQ input
4. Narrative cards
5. Investigation page shell
6. Executive summary
7. Report component
8. Receipts component
9. Timeline component
10. Source diversity component
11. Counter-narrative component
12. Narrative family tree
13. Agent debate component
14. Spread graph
15. Loading states
16. Error/fallback states
17. Polish
```

Why this order?

Because report + receipts + timeline are the core. Graph and polish come after.

---

## 28. Frontend / Backend Integration Milestones

## Milestone 1

Frontend renders static imported JSON.

```ts
import demoData from "../../data/demo_investigation.json";
```

## Milestone 2

Frontend fetches backend demo endpoint.

```text
GET /api/demo-investigation
```

## Milestone 3

Frontend submits prompt.

```text
POST /api/investigate
```

## Milestone 4

Frontend handles live AI output and fallback.

## Milestone 5

Frontend displays sponsor/trust statuses:

- Redis retrieval
- Arize eval
- Browserbase verified receipt
- Fetch agent available

---

## 29. Demo Fallback Requirements

The frontend should never go blank during judging.

If live investigation fails:

- route to seeded demo
- show non-scary fallback message
- keep demo moving

Fallback message:

```text
Live investigation is unavailable, so RhetoriQ is showing a preloaded investigation to demonstrate the workflow.
```

---

## 30. Accessibility and UX Basics

Minimum:

- readable font sizes
- high contrast
- buttons have clear labels
- links are visibly clickable
- keyboard accessible input
- no tiny dense text blocks
- graph has alternative summary text
- badges are not color-only

---

## 31. Devpost Screenshot Targets

Capture screenshots of:

1. Homepage with Ask RhetoriQ.
2. Live Narrative Radar cards.
3. Investigation page summary.
4. Timeline.
5. Spread graph.
6. Receipts Mode with clickable evidence.
7. Agent Debate panel.
8. Source Diversity panel.

Best hero screenshot:

```text
Investigation page showing summary + timeline + receipts
```

---

## 32. Frontend Success Criteria

The frontend is successful if judges say:

- “I immediately understand what this does.”
- “The receipts make it trustworthy.”
- “The timeline makes the spread obvious.”
- “The family tree is cool.”
- “The counter-narratives make it balanced.”
- “The agent debate feels responsible.”
- “This is more than a chatbot.”
- “This fits civic/social impact.”

---

## 33. Final Frontend Recommendation

The frontend should optimize for:

```text
clarity > completeness
evidence > hype
demo reliability > live complexity
product story > architecture
```

The winning UI is not the one with the most charts.

The winning UI is the one where a judge can instantly understand:

> **I ask about a political story, RhetoriQ traces how it spread, and I can verify every claim with receipts.**
