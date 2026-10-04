"""A story writer that returns scripted continuations: deterministic, for tests."""

from collections.abc import Sequence

from writing.interfaces import Continuation, WritingRequest


class ScriptExhausted(LookupError):
    pass


class FixtureStoryWriter:
    def __init__(self, script: Sequence[Continuation]) -> None:
        self.script = list(script)
        self.written = 0

    def continue_story(self, request: WritingRequest) -> Continuation:
        if self.written >= len(self.script):
            raise ScriptExhausted(f"the script has only {len(self.script)} continuations")
        continuation = self.script[self.written]
        self.written += 1
        return continuation
