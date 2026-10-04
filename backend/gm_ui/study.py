"""Privacy for the RQ2 study (WP-056): only tables where every player consented are exported, and
exports name players by pseudonym. Characters and outlets are fiction or public and keep their names."""

import re
from collections.abc import Mapping
from typing import Any

from chronicle.models import Chronicle, Player

# Usage-event parameters that hold a player's id.
PLAYER_PARAMETERS = ("audience", "player")


def has_consent(chronicle: Chronicle) -> bool:
    """Every human at the table consented; literature and media have no humans at the table."""
    return not chronicle.players.filter(implicit=False, consent_given_at__isnull=True).exists()


def humans(chronicle: Chronicle) -> list[Player]:
    return list(chronicle.players.filter(implicit=False).order_by("pk"))


def pseudonymized_text(text: str, chronicle: Chronicle) -> str:
    """Whole-word mentions of a player's name replaced by their pseudonym."""
    for player in humans(chronicle):
        text = re.sub(rf"\b{re.escape(player.name)}\b", player.pseudonym, text)
    return text


def pseudonymized_params(params: Mapping[str, Any], chronicle: Chronicle | None) -> dict[str, Any]:
    """Player ids in a usage event's parameters replaced by pseudonyms."""
    pseudonyms = {player.pk: player.pseudonym for player in humans(chronicle)} if chronicle else {}
    replaced = dict(params)
    for key in PLAYER_PARAMETERS:
        value = replaced.get(key)
        if isinstance(value, str) and value.isdigit() and int(value) in pseudonyms:
            replaced[key] = pseudonyms[int(value)]
    body = replaced.get("body")
    if isinstance(body, dict) and isinstance(body.get("players_present"), list):
        replaced["body"] = {
            **body,
            "players_present": [pseudonyms.get(player, player) for player in body["players_present"]],
        }
    return replaced
