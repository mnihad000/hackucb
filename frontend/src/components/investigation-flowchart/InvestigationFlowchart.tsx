import "@xyflow/react/dist/style.css";

import {
  ReactFlow,
  type NodeMouseHandler,
  type ReactFlowInstance,
} from "@xyflow/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { InvestigationFlowchartData } from "../../types/rhetoriq";
import AnimatedInvestigationEdge from "./AnimatedInvestigationEdge";
import FlowchartControls from "./FlowchartControls";
import InvestigationNodeCard from "./InvestigationNodeCard";
import {
  buildRevealPlan,
  createFlowEdges,
  createFlowNodes,
  filterFlowchartData,
  FLOW_NODE_HEIGHT,
  FLOW_NODE_WIDTH,
  getConnectedNeighborhood,
  getNodePositions,
  resolvePathToCurrent,
  type InvestigationFlowEdge,
  type InvestigationFlowNode,
} from "./utils";

const edgeTypes = {
  investigationEdge: AnimatedInvestigationEdge,
};

const nodeTypes = {
  investigationNode: InvestigationNodeCard,
};

const CURRENT_NODE_MS = 280;
const EDGE_MAIN_MS = 640;
const EDGE_BRANCH_MS = 420;
const EDGE_CONNECTOR_MS = 300;
const NODE_MAIN_MS = 280;
const NODE_BRANCH_MS = 230;
const PAUSE_MAIN_MS = 125;
const PAUSE_BRANCH_MS = 90;
const FINAL_FRAME_MS = 880;

type InvestigationFlowchartProps = {
  data: InvestigationFlowchartData;
};

