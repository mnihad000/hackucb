import {
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";
import { motion } from "framer-motion";
import type { InvestigationFlowEdge } from "./utils";

const edgeStyles = {
  counter: {
    dasharray: "10 8",
    glow: "rgba(24, 24, 24, 0.05)",
    stroke: "#4b4b4b",
    width: 2.1,
  },
  main: {
    dasharray: undefined,
    glow: "rgba(0, 0, 0, 0.08)",
    stroke: "#070707",
    width: 2.9,
  },
  related: {
    dasharray: undefined,
    glow: "rgba(34, 34, 34, 0.04)",
    stroke: "#5c5c5c",
    width: 1.9,
  },
  uncertain: {
    dasharray: "3 10",
    glow: "rgba(34, 34, 34, 0.02)",
    stroke: "#9d9d9d",
    width: 1.7,
  },
} as const;

export default function AnimatedInvestigationEdge({
  data,
  markerEnd,
  sourcePosition,
  sourceX,
  sourceY,
  targetPosition,
  targetX,
  targetY,
}: EdgeProps<InvestigationFlowEdge>) {
  if (!data) {
    return null;
  }

  const pathArgs =
    data.revealDirection === "reverse"
      ? {
          borderRadius: 14,
          offset: 12,
          sourcePosition: targetPosition,
          sourceX: targetX,
          sourceY: targetY,
          targetPosition: sourcePosition,
          targetX: sourceX,
          targetY: sourceY,
        }
      : {
          borderRadius: 14,
          offset: 12,
          sourcePosition,
          sourceX,
          sourceY,
          targetPosition,
          targetX,
          targetY,
        };
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    ...pathArgs,
    borderRadius: 6,
    offset: 10,
  });
  const style = edgeStyles[data.variant];
  const duration = data.revealDurationMs / 1000;
  const baseOpacity = data.isDimmed ? 0.12 : data.isHighlighted ? 1 : 0.72;

  return (
    <>
      <motion.path
        animate={{
          opacity: data.isRevealed ? (data.isDimmed ? 0.08 : 0.18) : 0,
          pathLength: data.isRevealed ? 1 : 0,
        }}
        d={edgePath}
        fill="none"
        initial={false}
        stroke={style.glow}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={style.width + 8}
        transition={{ duration, ease: [0.16, 1, 0.3, 1] }}
      />
      <motion.path
        animate={{
          opacity: data.isRevealed ? baseOpacity : 0,
          pathLength: data.isRevealed ? 1 : 0,
        }}
        d={edgePath}
        fill="none"
        initial={false}
        markerEnd={markerEnd}
        stroke={style.stroke}
        strokeDasharray={style.dasharray}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={style.width}
        transition={{ duration, ease: [0.16, 1, 0.3, 1] }}
      />

      {data.showLabel && data.edge.label ? (
        <EdgeLabelRenderer>
          <div
            className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 border border-[rgba(14,14,14,0.24)] bg-[rgba(255,255,253,0.96)] px-2.5 py-1 text-[0.64rem] font-semibold uppercase tracking-[0.16em] text-[rgba(15,15,15,0.62)] shadow-[0_12px_24px_-22px_rgba(0,0,0,0.22)]"
            style={{
              left: `${labelX}px`,
              top: `${labelY}px`,
            }}
          >
            {data.edge.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
