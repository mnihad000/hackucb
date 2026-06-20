import { hiddenEnergyTaxFlowchartData } from "../components/investigation-flowchart/demoInvestigationFlowchartData";
import type {
  ExamplePrompt,
  InvestigationExperience,
  InvestigationFlowchartData,
  InvestigationStatus,
  InvestigationStub,
  RadarTopic,
  RecentInvestigation,
} from "../types/rhetoriq";

export const examplePrompts: ExamplePrompt[] = [
  {
    id: "hidden-energy-tax",
    label: "Hidden energy tax",
    query: "Where did the hidden energy tax narrative come from?",
  },
  {
    id: "tiktok-ban",
    label: "TikTok ban",
    query: "Trace the story behind the TikTok ban.",
  },
  {
    id: "immigration-this-week",
    label: "Immigration this week",
    query: "What narratives are forming around immigration this week?",
  },
  {
    id: "education-policy",
    label: "Education policy",
    query: "Find counter-narratives around this education policy.",
  },
];

export const radarTopics: RadarTopic[] = [
  {
    id: "hidden-energy-tax",
    title: "Hidden Energy Tax",
    summary:
      "A cost-of-living frame moving from local energy commentary into broader political coverage.",
    spike: "7.4x",
    sourceCount: 26,
    firstObserved: "First observed in our dataset at 9:14 AM",
    status: "Amplifying",
    sourceMix: "Local blogs, community posts, national news",
    confidence: "Medium",
  },
  {
    id: "tiktok-ban",
    title: "TikTok Ban Narrative Shift",
    summary:
      "Coverage is moving from security framing toward creator-economy backlash and youth speech concerns.",
    spike: "5.8x",
    sourceCount: 19,
    firstObserved: "First observed in our dataset at 11:42 AM",
    status: "Reframing",
    sourceMix: "National news, creator posts, policy commentary",
    confidence: "High",
  },
  {
    id: "border-enforcement",
    title: "Border Enforcement Cost Narrative",
    summary:
      "Budget pressure language is clustering around state-level policy reactions and national campaign messaging.",
    spike: "4.9x",
    sourceCount: 21,
    firstObserved: "First observed in our dataset at 8:07 AM",
    status: "Emerging",
    sourceMix: "State officials, local news, campaign clips",
    confidence: "Medium",
  },
  {
    id: "classroom-curriculum",
    title: "Classroom Curriculum Flashpoint",
    summary:
      "School-board rhetoric is being recast into broader culture-war framing with fast phrase reuse.",
    spike: "6.1x",
    sourceCount: 17,
    firstObserved: "First observed in our dataset at 1:26 PM",
    status: "Escalating",
    sourceMix: "School board posts, advocacy blogs, talk radio clips",
    confidence: "Medium",
  },
  {
    id: "campaign-deepfakes",
    title: "Campaign Deepfake Warnings",
    summary:
      "Competing frames are splitting between election-security warnings and claims of overreaction.",
    spike: "3.7x",
    sourceCount: 14,
    firstObserved: "First observed in our dataset at 10:03 AM",
    status: "Splitting",
    sourceMix: "Tech policy reporters, official statements, viral clips",
    confidence: "Low",
  },
];

export const recentInvestigations: RecentInvestigation[] = [
  {
    id: "tiktok-ban",
    title: "TikTok Ban Narrative Shift",
    summary:
      "Tracks how creator-economy language caught up with national security framing.",
    updatedAt: "Updated 34 minutes ago",
    receiptCount: 8,
    focus: "Counter-narratives",
  },
  {
    id: "hidden-energy-tax",
    title: "Hidden Energy Tax",
    summary:
      "Maps a local-to-national spread pattern with cautious coordination language.",
    updatedAt: "Updated 52 minutes ago",
    receiptCount: 9,
    focus: "Timeline and receipts",
  },
  {
    id: "campaign-deepfakes",
    title: "Campaign Deepfake Warnings",
    summary:
      "Shows where the conversation splits between safety concerns and free-expression pushback.",
    updatedAt: "Updated 1 hour ago",
    receiptCount: 6,
    focus: "Source diversity",
  },
];

type InvestigationSeed = {
  confidence: "Low" | "Medium" | "High";
  currentNarrativeLabel?: string;
  currentNarrativeStatus?: InvestigationStatus;
  generatedAt: string;
  id: string;
  firstObserved: string;
  kicker: string;
  query?: string;
  status: string;
  summary: string;
  title: string;
};

