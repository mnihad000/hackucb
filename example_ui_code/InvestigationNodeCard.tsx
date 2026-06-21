import { Handle, Position, type NodeProps } from "@xyflow/react";
import { motion } from "framer-motion";
import {
  countNodeReceipts,
  getConfidenceLabel,
  getNodeTypeLabel,
  hasBrowserVerifiedReceipt,
  type InvestigationFlowNode,
} from "./utils";

const containerStyles = {
  counter:
    "border-[rgba(22,22,22,0.88)] bg-[rgba(251,251,249,0.98)] shadow-[0_24px_48px_-36px_rgba(0,0,0,0.2)]",
  current:
    "border-black bg-[rgba(253,253,251,0.995)] shadow-[0_28px_56px_-34px_rgba(0,0,0,0.24)]",
  dimmed: "border-[rgba(24,24,24,0.2)] bg-[rgba(248,248,246,0.76)] shadow-none",
  main:
    "border-[rgba(24,24,24,0.82)] bg-[rgba(251,251,249,0.99)] shadow-[0_24px_48px_-38px_rgba(0,0,0,0.18)]",
  related:
    "border-[rgba(24,24,24,0.72)] bg-[rgba(250,250,248,0.98)] shadow-[0_24px_46px_-40px_rgba(0,0,0,0.14)]",
  selected:
    "border-black bg-[rgba(255,255,253,1)] shadow-[0_0_0_1px_rgba(0,0,0,0.1),0_32px_64px_-34px_rgba(0,0,0,0.28)]",
  uncertain:
    "border-[rgba(70,70,70,0.6)] bg-[rgba(247,247,245,0.92)] shadow-[0_18px_36px_-30px_rgba(0,0,0,0.14)]",
} as const;

export default function InvestigationNodeCard({
  data,
}: NodeProps<InvestigationFlowNode>) {
  const {
    isCurrent,
    isHighlighted,
    isRevealed,
    node,
    showReceipts,
    visualState,
  } = data;
  const receiptCount = countNodeReceipts(node);
  const hasVerified = hasBrowserVerifiedReceipt(node);

  return (
    <>
      <Handle
        className="!h-0 !min-h-0 !min-w-0 !w-0 !border-0 !bg-transparent !opacity-0"
        id="top"
        position={Position.Top}
        type="target"
      />
      <motion.div
        animate={{
          opacity: isRevealed ? 1 : 0,
          scale: isRevealed ? 1 : 0.985,
          y: isRevealed ? 0 : 28,
        }}
        className="nodrag nopan relative w-[420px]"
        initial={false}
        transition={{ duration: 0.68, ease: [0.16, 1, 0.3, 1] }}
      >
        <div
          className={`relative min-h-[318px] overflow-hidden rounded-[0.55rem] border px-7 py-7 transition duration-300 ${
            containerStyles[visualState]
          } ${isHighlighted ? "ring-1 ring-[rgba(0,0,0,0.18)]" : ""}`}
        >
          <div className="relative">
            <div className="flex items-start justify-between gap-4">
              <p className="text-[0.66rem] font-semibold uppercase tracking-[0.26em] text-[rgba(18,18,18,0.54)]">
                {getNodeTypeLabel(node.nodeType)}
              </p>
              <div
                className={`flex shrink-0 items-center gap-2.5 rounded-full border px-2.5 py-1.5 ${
                  isHighlighted || visualState === "selected"
                    ? "border-black bg-black text-white"
                    : "border-[rgba(18,18,18,0.12)] bg-[rgba(0,0,0,0.035)] text-[rgba(12,12,12,0.62)]"
                }`}
              >
                <span className="text-[0.72rem] font-semibold uppercase tracking-[0.1em]">
                  {node.timestamp ?? "Observed"}
                </span>
                <span className="grid h-7 w-7 place-items-center rounded-full bg-black">
                  <NodeGlyph className="h-[1.125rem] w-[1.125rem]" />
                </span>
              </div>
            </div>
            <h3
              className={`mt-4 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] tracking-[-0.03em] text-[rgba(9,9,9,0.96)] ${
                isCurrent ? "text-[2rem] leading-[1.02]" : "text-[1.7rem] leading-[1.14]"
              }`}
            >
              {node.label}
            </h3>

            {node.summary ? (
              <p className="mt-7 text-[0.97rem] leading-9 text-[rgba(14,14,14,0.9)]">
                {node.summary}
              </p>
            ) : null}

            <div className="mt-7 flex flex-wrap gap-2.5 text-[0.76rem] font-semibold uppercase tracking-[0.12em] text-[rgba(22,22,22,0.64)]">
              <span className="border border-[rgba(18,18,18,0.12)] bg-[rgba(0,0,0,0.035)] px-2.5 py-1">
                {node.sourceCount} sources
              </span>
              {receiptCount > 0 ? (
                <span
                  className={`border px-2.5 py-1 ${
                    showReceipts
                      ? "border-black bg-[rgba(0,0,0,0.06)] text-black"
                      : "border-[rgba(18,18,18,0.12)] bg-[rgba(0,0,0,0.03)]"
                  }`}
                >
                  {receiptCount} receipts
                </span>
              ) : null}
              {node.confidence ? (
                <span className="border border-[rgba(18,18,18,0.12)] bg-[rgba(0,0,0,0.03)] px-2.5 py-1">
                  {getConfidenceLabel(node.confidence)}
                </span>
              ) : null}
              {hasVerified ? (
                <span className="border border-black bg-black px-2.5 py-1 text-white">
                  Receipt verified
                </span>
              ) : null}
            </div>

            {node.subtitle ? (
              <p className="mt-6 text-sm font-medium uppercase tracking-[0.14em] text-[rgba(20,20,20,0.5)]">
                {node.subtitle}
              </p>
            ) : null}
          </div>
        </div>
      </motion.div>
      <Handle
        className="!h-0 !min-h-0 !min-w-0 !w-0 !border-0 !bg-transparent !opacity-0"
        id="bottom"
        position={Position.Bottom}
        type="source"
      />
    </>
  );
}

function NodeGlyph({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {Array.from({ length: 8 }, (_, index) => {
        const angle = (index * Math.PI) / 4;
        const x1 = 20 + Math.cos(angle) * 3;
        const y1 = 20 + Math.sin(angle) * 3;
        const x2 = 20 + Math.cos(angle) * 12;
        const y2 = 20 + Math.sin(angle) * 12;

        return (
          <line
            key={index}
            stroke="white"
            strokeLinecap="round"
            strokeWidth="2.8"
            x1={x1}
            x2={x2}
            y1={y1}
            y2={y2}
          />
        );
      })}
      <circle cx="20" cy="20" fill="white" r="2.6" />
    </svg>
  );
}
