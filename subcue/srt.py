"""Streaming reader and writer for the SubRip (.srt) format."""

import re
from typing import IO, Iterable, Iterator, Optional

from .model import Cue

_TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def parse(stream: Iterable[str]) -> Iterator[Cue]:
    """Yield Cue objects one at a time from an SRT stream.

    `stream` is any iterable of lines - a file object opened in text mode
    works directly. Only the lines belonging to the cue currently being
    read are held in memory, so a caller can iterate over a multi-gigabyte
    file (a full-length film with burned-in captions, a day-long stream
    transcript) without ever holding more than one cue block at a time.
    """
    block: list[str] = []
    for raw_line in stream:
        line = raw_line.rstrip("\r\n")
        if line.strip() == "":
            if block:
                cue = _parse_block(block)
                if cue is not None:
                    yield cue
                block = []
            continue
        block.append(line)
    if block:
        cue = _parse_block(block)
        if cue is not None:
            yield cue


def _parse_block(block: list[str]) -> Optional[Cue]:
    first = block[0].strip()
    rest = block[1:]
    if first.isdigit() and rest and "-->" in rest[0]:
        index = int(first)
        timing_line = rest[0]
        text_lines = rest[1:]
    elif "-->" in first:
        # tolerate files that drop the numeric index line
        index = 0
        timing_line = first
        text_lines = rest
    else:
        raise ValueError(f"malformed cue block starting with {first!r}")
    start_ms, end_ms = _parse_timing_line(timing_line)
    return Cue(index=index, start_ms=start_ms, end_ms=end_ms, text="\n".join(text_lines))


def _parse_timing_line(line: str) -> tuple[int, int]:
    match = _TIME_RE.search(line)
    if not match:
        raise ValueError(f"malformed timing line: {line!r}")
    h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(g) for g in match.groups())
    start = ((h1 * 60 + m1) * 60 + s1) * 1000 + ms1
    end = ((h2 * 60 + m2) * 60 + s2) * 1000 + ms2
    return start, end


def _format_timestamp(ms: int) -> str:
    ms = max(0, ms)
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write(cues: Iterable[Cue], out: IO[str]) -> None:
    """Write cues to `out`, one at a time, without buffering the whole set.

    Cues are renumbered sequentially starting at 1, since that's what most
    players expect regardless of the original index values.
    """
    for position, cue in enumerate(cues, start=1):
        out.write(f"{position}\n")
        out.write(f"{_format_timestamp(cue.start_ms)} --> {_format_timestamp(cue.end_ms)}\n")
        out.write(cue.text)
        out.write("\n\n")
