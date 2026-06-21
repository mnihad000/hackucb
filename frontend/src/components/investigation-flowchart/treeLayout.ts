import type {
  InvestigationConfidence,
  InvestigationEdge,
  InvestigationFlowchartData,
  InvestigationNode,
} from "../../types/rhetoriq";

export type BranchVariant = "counter" | "related" | "uncertain";

export type TreeBranch = {
  node: InvestigationNode;
  variant: BranchVariant;
};

export type TreeRow = {
  node: InvestigationNode;
  branches: TreeBranch[];
  index: number;
  isOrigin: boolean;
  isCurrent: boolean;
};

/**
 * Walk the temporal trunk from the current narrative back to the origin, then
 * return it ordered origin -> current (top to bottom).
 */
function buildTrunk(data: InvestigationFlowchartData): InvestigationNode[] {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const incoming = new Map<string, InvestigationEdge[]>();

  for (const edge of data.edges) {
    const next = incoming.get(edge.target) ?? [];
    next.push(edge);
    incoming.set(edge.target, next);
  }

  const chain: string[] = [];
  const visited = new Set<string>();
  let cursor: string | undefined = data.currentNodeId;

  while (cursor && !visited.has(cursor) && nodeById.has(cursor)) {
    chain.push(cursor);
    visited.add(cursor);

    const temporal = (incoming.get(cursor) ?? []).filter(
      (edge) => edge.edgeType === "temporal_sequence",
    );
    const next = temporal.find(
      (edge) => nodeById.has(edge.source) && !visited.has(edge.source),
    );
    cursor = next?.source;
  }

  // chain is [current, ..., origin]; flip to [origin, ..., current]
  const ordered = chain
    .reverse()
    .map((id) => nodeById.get(id))
    .filter((node): node is InvestigationNode => Boolean(node));

  if (ordered.length > 0) {
    return ordered;
  }

  // Fallback: no temporal edges — keep the current node alone.
  const current = nodeById.get(data.currentNodeId);
  return current ? [current] : data.nodes.slice(0, 1);
}

function branchVariant(node: InvestigationNode): BranchVariant {
  switch (node.nodeType) {
    case "counter_narrative":
      return "counter";
    case "uncertain":
      return "uncertain";
    default:
      return "related";
  }
}

/**
 * Produce a top-to-bottom tree: a trunk (origin -> current) with branch nodes
 * (counter-frames, related context) anchored beneath the trunk step they relate to.
 */
export function buildTree(data: InvestigationFlowchartData): TreeRow[] {
  const trunk = buildTrunk(data);
  const trunkIds = new Set(trunk.map((node) => node.id));

  const rows: TreeRow[] = trunk.map((node, index) => ({
    node,
    branches: [],
    index,
    isOrigin: index === 0 && trunk.length > 1,
    isCurrent: node.id === data.currentNodeId,
  }));

  const rowByNodeId = new Map(rows.map((row) => [row.node.id, row]));
  const fallbackRow = rowByNodeId.get(data.currentNodeId) ?? rows[rows.length - 1];

  const branchNodes = data.nodes.filter((node) => !trunkIds.has(node.id));

  for (const node of branchNodes) {
    let anchorId: string | undefined;

    for (const edge of data.edges) {
      if (edge.source === node.id && trunkIds.has(edge.target)) {
        anchorId = edge.target;
        break;
      }
      if (edge.target === node.id && trunkIds.has(edge.source)) {
        anchorId = edge.source;
        break;
      }
    }

    const row = (anchorId && rowByNodeId.get(anchorId)) || fallbackRow;
    row?.branches.push({ node, variant: branchVariant(node) });
  }

  return rows;
}

export function pickNodeUrl(node: InvestigationNode): string | undefined {
  const sourceUrl = node.sources?.find((source) => source.url)?.url;
  if (sourceUrl) {
    return sourceUrl;
  }

  return node.receipts?.find((receipt) => receipt.url)?.url;
}

export function getNodeTypeLabel(nodeType: InvestigationNode["nodeType"]): string {
  switch (nodeType) {
    case "current":
      return "Current narrative";
    case "first_observed":
      return "Origin · first observed";
    case "amplification":
      return "Amplification";
    case "media_pickup":
      return "Media pickup";
    case "official_mention":
      return "Official mention";
    case "counter_narrative":
      return "Counter-frame";
    case "related":
      return "Related framing";
    case "uncertain":
      return "Needs review";
    default:
      return "Narrative moment";
  }
}

export function getConfidenceLabel(confidence?: InvestigationConfidence): string {
  if (!confidence || confidence === "unknown") {
    return "Unknown confidence";
  }

  return `${confidence.charAt(0).toUpperCase()}${confidence.slice(1)} confidence`;
}

export function countNodeReceipts(node: InvestigationNode): number {
  return node.receiptCount ?? node.receipts?.length ?? 0;
}

export function hasBrowserVerifiedReceipt(node: InvestigationNode): boolean {
  return (node.receipts ?? []).some((receipt) => receipt.browserVerified);
}

export function getNodeHost(node: InvestigationNode): string | undefined {
  const url = pickNodeUrl(node);
  if (!url) {
    return undefined;
  }

  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return undefined;
  }
}
