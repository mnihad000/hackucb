export default function FlowchartLegend() {
  return (
    <div className="max-w-[18rem] rounded-[0.8rem] border border-[rgba(12,12,12,0.12)] bg-[rgba(255,255,252,0.92)] p-4 shadow-[0_18px_32px_-28px_rgba(0,0,0,0.18)] backdrop-blur-sm">
      <p className="text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-[rgba(12,12,12,0.56)]">
        Narrative path map
      </p>
      <div className="mt-3 space-y-2.5 text-sm text-[rgba(10,10,10,0.94)]">
        <LegendItem accent="solid" label="Main narrative path" />
        <LegendItem accent="counter" label="Counter-frame branch" />
        <LegendItem accent="related" label="Related context" />
        <LegendItem accent="uncertain" label="Needs human review" />
        <LegendItem accent="badge" label="Browser-verified receipt" />
      </div>
    </div>
  );
}

function LegendItem({
  accent,
  label,
}: {
  accent: "badge" | "counter" | "related" | "solid" | "uncertain";
  label: string;
}) {
  return (
    <div className="flex items-center gap-3">
      {accent === "badge" ? (
        <span className="rounded-full border border-black bg-black px-2 py-1 text-[0.68rem] font-semibold text-white">
          Verified
        </span>
      ) : (
        <span className="relative inline-flex h-3 w-10 items-center">
          <span
            className={`absolute inset-x-0 top-1/2 h-[2px] -translate-y-1/2 rounded-full ${
              accent === "solid"
                ? "bg-black"
                : accent === "counter"
                  ? "border-t-2 border-dashed border-[#4b4b4b]"
                  : accent === "related"
                    ? "bg-[#5c5c5c]"
                    : "border-t-2 border-dotted border-[#9d9d9d]"
            }`}
          />
        </span>
      )}
      <span>{label}</span>
    </div>
  );
}
