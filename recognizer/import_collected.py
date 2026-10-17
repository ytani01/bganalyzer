"""Add the misread pairs of collected/ to samples/collected-*, and merge the PR (TODO-114).

    BG_IMPORT=1 uv run python recognizer/collected.py collected --force   # measures, then this

collected.py starts it after measuring, with the pairs it found misread, on a server with BG_IMPORT set
(the development machine only: anyone can send pairs to the Pi). It works in a worktree of origin/main
of its own, so the checkout the server runs from is not touched. Up to MAX pairs a time, the oldest
first: the rest go in the next time. Skipped: a pair whose id is in samples/ already, a photo sent
before under another name, a photo that cannot be read. Nothing is added while a PR of an earlier time
is open (its checks failed, it conflicts with main, or the service was restarted while waiting: someone has to
look at it, and merge or close it).
The photo is painted black outside the truth's corners (its size and the corners stay), and written
again without EXIF; of the truth, only the fields the samples have go in (anyone can send one).
The PR is brought up to date with main and merged when its checks pass; otherwise it is left open.
What it did goes to import.log next to the pairs.
"""
import hashlib, json, re, signal, subprocess, sys, tempfile, time
from pathlib import Path

import cv2
import numpy as np

MAX = 10
REPO = Path(__file__).resolve().parent.parent
BRANCH = "claude/collected-import-"
ROW = re.compile(r"^\| (?:Pi に)?集めた写真 .*$", re.M)   # the row of samples/collected-* in recognizer/README.md


def sample_id(name):
    """user-<time>-<id>.truth.json -> <id> (the names the samples have been given)."""
    return name.removesuffix(".truth.json").rsplit("-", 1)[-1]


def photo(d, name):
    return d / (name.removesuffix(".truth.json") + Path(json.loads((d / name).read_text())["image"]).suffix)


def pick(d, names, samples):
    """The pairs to add, the oldest first, up to MAX: not in samples/ yet by id, no photo sent before
    under another name (same bytes as a pair already added, or as a photo in samples/), readable."""
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    added = lambda n: (samples / f"collected-{sample_id(n)}.truth.json").exists()
    seen = {sha(p) for p in samples.glob("*") if p.suffix in (".jpg", ".png")}
    seen |= {sha(photo(d, n)) for n in (p.name for p in d.glob("user-*.truth.json")) if added(n)}
    out, ids = [], set()
    for n in sorted(names, key=lambda n: (d / n).stat().st_mtime):
        h, i = sha(photo(d, n)), sample_id(n)
        if len(out) < MAX and i and i not in ids and h not in seen and cv2.imread(str(photo(d, n))) is not None:
            seen.add(h), ids.add(i)
            out.append(n)
    return out


def paint(img, corners):
    """The photo with everything outside the board black."""
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(mask, [np.round(np.array(corners)).astype(np.int32)], 255)
    out = img.copy()
    out[mask == 0] = 0
    return out


def clean(t):
    """The fields the samples have, of the types they have (collected.valid has checked the rest)."""
    is_int = lambda v: type(v) is int
    out = {k: t[k] for k in ("corners_TL_TR_BR_BL", "home", "points", "bar_white", "bar_black", "dice") if k in t}
    if t.get("side") in ("right", "left"):   # taken from beside the board (TODO-120)
        out["side"] = t["side"]
    out |= {k: t[k] for k in ("bottom_colour", "off_white", "off_black", "cube_value") if is_int(t.get(k))}
    if isinstance(t.get("cube"), dict):
        out["cube"] = {"at": t["cube"]["at"]} | ({"value": t["cube"]["value"]} if is_int(t["cube"].get("value")) else {})
    if isinstance(t.get("read"), dict):
        r = t["read"]
        out["read"] = {k: r[k] for k in ("points", "bar_white", "bar_black")
                       if is_int(r.get(k)) or (isinstance(r.get(k), list) and all(map(is_int, r[k])))}
    if isinstance(t.get("fixed_points"), list) and all(map(is_int, t["fixed_points"])):
        out["fixed_points"] = t["fixed_points"]
    return out


def add(d, name, samples):
    """Write one pair to samples/ as collected-<id>; returns the new name."""
    t = json.loads((d / name).read_text())
    suffix = Path(t["image"]).suffix
    new = f"collected-{sample_id(name)}"
    cv2.imwrite(str(samples / (new + suffix)), paint(cv2.imread(str(photo(d, name))), t["corners_TL_TR_BR_BL"]), [cv2.IMWRITE_JPEG_QUALITY, 95])
    note = f"Collected on the server ({time.strftime('%Y-%m-%d')}) and added automatically: the board as corrected by hand."
    (samples / (new + ".truth.json")).write_text(json.dumps({"image": new + suffix, "note": note} | clean(t), ensure_ascii=False))
    return new


