import { startTransition, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import InvestigationFlowchart from "../components/investigation-flowchart/InvestigationFlowchart";
import Header from "../components/layout/Header";
import { Waves } from "../components/ui/wave-background";
import {
  ApiError,
  runAgentDebate,
  getInvestigationWorkspace,
  runAnalyst,
  runClaimCounterpoints,
  runCounterNarratives,
  runNarrativeFamily,
  runReport,
  runReceipts,
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

        if (!nextWorkspace.narrative_family) {
          setIsRunningPipeline(true);
          await runNarrativeFamily(id);
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

        if (!nextWorkspace.receipts) {
          setIsRunningPipeline(true);
          await runReceipts(id);
          nextWorkspace = await getInvestigationWorkspace(id);
          if (cancelled) {
            return;
          }
          startTransition(() => {
            setWorkspace(nextWorkspace);
          });
        }

        if (!nextWorkspace.agent_debate) {
          setIsRunningPipeline(true);
          await runAgentDebate(id);
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
                {workspace.timeline ? <TimelineCard timeline={workspace.timeline} /> : null}
                {workspace.narrative_family ? (
                  <NarrativeFamilyCard
                    family={workspace.narrative_family}
                    documents={workspace.retrieved_documents}
                  />
                ) : null}
                {topClaims.length > 0 ? <ClaimsCard claims={topClaims} /> : null}
              </div>
              <div className="space-y-6">
                {workspace.agent_debate ? (
                  <AgentDebateCard debate={workspace.agent_debate} />
                ) : null}
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
              {claim.support_status ? (
                <span className="data-pill">{claim.support_status.replaceAll("_", " ")}</span>
              ) : null}
              {claim.verification_state ? (
                <span className="data-pill">{claim.verification_state.replaceAll("_", " ")}</span>
              ) : null}
            </div>
            <p className="mt-4 text-base leading-7 text-[var(--ink)]">{claim.claim_text}</p>
            {claim.support_summary ? (
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{claim.support_summary}</p>
            ) : null}
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

function TimelineCard({
  timeline,
}: {
  timeline: NonNullable<LiveInvestigationWorkspace["timeline"]>;
}) {
  return (
    <div className="rounded-[2rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.86)] p-7 shadow-[0_38px_68px_-46px_rgba(19,35,58,0.4)] backdrop-blur-xl sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Timeline</p>
          <p className="mt-4 max-w-3xl text-base leading-7 text-[var(--muted)]">
            {timeline.timeline_summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="data-pill">{timeline.confidence_label} confidence</span>
          <span className="data-pill">{timeline.timeline_events.length} events</span>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {timeline.timeline_events.slice(0, 6).map((event) => (
          <article
            key={event.id}
            className="rounded-[1.35rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-5"
          >
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="data-pill">{event.event_type.replaceAll("_", " ")}</span>
              <span className="data-pill">{event.narrative_side}</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold tracking-[-0.03em] text-[var(--ink)]">
              {event.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              {formatTimestamp(event.timestamp)} · {event.source_name}
            </p>
            <p className="mt-3 text-sm leading-6 text-[var(--ink)]">{event.explanation}</p>
            {event.snippet ? (
              <p className="mt-3 rounded-[1rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(245,247,250,0.9)] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
                {event.snippet}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function NarrativeFamilyCard({
  family,
  documents,
}: {
  family: NonNullable<LiveInvestigationWorkspace["narrative_family"]>;
  documents: LiveInvestigationWorkspace["retrieved_documents"];
}) {
  const documentMap = new Map(documents.map((document) => [document.id, document]));
  const fastest = family.fastest_growing_child;
  const broadest = family.broadest_source_diversity_child;
  const activeBranchId = family.active_branch_id;

  return (
    <div className="rounded-[2rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.86)] p-7 shadow-[0_38px_68px_-46px_rgba(19,35,58,0.4)] backdrop-blur-xl sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Narrative family</p>
          <h2 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-[var(--ink)]">
            {family.family_title}
          </h2>
          <p className="mt-3 text-base leading-7 text-[var(--muted)]">
            {family.summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="data-pill">{family.confidence_label} confidence</span>
          <span className="data-pill">{family.child_narratives.length} branches</span>
          <span className="data-pill">{family.generation_method.replaceAll("_", " ")}</span>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <div className="rounded-[1.4rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-5">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Parent frame
          </p>
          <p className="mt-3 text-lg font-semibold text-[var(--ink)]">{family.parent_frame}</p>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
            RhetoriQ maps semantic framing and mutation patterns in the retrieved corpus.
            It does not treat family placement as proof of coordination or truth.
          </p>
        </div>

        <div className="rounded-[1.4rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Mutation rail
            </p>
            <span className="data-pill">{family.mutation_trail.length} steps</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-[var(--ink)]">
            {family.mutation_summary || "No strong phrase evolution chain was isolated for this branch."}
          </p>
          {family.mutation_trail.length > 0 ? (
            <div className="mt-4 space-y-3">
              {family.mutation_trail.map((step) => {
                const fromDoc = documentMap.get(step.from_doc_id);
                const toDoc = documentMap.get(step.to_doc_id);
                return (
                  <article
                    key={`${step.from_doc_id}-${step.to_doc_id}-${step.from_phrase}-${step.to_phrase}`}
                    className="rounded-[1.1rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(245,247,250,0.94)] p-4"
                  >
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="data-pill">{step.mutation_type.replaceAll("_", " ")}</span>
                      <span className="data-pill">{Math.round(step.similarity_score * 100)}% match</span>
                      <span className="data-pill">{Math.round(step.time_delta_hours)}h later</span>
                      {step.source_shift ? <span className="data-pill">source shift</span> : null}
                    </div>
                    <p className="mt-4 text-base font-semibold leading-7 text-[var(--ink)]">
                      {step.from_phrase} {"->"} {step.to_phrase}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                      {fromDoc ? `${fromDoc.source_name} -> ` : ""}
                      {toDoc ? toDoc.source_name : "later source"}
                    </p>
                    <p className="mt-3 text-sm leading-6 text-[var(--ink)]">{step.explanation}</p>
                  </article>
                );
              })}
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Branches
          </p>
          {activeBranchId ? <span className="data-pill">active branch highlighted</span> : null}
        </div>

        <div className="mt-4 space-y-4">
          {family.child_narratives.map((child) => {
            const firstObservedDoc = child.first_observed_doc_id
              ? documentMap.get(child.first_observed_doc_id)
              : null;
            const isActive = child.id === activeBranchId;
            return (
              <article
                key={child.id}
                className={`rounded-[1.35rem] border bg-white/92 p-5 ${
                  isActive
                    ? "border-[rgba(160,106,46,0.32)] shadow-[0_24px_44px_-34px_rgba(160,106,46,0.34)]"
                    : "border-[rgba(19,35,58,0.08)]"
                }`}
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="data-pill">{describeBranchType(child.branch_type)}</span>
                  <span className="data-pill">{child.growth_status}</span>
                  {isActive ? <span className="data-pill">active branch</span> : null}
                  {child.id === fastest ? <span className="data-pill">fastest growing</span> : null}
                  {child.id === broadest ? <span className="data-pill">broadest sources</span> : null}
                </div>
                <h3 className="mt-4 text-lg font-semibold tracking-[-0.03em] text-[var(--ink)]">
                  {child.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  {child.relationship_to_parent}
                </p>
                <p className="mt-3 text-sm leading-6 text-[var(--ink)]">{child.branch_summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="data-pill">{child.source_count} sources</span>
                  <span className="data-pill">{child.source_type_count} source types</span>
                  {firstObservedDoc ? (
                    <span className="data-pill">
                      first observed: {firstObservedDoc.source_name}
                    </span>
                  ) : null}
                </div>
                {child.related_phrases.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {child.related_phrases.map((phrase) => (
                      <span
                        key={`${child.id}-${phrase}`}
                        className="rounded-full border border-[rgba(19,35,58,0.08)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]"
                      >
                        {phrase}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function AgentDebateCard({
  debate,
}: {
  debate: NonNullable<LiveInvestigationWorkspace["agent_debate"]>;
}) {
  return (
    <div className="rounded-[1.7rem] border border-[rgba(19,35,58,0.08)] bg-[rgba(255,255,255,0.88)] p-5 shadow-[0_24px_44px_-34px_rgba(19,35,58,0.34)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
          Agent debate
        </p>
        <span className="data-pill">{debate.confidence_label} confidence</span>
      </div>

      <div className="mt-4 space-y-4">
        <DebateBlock title="Analyst Agent" value={debate.analyst_position} />
        <DebateBlock title="Skeptic Summary" value={debate.skeptic_response} />
        <DebateBlock title="Receipts Check" value={debate.receipts_check} />
        <DebateBlock title="Counter-Narrative Note" value={debate.counter_narrative_note} />
        <DebateBlock title="Safety / Grounding" value={debate.safety_grounding_decision} />
        <DebateBlock title="Final Language Decision" value={debate.final_language_decision} />

        {debate.rejected_claims.length > 0 ? (
          <div className="rounded-[1.1rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Rejected claims
            </p>
            <div className="mt-3 space-y-2">
              {debate.rejected_claims.map((item) => (
                <p key={item} className="text-sm leading-6 text-[var(--ink)]">
                  {item}
                </p>
              ))}
            </div>
          </div>
        ) : null}

        {debate.softened_claims.length > 0 ? (
          <div className="rounded-[1.1rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Softened claims
            </p>
            <div className="mt-3 space-y-3">
              {debate.softened_claims.map((item) => (
                <div key={item.claim_id} className="rounded-[0.95rem] bg-[rgba(245,247,250,0.9)] p-3">
                  <p className="text-sm font-semibold text-[var(--ink)]">{item.original}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{item.softened}</p>
                  <p className="mt-2 text-xs uppercase tracking-[0.12em] text-[var(--muted)]">
                    {item.reason}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function DebateBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-[1.1rem] border border-[rgba(19,35,58,0.08)] bg-white/92 p-4">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {title}
      </p>
      <p className="mt-3 text-sm leading-7 text-[var(--ink)]">{value}</p>
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

function describeBranchType(value: "main" | "counter" | "related" | "mutation") {
  return value.replaceAll("_", " ");
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
