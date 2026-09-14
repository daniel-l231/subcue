import io
import os
import unittest

from subcue import vtt
from subcue.model import Cue

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class ParseTests(unittest.TestCase):
    def test_parses_fixture(self):
        with open(os.path.join(FIXTURES, "sample.vtt"), encoding="utf-8") as f:
            cues = list(vtt.parse(f))

        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[0], Cue(index=1, start_ms=1000, end_ms=3500, text="Hello there."))
        self.assertEqual(cues[1].text, "This is a\ntwo-line cue.")
        self.assertEqual(cues[2], Cue(index=3, start_ms=7000, end_ms=9000, text="Goodbye."))

    def test_requires_webvtt_header(self):
        lines = ["not a header\n", "\n", "00:00:01.000 --> 00:00:02.000\n", "text\n"]
        with self.assertRaises(ValueError):
            list(vtt.parse(lines))

    def test_skips_note_blocks(self):
        lines = [
            "WEBVTT\n",
            "\n",
            "NOTE this is a comment\n",
            "\n",
            "00:00:01.000 --> 00:00:02.000\n",
            "actual cue\n",
        ]
        cues = list(vtt.parse(lines))
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "actual cue")

    def test_optional_cue_identifier_line(self):
        lines = [
            "WEBVTT\n",
            "\n",
            "intro\n",
            "00:00:01.000 --> 00:00:02.000\n",
            "text\n",
        ]
        cues = list(vtt.parse(lines))
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "text")

    def test_hours_are_optional(self):
        lines = ["WEBVTT\n", "\n", "01:02.000 --> 01:05.000\n", "text\n"]
        cues = list(vtt.parse(lines))
        self.assertEqual(cues[0].start_ms, 62000)
        self.assertEqual(cues[0].end_ms, 65000)

    def test_malformed_timing_raises(self):
        lines = ["WEBVTT\n", "\n", "identifier\n", "not a timing line\n", "text\n"]
        with self.assertRaises(ValueError):
            list(vtt.parse(lines))


class WriteTests(unittest.TestCase):
    def test_write_format(self):
        cues = [Cue(index=1, start_ms=1000, end_ms=3500, text="Hello there.")]
        out = io.StringIO()
        vtt.write(cues, out)
        self.assertEqual(
            out.getvalue(),
            "WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nHello there.\n\n",
        )

    def test_round_trip(self):
        with open(os.path.join(FIXTURES, "sample.vtt"), encoding="utf-8") as f:
            original = list(vtt.parse(f))

        out = io.StringIO()
        vtt.write(original, out)
        round_tripped = list(vtt.parse(io.StringIO(out.getvalue())))

        self.assertEqual(
            [(c.start_ms, c.end_ms, c.text) for c in original],
            [(c.start_ms, c.end_ms, c.text) for c in round_tripped],
        )


if __name__ == "__main__":
    unittest.main()
