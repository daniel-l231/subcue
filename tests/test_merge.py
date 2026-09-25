import unittest

from subcue.merge import merge_streams
from subcue.model import Cue


def _cue(start_ms, text):
    return Cue(index=0, start_ms=start_ms, end_ms=start_ms + 500, text=text)


class MergeTests(unittest.TestCase):
    def test_interleaves_by_start_time(self):
        first = [_cue(0, "a1"), _cue(2000, "a2"), _cue(4000, "a3")]
        second = [_cue(1000, "b1"), _cue(3000, "b2")]

        merged = list(merge_streams(first, second))

        self.assertEqual(
            [c.text for c in merged], ["a1", "b1", "a2", "b2", "a3"]
        )

    def test_ties_keep_first_stream_before_second(self):
        first = [_cue(1000, "a")]
        second = [_cue(1000, "b")]

        merged = list(merge_streams(first, second))

        self.assertEqual([c.text for c in merged], ["a", "b"])

    def test_merges_more_than_two_streams(self):
        first = [_cue(0, "a")]
        second = [_cue(1000, "b")]
        third = [_cue(500, "c")]

        merged = list(merge_streams(first, second, third))

        self.assertEqual([c.text for c in merged], ["a", "c", "b"])

    def test_empty_stream_is_ignored(self):
        first = [_cue(0, "a"), _cue(1000, "b")]

        merged = list(merge_streams(first, []))

        self.assertEqual([c.text for c in merged], ["a", "b"])

    def test_lazy_over_iterators(self):
        # merge_streams must work with one-shot iterators, not just lists,
        # since that's what srt.parse hands it.
        first = iter([_cue(0, "a")])
        second = iter([_cue(1000, "b")])

        merged = list(merge_streams(first, second))

        self.assertEqual([c.text for c in merged], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
