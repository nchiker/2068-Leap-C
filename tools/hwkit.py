"""The hardware kit (Phase 9, project_plan.md section 11): what a person with a TS2068 needs to run
docs/HARDWARE_CHECKLIST.md, built from the production images and checked on both emulators.

build/kit/
  eprom/leapc_home_27128.bin  .hex     HOME (16,384 B) for a 27128 (Intel HEX for programmers that want it)
  eprom/leapc_exrom_2764.bin  .hex     EXROM (8,192 B) for a 2764
  tapes/hN_name.tap .tzx .wav          the hardware check programs (docs/hardware/*.c)
  tapes/l1_shapes.tap .tzx .wav        (Phase 10) the example library (build/libs/: tools/lib2tape.py), for LIB "shapes"
  libs/shapes.asm                      its source
  tapes/exNN.tap .tzx .wav             the documentation's examples (tests/doc/, docs/EXAMPLES.md)
  CHECKSUMS.txt                        every file: size, SHA-256, CRC-32, the byte sum (32 and 16 bits)
  HARDWARE_CHECKLIST.md                the checklist
  EMULATOR_RESULTS.md                  what each check program shows on ZEsarUX 13.0 and Fuse 1.9.1: --verify writes
                                       it, and docs/hardware/EMULATOR_RESULTS.md, which the kit takes when it was made
                                       for the same images (their SHA-256s are in it)

The WAVs are the tapes as audio for a cassette recorder or a phone/PC line out into the EAR socket:
8-bit mono PCM at 44.1 kHz, the stock ROM's pulses at the TS2068's 3.528 MHz (tools/tapes.py Tape.to_wav,
the pulses Leap-C's own SAVE sends). --verify loads every check program's WAV in both emulators through
their tape signal inputs (ZEsarUX's real-tape input, Fuse's tape deck), compares the source, runs it
(typing keys, pressing BREAK or recording and playing the data tape where the program asks; H11: LIB "shapes"
from the library's WAV first), and decodes every WAV with fuse-utils' audio2tape (an independent decoder) when
it is installed.

Usage: hwkit.py [--verify] [--soak-minutes N]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import c2tape           # noqa: E402
import tapes            # noqa: E402

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
KIT = os.path.join(BUILD, "kit")
HW = os.path.join(ROOT, "docs", "hardware")
# (file, tape name, check id, how the emulators run it)
PROGRAMS = [("hello.c", "hello", "H1", "run"), ("keys.c", "keys", "H2", "keys"), ("hz60.c", "hz60", "H3", "run"),
            ("cont1.c", "cont1", "H4", "run"), ("cont4.c", "cont4", "H5", "run"), ("float.c", "float", "H6", "run"),
            ("sound.c", "sound", "H7", "run"), ("brk.c", "brk", "H8", "break"), ("tapedata.c", "tapedata", "H9", "tape"),
            ("soak.c", "soak", "H10", "soak"), ("lib.c", "libcheck", "H11", "lib")]
# (library, kit id): LIB "name" reads them (Phase 10); H11 needs L1
LIBRARIES = [("shapes", "L1", os.path.join("libs", "shapes.asm"))]
LIBS = os.path.join(BUILD, "libs")
KEYS_TYPED = "aZ5{|}~[]\\^"


def ihex(data, base=0):
    out = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        a = base + i
        rec = bytes([len(chunk), a >> 8 & 0xFF, a & 0xFF, 0]) + chunk
        out.append(":%s%02X" % (rec.hex().upper(), -sum(rec) & 0xFF))
    out.append(":00000001FF")
    return "\n".join(out) + "\n"


def tape_files(text, name, stem):
    blocks = c2tape.program_blocks(text, name)
    d = os.path.join(KIT, "tapes")
    open(os.path.join(d, stem + ".tap"), "wb").write(tapes.tap(blocks))
    open(os.path.join(d, stem + ".tzx"), "wb").write(tapes.tzx(blocks))
    open(os.path.join(d, stem + ".wav"), "wb").write(tapes.Tape().file(blocks).to_wav())
    return blocks


def image_ids():
    """The images' SHA-256s, as EMULATOR_RESULTS.md records them."""
    return "HOME %s, EXROM %s" % tuple(hashlib.sha256(open(os.path.join(BUILD, f), "rb").read()).hexdigest()
                                      for f in ("leapc_home.bin", "leapc_exrom.bin"))


RESULTS = os.path.join(HW, "EMULATOR_RESULTS.md")


