#!/usr/bin/env python3
"""Build the Word 97-2003 (.doc) edition of the user's manual from the Word edition (make manual).

docs/2068_Leap-C_Users_Manual.docx -> docs/2068_Leap-C_Users_Manual.doc, converted by LibreOffice
(`soffice --convert-to "doc:MS Word 97"`), a real binary Word file, not a renamed .docx. The result is
checked before it replaces the committed file:
  * it is an OLE2 compound file (magic D0 CF 11 E0 A1 B1 1A E1) with a WordDocument stream;
  * its text, read back by LibreOffice, is identical to the .docx's text;
  * converted back to .docx it keeps every picture, table and heading of the source.
Needs LibreOffice (soffice) on PATH; the CI does not run this, so run `make manual` whenever the manual changes.

Usage: build_manual_doc.py [manual.docx]     the .doc is written beside it (default docs/2068_Leap-C_Users_Manual.docx)"""
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "docs/2068_Leap-C_Users_Manual.docx"
OLE2 = bytes.fromhex("D0CF11E0A1B11AE1")


def soffice(profile, out, target, src):
    subprocess.run(["soffice", "--headless", "-env:UserInstallation=" + profile.as_uri(),
                    "--convert-to", target, "--outdir", str(out), str(src)],
                   check=True, capture_output=True, text=True, timeout=600)


def census(docx):
    z = zipfile.ZipFile(docx)
    x = z.read("word/document.xml").decode("utf-8")
    return {"pictures": len([n for n in z.namelist() if n.startswith("word/media/")]),
            "tables": x.count("<w:tbl>"),
            "headings": len(re.findall(r'w:pStyle w:val="Heading\d"', x))}


def main():
    docx = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCX
    out = docx.with_suffix(".doc")
    if shutil.which("soffice") is None:
        print("build_manual_doc: LibreOffice (soffice) not found; the .doc edition was NOT rebuilt", file=sys.stderr)
        return 1
    if not docx.exists():
        print("build_manual_doc: %s not found (run tools/build_manual_docx.py)" % docx, file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        profile = t / "profile"
        soffice(profile, t / "doc", "doc:MS Word 97", docx)
        doc = t / "doc" / (docx.stem + ".doc")
        data = doc.read_bytes()
        assert data[:8] == OLE2, "not an OLE2 compound file"
        assert "WordDocument".encode("utf-16-le") in data, "no WordDocument stream"
        soffice(profile, t / "txt_docx", "txt:Text (encoded):UTF8", docx)
        soffice(profile, t / "txt_doc", "txt:Text (encoded):UTF8", doc)
        a = (t / "txt_docx" / (docx.stem + ".txt")).read_text(encoding="utf-8")
        b = (t / "txt_doc" / (docx.stem + ".txt")).read_text(encoding="utf-8")
        assert a == b, "the .doc text differs from the .docx text"
        soffice(profile, t / "rt", "docx", doc)
        want, got = census(docx), census(t / "rt" / (docx.stem + ".docx"))
        assert want == got, "content lost in the .doc: %s vs %s" % (got, want)
        shutil.copyfile(doc, out)
    print("Wrote %s (%d bytes; text identical to the .docx; %d pictures, %d tables, %d headings)"
          % (out, len(data), want["pictures"], want["tables"], want["headings"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
