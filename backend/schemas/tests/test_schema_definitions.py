import textwrap

import pytest
import yaml

from schemas.definitions import SchemaDefinitionError, parse_schema
from schemas.library import LIBRARY_DIR
from schemas.patterns import BeatPattern, Literal, RoleVariable, StepReference, Wildcard

BETRAYAL_FILE = LIBRARY_DIR / "betrayal.yaml"


def betrayal_document():
    return yaml.safe_load(BETRAYAL_FILE.read_text())


def schema_from(text):
    return parse_schema(yaml.safe_load(textwrap.dedent(text)), source="test.yaml")


MINIMAL_SCHEMA = """
    slug: rivalry
    name: Rivalry
    roles: {A: character, B: character}
    steps:
      - step_id: clash
        phase: setup
        trigger: true
        patterns:
          - {pred: opposes, args: {who: $A, whom: $B}}
"""


def test_betrayal_round_trips_to_an_equal_document():
    document = betrayal_document()

    assert parse_schema(document, source="betrayal.yaml").to_document() == document


def test_betrayal_steps_are_parsed_in_order_with_their_attributes():
    betrayal = parse_schema(betrayal_document(), source="betrayal.yaml")

    trust, access, harm, benefit, reveal = betrayal.steps
    assert [step.step_id for step in betrayal.steps] == ["trust", "access", "harm", "benefit", "reveal"]
    assert (trust.trigger, trust.repeatable, trust.weight, trust.phase) == (True, True, 0.5, "setup")
    assert benefit.required is False
    assert reveal.phase == "payoff"
    assert betrayal.payoff_steps == ("reveal",)
    assert betrayal.prior == -2.0


def test_patterns_are_typed():
    betrayal = parse_schema(betrayal_document(), source="betrayal.yaml")
    access, harm, benefit, reveal = (betrayal.step(name) for name in ["access", "harm", "benefit", "reveal"])

    learns_hiding = access.patterns[0]
    assert learns_hiding.pred == "learns"
    assert learns_hiding.args["who"] == RoleVariable("T")
    assert learns_hiding.args["what"] == BeatPattern(
        pred="hides", args={"who": RoleVariable("V"), "what": RoleVariable("S")}
    )
    assert benefit.patterns[0].args["what"] == Wildcard()
    assert reveal.patterns[0].args["what"] == StepReference("harm")
    assert harm.contradicts[0].args == {"who": Wildcard(), "whom": RoleVariable("T")}


def test_literals_tags_scope_and_claims_are_parsed():
    schema = schema_from(
        """
        slug: rumour
        name: Rumour
        roles: {A: character, B: character, O: source}
        steps:
          - step_id: gossip
            phase: setup
            patterns:
              - pred: is
                args: {who: $A, trait: nervous}
                tags_any: [secretly, quietly]
                tags_all: [twice]
                scope: {players_know: true}
              - {pred: harms, args: {who: $A, whom: $B}, claimed_by: $O}
        """
    )
    nervous, claimed = schema.step("gossip").patterns

    assert nervous.args["trait"] == Literal("nervous")
    assert nervous.tags_any == ("secretly", "quietly")
    assert nervous.tags_all == ("twice",)
    assert nervous.players_know is True
    assert claimed.claimed_by == RoleVariable("O")


