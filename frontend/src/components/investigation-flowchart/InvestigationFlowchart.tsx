import "@xyflow/react/dist/style.css";

import {
  ReactFlow,
  type NodeMouseHandler,
  type ReactFlowInstance,
} from "@xyflow/react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { InvestigationFlowchartData } from "../../types/rhetoriq";
import AnimatedInvestigationEdge from "./AnimatedInvestigationEdge";
import InvestigationNodeCard from "./InvestigationNodeCard";
import {
  buildRevealPlan,
  createFlowEdges,
  createFlowNodes,
  FLOW_NODE_HEIGHT,
  FLOW_NODE_WIDTH,
  getGraphViewportBounds,
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

const CURRENT_NODE_MS = 820;
const EDGE_MAIN_MS = 1380;
const EDGE_BRANCH_MS = 1040;
const EDGE_CONNECTOR_MS = 760;
const NODE_MAIN_MS = 780;
const NODE_BRANCH_MS = 660;
const PAUSE_MAIN_MS = 340;
const PAUSE_BRANCH_MS = 240;
const FINAL_FRAME_MS = 1120;

type InvestigationFlowchartProps = {
  data?: InvestigationFlowchartData;
  isLoading?: boolean;
};

export default function InvestigationFlowchart({
  data,
  isLoading = false,
}: InvestigationFlowchartProps) {
  const animationController = useRef<{
    runId: number;
    timeoutIds: Set<number>;
  }>({
    runId: 0,
    timeoutIds: new Set<number>(),
  });
  const [focusMode, setFocusMode] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isIntroRunning, setIsIntroRunning] = useState(false);
  const [revealedEdgeIds, setRevealedEdgeIds] = useState<string[]>([]);
  const [revealedNodeIds, setRevealedNodeIds] = useState<string[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    data?.currentNodeId ?? null,
  );
  const flowRef = useRef<ReactFlowInstance<
    InvestigationFlowNode,
    InvestigationFlowEdge
  > | null>(null);

  const visibleData = data ?? null;
  const hasGraphData = Boolean(visibleData && visibleData.nodes.length > 0);
  const positions = useMemo(
    () => (visibleData ? getNodePositions(visibleData) : {}),
    [visibleData],
  );
  const viewportBounds = useMemo(
    () =>
      visibleData
        ? getGraphViewportBounds(visibleData)
        : { minX: 0, minY: 0, maxX: 1400, maxY: 2200 },
    [visibleData],
  );
  const revealPlan = useMemo(
    () => (visibleData ? buildRevealPlan(visibleData) : { phases: [] }),
    [visibleData],
  );
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
    if (!visibleData) {
      setSelectedNodeId(null);
      setFocusMode(false);
      return;
    }

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
    if (!visibleData) {
      return;
    }

    setRevealedNodeIds(visibleData.nodes.map((node) => node.id));
    setRevealedEdgeIds(visibleData.edges.map((edge) => edge.id));
  }, [visibleData]);

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
    if (!visibleData) {
      return;
    }

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
              focusNode(step.id, 1.12, 980);
            } else {
              framePair(step.cameraAnchorId, step.cameraNodeId, 980);
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

          framePair(step.cameraAnchorId, step.cameraNodeId, 1180);
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

      await waitFor(240, runId);

      if (animationController.current.runId !== runId) {
        return;
      }

      void flowRef.current?.fitView({
        duration: FINAL_FRAME_MS,
        maxZoom: 1.02,
        minZoom: 0.56,
        padding: 0.24,
      });

      const finished = await waitFor(FINAL_FRAME_MS, runId);

      if (!finished) {
        return;
      }

      setIsIntroRunning(false);
    })();
  }, [focusNode, framePair, revealPlan.phases, stopIntro, visibleData, waitFor]);

  useEffect(() => {
    if (!hasGraphData || isLoading) {
      stopIntro();
      setRevealedEdgeIds([]);
      setRevealedNodeIds([]);
      return;
    }

    startReveal();

    return () => {
      animationController.current.runId += 1;
      clearScheduledAnimation();
    };
  }, [clearScheduledAnimation, hasGraphData, isLoading, startReveal, stopIntro]);

  const highlightedPath = useMemo(() => {
    if (!visibleData || !focusMode || !selectedNodeId) {
      return { edgeIds: new Set<string>(), nodeIds: new Set<string>() };
    }

    const resolved = resolvePathToCurrent(visibleData, selectedNodeId);

    if (resolved.found) {
      return resolved;
    }

    return getConnectedNeighborhood(visibleData, selectedNodeId);
  }, [focusMode, selectedNodeId, visibleData]);

  const hoverNeighborhood = useMemo(() => {
    if (!visibleData || !hoveredNodeId || focusMode) {
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
    if (!visibleData || !focusMode || highlightedPath.nodeIds.size === 0) {
      return new Set<string>();
    }

    return new Set(
      visibleData.nodes
        .map((node) => node.id)
        .filter((nodeId) => !highlightedPath.nodeIds.has(nodeId)),
    );
  }, [focusMode, highlightedPath.nodeIds, visibleData]);

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
      visibleData
        ? createFlowNodes({
            data: visibleData,
            dimmedNodeIds,
            highlightedNodeIds,
            isFocusMode: focusMode,
            positions,
            revealedNodeIds: revealedNodeIdSet,
            selectedNodeId,
            showReceipts: false,
          })
        : [],
    [
      dimmedNodeIds,
      focusMode,
      highlightedNodeIds,
      positions,
      revealedNodeIdSet,
      selectedNodeId,
      visibleData,
    ],
  );

  const edges = useMemo(
    () =>
      visibleData
        ? createFlowEdges({
            data: visibleData,
            dimmedNodeIds,
            highlightedEdgeIds,
            isFocusMode: focusMode,
            revealDirections,
            revealDurations,
            revealedEdgeIds: revealedEdgeIdSet,
          })
        : [],
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
      if (!visibleData) {
        return;
      }

      if (isIntroRunning) {
        stopIntro({ revealAll: true });
      }

      setSelectedNodeId(node.id);
      setFocusMode(true);
      focusNode(node.id, node.id === visibleData.currentNodeId ? 1.03 : 1.1, 760);
    },
    [focusNode, isIntroRunning, stopIntro, visibleData],
  );

  return (
    <section>
      <div className="flowchart-canvas relative overflow-hidden rounded-[1.3rem] border border-[rgba(12,12,12,0.12)] bg-[rgba(255,255,252,0.96)] shadow-[0_32px_66px_-44px_rgba(0,0,0,0.18)] backdrop-blur-xl">
        <StructuredBackdrop />

        <div className="relative h-[820px] sm:h-[920px] xl:h-[980px]">
          {hasGraphData ? (
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
              nodeExtent={[
                [viewportBounds.minX, viewportBounds.minY],
                [viewportBounds.maxX, viewportBounds.maxY],
              ]}
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
              translateExtent={[
                [viewportBounds.minX, viewportBounds.minY],
                [viewportBounds.maxX, viewportBounds.maxY],
              ]}
              zoomOnDoubleClick={false}
            />
          ) : null}

          {isLoading ? <WaitingTraceOverlay /> : null}
        </div>
      </div>
    </section>
  );
}

function StructuredBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <div className="absolute inset-x-6 bottom-8 top-6 rounded-[1rem] border border-[rgba(12,12,12,0.08)] bg-[linear-gradient(180deg,rgba(255,255,252,0.98),rgba(248,248,245,0.94))]" />
      <div className="absolute inset-x-6 top-6 h-12 border-b border-[rgba(12,12,12,0.08)]" />
      <div className="absolute inset-x-6 bottom-8 h-12 border-t border-[rgba(12,12,12,0.08)]" />
      <div className="absolute bottom-8 left-1/2 top-6 w-px -translate-x-1/2 bg-[linear-gradient(180deg,rgba(12,12,12,0.12),rgba(12,12,12,0.04))]" />
      <div className="absolute bottom-8 left-[29%] top-6 w-px bg-[linear-gradient(180deg,rgba(12,12,12,0.08),rgba(12,12,12,0.02))]" />
      <div className="absolute bottom-8 right-[29%] top-6 w-px bg-[linear-gradient(180deg,rgba(12,12,12,0.08),rgba(12,12,12,0.02))]" />
      <div className="absolute inset-x-6 top-[15rem] h-px bg-[rgba(12,12,12,0.06)]" />
      <div className="absolute inset-x-6 top-[28rem] h-px bg-[rgba(12,12,12,0.05)]" />
      <div className="absolute inset-x-6 top-[41rem] h-px bg-[rgba(12,12,12,0.04)]" />
    </div>
  );
}

function WaitingTraceOverlay() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[4] flex items-center justify-center">
      <div className="relative h-full w-full">
        <motion.div
          animate={{ opacity: [0.14, 0.3, 0.14] }}
          className="absolute left-1/2 top-[18%] h-[52%] w-px -translate-x-1/2 bg-[linear-gradient(180deg,rgba(0,0,0,0.12),rgba(0,0,0,0.44),rgba(0,0,0,0.1))]"
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          animate={{ scaleX: [0.3, 1, 0.3], opacity: [0.08, 0.26, 0.08] }}
          className="absolute left-1/2 top-[32%] h-px w-[22rem] origin-center -translate-x-1/2 bg-[linear-gradient(90deg,rgba(0,0,0,0.02),rgba(0,0,0,0.4),rgba(0,0,0,0.02))]"
          transition={{ duration: 2.2, repeat: Infinity, ease: [0.16, 1, 0.3, 1] }}
        />
        <motion.div
          animate={{ scaleX: [0.2, 1, 0.2], opacity: [0.06, 0.24, 0.06] }}
          className="absolute left-1/2 top-[48%] h-px w-[30rem] origin-center -translate-x-1/2 bg-[linear-gradient(90deg,rgba(0,0,0,0.02),rgba(0,0,0,0.35),rgba(0,0,0,0.02))]"
          transition={{ duration: 2.8, repeat: Infinity, ease: [0.16, 1, 0.3, 1], delay: 0.35 }}
        />
        <motion.div
          animate={{ y: ["0%", "88%", "0%"], opacity: [0, 1, 0] }}
          className="absolute left-1/2 top-[18%] h-6 w-6 -translate-x-1/2 rounded-full border border-[rgba(0,0,0,0.28)] bg-[rgba(255,255,252,0.94)] shadow-[0_10px_28px_-18px_rgba(0,0,0,0.34)]"
          transition={{ duration: 2.9, repeat: Infinity, ease: [0.25, 0.1, 0.25, 1] }}
        />
        <div className="absolute bottom-10 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-center">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[rgba(15,15,15,0.56)]">
            Tracing narrative branches
          </p>
          <p className="max-w-md text-sm leading-6 text-[rgba(15,15,15,0.52)]">
            Holding the tree open while evidence resolves.
          </p>
        </div>
      </div>
    </div>
  );
}