def table_row(wt):
    """The README row of samples/collected-*, from the baseline."""
    base = json.loads((wt / "recognizer/accuracy_baseline.json").read_text())
    got = [r["points"] for k, r in base.items() if k.startswith("collected-")]
    ver = re.search(r'__version__ = "(.+)"', (wt / "recognizer/board.py").read_text())[1]
    return (f"| 集めた写真 {len(got)}枚（`samples/collected-*`、ユーザーがスマホで直した盤面。実物の盤・配信の画面・アプリの画面。"
            f"読み違いのある組を自動で取り込む） | {24 * len(got)}ポイント中 {sum(got)}（recognizer {ver}、{time.strftime('%Y-%m-%d')}） | － |")


def run(d, names):
    d = Path(d)
    with open(d / "import.log", "a") as f:
        log = lambda m: print(time.strftime("%Y-%m-%d %H:%M"), m, file=f, flush=True)
        try:
            _run(d, names, log)
        except BaseException as e:   # SystemExit too: the service was restarted
            log(f"failed: {e!r}")
            raise


def _run(d, names, log):
    git = lambda *a, cwd=REPO: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout
    gh = lambda *a: subprocess.run(["gh", *a], cwd=REPO, capture_output=True, text=True)
    prs = gh("pr", "list", "--state", "open", "--json", "headRefName,url")
    if prs.returncode:
        return log(f"could not list the PRs: {prs.stderr.strip()}")
    if left := [p["url"] for p in json.loads(prs.stdout) if p["headRefName"].startswith(BRANCH)]:
        return log(f"nothing added while {' '.join(left)} is open")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))   # a restart of the service: still remove the worktree
    git("fetch", "-q", "origin", "main")
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "wt"
        branch = BRANCH + time.strftime("%Y%m%d-%H%M%S")
        git("worktree", "add", "-q", "-b", branch, str(wt), "origin/main")
        try:
            todo = pick(d, names, wt / "samples")
            if not todo:
                return log("nothing to add")
            added = [add(d, n, wt / "samples") for n in todo]
            # this venv with the worktree's code (a venv of its own would mean installing everything again)
            subprocess.run([sys.executable, "recognizer/check_accuracy.py", "--update"], cwd=wt, check=True, capture_output=True)
            readme = wt / "recognizer/README.md"
            text, n = ROW.subn(lambda _: table_row(wt), readme.read_text(), count=1)
            if not n:
                return log("the row of samples/collected-* is not in recognizer/README.md: nothing added")
            readme.write_text(text)
            git("add", "samples", "recognizer", cwd=wt)
            git("commit", "-q", "-m", f"feat(samples): 集めた写真 {len(added)} 組を自動で取り込む\n\n" + "\n".join(added), cwd=wt)
            git("push", "-q", "-u", "origin", branch, cwd=wt)
            made = gh("pr", "create", "--head", branch, "--fill-first", "--body",
                      "collected/ の読み違いのある組を自動で取り込んだ（recognizer/import_collected.py）。\n\n" + "\n".join(f"- {a}" for a in added))
            if made.returncode:
                git("push", "-q", "origin", "--delete", branch)
                return log(f"could not make the PR: {made.stderr.strip()}")
            url = made.stdout.strip()
            log(f"{url}: {' '.join(added)}")
            merge(url, gh, log)
        finally:
            git("worktree", "remove", "--force", str(wt))
            git("branch", "-q", "-D", branch)


def merge(url, gh, log):
    """Merge when the checks pass on the latest main (CLAUDE.md の「共同開発」); left open otherwise.
    The branch goes with the merge (the repository deletes merged branches)."""
    head = lambda: json.loads(gh("pr", "view", url, "--json", "headRefOid").stdout)["headRefOid"]
    while True:
        for _ in range(20):   # until the checks show up
            time.sleep(30)
            checks = gh("pr", "checks", url, "--watch", "--fail-fast", "-i", "30")
            if "no checks reported" not in checks.stderr:
                break
        if checks.returncode:
            return log(f"{url}: checks failed, left open")
        sha = head()
        if (up := gh("pr", "update-branch", url)).returncode:
            return log(f"{url}: does not go onto main ({up.stderr.strip()}), left open")
        time.sleep(10)   # for the new head to show
        if head() == sha:   # main had not moved: these checks are of the latest main
            break
    merged = gh("pr", "merge", url, "--merge", "--match-head-commit", sha)
    log(f"{url}: " + ("merged" if merged.returncode == 0 else f"not merged, left open: {merged.stderr.strip()}"))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2:])