def test_defaults_apply_to_omitted_step_attributes():
    rivalry = schema_from(MINIMAL_SCHEMA)
    clash = rivalry.step("clash")

    assert (clash.required, clash.repeatable, clash.weight, clash.contradicts) == (True, False, 1.0, ())
    assert (rivalry.prior, rivalry.payoff_steps, rivalry.constraints, rivalry.origin) == (
        0.0,
        (),
        (),
        "library",
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            "{pred: stabs, args: {who: $A, whom: $B}}",
            r"test\.yaml: step 'clash', pattern 1: unknown predicate 'stabs'",
        ),
        ("{pred: opposes, args: {who: $A, whom: $C}}", r"test\.yaml: step 'clash', pattern 1: .*'\$C'.*"),
        ("{pred: opposes, args: {who: $A, whom: $nowhere}}", r"'\$nowhere'"),
        ("{pred: opposes, args: {who: $A, with: $B}}", r"opposes.*role 'with'"),
        (
            "{pred: opposes, args: {who: $A, whom: {pred: is, args: {who: $B, trait: x}}}}",
            r"opposes.*'whom'.*prop",
        ),
        ("{pred: is, args: {who: $A, trait: $B}}", r"is.*'trait'.*entity"),
        ("{pred: opposes, args: {who: $A, whom: $B}, claimed_by: sometimes}", r"claimed_by"),
        ("{pred: opposes, args: {who: $A, whom: $B}, colour: red}", r"unknown key 'colour'"),
    ],
)
def test_invalid_patterns_are_rejected_with_their_location(change, message):
    text = MINIMAL_SCHEMA.replace("{pred: opposes, args: {who: $A, whom: $B}}", change)

    with pytest.raises(SchemaDefinitionError, match=message):
        schema_from(text)


def test_unknown_predicate_inside_a_nested_pattern_is_rejected():
    text = MINIMAL_SCHEMA.replace(
        "{pred: opposes, args: {who: $A, whom: $B}}",
        "{pred: says, args: {who: $A, what: {pred: stabs, args: {}}}}",
    )

    with pytest.raises(SchemaDefinitionError, match="unknown predicate 'stabs'"):
        schema_from(text)


def test_unknown_predicate_in_a_contradicts_pattern_is_rejected():
    text = MINIMAL_SCHEMA + "        contradicts: [{pred: stabs, args: {}}]\n"

    with pytest.raises(
        SchemaDefinitionError, match=r"step 'clash', contradicts 1: unknown predicate 'stabs'"
    ):
        schema_from(text)


def test_reference_to_a_missing_step_is_rejected():
    text = MINIMAL_SCHEMA.replace(
        "{pred: opposes, args: {who: $A, whom: $B}}", "{pred: learns, args: {who: $A, what: $reveal}}"
    )

    with pytest.raises(SchemaDefinitionError, match=r"'\$reveal' is neither a role nor a step"):
        schema_from(text)


def test_payoff_step_that_is_not_a_step_is_rejected():
    with pytest.raises(SchemaDefinitionError, match=r"payoff step 'reveal' is not a step"):
        schema_from(MINIMAL_SCHEMA + "    payoff_steps: [reveal]\n")


def test_role_of_a_kind_that_is_not_an_entity_kind_is_rejected():
    with pytest.raises(SchemaDefinitionError, match=r"role 'B'.*'weather'"):
        schema_from(MINIMAL_SCHEMA.replace("B: character", "B: weather"))


def test_name_that_is_both_a_role_and_a_step_is_rejected():
    with pytest.raises(SchemaDefinitionError, match=r"'clash' is both a role and a step"):
        schema_from(
            MINIMAL_SCHEMA.replace(
                "{A: character, B: character}", "{A: character, B: character, clash: place}"
            )
        )


def test_duplicate_step_ids_are_rejected():
    duplicated = MINIMAL_SCHEMA + textwrap.indent(
        "- step_id: clash\n  phase: payoff\n  patterns: [{pred: opposes, args: {who: $B, whom: $A}}]\n",
        "      ",
    )

    with pytest.raises(SchemaDefinitionError, match=r"step 'clash' is defined twice"):
        schema_from(duplicated)


def test_unknown_phase_is_rejected():
    with pytest.raises(SchemaDefinitionError, match=r"step 'clash'.*phase 'climax'"):
        schema_from(MINIMAL_SCHEMA.replace("phase: setup", "phase: climax"))


def test_step_without_patterns_is_rejected():
    text = MINIMAL_SCHEMA.replace(
        "        patterns:\n          - {pred: opposes, args: {who: $A, whom: $B}}\n",
        "        patterns: []\n",
    )

    with pytest.raises(SchemaDefinitionError, match=r"step 'clash' needs at least one pattern"):
        schema_from(text)


def test_missing_required_key_is_rejected():
    with pytest.raises(SchemaDefinitionError, match=r"test\.yaml: missing key 'name'"):
        schema_from(MINIMAL_SCHEMA.replace("    name: Rivalry\n", ""))
