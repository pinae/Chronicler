"""Choosing the reader model for a command run: the configured one, the uniform baseline, or none."""

from narrative_engine import di
from reader.interfaces import ReaderModel
from reader.uniform import UniformReader

READER_CHOICES = ["configured", "uniform", "none"]
READER_HELP = (
    "configured: settings.INJECTED['ReaderModel']; uniform: the know-nothing baseline; none: no readouts"
)


def choose_reader(choice: str) -> ReaderModel | None:
    if choice == "none":
        return None
    if choice == "uniform":
        return UniformReader()
    reader: ReaderModel = di.make("ReaderModel")
    return reader
