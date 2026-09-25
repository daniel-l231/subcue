"""Merge multiple cue streams into one, ordered by start time."""

import heapq
from typing import Iterable, Iterator

from .model import Cue


def merge_streams(*streams: Iterable[Cue]) -> Iterator[Cue]:
    """Merge cue streams into a single stream ordered by start time.

    Each stream must already be sorted by start_ms, which every valid
    subtitle file is, so this is a k-way merge that only ever holds one
    cue per stream in memory at a time - the same streaming guarantee
    `srt.parse` and `srt.write` make individually. Cues with equal start
    times keep the order of the streams passed in, so a cue from the
    first argument sorts before a simultaneous cue from the second.
    """
    return heapq.merge(*streams, key=lambda cue: cue.start_ms)
