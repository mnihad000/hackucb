# RhetoriQ Ethics and Safety

**Document purpose:** Define the ethical, safety, and responsible-AI rules for RhetoriQ.  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`, `DATA_SCHEMA.md`, `AGENT_SYSTEM.md`, `AGENT_PROMPTS.md`, `SPONSOR_STRATEGY.md`, `BUILD_PLAN.md`  
**Audience:** teammates, judges, mentors, AI coding agents, sponsor reviewers, and future contributors.

---

## 1. Why This Document Exists

RhetoriQ analyzes political and civic narratives.

That makes the project powerful, but also sensitive.

The system may touch topics such as:

- elections
- public policy
- misinformation
- media narratives
- political messaging
- source diversity
- coordinated amplification
- public figures
- advocacy groups
- ideological framing

Because of that, RhetoriQ must be designed carefully.

The goal is not to build a tool that tells users what to believe. The goal is to build a tool that helps users investigate how narratives move through public information systems.

The core ethical principle is:

> **RhetoriQ does not determine truth or assign blame. It organizes public evidence, traces narrative spread, shows source diversity, includes counter-narratives, and backs major claims with clickable receipts so humans can investigate responsibly.**

---

## 2. What RhetoriQ Is

RhetoriQ is:

- a civic narrative investigation assistant
- a source-grounded research tool
- a timeline and graph builder for political stories
- a system for detecting narrative spread patterns
- a tool for journalists, researchers, students, and civic organizations
- a way to understand how public narratives evolve
- a way to compare main narratives and counter-narratives
- a system that shows evidence and uncertainty

RhetoriQ helps answer questions like:

```text
Where did this narrative first appear in the observed dataset?
```

```text
How did this phrase spread across sources?
```

```text
Which counter-narratives appeared?
```

```text
What kinds of sources are discussing this?
```

```text
What evidence supports the AI report?
```

```text
What should a human verify next?
```

---

## 3. What RhetoriQ Is Not

RhetoriQ is **not**:

- a fake-news detector
- a political truth engine
- a partisan bias judge
- a propaganda detector
- an astroturfing proof machine
- a system for accusing people or groups
- a tool for deciding who is good or bad
- a replacement for journalists, researchers, or fact-checkers
- a tool that claims absolute origin of a story
- a tool that determines intent behind public messaging

RhetoriQ should never be pitched as:

```text
“We prove where misinformation started.”
```

or:

```text
“We detect propaganda.”
```

or:

```text
“We know who coordinated this.”
```

The safer and more accurate framing is:

```text
“We trace first observed appearances in our dataset, map spread patterns, surface signals, provide receipts, and recommend human review.”
```

---

## 4. Core Safety Principles

## 4.1 Evidence First

Every major claim must be grounded in source evidence.

If the system says:

```text
The phrase appeared in three sources within two hours.
```

Then it must show:

- the three sources
- timestamps
- snippets
- clickable links
- why those sources support the claim

This is the purpose of **Receipts Mode**.

---

## 4.2 First Observed, Not True Origin

RhetoriQ must not claim that it found the true origin of a narrative.

Use:

```text
first observed in our dataset
```

or:

```text
earliest source found in the observed data
```

Do not use:

```text
the origin
```

or:

```text
where it started
```

unless qualified.

Correct:

```text
The phrase was first observed in our dataset in a local blog post at 9:14 AM.
```

Incorrect:

```text
The phrase originated in a local blog post at 9:14 AM.
```

Why this matters:

- the dataset may be incomplete
- deleted posts may exist
- offline or private sources may exist
- another source may have used the phrase earlier
- search APIs may miss documents

---

## 4.3 Observed Facts vs Inference

Reports must separate:

```text
Observed Facts
Reasonable Inferences
Uncertainties
Rejected / Unsupported Claims
Recommended Human Checks
```

Example:

### Observed Fact

```text
Three documents in the dataset used the phrase “hidden energy tax” between 9:14 AM and 10:47 AM.
```

### Reasonable Inference

```text
The short time window and repeated wording are consistent with rapid amplification.
```

### Uncertainty

```text
The dataset may not include earlier appearances outside the monitored sources.
```

### Unsupported Claim

```text
The system does not have enough evidence to claim intentional coordination.
```

---

## 4.4 No Definitive Coordination Claims Without Strong Evidence

RhetoriQ may surface signals that are **consistent with** coordinated amplification.

It should not claim definitive coordination unless evidence is very strong.

Use:

```text
signals consistent with coordinated amplification
```

```text
possible coordination signals
```

```text
shared wording may indicate a common source or shared framing
```

```text
requires human review
```

Avoid:

```text
this was coordinated
```

```text
this was astroturfed
```

```text
this group manipulated the narrative
```

```text
this was a propaganda campaign
```

Why this matters:

Repeated wording can come from:

- shared press releases
- common public statements
- syndicated content
- quoting the same speech
- reacting to the same event
- coincidence
- journalistic reuse
- actual coordination

The system should not overclaim intent.

---

## 4.5 No Truth Scores

RhetoriQ should not assign a simplistic truth score.

Avoid:

```text
Truth Score: 27%
```

```text
This claim is false.
```

```text
This side is lying.
```

Instead, RhetoriQ should show:

- source evidence
- counter-narratives
- source diversity
- observed spread pattern
- uncertainty
- recommended human checks

If external fact-checking sources are later integrated, RhetoriQ can cite them as additional evidence, but it still should not become a simplistic truth-score product.

---

## 4.6 Source Diversity, Not Source Judgment

RhetoriQ can show source diversity.

Examples:

- local vs national
- official vs unofficial
- independent vs advocacy
- original reporting vs reposting
- article vs opinion vs transcript
- left / center / right / unknown, if labels are available

But RhetoriQ should not say:

```text
This source is bad.
```

```text
This source is lying.
```

```text
This ideology is more truthful.
```

The correct framing is:

```text
RhetoriQ measures source diversity and spread patterns, not truthfulness or moral correctness.
```

Ideology labels should be used only if they come from provided metadata or clearly labeled datasets. If not available, use:

```text
unknown
```

---

## 4.7 Counter-Narratives Are Required When Available

Political stories often have competing frames.

A responsible report should show:

- the main narrative
- counter-narratives
- sources supporting each frame
- timeline of each frame
- uncertainty

Example:

Main narrative:

```text
The bill is a hidden energy tax on working families.
```

Counter-narrative:

```text
The bill funds infrastructure and lowers long-term household costs.
```

RhetoriQ should not decide which side is morally correct. It should show that both frames exist and provide evidence.

---

## 4.8 Human Review Is Required

RhetoriQ is an investigation assistant, not a final authority.

Every report should include recommended human checks, such as:

- verify source timestamps
- inspect whether sources cite each other
- search for earlier appearances outside the dataset
- check archived or deleted content
- compare against press releases
- review official transcripts
- inspect source metadata
- ask domain experts when needed

The system should use language like:

```text
Human review is recommended before drawing conclusions.
```

---

## 5. Receipts Mode Safety Rules

Receipts Mode is one of RhetoriQ’s most important trust features.

Every major claim must map to at least one receipt.

## 5.1 Receipt Requirements

Each receipt should include:

- source name
- source type
- title
- clickable URL, if available
- timestamp or publication date
- quote or snippet
- support reason
- browser verification status, if available

## 5.2 Claim Support Labels

Each report claim should have one of these statuses:

```text
supported
partially_supported
unsupported
contradicted
needs_human_review
```

## 5.3 Unsupported Claims

Unsupported claims should not appear as confident statements in the final report.

They can appear in a section like:

```text
Rejected or Unsupported Claims
```

Example:

```text
The system rejected the claim that specific actors intentionally coordinated the narrative because the available evidence only showed repeated language and timing proximity.
```

## 5.4 Clickable Evidence

All available evidence URLs should be clickable in the UI.

If a link is unavailable, the receipt should say:

```text
No public URL available.
```

or:

```text
Source included in seeded demo dataset.
```

Do not fabricate URLs.

---

## 6. Multi-Agent Safety Rules

RhetoriQ uses multiple agents to reduce risk.

Key safety agents:

- Skeptic Agent
- Receipts Agent
- Safety / Grounding Agent

## 6.1 Analyst Agent

The Analyst Agent may propose an interpretation, but its draft is not final.

It should:

- summarize evidence
- propose spread pattern
- include caveats
- identify claims needing receipts

It should not publish directly.

## 6.2 Skeptic Agent

The Skeptic Agent challenges the draft.

It should ask:

- Is this claim supported?
- Does this overstate certainty?
- Does this imply intent without evidence?
- Are counter-narratives missing?
- Are limitations missing?
- Is “origin” language too strong?

## 6.3 Receipts Agent

The Receipts Agent maps claims to evidence.

It should:

- create receipts
- mark unsupported claims
- preserve URLs
- flag missing evidence

## 6.4 Safety / Grounding Agent

The Safety / Grounding Agent has veto power.

It should block or revise reports that:

- claim absolute origin
- claim definitive coordination without evidence
- accuse people or groups
- lack receipts
- omit uncertainty
- omit counter-narratives when available
- contain defamatory language
- label content fake/propaganda without strong evidence

---

## 7. Agent Debate Safety

Before the final report, agents should debate the evidence.

Example:

```text
Analyst Agent:
“The repeated phrase use and short time window may indicate coordinated amplification.”

