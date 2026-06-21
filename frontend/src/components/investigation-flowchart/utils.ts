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
export const TIMELINE_AXIS_X = 1180;
export const FLOW_STAGE_PADDING_TOP = 180;
export const FLOW_STAGE_PADDING_RIGHT = 420;
export const FLOW_STAGE_PADDING_BOTTOM = 260;
export const FLOW_STAGE_PADDING_LEFT = 420;

const TREE_TOP_Y = 72;
const TREE_CENTER_X = 970;
const TRUNK_SPACING_Y = 420;
const BRANCH_COLUMN_GAP = 760;
const BRANCH_ROW_GAP = 320;
const BRANCH_STEM_LENGTH = 96;
const CARD_SAFE_GUTTER = 96;
const BRANCH_JOIN_OFFSET_X = 110;
const CARD_CENTER_X = FLOW_NODE_WIDTH / 2;
const CARD_TOP_Y = 0;
const CARD_BOTTOM_Y = FLOW_NODE_HEIGHT;

type TreeSide = "left" | "right";
type TreeEdgeKind = "trunk" | "branch";

export type InvestigationFlowNodeData = {
  node: InvestigationNode;
  visualState: NodeState;
  isRevealed: boolean;
  isHighlighted: boolean;
  showReceipts: boolean;
  isCurrent: boolean;
  layoutSide: "left" | "right";
};

export type TreeConnectorPoint = {
  x: number;
  y: number;
};

