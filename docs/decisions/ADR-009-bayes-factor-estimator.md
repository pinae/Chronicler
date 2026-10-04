# ADR-009: Bayes factors by forced scoring through Ollama's top logprobs

**Status:** accepted (2026-10-04) · **Work package:** WP-044

## Context
Retrospective fit (concept §9.2) needs log P(beat | story so far, assumption) for the beats of a
story's dormant window, under the truth and under its strongest rival; the Bayes factor is their
difference. The owner's server (Ollama 0.22.1, `gemma4:e4b`, `docs/llm-smoke.md`) returns logprobs
for generated tokens only (at most 20 alternatives per token), not for prompt tokens. The estimator
must work with that server and any model on it, go through the LLM call cache (concept §8.4), and
keep identical inputs giving identical numbers.

## Options considered
- **Ollama prompt logprobs (`echo`)**: one call per beat, exact. Not available: Ollama scores
  generated tokens only, and the smoke check confirms it.
- **A sidecar inference server with prompt logprobs** (vLLM's `prompt_logprobs`, the OpenAI-style
  `echo` with `logprobs`): exact and one call per beat, but a second server to run, with its own
  model files and GPU memory next to Ollama.
- **Forced scoring through Ollama's top logprobs**: ask for one token after the prompt plus the text
  scored so far, take the probability of the alternative that continues the beat's text, repeat.
  Works with every model on the existing server; one call per token of the beat; approximate when
  the true token is not among the 20 alternatives.
- **Belief updates instead of likelihoods**: ask "Is the story H?" before and after the beat and
  compare. Cheap, but it measures a change of opinion, not how well the beat fits a hypothesis, and
  it is already what the surprise curve does.

## Decision
Forced scoring through Ollama (`reader/forced_scoring.py`):
- The prompt is the story so far in plain text, ending with the beat's line prefix (`t=17:`), sent
  **raw** (no chat template, so the model continues the text itself and has no turn to think in),
  with `truncate: false` and neutral sampling (`llm.next_token.NEUTRAL_SAMPLING`).
- Each step takes the **longest** alternative that continues the remaining text, adds its logprob
  and appends it to the prompt.
- A token outside the alternatives is charged an **upper bound** of its probability (the smaller of
  the least probable alternative and the probability left over by all of them), and the text is
  skipped by one word, because the model's tokenization of it is unknown. The number of such steps
  is counted (`ForcedScore.unmatched`).
- Every step is an ordinary cached request, so a re-run is free and gives the same factor.

The sidecar stays the upgrade path: it would implement the same `BeatScorer.beat_log_likelihood`.

## Reasoning
- Ollama's API types list `logprobs` and `top_logprobs` (0–20) on generate requests, and `raw` for
  prompts without a template ([`api/types.go`](https://github.com/ollama/ollama/blob/main/api/types.go));
  there is no prompt-logprob field. A request to raise the cap to 100 is open
  ([ollama#18590](https://github.com/ollama/ollama/issues/18590),
  [PR #18591](https://github.com/ollama/ollama/pull/18591)); `MAX_TOP_LOGPROBS` would follow it.
  Asking for named tokens' logprobs was proposed and closed in favour of that
  ([PR #18580](https://github.com/ollama/ollama/pull/18580)).
- vLLM supports prompt logprobs and `echo` for exactly this kind of scoring
  ([vLLM sampling parameters](https://docs.vllm.ai/en/latest/api/vllm/sampling_params/),
  [vLLM forum: purpose of prompt logprobs](https://discuss.vllm.ai/t/what-is-the-purpose-of-prompt-logprobs/1714)),
  which is why it remains the exact alternative.
- A Bayes factor compares the same text under two assumptions; the forced tokenization and the
  bounds are the same in both, so much of their error cancels in the difference.

## Consequences
- Scoring costs one request per token of a beat, twice per beat (truth and rival): a dormant
  window of 20 beats of about 12 tokens is about 500 requests, each a short continuation of a
  cached prompt prefix on the server. Re-runs come from the call log.
- Where a model ranks the true tokens low, `unmatched` grows and the factor gets coarser; a sidecar
  with prompt logprobs removes that.
