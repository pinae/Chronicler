"""Bayes factors between two hypotheses (concept §8.3, §9.2 retrospective fit)."""

from reader.interfaces import BeatScorer, ContextBeat, ReaderContext


def bayes_factor(
    reader: BeatScorer, beat: ContextBeat, context: ReaderContext, assumption_a: str, assumption_b: str | None
) -> float:
    """log p(beat | context, a) - log p(beat | context, b). The identical beat is scored under both
    assumptions, so the factor measures the hypotheses, not two different texts. Without
    `assumption_b`, a is compared with the reader assuming nothing."""
    log_likelihood_a = reader.beat_log_likelihood(context.assuming(assumption_a), beat)
    context_b = context if assumption_b is None else context.assuming(assumption_b)
    return log_likelihood_a - reader.beat_log_likelihood(context_b, beat)
