import { motion } from "framer-motion";
import type { InvestigationNode } from "../../types/rhetoriq";
import {
  countNodeReceipts,
  getConfidenceLabel,
  getNodeHost,
  getNodeTypeLabel,
  hasBrowserVerifiedReceipt,
  pickNodeUrl,
  type BranchVariant,
} from "./treeLayout";

type CardKind = "trunk" | "current" | BranchVariant;

const EASE_OUT = [0.16, 1, 0.3, 1] as const;

const kindAccent: Record<CardKind, string> = {
  current: "var(--ink)",
  trunk: "var(--accent)",
  counter: "#b06a5b",
  related: "var(--accent)",
  uncertain: "#9a8a5c",
};

export default function InvestigationNodeCard({
  node,
  kind,
}: {
  node: InvestigationNode;
  kind: CardKind;
}) {
  const url = pickNodeUrl(node);
  const host = getNodeHost(node);
  const receiptCount = countNodeReceipts(node);
  const verified = hasBrowserVerifiedReceipt(node);
  const accent = kindAccent[kind];
  const isBranch = kind === "counter" || kind === "related" || kind === "uncertain";
  const isCurrent = kind === "current";

  const shell = isCurrent
    ? "border-[var(--ink)] bg-white shadow-[0_30px_60px_-40px_rgba(19,35,58,0.45)] ring-1 ring-[rgba(19,35,58,0.08)]"
    : isBranch
      ? "border-[rgba(23,44,71,0.12)] bg-[rgba(255,255,255,0.78)] shadow-[0_18px_38px_-34px_rgba(19,35,58,0.3)]"
      : "border-[rgba(23,44,71,0.12)] bg-[rgba(255,255,255,0.92)] shadow-[0_24px_50px_-40px_rgba(19,35,58,0.36)]";

  const Wrapper = url ? motion.a : motion.div;
  const interactiveProps = url
    ? {
        href: url,
        target: "_blank" as const,
        rel: "noreferrer noopener" as const,
        whileHover: { y: -3 },
      }
    : {};

  return (
    <Wrapper
      {...interactiveProps}
      className={`group relative block overflow-hidden rounded-[1.15rem] border ${shell} ${
        url
          ? "cursor-pointer transition-shadow hover:shadow-[0_34px_64px_-38px_rgba(19,35,58,0.5)]"
          : ""
      } ${isBranch ? "px-4 py-4" : "px-5 py-5 sm:px-6 sm:py-6"}`}
      transition={{ duration: 0.35, ease: EASE_OUT }}
    >
      {/* accent spine on the card's left edge */}
      <span
        aria-hidden="true"
        className="absolute inset-y-0 left-0 w-[3px]"
        style={{ backgroundColor: accent, opacity: isCurrent ? 1 : 0.55 }}
      />

      <div className="flex items-start justify-between gap-3">
        <p
          className="text-[0.62rem] font-semibold uppercase tracking-[0.22em]"
          style={{ color: accent }}
        >
          {getNodeTypeLabel(node.nodeType)}
        </p>
        {node.timestamp ? (
          <span className="shrink-0 rounded-full border border-[var(--border)] bg-[var(--accent-soft)] px-2.5 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
            {node.timestamp}
          </span>
        ) : null}
      </div>

      <h3
        className={`mt-3 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] tracking-[-0.02em] text-[var(--ink)] ${
          isCurrent
            ? "text-[1.5rem] leading-[1.12]"
            : isBranch
              ? "text-[1.05rem] leading-[1.2]"
              : "text-[1.25rem] leading-[1.16]"
        }`}
      >
        {node.label}
      </h3>

      {node.summary ? (
        <p
          className={`mt-2.5 text-[0.9rem] leading-6 text-[var(--muted)] ${
            isBranch ? "line-clamp-2" : "line-clamp-3"
          }`}
        >
          {node.summary}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.1em] text-[var(--muted)]">
        <span className="rounded-md border border-[var(--border)] bg-white/70 px-2 py-1">
          {node.sourceCount} {node.sourceCount === 1 ? "source" : "sources"}
        </span>
        {receiptCount > 0 ? (
          <span className="rounded-md border border-[var(--border)] bg-white/70 px-2 py-1">
            {receiptCount} receipts
          </span>
        ) : null}
        {node.confidence ? (
          <span className="rounded-md border border-[var(--border)] bg-white/70 px-2 py-1">
            {getConfidenceLabel(node.confidence)}
          </span>
        ) : null}
        {verified ? (
          <span className="rounded-md border border-[var(--ink)] bg-[var(--ink)] px-2 py-1 text-white">
            Verified
          </span>
        ) : null}
      </div>

      {url ? (
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-[var(--border)] pt-3">
          <span className="truncate text-[0.72rem] font-medium text-[var(--muted)]">
            {host ?? "Open source"}
          </span>
          <span className="inline-flex shrink-0 items-center gap-1 text-[0.72rem] font-semibold text-[var(--accent)] transition-colors group-hover:text-[var(--ink)]">
            Read article
            <svg
              aria-hidden="true"
              className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              viewBox="0 0 16 16"
              fill="none"
            >
              <path
                d="M5 11L11 5M11 5H6M11 5V10"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        </div>
      ) : null}
    </Wrapper>
  );
}
