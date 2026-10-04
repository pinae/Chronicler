from io import StringIO

import pytest
import yaml
from django.core.management import CommandError, call_command

from chronicle.importers.media import ArticleCollectionError, parse_articles

COLLECTION = {
    "event": "harbour-fire",
    "title": "The Harbour Fire",
    "articles": [
        {
            "outlet": "The Courier",
            "author": "Tom Reiss",
            "published_at": "2026-05-04T08:15:00Z",
            "url": "https://courier.example/neighbours",
            "text": "The neighbours helped Petra clear the ashes.",
        },
        {
            "outlet": "The Courier",
            "author": "Ines Varga",
            "published_at": "2026-05-02T07:30:00Z",
            "url": "https://courier.example/harbour-fire",
            "text": "Fire destroyed old Petra's boat shed.\n\nWitnesses saw Mayor Holt nearby.",
        },
        {
            "outlet": "Harbour Herald",
            "author": "Ana Lund",
            "published_at": "2026-05-02T12:00:00Z",
            "url": "https://herald.example/fire",
            "text": "An electrical fault is the likely cause of the fire.",
        },
    ],
}


def test_each_outlet_gets_its_passages_in_order_of_publication():
    collection = parse_articles(COLLECTION)

    courier = collection.outlets["the-courier"]
    assert courier.name == "The Courier"
    assert [passage.text for passage in courier.passages] == [
        "Fire destroyed old Petra's boat shed.",
        "Witnesses saw Mayor Holt nearby.",
        "The neighbours helped Petra clear the ashes.",
    ]
    assert courier.passages[0].source == {
        "outlet": "The Courier",
        "author": "Ines Varga",
        "published_at": "2026-05-02T07:30:00Z",
        "url": "https://courier.example/harbour-fire",
    }
    assert list(collection.outlets) == ["the-courier", "harbour-herald"]


def test_an_article_without_its_outlet_is_rejected():
    broken = {**COLLECTION, "articles": [{"text": "Something happened."}]}

    with pytest.raises(ArticleCollectionError, match="article 1: missing 'outlet'"):
        parse_articles(broken)


def import_media(*arguments):
    output = StringIO()
    call_command("import_media", *arguments, stdout=output)
    return output.getvalue()


def test_the_command_writes_one_media_story_per_outlet_with_the_outlet_as_a_source(tmp_path):
    collection_file = tmp_path / "harbour-fire.yaml"
    collection_file.write_text(yaml.safe_dump(COLLECTION))

    output = import_media(str(collection_file), "--stories-dir", str(tmp_path))

    story_dir = tmp_path / "harbour-fire-the-courier"
    transcript = yaml.safe_load((story_dir / "transcript.yaml").read_text())
    assert (transcript["title"], transcript["kind"]) == ("The Harbour Fire (The Courier)", "media")
    assert transcript["utterances"][0]["speaker"] == "the-courier"
    assert transcript["utterances"][0]["source"]["author"] == "Ines Varga"
    assert yaml.safe_load((story_dir / "entities.yaml").read_text()) == {
        "the-courier": {"kind": "source", "name": "The Courier"}
    }
    assert "- **Kind:** media" in (story_dir / "README.md").read_text()
    assert (tmp_path / "harbour-fire-harbour-herald" / "transcript.yaml").exists()
    assert "2 outlets, 4 passages" in output


def test_the_command_does_not_overwrite_an_existing_story(tmp_path):
    collection_file = tmp_path / "harbour-fire.yaml"
    collection_file.write_text(yaml.safe_dump(COLLECTION))
    import_media(str(collection_file), "--stories-dir", str(tmp_path))

    with pytest.raises(CommandError, match="already has a transcript.yaml"):
        import_media(str(collection_file), "--stories-dir", str(tmp_path))
