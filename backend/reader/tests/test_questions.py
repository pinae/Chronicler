import pytest

from matching.engine import Fill, HypothesisState
from matching.tests.betrayal_world import ALDRIC, KEY, LETTER, MIRA, RONAN, betrayal
from reader.interfaces import Candidate
from reader.questions import NOTHING_YET, EntityInView, build_questions, entities_in_view, next_open_step
from reader.templates import PREDICATE_TEMPLATES
from schemas.vocabulary import default_vocabulary

SEAL = 6
CAST = [
    EntityInView(id=MIRA, name="Mira", kind="character", introduced_at_t=1),
    EntityInView(id=ALDRIC, name="Aldric", kind="character", introduced_at_t=1),
    EntityInView(id=RONAN, name="Ronan", kind="character", introduced_at_t=3),
    EntityInView(id=LETTER, name="The letter", kind="secret", introduced_at_t=5),
    EntityInView(id=KEY, name="The key", kind="secret", introduced_at_t=4),
    EntityInView(id=SEAL, name="The seal", kind="secret", introduced_at_t=9),
]


def hypothesis(binding, *fills):
    full_binding = {"T": None, "V": None, "S": None, **binding}
    return HypothesisState(schema=betrayal(), binding=full_binding, created_at_t=1, fills=list(fills))


def test_the_next_open_step_is_the_first_unfilled_required_step():
    trusted = hypothesis({"T": ALDRIC, "V": MIRA}, Fill("trust", 1))

    step = next_open_step(trusted)

    assert step is not None
    assert step.step_id == "access"


def test_optional_steps_are_asked_about_once_required_steps_are_filled():
    all_required = hypothesis(
        {"T": ALDRIC, "V": MIRA, "S": KEY},
        Fill("trust", 1),
        Fill("access", 2),
        Fill("harm", 3),
        Fill("reveal", 4),
    )

    step = next_open_step(all_required)

    assert step is not None
    assert step.step_id == "benefit"


def test_question_names_the_open_role_as_a_blank_in_the_predicate_template():
    trusted = hypothesis({"T": ALDRIC, "V": MIRA}, Fill("trust", 1))

    [question] = build_questions(trusted, t=8, entities=CAST, step_texts={})

    assert question.t == 8
    assert question.text == "Next: Aldric learns that Mira hides ___."


def test_candidates_are_entities_of_the_open_roles_kind_introduced_by_t_plus_nothing_yet():
    trusted = hypothesis({"T": ALDRIC, "V": MIRA}, Fill("trust", 1))

    [question] = build_questions(trusted, t=8, entities=CAST, step_texts={})

    assert question.candidates == (
        Candidate(label="A", text="The key", binding_delta={"S": KEY}),
        Candidate(label="B", text="The letter", binding_delta={"S": LETTER}),
        Candidate(label="C", text=NOTHING_YET, binding_delta=None),
    )


def test_labels_are_stable_across_calls_with_the_same_inputs():
    trusted = hypothesis({"T": ALDRIC, "V": MIRA}, Fill("trust", 1))

    first = build_questions(trusted, t=12, entities=CAST, step_texts={})
    second = build_questions(trusted, t=12, entities=list(reversed(CAST)), step_texts={})

    assert first == second


def test_when_every_role_of_the_step_is_bound_the_question_is_whether_it_happens_next():
    with_access = hypothesis({"T": ALDRIC, "V": MIRA, "S": KEY}, Fill("trust", 1), Fill("access", 2))

    [question] = build_questions(with_access, t=8, entities=CAST, step_texts={})

    assert question.text == "Next: Aldric harms Mira."
    assert question.candidates == (
        Candidate(label="A", text="this happens next", binding_delta={}),
        Candidate(label="B", text=NOTHING_YET, binding_delta=None),
    )


def test_a_step_reference_is_shown_as_the_text_of_the_beat_that_filled_it():
    harmed = hypothesis(
        {"T": ALDRIC, "V": MIRA, "S": KEY}, Fill("trust", 1), Fill("access", 2), Fill("harm", 3)
    )

    [question] = build_questions(harmed, t=8, entities=CAST, step_texts={3: "Aldric steals the key"})

    assert question.text == "Next: Mira learns that Aldric steals the key."


def test_long_candidate_lists_are_split_into_pages_each_with_nothing_yet():
    someone = hypothesis({"V": MIRA})
    many_characters = CAST + [
        EntityInView(id=100 + n, name=f"Guard {n}", kind="character", introduced_at_t=1) for n in range(4)
    ]

    pages = build_questions(someone, t=10, entities=many_characters, step_texts={}, max_candidates=3)

    assert [[candidate.label for candidate in page.candidates] for page in pages] == [
        ["A", "B", "C"],
        ["A", "B", "C"],
        ["A", "B", "C"],
        ["A", "B"],
    ]
    assert all(page.candidates[-1].binding_delta is None for page in pages)
    assert [len(page.candidates) - 1 for page in pages] == [2, 2, 2, 1]


def test_hypothesis_without_open_steps_has_no_questions():
    done = hypothesis(
        {"T": ALDRIC, "V": MIRA, "S": KEY},
        *[Fill(step, t) for t, step in enumerate(["trust", "access", "harm", "benefit", "reveal"], start=1)],
    )

    assert build_questions(done, t=8, entities=CAST, step_texts={}) == []


def test_every_predicate_of_the_vocabulary_has_a_template():
    assert set(default_vocabulary().predicate_names) <= set(PREDICATE_TEMPLATES)


@pytest.mark.django_db
def test_entities_in_view_are_those_mentioned_in_beats_the_audience_saw(
    chronicle, players, entity_factory, beat_factory
):
    anna, ben = players
    mira, aldric, ledger = (
        entity_factory(canonical_name="Mira"),
        entity_factory(canonical_name="Aldric"),
        entity_factory(canonical_name="Ledger", kind="secret"),
    )
    beat_factory("trusts", who=mira, whom=aldric, players=[anna, ben])
    beat_factory("hides", who=mira, what=ledger, players=[anna])

    assert [entity.name for entity in entities_in_view(chronicle, ben, t=2)] == ["Mira", "Aldric"]
    assert [entity.name for entity in entities_in_view(chronicle, anna, t=2)] == ["Mira", "Aldric", "Ledger"]
    assert [entity.name for entity in entities_in_view(chronicle, None, t=2)] == ["Mira", "Aldric"]
