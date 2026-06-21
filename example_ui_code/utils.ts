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
export const FLOW_NODE_HEIGHT = 318;
export const FLOW_STAGE_PADDING_TOP = 260;
export const FLOW_STAGE_PADDING_RIGHT = 500;
export const FLOW_STAGE_PADDING_BOTTOM = 340;
export const FLOW_STAGE_PADDING_LEFT = 300;

const TRACE_START_X = 120;
const TRACE_TRUNK_Y = 470;
const TRACE_SPACING_X = 640;
const BRANCH_LANE_GAP_Y = 430;
const BRANCH_ROW_GAP_Y = 260;
const BRANCH_COLUMN_NUDGE_X = 84;
const CROSS_EDGE_GAP_Y = 82;
const CROSS_EDGE_ROW_GAP_Y = 46;
const CARD_CENTER_X = FLOW_NODE_WIDTH / 2;
const CARD_CENTER_Y = FLOW_NODE_HEIGHT / 2;

type TraceLane = "above" | "below";
type TraceEdgeKind = "trunk" | "branch" | "cross";

export type InvestigationFlowNodeData = {
  node: InvestigationNode;
  visualState: NodeState;
  isRevealed: boolean;
  isHighlighted: boolean;
  showReceipts: boolean;
  isCurrent: boolean;
};

export type TraceConnectorPoint = {
  x: number;
  y: number;
};