def build_kit():
    """The kit from the images, with docs/hardware/EMULATOR_RESULTS.md if it was made for the same images."""
    res = os.path.join(KIT, "EMULATOR_RESULTS.md")
    keep = open(RESULTS).read() if os.path.exists(RESULTS) else None
    if keep and image_ids() not in keep:
        print("hwkit: %s is for other images: run --verify" % os.path.relpath(RESULTS, ROOT))
        keep = None
    shutil.rmtree(KIT, ignore_errors=True)
    for d in ("eprom", "tapes"):
        os.makedirs(os.path.join(KIT, d))
    if keep:
        open(res, "w").write(keep)
    home = open(os.path.join(BUILD, "leapc_home.bin"), "rb").read()
    exrom = open(os.path.join(BUILD, "leapc_exrom.bin"), "rb").read()
    assert len(home) == 16384 and len(exrom) == 8192, "image sizes"
    for name, data in (("leapc_home_27128", home), ("leapc_exrom_2764", exrom)):
        open(os.path.join(KIT, "eprom", name + ".bin"), "wb").write(data)
        open(os.path.join(KIT, "eprom", name + ".hex"), "w").write(ihex(data))
    tapes_made = []
    for f, name, cid, _ in PROGRAMS:
        stem = "%s_%s" % (cid.lower(), name)
        tape_files(open(os.path.join(HW, f)).read(), name, stem)
        tapes_made.append(stem)
    for p in sorted(os.listdir(os.path.join(ROOT, "tests", "doc"))):
        n = p.split("_")[-1].split(".")[0]
        stem = "ex%s" % n
        tape_files(open(os.path.join(ROOT, "tests", "doc", p)).read(), "example" + n, stem)
        tapes_made.append(stem)
    os.makedirs(os.path.join(KIT, "libs"))
    for name, lid, src in LIBRARIES:              # (make libs built them: tools/lib2tape.py)
        stem = "%s_%s" % (lid.lower(), name)
        for ext in (".tap", ".tzx", ".wav"):
            shutil.copy(os.path.join(LIBS, name + ext), os.path.join(KIT, "tapes", stem + ext))
        shutil.copy(os.path.join(ROOT, src), os.path.join(KIT, "libs"))
        tapes_made.append(stem)
    shutil.copy(os.path.join(ROOT, "docs", "HARDWARE_CHECKLIST.md"), KIT)
    write_checksums()
    return tapes_made


def write_checksums():
    lines = ["# Leap-C hardware kit: size, SHA-256, CRC-32, byte sum (32-bit and 16-bit) of every file", ""]
    for d, _, fs in sorted(os.walk(KIT)):
        for f in sorted(fs):
            if f == "CHECKSUMS.txt":
                continue
            p = os.path.join(d, f)
            data = open(p, "rb").read()
            lines.append("%-34s %8d  sha256 %s  crc32 %08X  sum %08X  sum16 %04X" % (
                os.path.relpath(p, KIT), len(data), hashlib.sha256(data).hexdigest(), zlib.crc32(data),
                sum(data) & 0xFFFFFFFF, sum(data) & 0xFFFF))
    open(os.path.join(KIT, "CHECKSUMS.txt"), "w").write("\n".join(lines) + "\n")


def decode_with_audio2tape(stem):
    """The WAV decoded by fuse-utils' audio2tape (an independent decoder): True if its ROM blocks are the
    tape's blocks, None if the tool is missing."""
    if not shutil.which("audio2tape"):
        return None
    d = os.path.join(KIT, "tapes")
    out = os.path.join(BUILD, "kit_decode_%s.tzx" % stem)
    subprocess.run(["audio2tape", os.path.join(d, stem + ".wav"), out], capture_output=True)
    want = tapes.read_tap(open(os.path.join(d, stem + ".tap"), "rb").read())
    data, p, got = open(out, "rb").read() if os.path.exists(out) else b"", 10, []
    while p < len(data):
        bid = data[p]
        if bid == 0x11:
            n = data[p + 16] | data[p + 17] << 8 | data[p + 18] << 16
            got.append(data[p + 19:p + 19 + n])
            p += 19 + n
        elif bid == 0x10:
            n = data[p + 3] | data[p + 4] << 8
            got.append(data[p + 5:p + 5 + n])
            p += 5 + n
        elif bid == 0x12:
            p += 5
        else:
            break
    if os.path.exists(out):
        os.remove(out)
    return got == want