Skeptic Agent:
“The evidence is not strong enough to claim coordination. Similar wording may come from a common press release or shared reaction.”

Receipts Agent:
“The repeated phrase claim is supported by three documents, but the intent claim is unsupported.”

Safety Agent:
“Use cautious language and include limitations.”

Final Report:
“The pattern shows signals consistent with coordinated amplification, but the evidence is insufficient to make a definitive claim. Human review is recommended.”
```

The debate should be summarized in the UI without exposing hidden chain-of-thought. Show only the agents’ conclusions and decisions.

---

## 8. Political Neutrality and Nonpartisan Design

RhetoriQ should be nonpartisan in its product behavior.

This means:

- it can analyze narratives from any political group
- it should apply the same evidence rules to all narratives
- it should not rank ideologies by truthfulness
- it should not favor one party’s framing
- it should include counter-narratives where available
- it should use the same cautious language across topics

RhetoriQ should be framed around:

```text
civic transparency
```

```text
media literacy
```

```text
journalistic research
```

```text
source-grounded investigation
```

not partisan advantage.

---

## 9. Defamation and Harm Avoidance

RhetoriQ should avoid statements that could unfairly harm individuals, organizations, or communities.

Avoid unsupported claims like:

```text
Person X coordinated this manipulation campaign.
```

```text
Organization Y is spreading propaganda.
```

```text
Group Z intentionally misled the public.
```

Safer alternatives:

```text
The available documents show repeated use of similar language by several sources.
```

```text
The timing and wording are consistent with shared framing, but the evidence does not establish intent.
```

```text
Human review is needed before drawing conclusions about coordination.
```

---

## 10. Handling Public Figures and Organizations

RhetoriQ may mention public figures or organizations when they appear in source documents.

Rules:

1. Only mention them if supported by evidence.
2. Cite the document where they appear.
3. Do not infer motive.
4. Do not accuse them of coordination without strong evidence.
5. Separate direct quotes from interpretation.
6. Include counter-evidence or caveats where relevant.

Example:

Correct:

```text
A public speech transcript in the dataset includes the phrase “hidden energy tax” at 1:20 PM.
```

Incorrect:

```text
The politician amplified a coordinated misinformation campaign.
```

---

## 11. Handling Ideology Labels

If RhetoriQ uses left/center/right labels, it must be careful.

Rules:

1. Use ideology labels only when provided by dataset metadata or reliable classification.
2. If unavailable, use `unknown`.
3. Do not infer ideology from one article.
4. Do not claim ideological labels are perfect.
5. Include a caveat.

Recommended caveat:

```text
Ideology labels are approximate and may be incomplete. Source diversity is provided for context, not as a truth judgment.
```

---

## 12. Handling Synthetic or Seeded Demo Data

For hackathon reliability, RhetoriQ may use seeded demo data.

If demo data is synthetic or partially synthetic:

- do not present it as real-world evidence
- label it clearly in internal docs and Devpost if needed
- avoid using real names with fake claims
- use fictional outlets or example domains
- do not fabricate harmful claims about real people

Recommended demo-data note:

```text
The demo uses a seeded dataset to reliably demonstrate the investigation workflow. The product is designed to work with public sources such as news, RSS, GDELT-style data, transcripts, and community posts.
```

---

## 13. Data Source Safety

RhetoriQ may use sources like:

- public news
- RSS feeds
- GDELT-style media data
- public transcripts
- community posts
- official statements
- seeded demo documents

Safety rules:

1. Respect API terms.
2. Respect rate limits.
3. Avoid private or non-consensual data.
4. Prefer public-interest sources.
5. Store only what is necessary for the investigation.
6. Avoid exposing private individuals unnecessarily.
7. Do not scrape content that violates site rules.
8. Preserve source attribution.

---

## 14. Privacy Rules

RhetoriQ should avoid collecting or exposing private personal information.

Avoid:

- private addresses
- private phone numbers
- private emails
- doxxing information
- private social profiles
- information about non-public individuals unless directly relevant and public

If user-generated uploads are supported later, the system should:

- avoid storing sensitive uploads by default
- avoid exposing uploaded data to other users
- clearly communicate what is stored
- allow deletion where appropriate

For the hackathon MVP, the safest approach is to use public or seeded sources only.

---

## 15. Hallucination Prevention

RhetoriQ should minimize hallucinations by design.

Required practices:

1. Use retrieval before generation.
2. Provide documents to the model.
3. Require structured JSON.
4. Require citations/receipts.
5. Validate outputs.
6. Run Skeptic Agent review.
7. Run Safety / Grounding Agent review.
8. Use Arize or another eval layer if available.
9. Cache known-good demo outputs.
10. Fall back to static data if live generation fails.

The model should be instructed:

```text
If the evidence is insufficient, say so.
```

---

## 16. Arize / Evaluation Safety

If Arize is used, it should evaluate:

- source grounding
- receipt coverage
- overclaiming risk
- uncertainty quality
- political safety risk
- counter-narrative inclusion
- defamation risk
- observed-fact vs inference separation

Example eval pass criteria:

```text
source_grounding_score >= 0.8
receipt_coverage_score >= 0.8
overclaiming_risk != high
political_safety_risk != high
defamation_risk == low
```

If the report fails eval, it should be revised or marked as needing human review.

---

## 17. Browserbase / Source Verification Safety

If Browserbase is used, it should support trust, not overclaiming.

Use Browserbase to:

- open source pages
- verify title/date/snippet
- preserve page URL
- mark receipts as browser verified

Do not use Browserbase to:

- bypass access controls
- scrape private data
- misrepresent what a page says
- claim a page proves intent

A browser-verified receipt means:

```text
The system verified that this source page contains the relevant evidence.
```

It does not mean:

```text
The source is truthful.
```

---

## 18. Redis / Memory Safety

Redis may store narrative memory, prior investigations, semantic cache, and embeddings.

Rules:

1. Do not store unnecessary personal data.
2. Do not let old memory override current evidence.
3. Treat memory as retrieval context, not truth.
4. If prior investigations are used, disclose that context.
5. Allow stale memory to be refreshed or invalidated.

Recommended language:

```text
Prior RhetoriQ memory found similar narratives, but the current report is based on the sources retrieved for this investigation.
```

---

## 19. UI Safety Requirements

The UI should make uncertainty visible.

Required UI elements:

- “first observed in our dataset” label
- confidence score or label
- limitations section
- recommended human checks
- receipts panel
- counter-narrative panel
- source diversity caveat
- agent debate summary
- unsupported/rejected claims section, if relevant

Avoid UI elements like:

- truth score
- propaganda score
- fake news badge
- partisan winner/loser
- definitive astroturf label
- red danger labels that imply guilt without evidence

---

## 20. Safe Report Language

## 20.1 Preferred Language

Use:

```text
first observed in our dataset
```

```text
earliest observed source
```

```text
appears to spread through
```

```text
is consistent with
```

```text
may indicate
```

```text
signals of
```

```text
source diversity suggests
```

```text
requires human review
```

```text
evidence is insufficient to conclude
```

## 20.2 Avoided Language

Avoid:

```text
originated
```

```text
proved
```

```text
definitely coordinated
```

```text
fake news
```

```text
propaganda
```

```text
astroturfed
```

```text
manipulated by
```

```text
this side is lying
```

unless heavily qualified and directly supported by strong evidence.

---

## 21. Example Safe Report Excerpt

Good:

```text
In the observed dataset, the phrase “hidden energy tax” first appears in a local energy politics blog at 9:14 AM. It later appears in several community posts and news articles within the same day. Several sources reuse similar wording, which is consistent with shared framing or rapid amplification. However, the evidence is insufficient to conclude intentional coordination. Human review should verify whether the sources cite a common press release or earlier statement outside the dataset.
```

Bad:

```text
The hidden energy tax narrative was created by a coordinated campaign and spread as propaganda through right-wing outlets.
```

Why bad:

- claims true origin
- claims coordination
- uses loaded language
- assigns ideology/intent
- lacks receipts
- lacks uncertainty

---

## 22. Demo and Devpost Safety

In the demo and Devpost, describe RhetoriQ as:

```text
a source-grounded civic narrative investigation platform
```

not:

```text
a misinformation detector
```

Use this wording:

```text
RhetoriQ helps users understand how political narratives spread by tracing first observed sources, mapping related and counter-narratives, analyzing source diversity, and backing AI-generated reports with clickable receipts.
```

Avoid this wording:

```text
RhetoriQ detects propaganda and tells you who started it.
```

---

## 23. Judge Q&A Safety Answers

## Question: Are you deciding what is true?

Answer:

```text
No. RhetoriQ does not assign truth scores. It organizes evidence, shows how narratives spread, includes counter-narratives, and provides receipts so humans can investigate responsibly.
```

## Question: How do you avoid falsely accusing people?

Answer:

```text
We avoid definitive claims about intent or coordination. The system uses cautious language, includes uncertainty, requires receipts for major claims, and runs a Skeptic Agent plus Safety/Grounding Agent before publishing a report.
```

## Question: What does “origin” mean in your app?

Answer:

```text
We say “first observed in our dataset,” not true origin. The system is transparent that earlier sources may exist outside our data.
```

## Question: What if the AI hallucinates?

Answer:

```text
Every major claim must map to receipts. Unsupported claims are removed or flagged. We also use a skeptic pass, a safety/grounding pass, and optionally Arize evals for source grounding.
```

## Question: Are you labeling sources as biased?

Answer:

```text
We show source diversity, not truthfulness. If ideology labels are unavailable, we mark them unknown. The panel is contextual, not a judgment.
```

## Question: Could this be used for partisan targeting?

Answer:

```text
The product is designed for civic research, journalism, and media literacy. It avoids personal targeting, avoids unsupported accusations, and applies the same evidence standards across political narratives.
```

---

## 24. Required Safety Checklist Before Final Demo

Before presenting RhetoriQ, verify:

- [ ] Demo does not claim absolute origin.
- [ ] Demo uses “first observed in our dataset.”
- [ ] Demo does not claim definitive astroturfing.
- [ ] Demo does not accuse real people or groups without evidence.
- [ ] Every major report claim has receipts.
- [ ] Receipt links are clickable.
- [ ] Counter-narrative section is visible.
- [ ] Source diversity caveat is visible.
- [ ] Confidence/limitations section is visible.
- [ ] Human review recommendations are visible.
- [ ] Agent debate shows skepticism and revision.
- [ ] Devpost does not overclaim.
- [ ] Synthetic/seeded demo data is not misrepresented as real if used.
- [ ] Sponsor explanations are accurate.

---

## 25. Final Ethical Positioning

RhetoriQ is built around this principle:

> **Civic AI should not ask users to trust the model. It should show users the evidence, uncertainty, competing narratives, and reasoning boundaries so they can investigate for themselves.**

The strongest version of RhetoriQ is not the version that sounds the most confident.

The strongest version is the one that is:

- useful
- transparent
- careful
- source-grounded
- nonpartisan in design
- honest about uncertainty
- backed by clickable receipts
- built for human review
