type FlowchartControlsProps = {
  onFitView: () => void;
  onReplay: () => void;
  onResetView: () => void;
  onToggleCounterNarratives: () => void;
  onToggleReceipts: () => void;
  showCounterNarratives: boolean;
  showReceipts: boolean;
};

export default function FlowchartControls({
  onFitView,
  onReplay,
  onResetView,
  onToggleCounterNarratives,
  onToggleReceipts,
  showCounterNarratives,
  showReceipts,
}: FlowchartControlsProps) {
  return (
    <div className="flex max-w-[21rem] flex-wrap justify-end gap-2 rounded-[0.75rem] border border-[rgba(12,12,12,0.12)] bg-[rgba(255,255,252,0.92)] p-3 shadow-[0_18px_34px_-28px_rgba(0,0,0,0.18)] backdrop-blur-sm">
      <ControlButton label="Reset View" onClick={onResetView} />
      <ControlButton label="Fit View" onClick={onFitView} />
      <ControlButton label="Replay Animation" onClick={onReplay} />
      <ControlButton
        active={showReceipts}
        label="Show Receipts"
        onClick={onToggleReceipts}
      />
      <ControlButton
        active={showCounterNarratives}
        label="Toggle Counter-Narratives"
        onClick={onToggleCounterNarratives}
      />
    </div>
  );
}

function ControlButton({
  active = false,
  label,
  onClick,
}: {
  active?: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      className={`rounded-full border px-3 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.14em] transition hover:-translate-y-0.5 ${
        active
          ? "border-black bg-black text-white"
          : "border-[rgba(12,12,12,0.12)] bg-white text-[rgba(14,14,14,0.62)] hover:border-black hover:text-black"
      }`}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}
