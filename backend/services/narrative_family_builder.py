from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone

from models.document import Document
from models.investigation import (
    CounterNarrativeResult,
    InvestigationPlan,
    NarrativeFamilyChild,
    NarrativeFamilyResult,
    RetrievalResult,
    TimelineResult,
)

_GENERIC_PHRASE_WORDS = {
    "breaking",
    "claim",
    "cost",
    "coverage",
    "debate",
    "frame",
    "framing",
    "issue",
    "narrative",
    "policy",
    "story",
    "talking",
}


def build_narrative_family(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
) -> NarrativeFamilyResult:
    docs_by_id = {document.id: document for document in documents}
    all_documents = list(docs_by_id.values())
    child_branches: list[NarrativeFamilyChild] = []
    limitations = [
        "Narrative family relationships are semantic groupings derived from the retrieved corpus, not proof of coordination.",
    ]

    main_branch = _build_main_branch(plan, retrieval, docs_by_id, all_documents)
    if main_branch is not None:
        child_branches.append(main_branch)

    child_branches.extend(
        _build_counter_branches(counter_narratives, docs_by_id, all_documents)
    )
    child_branches.extend(
        _build_related_phrase_branches(
            plan,
            retrieval,
            all_documents,
            existing_phrases={branch.canonical_phrase.lower() for branch in child_branches},
        )
    )

    child_branches = _dedupe_children(child_branches)
    child_branches.sort(
        key=lambda branch: (
            -branch.growth_score,
            -branch.source_diversity_score,
            branch.title.lower(),
        )
    )

    if len(child_branches) <= 1:
        limitations.append(
            "Only a narrow set of related branches could be established from the current retrieved evidence packet."
        )
    if not counter_narratives.counter_narratives:
        limitations.append(
            "No counter-frame branches were available, so the family tree may underrepresent contested framing."
        )
    if timeline.first_observed_doc_id is None:
        limitations.append(
            "Family chronology confidence is limited because the retrieved timeline did not establish a clear first-observed document."
        )

    fastest_child = max(child_branches, key=lambda branch: branch.growth_score, default=None)
    broadest_child = max(
        child_branches,
        key=lambda branch: branch.source_diversity_score,
        default=None,
    )
    confidence_score = _family_confidence(all_documents, child_branches, counter_narratives)

    return NarrativeFamilyResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        family_title=f"{(plan.canonical_phrase or plan.topic).title()} Narrative Family",
        parent_frame=_parent_frame(plan, child_branches),
        summary=_family_summary(plan, child_branches, fastest_child, broadest_child),
        child_narratives=child_branches,
        fastest_growing_child=fastest_child.id if fastest_child else None,
        broadest_source_diversity_child=broadest_child.id if broadest_child else None,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=_confidence_label(confidence_score),
    )


def _build_main_branch(
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    docs_by_id: dict[str, Document],
    all_documents: list[Document],
) -> NarrativeFamilyChild | None:
    preferred_ids = [
        *retrieval.main_narrative_document_ids,
        *retrieval.high_relevance_document_ids,
        *retrieval.retrieved_document_ids,
    ]
    branch_docs = [
        docs_by_id[doc_id]
        for doc_id in dict.fromkeys(preferred_ids)
        if doc_id in docs_by_id
    ]
    if not branch_docs:
        return None

    canonical_phrase = (plan.canonical_phrase or plan.topic).strip() or "main narrative"
    return _build_branch(
        branch_id="family_main",
        title=f"{canonical_phrase.title()} Main Branch",
        canonical_phrase=canonical_phrase,
        related_phrases=_top_related_phrases(branch_docs, exclude={canonical_phrase.lower()}),
        relationship_to_parent="Primary branch of the investigated narrative in the retrieved corpus.",
        documents=branch_docs,
        all_documents=all_documents,
    )


def _build_counter_branches(
    counter_narratives: CounterNarrativeResult,
    docs_by_id: dict[str, Document],
    all_documents: list[Document],
) -> list[NarrativeFamilyChild]:
    children: list[NarrativeFamilyChild] = []
    for index, counter in enumerate(counter_narratives.counter_narratives, start=1):
        branch_docs = [
            docs_by_id[doc_id]
            for doc_id in counter.supporting_document_ids
            if doc_id in docs_by_id
        ]
        if not branch_docs:
            continue
        canonical_phrase = (counter.canonical_phrase or counter.title).strip()
        children.append(
            _build_branch(
                branch_id=f"family_counter_{index}",
                title=counter.title,
                canonical_phrase=canonical_phrase,
                related_phrases=counter.related_phrases,
                relationship_to_parent=counter.relationship_to_main_narrative.replace("_", " "),
                documents=branch_docs,
                all_documents=all_documents,
            )
        )
    return children


