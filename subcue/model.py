from dataclasses import dataclass


@dataclass(frozen=True)
class Cue:
    """A single subtitle entry. Times are milliseconds from the start."""

    index: int
    start_ms: int
    end_ms: int
    text: str
