import type { Edge, Node, XYPosition } from "@xyflow/react";
import type {
  InvestigationConfidence,
  InvestigationEdge,
  InvestigationFlowchartData,
  InvestigationNode,
  InvestigationNodeSource,
  NodeState,
} from "../../types/rhetoriq";

export const FLOW_NODE_WIDTH = 420;
export const FLOW_NODE_HEIGHT = 204;
export const TIMELINE_AXIS_X = 620;

export type InvestigationFlowNodeData = {
  node: InvestigationNode;
  visualState: NodeState;
  isRevealed: boolean;
  isHighlighted: boolean;
  showReceipts: boolean;
  isCurrent: boolean;
  layoutSide: "left" | "right";
};

export type InvestigationFlowEdgeData = {
  edge: InvestigationEdge;
  variant: "main" | "counter" | "uncertain" | "related";
  isRevealed: boolean;
  isHighlighted: boolean;
  isDimmed: boolean;
  revealDirection: RevealDirection;
  revealDurationMs: number;
  showLabel: boolean;
};

export type InvestigationFlowNode = Node<
  InvestigationFlowNodeData,
  "investigationNode"
>;

export type InvestigationFlowEdge = Edge<
  InvestigationFlowEdgeData,
  "investigationEdge"
>;

export type RevealDirection = "forward" | "reverse";

type RevealBaseStep = {
  cameraAnchorId: string;
  cameraNodeId: string;
};

export type RevealStep =
  | ({
      kind: "edge";
      direction: RevealDirection;
      id: string;
    } & RevealBaseStep)
  | ({
      kind: "node";
      id: string;
    } & RevealBaseStep);

export type RevealPhaseId =
  | "current"
  | "main"
  | "supporting"
  | "counter"
  | "uncertain";

export type RevealPhase = {
  id: RevealPhaseId;
  steps: RevealStep[];
};

export type InvestigationRevealPlan = {
  phases: RevealPhase[];
};

type PathResult = {
  edgeIds: Set<string>;
  found: boolean;
  nodeIds: Set<string>;
};

const PRESET_POSITIONS: Record<string, XYPosition> = {
  "current-narrative": { x: 760, y: 80 },
  "national-pickup": { x: 20, y: 320 },
  "official-transcript": { x: 760, y: 470 },
  "advocacy-framing": { x: 760, y: 660 },
  "counter-savings": { x: 760, y: 840 },
  "local-news": { x: 20, y: 1010 },
  "policy-blogs": { x: 760, y: 1260 },
  "community-pickup": { x: 20, y: 1510 },
  "first-observed": { x: 760, y: 1750 },
  "uncertain-earlier-mention": { x: 20, y: 1920 },
};

