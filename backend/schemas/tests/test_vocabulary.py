import pytest

from schemas.vocabulary import (
    InvalidBeatArgs,
    UnknownPredicate,
    ValueKind,
    VocabularyError,
    default_vocabulary,
    load_vocabulary,
)

STARTER_PREDICATES = {
    "gives", "takes", "steals",
    "helps", "harms", "protects", "saves", "kills",
    "trusts", "distrusts", "promises", "breaks", "allies", "opposes",
    "learns", "hides", "reveals", "says", "believes",
    "has", "is_at", "is",
    "wants", "fears", "seeks", "avoids",
}  # fmt: skip


def entity(entity_id):
    return {"entity": entity_id}


def prop(pred, **args):
    return {"prop": {"pred": pred, "args": args}}


@pytest.fixture
def vocabulary():
    return default_vocabulary()


def write_vocabulary(tmp_path, text):
    path = tmp_path / "vocabulary.yaml"
    path.write_text(text)
    return path


def test_starter_vocabulary_contains_the_predicates_from_the_concept(vocabulary):
    assert set(vocabulary.predicate_names) == STARTER_PREDICATES


def test_starter_vocabulary_stays_under_forty_predicates(vocabulary):
    assert len(vocabulary.predicate_names) <= 40


def test_roles_marked_with_a_question_mark_are_optional(vocabulary):
    helps = vocabulary.predicate("helps")

    assert helps.role("how").optional is True
    assert helps.role("who").optional is False


def test_roles_declare_the_value_kinds_they_accept(vocabulary):
    learns = vocabulary.predicate("learns")

    assert learns.role("what").kinds == {ValueKind.BEAT, ValueKind.PROP}


def test_loading_a_role_with_an_unknown_value_kind_names_the_predicate(tmp_path):
    path = write_vocabulary(tmp_path, "predicates:\n  gives:\n    who: [entity]\n    what: [number]\n")

    with pytest.raises(VocabularyError, match="gives.*number"):
        load_vocabulary(path)


def test_loading_a_predicate_without_roles_names_the_predicate(tmp_path):
    path = write_vocabulary(tmp_path, "predicates:\n  vanishes: {}\n")

    with pytest.raises(VocabularyError, match="vanishes"):
        load_vocabulary(path)


def test_loading_a_role_without_value_kinds_names_the_predicate(tmp_path):
    path = write_vocabulary(tmp_path, "predicates:\n  gives:\n    who: []\n")

    with pytest.raises(VocabularyError, match="gives.*who"):
        load_vocabulary(path)


def test_valid_arguments_pass(vocabulary):
    vocabulary.validate_args("helps", {"who": entity(1), "whom": entity(2)})


def test_optional_role_may_be_given(vocabulary):
    vocabulary.validate_args(
        "helps", {"who": entity(1), "whom": entity(2), "how": {"literal": "with a rope"}}
    )


def test_unknown_role_is_rejected(vocabulary):
    with pytest.raises(InvalidBeatArgs, match="helps.*unknown role 'with'"):
        vocabulary.validate_args("helps", {"who": entity(1), "whom": entity(2), "with": entity(3)})


def test_missing_required_role_is_rejected(vocabulary):
    with pytest.raises(InvalidBeatArgs, match="helps.*missing role 'whom'"):
        vocabulary.validate_args("helps", {"who": entity(1)})


def test_value_of_a_kind_the_role_does_not_allow_is_rejected(vocabulary):
    with pytest.raises(InvalidBeatArgs, match="is_at.*'where'.*literal"):
        vocabulary.validate_args("is_at", {"who": entity(1), "where": {"literal": "kitchen"}})


@pytest.mark.parametrize(
    "malformed",
    [
        "Aldric",
        {},
        {"entity": 1, "literal": "x"},
        {"person": 1},
        {"entity": "Aldric"},
        {"beat": "42"},
        {"literal": ["a", "list"]},
        {"prop": "is_at"},
    ],
)
def test_malformed_values_are_rejected(vocabulary, malformed):
    with pytest.raises(InvalidBeatArgs, match="helps.*'who'"):
        vocabulary.validate_args("helps", {"who": malformed, "whom": entity(2)})


def test_arguments_must_be_a_mapping(vocabulary):
    with pytest.raises(InvalidBeatArgs, match="helps"):
        vocabulary.validate_args("helps", [entity(1), entity(2)])


def test_beat_reference_is_accepted_where_the_role_allows_beats(vocabulary):
    vocabulary.validate_args("learns", {"who": entity(1), "what": {"beat": 42}})


def test_proposition_is_validated_against_its_own_predicate(vocabulary):
    claim = prop("is_at", who=entity(1), where=entity(2))

    vocabulary.validate_args("says", {"who": entity(3), "what": claim})


def test_invalid_proposition_is_rejected_with_its_predicate_named(vocabulary):
    claim = prop("is_at", who=entity(1))

    with pytest.raises(InvalidBeatArgs, match="is_at.*missing role 'where'"):
        vocabulary.validate_args("says", {"who": entity(3), "what": claim})


def test_propositions_are_validated_at_any_depth(vocabulary):
    rumour = prop("believes", who=entity(4), what=prop("is_at", who=entity(1), where={"literal": "x"}))

    with pytest.raises(InvalidBeatArgs, match="is_at"):
        vocabulary.validate_args("says", {"who": entity(3), "what": rumour})


def test_unknown_predicate_is_reported_as_unknown(vocabulary):
    with pytest.raises(UnknownPredicate, match="resigns"):
        vocabulary.validate_args("resigns", {"who": entity(1)})


def test_unknown_predicate_inside_a_proposition_is_reported_as_unknown(vocabulary):
    with pytest.raises(UnknownPredicate, match="resigns"):
        vocabulary.validate_args("says", {"who": entity(3), "what": prop("resigns", who=entity(1))})