export default function InvestigationFlowchart({
  data,
}: InvestigationFlowchartProps) {
  const animationController = useRef<{
    runId: number;
    timeoutIds: Set<number>;
  }>({
    runId: 0,
    timeoutIds: new Set<number>(),
  });
  const [animationNonce, setAnimationNonce] = useState(0);
  const [focusMode, setFocusMode] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isIntroRunning, setIsIntroRunning] = useState(false);
  const [revealedEdgeIds, setRevealedEdgeIds] = useState<string[]>([]);
  const [revealedNodeIds, setRevealedNodeIds] = useState<string[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    data.currentNodeId,
  );
  const [showCounterNarratives, setShowCounterNarratives] = useState(true);
  const [showReceipts, setShowReceipts] = useState(false);
  const flowRef = useRef<ReactFlowInstance<
    InvestigationFlowNode,
    InvestigationFlowEdge
  > | null>(null);

  const visibleData = useMemo(
    () => filterFlowchartData(data, showCounterNarratives),
    [data, showCounterNarratives],
  );
  const positions = useMemo(() => getNodePositions(visibleData), [visibleData]);
  const revealPlan = useMemo(() => buildRevealPlan(visibleData), [visibleData]);
  const revealDirections = useMemo(() => {
    const next = new Map<string, "forward" | "reverse">();

    for (const phase of revealPlan.phases) {
      for (const step of phase.steps) {
        if (step.kind === "edge") {
          next.set(step.id, step.direction);
        }
      }
    }

    return next;
  }, [revealPlan]);
  const revealDurations = useMemo(() => {
    const next = new Map<string, number>();

    for (const phase of revealPlan.phases) {
      phase.steps.forEach((step, index) => {
        if (step.kind !== "edge") {
          return;
        }

        const followingStep = phase.steps[index + 1];
        const hasNodeImmediatelyAfter =
          followingStep?.kind === "node" && followingStep.id === step.cameraNodeId;
        const duration =
          phase.id === "main"
            ? EDGE_MAIN_MS
            : hasNodeImmediatelyAfter
              ? EDGE_BRANCH_MS
              : EDGE_CONNECTOR_MS;

        next.set(step.id, duration);
      });
    }

    return next;
  }, [revealPlan]);

  useEffect(() => {
    if (!visibleData.nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(visibleData.currentNodeId);
      setFocusMode(false);
    }
  }, [selectedNodeId, visibleData]);

  const focusNode = useCallback(
    (nodeId: string, zoom = 1.12, duration = 750) => {
      const position = positions[nodeId];

      if (!position || !flowRef.current) {
        return;
      }

      void flowRef.current.setCenter(
        position.x + FLOW_NODE_WIDTH / 2,
        position.y + FLOW_NODE_HEIGHT / 2,
        { duration, zoom },
      );
    },
    [positions],
  );

  const framePair = useCallback(
    (anchorNodeId: string, nodeId: string, duration = 720) => {
      const anchor = positions[anchorNodeId];
      const node = positions[nodeId];

      if (!anchor || !node || !flowRef.current) {
        return;
      }

      const anchorCenterX = anchor.x + FLOW_NODE_WIDTH / 2;
      const anchorCenterY = anchor.y + FLOW_NODE_HEIGHT / 2;
      const nodeCenterX = node.x + FLOW_NODE_WIDTH / 2;
      const nodeCenterY = node.y + FLOW_NODE_HEIGHT / 2;
      const centerX = (anchorCenterX + nodeCenterX) / 2;
      const centerY = (anchorCenterY + nodeCenterY) / 2;
      const spanX = Math.abs(anchorCenterX - nodeCenterX);
      const spanY = Math.abs(anchorCenterY - nodeCenterY);
      const zoom = Math.max(
        0.82,
        Math.min(1.16, 1.18 - spanX / 2300 - spanY / 1800),
      );

      void flowRef.current.setCenter(centerX, centerY, { duration, zoom });
    },
    [positions],
  );

  const clearScheduledAnimation = useCallback(() => {
    for (const timeoutId of animationController.current.timeoutIds) {
      window.clearTimeout(timeoutId);
    }

    animationController.current.timeoutIds.clear();
  }, []);

  const revealAllVisibleGraph = useCallback(() => {
    setRevealedNodeIds(visibleData.nodes.map((node) => node.id));
    setRevealedEdgeIds(visibleData.edges.map((edge) => edge.id));
  }, [visibleData.edges, visibleData.nodes]);

  const stopIntro = useCallback(
    ({ revealAll = false }: { revealAll?: boolean } = {}) => {
      animationController.current.runId += 1;
      clearScheduledAnimation();
      setIsIntroRunning(false);

      if (revealAll) {
        revealAllVisibleGraph();
      }
    },
    [clearScheduledAnimation, revealAllVisibleGraph],
  );

  const waitFor = useCallback(
    (ms: number, runId: number) =>
      new Promise<boolean>((resolve) => {
        if (animationController.current.runId !== runId) {
          resolve(false);
          return;
        }

        const timeoutId = window.setTimeout(() => {
          animationController.current.timeoutIds.delete(timeoutId);
          resolve(animationController.current.runId === runId);
        }, ms);

        animationController.current.timeoutIds.add(timeoutId);
      }),
    [],
  );

  const startReveal = useCallback(() => {
    stopIntro();
    const runId = animationController.current.runId;
    setIsIntroRunning(true);
    setRevealedEdgeIds([]);
    setRevealedNodeIds([]);

    const revealNode = (nodeId: string) => {
      setRevealedNodeIds((current) =>
        current.includes(nodeId) ? current : [...current, nodeId],
      );
    };

    const revealEdge = (edgeId: string) => {
      setRevealedEdgeIds((current) =>
        current.includes(edgeId) ? current : [...current, edgeId],
      );
    };

    void (async () => {
      for (const phase of revealPlan.phases) {
        for (let index = 0; index < phase.steps.length; index += 1) {
          if (animationController.current.runId !== runId) {
            return;
          }

          const step = phase.steps[index];
          const nextStep = phase.steps[index + 1];

          if (step.kind === "node") {
            if (phase.id === "current") {
              focusNode(step.id, 1.18, 720);
            } else {
              framePair(step.cameraAnchorId, step.cameraNodeId, 700);
            }

            revealNode(step.id);

            const settled = await waitFor(
              phase.id === "current" ? CURRENT_NODE_MS : phase.id === "main" ? NODE_MAIN_MS : NODE_BRANCH_MS,
              runId,
            );

            if (!settled) {
              return;
            }

            const paused = await waitFor(
              phase.id === "main" ? PAUSE_MAIN_MS : PAUSE_BRANCH_MS,
              runId,
            );

            if (!paused) {
              return;
            }

            continue;
          }

          framePair(step.cameraAnchorId, step.cameraNodeId, 760);
          revealEdge(step.id);

          const hasNodeImmediatelyAfter =
            nextStep?.kind === "node" && nextStep.id === step.cameraNodeId;
          const edgeDuration =
            phase.id === "main"
              ? EDGE_MAIN_MS
              : hasNodeImmediatelyAfter
                ? EDGE_BRANCH_MS
                : EDGE_CONNECTOR_MS;
          const completed = await waitFor(edgeDuration, runId);

          if (!completed) {
            return;
          }
        }
      }

      if (animationController.current.runId !== runId) {
        return;
      }

      await waitFor(120, runId);

      if (animationController.current.runId !== runId) {
        return;
      }

      void flowRef.current?.fitView({
        duration: FINAL_FRAME_MS,
        maxZoom: 1.03,
        minZoom: 0.56,
        padding: 0.18,
      });

      const finished = await waitFor(FINAL_FRAME_MS, runId);

      if (!finished) {
        return;
      }

      setIsIntroRunning(false);
    })();
  }, [focusNode, framePair, revealPlan.phases, stopIntro, waitFor]);

  useEffect(() => {
    startReveal();

    return () => {
      animationController.current.runId += 1;
      clearScheduledAnimation();
    };
  }, [animationNonce, clearScheduledAnimation, startReveal]);

  const highlightedPath = useMemo(() => {
    if (!focusMode || !selectedNodeId) {
      return { edgeIds: new Set<string>(), nodeIds: new Set<string>() };
    }

    const resolved = resolvePathToCurrent(visibleData, selectedNodeId);

    if (resolved.found) {
      return resolved;
    }

    return getConnectedNeighborhood(visibleData, selectedNodeId);
  }, [focusMode, selectedNodeId, visibleData]);

  const hoverNeighborhood = useMemo(() => {
    if (!hoveredNodeId || focusMode) {
      return { edgeIds: new Set<string>(), nodeIds: new Set<string>() };
    }

    return getConnectedNeighborhood(visibleData, hoveredNodeId);
  }, [focusMode, hoveredNodeId, visibleData]);

  const highlightedNodeIds = useMemo(() => {
    const next = new Set<string>();

    for (const nodeId of highlightedPath.nodeIds) {
      next.add(nodeId);
    }

    for (const nodeId of hoverNeighborhood.nodeIds) {
      next.add(nodeId);
    }

    return next;
  }, [highlightedPath.nodeIds, hoverNeighborhood.nodeIds]);

  const highlightedEdgeIds = useMemo(() => {
    const next = new Set<string>();

    for (const edgeId of highlightedPath.edgeIds) {
      next.add(edgeId);
    }

    for (const edgeId of hoverNeighborhood.edgeIds) {
      next.add(edgeId);
    }

    return next;
  }, [highlightedPath.edgeIds, hoverNeighborhood.edgeIds]);

  const dimmedNodeIds = useMemo(() => {
    if (!focusMode || highlightedPath.nodeIds.size === 0) {
      return new Set<string>();
    }

    return new Set(
      visibleData.nodes
        .map((node) => node.id)
        .filter((nodeId) => !highlightedPath.nodeIds.has(nodeId)),
    );
  }, [focusMode, highlightedPath.nodeIds, visibleData.nodes]);

  const revealedNodeIdSet = useMemo(
    () => new Set(revealedNodeIds),
    [revealedNodeIds],
  );
  const revealedEdgeIdSet = useMemo(
    () => new Set(revealedEdgeIds),
    [revealedEdgeIds],
  );

  const nodes = useMemo(
    () =>
      createFlowNodes({
        data: visibleData,
        dimmedNodeIds,
        highlightedNodeIds,
        isFocusMode: focusMode,
        positions,
        revealedNodeIds: revealedNodeIdSet,
        selectedNodeId,
        showReceipts,
      }),
    [
      dimmedNodeIds,
      focusMode,
      highlightedNodeIds,
      positions,
      revealedNodeIdSet,
      selectedNodeId,
      showReceipts,
      visibleData,
    ],
  );

  const edges = useMemo(
    () =>
      createFlowEdges({
        data: visibleData,
        dimmedNodeIds,
        highlightedEdgeIds,
        isFocusMode: focusMode,
        revealDirections,
        revealDurations,
        revealedEdgeIds: revealedEdgeIdSet,
      }),
    [
      dimmedNodeIds,
      focusMode,
      highlightedEdgeIds,
      revealDirections,
      revealDurations,
      revealedEdgeIdSet,
      visibleData,
    ],
  );

  const handleNodeClick: NodeMouseHandler<InvestigationFlowNode> = useCallback(
    (_event, node) => {
      if (isIntroRunning) {
        stopIntro({ revealAll: true });
      }

      setSelectedNodeId(node.id);
      setFocusMode(true);
      focusNode(node.id, node.id === visibleData.currentNodeId ? 1.08 : 1.16, 720);
    },
    [focusNode, isIntroRunning, stopIntro, visibleData.currentNodeId],
  );

  const handleResetView = useCallback(() => {
    stopIntro({ revealAll: true });
    setFocusMode(false);
    setHoveredNodeId(null);
    setSelectedNodeId(visibleData.currentNodeId);
    void flowRef.current?.fitView({
      duration: 650,
      maxZoom: 1.03,
      minZoom: 0.56,
      padding: 0.18,
    });
  }, [stopIntro, visibleData.currentNodeId]);

  const handleReplay = useCallback(() => {
    stopIntro();
    setFocusMode(false);
    setHoveredNodeId(null);
    setSelectedNodeId(visibleData.currentNodeId);
    setAnimationNonce((current) => current + 1);
  }, [stopIntro, visibleData.currentNodeId]);

  const handleFitView = useCallback(() => {
    stopIntro({ revealAll: true });
    void flowRef.current?.fitView({
      duration: 680,
      maxZoom: 1.03,
      minZoom: 0.56,
      padding: 0.18,
    });
  }, [stopIntro]);

  const handleCounterNarrativeToggle = useCallback(() => {
    stopIntro();
    setShowCounterNarratives((current) => !current);
    setFocusMode(false);
    setHoveredNodeId(null);
    setSelectedNodeId(data.currentNodeId);
    setAnimationNonce((current) => current + 1);
  }, [data.currentNodeId, stopIntro]);

  return (
    <section>
      <div className="space-y-4">
        <div className="flowchart-canvas relative overflow-hidden rounded-[1.3rem] border border-[rgba(12,12,12,0.12)] bg-[rgba(255,255,252,0.96)] shadow-[0_32px_66px_-44px_rgba(0,0,0,0.18)] backdrop-blur-xl">
          <TerrainBackdrop />

          <div className="relative h-[960px] sm:h-[1240px]">
            <ReactFlow<InvestigationFlowNode, InvestigationFlowEdge>
              aria-label="Narrative path map"
              className="!bg-transparent"
              defaultEdgeOptions={{ selectable: false }}
              edges={edges}
              edgeTypes={edgeTypes}
              elementsSelectable={false}
              maxZoom={1.45}
              minZoom={0.5}
              nodeTypes={nodeTypes}
              nodes={nodes}
              nodesConnectable={false}
              nodesDraggable={false}
              onInit={(instance) => {
                flowRef.current = instance;
              }}
              onNodeClick={handleNodeClick}
              onNodeMouseEnter={(_event, node) => setHoveredNodeId(node.id)}
              onNodeMouseLeave={() => setHoveredNodeId(null)}
              onMoveStart={(event) => {
                if (event && isIntroRunning) {
                  stopIntro({ revealAll: true });
                }
              }}
              onPaneClick={() => {
                if (isIntroRunning) {
                  stopIntro({ revealAll: true });
                }

                setHoveredNodeId(null);
              }}
              onPaneScroll={() => {
                if (isIntroRunning) {
                  stopIntro({ revealAll: true });
                }
              }}
              panOnDrag
              panOnScroll
              proOptions={{ hideAttribution: true }}
              zoomOnDoubleClick={false}
            />
          </div>
        </div>

        <p className="rounded-[0.95rem] border border-[rgba(12,12,12,0.12)] bg-[rgba(255,255,252,0.9)] px-5 py-4 text-sm leading-7 text-[rgba(14,14,14,0.64)] shadow-[0_18px_34px_-28px_rgba(0,0,0,0.16)]">
          This map shows first observed sources and spread patterns in the available
          dataset. It does not prove true origin or coordination.
        </p>

        <div className="flex justify-end">
          <div className="max-w-[22rem]">
            <FlowchartControls
              onFitView={handleFitView}
              onReplay={handleReplay}
              onResetView={handleResetView}
              onToggleCounterNarratives={handleCounterNarrativeToggle}
              onToggleReceipts={() => {
                if (isIntroRunning) {
                  stopIntro({ revealAll: true });
                }

                setShowReceipts((current) => !current);
              }}
              showCounterNarratives={showCounterNarratives}
              showReceipts={showReceipts}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function TerrainBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.18]"
        fill="none"
        preserveAspectRatio="none"
        viewBox="0 0 1280 1800"
        xmlns="http://www.w3.org/2000/svg"
      >
        {Array.from({ length: 24 }, (_, index) => {
          const startY = index * 72 - 180;
          const controlA = startY + 34 - (index % 4) * 18;
          const controlB = startY - 72 + (index % 5) * 20;
          const controlC = startY + 118 - (index % 3) * 26;
          const controlD = startY - 42 + (index % 6) * 14;
          const endY = startY + 28 - (index % 2) * 22;
          const d = [
            `M -120 ${startY}`,
            `C 90 ${controlA}, 240 ${startY + 98}, 430 ${controlB}`,
            `S 770 ${controlC}, 980 ${controlD}`,
            `S 1280 ${startY + 72}, 1440 ${endY}`,
          ].join(" ");

          return (
            <path
              key={index}
              d={d}
              stroke="rgba(17,17,17,0.34)"
              strokeWidth="1.2"
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,252,0.28),rgba(255,255,252,0.72))]" />
    </div>
  );
}