export function getNodeTypeLabel(nodeType: InvestigationNode["nodeType"]) {
  switch (nodeType) {
    case "current":
      return "Current narrative";
    case "first_observed":
      return "First observed";
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

export function getConfidenceLabel(confidence?: InvestigationConfidence) {
  if (!confidence || confidence === "unknown") {
    return "Unknown confidence";
  }

  return `${confidence.charAt(0).toUpperCase()}${confidence.slice(1)} confidence`;
}

export function countNodeReceipts(node: InvestigationNode) {
  return node.receiptCount ?? node.receipts?.length ?? 0;
}

export function countInvestigationReceipts(data: InvestigationFlowchartData) {
  const receiptIds = new Set<string>();

  for (const node of data.nodes) {
    for (const receipt of node.receipts ?? []) {
      receiptIds.add(receipt.id);
    }
  }

  return receiptIds.size;
}

export function countInvestigationSources(data: InvestigationFlowchartData) {
  const currentNode = data.nodes.find((node) => node.id === data.currentNodeId);

  if (currentNode?.sourceCount) {
    return currentNode.sourceCount;
  }

  return data.nodes.reduce((sum, node) => sum + node.sourceCount, 0);
}

export function hasBrowserVerifiedReceipt(node: InvestigationNode) {
  return (node.receipts ?? []).some((receipt) => receipt.browserVerified);
}

export function splitSourcesByStance(node: InvestigationNode) {
  const supporting: InvestigationNodeSource[] = [];
  const opposing: InvestigationNodeSource[] = [];

  for (const source of node.sources ?? []) {
    if (source.stance === "opposing") {
      opposing.push(source);
      continue;
    }

    supporting.push(source);
  }

  return { opposing, supporting };
}

export function filterFlowchartData(
  data: InvestigationFlowchartData,
  showCounterNarratives: boolean,
) {
  if (showCounterNarratives) {
    return data;
  }

  const visibleNodes = data.nodes.filter(
    (node) =>
      node.nodeType !== "counter_narrative" && node.nodeType !== "uncertain",
  );
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = data.edges.filter(
    (edge) =>
      visibleIds.has(edge.source) &&
      visibleIds.has(edge.target) &&
      edge.edgeType !== "counter_narrative" &&
      edge.edgeType !== "uncertain",
  );

  return {
    ...data,
    edges: visibleEdges,
    nodes: visibleNodes,
  };
}

function getFallbackPositions(data: InvestigationFlowchartData) {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const incomingCounts = new Map<string, number>(
    data.nodes.map((node) => [node.id, 0]),
  );
  const outgoing = new Map<string, string[]>();

  for (const edge of data.edges) {
    incomingCounts.set(edge.target, (incomingCounts.get(edge.target) ?? 0) + 1);
    const next = outgoing.get(edge.source) ?? [];
    next.push(edge.target);
    outgoing.set(edge.source, next);
  }

  const queue = data.nodes
    .filter((node) => (incomingCounts.get(node.id) ?? 0) === 0)
    .map((node) => node.id);
  const ordered: string[] = [];

  while (queue.length > 0) {
    const currentId = queue.shift();

    if (!currentId) {
      continue;
    }

    ordered.push(currentId);

    for (const nextId of outgoing.get(currentId) ?? []) {
      const remaining = (incomingCounts.get(nextId) ?? 1) - 1;
      incomingCounts.set(nextId, remaining);

      if (remaining === 0) {
        queue.push(nextId);
      }
    }
  }

  const depthMap = new Map<string, number>();

  for (const nodeId of ordered) {
    const parentEdges = data.edges.filter((edge) => edge.target === nodeId);
    const depth =
      parentEdges.length === 0
        ? 0
        : Math.max(
            ...parentEdges.map(
              (edge) => (depthMap.get(edge.source) ?? 0) + 1,
            ),
          );

    depthMap.set(nodeId, depth);
  }

  const laneBase: Record<InvestigationNode["nodeType"], number> = {
    amplification: 2,
    counter_narrative: 4,
    current: 2,
    first_observed: 2,
    media_pickup: 2,
    official_mention: 1,
    related: 2,
    uncertain: 0,
  };
  const laneCounts = new Map<string, number>();
  const positions: Record<string, XYPosition> = {};

  for (const [index, nodeId] of data.nodes.map((node, order) => [order, node.id] as const)) {
    const node = nodeById.get(nodeId);

    if (!node) {
      continue;
    }

    const depth = depthMap.get(nodeId) ?? index;
    const lane = laneBase[node.nodeType];
    const laneKey = `${depth}-${lane}`;
    const laneOffset = laneCounts.get(laneKey) ?? 0;
    laneCounts.set(laneKey, laneOffset + 1);

    positions[nodeId] = {
      x: 60 + depth * 360,
      y: 64 + lane * 160 + laneOffset * 26,
    };
  }

  return positions;
}

export function getNodePositions(data: InvestigationFlowchartData) {
  const fallbackPositions = getFallbackPositions(data);
  const positions: Record<string, XYPosition> = {};

  for (const node of data.nodes) {
    positions[node.id] = PRESET_POSITIONS[node.id] ?? fallbackPositions[node.id];
  }

  return positions;
}

function getIncomingEdges(data: InvestigationFlowchartData) {
  const incoming = new Map<string, InvestigationEdge[]>();

  for (const edge of data.edges) {
    const next = incoming.get(edge.target) ?? [];
    next.push(edge);
    incoming.set(edge.target, next);
  }

  return incoming;
}

function getOutgoingEdges(data: InvestigationFlowchartData) {
  const outgoing = new Map<string, InvestigationEdge[]>();

  for (const edge of data.edges) {
    const next = outgoing.get(edge.source) ?? [];
    next.push(edge);
    outgoing.set(edge.source, next);
  }

  return outgoing;
}

function isCounterLike(
  edge: InvestigationEdge,
  sourceNode?: InvestigationNode,
  targetNode?: InvestigationNode,
) {
  return (
    edge.edgeType === "counter_narrative" ||
    sourceNode?.nodeType === "counter_narrative" ||
    targetNode?.nodeType === "counter_narrative"
  );
}

function isUncertainLike(
  edge: InvestigationEdge,
  sourceNode?: InvestigationNode,
  targetNode?: InvestigationNode,
) {
  return (
    edge.edgeType === "uncertain" ||
    sourceNode?.nodeType === "uncertain" ||
    targetNode?.nodeType === "uncertain"
  );
}

function getMainPathNodeIds(data: InvestigationFlowchartData) {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const incoming = getIncomingEdges(data);
  const positions = getNodePositions(data);
  const mainPathNodeIds: string[] = [data.currentNodeId];
  let cursorId = data.currentNodeId;
  const visitedNodes = new Set(mainPathNodeIds);

  while (true) {
    const candidates = (incoming.get(cursorId) ?? []).filter((edge) => {
      const sourceNode = nodeById.get(edge.source);

      return (
        !isCounterLike(edge, sourceNode) &&
        !isUncertainLike(edge, sourceNode) &&
        sourceNode?.nodeType !== "official_mention"
      );
    });

    if (candidates.length === 0) {
      break;
    }

    candidates.sort(
      (left, right) =>
        (positions[right.source]?.x ?? 0) - (positions[left.source]?.x ?? 0),
    );

    const nextEdge = candidates[0];

    if (visitedNodes.has(nextEdge.source)) {
      break;
    }

    mainPathNodeIds.push(nextEdge.source);
    visitedNodes.add(nextEdge.source);
    cursorId = nextEdge.source;
  }

  return mainPathNodeIds;
}

function buildBranchPhase(
  edges: InvestigationEdge[],
  positions: Record<string, XYPosition>,
  initialVisibleNodeIds: Set<string>,
): RevealStep[] {
  const steps: RevealStep[] = [];
  const visibleNodeIds = new Set(initialVisibleNodeIds);
  const remainingEdges = [...edges];

  while (true) {
    const candidates = remainingEdges.filter((edge) => {
      const sourceVisible = visibleNodeIds.has(edge.source);
      const targetVisible = visibleNodeIds.has(edge.target);

      return sourceVisible !== targetVisible;
    });

    if (candidates.length === 0) {
      break;
    }

    candidates.sort((left, right) => {
      const leftVisibleId = visibleNodeIds.has(left.source)
        ? left.source
        : left.target;
      const rightVisibleId = visibleNodeIds.has(right.source)
        ? right.source
        : right.target;

      return (positions[rightVisibleId]?.x ?? 0) - (positions[leftVisibleId]?.x ?? 0);
    });

    const nextEdge = candidates[0];
    const edgeIndex = remainingEdges.findIndex((edge) => edge.id === nextEdge.id);

    if (edgeIndex >= 0) {
      remainingEdges.splice(edgeIndex, 1);
    }

    const sourceVisible = visibleNodeIds.has(nextEdge.source);
    const cameraAnchorId = sourceVisible ? nextEdge.source : nextEdge.target;
    const cameraNodeId = sourceVisible ? nextEdge.target : nextEdge.source;

    steps.push({
      cameraAnchorId,
      cameraNodeId,
      direction: sourceVisible ? "forward" : "reverse",
      id: nextEdge.id,
      kind: "edge",
    });
    steps.push({
      cameraAnchorId,
      cameraNodeId,
      id: cameraNodeId,
      kind: "node",
    });
    visibleNodeIds.add(cameraNodeId);
  }

  remainingEdges.sort((left, right) => {
    const leftMax = Math.max(
      positions[left.source]?.x ?? 0,
      positions[left.target]?.x ?? 0,
    );
    const rightMax = Math.max(
      positions[right.source]?.x ?? 0,
      positions[right.target]?.x ?? 0,
    );

    return rightMax - leftMax;
  });

  for (const edge of remainingEdges) {
    const sourceX = positions[edge.source]?.x ?? 0;
    const targetX = positions[edge.target]?.x ?? 0;

    steps.push({
      cameraAnchorId: sourceX >= targetX ? edge.source : edge.target,
      cameraNodeId: sourceX >= targetX ? edge.target : edge.source,
      direction: sourceX <= targetX ? "forward" : "reverse",
      id: edge.id,
      kind: "edge",
    });
  }

  return steps;
}

export function buildRevealPlan(
  data: InvestigationFlowchartData,
): InvestigationRevealPlan {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const positions = getNodePositions(data);
  const mainPathNodeIds = getMainPathNodeIds(data);
  const mainPathNodeIdSet = new Set(mainPathNodeIds);
  const mainPathEdgeIds = new Set<string>();
  const mainSteps: RevealStep[] = [];

  for (let index = 1; index < mainPathNodeIds.length; index += 1) {
    const sourceId = mainPathNodeIds[index];
    const targetId = mainPathNodeIds[index - 1];
    const edge = data.edges.find(
      (candidate) =>
        candidate.source === sourceId && candidate.target === targetId,
    );

    if (!edge) {
      continue;
    }

    mainPathEdgeIds.add(edge.id);
    mainSteps.push({
      cameraAnchorId: targetId,
      cameraNodeId: sourceId,
      direction: "reverse",
      id: edge.id,
      kind: "edge",
    });
    mainSteps.push({
      cameraAnchorId: targetId,
      cameraNodeId: sourceId,
      id: sourceId,
      kind: "node",
    });
  }

  const supportingEdges = data.edges.filter((edge) => {
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);

    return (
      !mainPathEdgeIds.has(edge.id) &&
      !isCounterLike(edge, sourceNode, targetNode) &&
      !isUncertainLike(edge, sourceNode, targetNode)
    );
  });
  const counterEdges = data.edges.filter((edge) => {
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);

    return isCounterLike(edge, sourceNode, targetNode);
  });
  const uncertainEdges = data.edges.filter((edge) => {
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);

    return isUncertainLike(edge, sourceNode, targetNode);
  });

  const phases: RevealPhase[] = [
    {
      id: "current",
      steps: [
        {
          cameraAnchorId: data.currentNodeId,
          cameraNodeId: data.currentNodeId,
          id: data.currentNodeId,
          kind: "node",
        },
      ],
    },
    { id: "main", steps: mainSteps },
    {
      id: "supporting",
      steps: buildBranchPhase(
        supportingEdges,
        positions,
        new Set(mainPathNodeIdSet),
      ),
    },
    {
      id: "counter",
      steps: buildBranchPhase(counterEdges, positions, new Set(mainPathNodeIdSet)),
    },
    {
      id: "uncertain",
      steps: buildBranchPhase(
        uncertainEdges,
        positions,
        new Set(mainPathNodeIdSet),
      ),
    },
  ];

  return {
    phases: phases.filter((phase) => phase.steps.length > 0),
  };
}

