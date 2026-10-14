"""Fail if tracked files contain identifiers that shouldn't ship.

Generic patterns (Slack ids, artifact URLs) live here. Names of real people,
companies or internal projects go in an untracked `.clean-denylist` file
(one regex per line) so the guard itself never publishes them.
"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERIC = [r"claude\.ai/artifact/[A-Za-z0-9]{10,}", r"\b[UCD]0[A-Z0-9]{8,}\b", r"\.atlassian\.net"]
ALLOWED_FILES = {"tests/test_repo_is_clean.py", "LICENSE"}


def patterns():
    deny = ROOT / ".clean-denylist"
    extra = [l.strip() for l in deny.read_text().splitlines() if l.strip() and not l.startswith("#")] if deny.exists() else []
    return GENERIC + extra


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f and f not in ALLOWED_FILES]


def test_no_personal_or_company_identifiers():
    hits = []
    for rel in tracked_files():
        text = (ROOT / rel).read_text(errors="ignore")
        for pat in patterns():
            for m in re.finditer(pat, text, re.I):
                hits.append(f"{rel}: {m.group(0)}")
    assert not hits, "\n".join(hits)
