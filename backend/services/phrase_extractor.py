"""
Cross-document n-gram phrase extractor.

Pure-Python — no sklearn dependency.
Returns top phrases by document frequency: how many distinct docs contain the phrase,
not just how many total times it appeared. Document frequency is a better signal for
"multiple sources are talking about this thing" vs. one source repeating a phrase.
"""

import re
from collections import defaultdict

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "it", "its",
    "this", "that", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "he", "his", "she", "her", "they", "their", "them",
    "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "more", "most", "other", "some",
    "such", "no", "not", "only", "same", "so", "than", "too", "very",
    "just", "as", "if", "up", "out", "about", "after", "before", "into",
    "over", "under", "again", "then", "here", "there", "also", "new",
    "one", "two", "says", "said", "say", "according", "amid", "via",
    "per", "report", "reports", "update", "updates", "amid", "amid",
    "around", "today",
}
_GENERIC_NEWS_TERMS = {
    "analysis", "article", "articles", "breaking", "coverage", "debate",
    "debates", "housing", "implications", "industry", "latest", "live",
    "market", "narrative", "narratives", "news", "official", "opinion",
    "policy", "political", "politics", "public", "reaction", "research",
    "review", "statement", "story", "stories", "topic", "topics", "update",
    "updates", "world", "counter",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\b[a-z][a-z'\-]{1,}\b", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]


def _is_publishable_phrase(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    if len(set(tokens)) == 1:
        return False
    return any(token not in _GENERIC_NEWS_TERMS for token in tokens)


def extract_top_phrases(
    texts: list[str],
    ngram_range: tuple[int, int] = (2, 4),
    top_n: int = 100,
    min_doc_freq: int = 2,
) -> list[tuple[str, int]]:
    """
    Returns [(phrase, doc_freq)] sorted by doc_freq descending.

    phrase    — the n-gram string
    doc_freq  — number of distinct documents containing the phrase

    Only phrases appearing in >= min_doc_freq distinct documents are returned.
    """
    phrase_doc_sets: dict[str, set[int]] = defaultdict(set)
    min_n, max_n = ngram_range

    for doc_idx, text in enumerate(texts):
        tokens = _tokenize(text)
        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                gram_tokens = tokens[i : i + n]
                if not _is_publishable_phrase(gram_tokens):
                    continue
                gram = " ".join(gram_tokens)
                phrase_doc_sets[gram].add(doc_idx)

    ranked = [
        (phrase, len(doc_idxs))
        for phrase, doc_idxs in phrase_doc_sets.items()
        if len(doc_idxs) >= min_doc_freq
    ]
    ranked.sort(key=lambda x: (x[1], len(x[0].split()), len(x[0])), reverse=True)
    return ranked[:top_n]
