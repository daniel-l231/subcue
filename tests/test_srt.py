import io
import os
import unittest

from subcue import srt
from subcue.model import Cue

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class ParseTests(unittest.TestCase):
    def test_parses_fixture(self):
        with open(os.path.join(FIXTURES, "sample.srt"), encoding="utf-8") as f:
            cues = list(srt.parse(f))

        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[0], Cue(index=1, start_ms=1000, end_ms=3500, text="Hello there."))
        self.assertEqual(cues[1].text, "This is a\ntwo-line cue.")
        self.assertEqual(cues[2], Cue(index=3, start_ms=7000, end_ms=9000, text="Goodbye."))

    def test_tolerates_missing_index_line(self):
        lines = [
            "00:00:01,000 --> 00:00:02,000\n",
            "no index here\n",
        ]
        cues = list(srt.parse(lines))
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].index, 0)
        self.assertEqual(cues[0].text, "no index here")

    def test_malformed_timing_raises(self):
        lines = [
            "1\n",
            "not a timing line\n",
            "text\n",
        ]
        with self.assertRaises(ValueError):
            list(srt.parse(lines))

    def test_malformed_block_raises(self):
        lines = ["not an index or a timing line\n"]
        with self.assertRaises(ValueError):
            list(srt.parse(lines))

    def test_trailing_block_without_blank_line(self):
        # a file with no trailing newline still yields its last cue
        lines = ["1\n", "00:00:01,000 --> 00:00:02,000\n", "last cue"]
        cues = list(srt.parse(lines))
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "last cue")


class WriteTests(unittest.TestCase):
    def test_write_format(self):
        cues = [Cue(index=1, start_ms=1000, end_ms=3500, text="Hello there.")]
        out = io.StringIO()
        srt.write(cues, out)
        self.assertEqual(
            out.getvalue(),
            "1\n00:00:01,000 --> 00:00:03,500\nHello there.\n\n",
        )

    def test_renumbers_sequentially(self):
        cues = [
            Cue(index=9, start_ms=0, end_ms=1000, text="a"),
            Cue(index=2, start_ms=1000, end_ms=2000, text="b"),
        ]
        out = io.StringIO()
        srt.write(cues, out)
        written = list(srt.parse(io.StringIO(out.getvalue())))
        self.assertEqual([c.index for c in written], [1, 2])

    def test_negative_start_clamped_to_zero(self):
        cues = [Cue(index=1, start_ms=-500, end_ms=1000, text="a")]
        out = io.StringIO()
        srt.write(cues, out)
        self.assertTrue(out.getvalue().startswith("1\n00:00:00,000"))

    def test_round_trip(self):
        with open(os.path.join(FIXTURES, "sample.srt"), encoding="utf-8") as f:
            original = list(srt.parse(f))

        out = io.StringIO()
        srt.write(original, out)
        round_tripped = list(srt.parse(io.StringIO(out.getvalue())))

        self.assertEqual(
            [(c.start_ms, c.end_ms, c.text) for c in original],
            [(c.start_ms, c.end_ms, c.text) for c in round_tripped],
        )


if __name__ == "__main__":
    unittest.main()
