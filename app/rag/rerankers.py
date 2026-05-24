import re
from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class Candidate:
    text: str
    vector_score: float
    payload: dict


class Reranker:
    def rerank(self, query: str, candidates: list[Candidate]) -> list[tuple[Candidate, float]]:
        raise NotImplementedError


class FallbackFinancialReranker(Reranker):
    financial_terms = {
        "debt",
        "ratio",
        "risk",
        "revenue",
        "liability",
        "asset",
        "cash",
        "profit",
        "loss",
        "margin",
        "covenant",
        "audit",
        "tax",
    }

    def rerank(self, query: str, candidates: list[Candidate]) -> list[tuple[Candidate, float]]:
        q_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        ranked: list[tuple[Candidate, float]] = []
        for candidate in candidates:
            c_terms = set(re.findall(r"[a-zA-Z0-9]+", candidate.text.lower()))
            lexical = len(q_terms & c_terms) / max(len(q_terms), 1)
            financial_boost = len((q_terms | c_terms) & self.financial_terms) / 20
            score = 0.7 * candidate.vector_score + 0.25 * lexical + 0.05 * financial_boost
            ranked.append((candidate, score))
        return sorted(ranked, key=lambda item: item[1], reverse=True)


class CrossEncoderFinancialReranker(Reranker):
    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)
        self.fallback = FallbackFinancialReranker()

    def rerank(self, query: str, candidates: list[Candidate]) -> list[tuple[Candidate, float]]:
        if not candidates:
            return []
        pairs = [(query, candidate.text) for candidate in candidates]
        raw_scores = self.model.predict(pairs)
        fallback_scores = {id(candidate): score for candidate, score in self.fallback.rerank(query, candidates)}
        ranked: list[tuple[Candidate, float]] = []
        for candidate, raw_score in zip(candidates, raw_scores, strict=True):
            # Cross-encoder score carries semantic relevance; fallback keeps finance keyword signal.
            score = 0.85 * float(raw_score) + 0.15 * fallback_scores[id(candidate)]
            ranked.append((candidate, score))
        return sorted(ranked, key=lambda item: item[1], reverse=True)


def get_reranker() -> Reranker:
    settings = get_settings()
    if settings.reranker_type.lower() == "cross_encoder":
        try:
            return CrossEncoderFinancialReranker(settings.cross_encoder_model_name)
        except Exception:
            return FallbackFinancialReranker()
    return FallbackFinancialReranker()
