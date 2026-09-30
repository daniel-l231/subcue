"""Pick a text encoding for subtitle files without reading them into memory."""

import codecs
from typing import IO

_CHUNK_SIZE = 64 * 1024

# Order matters: the UTF-32 LE mark starts with the UTF-16 LE mark.
_BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def detect_encoding(path: str) -> str:
    """Return a codec name that can decode the file at `path`.

    A byte order mark wins if there is one. Otherwise the whole file is
    checked as UTF-8 in fixed-size chunks, which keeps memory flat for huge
    transcripts. Files that are not valid UTF-8 are assumed to be Windows
    code page 1252, which is what most legacy subtitle files in western
    languages use; latin-1 is the last resort because it accepts any byte.
    """
    with open(path, "rb") as f:
        head = f.read(4)
        for bom, name in _BOMS:
            if head.startswith(bom):
                return name
        f.seek(0)
        if _decodes(f, "utf-8"):
            return "utf-8"
        f.seek(0)
        if _decodes(f, "cp1252"):
            return "cp1252"
    return "latin-1"


def _decodes(f: IO[bytes], encoding: str) -> bool:
    # An incremental decoder copes with a multibyte sequence that straddles
    # a chunk boundary, which a plain bytes.decode on each chunk would not.
    decoder = codecs.getincrementaldecoder(encoding)()
    try:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                decoder.decode(b"", final=True)
                return True
            decoder.decode(chunk)
    except UnicodeDecodeError:
        return False


def open_text(path: str, encoding: str = "auto") -> IO[str]:
    """Open `path` for reading as text, detecting the encoding if asked to."""
    if encoding == "auto":
        encoding = detect_encoding(path)
    return open(path, "r", encoding=encoding)
