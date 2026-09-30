import codecs
import os
import tempfile
import unittest

from subcue import srt
from subcue.encoding import detect_encoding, open_text

_SRT = "1\n00:00:01,000 --> 00:00:02,000\ncafé crème\n\n"


class EncodingTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def _write(self, data: bytes) -> str:
        path = os.path.join(self._dir.name, "in.srt")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_plain_utf8(self):
        path = self._write(_SRT.encode("utf-8"))
        self.assertEqual(detect_encoding(path), "utf-8")

    def test_utf8_bom_is_stripped(self):
        path = self._write(codecs.BOM_UTF8 + _SRT.encode("utf-8"))
        self.assertEqual(detect_encoding(path), "utf-8-sig")
        with open_text(path) as f:
            cues = list(srt.parse(f))
        self.assertEqual(cues[0].index, 1)

    def test_utf16_with_bom(self):
        path = self._write(codecs.BOM_UTF16_LE + _SRT.encode("utf-16-le"))
        self.assertEqual(detect_encoding(path), "utf-16")
        with open_text(path) as f:
            self.assertEqual(list(srt.parse(f))[0].text, "café crème")

    def test_utf32_bom_is_not_mistaken_for_utf16(self):
        path = self._write(codecs.BOM_UTF32_LE + _SRT.encode("utf-32-le"))
        self.assertEqual(detect_encoding(path), "utf-32")

    def test_falls_back_to_cp1252(self):
        path = self._write(_SRT.encode("cp1252"))
        self.assertEqual(detect_encoding(path), "cp1252")
        with open_text(path) as f:
            self.assertEqual(list(srt.parse(f))[0].text, "café crème")

    def test_undefined_cp1252_byte_falls_back_to_latin1(self):
        path = self._write(b"1\n00:00:01,000 --> 00:00:02,000\nx\x81y\n\n")
        self.assertEqual(detect_encoding(path), "latin-1")

    def test_multibyte_sequence_across_chunk_boundary(self):
        # push a two-byte character across the 64 KiB read boundary
        data = b"a" * (64 * 1024 - 1) + "é".encode("utf-8") + b"\n"
        path = self._write(data)
        self.assertEqual(detect_encoding(path), "utf-8")

    def test_explicit_encoding_skips_detection(self):
        path = self._write(_SRT.encode("cp1252"))
        with open_text(path, "latin-1") as f:
            self.assertEqual(list(srt.parse(f))[0].text, "café crème")


if __name__ == "__main__":
    unittest.main()