# ============================================================================ the emulators
def zesarux_verify(soak_frames):
    from lcharness import Machine
    from shelltest import Shell, ENTER
    import tapetest
    m = Machine(BUILD, 10856)
    out = {}
    try:
        m.start()
        sh = Shell(m)
        S = m.sym
        for f, name, cid, how in PROGRAMS:
            stem = "%s_%s" % (cid.lower(), name)
            lines = c2src.lines_of(open(os.path.join(HW, f)).read())
            rate, samples = tapes.read_wav(open(os.path.join(KIT, "tapes", stem + ".wav"), "rb").read())
            if how == "lib":                    # the library's WAV, 3 s of silence, the program's: one insert (an
                lrate, lsamples = tapes.read_wav(open(os.path.join(KIT, "tapes", "l1_shapes.wav"), "rb").read())
                assert lrate == rate            # insert resets the machine, and so the library)
                samples = lsamples + bytes([0x80]) * (3 * rate) + samples
            rwa = os.path.join(m.snapdir, "kit.rwa")
            open(rwa, "wb").write(tapes.rwa_from_wav(rate, samples))
            m.tape_insert(rwa)
            sh.boot()
            r = {}
            if how == "lib":
                lmsg, _ = tapetest.command(sh, 'LIB "shapes"', invariants=False)
                r["lib"] = list(lmsg)
            msg, _ = tapetest.command(sh, 'LOAD ""', invariants=False)
            r.update(load=msg, source=sh.store() == lines)
            if how == "tape":
                r["run"] = "not run here (the cassette suite runs tape_save / tape_load; Fuse runs this one)"
            else:
                for ch in "run":
                    sh.key(ord(ch))
                if how in ("run", "lib"):
                    rep = sh.key(ENTER, maxi=2_000_000_000)
                elif how == "keys":
                    sh.key(ENTER)
                    for ch in KEYS_TYPED:
                        sh.key(ord(ch))
                    rep = sh.key(ENTER)
                elif how == "break":
                    rep, _ = sh.run_break(after=3_000_000)
                elif how == "soak":
                    m.write(S("KBD_LASTK"), ENTER)
                    m.write(S("KBD_KEYHIT"), 0xFF)
                    m.cmd("cpu-step")
                    last, done = m.w16(S("FRAMES")), 0
                    m.cmd("disable-breakpoints")        # (run_to enables them again)
                    while done < soak_frames:           # FRAMES is 16 bits: sum the steps (20M T is 286 frames)
                        m.run(20_000_000)
                        now = m.w16(S("FRAMES"))
                        done, last = done + ((now - last) & 0xFFFF), now
                    m.write(S("KBD_LASTK"), ord(" "))
                    m.write(S("KBD_KEYHIT"), 0xFF)
                    rep = sh._wait(200_000_000)
                rows = m.screen_rows()
                r["report"] = list(rep) if isinstance(rep, tuple) else rep
                r["screen"] = [x for x in rows[:22] if x]
                sh.key(ord(" "))
            out[cid] = r
    finally:
        m.stop()
    return out


def fuse_verify(soak_frames):
    from fusedrive import Fuse, BREAK, chord
    wdir = os.path.join(BUILD, "fuse", "kit")
    shutil.rmtree(wdir, ignore_errors=True)
    f = Fuse(BUILD, wdir).start()
    out = {}
    try:
        for fn, name, cid, how in PROGRAMS:
            stem = "%s_%s" % (cid.lower(), name)
            lines = c2src.lines_of(open(os.path.join(HW, fn)).read())
            r = {}
            if how == "lib":                    # LIB "shapes" from the library's WAV first
                ltzx = os.path.join(wdir, "l1_shapes.tzx")
                open(ltzx, "wb").write(tapes.tzx_from_wav(*tapes.read_wav(open(os.path.join(KIT, "tapes", "l1_shapes.wav"),
                                                                                "rb").read())))
                assert f.cmd("tape_open %s" % ltzx) == "0"
                f.command('lib "shapes"')
                r["lib"] = f.rows()[22:24]
                f.key(" ")
            tzx = os.path.join(wdir, stem + ".tzx")
            open(tzx, "wb").write(tapes.tzx_from_wav(*tapes.read_wav(open(os.path.join(KIT, "tapes", stem + ".wav"),
                                                                            "rb").read())))
            assert f.cmd("tape_open %s" % tzx) == "0"
            f.command('load ""')
            r["load"] = f.rows()[22:24]
            f.key(" ")
            r["source"] = f.store() == lines
            f.to_append_line()
            if how in ("run", "lib"):
                f.type("run", timeout=900)
            elif how == "keys":
                f.type("run")
                f.type(KEYS_TYPED, timeout=60)
            elif how == "break":
                f.chords([chord(c) for c in "run"] + [[0x100]], settle=False)
                f.wait_frames(120)
                for _ in range(20):
                    f.hold(BREAK, 5)
                    if f.at_key_wait():
                        break
            elif how == "soak":
                f.chords([chord(c) for c in "run"] + [[0x100]], settle=False)
                f.wait_frames(soak_frames, timeout=3600)
                f.hold([0x20], 5)
                f.wait(f.at_key_wait, 600, "the soak's report")
            elif how == "tape":                 # record tape_save on Fuse's deck, then play it to tape_load
                f.type("run")                   # (to the program's first getkey)
                f.cmd("tape_rec_start")
                f.key("\n", timeout=600)        # ENTER: tape_save, to the second getkey (SPACE would be BREAK)
                f.cmd("tape_rec_stop")
                rec = os.path.join(wdir, "leapdata.tzx")
                f.cmd("tape_write %s" % rec)
                f.cmd("tape_open %s" % rec)
                f.key("\n", timeout=900)        # tape_load, to the report
            rows = f.rows()
            r["report"] = rows[22:24]
            r["screen"] = [x for x in rows[:22] if x]
            f.key(" ")
            out[cid] = r
    finally:
        f.stop()
    return out


