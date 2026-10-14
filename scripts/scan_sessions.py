#!/usr/bin/env python3
"""Summarise Claude Code sessions with new activity, for the Morning Desk.

Reads local transcripts (CLAUDE_PROJECTS_DIR, default ~/.claude/projects) and prints
JSON: {"scannedAt", "since", "sessions": [...]}. Keeps short, redacted excerpts only.

Usage:
  scan_sessions.py [--since-hours N] [--no-state]   scan; records the scan as pending
  scan_sessions.py --commit                         mark the pending scan done (run after the desk is written)

Timestamps without a timezone are read as local time.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

DESK_HOME = Path(os.environ.get("MORNING_DESK_HOME", "~/.config/morning-desk")).expanduser()
PROJECTS = Path(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()
STATE = DESK_HOME / "last_scan.json"
PENDING = DESK_HOME / "last_scan.pending.json"
IGNORE = DESK_HOME / "ignore.txt"

SECRET = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|xox[abprs]-[A-Za-z0-9-]+|xapp-[A-Za-z0-9-]+|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{20,})"
)
PR = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError, TypeError):
        return None


def clean(s, n):
    s = SECRET.sub("[redacted]", re.sub(r"\s+", " ", s or "")).strip()
    return s[:n]


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(c.get("text") or "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    return ""


def scan(path):
    path = Path(path)
    s = {"id": path.stem, "title": None, "cwd": None, "branch": None, "prompts": [],
         "lastAssistant": "", "prs": set(), "files": set(), "firstAt": None, "lastAt": None}
    with path.open(errors="ignore") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            t = o.get("type")
            ts = o.get("timestamp")
            if ts:
                s["firstAt"] = s["firstAt"] or ts
                s["lastAt"] = ts
            if t == "ai-title":
                s["title"] = o.get("aiTitle") or o.get("title") or s["title"]
            s["cwd"] = o.get("cwd") or s["cwd"]
            s["branch"] = o.get("gitBranch") or s["branch"]
            msg = o.get("message")
            msg = msg if isinstance(msg, dict) else {}
            if t == "user" and not o.get("isMeta") and not o.get("isSidechain"):
                c = text_of(msg.get("content")).strip()
                if c and not c.startswith("<"):
                    s["prompts"].append(clean(c, 220))
            if t == "assistant" and not o.get("isSidechain"):
                content = msg.get("content")
                txt = text_of(content).strip()
                if txt:
                    s["lastAssistant"] = txt
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") in ("Write", "Edit"):
                            inp = c.get("input")
                            fp = inp.get("file_path") if isinstance(inp, dict) else None
                            if isinstance(fp, str):
                                s["files"].add(fp)
            s["prs"].update(PR.findall(line))
    if not s["prompts"]:
        return None
    cwd = s["cwd"]
    return {
        "id": s["id"], "title": s["title"], "repo": (cwd or "").rstrip("/").split("/")[-1], "cwd": cwd,
        "branch": s["branch"], "firstAt": s["firstAt"], "lastAt": s["lastAt"],
        "promptCount": len(s["prompts"]), "firstPrompt": s["prompts"][0], "recentPrompts": s["prompts"][-4:],
        "lastAssistant": clean(s["lastAssistant"], 700), "prs": sorted(s["prs"])[-8:],
        "filesTouched": [clean(f, 300) for f in sorted(s["files"])[-10:]],
        "resume": f'cd "{cwd}" && claude --resume {s["id"]}' if cwd else f"claude --resume {s['id']}",
    }


def collect(root, since, ignored):
    out = []
    for f in Path(root).glob("*/*.jsonl"):
        if f.stem in ignored or f.stat().st_mtime <= since:
            continue
        try:
            r = scan(f)
        except Exception:  # one odd file must not hide every other session
            continue
        last = parse_ts(r["lastAt"]) if r and r["lastAt"] else None
        if r and last and last > since:
            out.append(r)
    out.sort(key=lambda r: r["lastAt"] or "", reverse=True)
    return out


def read_state():
    try:
        return json.loads(STATE.read_text()).get("scannedAt")
    except (OSError, ValueError, AttributeError):
        return None


def main(argv):
    ap = argparse.ArgumentParser(description="Summarise Claude Code sessions for the Morning Desk.")
    ap.add_argument("--since-hours", type=float)
    ap.add_argument("--no-state", action="store_true")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args(argv)
    if args.commit:
        if PENDING.exists():
            PENDING.replace(STATE)
        return
    since = None
    if args.since_hours is not None:
        since = time.time() - args.since_hours * 3600
    elif not args.no_state:
        since = read_state()
    since = since or time.time() - 24 * 3600
    try:
        ignored = set(IGNORE.read_text().split())
    except OSError:
        ignored = set()
    now = time.time()
    print(json.dumps({"scannedAt": now, "since": since, "sessions": collect(PROJECTS, since, ignored)}, indent=1))
    if not args.no_state:
        DESK_HOME.mkdir(parents=True, exist_ok=True)
        PENDING.write_text(json.dumps({"scannedAt": now}))

if __name__ == "__main__":
    main(sys.argv[1:])
