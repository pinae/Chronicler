import math
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from evaluation.replay import replay_story
from llm.models import LLMCall
from reader.ollama import OllamaChoiceReader
from reader.uniform import UniformReader

pytestmark = pytest.mark.django_db

FIRST_TOKEN = [("A", 0.6), ("B", 0.2), ("The", 0.1), (" A", 0.05)]


class ScriptedReaderServer:
    """Answers every readout with the same first-token alternatives."""

    def server_version(self):
        return "0.22.1"

    def generate(self, request):
        return {
            "response": "A",
            "eval_count": 1,
            "prompt_eval_count": 812,
            "logprobs": [
                {
                    "token": "A",
                    "logprob": math.log(0.6),
                    "top_logprobs": [{"token": token, "logprob": math.log(p)} for token, p in FIRST_TOKEN],
                }
            ],
        }


@pytest.fixture
def read_by_a_model(settings):
    settings.OLLAMA_READER_MODEL = "gemma4:e4b"
    reader = OllamaChoiceReader(transport=ScriptedReaderServer())
    return replay_story("steward", reader=reader, until_t=5, per_player=True)


def inspect(*arguments):
    output = StringIO()
    call_command("inspect_readouts", *arguments, stdout=output)
    return output.getvalue()


def test_a_readout_shows_the_question_the_raw_alternatives_and_the_answers(read_by_a_model):
    output = inspect(str(read_by_a_model.pk), "--t", "5")

    assert f"Readouts at t=5 for the table (steward, chronicle {read_by_a_model.pk})" in output
    assert "Betrayal: T = Aldric, V = ?, S = ?\n  Next: ___ trusts Aldric." in output
    assert '  model gemma4:e4b · prompt 812 tokens · first token "A"' in output
    assert '  first-token alternatives: "A" 60.0% · "B" 20.0% · "The" 10.0% · " A" 5.0%' in output
    assert "outside the letters 15.0%" in output


def test_the_answers_add_up_the_spellings_of_each_letter(read_by_a_model):
    output = inspect(str(read_by_a_model.pk), "--t", "5")

    answers = next(line for line in output.splitlines() if line.startswith("  answers: "))
    assert answers.startswith("  answers: A) ")
    assert " 76.5% · B) " in answers


def test_a_story_slug_inspects_its_newest_replay(read_by_a_model):
    assert inspect("steward", "--t", "5") == inspect(str(read_by_a_model.pk), "--t", "5")


def test_a_players_readouts(read_by_a_model):
    output = inspect("steward", "--t", "5", "--audience", "Anna")

    assert f"Readouts at t=5 for Anna (steward, chronicle {read_by_a_model.pk})" in output
    assert "  answers: A) " in output


def test_a_readout_in_which_the_model_was_thinking_says_so(read_by_a_model):
    for call in LLMCall.objects.all():
        call.response = {**call.response, "response": "", "thinking": "Let"}
        call.save()

    output = inspect("steward", "--t", "5")

    assert '  the model was thinking ("Let"): its first token is no answer. Replay to ask again.' in output


def test_readouts_of_the_uniform_reader_asked_no_model():
    replay_story("steward", reader=UniformReader(), until_t=5)

    output = inspect("steward", "--t", "5")

    assert "  no language model was asked (uniform reader)" in output


def test_a_moment_without_readouts_says_so(read_by_a_model):
    assert "No readouts at t=2 for the table." in inspect("steward", "--t", "2")


def test_an_unknown_chronicle_explains_what_to_do():
    with pytest.raises(CommandError, match="no chronicle 'macbeth'; replay the story first"):
        inspect("macbeth", "--t", "5")
