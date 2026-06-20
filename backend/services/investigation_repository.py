from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from models.document import Document
from models.investigation import (
    AnalystResult,
    CounterNarrativeResult,
    FinalReportResult,
    InvestigationPlan,
    InvestigationWorkspace,
    RetrievalResult,
    SourceDiversityResult,
    TimelineResult,
)


class InvestigationRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_parent_dir()
        self._init_schema()

    def save_plan(self, investigation_id: str, query_text: str, plan: InvestigationPlan) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO investigations (
                    investigation_id, query_text, status, current_stage, plan_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    query_text=excluded.query_text,
                    status=excluded.status,
                    current_stage=excluded.current_stage,
                    plan_json=excluded.plan_json,
                    updated_at=excluded.updated_at
                """,
                (
                    investigation_id,
                    query_text,
                    "planning_completed",
                    "planner",
                    plan.model_dump_json(),
                    now,
                    now,
                ),
            )

    def get_plan(self, investigation_id: str) -> InvestigationPlan | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT plan_json FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row or not row["plan_json"]:
            return None
        return InvestigationPlan.model_validate_json(row["plan_json"])

    def investigation_exists(self, investigation_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        return row is not None

    def get_investigation_workspace(
        self,
        investigation_id: str,
    ) -> InvestigationWorkspace | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT investigation_id, query_text, status, current_stage, created_at, updated_at
                FROM investigations
                WHERE investigation_id = ?
                """,
                (investigation_id,),
            ).fetchone()

        if not row:
            return None

        return InvestigationWorkspace(
            investigation_id=row["investigation_id"],
            query_text=row["query_text"],
            status=row["status"],
            current_stage=row["current_stage"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            plan=self.get_plan(investigation_id),
            retrieval=self.get_retrieval_result(investigation_id),
            retrieved_documents=self.get_retrieved_documents(investigation_id),
            source_diversity=self.get_source_diversity_result(investigation_id),
            timeline=self.get_timeline_result(investigation_id),
            counter_narratives=self.get_counter_narrative_result(investigation_id),
            analyst=self.get_analyst_result(investigation_id),
            report=self.get_final_report_result(investigation_id),
        )

    def save_retrieval_result(self, result: RetrievalResult, documents: list[Document]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("retrieval_completed", "retriever", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO retrieval_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )
            conn.execute(
                "DELETE FROM retrieved_documents WHERE investigation_id = ?",
                (result.investigation_id,),
            )
            conn.execute(
                "DELETE FROM retrieval_rounds WHERE investigation_id = ?",
                (result.investigation_id,),
            )
            conn.execute(
                "DELETE FROM duplicate_candidates WHERE investigation_id = ?",
                (result.investigation_id,),
            )
            conn.execute(
                "DELETE FROM search_results WHERE investigation_id = ?",
                (result.investigation_id,),
            )
            for doc in documents:
                conn.execute(
                    """
                    INSERT INTO retrieved_documents (investigation_id, doc_id, document_json, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (result.investigation_id, doc.id, doc.model_dump_json(), now),
                )
            for retrieval_round in result.search_rounds:
                conn.execute(
                    """
                    INSERT INTO retrieval_rounds (investigation_id, round_number, round_json, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        result.investigation_id,
                        retrieval_round.round_number,
                        retrieval_round.model_dump_json(),
                        now,
                    ),
                )
            for duplicate in result.possible_duplicate_pairs:
                conn.execute(
                    """
                    INSERT INTO duplicate_candidates (
                        investigation_id, left_doc_id, right_doc_id, duplicate_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        result.investigation_id,
                        duplicate.left_doc_id,
                        duplicate.right_doc_id,
                        duplicate.model_dump_json(),
                        now,
                    ),
                )

    def save_search_results(self, investigation_id: str, round_number: int, results: list[dict]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            for result in results:
                conn.execute(
                    """
                    INSERT INTO search_results (investigation_id, round_number, url, result_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(investigation_id, round_number, url) DO UPDATE SET
                        result_json=excluded.result_json
                    """,
                    (
                        investigation_id,
                        round_number,
                        result["url"],
                        json.dumps(result),
                        now,
                    ),
                )

    def get_retrieval_result(self, investigation_id: str) -> RetrievalResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM retrieval_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return RetrievalResult.model_validate_json(row["result_json"])

    def get_retrieved_documents(self, investigation_id: str) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT document_json
                FROM retrieved_documents
                WHERE investigation_id = ?
                ORDER BY doc_id
                """,
                (investigation_id,),
            ).fetchall()
        return [Document.model_validate_json(row["document_json"]) for row in rows]

    def save_timeline_result(self, result: TimelineResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("timeline_completed", "timeline", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO timeline_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )

    def get_timeline_result(self, investigation_id: str) -> TimelineResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM timeline_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return TimelineResult.model_validate_json(row["result_json"])

    def save_source_diversity_result(self, result: SourceDiversityResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("source_diversity_completed", "source_diversity", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO source_diversity_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )

    def get_source_diversity_result(self, investigation_id: str) -> SourceDiversityResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM source_diversity_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return SourceDiversityResult.model_validate_json(row["result_json"])

    def save_counter_narrative_result(self, result: CounterNarrativeResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("counter_narrative_completed", "counter_narrative", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO counter_narrative_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )

    def get_counter_narrative_result(self, investigation_id: str) -> CounterNarrativeResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM counter_narrative_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return CounterNarrativeResult.model_validate_json(row["result_json"])

    def save_analyst_result(self, result: AnalystResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("analyst_completed", "analyst", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO analyst_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )

    def get_analyst_result(self, investigation_id: str) -> AnalystResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM analyst_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return AnalystResult.model_validate_json(row["result_json"])

    def save_final_report_result(self, result: FinalReportResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, current_stage = ?, updated_at = ?
                WHERE investigation_id = ?
                """,
                ("report_completed", "report", now, result.investigation_id),
            )
            conn.execute(
                """
                INSERT INTO final_report_results (investigation_id, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(investigation_id) DO UPDATE SET
                    result_json=excluded.result_json,
                    updated_at=excluded.updated_at
                """,
                (result.investigation_id, result.model_dump_json(), now, now),
            )

    def get_final_report_result(self, investigation_id: str) -> FinalReportResult | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM final_report_results WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if not row:
            return None
        return FinalReportResult.model_validate_json(row["result_json"])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_parent_dir(self) -> None:
        if self._db_path == ":memory:":
            return
        parent = os.path.dirname(self._db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS investigations (
                    investigation_id TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    plan_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS retrieval_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS retrieved_documents (
                    investigation_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    document_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (investigation_id, doc_id)
                );

                CREATE TABLE IF NOT EXISTS retrieval_rounds (
                    investigation_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    round_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (investigation_id, round_number)
                );

                CREATE TABLE IF NOT EXISTS duplicate_candidates (
                    investigation_id TEXT NOT NULL,
                    left_doc_id TEXT NOT NULL,
                    right_doc_id TEXT NOT NULL,
                    duplicate_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (investigation_id, left_doc_id, right_doc_id)
                );

                CREATE TABLE IF NOT EXISTS search_results (
                    investigation_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (investigation_id, round_number, url)
                );

                CREATE TABLE IF NOT EXISTS timeline_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_diversity_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS counter_narrative_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS analyst_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS final_report_results (
                    investigation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
