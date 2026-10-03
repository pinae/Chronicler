"""Running fixture stories through the matcher in tests."""

from chronicle.models import Chronicle
from chronicle.story_fixtures import load_story
from matching.store import StoredMatcher
from schemas.library import load_library


def matched_story(slug: str, until_t: int | None = None) -> Chronicle:
    """Load a fixture story (up to `until_t`) and run the matcher over every beat in order."""
    load_library()
    chronicle = load_story(slug, until_t=until_t)
    matcher = StoredMatcher(chronicle)
    for beat in chronicle.beats.order_by("t"):
        matcher.step(beat)
    return chronicle