export type TraceConnectorPath = {
  points: TraceConnectorPoint[];
  kind: TraceEdgeKind;
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
  treePath: TraceConnectorPath;
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

type TraceLayout = {
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
  edgePaths: Map<string, TraceConnectorPath>;
  positions: Record<string, XYPosition>;
  trunkNodeIds: string[];
};

type BranchAssignment = {
  anchorId: string;
  branchOrder: number;
  lane: TraceLane;
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

export function getNodePositions(data: InvestigationFlowchartData) {
  return getTraceLayout(data).positions;
}

export function getGraphViewportBounds(data: InvestigationFlowchartData) {
  return getTraceLayout(data).bounds;
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

function getTrunkNodeIds(data: InvestigationFlowchartData) {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const incoming = getIncomingEdges(data);
  const trunkNodeIds: string[] = [data.currentNodeId];
  let cursorId = data.currentNodeId;
  const visitedNodes = new Set(trunkNodeIds);
  const typePriority: Record<InvestigationNode["nodeType"], number> = {
    media_pickup: 0,
    amplification: 1,
    first_observed: 2,
    related: 3,
    official_mention: 4,
    counter_narrative: 5,
    uncertain: 6,
    current: 7,
  };

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

    candidates.sort((left, right) => {
      const leftNode = nodeById.get(left.source);
      const rightNode = nodeById.get(right.source);
      const typeDelta =
        typePriority[leftNode?.nodeType ?? "uncertain"] -
        typePriority[rightNode?.nodeType ?? "uncertain"];
      if (typeDelta !== 0) {
        return typeDelta;
      }

      return left.source.localeCompare(right.source);
    });

    const nextEdge = candidates[0];
    if (visitedNodes.has(nextEdge.source)) {
      break;
    }

    trunkNodeIds.push(nextEdge.source);
    visitedNodes.add(nextEdge.source);
    cursorId = nextEdge.source;
  }

  return trunkNodeIds;
}

function getBranchAnchorPriority(node: InvestigationNode) {
  switch (node.nodeType) {
    case "official_mention":
      return 0;
    case "related":
      return 1;
    case "counter_narrative":
      return 2;
    case "uncertain":
      return 3;
    default:
      return 4;
  }
}

function getBranchLane(node: InvestigationNode): TraceLane {
  switch (node.nodeType) {
    case "official_mention":
    case "related":
      return "above";
    default:
      return "below";
  }
}

function getBranchAnchorId({
  incoming,
  nodeId,
  outgoing,
  trunkIndexById,
  trunkNodeIds,
  trunkNodeIdSet,
}: {
  incoming: Map<string, InvestigationEdge[]>;
  nodeId: string;
  outgoing: Map<string, InvestigationEdge[]>;
  trunkIndexById: Map<string, number>;
  trunkNodeIds: string[];
  trunkNodeIdSet: Set<string>;
}) {
  const sourceAnchors = (incoming.get(nodeId) ?? [])
    .map((edge) => edge.source)
    .filter((candidateId) => trunkNodeIdSet.has(candidateId));

  if (sourceAnchors.length > 0) {
    return sourceAnchors.sort(
      (left, right) =>
        (trunkIndexById.get(right) ?? -1) - (trunkIndexById.get(left) ?? -1),
    )[0];
  }

  const targetAnchors = (outgoing.get(nodeId) ?? [])
    .map((edge) => edge.target)
    .filter((candidateId) => trunkNodeIdSet.has(candidateId));

  if (targetAnchors.length > 0) {
    return targetAnchors.sort(
      (left, right) =>
        (trunkIndexById.get(right) ?? -1) - (trunkIndexById.get(left) ?? -1),
    )[0];
  }

  return trunkNodeIds[Math.min(1, trunkNodeIds.length - 1)] ?? trunkNodeIds[0];
}

function getBranchAssignments(data: InvestigationFlowchartData, trunkNodeIds: string[]) {
  const branchAssignments = new Map<string, BranchAssignment>();
  const branchCounts = new Map<string, number>();
  const trunkNodeIdSet = new Set(trunkNodeIds);
  const trunkIndexById = new Map(
    trunkNodeIds.map((nodeId, index) => [nodeId, index]),
  );
  const incoming = getIncomingEdges(data);
  const outgoing = getOutgoingEdges(data);

  const branchNodes = data.nodes
    .filter((node) => !trunkNodeIdSet.has(node.id))
    .sort((left, right) => {
      const leftAnchorId = getBranchAnchorId({
        incoming,
        nodeId: left.id,
        outgoing,
        trunkIndexById,
        trunkNodeIds,
        trunkNodeIdSet,
      });
      const rightAnchorId = getBranchAnchorId({
        incoming,
        nodeId: right.id,
        outgoing,
        trunkIndexById,
        trunkNodeIds,
        trunkNodeIdSet,
      });
      const anchorDelta =
        (trunkIndexById.get(leftAnchorId) ?? 999) -
        (trunkIndexById.get(rightAnchorId) ?? 999);

      if (anchorDelta !== 0) {
        return anchorDelta;
      }

      const laneDelta = getBranchLane(left).localeCompare(getBranchLane(right));

      if (laneDelta !== 0) {
        return laneDelta;
      }

      const priorityDelta =
        getBranchAnchorPriority(left) - getBranchAnchorPriority(right);

      if (priorityDelta !== 0) {
        return priorityDelta;
      }

      return left.label.localeCompare(right.label);
    });

  for (const node of branchNodes) {
    const anchorId = getBranchAnchorId({
      incoming,
      nodeId: node.id,
      outgoing,
      trunkIndexById,
      trunkNodeIds,
      trunkNodeIdSet,
    });
    const lane = getBranchLane(node);
    const branchKey = `${anchorId}:${lane}`;
    const branchOrder = branchCounts.get(branchKey) ?? 0;

    branchCounts.set(branchKey, branchOrder + 1);
    branchAssignments.set(node.id, {
      anchorId,
      branchOrder,
      lane,
    });
  }

  return branchAssignments;
}

function getNodeCenter(position: XYPosition) {
  return {
    x: position.x + CARD_CENTER_X,
    y: position.y + CARD_CENTER_Y,
  };
}

function getHorizontalConnectorPoints(
  sourcePosition: XYPosition,
  targetPosition: XYPosition,
) {
  const sourceCenter = getNodeCenter(sourcePosition);
  const targetCenter = getNodeCenter(targetPosition);
  const sourceIsLeft = sourceCenter.x < targetCenter.x;

  return [
    {
      x: sourceIsLeft ? sourcePosition.x + FLOW_NODE_WIDTH : sourcePosition.x,
      y: sourceCenter.y,
    },
    {
      x: sourceIsLeft ? targetPosition.x : targetPosition.x + FLOW_NODE_WIDTH,
      y: targetCenter.y,
    },
  ];
}

function getVerticalConnectorPoint(
  position: XYPosition,
  targetPosition: XYPosition,
) {
  const center = getNodeCenter(position);
  const targetCenter = getNodeCenter(targetPosition);

  return {
    x: center.x,
    y: targetCenter.y > center.y ? position.y + FLOW_NODE_HEIGHT : position.y,
  };
}

function getBranchConnectorPath(
  sourcePosition: XYPosition,
  targetPosition: XYPosition,
): TraceConnectorPath {
  const start = getVerticalConnectorPoint(sourcePosition, targetPosition);
  const end = getVerticalConnectorPoint(targetPosition, sourcePosition);
  const bendY = (start.y + end.y) / 2;

  return {
    kind: "branch",
    points: [
      start,
      { x: start.x, y: bendY },
      { x: end.x, y: bendY },
      end,
    ],
  };
}

function getCrossConnectorPath(
  sourcePosition: XYPosition,
  targetPosition: XYPosition,
  routeOrder: number,
): TraceConnectorPath {
  const sourceCenter = getNodeCenter(sourcePosition);
  const targetCenter = getNodeCenter(targetPosition);
  const routeY =
    Math.min(sourcePosition.y, targetPosition.y) -
    CROSS_EDGE_GAP_Y -
    routeOrder * CROSS_EDGE_ROW_GAP_Y;

  return {
    kind: "cross",
    points: [
      { x: sourceCenter.x, y: sourcePosition.y },
      { x: sourceCenter.x, y: routeY },
      { x: targetCenter.x, y: routeY },
      { x: targetCenter.x, y: targetPosition.y },
    ],
  };
}

function getTraceLayout(data: InvestigationFlowchartData): TraceLayout {
  const positions: Record<string, XYPosition> = {};
  const edgePaths = new Map<string, TraceConnectorPath>();
  const trunkNodeIds = getTrunkNodeIds(data);
  const trunkNodeIdSet = new Set(trunkNodeIds);
  const edgesByPair = new Map<string, InvestigationEdge>();
  const branchAssignments = getBranchAssignments(data, trunkNodeIds);
  const mainTrunkEdgeIds = new Set<string>();
  let crossRouteOrder = 0;

  for (const edge of data.edges) {
    edgesByPair.set(`${edge.source}=>${edge.target}`, edge);
  }

  trunkNodeIds.forEach((nodeId, index) => {
    positions[nodeId] = {
      x: TRACE_START_X + index * TRACE_SPACING_X,
      y: TRACE_TRUNK_Y,
    };
  });

  for (const [nodeId, assignment] of branchAssignments) {
    const anchorPosition = positions[assignment.anchorId];

    if (!anchorPosition) {
      continue;
    }

    const laneDirection = assignment.lane === "above" ? -1 : 1;
    const horizontalNudge = assignment.branchOrder * BRANCH_COLUMN_NUDGE_X;

    positions[nodeId] = {
      x: anchorPosition.x + horizontalNudge,
      y:
        TRACE_TRUNK_Y +
        laneDirection *
          (BRANCH_LANE_GAP_Y + assignment.branchOrder * BRANCH_ROW_GAP_Y),
    };
  }

  for (let index = 0; index < trunkNodeIds.length - 1; index += 1) {
    const currentSideId = trunkNodeIds[index];
    const earlierSideId = trunkNodeIds[index + 1];
    const edge = edgesByPair.get(`${earlierSideId}=>${currentSideId}`);

    if (!edge) {
      continue;
    }

    mainTrunkEdgeIds.add(edge.id);
  }

  for (const edge of data.edges) {
    const sourcePosition = positions[edge.source];
    const targetPosition = positions[edge.target];

    if (!sourcePosition || !targetPosition) {
      continue;
    }

    const sourceIsTrunk = trunkNodeIdSet.has(edge.source);
    const targetIsTrunk = trunkNodeIdSet.has(edge.target);

    if (mainTrunkEdgeIds.has(edge.id)) {
      edgePaths.set(edge.id, {
        kind: "trunk",
        points: getHorizontalConnectorPoints(sourcePosition, targetPosition),
      });
    } else if (sourceIsTrunk && targetIsTrunk) {
      edgePaths.set(
        edge.id,
        getCrossConnectorPath(sourcePosition, targetPosition, crossRouteOrder),
      );
      crossRouteOrder += 1;
    } else {
      edgePaths.set(edge.id, getBranchConnectorPath(sourcePosition, targetPosition));
    }
  }

  const values = Object.values(positions);
  const minX = Math.min(...values.map((position) => position.x)) - FLOW_STAGE_PADDING_LEFT;
  const minY = Math.min(...values.map((position) => position.y)) - FLOW_STAGE_PADDING_TOP;
  const maxX =
    Math.max(...values.map((position) => position.x + FLOW_NODE_WIDTH)) +
    FLOW_STAGE_PADDING_RIGHT;
  const maxY =
    Math.max(...values.map((position) => position.y + FLOW_NODE_HEIGHT)) +
    FLOW_STAGE_PADDING_BOTTOM;

  return {
    bounds: {
      maxX,
      maxY,
      minX,
      minY,
    },
    edgePaths,
    positions,
    trunkNodeIds,
  };
}

function getTraceRevealDirection(
  edge: InvestigationEdge,
  trunkIndexById: Map<string, number>,
): RevealDirection {
  const sourceIndex = trunkIndexById.get(edge.source);
  const targetIndex = trunkIndexById.get(edge.target);

  if (sourceIndex !== undefined && targetIndex !== undefined) {
    return sourceIndex > targetIndex ? "reverse" : "forward";
  }

  if (sourceIndex === undefined && targetIndex !== undefined) {
    return "reverse";
  }

  return "forward";
}

function buildBranchPhase(
  edges: InvestigationEdge[],
  visibleNodeIds: Set<string>,
  branchAssignments: Map<string, BranchAssignment>,
  trunkIndexById: Map<string, number>,
): RevealStep[] {
  const remainingEdges = [...edges];
  const steps: RevealStep[] = [];
  const visible = new Set(visibleNodeIds);

  while (true) {
    const nextEdge = remainingEdges.find((edge) => {
      const sourceVisible = visible.has(edge.source);
      const targetVisible = visible.has(edge.target);

      return sourceVisible !== targetVisible;
    });

    if (!nextEdge) {
      break;
    }

    const edgeIndex = remainingEdges.findIndex((edge) => edge.id === nextEdge.id);
    if (edgeIndex >= 0) {
      remainingEdges.splice(edgeIndex, 1);
    }

    const sourceVisible = visible.has(nextEdge.source);
    const cameraAnchorId = sourceVisible ? nextEdge.source : nextEdge.target;
    const cameraNodeId = sourceVisible ? nextEdge.target : nextEdge.source;
    const assignment = branchAssignments.get(cameraNodeId);

    steps.push({
      cameraAnchorId: assignment?.anchorId ?? cameraAnchorId,
      cameraNodeId,
      direction: sourceVisible ? "forward" : "reverse",
      id: nextEdge.id,
      kind: "edge",
    });
    steps.push({
      cameraAnchorId: assignment?.anchorId ?? cameraAnchorId,
      cameraNodeId,
      id: cameraNodeId,
      kind: "node",
    });

    visible.add(cameraNodeId);
  }

  for (const edge of remainingEdges) {
    if (!visible.has(edge.source) || !visible.has(edge.target)) {
      continue;
    }

    steps.push({
      cameraAnchorId: edge.target,
      cameraNodeId: edge.source,
      direction: getTraceRevealDirection(edge, trunkIndexById),
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
  const trunkNodeIds = getTrunkNodeIds(data);
  const trunkNodeIdSet = new Set(trunkNodeIds);
  const trunkIndexById = new Map(
    trunkNodeIds.map((nodeId, index) => [nodeId, index]),
  );
  const trunkEdgeIds = new Set<string>();
  const mainSteps: RevealStep[] = [];
  const branchAssignments = getBranchAssignments(data, trunkNodeIds);

  for (let index = 0; index < trunkNodeIds.length - 1; index += 1) {
    const parentId = trunkNodeIds[index];
    const childId = trunkNodeIds[index + 1];
    const edge = data.edges.find(
      (candidate) => candidate.source === childId && candidate.target === parentId,
    );

    if (!edge) {
      continue;
    }

    trunkEdgeIds.add(edge.id);
    mainSteps.push({
      cameraAnchorId: parentId,
      cameraNodeId: childId,
      direction: "reverse",
      id: edge.id,
      kind: "edge",
    });
    mainSteps.push({
      cameraAnchorId: parentId,
      cameraNodeId: childId,
      id: childId,
      kind: "node",
    });
  }

  const supportingEdges = data.edges.filter((edge) => {
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);

    return (
      !trunkEdgeIds.has(edge.id) &&
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
        trunkNodeIdSet,
        branchAssignments,
        trunkIndexById,
      ),
    },
    {
      id: "counter",
      steps: buildBranchPhase(
        counterEdges,
        trunkNodeIdSet,
        branchAssignments,
        trunkIndexById,
      ),
    },
    {
      id: "uncertain",
      steps: buildBranchPhase(
        uncertainEdges,
        trunkNodeIdSet,
        branchAssignments,
        trunkIndexById,
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
    const position = positions[node.id] ?? { x: 0, y: 0 };

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
        node,
        showReceipts,
        visualState,
      },
      draggable: false,
      position,
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

function getTracebackEdgeLabel(
  edge: InvestigationEdge,
  sourceNode?: InvestigationNode,
  targetNode?: InvestigationNode,
) {
  if (isUncertainLike(edge, sourceNode, targetNode)) {
    return "Weak earlier mention";
  }

  if (isCounterLike(edge, sourceNode, targetNode)) {
    return "Counter-frame response";
  }

  if (
    edge.edgeType === "related_context" ||
    sourceNode?.nodeType === "official_mention" ||
    targetNode?.nodeType === "official_mention"
  ) {
    return "Related official context";
  }

  switch (edge.edgeType) {
    case "exact_phrase_reuse":
      return "Phrase reused from";
    case "semantic_similarity":
      return "Similar earlier frame";
    case "source_link":
      return "Cites earlier source";
    case "temporal_sequence":
      return targetNode?.nodeType === "current" ? "Traced to" : "Earlier source";
    default:
      return "Traced to";
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
  const layout = getTraceLayout(data);
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));

  return data.edges
    .filter((edge) => layout.edgePaths.has(edge.id))
    .map((edge) => {
      const sourceNode = nodeById.get(edge.source);
      const targetNode = nodeById.get(edge.target);
      const isDimmed =
        isFocusMode &&
        (dimmedNodeIds.has(edge.source) || dimmedNodeIds.has(edge.target)) &&
        !highlightedEdgeIds.has(edge.id);

      return {
        animated: false,
        data: {
          edge: {
            ...edge,
            label: getTracebackEdgeLabel(edge, sourceNode, targetNode),
          },
          isDimmed,
          isHighlighted: highlightedEdgeIds.has(edge.id),
          isRevealed: revealedEdgeIds.has(edge.id),
          revealDirection: revealDirections.get(edge.id) ?? "forward",
          revealDurationMs: revealDurations.get(edge.id) ?? 640,
          showLabel: highlightedEdgeIds.has(edge.id),
          treePath: layout.edgePaths.get(edge.id)!,
          variant: getEdgeVariant(edge),
        },
        id: edge.id,
        selectable: false,
        source: edge.source,
        sourceHandle: "bottom",
        target: edge.target,
        targetHandle: "top",
        type: "investigationEdge",
        zIndex: highlightedEdgeIds.has(edge.id) ? 7 : 3,
      };
    });
}
