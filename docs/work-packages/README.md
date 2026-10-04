# Work packages

One file per package (`WP-NNN-short-name.md`), in the format of the `work-package` skill:
Goal, Acceptance criteria, Dependencies, Out of scope, Status, and a Summary once done.
Some packages have a **Notes** section for open questions. Since 2026-10-03 the user has asked
Claude to work through the packages on its own: open questions are resolved by best judgement
and each decision is recorded in that package's Summary.

Packages are numbered in dependency order: each one depends only on lower-numbered packages,
so working through them in order never blocks. "Depends on" lists direct dependencies only.
Milestones refer to §11 of [`docs/narrative-engine-concept.md`](../narrative-engine-concept.md):
M0–M9 are the v1 core, R1–R4 the research tracks. Research-track packages are coarser and
will probably be split further once the core exists.

Each package's status is kept in its own file, not here.

| Package | Title | Milestone | Depends on |
|---|---|---|---|
| [WP-001](WP-001-project-layout-and-backend-skeleton.md) | Monorepo layout and backend skeleton | M0 | — |
| [WP-002](WP-002-ci-and-pre-commit.md) | CI pipeline and pre-commit hooks | M0 | 001 |
| [WP-003](WP-003-ollama-settings-and-smoke-check.md) | Ollama settings, opt-in integration tests and smoke check | M0 (pulled forward from §8.2) | 001 |
| [WP-004](WP-004-chronicle-core-models.md) | Chronicle, player, utterance and entity models | M0/M1 | 001 |
| [WP-005](WP-005-predicate-vocabulary.md) | Predicate vocabulary and argument validation | M1 | 001 |
| [WP-006](WP-006-append-only-beat-log.md) | Append-only beat log | M1 | 004, 005 |
| [WP-007](WP-007-entity-attribute-view.md) | Entity attribute view | M1 | 006 |
| [WP-008](WP-008-scope-grants.md) | Scope grants | M2 | 006 |
| [WP-009](WP-009-player-visible-views.md) | Player-visible chronicle views | M2 | 008 |
| [WP-010](WP-010-test-factories-and-story-loader.md) | Test factories and fixture-story loader | M0 | 006, 008 |
| [WP-011](WP-011-schema-library-loader.md) | Schema library loader | M3 | 005 |
| [WP-012](WP-012-schema-constraints.md) | Schema constraints | M3 | 007, 008, 011 |
| [WP-013](WP-013-pattern-matching-core.md) | Beat pattern matching | M4 | 011 |
| [WP-014](WP-014-pattern-matching-scope-and-claims.md) | Pattern matching with scope and claims | M4 | 009, 013 |
| [WP-015](WP-015-hypothesis-seeding-and-fill.md) | Hypotheses, seeding and fill | M4 | 011, 013 |
| [WP-016](WP-016-hypothesis-refinement.md) | Hypothesis refinement | M4 | 015 |
| [WP-017](WP-017-weights-and-completion.md) | Weights and completion | M4 | 015 |
| [WP-018](WP-018-refutation.md) | Refutation | M4 | 012, 015 |
| [WP-019](WP-019-merge-and-prune.md) | Merging and pruning | M4 | 016, 017, 018 |
| [WP-020](WP-020-lattice-at-t-and-replay-guarantee.md) | Lattice at t and the replay guarantee | M4 | 010, 016, 017, 018, 019 |
| [WP-021](WP-021-per-player-lattices.md) | Per-player lattices | M4 (§9.3) | 014, 020 |
| [WP-022](WP-022-voiced-hypotheses.md) | Voiced hypotheses | M5 | 010, 019 |
| [WP-023](WP-023-llm-call-log-and-cache.md) | LLM call log and cache | M6 | 003 |
| [WP-024](WP-024-reader-model-protocol-and-table-reader.md) | Reader model protocol, TableReader and dependency registry | M6 | 015 |
| [WP-025](WP-025-readout-questions.md) | Readout questions and candidates | M6 | 009, 015 |
| [WP-026](WP-026-context-builder.md) | Context builder | M6 (§9.3) | 020, 024 |
| [WP-027](WP-027-seed-phase-and-expectations.md) | Seed phase and expectations | M6 | 023, 024, 025, 026 |
| [WP-028](WP-028-ollama-choice-reader.md) | Ollama choice reader | M6 | 003, 023, 024 |
| [WP-029](WP-029-ingester-protocol-and-fixture-ingester.md) | Ingester protocol and fixture ingester | M7 | 010, 022, 024 |
| [WP-030](WP-030-replay-command.md) | Replay command and run files | M7 | 020, 027, 029 |
| [WP-031](WP-031-ollama-ingester.md) | Ollama ingester | M7 | 003, 023, 029 |
| [WP-032](WP-032-api-foundation-and-usage-events.md) | API foundation and usage events | M8 | 006 |
| [WP-033](WP-033-admin.md) | Admin for all models | M8 | 027, 032 |
| [WP-034](WP-034-frontend-and-e2e-skeleton.md) | Frontend and end-to-end test skeleton | M8 | 002, 032 |
| [WP-035](WP-035-chronicle-screen.md) | Chronicle screen | M8 | 009, 034 |
| [WP-036](WP-036-lattice-screen.md) | Lattice screen | M8 | 021, 035 |
| [WP-037](WP-037-expectations-view.md) | Expectations view | M8 | 027, 036 |
| [WP-038](WP-038-knowledge-screen.md) | Knowledge screen | M8 | 008, 035 |
| [WP-039](WP-039-candidate-beat-dry-run.md) | Candidate beat dry run | M8 | 036 |
| [WP-040](WP-040-ground-truth-and-lattice-metrics.md) | Ground truth and lattice metrics | M9 | 022, 030 |
| [WP-041](WP-041-reader-metrics.md) | Reader-based metrics | M9 | 027, 040 |
| [WP-042](WP-042-evaluate-command.md) | Evaluate command | M9 | 041 |
| [WP-043](WP-043-evaluation-stories.md) | Evaluation stories | M9 | 042 |
| [WP-044](WP-044-bayes-factor-backend.md) | Production Bayes-factor estimator | R1 (deferred decision, §13) | 003, 028, 043 |
| [WP-045](WP-045-prose-importer.md) | Prose importer | R1 | 029 |
| [WP-046](WP-046-session-transcript-importer.md) | Session transcript importer | R1 | 029 |
| [WP-047](WP-047-draft-beats-command.md) | Draft beats command | R1 | 031 |
| [WP-048](WP-048-rq1-report.md) | RQ1 report | R1 | 042, 043, 045, 046, 047 |
| [WP-049](WP-049-story-writer-and-generate.md) | Story writer protocol and generate command | R2 | 029, 042 |
| [WP-050](WP-050-ollama-story-writer.md) | Ollama story writer | R2 | 023, 049 |
| [WP-051](WP-051-paired-comparison-and-blind-export.md) | Paired comparison and blind export | R2 | 050 |
| [WP-052](WP-052-media-importer.md) | Media importer and claim ingest | R3 | 014, 031 |
| [WP-053](WP-053-fact-labels.md) | Fact labels | R3 | 033, 052 |
| [WP-054](WP-054-cross-chronicle-comparison.md) | Cross-chronicle comparison | R3 | 040, 053 |
| [WP-055](WP-055-usage-export-and-summaries.md) | Usage event export and session summaries | R4 | 039 |
| [WP-056](WP-056-consent-and-anonymisation.md) | Consent and anonymisation | R4 | 055 |
| [WP-057](WP-057-rq1-corpus.md) | RQ1 corpus (split off WP-048) | R1 | 044, 048 |
| [WP-058](WP-058-development-database-and-env.md) | Development database and settings from .env | M0 | 001, 003 |
| [WP-059](WP-059-learned-beats-in-player-views.md) | Learned beats enter players' views and lattices | M5 | 008, 021 |
| [WP-060](WP-060-schemas-for-the-example-stories.md) | Schemas for the example stories | M3 | 011, 012 |
| [WP-061](WP-061-example-stories-and-guided-tour.md) | Example stories (Macbeth, The Broken Jug) and a guided tour | M9 | 043, 059, 060 |
