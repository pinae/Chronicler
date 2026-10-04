import pytest
from django.apps import apps
from django.contrib import admin
from django.urls import reverse

from chronicle.models import Beat, Chronicle, Entity, FactLabel, Player, ScopeGrant
from evaluation.replay import replay_story
from llm.models import LLMCall
from matching.models import Hypothesis
from reader.uniform import UniformReader

pytestmark = pytest.mark.django_db

OUR_APPS = ["chronicle", "schemas", "matching", "reader", "llm", "evaluation", "gm_ui"]


@pytest.fixture
def every_kind_of_record(client):
    steward = replay_story("steward", reader=UniformReader(), until_t=10)
    FactLabel.objects.create(beat=steward.beats.get(t=1), verdict="verified", labeler="annotator")
    LLMCall.objects.create(
        request_hash="a" * 64,
        model="reader",
        endpoint="generate",
        request={"prompt": "Who?"},
        response={"response": "A"},
        server_version="0.12.3",
    )
    client.get(reverse("api:list_chronicles"))


def our_models():
    return [model for app in OUR_APPS for model in apps.get_app_config(app).get_models()]


def test_every_model_is_registered_in_the_admin():
    assert [model for model in our_models() if model not in admin.site._registry] == []


def test_every_list_and_detail_page_opens_for_a_superuser(admin_client, every_kind_of_record):
    for model in our_models():
        meta = model._meta
        changelist = reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist")
        assert admin_client.get(changelist).status_code == 200, changelist
        record = model.objects.first()
        assert record is not None, f"no {meta.model_name} to open"
        change = reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[record.pk])
        assert admin_client.get(change).status_code == 200, change


@pytest.mark.parametrize("model", [Beat, ScopeGrant, Hypothesis, LLMCall])
def test_engine_records_are_read_only(admin_client, model):
    model_admin = admin.site._registry[model]
    request = admin_client.get("/").wsgi_request

    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)


@pytest.mark.parametrize("model", [Chronicle, Player, Entity, FactLabel])
def test_story_metadata_and_annotations_stay_editable(admin_client, model):
    request = admin_client.get("/").wsgi_request

    assert admin.site._registry[model].has_change_permission(request)


def test_hypothesis_page_lists_its_fills(admin_client, every_kind_of_record):
    hypothesis = Hypothesis.objects.filter(fills__isnull=False).first()
    assert hypothesis is not None

    page = admin_client.get(
        reverse("admin:matching_hypothesis_change", args=[hypothesis.pk])
    ).content.decode()

    for fill in hypothesis.fills.all():
        assert f"t={fill.beat.t}" in page


def test_llm_call_page_shows_request_and_response_as_indented_json(admin_client, every_kind_of_record):
    call = LLMCall.objects.get(request_hash="a" * 64)

    page = admin_client.get(reverse("admin:llm_llmcall_change", args=[call.pk])).content.decode()

    assert "&quot;prompt&quot;: &quot;Who?&quot;" in page
    assert "<pre>" in page