def results_md(z, u, decoded, soak_minutes):
    out = ["# Leap-C hardware kit: the check programs on the emulators (Phase 9, tools/hwkit.py --verify)", "",
           "Images: %s." % image_ids(), "",
           "Each program's WAV (tapes/) loaded through the emulator's tape signal input and run. A TS2068 should "
           "show Fuse's figures (60 Hz); ZEsarUX 13.0 emulates the TS2068 with a 50 Hz frame. The soak ran %d "
           "emulated minutes on each (ZEsarUX: at 50 Hz, so its frame count is lower)." % soak_minutes, ""]
    for fn, name, cid, how in PROGRAMS:
        out += ["## %s `%s` (%s)" % (cid, fn, how), ""]
        for emu, res in (("ZEsarUX 13.0", z), ("Fuse 1.9.1", u)):
            r = res.get(cid, {})
            out.append("- **%s:** %sLOAD %r, source %s; report %r" % (
                emu, "LIB %r; " % (r["lib"],) if "lib" in r else "", r.get("load"),
                "identical" if r.get("source") else "DIFFERENT", r.get("report", r.get("run"))))
            for line in r.get("screen", []):
                out.append("  - `%s`" % line)
        out.append("")
    if decoded is not None:
        good = [s for s, ok in decoded.items() if ok]
        out += ["## Independent decode", "", "fuse-utils' audio2tape decoded %d of %d kit WAVs to exactly their tapes' "
                "blocks%s." % (len(good), len(decoded), "" if len(good) == len(decoded) else
                               ": not " + ", ".join(s for s, ok in decoded.items() if not ok)), ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--soak-minutes", type=int, default=10)
    a = ap.parse_args()
    made = build_kit()
    print("hwkit: %s: 2 EPROM images, %d tapes (.tap, .tzx, .wav)" % (os.path.relpath(KIT, ROOT), len(made)))
    if not a.verify:
        return 0
    decoded = None
    if shutil.which("audio2tape"):
        decoded = {s: decode_with_audio2tape(s) for s in made}
        print("hwkit: audio2tape decoded %d/%d WAVs to their tapes' blocks" % (sum(1 for v in decoded.values() if v),
                                                                             len(decoded)))
    z = zesarux_verify(a.soak_minutes * 60 * 50)
    u = fuse_verify(a.soak_minutes * 60 * 60)
    text = results_md(z, u, decoded, a.soak_minutes)
    open(os.path.join(KIT, "EMULATOR_RESULTS.md"), "w").write(text)
    open(RESULTS, "w").write(text)
    json.dump(dict(zesarux=z, fuse=u, decoded=decoded), open(os.path.join(BUILD, "kit_results.json"), "w"), indent=1)
    write_checksums()
    bad = [cid for cid in z if not z[cid].get("source")] + [cid for cid in u if not u[cid].get("source")]
    want_lib = ["LIBRARY shapes: 3 FUNCTIONS"]          # (H11: the library from its WAV on both emulators)
    bad += ["%s LIB %r" % (cid, res[cid]["lib"]) for res in (z, u) for cid in res
            if "lib" in res[cid] and list(res[cid]["lib"])[:1] != want_lib]
    bad += [s for s, ok in (decoded or {}).items() if not ok]
    for cid in sorted(set(z) | set(u)):
        print("hwkit: %s ZEsarUX %r | Fuse %r" % (cid, z.get(cid, {}).get("report", z.get(cid, {}).get("run")),
                                                u.get(cid, {}).get("report")))
    print("hwkit: %s" % ("PASS" if not bad else "FAIL %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
