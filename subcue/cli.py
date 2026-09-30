import argparse
import sys
from typing import Iterator, List, Optional

from . import merge, srt
from .encoding import open_text
from .model import Cue


def _shift_cues(cues: Iterator[Cue], offset_ms: int) -> Iterator[Cue]:
    for cue in cues:
        yield Cue(
            index=cue.index,
            start_ms=max(0, cue.start_ms + offset_ms),
            end_ms=max(0, cue.end_ms + offset_ms),
            text=cue.text,
        )


def _cmd_shift(args: argparse.Namespace) -> int:
    offset_ms = round(args.seconds * 1000)
    with open_text(args.input, args.encoding) as infile, \
            open(args.output, "w", encoding="utf-8") as outfile:
        srt.write(_shift_cues(srt.parse(infile), offset_ms), outfile)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    count = 0
    problems = 0
    with open_text(args.input, args.encoding) as infile:
        try:
            previous_end = None
            for cue in srt.parse(infile):
                count += 1
                if cue.end_ms < cue.start_ms:
                    print(f"cue {count}: end time is before start time", file=sys.stderr)
                    problems += 1
                if previous_end is not None and cue.start_ms < previous_end:
                    print(f"cue {count}: overlaps the previous cue", file=sys.stderr)
                    problems += 1
                previous_end = cue.end_ms
        except ValueError as exc:
            print(f"parse error after {count} cues: {exc}", file=sys.stderr)
            return 1
    print(f"{count} cues, {problems} problems")
    return 1 if problems else 0


def _cmd_merge(args: argparse.Namespace) -> int:
    with open_text(args.first, args.encoding) as f1, \
            open_text(args.second, args.encoding) as f2, \
            open(args.output, "w", encoding="utf-8") as outfile:
        merged = merge.merge_streams(srt.parse(f1), srt.parse(f2))
        srt.write(merged, outfile)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subcue", description="small tools for working with subtitle files"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # shared by every command that reads a file; output is always UTF-8
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--encoding",
        default="auto",
        help="input encoding (default: detect from BOM, then UTF-8, then cp1252)",
    )

    shift = sub.add_parser("shift", parents=[common], help="shift every timestamp in an SRT file by a fixed offset")
    shift.add_argument("input")
    shift.add_argument("output")
    shift.add_argument("--seconds", type=float, required=True, help="offset in seconds, may be negative")
    shift.set_defaults(func=_cmd_shift)

    validate = sub.add_parser("validate", parents=[common], help="check an SRT file for overlaps and ordering problems")
    validate.add_argument("input")
    validate.set_defaults(func=_cmd_validate)

    merge_parser = sub.add_parser(
        "merge", parents=[common], help="merge two SRT files into one, ordered by start time"
    )
    merge_parser.add_argument("first")
    merge_parser.add_argument("second")
    merge_parser.add_argument("output")
    merge_parser.set_defaults(func=_cmd_merge)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
