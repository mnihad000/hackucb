# RhetoriQ Frontend Description

**Purpose of this doc:** Map what the frontend currently shows, what data backs each piece, and what needs to be displayed to support a live trending-narrative detection algorithm.

---

## 1. Current Page Structure

Two routes exist:

| Route | Component | Role |
|---|---|---|
| `/` | `DashboardPage` | Homepage — radar, search, recent investigations |
| `/investigation/:id?q=...` | `InvestigationPage` | Deep-dive narrative map for one story |

---

## 2. Dashboard Page (what is currently shown)

### 2.1 Header
Static nav bar with branding. No live data.

### 2.2 Hero — `Hero.tsx`
**What it shows:**
- Headline: "Trace how political stories spread."
- Three trust pills: "Clickable receipts", "Counter-narratives", "Human review recommended"
- The **AskRhetoriQ** search panel (see 2.3)

**Data source:** Hardcoded copy + `examplePrompts[]` from `demoData.ts`

---

### 2.3 AskRhetoriQ Search — `AskRhetoriQ.tsx`
**What it shows:**
- Free-text input field
- "Investigate" submit button
- Example prompt chips: "Hidden energy tax", "TikTok ban", "Immigration this week", "Education policy"

**What it does:** On submit, routes to `/investigation/demo?q=<encoded-query>`. Always lands on the seeded demo investigation regardless of the query typed. No live backend call.

**Data source:** `examplePrompts[]` (static array of 4 items)

**What is missing for live use:** The submit should POST to `/api/investigate` on the Node backend (port 8787) and route to a real investigation ID returned by the backend.

---

### 2.4 Narrative Radar — `NarrativeRadar.tsx` + `NarrativeCard.tsx`
**What it shows:** A 3-column grid of `NarrativeCard` components — currently 5 cards.

Each card displays:

| Field | Source field | Example value |
|---|---|---|
| Status badge | `topic.status` | "Amplifying" |
| Title | `topic.title` | "Hidden Energy Tax" |
| Confidence pill | `topic.confidence` | "Medium" |
| Summary paragraph | `topic.summary` | "A cost-of-living frame moving..." |
| Spike multiplier | `topic.spike` | "7.4x" |
| Source count | `topic.sourceCount` | 26 |
| First observed time | `topic.firstObserved` | "First observed in our dataset at 9:14 AM" |
| Source mix description | `topic.sourceMix` | "Local blogs, community posts, national news" |
| "Investigate" link | `topic.id` → `/investigation/:id` | Routes to the named seed |

**Data source:** `radarTopics[]` — 5 hardcoded `RadarTopic` objects in `demoData.ts`. No API call.

**The 5 current seeded narratives:**
1. Hidden Energy Tax — Amplifying, 7.4x spike, 26 sources, Medium confidence
2. TikTok Ban Narrative Shift — Reframing, 5.8x spike, 19 sources, High confidence
3. Border Enforcement Cost Narrative — Emerging, 4.9x spike, 21 sources, Medium confidence
4. Classroom Curriculum Flashpoint — Escalating, 6.1x spike, 17 sources, Medium confidence
5. Campaign Deepfake Warnings — Splitting, 3.7x spike, 14 sources, Low confidence

---

### 2.5 Recent Investigations — `RecentInvestigations.tsx`
**What it shows:** A 3-column grid of clickable cards, each showing:

| Field | Example |
|---|---|
| Focus label | "Counter-narratives" |
| Title | "TikTok Ban Narrative Shift" |
| Receipt count badge | "8 receipts" |
| Summary | "Tracks how creator-economy language caught up..." |
| Last updated | "Updated 34 minutes ago" |

**Data source:** `recentInvestigations[]` — 3 hardcoded entries in `demoData.ts`. No API call.

---

### 2.6 TrustStrip — `TrustStrip.tsx`
**What it shows:** A footer banner with three trust signals:
- "First observed in our dataset"
- "Signals consistent with evidence"
- "Human review recommended"

No data, all static copy.

---

## 3. Investigation Page (what is currently shown)

Route: `/investigation/:id?q=<query>`

### 3.1 Investigation Hero Panel
**What it shows:**

| Field | Where it comes from |
|---|---|
| Kicker / eyebrow label | `experience.kicker` (e.g. "Narrative path map") |
| H1 title | `experience.title` (e.g. "Hidden Energy Tax Investigation") |
| Status pill | `experience.status` |
| Confidence pill | `experience.confidence` |
| Source count pill | `experience.sourceCount` |
| Receipt count pill | `experience.receiptCount` |
| "User asked" quote box | URL query param `?q=` or `experience.flowchartData.query` |
| Generated at | `experience.generatedAt` |
| First observed | `experience.firstObserved` |
| Receipts available | `experience.receiptCount` |
| Current narrative state | `experience.status` |

**Data source:** `getInvestigationExperience(id, query)` in `demoData.ts`. Every route (tiktok-ban, border-enforcement, etc.) clones the same `hiddenEnergyTaxFlowchartData` flowchart and overwrites the title and current-node label. No API call.