const investigationSeeds: Record<string, InvestigationSeed> = {
  demo: {
    confidence: "Medium",
    generatedAt: "Seeded demo walkthrough",
    id: "demo",
    firstObserved: "First observed source shown in seeded dataset",
    kicker: "Seeded narrative path walkthrough",
    query: "Ask about any political story, claim, phrase, or issue...",
    status: "Source-grounded preview",
    summary:
      "This seeded investigation preview routes custom questions into a full narrative path map with evidence, branching context, and cautious language. The live backend is not connected yet, so the flow stays reliable while the investigation surface matures.",
    title: "Narrative Investigation Preview",
  },
  "hidden-energy-tax": {
    confidence: "Medium",
    currentNarrativeLabel: "Hidden Energy Tax",
    currentNarrativeStatus: "amplifying",
    generatedAt: "Generated 4 minutes ago",
    id: "hidden-energy-tax",
    firstObserved: "Local Energy Watch, 9:14 AM",
    kicker: "Narrative path map",
    status: "Source-grounded report",
    summary:
      "In the observed dataset, the phrase appears first in local energy politics coverage before spreading through community posts, local news, advocacy framing, and later national pickup. Several sources reuse similar cost language, which is consistent with rapid amplification. The evidence is still insufficient to conclude coordinated intent, so human review should verify whether earlier off-dataset sources exist.",
    title: "Hidden Energy Tax Investigation",
  },
  "tiktok-ban": {
    confidence: "High",
    currentNarrativeLabel: "TikTok Ban Narrative Shift",
    currentNarrativeStatus: "mainstreaming",
    generatedAt: "Generated from seeded flowchart data",
    id: "tiktok-ban",
    firstObserved: "Capitol Signal, 11:42 AM",
    kicker: "Counter-narrative preview",
    query: "Trace the story behind the TikTok ban.",
    status: "Human review recommended",
    summary:
      "The early framing centers on national security, but later posts shift the conversation toward creators, small-business impact, and youth speech concerns. This seeded page reuses the canonical flowchart structure while preserving the same evidence-first interaction model.",
    title: "TikTok Ban Narrative Investigation",
  },
  "border-enforcement": {
    confidence: "Medium",
    currentNarrativeLabel: "Border Enforcement Cost Narrative",
    currentNarrativeStatus: "emerging",
    generatedAt: "Generated from seeded flowchart data",
    id: "border-enforcement",
    firstObserved: "Southwest Ledger, 8:07 AM",
    kicker: "Emerging narrative preview",
    query: "What narratives are forming around border enforcement this week?",
    status: "Signals consistent with amplification",
    summary:
      "Budget pressure language is spreading across state-level reactions and campaign messaging, with several sources converging on similar phrasing. This seeded view keeps the cinematic investigation surface functional while richer route-specific datasets are added later.",
    title: "Border Enforcement Cost Investigation",
  },
  "classroom-curriculum": {
    confidence: "Medium",
    currentNarrativeLabel: "Classroom Curriculum Flashpoint",
    currentNarrativeStatus: "amplifying",
    generatedAt: "Generated from seeded flowchart data",
    id: "classroom-curriculum",
    firstObserved: "County Board Monitor, 1:26 PM",
    kicker: "Narrative family preview",
    query: "Find counter-narratives around this education policy.",
    status: "Cautious framing applied",
    summary:
      "Local conflict language is being folded into a broader culture-war frame, with related branches and counter-frames appearing quickly. The current phase focuses on the flowchart as the premium investigation surface before the family-tree module lands separately.",
    title: "Classroom Curriculum Investigation",
  },
  "campaign-deepfakes": {
    confidence: "Low",
    currentNarrativeLabel: "Campaign Deepfake Warnings",
    currentNarrativeStatus: "emerging",
    generatedAt: "Generated from seeded flowchart data",
    id: "campaign-deepfakes",
    firstObserved: "Civic Tech Brief, 10:03 AM",
    kicker: "Split-frame preview",
    query: "How are campaign deepfake warnings spreading right now?",
    status: "Competing narratives mapped",
    summary:
      "The tracked conversation divides between election-integrity warnings and skepticism about regulation. This seeded route keeps the investigation workspace usable while route-specific evidence and receipts are expanded.",
    title: "Campaign Deepfakes Investigation",
  },
};

function cloneFlowchartData(
  data: InvestigationFlowchartData,
): InvestigationFlowchartData {
  return {
    ...data,
    edges: data.edges.map((edge) => ({ ...edge })),
    nodes: data.nodes.map((node) => ({
      ...node,
      receipts: node.receipts?.map((receipt) => ({ ...receipt })),
      sources: node.sources?.map((source) => ({ ...source })),
    })),
  };
}

function countInvestigationReceipts(data: InvestigationFlowchartData) {
  const receiptIds = new Set<string>();

  for (const node of data.nodes) {
    for (const receipt of node.receipts ?? []) {
      receiptIds.add(receipt.id);
    }
  }

  return receiptIds.size;
}

function createFlowchartVariant(
  seed: InvestigationSeed,
  query?: string,
): InvestigationFlowchartData {
  const flowchartData = cloneFlowchartData(hiddenEnergyTaxFlowchartData);
  const currentNode = flowchartData.nodes.find(
    (node) => node.id === flowchartData.currentNodeId,
  );

  flowchartData.title = seed.title;
  flowchartData.query = query ?? seed.query ?? flowchartData.query;

  if (currentNode) {
    currentNode.label = seed.currentNarrativeLabel ?? currentNode.label;
    currentNode.status = seed.currentNarrativeStatus ?? currentNode.status;
  }

  return flowchartData;
}

export function createInvestigationHref(id: string, query?: string) {
  const search = query ? `?q=${encodeURIComponent(query)}` : "";
  return `/investigation/${id}${search}`;
}

export function getInvestigationStub(id: string) {
  const seed = investigationSeeds[id] ?? investigationSeeds.demo;

  return {
    firstObserved: seed.firstObserved,
    id: seed.id,
    kicker: seed.kicker,
    status: seed.status,
    summary: seed.summary,
    title: seed.title,
  } satisfies InvestigationStub;
}

export function getInvestigationExperience(
  id: string,
  query?: string,
): InvestigationExperience {
  const seed = investigationSeeds[id] ?? investigationSeeds.demo;
  const flowchartData = createFlowchartVariant(seed, query);
  const currentNode = flowchartData.nodes.find(
    (node) => node.id === flowchartData.currentNodeId,
  );

  return {
    confidence: seed.confidence,
    firstObserved: seed.firstObserved,
    flowchartData,
    generatedAt: seed.generatedAt,
    id: seed.id,
    kicker: seed.kicker,
    receiptCount: countInvestigationReceipts(flowchartData),
    sourceCount:
      currentNode?.sourceCount ??
      flowchartData.nodes.reduce((sum, node) => sum + node.sourceCount, 0),
    status: seed.status,
    summary: seed.summary,
    title: seed.title,
  };
}