export type TreeConnectorPath = {
  points: TreeConnectorPoint[];
  kind: TreeEdgeKind;
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
  treePath: TreeConnectorPath;
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

type TreeLayout = {
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
  edgePaths: Map<string, TreeConnectorPath>;
  positions: Record<string, XYPosition>;
  trunkNodeIds: string[];
};

type BranchAssignment = {
  anchorId: string;
  branchOrder: number;
  side: TreeSide;
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
  return getTreeLayout(data).positions;
}

export function getGraphViewportBounds(data: InvestigationFlowchartData) {
  return getTreeLayout(data).bounds;
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

function getBranchSide(node: InvestigationNode): TreeSide {
  switch (node.nodeType) {
    case "official_mention":
    case "uncertain":
      return "left";
    default:
      return "right";
  }
}

function getTreeLayout(data: InvestigationFlowchartData): TreeLayout {
  const positions: Record<string, XYPosition> = {};
  const edgePaths = new Map<string, TreeConnectorPath>();
  const trunkNodeIds = getTrunkNodeIds(data);
  const trunkNodeIdSet = new Set(trunkNodeIds);
  const trunkIndexById = new Map(trunkNodeIds.map((nodeId, index) => [nodeId, index]));
  const incoming = getIncomingEdges(data);
  const outgoing = getOutgoingEdges(data);
  const edgesByPair = new Map<string, InvestigationEdge>();
  const branchAssignments = new Map<string, BranchAssignment>();
  const branchCounts = new Map<string, number>();

  for (const edge of data.edges) {
    edgesByPair.set(`${edge.source}=>${edge.target}`, edge);
  }

  trunkNodeIds.forEach((nodeId, index) => {
    positions[nodeId] = {
      x: TREE_CENTER_X,
      y: TREE_TOP_Y + index * TRUNK_SPACING_Y,
    };
  });

  const branchNodes = data.nodes
    .filter((node) => !trunkNodeIdSet.has(node.id))
    .sort((left, right) => {
      const leftCandidates = [
        ...(outgoing.get(left.id) ?? []).map((edge) => edge.target),
        ...(incoming.get(left.id) ?? []).map((edge) => edge.source),
      ];
      const rightCandidates = [
        ...(outgoing.get(right.id) ?? []).map((edge) => edge.target),
        ...(incoming.get(right.id) ?? []).map((edge) => edge.source),
      ];
      const leftAnchorIndex = Math.min(
        ...leftCandidates
          .map((nodeId) => trunkIndexById.get(nodeId))
          .filter((value): value is number => value !== undefined),
        Number.POSITIVE_INFINITY,
      );
      const rightAnchorIndex = Math.min(
        ...rightCandidates
          .map((nodeId) => trunkIndexById.get(nodeId))
          .filter((value): value is number => value !== undefined),
        Number.POSITIVE_INFINITY,
      );
      if (leftAnchorIndex !== rightAnchorIndex) {
        return leftAnchorIndex - rightAnchorIndex;
      }

      const priorityDelta = getBranchAnchorPriority(left) - getBranchAnchorPriority(right);
      if (priorityDelta !== 0) {
        return priorityDelta;
      }

      return left.label.localeCompare(right.label);
    });

  for (const node of branchNodes) {
    const connectedTrunkIds = [
      ...(outgoing.get(node.id) ?? []).map((edge) => edge.target),
      ...(incoming.get(node.id) ?? []).map((edge) => edge.source),
    ]
      .filter((nodeId) => trunkNodeIdSet.has(nodeId))
      .sort((left, right) => (trunkIndexById.get(left) ?? 999) - (trunkIndexById.get(right) ?? 999));
    const anchorId = connectedTrunkIds[0] ?? trunkNodeIds[Math.min(1, trunkNodeIds.length - 1)];
    const side = getBranchSide(node);
    const branchKey = `${anchorId}:${side}`;
    const branchOrder = branchCounts.get(branchKey) ?? 0;
    branchCounts.set(branchKey, branchOrder + 1);
    branchAssignments.set(node.id, {
      anchorId,
      branchOrder,
      side,
    });

    const anchorPosition = positions[anchorId];
    const direction = side === "left" ? -1 : 1;
    positions[node.id] = {
      x: TREE_CENTER_X + direction * BRANCH_COLUMN_GAP,
      y: anchorPosition.y + 110 + branchOrder * BRANCH_ROW_GAP,
    };
  }

  for (let index = 0; index < trunkNodeIds.length - 1; index += 1) {
    const sourceId = trunkNodeIds[index];
    const targetId = trunkNodeIds[index + 1];
    const edge = edgesByPair.get(`${targetId}=>${sourceId}`);

    if (!edge) {
      continue;
    }

    const sourcePosition = positions[sourceId];
    const targetPosition = positions[targetId];
    const trunkX = sourcePosition.x + CARD_CENTER_X;
    const startY = sourcePosition.y + CARD_BOTTOM_Y;
    const endY = targetPosition.y + CARD_TOP_Y;

    edgePaths.set(edge.id, {
      kind: "trunk",
      points: [
        { x: trunkX, y: startY },
        { x: trunkX, y: endY },
      ],
    });
  }

  for (const node of branchNodes) {
    const assignment = branchAssignments.get(node.id);

    if (!assignment) {
      continue;
    }

    const anchorPosition = positions[assignment.anchorId];
    const branchPosition = positions[node.id];
    const direction = assignment.side === "left" ? -1 : 1;
    const branchLaneX =
      anchorPosition.x +
      CARD_CENTER_X +
      direction * (CARD_CENTER_X + CARD_SAFE_GUTTER + assignment.branchOrder * 38);
    const startY = anchorPosition.y + CARD_BOTTOM_Y;
    const splitY = startY + BRANCH_STEM_LENGTH;
    const endX =
      branchPosition.x +
      (assignment.side === "left" ? FLOW_NODE_WIDTH - BRANCH_JOIN_OFFSET_X : BRANCH_JOIN_OFFSET_X);
    const endY = branchPosition.y + CARD_TOP_Y + 74;

    const possibleEdges = [
      ...(outgoing.get(node.id) ?? []).filter((edge) => trunkNodeIdSet.has(edge.target)),
      ...(incoming.get(node.id) ?? []).filter((edge) => trunkNodeIdSet.has(edge.source)),
    ];
    const edge = possibleEdges[0];

    if (!edge) {
      continue;
    }

    edgePaths.set(edge.id, {
      kind: "branch",
      points: [
        { x: anchorPosition.x + CARD_CENTER_X, y: startY },
        { x: branchLaneX, y: splitY },
        { x: endX, y: endY },
      ],
    });
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

function buildBranchPhase(
  edges: InvestigationEdge[],
  visibleNodeIds: Set<string>,
  branchAssignments: Map<string, BranchAssignment>,
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

  return steps;
}

export function buildRevealPlan(
  data: InvestigationFlowchartData,
): InvestigationRevealPlan {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const trunkNodeIds = getTrunkNodeIds(data);
  const trunkNodeIdSet = new Set(trunkNodeIds);
  const incoming = getIncomingEdges(data);
  const outgoing = getOutgoingEdges(data);
  const trunkEdgeIds = new Set<string>();
  const mainSteps: RevealStep[] = [];
  const branchAssignments = new Map<string, BranchAssignment>();

  for (const node of data.nodes) {
    if (trunkNodeIdSet.has(node.id)) {
      continue;
    }

    const connectedTrunkIds = [
      ...(outgoing.get(node.id) ?? []).map((edge) => edge.target),
      ...(incoming.get(node.id) ?? []).map((edge) => edge.source),
    ].filter((nodeId) => trunkNodeIdSet.has(nodeId));

    if (connectedTrunkIds[0]) {
      branchAssignments.set(node.id, {
        anchorId: connectedTrunkIds[0],
        branchOrder: 0,
        side: getBranchSide(node),
      });
    }
  }

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
      ),
    },
    {
      id: "counter",
      steps: buildBranchPhase(counterEdges, trunkNodeIdSet, branchAssignments),
    },
    {
      id: "uncertain",
      steps: buildBranchPhase(uncertainEdges, trunkNodeIdSet, branchAssignments),
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
          (position?.x ?? 0) + FLOW_NODE_WIDTH / 2 < TIMELINE_AXIS_X ? "left" : "right",
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
  const layout = getTreeLayout(data);

  return data.edges
    .filter((edge) => layout.edgePaths.has(edge.id))
    .map((edge) => {
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
