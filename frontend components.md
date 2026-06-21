# Frontend Components

## Key Claims
- Removed from the shared investigation page in both mock and live modes.
- This section rendered the report claim cards with confidence, support, and verification badges.
- It repeated conclusions already implied by the report, timeline, and broader investigation state.
- The card stack added a lot of vertical weight without helping first-pass comprehension.
- Source links inside the cards were useful, but the surrounding framing was too dense for the main page.
- The page now relies on stronger primary structures instead of a separate claim-summary block.

## Narrative Family
- Removed from the shared investigation page in both mock and live modes.
- This section showed the parent frame, mutation rail, branch list, and branch metadata.
- It was visually large and demanded too much attention relative to its value in the primary flow.
- The mutation and branch breakdown made the page feel over-explained and harder to scan.
- Family analysis can return later in a more compact or secondary experience if needed.
- For now, the main investigation page stays focused on higher-signal core content.

## Retriever Warnings
- Removed from the shared investigation page in both mock and live modes.
- This panel listed retrieval caveats and backend warnings from the workspace data.
- In practice it surfaced implementation-oriented noise instead of helping the user understand the story.
- The warnings were especially distracting in mock mode because they described fixture behavior.
- Error and missing-state handling still remain elsewhere on the page when genuinely needed.
- The investigation view is now less cluttered by diagnostic-only copy.

## Rival Hypotheses
- Removed from the shared investigation page in both mock and live modes.
- This panel listed alternative interpretations and short rationales.
- The content was interesting, but it competed with the main narrative instead of clarifying it.
- On a dense page, it felt like a second analysis layer before the primary one had landed.
- Removing it makes the right-hand rail less noisy and more readable.
- If reintroduced later, it should likely be collapsed or moved into a drill-down view.

## Coverage
- Removed from the shared investigation page in both mock and live modes.
- This card summarized document counts, source counts, and search-round metadata.
- It read more like system telemetry than user-facing investigation substance.
- The metrics were not helping users decide what to read next or what mattered most.
- Coverage detail still exists in the underlying workspace data if needed for future tooling.
- The visible page now avoids spending precious space on inventory-style stats.

## Source Diversity
- Removed from the shared investigation page in both mock and live modes.
- This card showed distribution counts, classifications, findings, and caveats.
- While useful for evaluation, it added too much taxonomy and numerical detail to the main experience.
- The section interrupted narrative flow with a methodology-heavy sidebar.
- It is better suited for an advanced analysis surface than the default investigation page.
- The page is now more focused on understanding the story rather than auditing the dataset mix.

## Limitations
- Removed from the shared investigation page in both mock and live modes.
- This panel aggregated caveats from multiple backend and mock investigation stages.
- In practice it became a long stack of implementation disclaimers instead of useful reading support.
- The mock version was especially noisy because many entries were fixture-oriented rather than user-oriented.
- Keeping it visible by default made the page feel defensive and over-instrumented.
- If limitations matter later, they should return in a more compact advanced-details surface.

## Timeline
- Removed from the shared investigation page in both mock and live modes.
- This section presented the investigation as a linear sequence of dated events and source pickups.
- It was useful for chronology, but on the current page it added another long reading block after the map.
- The result was too much duplication between the visual flowchart and the textual event list.
- Keeping both by default made the page longer and harder to scan.
- The investigation page now favors a lighter primary narrative surface over a second chronology module.

## Flowchart Guidance Note
- Removed from the shared investigation page in both mock and live modes.
- This was the short paragraph under the map about first-observed sources and coordination.
- The note repeated framing already established elsewhere in the experience.
- It also created extra separation between the map and the content below it.
- The map can stand on its own without an always-visible disclaimer block directly beneath it.
- This keeps the flowchart area visually tighter and reduces filler text.

## Flowchart Controls Panel
- Removed from the shared investigation page in both mock and live modes.
- This was the button group for reset view, fit view, replay animation, receipts, and counter-narratives.
- The controls took a large footprint and made the page feel tool-heavy instead of editorial.
- Most of the buttons supported exploration depth rather than primary reading.
- The flowchart still renders, but the surrounding control chrome is gone.
- This shifts the investigation page toward a cleaner default reading experience.