### 3.2 Executive Summary Panel
**What it shows:**
- Summary paragraph (cautious, source-grounded language)
- A fixed "Cautious framing" sidebar explaining what RhetoriQ does and doesn't claim

**Data source:** `experience.summary` — per-seed static string

### 3.3 Investigation Flowchart — `InvestigationFlowchart.tsx`
**What it shows:** An animated ReactFlow canvas where each node is an `InvestigationNodeCard` and each edge is an `AnimatedInvestigationEdge`.

**Node types and their visual meaning:**

| nodeType | Meaning |
|---|---|
| `current` | The narrative being investigated right now |
| `first_observed` | Earliest source in the dataset for this phrase |
| `amplification` | A source that significantly boosted reach |
| `media_pickup` | When mainstream/national media picked it up |
| `official_mention` | Government, politician, or official source used it |
| `counter_narrative` | A competing or opposing frame |
| `related` | Adjacent story or context node |
| `uncertain` | Low-confidence connection |

**Edge types and their visual meaning:**

| edgeType | Meaning |
|---|---|
| `temporal_sequence` | This source published after that one |
| `exact_phrase_reuse` | Same phrase appeared word-for-word |
| `semantic_similarity` | Similar framing without exact match |
| `source_link` | One source cited or linked to another |
| `counter_narrative` | Edge connecting opposing frames |
| `related_context` | Loose topical connection |
| `uncertain` | Low-confidence link |

**Each node card shows:**
- Node type label
- Timestamp
- Title / label
- Subtitle
- Source count
- Counter-source count (if applicable)
- Receipt count
- Status badge
- Confidence badge
- On click → opens `NodeDetailsPanel` sidebar

**NodeDetailsPanel shows:**
- Full source list (`InvestigationNodeSource[]`): name, type, title, URL, published date, snippet, stance
- Full receipt list (`InvestigationReceipt[]`): source name, title, URL, quote, support reason, browser-verified badge

**Data source:** `hiddenEnergyTaxFlowchartData` — a single hardcoded `InvestigationFlowchartData` object. All investigation routes reuse it.

---

## 4. What the Backend Currently Provides

The Node backend (port 8787) exposes these live endpoints. **The frontend does not call any of them yet.**

| Endpoint | What it returns |
|---|---|
| `GET /health` | Service heartbeat |
| `GET /api/narratives/trending` | One `NarrativeCluster` (Hidden Energy Tax) with spike_score, source_count, confidence, growth rate, source diversity breakdown |
| `GET /api/demo-investigation` | Full seeded investigation payload: report, claims, receipts, source_verification, grounding_evals |
| `POST /api/investigate` | Accepts `{query}`, returns an investigation payload (currently mirrors demo data) |
| `GET /api/reports/:id` | Returns `report + claims + receipts + source_verification + grounding_evals` for a given report ID |

The Python FastAPI backend (port 8000 when running) has a deeper `SpikeDetector` service and `HNIngestion` service that the Node layer will eventually call into.

---

## 5. What Needs to Be Displayed for a Live Trending Algorithm

To wire up a real trending-narrative feed, the frontend needs to show the following. These are grouped by what the algorithm must emit and what the UI must render.

---

### 5.1 Narrative Radar Cards (live version)
The `NarrativeCard` already has the right shape. It needs these fields populated from live data:

| Field | Algorithm output needed | Notes |
|---|---|---|
| `spike` | `spike_score` as a multiplier (e.g. `6.0x`) | `SpikeDetector.compute_spike_score()` already produces this |
| `sourceCount` | Count of distinct documents in the cluster | Available on `NarrativeCluster.document_ids` |
| `firstObserved` | Timestamp of earliest document matching the phrase | Needs to be surfaced per cluster |
| `status` | Lifecycle stage: emerging / amplifying / mainstreaming / declining | Derived from spike trajectory over time (see 5.4) |
| `confidence` | Low / Medium / High | Based on source count + phrase match strength |
| `sourceMix` | Human-readable breakdown of source types | e.g. "Forum: 12, News: 8, Official: 2" from `source_diversity_snapshot` |

The backend's `GET /api/narratives/trending` already returns `source_diversity_snapshot` and `recent_growth_rate`. The frontend just needs to call it.

---

### 5.2 Spike Timeline Chart (missing from frontend)
**Not currently displayed anywhere.** This is the most useful visual for a trending algorithm.

**What to show:** A small sparkline or bar chart per NarrativeCard showing daily mention count over the past 7 days.

**Algorithm output needed:** `SpikeDetector.compute_phrase_timeline(phrase, documents)` already returns `[{date, count}]`. The backend needs an endpoint like `GET /api/narratives/:id/timeline` and the card needs a chart component.

**Why it matters for the algorithm:** The shape of the curve tells you whether a narrative is newly emerging (steep ramp), peaking (flat top), or declining (falling). The spike score alone is a snapshot; the timeline is the trajectory.