export function resolvePathToCurrent(
  data: InvestigationFlowchartData,
  selectedNodeId: string,
): PathResult {
  if (selectedNodeId === data.currentNodeId) {
    return {
      edgeIds: new Set(),
      found: true,
      nodeIds: new Set([selectedNodeId]),
    };
  }

  const outgoing = getOutgoingEdges(data);
  const queue: string[] = [selectedNodeId];
  const visited = new Set<string>(queue);
  const previousEdge = new Map<string, InvestigationEdge>();

  while (queue.length > 0) {
    const currentId = queue.shift();

    if (!currentId) {
      continue;
    }

    for (const edge of outgoing.get(currentId) ?? []) {
      if (visited.has(edge.target)) {
        continue;
      }

      previousEdge.set(edge.target, edge);
      visited.add(edge.target);
      queue.push(edge.target);

      if (edge.target === data.currentNodeId) {
        queue.length = 0;
        break;
      }
    }
  }

  if (!previousEdge.has(data.currentNodeId)) {
    return {
      edgeIds: new Set(),
      found: false,
      nodeIds: new Set([selectedNodeId]),
    };
  }

  const edgeIds = new Set<string>();
  const nodeIds = new Set<string>([selectedNodeId, data.currentNodeId]);
  let cursorId = data.currentNodeId;

  while (cursorId !== selectedNodeId) {
    const edge = previousEdge.get(cursorId);

    if (!edge) {
      break;
    }

    edgeIds.add(edge.id);
    nodeIds.add(edge.source);
    nodeIds.add(edge.target);
    cursorId = edge.source;
  }

  return { edgeIds, found: true, nodeIds };
}

