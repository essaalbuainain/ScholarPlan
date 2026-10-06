from __future__ import annotations
import html
import re
from typing import Dict, Any, Set

_GENERIC_STOPWORDS = {
    "what", "which", "who", "how", "why", "when", "where", "the", "a", "an",
    "and", "or", "of", "to", "in", "on", "for", "with", "from", "by", "as",
    "is", "are", "was", "were", "be", "been", "being", "this", "that", "these",
    "those", "can", "could", "should", "would", "may", "might", "do", "does", "did",
    "into", "through", "using", "use", "used", "based", "relevant", "scholarly",
    "research", "academic", "evidence", "define", "scope", "key", "concept", "concepts",
    "retrieve", "compare", "finding", "findings", "limitation", "limitations", "implication",
    "implications", "investigate", "additional", "synthesise", "synthesize"
}

_GENERIC_RESEARCH_TERMS = {
    "technique", "techniques", "reduce", "reducing", "mitigation", "mitigate",
    "method", "methods", "approach", "approaches", "study", "studies"
}


def _normalise_tokens(text: str) -> Set[str]:
    text = html.unescape(text or "").lower()
    text = text.replace("large language models", "llm").replace("large language model", "llm")
    tokens = []
    for token in re.findall(r"[a-z0-9]+", text):
        if len(token) <= 1 or token in _GENERIC_STOPWORDS:
            continue
        if token == "llms":
            token = "llm"
        elif token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("s") and len(token) > 3:
            token = token[:-1]
        tokens.append(token)
    return set(tokens)


def relevance_score(query: str, title: str, abstract: str = "") -> float:
    """
    Transparent lexical relevance score used before the Retriever's top-k cut.

    It rewards overlap with the user's domain terms in the title/abstract and
    suppresses records that only match generic research words. This is intended
    as a lightweight, auditable baseline; Sentence-BERT remains future work.
    """
    query_tokens = _normalise_tokens(query)
    if not query_tokens:
        return 0.0

    title_tokens = _normalise_tokens(title)
    abstract_tokens = _normalise_tokens(abstract)
    domain_tokens = query_tokens - _GENERIC_RESEARCH_TERMS
    anchor_matches = domain_tokens & (title_tokens | abstract_tokens)

    # If the query contains domain-specific terms, require at least one of them.
    if domain_tokens and not anchor_matches:
        return 0.0

    title_coverage = len(query_tokens & title_tokens) / len(query_tokens)
    abstract_coverage = len(query_tokens & abstract_tokens) / len(query_tokens)
    domain_coverage = len(anchor_matches) / max(1, len(domain_tokens))

    score = 0.65 * title_coverage + 0.25 * abstract_coverage + 0.10 * domain_coverage
    return round(min(1.0, max(0.0, score)), 4)


def source_relevance(query: str, source: Dict[str, Any]) -> float:
    return relevance_score(query, source.get("title", ""), source.get("abstract", ""))