def _build_related_phrase_branches(
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    *,
    existing_phrases: set[str],
) -> list[NarrativeFamilyChild]:
    grouped: dict[str, list[Document]] = defaultdict(list)
    for document in documents:
        for phrase in document.phrases:
            normalized = phrase.strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in existing_phrases:
                continue
            if lowered == (plan.canonical_phrase or plan.topic).strip().lower():
                continue
            if not _is_branch_phrase(normalized):
                continue
            grouped[normalized].append(document)

    ranked_groups = sorted(
        grouped.items(),
        key=lambda item: (
            -len({doc.id for doc in item[1]}),
            -len({doc.source_name for doc in item[1]}),
            item[0].lower(),
        ),
    )

    main_doc_ids = set(retrieval.main_narrative_document_ids)
    children: list[NarrativeFamilyChild] = []
    for index, (phrase, phrase_docs) in enumerate(ranked_groups, start=1):
        unique_docs = list({doc.id: doc for doc in phrase_docs}.values())
        unique_sources = {doc.source_name for doc in unique_docs}
        if len(unique_docs) < 2 and len(unique_sources) < 2:
            continue
        relationship = (
            "Phrase branch adjacent to the main narrative."
            if any(doc.id in main_doc_ids for doc in unique_docs)
            else "Related branch connected by recurring phrase reuse in the retrieved corpus."
        )
        children.append(
            _build_branch(
                branch_id=f"family_related_{index}",
                title=f"{phrase.title()} Related Branch",
                canonical_phrase=phrase,
                related_phrases=_top_related_phrases(
                    unique_docs,
                    exclude={phrase.lower(), (plan.canonical_phrase or "").lower()},
                ),
                relationship_to_parent=relationship,
                documents=unique_docs,
                all_documents=documents,
            )
        )
        if len(children) >= 3:
            break
    return children


def _build_branch(
    *,
    branch_id: str,
    title: str,
    canonical_phrase: str,
    related_phrases: list[str],
    relationship_to_parent: str,
    documents: list[Document],
    all_documents: list[Document],
) -> NarrativeFamilyChild:
    ordered = sorted(
        documents,
        key=lambda document: document.published_at or datetime.max.replace(tzinfo=timezone.utc),
    )
    first_document = next((document for document in ordered if document.published_at is not None), ordered[0] if ordered else None)
    source_count = len({document.source_name for document in documents})
    source_type_count = len({document.source_type for document in documents})
    source_diversity_score = _source_diversity_score(documents, all_documents)
    growth_score = _growth_score(documents, all_documents)
    growth_status = _growth_status(documents, all_documents, growth_score)

    return NarrativeFamilyChild(
        id=branch_id,
        title=title,
        canonical_phrase=canonical_phrase,
        related_phrases=related_phrases[:6],
        first_observed_doc_id=first_document.id if first_document else None,
        relationship_to_parent=relationship_to_parent,
        growth_status=growth_status,
        branch_summary=_branch_summary(canonical_phrase, documents, growth_status, relationship_to_parent),
        supporting_document_ids=[document.id for document in ordered],
        source_count=source_count,
        source_type_count=source_type_count,
        source_diversity_score=source_diversity_score,
        growth_score=growth_score,
    )


def _branch_summary(
    canonical_phrase: str,
    documents: list[Document],
    growth_status: str,
    relationship_to_parent: str,
) -> str:
    source_count = len({document.source_name for document in documents})
    return (
        f"'{canonical_phrase}' appears across {len(documents)} retrieved document(s) from "
        f"{source_count} source(s). It is currently classified as {growth_status.replace('_', ' ')} "
        f"and is grouped here because it {relationship_to_parent.lower().rstrip('.') }."
    )


def _top_related_phrases(documents: list[Document], *, exclude: set[str]) -> list[str]:
    phrases: list[str] = []
    seen: set[str] = set()
    for document in documents:
        for phrase in document.phrases:
            normalized = phrase.strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in exclude or lowered in seen:
                continue
            seen.add(lowered)
            phrases.append(normalized)
    return phrases[:6]


