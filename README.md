# subcue

A small library and CLI for working with subtitle files.

Most tools I found for this either shell out to ffmpeg for trivial edits or
load the whole file into a list before doing anything with it. That's fine
for a two-minute clip's subtitles, less fine for a transcript generated from
a multi-hour stream or lecture recording, where the SRT file itself can run
into the tens of megabytes. `subcue` parses and writes cues one at a time,
so memory use stays flat regardless of file size.

It speaks SubRip (`.srt`) and WebVTT (`.vtt`).

## Library usage

```python
from subcue import parse, write

with open("input.srt", encoding="utf-8") as f:
    for cue in parse(f):
        print(cue.start_ms, cue.end_ms, cue.text)
```

`parse` takes any iterable of lines and yields `Cue` objects lazily - it
never reads the whole file into memory. `write` takes an iterable of cues
and a text-mode file object and streams them out the same way:

```python
from subcue import Cue, write

cues = (Cue(index=i, start_ms=i * 1000, end_ms=i * 1000 + 800, text=f"line {i}")
        for i in range(3))

with open("output.srt", "w", encoding="utf-8") as f:
    write(cues, f)
```

Because both ends are iterators, you can pipe a transform between a `parse`
call and a `write` call - shifting timestamps, dropping empty cues, merging
adjacent ones - without ever materializing the full cue list.

The top-level `parse`/`write` are the SRT versions. WebVTT lives in its own
submodule, since the two formats have different headers and timestamp
syntax:

```python
from subcue import vtt

with open("input.vtt", encoding="utf-8") as f:
    for cue in vtt.parse(f):
        print(cue.start_ms, cue.end_ms, cue.text)

with open("output.vtt", "w", encoding="utf-8") as f:
    vtt.write(cues, f)
```

Both modules produce and consume the same `Cue` type, so converting between
formats is just parsing with one module and writing with the other.

## CLI usage

```
# nudge every timestamp forward by 1.5 seconds
subcue shift input.srt output.srt --seconds 1.5

# pull audio out of sync by shifting backward
subcue shift input.srt output.srt --seconds -0.75

# check for overlapping or out-of-order cues
subcue validate input.srt
```

`validate` exits non-zero if it finds problems, so it's usable as a check
in a script.

## Status

Early. SRT and WebVTT parsing and writing, timestamp shifting, and basic
validation work. The CLI (`shift`, `validate`) is still SRT-only - WebVTT
support so far is library-level. See the roadmap for what's missing.
