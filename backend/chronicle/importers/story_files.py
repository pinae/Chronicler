"""Writing a new fixture story's transcript and README skeleton (format: fixtures/stories/README.md)."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

TODO = "TODO"


class StoryExists(Exception):
    pass


def story_directory(stories_dir: Path, slug: str, force: bool) -> Path:
    """The story's directory, created if needed; refuses to replace a transcript unless forced."""
    directory = stories_dir / slug
    if (directory / "transcript.yaml").exists() and not force:
        raise StoryExists(f"{slug} already has a transcript.yaml; pass --force to replace it")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_transcript(
    directory: Path, title: str, kind: str, utterances: Sequence[dict[str, Any]], players: Sequence[str] = ()
) -> None:
    document: dict[str, Any] = {"title": title, "kind": kind}
    if players:
        document["players"] = list(players)
    document["utterances"] = list(utterances)
    (directory / "transcript.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100)
    )


def write_readme_skeleton(
    directory: Path, slug: str, kind: str, provenance: str = TODO, license_text: str = TODO
) -> None:
    """Provenance and license are left as TODO unless known: only public-domain or our own
    material may become a fixture (concept §9.1)."""
    (directory / "README.md").write_text(
        f"# {slug}\n\n"
        f"- **Kind:** {kind}\n"
        f"- **Provenance:** {provenance}\n"
        f"- **License:** {license_text} (public domain or our own material only)\n\n"
        f"{TODO}: what the story is about, and where its twist is revealed.\n"
    )
