from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Thread
from uuid import uuid4

from agents.discovery_agent import DiscoveryAgent
from agents.model_client import MockModelClient
from agents.planner_agent import plan_investigation
from config import get_settings
from models.trending import (
    DiscoveryRunStats,
    PublishedTrendingSnapshot,
    TrendingFeedResponse,
    TrendingInvestigationResponse,
    TrendingStatusResponse,
)
from services.redis_store import PhraseStore
from services.search_provider import source_name_from_url
from services.trending_ranker import TrendingRanker
from services.trending_repository import TrendingRepository
from services.trending_runtime import TrendingRuntimeStore


class TrendingService:
    def __init__(
        self,
        *,
        repository: TrendingRepository,
        runtime_store: TrendingRuntimeStore,
        discovery_agent: DiscoveryAgent | None = None,
    ) -> None:
        self._settings = get_settings()
        self._repository = repository
        self._runtime = runtime_store
        self._discovery = discovery_agent or DiscoveryAgent()
        self._ranker = TrendingRanker(
            min_docs=self._settings.TRENDING_MIN_DOCS,
            min_publishers=self._settings.TRENDING_MIN_PUBLISHERS,
            min_source_types=self._settings.TRENDING_MIN_SOURCE_TYPES,
        )
        self._phrase_store = PhraseStore(redis_url=self._settings.REDIS_URL)

    def ensure_warm_async(self) -> None:
        snapshot = self._repository.get_latest_snapshot()
        if snapshot is not None:
            return
        if not self._runtime.acquire_refresh_lock():
            return
        thread = Thread(target=self._run_refresh_thread, kwargs={"is_reseed": True}, daemon=True)
        thread.start()

    def get_feed(self, *, limit: int = 10) -> TrendingFeedResponse:
        now = datetime.now(timezone.utc)
        snapshot = self._repository.get_latest_snapshot()
        last_error = self._runtime.get_last_error()

        if snapshot is None:
            triggered = self._schedule_refresh_if_possible(is_reseed=True)
            warning = "Discovery pipeline is warming up."
            if not triggered and not self._runtime.redis_available:
                warning = "Redis unavailable and no live snapshot is ready yet."
            return TrendingFeedResponse(
                state="warming" if triggered else "error",
                warning=warning if last_error is None else f"{warning} Last error: {last_error}",
                topics=[],
            )

        if snapshot.fresh_until >= now:
            return TrendingFeedResponse(
                state="ready",
                generated_at=snapshot.generated_at,
                fresh_until=snapshot.fresh_until,
                last_completed_run_at=snapshot.last_completed_run_at,
                last_reseed_at=snapshot.last_reseed_at,
                warning=self._snapshot_warning(snapshot, last_error),
                topics=snapshot.topics[:limit],
            )

        triggered = self._schedule_refresh_if_possible(is_reseed=self._needs_reseed(snapshot, now))
        return TrendingFeedResponse(
            state="warming" if triggered else "stale",
            generated_at=snapshot.generated_at,
            fresh_until=snapshot.fresh_until,
            last_completed_run_at=snapshot.last_completed_run_at,
            last_reseed_at=snapshot.last_reseed_at,
            warning=self._snapshot_warning(
                snapshot,
                last_error or "Trending snapshot is stale and a refresh is pending.",
            ),
            topics=[],
        )

    def get_status(self) -> TrendingStatusResponse:
        snapshot = self._repository.get_latest_snapshot()
        feed = self.get_feed(limit=1)
        return TrendingStatusResponse(
            state=feed.state,
            redis_available=self._runtime.redis_available,
            refresh_lock_active=self._runtime.refresh_lock_active(),
            generated_at=snapshot.generated_at if snapshot else None,
            fresh_until=snapshot.fresh_until if snapshot else None,
            last_completed_run_at=snapshot.last_completed_run_at if snapshot else None,
            last_reseed_at=snapshot.last_reseed_at if snapshot else None,
            last_error=self._runtime.get_last_error(),
            latest_snapshot_id=snapshot.snapshot_id if snapshot else None,
        )

    def refresh_now(self, *, is_reseed: bool = False) -> PublishedTrendingSnapshot:
        return self._refresh(is_reseed=is_reseed)

    def start_investigation_for_topic(
        self,
        topic_id: str,
        investigation_repository,
    ) -> TrendingInvestigationResponse:
        snapshot = self._repository.get_latest_snapshot()
        if snapshot is None:
            raise ValueError("No published trending snapshot is available.")
        topic = next((candidate for candidate in snapshot.topics if candidate.id == topic_id), None)
        if topic is None:
            raise ValueError(f"Trending topic '{topic_id}' not found.")

        ttl_seconds = int(timedelta(hours=self._settings.TRENDING_REFRESH_HOURS).total_seconds())
        cached = self._runtime.get_topic_investigation(topic_id)
        if cached and investigation_repository.investigation_exists(cached):
            return TrendingInvestigationResponse(
                investigation_id=cached,
                reused_existing=True,
                topic_id=topic.id,
                canonical_phrase=topic.canonical_phrase,
            )

        plan = plan_investigation(
            f"Trace the narrative around {topic.canonical_phrase}",
            prior_context={
                "canonical_phrase": topic.canonical_phrase,
                "topic_id": topic.id,
                "related_phrases": topic.related_phrases,
            },
            model_client=MockModelClient(),
        )
        investigation_id = f"inv_{uuid4().hex}"
        investigation_repository.save_plan(investigation_id, plan.query_text, plan)
        self._runtime.set_topic_investigation(topic_id, investigation_id, ttl_seconds=ttl_seconds)
        return TrendingInvestigationResponse(
            investigation_id=investigation_id,
            reused_existing=False,
            topic_id=topic.id,
            canonical_phrase=topic.canonical_phrase,
        )

    def _schedule_refresh_if_possible(self, *, is_reseed: bool) -> bool:
        if not self._runtime.acquire_refresh_lock():
            return False
        thread = Thread(target=self._run_refresh_thread, kwargs={"is_reseed": is_reseed}, daemon=True)
        thread.start()
        return True

    def _run_refresh_thread(self, *, is_reseed: bool) -> None:
        try:
            self._refresh(is_reseed=is_reseed)
        finally:
            self._runtime.release_refresh_lock()

    def _refresh(self, *, is_reseed: bool) -> PublishedTrendingSnapshot:
        run_id = f"disc_{uuid4().hex}"
        prior_topics = []
        previous = self._repository.get_latest_snapshot()
        if previous is not None:
            prior_topics = [topic.canonical_phrase for topic in previous.topics[:6]]
        queries = self._discovery.build_queries(prior_topics=prior_topics, is_reseed=is_reseed)
        self._repository.create_run(run_id, is_reseed=is_reseed, queries=queries)
        try:
            batch = self._discovery.discover(prior_topics=prior_topics, is_reseed=is_reseed)
        except Exception as exc:
            self._repository.complete_run(
                run_id,
                stats=self._empty_stats(query_count=len(queries)),
                warnings=[],
                error=str(exc),
            )
            self._runtime.set_last_error(str(exc))
            raise

        accepted = 0
        duplicates = 0
        for candidate in batch.candidates:
            document = self._discovery.normalize_candidate(candidate)
            document.source_name = candidate.search_result.metadata.get("source_name_hint") or source_name_from_url(document.url)
            record, created = self._repository.save_discovery_document(
                run_id,
                document,
                canonical_url=self._normalize_url(document.url),
                domain=source_name_from_url(document.url),
                provider=candidate.search_result.provider,
                search_query=candidate.search_result.query,
            )
            if created:
                accepted += 1
            else:
                duplicates += 1

        stats = batch.stats.model_copy(
            update={
                "accepted_documents": accepted,
                "duplicate_documents": duplicates + batch.stats.duplicate_documents,
            }
        )
        documents = self._repository.list_discovery_documents()

        # Record each document's phrases in the Redis phrase counter so spike scores
        # are backed by real Redis sorted sets instead of in-memory dicts.
        now_ts = datetime.now(timezone.utc)
        for rec in documents:
            doc = rec.document
            ts = doc.published_at or rec.latest_seen_at or now_ts
            for phrase in doc.phrases or []:
                if phrase:
                    self._phrase_store.record_phrase(phrase, ts, doc.id)

        topics = self._ranker.rank(documents, max_topics=self._settings.TRENDING_MAX_TOPICS)
        now = datetime.now(timezone.utc)
        snapshot = PublishedTrendingSnapshot(
            snapshot_id=f"snap_{uuid4().hex}",
            state="ready" if topics else "warming",
            generated_at=now,
            fresh_until=now + timedelta(hours=self._settings.TRENDING_REFRESH_HOURS),
            last_completed_run_at=now,
            last_reseed_at=now if is_reseed else (previous.last_reseed_at if previous else None),
            warning=None if topics else "Discovery run completed but no topics cleared the publish thresholds yet.",
            topics=topics,
        )
        self._repository.complete_run(run_id, stats=stats, warnings=batch.warnings)
        self._repository.save_snapshot(snapshot)
        self._runtime.set_last_error(None)
        return snapshot

    def _needs_reseed(self, snapshot: PublishedTrendingSnapshot, now: datetime) -> bool:
        if snapshot.last_reseed_at is None:
            return True
        return snapshot.last_reseed_at <= now - timedelta(hours=self._settings.TRENDING_RESEED_HOURS)

    def _normalize_url(self, url: str) -> str:
        return url.strip().rstrip("/").lower()

    def _snapshot_warning(
        self,
        snapshot: PublishedTrendingSnapshot,
        last_error: str | None,
    ) -> str | None:
        if snapshot.warning and last_error:
            return f"{snapshot.warning} Last error: {last_error}"
        return snapshot.warning or last_error

    def _empty_stats(self, *, query_count: int):
        return DiscoveryRunStats(query_count=query_count)