---

### 5.3 Source Diversity Breakdown (partially shown)
The current `NarrativeCard` shows `sourceMix` as a single string. For the algorithm to be credible, the UI should show:

| Source type | What it signals |
|---|---|
| `local` → `national` spread | Narrative is mainstreaming |
| Forum-only → news pickup | Amplification happening |
| High `unknown_ideology` share | Source diversity is unclear, lower confidence |
| `official` source appearance | Narrative has reached policy level |

**What to add:** A mini-bar or icon row showing the numeric breakdown from `source_diversity_snapshot`: `{local, state, national, official, media, unknown_ideology}`.

---

### 5.4 Narrative Lifecycle Status (needs algorithm logic)
The `status` field on `RadarTopic` is currently a hardcoded string. It needs to be computed.

**Suggested derivation logic the algorithm should implement:**

| Condition | Status label |
|---|---|
| `spike_score >= 5` and first seen < 24h ago | `emerging` |
| `spike_score >= 4` and spread across 2+ source types | `amplifying` |
| `spike_score >= 3` and national/official sources present | `mainstreaming` |
| `spike_score < 2` and was previously higher | `declining` |
| Multiple competing frames with similar spike scores | `splitting` / `reframing` |

The frontend status badge already supports these values via `InvestigationStatus` type.

---

### 5.5 Confidence Score Display (needs more nuance)
Currently shown as a single pill (Low / Medium / High). For the algorithm, confidence should reflect:

- **Phrase match strength**: exact match vs. semantic similarity
- **Source count**: more sources = higher confidence
- **Source diversity**: single-source spike is suspicious, not impressive
- **Mutation score**: if the phrase has mutated heavily, confidence in "same narrative" drops

The `NarrativeCluster.confidence_score` (float 0–1) already exists in the backend model. The frontend should show the numeric score alongside the label.

---

### 5.6 Mutation / Phrase Drift Indicator (missing)
**Not currently shown.** The backend has `MutationDetector` logic.

**What to add to the card:** A small indicator showing whether the canonical phrase has drifted into variant phrasings (e.g., "hidden energy tax" → "secret utility surcharge"). This signals active narrative evolution and is a strong trending signal.

**Algorithm output needed:** A `mutation_variants` array or `mutation_count` integer per cluster.

---

### 5.7 Cross-Source Velocity (missing)
**What to add:** A "velocity" metric showing how fast new sources are picking up the phrase — e.g., "+4 sources in the last 2 hours." This is more useful for a judge or journalist than a static source count.

**Algorithm output needed:** Count of documents added to the cluster in the last N hours, exposed as `recent_source_velocity` on the cluster.

---

## 6. API Shape the Frontend Expects

For the radar to go live, `GET /api/narratives/trending` needs to return an array of objects in this shape (already partially matched by the backend):

```ts
type LiveNarrativeTopic = {
  id: string;
  title: string;
  canonical_phrase: string;
  summary: string;                      // AI-generated, 1-2 sentences
  spike_score: number;                  // e.g. 6.0 → displayed as "6x"
  status: "emerging" | "amplifying" | "mainstreaming" | "declining" | "splitting";
  confidence_score: number;             // 0.0–1.0
  confidence_label: "Low" | "Medium" | "High";
  source_count: number;
  first_observed_at: string;            // ISO timestamp
  source_diversity_snapshot: {
    local: number;
    state: number;
    national: number;
    official: number;
    media: number;
    unknown_ideology: number;
  };
  recent_growth_rate: string;           // e.g. "6x baseline"
  timeline: { date: string; count: number }[];   // 7-day daily counts
  mutation_count?: number;              // optional: how many phrase variants exist
  recent_source_velocity?: number;      // optional: new sources in last 2h
};
```

The `NarrativeCard` component needs to be updated to consume this shape instead of the static `RadarTopic` type.

---

## 7. Summary: What Is Hardcoded vs. What Needs to Be Live

| UI Element | Current state | What needs to change |
|---|---|---|
| Radar cards | 5 hardcoded topics | Fetch from `GET /api/narratives/trending` |
| Spike score | Hardcoded string ("7.4x") | Computed by `SpikeDetector`, returned in API |
| Spike timeline chart | Does not exist | New component + `timeline[]` in API response |
| Source diversity | Single string | Numeric breakdown from `source_diversity_snapshot` |
| Narrative status | Hardcoded string | Derived from spike trajectory in algorithm |
| AskRhetoriQ submit | Routes to demo | POST to `/api/investigate`, get real report ID |
| Recent investigations | 3 hardcoded entries | Should come from a `GET /api/investigations/recent` list |
| Investigation flowchart | Single seeded dataset | Backend returns `InvestigationFlowchartData` per query |
| Mutation indicator | Does not exist | `mutation_count` from `MutationDetector` |
| Source velocity | Does not exist | `recent_source_velocity` computed over sliding window |
