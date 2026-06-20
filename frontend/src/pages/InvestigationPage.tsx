import { startTransition, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import InvestigationFlowchart from "../components/investigation-flowchart/InvestigationFlowchart";
import Header from "../components/layout/Header";
import { Waves } from "../components/ui/wave-background";
import {
  ApiError,
  getInvestigationWorkspace,
  runAnalyst,
  runClaimCounterpoints,
  runCounterNarratives,
  runReport,
  runRetrieval,
  runSourceDiversity,
  runTimeline,
} from "../lib/api";
import { getInvestigationExperience } from "../lib/demoData";
import {
  buildInvestigationExperienceFromWorkspace,
  formatClaimConfidence,
  getCoverageHighlights,
  getLimitations,
  getRecommendedChecks,
  getSearchWarnings,
  getSourceDiversityCaveat,
  getSourceDiversityFindings,
  getSourceDiversityHighlights,
  getStageLabel,
  getTopClaims,
  isLiveInvestigationId,
} from "../lib/liveInvestigation";
import type { LiveInvestigationWorkspace, LiveSourceDiversityResult } from "../types/rhetoriq";

export default function InvestigationPage() {
  const { id = "demo" } = useParams();
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") ?? undefined;
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [workspace, setWorkspace] = useState<LiveInvestigationWorkspace | null>(null);
  const isLiveInvestigation = isLiveInvestigationId(id);

  useEffect(() => {
    if (!isLiveInvestigation) {
      setWorkspace(null);
      setErrorMessage(null);
      setIsLoading(false);
      setIsRunningPipeline(false);
      return;
    }

    let cancelled = false;

    async function hydrateLiveInvestigation() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        let nextWorkspace = await getInvestigationWorkspace(id);
        if (cancelled) {
          return;
        }

        startTransition(() => {
          setWorkspace(nextWorkspace);
        });

        if (!nextWorkspace.retrieval) {
          setIsRunningPipeline(true);
          await runRetrieval(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.source_diversity) {
          setIsRunningPipeline(true);
          await runSourceDiversity(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.timeline) {
          setIsRunningPipeline(true);
          await runTimeline(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.counter_narratives) {
          setIsRunningPipeline(true);
          await runCounterNarratives(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.analyst) {
          setIsRunningPipeline(true);
          await runAnalyst(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.claim_counterpoints) {
          setIsRunningPipeline(true);
          await runClaimCounterpoints(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.report) {
          setIsRunningPipeline(true);
          await runReport(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof ApiError
              ? error.message
              : "Unable to load the live investigation.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
          setIsRunningPipeline(false);
        }
      }
    }

    void hydrateLiveInvestigation();

    return () => {
      cancelled = true;
    };
  }, [id, isLiveInvestigation]);

  const experience = isLiveInvestigation
    ? workspace
      ? buildInvestigationExperienceFromWorkspace(workspace)
      : null
    : getInvestigationExperience(id, query);
  const coverageHighlights = workspace ? getCoverageHighlights(workspace) : [];
  const limitations = workspace ? getLimitations(workspace) : [];
  const recommendedChecks = workspace ? getRecommendedChecks(workspace) : [];
  const searchWarnings = workspace ? getSearchWarnings(workspace) : [];
  const topClaims = workspace ? getTopClaims(workspace) : [];
  const stageLabel = workspace ? getStageLabel(workspace) : null;
  const sourceDiversityHighlights = workspace ? getSourceDiversityHighlights(workspace) : [];
  const sourceDiversityFindings = workspace ? getSourceDiversityFindings(workspace) : [];
  const sourceDiversityCaveat = workspace ? getSourceDiversityCaveat(workspace.source_diversity) : null;

  return (
    <main className="investigation-page min-h-screen bg-white">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0">
        <Waves
          backgroundColor="#ffffff"
          className="h-full w-full opacity-100"
          strokeColor="#000000"
        />
      </div>

      <div className="relative z-10">
        <Header />
      </div>

      <section className="relative z-10 px-4 pb-24 pt-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1440px] space-y-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--muted)] transition hover:text-[var(--accent)]"
          >
            <span aria-hidden="true">{"<"}</span>
            Back to homepage
          </Link>

          {experience ? (
            <div className="investigation-hero page-enter overflow-hidden rounded-[2.2rem] border border-[rgba(19,35,58,0.08)] p-7 shadow-[0_55px_90px_-54px_rgba(19,35,58,0.46)] backdrop-blur-xl sm:p-9">
              <div className="grid gap-7 xl:grid-cols-[minmax(0,1.15fr)_21rem] xl:items-end">
                <div>
                  <p className="eyebrow">{experience.kicker}</p>
                  <h1 className="mt-5 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] text-4xl font-semibold tracking-[-0.05em] text-[var(--ink)] sm:text-5xl lg:text-6xl">
                    {experience.title}
                  </h1>
                  <p className="mt-5 max-w-3xl text-lg leading-8 text-[var(--muted)]">
                    Source-grounded investigation workspace for tracing how a civic
                    narrative spread, branched, and took shape in the available dataset.
                  </p>

                  <div className="mt-6 flex flex-wrap gap-3">
                    <span className="data-pill">{experience.status}</span>
                    <span className="data-pill">{experience.confidence} confidence</span>
                    <span className="data-pill">{experience.sourceCount} sources</span>
                    <span className="data-pill">{experience.receiptCount} receipts</span>
                  </div>

                  <div className="mt-7 rounded-[1.6rem] border border-[rgba(19,35,58,0.08)] bg-white/78 p-5">
                    <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
                      User asked
                    </p>
                    <p className="mt-3 text-lg leading-8 text-[var(--ink)]">
                      "{workspace?.query_text ?? query ?? experience.flowchartData.query}"
                    </p>
                  </div>
                </div>

                <div className="grid gap-3">
                  <MetricCard label="Generated" value={experience.generatedAt} />
                  <MetricCard
                    label="First observed in our dataset"
                    value={experience.firstObserved}
                  />
                  <MetricCard label="Receipts available" value={`${experience.receiptCount}`} />
                  <MetricCard
                    label="Current narrative state"
                    value={stageLabel ?? experience.status}
                  />
                </div>
              </div>
            </div>
          ) : (
            <LoadingHero query={query} />
          )}

          {isLiveInvestigation ? (
            <PipelineStatusCard
              errorMessage={errorMessage}
              isLoading={isLoading}
              isRunningPipeline={isRunningPipeline}
              stageLabel={stageLabel}
            />
          ) : null}

          {experience ? (
            <div className="rounded-[2rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.86)] p-7 shadow-[0_38px_68px_-46px_rgba(19,35,58,0.4)] backdrop-blur-xl sm:p-8">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div className="max-w-4xl">
                  <p className="eyebrow">Executive summary</p>
                  <p className="mt-5 text-lg leading-8 text-[var(--ink)]">
                    {experience.summary}
                  </p>
                </div>
                <div className="rounded-[1.5rem] border border-[rgba(19,35,58,0.08)] bg-white/88 p-5 lg:max-w-[20rem]">
                  <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                    Cautious framing
                  </p>
                  <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                    RhetoriQ shows first observed sources, spread patterns, and competing
                    frames. It does not assign truth scores or claim coordination without
                    evidence.
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          {workspace ? (
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(18rem,24rem)]">
              <div className="space-y-6">
                {experience ? <InvestigationFlowchart data={experience.flowchartData} /> : null}
                {topClaims.length > 0 ? <ClaimsCard claims={topClaims} /> : null}
              </div>
              <div className="space-y-6">
                {coverageHighlights.length > 0 ? (
                  <InfoCard title="Coverage">
                    {coverageHighlights.map((item) => (
                      <InfoPill key={item} value={item} />
                    ))}
                  </InfoCard>
                ) : null}
                {workspace.source_diversity ? (
                  <InfoCard title="Source Diversity">
                    {sourceDiversityHighlights.map((item) => (
                      <InfoPill key={item} value={item} />
                    ))}
                    {formatDistributionRows(workspace.source_diversity).map((item) => (
                      <InfoListItem key={item} value={item} />
                    ))}
                    {sourceDiversityFindings.map((item) => (
                      <InfoListItem key={item.id} value={`${item.label}: ${item.detail}`} />
                    ))}
                    {sourceDiversityCaveat ? <InfoListItem value={sourceDiversityCaveat} /> : null}
                  </InfoCard>
                ) : null}
                {recommendedChecks.length > 0 ? (
                  <InfoCard title="Recommended Human Checks">
                    {recommendedChecks.map((item) => (
                      <InfoListItem key={item} value={item} />
                    ))}
                  </InfoCard>
                ) : null}
                {limitations.length > 0 ? (
                  <InfoCard title="Limitations">
                    {limitations.map((item) => (
                      <InfoListItem key={item} value={item} />
                    ))}
                  </InfoCard>
                ) : null}
                {searchWarnings.length > 0 ? (
                  <InfoCard title="Retriever Warnings">
                    {searchWarnings.map((item) => (
                      <InfoListItem key={item} value={item} />
                    ))}
                  </InfoCard>
                ) : null}
              </div>
            </div>
          ) : null}

          {!workspace && !experience && errorMessage ? (
            <div className="rounded-[1.6rem] border border-[rgba(146,71,71,0.18)] bg-[rgba(255,244,244,0.92)] p-6 text-sm leading-7 text-[rgb(130,50,50)]">
              {errorMessage}
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}

function LoadingHero({ query }: { query?: string }) {
  return (
    <div className="investigation-hero page-enter overflow-hidden rounded-[2.2rem] border border-[rgba(19,35,58,0.08)] p-7 shadow-[0_55px_90px_-54px_rgba(19,35,58,0.46)] backdrop-blur-xl sm:p-9">
      <p className="eyebrow">Live investigation workspace</p>
      <h1 className="mt-5 font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] text-4xl font-semibold tracking-[-0.05em] text-[var(--ink)] sm:text-5xl lg:text-6xl">
        Building investigation
      </h1>
      <p className="mt-5 max-w-3xl text-lg leading-8 text-[var(--muted)]">
        {query
          ? `Preparing evidence-backed investigation for "${query}".`
          : "Preparing evidence-backed investigation."}
      </p>
    </div>
  );
}

function PipelineStatusCard({
  errorMessage,
  isLoading,
  isRunningPipeline,
  stageLabel,
}: {
  errorMessage: string | null;
  isLoading: boolean;
  isRunningPipeline: boolean;
  stageLabel: string | null;
}) {
  if (!isLoading && !isRunningPipeline && !errorMessage) {
    return null;
  }

  return (
    <div className="rounded-[1.6rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.9)] p-5 shadow-[0_28px_55px_-42px_rgba(19,35,58,0.34)]">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        Live pipeline
      </p>
      <p className="mt-3 text-base leading-7 text-[var(--ink)]">
        {errorMessage
          ? errorMessage
          : isRunningPipeline
            ? `Advancing backend stages. ${stageLabel ?? "Investigation in progress."}`
            : "Loading persisted investigation state."}
      </p>
    </div>
  );
}

function ClaimsCard({
  claims,
}: {
  claims: NonNullable<LiveInvestigationWorkspace["report"]>["key_claims"];
}) {
  return (
    <div className="rounded-[2rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.86)] p-7 shadow-[0_38px_68px_-46px_rgba(19,35,58,0.4)] backdrop-blur-xl sm:p-8">
      <p className="eyebrow">Key claims</p>
      <div className="mt-5 space-y-4">
        {claims.slice(0, 4).map((claim) => (
          <article
            key={claim.claim_id}
            className="rounded-[1.4rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-5"
          >
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="data-pill">{claim.claim_type}</span>
              <span className="data-pill">{formatClaimConfidence(claim)}</span>
            </div>
            <p className="mt-4 text-base leading-7 text-[var(--ink)]">{claim.claim_text}</p>
            {claim.counterpoint_summary ? (
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                Counterpoint: {claim.counterpoint_summary}
              </p>
            ) : null}
            {claim.citations[0] ? (
              <a
                className="mt-4 inline-flex text-sm font-semibold text-[var(--accent)] transition hover:text-[#627997]"
                href={claim.citations[0].url}
                rel="noreferrer"
                target="_blank"
              >
                {claim.citations[0].source_name}
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function InfoCard({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) {
  return (
    <div className="rounded-[1.7rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.88)] p-5 shadow-[0_24px_44px_-34px_rgba(19,35,58,0.34)]">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {title}
      </p>
      <div className="mt-4 space-y-3">{children}</div>
    </div>
  );
}

function InfoPill({ value }: { value: string }) {
  return (
    <div className="rounded-[1rem] border border-[rgba(19,35,58,0.08)] bg-white/90 px-4 py-3 text-sm font-semibold text-[var(--ink)]">
      {value}
    </div>
  );
}

function InfoListItem({ value }: { value: string }) {
  return (
    <p className="rounded-[1rem] border border-[rgba(19,35,58,0.08)] bg-white/90 px-4 py-3 text-sm leading-7 text-[var(--ink)]">
      {value}
    </p>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.45rem] border border-[rgba(19,35,58,0.08)] bg-white/82 p-4 shadow-[0_20px_44px_-34px_rgba(19,35,58,0.34)]">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold leading-6 text-[var(--ink)]">{value}</p>
    </div>
  );
}

function formatDistributionRows(diversity: LiveSourceDiversityResult) {
  return [
    formatDistributionLine("Source types", diversity.source_type_distribution),
    formatDistributionLine("Geography", diversity.geographic_distribution),
    formatDistributionLine("Institutions", diversity.institution_distribution),
    formatDistributionLine("Content forms", diversity.content_form_distribution),
  ].filter(Boolean) as string[];
}

function formatDistributionLine(label: string, distribution: Record<string, number>) {
  const entries = Object.entries(distribution)
    .filter(([, count]) => count > 0)
    .sort((left, right) => right[1] - left[1]);
  if (entries.length === 0) {
    return "";
  }
  const summary = entries
    .map(([key, count]) => `${key.replaceAll("_", " ")}: ${count}`)
    .join(", ");
  return `${label}: ${summary}`;
}
