import type { InvestigationFlowchartData } from "../../types/rhetoriq";

export const hiddenEnergyTaxFlowchartData: InvestigationFlowchartData = {
  title: "Hidden Energy Tax Investigation",
  query: "Where did the hidden energy tax narrative come from?",
  currentNodeId: "current-narrative",
  nodes: [
    {
      id: "uncertain-earlier-mention",
      label: "Earlier Mention",
      subtitle: "Needs review",
      nodeType: "uncertain",
      timestamp: "8:21 AM",
      status: "unknown",
      confidence: "low",
      sourceCount: 1,
      receiptCount: 1,
      summary:
        "A similar cost claim appears earlier in one forum thread, but the wording and source chain are too weak to treat as a reliable starting point.",
      sources: [
        {
          id: "src-uncertain-1",
          name: "Metro Utility Forum",
          type: "Community post",
          title: "Utility bills thread raises a hidden fee concern",
          url: "https://example.com/metro-utility-forum",
          publishedAt: "8:21 AM",
          snippet:
            "One commenter suggests a hidden fee may be buried in the next rate filing, but no source document is linked.",
          stance: "unknown",
        },
      ],
      receipts: [
        {
          id: "rcpt-uncertain-1",
          sourceName: "Metro Utility Forum",
          title: "Utility bills thread raises a hidden fee concern",
          url: "https://example.com/metro-utility-forum",
          quoteOrSnippet:
            "There may be a hidden fee in the next utility filing, but I cannot find the document yet.",
          supportReason:
            "Shows a weak earlier mention that uses similar cost language but lacks enough grounding to count as the first observed source.",
        },
      ],
    },
    {
      id: "first-observed",
      label: "First Observed",
      subtitle: "Local Energy Watch",
      nodeType: "first_observed",
      timestamp: "9:14 AM",
      status: "emerging",
      confidence: "high",
      sourceCount: 2,
      receiptCount: 1,
      summary:
        "The clearest first observed phrasing in the current dataset appears in a local energy politics blog post focused on rate changes.",
      sources: [
        {
          id: "src-first-1",
          name: "Local Energy Watch",
          type: "Local blog",
          title: "Why residents are calling the latest rate package a hidden energy tax",
          url: "https://example.com/local-energy-watch",
          publishedAt: "9:14 AM",
          snippet:
            "The post frames the rate package as a hidden energy tax on working households and links to the public utility filing.",
          stance: "supporting",
        },
        {
          id: "src-first-2",
          name: "City Utility Notes",
          type: "Policy newsletter",
          title: "Morning rate filing roundup",
          url: "https://example.com/city-utility-notes",
          publishedAt: "9:22 AM",
          snippet:
            "A short briefing echoes the same hidden energy tax phrase while summarizing the cost impact claim.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-first-1",
          sourceName: "Local Energy Watch",
          title: "Why residents are calling the latest rate package a hidden energy tax",
          url: "https://example.com/local-energy-watch",
          quoteOrSnippet:
            "The latest rate package is being framed by critics as a hidden energy tax on monthly bills.",
          supportReason:
            "This is the earliest clearly sourced phrasing in the seeded dataset and anchors the first observed claim.",
          browserVerified: true,
        },
      ],
    },
    {
      id: "community-pickup",
      label: "Community Pickup",
      subtitle: "Neighborhood forums and reposts",
      nodeType: "amplification",
      timestamp: "9:48 AM",
      status: "emerging",
      confidence: "medium",
      sourceCount: 3,
      receiptCount: 1,
      summary:
        "Forum reposts and local social feeds reuse the cost framing and make the phrase easier to circulate beyond the original post.",
      sources: [
        {
          id: "src-community-1",
          name: "Northside Neighbors",
          type: "Community post",
          title: "Watch out for this hidden energy tax story",
          url: "https://example.com/northside-neighbors",
          publishedAt: "9:48 AM",
          snippet:
            "A neighborhood forum post links the local blog and repeats the same headline phrase almost verbatim.",
          stance: "supporting",
        },
        {
          id: "src-community-2",
          name: "Local Cost Tracker",
          type: "Facebook group",
          title: "Bills could jump under a hidden energy tax",
          url: "https://example.com/local-cost-tracker",
          publishedAt: "9:55 AM",
          snippet:
            "Members repost the framing with screenshots rather than linking back to the filing itself.",
          stance: "supporting",
        },
        {
          id: "src-community-3",
          name: "Town Hall Notes",
          type: "Community newsletter",
          title: "Rate package sparks early cost backlash",
          url: "https://example.com/town-hall-notes",
          publishedAt: "10:01 AM",
          snippet:
            "The newsletter references the backlash and treats the hidden energy tax phrase as the shorthand readers already recognize.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-community-1",
          sourceName: "Northside Neighbors",
          title: "Watch out for this hidden energy tax story",
          url: "https://example.com/northside-neighbors",
          quoteOrSnippet:
            "This hidden energy tax story is exactly what people warned about in the filing debate.",
          supportReason:
            "Shows the phrase moving into community spaces and being reused without additional sourcing.",
        },
      ],
    },
    {
      id: "policy-blogs",
      label: "Policy Blog Amplification",
      subtitle: "Advocacy and issue blogs",
      nodeType: "amplification",
      timestamp: "10:42 AM",
      status: "amplifying",
      confidence: "medium",
      sourceCount: 3,
      receiptCount: 1,
      summary:
        "Issue-focused blogs standardize the cost frame and push it into a more reusable policy argument.",
      sources: [
        {
          id: "src-policy-1",
          name: "Grid Policy Review",
          type: "Policy blog",
          title: "The hidden energy tax framing gains traction",
          url: "https://example.com/grid-policy-review",
          publishedAt: "10:42 AM",
          snippet:
            "The post keeps the phrase but shifts into a broader argument about regulatory costs.",
          stance: "supporting",
        },
        {
          id: "src-policy-2",
          name: "Household Rate Brief",
          type: "Issue blog",
          title: "Why the hidden energy tax label is spreading",
          url: "https://example.com/household-rate-brief",
          publishedAt: "10:57 AM",
          snippet:
            "The blog compares local language and turns the phrase into a reusable political shorthand.",
          stance: "supporting",
        },
        {
          id: "src-policy-3",
          name: "Regional Docket Notes",
          type: "Newsletter",
          title: "Rate filing context and rhetoric",
          url: "https://example.com/regional-docket-notes",
          publishedAt: "11:04 AM",
          snippet:
            "The roundup notes the phrase is spreading faster than the underlying filing details.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-policy-1",
          sourceName: "Grid Policy Review",
          title: "The hidden energy tax framing gains traction",
          url: "https://example.com/grid-policy-review",
          quoteOrSnippet:
            "What began as a local complaint is turning into a broader hidden energy tax argument.",
          supportReason:
            "Captures the shift from local complaint to more reusable policy framing.",
        },
      ],
    },
    {
      id: "local-news",
      label: "Local News Pickup",
      subtitle: "Regional outlets repeat the frame",
      nodeType: "media_pickup",
      timestamp: "11:36 AM",
      status: "amplifying",
      confidence: "medium",
      sourceCount: 4,
      receiptCount: 1,
      summary:
        "Regional outlets adopt the phrase in headlines and summaries, widening reach without independently resolving the underlying claim.",
      sources: [
        {
          id: "src-local-1",
          name: "River City Bulletin",
          type: "Local news",
          title: "Critics call rate package a hidden energy tax",
          url: "https://example.com/river-city-bulletin",
          publishedAt: "11:36 AM",
          snippet:
            "The outlet quotes critics and repeats the headline phrase in its summary deck.",
          stance: "supporting",
        },
        {
          id: "src-local-2",
          name: "Morning Signal Radio",
          type: "Local radio transcript",
          title: "Rate package backlash grows",
          url: "https://example.com/morning-signal-radio",
          publishedAt: "11:49 AM",
          snippet:
            "A radio segment introduces the hidden energy tax phrase to a wider commuter audience.",
          stance: "context",
        },
        {
          id: "src-local-3",
          name: "Capital District Daily",
          type: "Local news",
          title: "Utility fight adds hidden energy tax language",
          url: "https://example.com/capital-district-daily",
          publishedAt: "11:53 AM",
          snippet:
            "The summary attributes the wording to local critics rather than asserting it as settled fact.",
          stance: "supporting",
        },
        {
          id: "src-local-4",
          name: "City Hall Stream",
          type: "Transcript",
          title: "Council members react to rate package",
          url: "https://example.com/city-hall-stream",
          publishedAt: "12:01 PM",
          snippet:
            "A live stream chat repeats the phrase while the hearing itself stays more procedural.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-local-1",
          sourceName: "River City Bulletin",
          title: "Critics call rate package a hidden energy tax",
          url: "https://example.com/river-city-bulletin",
          quoteOrSnippet:
            "Critics are describing the proposal as a hidden energy tax on monthly household bills.",
          supportReason:
            "Shows the narrative moving from blogs and community posts into local newsroom language.",
        },
      ],
    },
    {
      id: "advocacy-framing",
      label: "Advocacy Group Framing",
      subtitle: "Cost-of-living language is standardized",
      nodeType: "related",
      timestamp: "12:24 PM",
      status: "amplifying",
      confidence: "medium",
      sourceCount: 3,
      receiptCount: 1,
      summary:
        "Advocacy messaging turns the phrase into a cleaner cost-of-living frame that can travel beyond the original local dispute.",
      sources: [
        {
          id: "src-advocacy-1",
          name: "Families for Fair Rates",
          type: "Advocacy statement",
          title: "Families deserve answers on the hidden energy tax",
          url: "https://example.com/families-for-fair-rates",
          publishedAt: "12:24 PM",
          snippet:
            "An advocacy group uses the phrase in a cleaner, more repeatable message about household costs.",
          stance: "supporting",
        },
        {
          id: "src-advocacy-2",
          name: "Pocketbook Agenda",
          type: "Issue campaign email",
          title: "A new pocketbook warning spreads",
          url: "https://example.com/pocketbook-agenda",
          publishedAt: "12:38 PM",
          snippet:
            "The email links cost-of-living pressure to the hidden energy tax frame for supporters.",
          stance: "supporting",
        },
        {
          id: "src-advocacy-3",
          name: "Public Utility Fact Sheet",
          type: "Official context",
          title: "Utility filing background note",
          url: "https://example.com/public-utility-fact-sheet",
          publishedAt: "12:40 PM",
          snippet:
            "An official fact sheet offers context but does not use the hidden energy tax phrase itself.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-advocacy-1",
          sourceName: "Families for Fair Rates",
          title: "Families deserve answers on the hidden energy tax",
          url: "https://example.com/families-for-fair-rates",
          quoteOrSnippet:
            "Families deserve answers before this hidden energy tax becomes the new normal on monthly bills.",
          supportReason:
            "Illustrates the phrase being standardized into advocacy-friendly cost-of-living rhetoric.",
        },
      ],
    },
    {
      id: "official-transcript",
      label: "Official Mention",
      subtitle: "Committee hearing transcript",
      nodeType: "official_mention",
      timestamp: "1:32 PM",
      status: "unknown",
      confidence: "medium",
      sourceCount: 2,
      receiptCount: 1,
      summary:
        "The phrase surfaces in hearing reactions and transcript annotations, showing institutional visibility without proving official adoption of the frame.",
      sources: [
        {
          id: "src-official-1",
          name: "State Energy Committee",
          type: "Transcript",
          title: "Rate package oversight hearing",
          url: "https://example.com/state-energy-committee",
          publishedAt: "1:32 PM",
          snippet:
            "A committee exchange references concerns being described publicly as a hidden energy tax.",
          stance: "context",
        },
        {
          id: "src-official-2",
          name: "Legislative Clip Desk",
          type: "Official clip summary",
          title: "Hearing highlights spread online",
          url: "https://example.com/legislative-clip-desk",
          publishedAt: "1:41 PM",
          snippet:
            "Clipped highlights package the phrase for sharing without adding new documentary support.",
          stance: "supporting",
        },
      ],
      receipts: [
        {
          id: "rcpt-official-1",
          sourceName: "State Energy Committee",
          title: "Rate package oversight hearing",
          url: "https://example.com/state-energy-committee",
          quoteOrSnippet:
            "Public comments have described the proposal as a hidden energy tax, and we need to address that concern directly.",
          supportReason:
            "Shows the narrative entering official discussion spaces as a referenced public frame.",
          browserVerified: true,
        },
      ],
    },
    {
      id: "national-pickup",
      label: "National Media Pickup",
      subtitle: "Cable clips and newsletter summaries",
      nodeType: "media_pickup",
      timestamp: "2:18 PM",
      status: "mainstreaming",
      confidence: "high",
      sourceCount: 4,
      receiptCount: 1,
      summary:
        "National outlets condense the local cost argument into a reusable political talking point with broader reach.",
      sources: [
        {
          id: "src-national-1",
          name: "National Policy Wire",
          type: "National news",
          title: "Hidden energy tax phrase jumps from local fight to national politics",
          url: "https://example.com/national-policy-wire",
          publishedAt: "2:18 PM",
          snippet:
            "A national roundup treats the phrase as the recognizable shorthand for the dispute.",
          stance: "supporting",
        },
        {
          id: "src-national-2",
          name: "Cable Briefing Desk",
          type: "Broadcast summary",
          title: "Cost backlash hits the national conversation",
          url: "https://example.com/cable-briefing-desk",
          publishedAt: "2:26 PM",
          snippet:
            "Short segments repeat the hidden energy tax frame with little additional sourcing.",
          stance: "supporting",
        },
        {
          id: "src-national-3",
          name: "Campaign Memo",
          type: "Newsletter",
          title: "How one local phrase became a national cue",
          url: "https://example.com/campaign-memo",
          publishedAt: "2:31 PM",
          snippet:
            "The memo notes that cost-of-living language helped the phrase travel quickly.",
          stance: "context",
        },
        {
          id: "src-national-4",
          name: "Desk Notes Live",
          type: "Live blog",
          title: "Rate package backlash enters the afternoon cycle",
          url: "https://example.com/desk-notes-live",
          publishedAt: "2:35 PM",
          snippet:
            "A live political blog packages the phrase as part of the broader afternoon news cycle.",
          stance: "supporting",
        },
      ],
      receipts: [
        {
          id: "rcpt-national-1",
          sourceName: "National Policy Wire",
          title: "Hidden energy tax phrase jumps from local fight to national politics",
          url: "https://example.com/national-policy-wire",
          quoteOrSnippet:
            "What started as a local backlash is now circulating nationally as a hidden energy tax argument.",
          supportReason:
            "Marks the point where the phrase becomes nationally legible as a political shorthand.",
        },
      ],
    },
    {
      id: "counter-savings",
      label: "Counter-frame",
      subtitle: "\"Long-term savings\" response",
      nodeType: "counter_narrative",
      timestamp: "2:44 PM",
      status: "emerging",
      confidence: "medium",
      sourceCount: 3,
      counterSourceCount: 3,
      receiptCount: 1,
      summary:
        "A competing frame argues that near-term cost complaints ignore long-term savings and infrastructure benefits.",
      sources: [
        {
          id: "src-counter-1",
          name: "Clean Grid Coalition",
          type: "Advocacy response",
          title: "Long-term savings should not be erased by a hidden tax label",
          url: "https://example.com/clean-grid-coalition",
          publishedAt: "2:44 PM",
          snippet:
            "The response argues that the hidden energy tax frame ignores future savings and system upgrades.",
          stance: "opposing",
        },
        {
          id: "src-counter-2",
          name: "Energy Transition Facts",
          type: "Issue explainer",
          title: "Short-term cost versus long-term savings",
          url: "https://example.com/energy-transition-facts",
          publishedAt: "2:52 PM",
          snippet:
            "The explainer explicitly counters the hidden energy tax phrase with future savings language.",
          stance: "opposing",
        },
        {
          id: "src-counter-3",
          name: "Utility Modernization Project",
          type: "Official statement",
          title: "Project team pushes back on tax framing",
          url: "https://example.com/utility-modernization-project",
          publishedAt: "2:58 PM",
          snippet:
            "Project officials avoid the phrase and stress reliability and long-term value instead.",
          stance: "opposing",
        },
      ],
      receipts: [
        {
          id: "rcpt-counter-1",
          sourceName: "Clean Grid Coalition",
          title: "Long-term savings should not be erased by a hidden tax label",
          url: "https://example.com/clean-grid-coalition",
          quoteOrSnippet:
            "Calling this a hidden energy tax leaves out the long-term savings and reliability benefits.",
          supportReason:
            "Represents the clearest counter-frame that emerges once the cost narrative grows louder.",
        },
      ],
    },
    {
      id: "current-narrative",
      label: "Hidden Energy Tax",
      subtitle: "Current narrative",
      nodeType: "current",
      timestamp: "4:05 PM",
      status: "amplifying",
      confidence: "medium",
      sourceCount: 26,
      counterSourceCount: 5,
      receiptCount: 3,
      summary:
        "The phrase is now circulating as a cost-of-living frame across local, advocacy, and national coverage. The observed spread is consistent with rapid amplification, but not enough to conclude coordinated intent.",
      sources: [
        {
          id: "src-current-1",
          name: "Afternoon Campaign Monitor",
          type: "Newsletter",
          title: "Hidden energy tax enters the daily briefing",
          url: "https://example.com/afternoon-campaign-monitor",
          publishedAt: "4:05 PM",
          snippet:
            "The daily briefing treats the phrase as familiar enough to headline without re-explaining the local context.",
          stance: "supporting",
        },
        {
          id: "src-current-2",
          name: "Prime Desk Clips",
          type: "Broadcast summary",
          title: "Cost frame dominates the evening setup",
          url: "https://example.com/prime-desk-clips",
          publishedAt: "4:11 PM",
          snippet:
            "Evening rundown language shows the phrase has entered the wider political shorthand.",
          stance: "supporting",
        },
        {
          id: "src-current-3",
          name: "Statehouse Notes",
          type: "Political memo",
          title: "Narrative watch: hidden energy tax",
          url: "https://example.com/statehouse-notes",
          publishedAt: "4:18 PM",
          snippet:
            "The memo tracks how the phrase is spreading and notes the emerging counter-frame.",
          stance: "context",
        },
      ],
      receipts: [
        {
          id: "rcpt-current-1",
          sourceName: "Afternoon Campaign Monitor",
          title: "Hidden energy tax enters the daily briefing",
          url: "https://example.com/afternoon-campaign-monitor",
          quoteOrSnippet:
            "By late afternoon, the hidden energy tax label has become the dominant shorthand for the rate debate.",
          supportReason:
            "Anchors the claim that the phrase becomes the current dominant narrative state in the seeded dataset.",
          browserVerified: true,
        },
        {
          id: "rcpt-current-2",
          sourceName: "Statehouse Notes",
          title: "Narrative watch: hidden energy tax",
          url: "https://example.com/statehouse-notes",
          quoteOrSnippet:
            "The frame is amplifying quickly, but the dataset still does not prove coordinated intent.",
          supportReason:
            "Supports the cautious language used in the executive summary and current node description.",
        },
        {
          id: "rcpt-current-3",
          sourceName: "Prime Desk Clips",
          title: "Cost frame dominates the evening setup",
          url: "https://example.com/prime-desk-clips",
          quoteOrSnippet:
            "The evening setup treats the hidden energy tax phrase as already familiar to a national audience.",
          supportReason:
            "Supports the claim that the phrase has matured into the latest narrative state rather than a local niche argument.",
        },
      ],
    },
  ],
  edges: [
    {
      id: "edge-uncertain-community",
      source: "uncertain-earlier-mention",
      target: "community-pickup",
      edgeType: "uncertain",
      label: "Needs review",
      evidenceText:
        "One earlier post uses similar language, but the evidence chain is weak and incomplete.",
      confidence: "low",
    },
    {
      id: "edge-first-community",
      source: "first-observed",
      target: "community-pickup",
      edgeType: "temporal_sequence",
      label: "Later pickup",
      evidenceText:
        "Community posts begin circulating after the first clearly sourced blog post appears.",
      confidence: "high",
      animated: true,
    },
    {
      id: "edge-community-policy",
      source: "community-pickup",
      target: "policy-blogs",
      edgeType: "exact_phrase_reuse",
      label: "Same phrase",
      evidenceText:
        "The policy blogs reuse the same hidden energy tax wording that appeared in community reposts.",
      confidence: "medium",
      animated: true,
    },
    {
      id: "edge-policy-local",
      source: "policy-blogs",
      target: "local-news",
      edgeType: "semantic_similarity",
      label: "Similar framing",
      evidenceText:
        "Local newsroom coverage picks up the same cost framing even when the exact wording shifts slightly.",
      confidence: "medium",
      animated: true,
    },
    {
      id: "edge-local-advocacy",
      source: "local-news",
      target: "advocacy-framing",
      edgeType: "source_link",
      label: "Source cited",
      evidenceText:
        "Advocacy statements reference the local coverage and use it to standardize the phrase.",
      confidence: "medium",
      animated: true,
    },
    {
      id: "edge-advocacy-national",
      source: "advocacy-framing",
      target: "national-pickup",
      edgeType: "temporal_sequence",
      label: "Later pickup",
      evidenceText:
        "The advocacy frame becomes visible in national roundups later in the day.",
      confidence: "high",
      animated: true,
    },
    {
      id: "edge-national-current",
      source: "national-pickup",
      target: "current-narrative",
      edgeType: "semantic_similarity",
      label: "Current state",
      evidenceText:
        "The national pickup settles into the current dominant narrative state seen at the right edge of the map.",
      confidence: "high",
      animated: true,
    },
    {
      id: "edge-policy-national",
      source: "policy-blogs",
      target: "national-pickup",
      edgeType: "semantic_similarity",
      label: "Phrase convergence",
      evidenceText:
        "National summaries converge on the phrase after it becomes common across policy and local media spaces.",
      confidence: "low",
    },
    {
      id: "edge-local-official",
      source: "local-news",
      target: "official-transcript",
      edgeType: "related_context",
      label: "Official mention",
      evidenceText:
        "The frame becomes visible in hearing context once local coverage has already amplified it.",
      confidence: "medium",
    },
    {
      id: "edge-official-current",
      source: "official-transcript",
      target: "current-narrative",
      edgeType: "temporal_sequence",
      label: "Later pickup",
      evidenceText:
        "The official mention helps signal broader visibility even though it does not settle the underlying claim.",
      confidence: "medium",
    },
    {
      id: "edge-local-counter",
      source: "local-news",
      target: "counter-savings",
      edgeType: "counter_narrative",
      label: "Counter-frame",
      evidenceText:
        "A long-term savings argument emerges as a direct response once the cost frame gains more attention.",
      confidence: "medium",
    },
    {
      id: "edge-counter-current",
      source: "counter-savings",
      target: "current-narrative",
      edgeType: "counter_narrative",
      label: "Competing response",
      evidenceText:
        "The counter-frame runs alongside the amplifying current narrative rather than replacing it.",
      confidence: "medium",
    },
  ],
};
