#!/usr/bin/env python3
"""Vendored-platform delta check (project_plan.md section 1.4).

platform/MANIFEST lists every vendored file: its sha256 at the V2 reference tag, its current
sha256, and either `pristine` or the delta ids applied to it. Each delta is a unified diff in
platform/deltas/<file>.patch (upstream -> current).

Checks:
  1. every file under platform/ (except UPSTREAM.md, MANIFEST, deltas/) is listed, and vice versa;
  2. a pristine file's current hash equals its upstream hash;
  3. a delta file's current hash is the recorded one, and reverse-applying its patch reproduces
     exactly the upstream hash (so the patch is the complete, exact delta);
  4. with --v2-repo (default $LEAPC_V2_REPO, else ~/2068-Leap, when it exists), the upstream hashes are re-derived from
     the tag with `git show` (read-only).

Cuts (Phase 11, M11-tape: delta D20/D21). A delta may remove upstream text that must not be reproduced in this
repository (V2's port of the stock ROM's tape routines and block-graphics sequence: NOTICE). Such a file has
platform/deltas/<file>.cut beside its patch: `cut FIRST LAST SHA256 reason` lines give the removed upstream line
ranges (1-based, inclusive) with the sha256 of each range's bytes, and `base SHA256` the hash of the upstream file
with the ranges removed. The patch is then the delta from that base to the current file, so it holds none of the
removed lines; check 3 reverse-applies it to the base hash, and check 4 (with the V2 repository) also removes the
ranges from the tag's file and checks the base hash and each range's hash.

Usage: check_platform.py [--v2-repo DIR | --no-v2] [--update]
--update rewrites MANIFEST current hashes and the patches from the V2 tag (needs the repo)."""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAT = os.path.join(ROOT, "platform")
TAG = "v2.0.1-emu.1"
SKIP = {"UPSTREAM.md", "MANIFEST"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_manifest():
    rows = {}
    for line in open(os.path.join(PLAT, "MANIFEST")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        up, cur, path, status = line.split(None, 3)
        rows[path] = (up, cur, status)
    return rows


def platform_files():
    out = []
    for d, _, fs in os.walk(PLAT):
        rel = os.path.relpath(d, PLAT)
        if rel.split(os.sep)[0] == "deltas":
            continue
        for f in fs:
            p = os.path.normpath(os.path.join(rel, f))
            if p not in SKIP:
                out.append(p)
    return sorted(out)


def upstream_bytes(repo, path):
    return subprocess.run(["git", "-C", repo, "show", "%s:%s" % (TAG, path)], check=True,
                          capture_output=True).stdout


def patch_path(path):
    return os.path.join(PLAT, "deltas", path.replace("/", "__") + ".patch")


def cut_path(path):
    return os.path.join(PLAT, "deltas", path.replace("/", "__") + ".cut")


def read_cut(path):
    """(base sha256, [(first, last, sha256)]) of the file's cut record, or None."""
    if not os.path.exists(cut_path(path)):
        return None
    base, cuts = None, []
    for line in open(cut_path(path)):
        f = line.split()
        if not f or f[0].startswith("#"):
            continue
        if f[0] == "base":
            base = f[1]
        elif f[0] == "cut":
            cuts.append((int(f[1]), int(f[2]), f[3]))
    return base, cuts


def apply_cuts(up, cuts):
    """The upstream bytes without the cut line ranges; and the list of each range's sha256."""
    lines = up.splitlines(keepends=True)
    keep, hashes, drop = [], [], set()
    for a, z, _ in cuts:
        hashes.append(sha(b"".join(lines[a - 1:z])))
        drop.update(range(a - 1, z))
    keep = [l for i, l in enumerate(lines) if i not in drop]
    return b"".join(keep), hashes


def reverse_apply(path, current):
    """Upstream text reconstructed by reverse-applying the file's patch to its current text."""
    with tempfile.TemporaryDirectory() as t:
        f = os.path.join(t, "file")
        open(f, "wb").write(current)
        r = subprocess.run(["patch", "-s", "-R", "-f", "--no-backup-if-mismatch", f, patch_path(path)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return None
        return open(f, "rb").read()


def update(repo):
    rows = read_manifest()
    lines = ["# sha256-at-%s  sha256-current  path  status" % TAG]
    for p in platform_files():
        up = upstream_bytes(repo, p)
        cur = open(os.path.join(PLAT, p), "rb").read()
        cut = read_cut(p)
        src = apply_cuts(up, cut[1])[0] if cut else up
        status = rows.get(p, (None, None, "pristine"))[2]
        if up == cur:
            status = "pristine"
            if os.path.exists(patch_path(p)):
                os.remove(patch_path(p))
        else:
            if status == "pristine":
                sys.exit("update: %s differs from the tag but MANIFEST says pristine; record its delta ids first" % p)
            with tempfile.TemporaryDirectory() as t:
                a = os.path.join(t, "a")
                open(a, "wb").write(src)
                d = subprocess.run(["diff", "-u", "--label", "a/" + p, "--label", "b/" + p, a,
                                    os.path.join(PLAT, p)], capture_output=True).stdout
            os.makedirs(os.path.dirname(patch_path(p)), exist_ok=True)
            open(patch_path(p), "wb").write(d)
        lines.append("%s %s %s %s" % (sha(up), sha(cur), p, status))
    open(os.path.join(PLAT, "MANIFEST"), "w").write("\n".join(lines) + "\n")
    print("MANIFEST updated")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-repo", default=os.environ.get("LEAPC_V2_REPO", os.path.expanduser("~/2068-Leap")))
    ap.add_argument("--no-v2", action="store_true")
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args()
    if a.update:
        update(a.v2_repo)
        return 0
    use_repo = not a.no_v2 and os.path.isdir(os.path.join(a.v2_repo, ".git"))
    rows = read_manifest()
    files = platform_files()
    errs = []
    for p in sorted(set(files) - set(rows)):
        errs.append("%s: not in MANIFEST" % p)
    for p in sorted(set(rows) - set(files)):
        errs.append("%s: in MANIFEST but missing" % p)
    npristine = ndelta = 0
    for p in files:
        if p not in rows:
            continue
        up, cur, status = rows[p]
        data = open(os.path.join(PLAT, p), "rb").read()
        cut = read_cut(p)
        if use_repo:
            tagged = upstream_bytes(a.v2_repo, p)
            if sha(tagged) != up:
                errs.append("%s: MANIFEST upstream hash differs from %s in %s" % (p, TAG, a.v2_repo))
            if cut:
                base, hashes = apply_cuts(tagged, cut[1])
                if sha(base) != cut[0] or hashes != [h for _, _, h in cut[1]]:
                    errs.append("%s: its cut record does not match %s" % (p, TAG))
        if status == "pristine":
            npristine += 1
            if sha(data) != up:
                errs.append("%s: modified, but MANIFEST lists it as pristine (unlisted delta)" % p)
            continue
        ndelta += 1
        if sha(data) != cur:
            errs.append("%s: changed since its delta (%s) was recorded" % (p, status))
        if not os.path.exists(patch_path(p)):
            errs.append("%s: no patch file for %s" % (p, status))
            continue
        orig = reverse_apply(p, data)
        if orig is None or sha(orig) != (cut[0] if cut else up):
            errs.append("%s: its patch does not reproduce the upstream file" % p)
    for e in errs:
        print("PLATFORM ERROR: " + e, file=sys.stderr)
    if errs:
        return 1
    print("platform check: OK (%d pristine, %d with recorded deltas%s)" % (
        npristine, ndelta, ", upstream hashes verified against %s %s" % (a.v2_repo, TAG) if use_repo else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
