"""Streaming reader and writer for the WebVTT (.vtt) format."""

import re
from typing import IO, Iterable, Iterator, Optional

from .model import Cue

# Hours are optional in WebVTT timestamps (unlike SRT, where they're required),
# and the fractional part is separated by a dot instead of a comma.
_TIME_RE = re.compile(
    r"(?:(\d{2}):)?(\d{2}):(\d{2})\.(\d{3})\s*-->\s*"
    r"(?:(\d{2}):)?(\d{2}):(\d{2})\.(\d{3})"
)


def parse(stream: Iterable[str]) -> Iterator[Cue]:
    """Yield Cue objects one at a time from a WebVTT stream.

    Mirrors `subcue.srt.parse`: only the lines belonging to the cue
    currently being read are held in memory, so a caller can iterate over
    a large file without holding more than one cue block at once. The
    leading `WEBVTT` header is required and consumed; `NOTE` blocks are
    skipped rather than yielded as cues.
    """
    lines = iter(stream)
    header = next(lines, None)
    if header is None or not header.rstrip("\r\n").startswith("WEBVTT"):
        raise ValueError(f"not a WebVTT file: expected WEBVTT header, got {header!r}")

    block: list[str] = []
    seen = 0
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if line.strip() == "":
            if block:
                cue = _parse_block(block, seen)
                if cue is not None:
                    seen += 1
                    yield cue
                block = []
            continue
        block.append(line)
    if block:
        cue = _parse_block(block, seen)
        if cue is not None:
            yield cue


def _parse_block(block: list[str], seen: int) -> Optional[Cue]:
    first = block[0].strip()
    if first.startswith("NOTE"):
        return None
    rest = block[1:]
    if "-->" in first:
        timing_line = first
        text_lines = rest
    elif rest and "-->" in rest[0]:
        # an optional cue identifier line precedes the timing line
        timing_line = rest[0]
        text_lines = rest[1:]
    else:
        raise ValueError(f"malformed cue block starting with {first!r}")
    start_ms, end_ms = _parse_timing_line(timing_line)
    return Cue(index=seen + 1, start_ms=start_ms, end_ms=end_ms, text="\n".join(text_lines))


def _parse_timing_line(line: str) -> tuple[int, int]:
    match = _TIME_RE.search(line)
    if not match:
        raise ValueError(f"malformed timing line: {line!r}")
    h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups()
    start = (((int(h1) if h1 else 0) * 60 + int(m1)) * 60 + int(s1)) * 1000 + int(ms1)
    end = (((int(h2) if h2 else 0) * 60 + int(m2)) * 60 + int(s2)) * 1000 + int(ms2)
    return start, end


def _format_timestamp(ms: int) -> str:
    ms = max(0, ms)
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def write(cues: Iterable[Cue], out: IO[str]) -> None:
    """Write cues to `out` as WebVTT, one at a time, without buffering the whole set."""
    out.write("WEBVTT\n\n")
    for cue in cues:
        out.write(f"{_format_timestamp(cue.start_ms)} --> {_format_timestamp(cue.end_ms)}\n")
        out.write(cue.text)
        out.write("\n\n")
