"""A tiny dependency registry: settings.INJECTED maps each injected interface to the dotted path of
the implementation to build (concept §10). No framework needed."""

from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def make(interface: str) -> Any:
    """Build the implementation bound to `interface` (e.g. "ReaderModel") with its defaults."""
    try:
        dotted_path = settings.INJECTED[interface]
    except KeyError:
        raise ImproperlyConfigured(f"settings.INJECTED has no binding for {interface}") from None
    return import_string(dotted_path)()
