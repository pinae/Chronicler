from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse

from chronicle.beat_log import BeatDraft
from evaluation.replay import replay_story
from gm_ui.usage_summary import dry_run_outcomes, expectation_outcomes
from matching.models import Hypothesis
from reader.uniform import UniformReader

pytestmark = pytest.mark.django_db


@pytest.fixture
def steward():
    return replay_story("steward", reader=UniformReader())


def entity(chronicle, slug):
    return {"entity": chronicle.entities.get(slug=slug).pk}


def mira_goes_to(chronicle, place):
    return {"pred": "is_at", "args": {"who": entity(chronicle, "mira"), "where": entity(chronicle, place)}}


def try_beat(client, chronicle, candidate):
    response = client.post(
        reverse("api:dry_run_beat", args=[chronicle.pk]), candidate, content_type="application/json"
    )
    assert response.status_code == 200, response.content


def narrate(chronicle, candidate):
    utterance = chronicle.utterances.create(order=chronicle.utterances.count() + 1, text="(narrated)")
    return chronicle.append(
        BeatDraft(pred=candidate["pred"], args=candidate["args"], source_utterance=utterance)
    )


def view_expectations(client, chronicle, hypothesis, t):
    url = reverse("api:list_expectations", args=[chronicle.pk, hypothesis.pk])
    assert client.get(url, {"t": t}).status_code == 200


def aldric_suspected(chronicle):
    return Hypothesis.objects.get(
        chronicle=chronicle,
        for_player=None,
        binding={"T": chronicle.entities.get(slug="aldric").pk, "V": None, "S": None},
    )


def test_a_tried_beat_that_was_then_narrated_was_acted_on(client, steward):
    to_the_hall, to_the_cellar = mira_goes_to(steward, "hall"), mira_goes_to(steward, "cellar")
    try_beat(client, steward, to_the_hall)
    try_beat(client, steward, to_the_cellar)

    narrate(steward, to_the_cellar)

    outcomes = dry_run_outcomes(steward)
    assert [(o.t, o.pred, o.acted_on_t) for o in outcomes] == [(25, "is_at", None), (25, "is_at", 25)]


def test_a_rejected_dry_run_is_no_engine_output(client, steward):
    client.post(
        reverse("api:dry_run_beat", args=[steward.pk]),
        {"pred": "is_at", "args": {}},
        content_type="application/json",
    )

    assert dry_run_outcomes(steward) == []


def test_an_expected_candidate_that_a_later_beat_brought_about_was_acted_on(client, steward):
    view_expectations(client, steward, aldric_suspected(steward), t=10)

    outcomes = {o.candidate: o for o in expectation_outcomes(steward)}

    # Mira trusts Aldric again at t=17, filling the step the table was asked about.
    assert outcomes["Mira"].question == "Next: ___ trusts Aldric."
    assert (outcomes["Mira"].asked_at_t, outcomes["Mira"].acted_on_t) == (10, 17)
    assert outcomes["Edda"].acted_on_t is None


def test_the_summary_command_lists_the_outputs_and_what_followed(client, steward):
    try_beat(client, steward, mira_goes_to(steward, "cellar"))
    narrate(steward, mira_goes_to(steward, "cellar"))
    view_expectations(client, steward, aldric_suspected(steward), t=10)
    output = StringIO()

    call_command("usage_summary", str(steward.pk), stdout=output)

    lines = output.getvalue().splitlines()
    assert lines[0] == "Engine outputs shown for The Steward of Wend, and whether a matching beat followed"
    assert "Dry runs: 1 of 1 acted on" in lines
    assert "  t=25  Mira is at The cellar.  acted on at t=25" in lines
    assert any(line.startswith("Expectations shown: 1 of ") for line in lines)
    assert "  t=10  Next: ___ trusts Aldric.  Mira (17%)  acted on at t=17" in lines