def _is_branch_phrase(value: str) -> bool:
    words = [word for word in re.findall(r"[a-z0-9']+", value.lower()) if len(word) > 2]
    if len(words) < 2:
        return False
    if all(word in _GENERIC_PHRASE_WORDS for word in words):
        return False
    return True


def _source_diversity_score(documents: list[Document], all_documents: list[Document]) -> float:
    if not documents or not all_documents:
        return 0.0
    source_count = len({document.source_name for document in documents})
    source_type_count = len({document.source_type for document in documents})
    total_sources = max(1, len({document.source_name for document in all_documents}))
    total_types = max(1, len({document.source_type for document in all_documents}))
    score = source_count / total_sources * 0.65 + source_type_count / total_types * 0.35
    return round(min(score, 1.0), 3)


def _growth_score(documents: list[Document], all_documents: list[Document]) -> float:
    if not documents or not all_documents:
        return 0.0

    document_fraction = len(documents) / max(1, len(all_documents))
    source_fraction = len({document.source_name for document in documents}) / max(
        1,
        len({document.source_name for document in all_documents}),
    )
    latest_corpus_time = max(
        (document.published_at for document in all_documents if document.published_at is not None),
        default=None,
    )
    latest_branch_time = max(
        (document.published_at for document in documents if document.published_at is not None),
        default=None,
    )
    recency_score = 0.2
    if latest_corpus_time is not None and latest_branch_time is not None:
        age_hours = max(0.0, (latest_corpus_time - latest_branch_time).total_seconds() / 3600)
        recency_score = max(0.05, 0.2 - min(0.15, age_hours / 240))

    score = 0.45 * document_fraction + 0.35 * source_fraction + recency_score
    return round(min(score, 1.0), 3)


def _growth_status(
    documents: list[Document],
    all_documents: list[Document],
    growth_score: float,
) -> str:
    if not documents:
        return "unknown"

    latest_corpus_time = max(
        (document.published_at for document in all_documents if document.published_at is not None),
        default=None,
    )
    latest_branch_time = max(
        (document.published_at for document in documents if document.published_at is not None),
        default=None,
    )
    if latest_corpus_time is not None and latest_branch_time is not None:
        age_hours = (latest_corpus_time - latest_branch_time).total_seconds() / 3600
        if age_hours >= 96 and growth_score < 0.35:
            return "declining"

    source_count = len({document.source_name for document in documents})
    if len(documents) >= 4 and source_count >= 3:
        return "mainstreaming"
    if len(documents) >= 2 and source_count >= 2:
        return "amplifying"
    return "emerging"


def _parent_frame(plan: InvestigationPlan, child_branches: list[NarrativeFamilyChild]) -> str:
    if child_branches:
        anchor = child_branches[0].canonical_phrase
        return f"Broader framing around {anchor}"
    return f"Broader framing around {plan.canonical_phrase or plan.topic}"


def _family_summary(
    plan: InvestigationPlan,
    child_branches: list[NarrativeFamilyChild],
    fastest_child: NarrativeFamilyChild | None,
    broadest_child: NarrativeFamilyChild | None,
) -> str:
    if not child_branches:
        return (
            f"The retrieved corpus did not contain enough distinct branches to build a strong family tree for "
            f"{plan.canonical_phrase or plan.topic}."
        )

    parts = [
        f"The family tree groups {len(child_branches)} related branch(es) around {plan.canonical_phrase or plan.topic}.",
    ]
    if fastest_child is not None:
        parts.append(f"The fastest-growing branch in the current corpus is '{fastest_child.title}'.")
    if broadest_child is not None:
        parts.append(
            f"The broadest source mix appears under '{broadest_child.title}'."
        )
    return " ".join(parts)


def _family_confidence(
    documents: list[Document],
    child_branches: list[NarrativeFamilyChild],
    counter_narratives: CounterNarrativeResult,
) -> float:
    if not documents:
        return 0.18
    score = 0.24
    score += min(0.2, len(child_branches) * 0.08)
    score += min(0.18, len({document.source_name for document in documents}) * 0.03)
    score += min(0.12, len({document.source_type for document in documents}) * 0.03)
    if counter_narratives.counter_narratives:
        score += 0.08
    return round(min(score, 0.91), 3)


def _confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.46:
        return "medium"
    return "low"


def _dedupe_children(children: list[NarrativeFamilyChild]) -> list[NarrativeFamilyChild]:
    output: list[NarrativeFamilyChild] = []
    seen: set[str] = set()
    for child in children:
        key = child.canonical_phrase.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(child)
    return output
