"""Running fixture stories through the matcher in tests."""

from chronicle.models import Chronicle
from chronicle.story_fixtures import load_story, read_story
from matching.store import StoredMatcher
from schemas.library import load_library


def matched_story(slug: str, until_t: int | None = None) -> Chronicle:
    """Load a fixture story (up to `until_t`) and run the matcher over it in time order, voicing each
    player theory after the beat it follows."""
    load_library()
    chronicle = load_story(slug, until_t=until_t)
    matcher = StoredMatcher(chronicle)
    theories = read_story(slug).theories
    last_t = chronicle.beats.count()
    for t in range(last_t + 1):
        if t > 0:
            matcher.step(chronicle.beats.get(t=t))
        for theory in (theory for theory in theories if theory.voiced_at_t == t):
            utterance = chronicle.utterances.select_related("speaker_player").get(
                order=theory.utterance_order
            )
            assert utterance.speaker_player is not None, "theories are voiced by players"
            binding = {role: chronicle.entities.get(slug=slug).pk for role, slug in theory.binding.items()}
            matcher.voice(theory.schema, binding, utterance.speaker_player, utterance, t)
    return chronicle