export function getConnectedNeighborhood(
  data: InvestigationFlowchartData,
  nodeId: string,
) {
  const nodeIds = new Set<string>([nodeId]);
  const edgeIds = new Set<string>();

  for (const edge of data.edges) {
    if (edge.source === nodeId || edge.target === nodeId) {
      edgeIds.add(edge.id);
      nodeIds.add(edge.source);
      nodeIds.add(edge.target);
    }
  }

  return { edgeIds, nodeIds };
}

function getBaseNodeState(node: InvestigationNode): NodeState {
  switch (node.nodeType) {
    case "current":
      return "current";
    case "counter_narrative":
      return "counter";
    case "related":
    case "official_mention":
      return "related";
    case "uncertain":
      return "uncertain";
    default:
      return "main";
  }
}

export function createFlowNodes({
  data,
  dimmedNodeIds,
  highlightedNodeIds,
  isFocusMode,
  positions,
  revealedNodeIds,
  selectedNodeId,
  showReceipts,
}: {
  data: InvestigationFlowchartData;
  dimmedNodeIds: Set<string>;
  highlightedNodeIds: Set<string>;
  isFocusMode: boolean;
  positions: Record<string, XYPosition>;
  revealedNodeIds: Set<string>;
  selectedNodeId: string | null;
  showReceipts: boolean;
}): InvestigationFlowNode[] {
  return data.nodes.map((node) => {
    let visualState = getBaseNodeState(node);
    const position = positions[node.id];

    if (isFocusMode && selectedNodeId === node.id) {
      visualState = "selected";
    } else if (dimmedNodeIds.has(node.id)) {
      visualState = "dimmed";
    }

    return {
      id: node.id,
      data: {
        isCurrent: node.id === data.currentNodeId,
        isHighlighted: highlightedNodeIds.has(node.id),
        isRevealed: revealedNodeIds.has(node.id),
        layoutSide:
          (position?.x ?? 0) + FLOW_NODE_WIDTH / 2 < TIMELINE_AXIS_X
            ? "left"
            : "right",
        node,
        showReceipts,
        visualState,
      },
      draggable: false,
      position: positions[node.id],
      selectable: false,
      type: "investigationNode",
    };
  });
}

