import { AnimatePresence, motion } from "framer-motion";
import type { InvestigationNode } from "../../types/rhetoriq";
import {
  countNodeReceipts,
  getConfidenceLabel,
  getNodeTypeLabel,
  hasBrowserVerifiedReceipt,
  splitSourcesByStance,
} from "./utils";

type NodeDetailsPanelProps = {
  node: InvestigationNode | null;
  onClose: () => void;
  showReceipts: boolean;
};

export default function NodeDetailsPanel({
  node,
  onClose,
  showReceipts,
}: NodeDetailsPanelProps) {
  return (
    <aside className="flowchart-panel min-h-[20rem] overflow-hidden rounded-[1.9rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.92)] shadow-[0_35px_65px_-38px_rgba(19,35,58,0.36)] backdrop-blur-xl">
      <AnimatePresence initial={false} mode="wait">
        {node ? (
          <motion.div
            key={node.id}
            animate={{ opacity: 1, x: 0 }}
            className="flex h-full flex-col"
            exit={{ opacity: 0, x: 16 }}
            initial={{ opacity: 0, x: 16 }}
            transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
          >
            <PanelHeader node={node} onClose={onClose} />
            <div className="flow-detail-scroll flex-1 space-y-5 overflow-y-auto px-5 pb-5">
              <section className="rounded-[1.4rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4">
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Why this node matters
                </p>
                <p className="mt-3 text-[0.98rem] leading-7 text-[var(--ink)]">
                  {node.summary ??
                    "This narrative moment has limited supporting detail in the current demo dataset."}
                </p>
              </section>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <Metric label="Node type" value={getNodeTypeLabel(node.nodeType)} />
                <Metric
                  label="Confidence"
                  value={
                    node.confidence
                      ? getConfidenceLabel(node.confidence)
                      : "Unknown confidence"
                  }
                />
                <Metric label="Sources" value={`${node.sourceCount}`} />
                <Metric
                  label="Counter sources"
                  value={`${node.counterSourceCount ?? 0}`}
                />
                <Metric label="Receipts" value={`${countNodeReceipts(node)}`} />
                <Metric label="Timestamp" value={node.timestamp ?? "Unavailable"} />
              </div>

              <SourceSection node={node} />

              <section className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                      Receipts
                    </p>
                    <p className="mt-1 text-sm text-[var(--muted)]">
                      Clickable evidence for this narrative moment.
                    </p>
                  </div>
                  {hasBrowserVerifiedReceipt(node) ? (
                    <span className="rounded-full bg-[rgba(147,167,194,0.14)] px-3 py-1 text-[0.72rem] font-semibold text-[#5c7391]">
                      Browser verified
                    </span>
                  ) : null}
                </div>

                {!showReceipts ? (
                  <div className="rounded-[1.3rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(245,248,250,0.92)] p-4 text-sm leading-6 text-[var(--muted)]">
                    Turn on <span className="font-semibold text-[var(--ink)]">Show Receipts</span> to
                    expand receipt evidence and strengthen the node indicators on the map.
                  </div>
                ) : (node.receipts ?? []).length > 0 ? (
                  <div className="space-y-3">
                    {(node.receipts ?? []).map((receipt) => (
                      <article
                        key={receipt.id}
                        className="rounded-[1.35rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="text-base font-semibold text-[var(--ink)]">
                              {receipt.title}
                            </h4>
                            <p className="mt-1 text-sm text-[var(--muted)]">
                              {receipt.sourceName}
                            </p>
                          </div>
                          {receipt.browserVerified ? (
                            <span className="rounded-full bg-[rgba(147,167,194,0.14)] px-2.5 py-1 text-[0.68rem] font-semibold text-[#5c7391]">
                              Verified
                            </span>
                          ) : null}
                        </div>
                        <p className="mt-3 text-sm leading-6 text-[var(--ink)]">
                          {receipt.quoteOrSnippet}
                        </p>
                        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                          {receipt.supportReason}
                        </p>
                        {receipt.url ? (
                          <a
                            className="mt-3 inline-flex text-sm font-semibold text-[var(--accent)] transition hover:text-[#627997]"
                            href={receipt.url}
                            rel="noreferrer"
                            target="_blank"
                          >
                            Open source
                          </a>
                        ) : (
                          <p className="mt-3 text-sm font-medium text-[var(--muted)]">
                            Seeded demo source
                          </p>
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-[1.3rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(245,248,250,0.92)] p-4 text-sm leading-6 text-[var(--muted)]">
                    No receipts are attached to this node yet. The map should still remain stable when
                    evidence is incomplete.
                  </div>
                )}
              </section>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            animate={{ opacity: 1 }}
            className="flex h-full min-h-[20rem] flex-col items-center justify-center px-6 text-center"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            transition={{ duration: 0.22 }}
          >
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
              Narrative moment details
            </p>
            <h3 className="mt-3 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">
              Select a node on the map.
            </h3>
            <p className="mt-4 max-w-sm text-sm leading-7 text-[var(--muted)]">
              Clicking a node focuses the camera, highlights the route to the latest narrative state,
              and opens its supporting sources and receipts here.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  );
}

function PanelHeader({
  node,
  onClose,
}: {
  node: InvestigationNode;
  onClose: () => void;
}) {
  return (
    <div className="border-b border-[rgba(19,35,58,0.08)] px-5 pb-4 pt-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            {getNodeTypeLabel(node.nodeType)}
          </p>
          <h3 className="mt-2 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">
            {node.label}
          </h3>
          {node.subtitle ? (
            <p className="mt-2 text-sm font-medium text-[var(--muted)]">{node.subtitle}</p>
          ) : null}
        </div>

        <button
          className="rounded-full border border-[rgba(19,35,58,0.08)] px-3 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)] transition hover:border-[rgba(124,144,172,0.24)] hover:text-[var(--accent)]"
          onClick={onClose}
          type="button"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-[rgba(19,35,58,0.08)] bg-white/90 p-4">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold text-[var(--ink)]">{value}</p>
    </div>
  );
}

function SourceSection({ node }: { node: InvestigationNode }) {
  const { opposing, supporting } = splitSourcesByStance(node);

  return (
    <section className="space-y-4">
      <SourceGroup
        emptyMessage="No supporting or contextual sources are attached to this node."
        sources={supporting}
        title="Supporting Sources"
      />
      <SourceGroup
        emptyMessage="No opposing or counter-frame sources are attached to this node."
        sources={opposing}
        title="Opposing / Counter-Frame Sources"
      />
    </section>
  );
}

function SourceGroup({
  emptyMessage,
  sources,
  title,
}: {
  emptyMessage: string;
  sources: InvestigationNode["sources"];
  title: string;
}) {
  return (
    <section>
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {title}
      </p>
      {(sources ?? []).length > 0 ? (
        <div className="mt-3 space-y-3">
          {(sources ?? []).map((source) => (
            <article
              key={source.id}
              className="rounded-[1.3rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-base font-semibold text-[var(--ink)]">{source.title}</h4>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {source.name} - {source.type}
                  </p>
                </div>
                {source.stance ? (
                  <span className="rounded-full bg-[rgba(19,35,58,0.06)] px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                    {source.counterType ?? source.stance}
                  </span>
                ) : null}
              </div>
              {source.publishedAt ? (
                <p className="mt-3 text-sm font-medium text-[var(--muted)]">{source.publishedAt}</p>
              ) : null}
              {source.snippet ? (
                <p className="mt-3 text-sm leading-6 text-[var(--ink)]">{source.snippet}</p>
              ) : null}
              {source.url ? (
                <a
                  className="mt-3 inline-flex text-sm font-semibold text-[var(--accent)] transition hover:text-[#627997]"
                  href={source.url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Open source
                </a>
              ) : (
                <p className="mt-3 text-sm font-medium text-[var(--muted)]">
                  No public URL available
                </p>
              )}
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-3 rounded-[1.25rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(245,248,250,0.92)] p-4 text-sm leading-6 text-[var(--muted)]">
          {emptyMessage}
        </div>
      )}
    </section>
  );
}