function getEdgeVariant(edge: InvestigationEdge): InvestigationFlowEdgeData["variant"] {
  switch (edge.edgeType) {
    case "counter_narrative":
      return "counter";
    case "related_context":
      return "related";
    case "uncertain":
      return "uncertain";
    default:
      return "main";
  }
}

export function createFlowEdges({
  data,
  dimmedNodeIds,
  highlightedEdgeIds,
  isFocusMode,
  revealDirections,
  revealDurations,
  revealedEdgeIds,
}: {
  data: InvestigationFlowchartData;
  dimmedNodeIds: Set<string>;
  highlightedEdgeIds: Set<string>;
  isFocusMode: boolean;
  revealDirections: Map<string, RevealDirection>;
  revealDurations: Map<string, number>;
  revealedEdgeIds: Set<string>;
}): InvestigationFlowEdge[] {
  return data.edges.map((edge) => {
    const isDimmed =
      isFocusMode &&
      (dimmedNodeIds.has(edge.source) || dimmedNodeIds.has(edge.target)) &&
      !highlightedEdgeIds.has(edge.id);

    return {
      animated: false,
      data: {
        edge,
        isDimmed,
        isHighlighted: highlightedEdgeIds.has(edge.id),
        isRevealed: revealedEdgeIds.has(edge.id),
        revealDirection: revealDirections.get(edge.id) ?? "forward",
        revealDurationMs: revealDurations.get(edge.id) ?? 640,
        showLabel: highlightedEdgeIds.has(edge.id),
        variant: getEdgeVariant(edge),
      },
      id: edge.id,
      selectable: false,
      source: edge.source,
      target: edge.target,
      type: "investigationEdge",
      zIndex: highlightedEdgeIds.has(edge.id) ? 7 : 3,
    };
  });
}
