# Morning Desk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `viveknigam3003/morning-desk`, a public Claude Code plugin that sets up a private Morning Desk page for any user, keeps it in sync with Slack, GitHub, their ticket tracker and their Claude sessions, and drafts their daily update in their own style.

**Architecture:** A single repo that is both a plugin marketplace and the plugin. Behaviour lives in skills and commands (Markdown instructions Claude follows); the only code is a stdlib Python session scanner and a static HTML page template that becomes each user's private claude.ai artifact (capabilities `db` + `sample`). Per-user state lives in `~/.config/morning-desk/` and in the user's own artifact database.

**Tech Stack:** Claude Code plugin format (`.claude-plugin/plugin.json`, `marketplace.json`, `commands/*.md`, `skills/*/SKILL.md`), Python 3.9+ stdlib, pytest, vanilla HTML/JS, Node (only for `node --check` in tests/CI), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-14-morning-desk-design.md`

## Global Constraints

- Never send, post, react or save drafts in Slack; never comment on or edit tickets or GitHub unless the user turns that on in config.
- `writes.close_merged_tickets: false` by default; it is the only write action that can be enabled in v1.
- Never reopen items the user marked done or won't do; treat their notes as instructions.
- Skip personal, HR and career topics, in both Slack and sessions; add such sessions to `ignore.txt`.
- Never copy secrets into the desk.
- Updates are short and crisp (3–5 workstreams, one sentence each, ≤2 sub-points), Markdown with links, facts only.
- Pin every db write to the version read; on conflict, re-read and merge.
- No Slack user/channel ids, workspace domains, tracker sites or ids, artifact URLs, people's names, company or product names, or learned style from the original setup may appear anywhere in the repo.
- Scanner: Python 3 stdlib only.
- Ticket trackers are pluggable (jira, clickup, devrev, linear, github-issues, other); nothing may assume Jira.
- Cloud routines are out of scope.

## Review Focus

- A transcript with malformed or truncated JSON lines (a session still being written) must be skipped line by line, never crash the scanner. → Task 2 `test_malformed_lines_are_skipped`.
- `lastAt` timestamps with `Z`, with `+00:00`, or without milliseconds must all filter correctly against `since`. → Task 2 `test_timestamp_formats`.
- Fine-grained GitHub tokens (`github_pat_…`), Slack app tokens (`xapp-…`) and Anthropic keys (`sk-ant-…`) in prompts must be redacted, not just classic `ghp_`/`sk-`. → Task 2 `test_redacts_modern_token_shapes`.
- A desk whose `meta/config` is missing (fresh install, or setup interrupted) must still render and produce a sensible daily-update prompt with neutral defaults. → Task 3 `test_template_has_neutral_defaults`.
- A user with no ticket tracker configured must get a refresh that silently skips tickets rather than erroring or inventing Jira links. → Task 5 `test_refresh_skill_handles_missing_tracker`.

---

## File Structure

```
.claude-plugin/marketplace.json   # marketplace listing the one plugin
.claude-plugin/plugin.json        # plugin manifest
commands/desk-setup.md            # /desk-setup
commands/desk-refresh.md          # /desk-refresh
commands/desk-sync.md             # /desk-sync
skills/morning-desk/SKILL.md      # router + standing rules
skills/desk-setup/SKILL.md        # onboarding + publish page
skills/desk-refresh/SKILL.md      # catch-up into the desk
skills/desk-sync/SKILL.md         # 30-min loop (CLI) / Scheduled Task (desktop)
skills/daily-update/SKILL.md      # draft + learn style
templates/morning-desk.html       # the page, de-personalised, reads meta/config
templates/config.example.yaml     # documented example of ~/.config/morning-desk/config.yaml
templates/style.default.md        # starting style for new users
scripts/scan_sessions.py          # session scanner
tests/conftest.py
tests/fixtures/                   # sample transcripts
tests/test_scan_sessions.py
tests/test_template.py
tests/test_repo_is_clean.py
tests/test_plugin_layout.py
docs/data-model.md
docs/privacy.md
README.md
.github/workflows/ci.yml
.gitignore
```

---

### Task 1: Plugin skeleton and layout tests

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.gitignore`, `tests/test_plugin_layout.py`

**Interfaces:**
- Produces: plugin name `morning-desk`; marketplace name `morning-desk`; `tests/test_plugin_layout.py::frontmatter(path) -> dict` helper reused in Task 5.

- [ ] **Step 1: Write the failing test**

`tests/test_plugin_layout.py`:
```python
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def frontmatter(path):
    """Parse the simple `key: value` YAML frontmatter used by commands and skills."""
    text = pathlib.Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_manifests_are_valid_json_and_consistent():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == "morning-desk"
    assert plugin["license"] == "MIT"
    assert market["plugins"][0]["name"] == plugin["name"]
    assert market["plugins"][0]["source"] == "./"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_plugin_layout.py -v`
Expected: FAIL with `FileNotFoundError` for `.claude-plugin/plugin.json`.

- [ ] **Step 3: Write the manifests and .gitignore**

`.claude-plugin/plugin.json`:
```json
{
  "name": "morning-desk",
  "displayName": "Morning Desk",
  "version": "0.1.0",
  "description": "A private morning triage desk for Claude Code: one page with what needs you across Slack, GitHub, your ticket tracker and your Claude sessions, kept current by Claude, plus a daily update drafted in your style. Never sends anything.",
  "author": { "name": "Vivek Nigam" },
  "homepage": "https://github.com/viveknigam3003/morning-desk",
  "repository": "https://github.com/viveknigam3003/morning-desk",
  "license": "MIT",
  "keywords": ["dashboard", "standup", "daily-update", "slack", "github", "triage", "artifact"]
}
```

`.claude-plugin/marketplace.json`:
```json
{
  "name": "morning-desk",
  "owner": { "name": "Vivek Nigam" },
  "plugins": [
    {
      "name": "morning-desk",
      "source": "./",
      "description": "Private morning triage desk and daily-update drafter for Claude Code."
    }
  ]
}
```

`.gitignore`:
```
__pycache__/
.pytest_cache/
*.pyc
.DS_Store
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_plugin_layout.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin .gitignore tests/test_plugin_layout.py
git commit -m "feat: add plugin and marketplace manifests"
```

---

### Task 2: Session scanner

**Files:**
- Create: `scripts/scan_sessions.py`, `tests/conftest.py`, `tests/fixtures/` (written by conftest), `tests/test_scan_sessions.py`
- Source to port: `~/.claude/desk/scan_sessions.py` (read it first; keep behaviour, change paths and add the fixes below)

**Interfaces:**
- Produces (importable as `scripts.scan_sessions` with `sys.path` insert, or run as a script):
  - `DESK_HOME = Path(os.environ.get("MORNING_DESK_HOME", "~/.config/morning-desk")).expanduser()`
  - `PROJECTS = Path(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()`
  - `parse_ts(s: str) -> float | None` — ISO 8601 with `Z`/offset, with or without fractional seconds → epoch seconds.
  - `clean(s: str, n: int) -> str` — collapse whitespace, redact secrets, truncate.
  - `scan(path: Path) -> dict | None` — one session summary, or None if it has no real user prompts.
  - `collect(root: Path, since: float, ignored: set[str]) -> list[dict]` — summaries with `lastAt` after `since`, newest first.
  - CLI: `scan_sessions.py [--since-hours N] [--no-state]`; state in `DESK_HOME/last_scan.json`, ignore list in `DESK_HOME/ignore.txt`.
  - Summary keys: `id, title, repo, cwd, branch, firstAt, lastAt, promptCount, firstPrompt, recentPrompts, lastAssistant, prs, filesTouched, resume`.

- [ ] **Step 1: Write fixtures and failing tests**

`tests/conftest.py`:
```python
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def write_session(dirpath, sid, lines):
    p = pathlib.Path(dirpath) / f"{sid}.jsonl"
    with p.open("w") as fh:
        for line in lines:
            fh.write(line if isinstance(line, str) else json.dumps(line))
            fh.write("\n")
    return p


def user(text, ts, **extra):
    return {"type": "user", "timestamp": ts, "cwd": "/home/u/code/app", "gitBranch": "main",
            "message": {"role": "user", "content": text}, **extra}


def assistant(text, ts):
    return {"type": "assistant", "timestamp": ts,
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


@pytest.fixture
def projects(tmp_path):
    root = tmp_path / "projects" / "-home-u-code-app"
    root.mkdir(parents=True)
    return root
```

`tests/test_scan_sessions.py`:
```python
from conftest import assistant, user, write_session

import scan_sessions as ss


def test_scan_summarises_a_session(projects):
    p = write_session(projects, "aaaaaaaa-1111", [
        {"type": "ai-title", "aiTitle": "Fix login bug"},
        user("Fix the login bug", "2026-10-14T08:00:00.000Z"),
        assistant("Opened https://github.com/acme/app/pull/42 for it.", "2026-10-14T08:05:00.000Z"),
    ])
    s = ss.scan(p)
    assert s["title"] == "Fix login bug"
    assert s["repo"] == "app"
    assert s["branch"] == "main"
    assert s["prs"] == ["https://github.com/acme/app/pull/42"]
    assert s["resume"] == 'cd "/home/u/code/app" && claude --resume aaaaaaaa-1111'


def test_meta_and_sidechain_prompts_are_ignored(projects):
    p = write_session(projects, "bbbb", [
        user("<command-name>/foo</command-name>", "2026-10-14T08:00:00Z"),
        user("internal", "2026-10-14T08:01:00Z", isMeta=True),
        user("subagent work", "2026-10-14T08:02:00Z", isSidechain=True),
    ])
    assert ss.scan(p) is None


def test_malformed_lines_are_skipped(projects):
    p = write_session(projects, "cccc", [
        "{not json",
        user("Real prompt", "2026-10-14T08:00:00Z"),
        '{"type": "user", "timestamp": "2026-10-14T08:0',
    ])
    s = ss.scan(p)
    assert s["promptCount"] == 1


def test_timestamp_formats():
    a = ss.parse_ts("2026-10-14T08:00:00.123Z")
    b = ss.parse_ts("2026-10-14T08:00:00+00:00")
    c = ss.parse_ts("2026-10-14T13:30:00+05:30")
    assert a is not None and abs(a - b) < 1 and abs(b - c) < 1
    assert ss.parse_ts("garbage") is None


def test_redacts_modern_token_shapes():
    for secret in ["github_pat_11ABCDEFG0123456789_abcdefghijklmnopqrstuvwxyz",
                   "xapp-1-A0123-4567-abcdef", "sk-ant-api03-abcdefghijklmnop",
                   "ghp_abcdefghijklmnopqrstuvwxyz0123", "AKIAABCDEFGHIJKLMNOP"]:
        assert secret not in ss.clean(f"token {secret} here", 500)


def test_collect_filters_by_activity_and_ignore_list(projects):
    write_session(projects, "old1", [user("old work", "2026-10-01T08:00:00Z")])
    write_session(projects, "new1", [user("new work", "2026-10-14T08:00:00Z")])
    write_session(projects, "skip", [user("personal", "2026-10-14T09:00:00Z")])
    since = ss.parse_ts("2026-10-10T00:00:00Z")
    out = ss.collect(projects.parent, since, {"skip"})
    assert [s["id"] for s in out] == ["new1"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_scan_sessions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scan_sessions'`.

- [ ] **Step 3: Implement the scanner**

`scripts/scan_sessions.py`:
```python
#!/usr/bin/env python3
"""Summarise Claude Code sessions with new activity, for the Morning Desk.

Reads local transcripts (CLAUDE_PROJECTS_DIR, default ~/.claude/projects) and prints
JSON: {"scannedAt", "since", "sessions": [...]}. Keeps short, redacted excerpts only.
Usage: scan_sessions.py [--since-hours N] [--no-state]
"""
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
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
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
            msg = o.get("message") or {}
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
                            fp = (c.get("input") or {}).get("file_path")
                            if fp:
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
        "filesTouched": sorted(s["files"])[-10:],
        "resume": f'cd "{cwd}" && claude --resume {s["id"]}' if cwd else f"claude --resume {s['id']}",
    }


def collect(root, since, ignored):
    out = []
    for f in Path(root).glob("*/*.jsonl"):
        if f.stem in ignored or f.stat().st_mtime <= since:
            continue
        r = scan(f)
        last = parse_ts(r["lastAt"]) if r and r["lastAt"] else None
        if r and last and last > since:
            out.append(r)
    out.sort(key=lambda r: r["lastAt"] or "", reverse=True)
    return out


def main(argv):
    use_state = "--no-state" not in argv
    since = None
    if "--since-hours" in argv:
        since = time.time() - float(argv[argv.index("--since-hours") + 1]) * 3600
    elif use_state and STATE.exists():
        since = json.loads(STATE.read_text()).get("scannedAt")
    since = since or time.time() - 24 * 3600
    ignored = set(IGNORE.read_text().split()) if IGNORE.exists() else set()
    now = time.time()
    print(json.dumps({"scannedAt": now, "since": since, "sessions": collect(PROJECTS, since, ignored)}, indent=1))
    if use_state:
        DESK_HOME.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"scannedAt": now}))


if __name__ == "__main__":
    main(sys.argv[1:])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_scan_sessions.py -v`
Expected: 6 passed. Note `collect` checks file mtime first: fixtures are written now, so mtime > since for every fixture; the `lastAt` check is what excludes `old1`.

- [ ] **Step 5: Commit**

```bash
git add scripts tests/conftest.py tests/test_scan_sessions.py
git commit -m "feat: add Claude session scanner"
```

---

### Task 3: Page template

**Files:**
- Create: `templates/morning-desk.html`, `tests/test_template.py`
- Source to port: `~/.claude/desk/morning-desk.html` (read it fully first)

**Interfaces:**
- Consumes: db layout from the spec (`items`, `sessions`, `updates`, `meta/pulse`, `meta/asks`, `meta/dailyThread`).
- Produces: new doc `meta/config` read by the page with fields `{ ownerName, channelName, teamName, updateHeader, trackerName, trackerLinkPattern, githubOrgs[] }`; every field optional. Later tasks write it (Task 5 setup skill).

- [ ] **Step 1: Write the failing tests**

`tests/test_template.py`:
```python
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / "templates/morning-desk.html"


def script_of(html):
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert blocks, "template has no inline script"
    return blocks[0]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_template_script_parses(tmp_path):
    js = tmp_path / "page.js"
    js.write_text(script_of(HTML.read_text()))
    subprocess.run(["node", "--check", str(js)], check=True)


def test_template_reads_meta_config():
    html = HTML.read_text()
    assert 'db.doc("meta/config")' in html


def test_template_has_neutral_defaults():
    html = HTML.read_text()
    for default in ["DEFAULT_CONFIG", 'ownerName: "the user"', 'channelName: "your team channel"',
                    'updateHeader: "Daily Update for {date}:"']:
        assert default in html, default


def test_template_keeps_core_sections():
    html = HTML.read_text()
    for marker in ['id="duCopy"', 'id="duRefresh"', 'id="sessPanel"', 'data-act="wontdo"', 'id="sortBy"', 'id="addForm"']:
        assert marker in html, marker
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_template.py -v`
Expected: FAIL with `FileNotFoundError` for the template.

- [ ] **Step 3: Port and de-personalise the page**

Copy `~/.claude/desk/morning-desk.html` to `templates/morning-desk.html`, then make exactly these changes:

1. Strip the publish-time skeleton if present: remove everything before `<title>` (the `<!doctype html>…<body>` prefix) and the trailing `</body></html>`.
2. Add, right after `const $ = id => document.getElementById(id);`:
```js
  /* per-user settings, written by /desk-setup into meta/config; every field optional */
  const DEFAULT_CONFIG = {
    ownerName: "the user",
    channelName: "your team channel",
    teamName: "",
    updateHeader: "Daily Update for {date}:",
    trackerName: "",
    trackerLinkPattern: "",
    githubOrgs: []
  };
  let CONFIG = { ...DEFAULT_CONFIG };
```
3. In the db init block (`state.db = db;`), add:
```js
    db.doc("meta/config").onSnapshot(s => {
      CONFIG = { ...DEFAULT_CONFIG, ...(s.exists ? s.data() : {}) };
      renderSessions(); duRender();
    }, () => {});
```
4. Replace the form placeholders: `placeholder="#team-channel"` → `placeholder="#team-channel"`; the Slack link placeholder → `placeholder="https://your-workspace.slack.com/archives/…"`.
5. In `renderSessions`, replace the hard-coded org prefix strip with a config-driven one:
```js
const orgPrefix = new RegExp("^https://github\\.com/(" + (CONFIG.githubOrgs.join("|") || "[^/]+") + ")/");
```
and use `u.replace(orgPrefix, "")`.
6. In `buildPrompt()`, replace the first line and the LINKS line with config-driven text:
```js
      `You write ${CONFIG.ownerName}'s daily standup update for the ${CONFIG.channelName} Slack channel${CONFIG.teamName ? ` (${CONFIG.teamName})` : ""}.`,
```
```js
      "LINKS: every PR, ticket, doc or thread you mention must be a Markdown link, e.g. [#123](https://github.com/<org>/<repo>/pull/123). Take URLs only from the data below (session prs, item links, notes)." +
        (CONFIG.trackerLinkPattern ? ` ${CONFIG.trackerName || "Ticket"} keys may be linked as ${CONFIG.trackerLinkPattern.replace("{key}", "<KEY>")}.` : "") +
        " If you have no URL for something, leave it as plain text.",
```
   and replace the header line with:
```js
      "**" + CONFIG.updateHeader.replace("{date}", ddmmyyyy(du.today)) + "**",
```
   and in the sessions line, replace "what Vivek has been working on" with `` `what ${CONFIG.ownerName} has been working on` ``.
7. Search the file for the names in `.clean-denylist` and any ticket keys or tracker sites, and rewrite each hit into neutral wording (e.g. the voice line keeps its rules but drops the name).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_template.py -v`
Expected: 4 passed (or 3 passed, 1 skipped without node).

- [ ] **Step 5: Commit**

```bash
git add templates/morning-desk.html tests/test_template.py
git commit -m "feat: add de-personalised Morning Desk page template"
```

---

### Task 4: Clean-repo guard

**Files:**
- Create: `tests/test_repo_is_clean.py`

**Interfaces:**
- Produces: a test that fails if any tracked file contains personal or company identifiers. Runs in CI (Task 7).

- [ ] **Step 1: Write the test**

`tests/test_repo_is_clean.py`: generic patterns (Slack ids, artifact URLs, tracker sites) in the test; names of real people, companies and internal projects in an untracked `.clean-denylist` (one regex per line), so the guard itself publishes nothing private.

- [ ] **Step 2: Run it**

Run: `python3 -m pytest tests/test_repo_is_clean.py -v`
Expected: PASS. If it fails, fix the reported lines in the named files (do not widen `ALLOWED_FILES`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_repo_is_clean.py
git commit -m "test: guard the repo against personal identifiers"
```

---

### Task 5: Skills and commands

**Files:**
- Create: `skills/morning-desk/SKILL.md`, `skills/desk-setup/SKILL.md`, `skills/desk-refresh/SKILL.md`, `skills/desk-sync/SKILL.md`, `skills/daily-update/SKILL.md`, `commands/desk-setup.md`, `commands/desk-refresh.md`, `commands/desk-sync.md`, `templates/config.example.yaml`, `templates/style.default.md`
- Modify: `tests/test_plugin_layout.py` (add tests)
- Sources to generalise: memory `morning-desk-artifact.md`, `daily-update-style.md`, and the sync prompt used in the original setup (see spec §Skills). Keep the rules, drop every personal fact.

**Interfaces:**
- Consumes: `scripts/scan_sessions.py` CLI (Task 2), `templates/morning-desk.html` and `meta/config` fields (Task 3).
- Produces: skill names `morning-desk`, `desk-setup`, `desk-refresh`, `desk-sync`, `daily-update`; commands `/desk-setup`, `/desk-refresh`, `/desk-sync`; config keys used by all skills (below).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_plugin_layout.py`:
```python
SKILLS = ["morning-desk", "desk-setup", "desk-refresh", "desk-sync", "daily-update"]
COMMANDS = ["desk-setup", "desk-refresh", "desk-sync"]


def test_skills_have_frontmatter():
    for name in SKILLS:
        fm = frontmatter(ROOT / f"skills/{name}/SKILL.md")
        assert fm.get("name") == name
        assert len(fm.get("description", "")) > 40


def test_commands_have_descriptions():
    for name in COMMANDS:
        assert frontmatter(ROOT / f"commands/{name}.md").get("description")


def test_every_skill_states_the_never_send_rule():
    for name in SKILLS:
        assert "Never send" in (ROOT / f"skills/{name}/SKILL.md").read_text(), name


def test_refresh_skill_handles_missing_tracker():
    text = (ROOT / "skills/desk-refresh/SKILL.md").read_text()
    assert "If no tracker is configured, skip tickets" in text
    assert "Jira" not in text.split("Tracker")[0], "refresh must not assume Jira before the tracker section"


def test_config_example_lists_all_keys():
    text = (ROOT / "templates/config.example.yaml").read_text()
    for key in ["desk_url", "slack_user_id", "slack_workspace", "update_channel", "update_cadence",
                "timezone", "github_orgs", "tracker", "close_merged_tickets"]:
        assert key in text, key
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_plugin_layout.py -v`
Expected: FAIL with `FileNotFoundError` for `skills/morning-desk/SKILL.md`.

- [ ] **Step 3: Write the config example and default style**

`templates/config.example.yaml`:
```yaml
# ~/.config/morning-desk/config.yaml (written by /desk-setup; edit freely)
desk_url: https://claude.ai/artifact/<your-desk-id>
owner_name: Alex
slack_workspace: your-workspace          # your-workspace.slack.com
slack_user_id: U00000000
team_channels:                            # channels whose threads you care about
  - { id: C00000000, name: "#team" }
update_channel: { id: C00000000, name: "#team" }
update_cadence: weekly-thread             # weekly-thread (Monday top-level, replies Tue-Fri) | daily-top-level | none
update_header: "Daily Update for {date}:" # {date} is DD-MM-YYYY
timezone: Europe/London
github_orgs: [your-org]
tracker:                                  # optional; delete the block if you don't use one
  type: linear                            # jira | clickup | devrev | linear | github-issues | other
  connector: linear                       # MCP server name the tracker tools come from
  link_pattern: https://linear.app/your-team/issue/{key}
  my_open_query: "issues assigned to me that are not done"
writes:
  close_merged_tickets: false             # true = move a ticket to done once all its linked PRs merged
```

`templates/style.default.md`:
```markdown
# Daily update style (starts generic; grows from what you actually post)

- Short and crisp: 3–5 workstreams, one sentence each (~15 words), at most 2 one-line sub-points.
- Only outcomes, impact and asks. Order by what moved most.
- Standard Markdown: `**Header**`, `**Workstream:**`, every PR/ticket/doc as a link.
- First person, plain. Asks as direct questions with @mentions; cc whoever asked for the thing.
- Add an **Impact:** sub-point only when a change has a user-visible effect.
- Cut: raw telemetry, internal-process status ("wrote a doc"), scheduling friction, housekeeping, anything not yet agreed or done.
- Thread replies to people go in the thread, not in the update.

## Learned from posts
(desk-update appends dated lessons here after each post)
```

- [ ] **Step 4: Write the skills**

`skills/morning-desk/SKILL.md`:
```markdown
---
name: morning-desk
description: Router for the Morning Desk, a private dashboard of what needs you across Slack, GitHub, your ticket tracker and your Claude sessions, plus a daily update drafted in your style. Use when the user says "set up my desk", "refresh my desk", "catch me up for today", "update the daily update", "start desk sync", or mentions their Morning Desk.
---

# Morning Desk

| User wants | Use |
|---|---|
| First-time setup, or a new machine | `desk-setup` skill (`/desk-setup`) |
| "Catch me up", "refresh my desk" | `desk-refresh` skill (`/desk-refresh`) |
| Keep it current automatically | `desk-sync` skill (`/desk-sync`) |
| Draft or fix today's daily update; learn from what they posted | `daily-update` skill |

Settings live in `~/.config/morning-desk/config.yaml`; the learned style in `~/.config/morning-desk/style.md`. If the config is missing, run `desk-setup` first.

## Standing rules (every skill)
- Never send, post, react or save drafts in Slack. Never comment on or edit tickets or GitHub, except closing tickets whose PRs all merged when `writes.close_merged_tickets: true`.
- Never reopen items the user marked done or won't do. Their `note` on an item is an instruction; act on it.
- Skip personal, HR, career and interpersonal topics in Slack and in sessions. Add such session ids to `~/.config/morning-desk/ignore.txt`. Don't write them to the desk.
- Never copy secrets (tokens, keys, passwords) into the desk.
- Pin every ArtifactData write with `if_version` from your last read. On a version conflict, re-read and merge the user's changes; never overwrite them.
- Summaries the user reads (sync replies, session `state`) are one short line.
```

`skills/desk-setup/SKILL.md`:
```markdown
---
name: desk-setup
description: Set up the Morning Desk for this user: check connectors, ask the few things that can't be detected, publish their private desk page from the plugin template, write ~/.config/morning-desk/config.yaml and the desk's meta/config, seed their daily-update style from their recent posts, then run the first refresh. Use for "set up my desk" or when the config is missing.
---

# Desk setup

Never send anything during setup; it only reads and writes the user's own files and desk.

1. **Connectors.** Check what's available in this session:
   - Slack read/search tools (required). If missing, stop and tell the user to connect Slack.
   - GitHub: `gh auth status` (required for PRs and review requests).
   - Ticket tracker (optional): list connected MCP servers; if one looks like a tracker (Jira, ClickUp, DevRev, Linear, GitHub Issues…), confirm with the user which one they use. Ask for the link pattern for a ticket key.
   - Artifact tools (required). If `Artifact`/`ArtifactData` aren't available on this surface, stop and say the desk needs Claude Code with artifacts (CLI or desktop app).
2. **Ask** (one question at a time, with a suggested default): their name as it should appear, their Slack user id (read it from the Slack tool's "current user" note when possible), workspace domain, the channel their daily update goes to and its cadence, header format, timezone, GitHub org(s). Skip anything you can detect.
3. **Publish the page.** Copy `${CLAUDE_PLUGIN_ROOT}/templates/morning-desk.html` to `~/.config/morning-desk/page.html` and publish it as a new private artifact (capabilities `db` and `sample`, icon "checklist", title "Morning Desk"). Record the URL.
4. **Write config.** Write `~/.config/morning-desk/config.yaml` following `templates/config.example.yaml`, with `writes.close_merged_tickets: false` unless the user opts in. Write the desk's `meta/config` doc with `ownerName`, `channelName`, `teamName`, `updateHeader`, `trackerName`, `trackerLinkPattern`, `githubOrgs`.
5. **Seed style.** Copy `templates/style.default.md` to `~/.config/morning-desk/style.md`. Search Slack for the user's last 5 posts in the update channel that look like daily updates; add a short "Learned from posts" entry describing their real format (header, workstream names, length, how they @mention). Never copy other people's names into the style.
6. **First refresh.** Run the `desk-refresh` skill with a 7-day window, then offer `/desk-sync`.
7. **Report** in 3–4 lines: desk URL, what was found, what's configured, how to keep it current.
```

`skills/desk-refresh/SKILL.md`:
```markdown
---
name: desk-refresh
description: Full catch-up into the Morning Desk: asks of the user in Slack, threads they're in, review requests on GitHub, tickets assigned to them in their tracker, and their recent Claude sessions; adds, updates and closes desk items with evidence, writes the morning brief, and drafts today's daily update. Use for "catch me up", "refresh my desk", or the morning run.
---

# Desk refresh

Never send, post or save drafts anywhere. Read `~/.config/morning-desk/config.yaml` first; if missing, run `desk-setup`.

**Window:** since the newest `updatedAt` in `meta/pulse`, or the last 24 hours (7 days on first run). Compute times with `date`, not mental arithmetic.

1. **Read the desk first:** `meta/asks` (the user's notes for Claude — act on these first), all `items` (honour done/won't do and every `note`).
2. **Slack:** messages to or mentioning the user, their DMs and group DMs, replies in this week's daily-update thread (`meta/dailyThread`), and threads they started where someone else spoke last. Skip personal messages (congratulations, weddings, HR, career, interpersonal).
3. **GitHub:** `gh` — PRs requesting the user's review, their open PRs and review state, PRs merged since the window.
4. **Tracker:** If no tracker is configured, skip tickets. Otherwise use the configured connector to list tickets assigned to the user that aren't done, and link keys with `tracker.link_pattern`. If `writes.close_merged_tickets` is true, move a ticket to done only when every PR linked to it has merged, and note that on the item.
5. **Sessions:** run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_sessions.py` (env `MORNING_DESK_HOME=~/.config/morning-desk`) and update `sessions/<first 8 chars of id>` with a one-sentence `state`, `prs`, `resume`, `itemIds`. Skip sessions about personal topics and add them to `ignore.txt`.
6. **Items:** for each new ask add an item (`kind`: reply, commit, waiting, quiet or hygiene; `due` when a date or "by Friday" is known). Close items the user has clearly handled with a one-line "Closed by Claude:" note. Never reopen done/won't-do items.
7. **Brief:** write `meta/pulse` with a one-line headline and up to 5 bullets with links.
8. **Daily update:** run the `daily-update` skill to draft today's update if it isn't posted.
9. **Reply** in under 10 lines: what needs the user, what you closed, coverage gaps.
```

`skills/desk-sync/SKILL.md`:
```markdown
---
name: desk-sync
description: Keep the Morning Desk current automatically every 30 minutes: sessions, new Slack asks, and today's daily-update draft. Picks the scheduler for the surface — a session loop (CronCreate) in the Claude Code CLI, or a Scheduled Task in the Claude desktop app. Use for "start desk sync", "keep my desk updated", "keep monitoring".
---

# Desk sync

Never send anything. The sync only reads sources and writes the user's own desk.

1. **Pick the scheduler.**
   - If the `CronCreate` tool is available (Claude Code CLI): create a recurring job at minutes 13 and 43 of every hour with the light-refresh prompt below. Tell the user it runs only while this session stays open and the machine is awake, and expires after 7 days.
   - Otherwise (Claude desktop app): tell the user to add a desktop Scheduled Task that runs `/desk-refresh light` every 30 minutes, and that the app must stay open.
2. **Light-refresh prompt** (use verbatim, it must stand alone):
   > Morning Desk sync. Work quietly; reply with ONE short line. Read ~/.config/morning-desk/config.yaml. Sessions: run the plugin's scan_sessions.py and update changed `sessions/<id8>` docs. Slack: since the last sync, find new asks of the user and replies in this week's update thread; add or close items. If anything changed and today's update isn't posted, refresh it with the daily-update rules. If the user posted today's update, mark it posted and learn from it. Never send, never reopen done/won't-do items, skip personal topics, pin every write. Reply "Desk sync: <what changed>" or "Desk sync: nothing new."
3. **Confirm** in 2 lines: which scheduler, when it next runs, how to stop it.
```

`skills/daily-update/SKILL.md`:
```markdown
---
name: daily-update
description: Draft the user's daily standup update in their own style, store it on the Morning Desk for one-click copy, and learn from what they actually post. Use for "update the daily update", "refresh it for today", or after the user posts their update.
---

# Daily update

Never send or post the update; the user copies it from the desk.

## Draft
1. Read `~/.config/morning-desk/style.md` and the last two posted updates (`updates/*` with `postedText`). Their phrasing and workstream names win; their length does not if `style.md` says shorter.
2. Gather since the last update: desk items (open, plus closed since), session `state`s, Slack facts from the refresh.
3. Write `updates/<YYYY-MM-DD>`: `text` (standard Markdown, header from config, links on every PR/ticket/doc), `status: draft`, `generatedAt` = now UTC, `generatedBy: claude-code`. Only facts from the data; never claim a decision that hasn't been made. Don't include replies the user owes someone in a thread.
4. On the first update of a `weekly-thread` week (Monday), clear `meta/dailyThread.link` and tell the user to post top-level; otherwise point them at this week's thread.

## Learn from the post
When the user's post for today appears in the update channel:
1. Set `status: posted`, `postedText` (converted to Markdown), `postedLink`.
2. Compare it with the draft. Append a dated entry under "Learned from posts" in `style.md`: what they kept, cut, added or reworded. Keep entries to 2–4 bullets, no names of other people.
3. If they replied in the thread after posting, those replies are not part of the update.
```

- [ ] **Step 5: Write the commands**

`commands/desk-setup.md`:
```markdown
---
description: Set up your Morning Desk (connectors, private desk page, config, your daily-update style). Never sends anything.
---

Run the `desk-setup` skill from the morning-desk plugin.
```

`commands/desk-refresh.md`:
```markdown
---
description: Catch up and refresh your Morning Desk now. Pass "light" for a quick sessions-and-Slack-only pass.
argument-hint: [light]
---

Run the `desk-refresh` skill. If `$ARGUMENTS` is `light`, only do the Sessions, Slack and Daily update steps and reply in one line.
```

`commands/desk-sync.md`:
```markdown
---
description: Keep your Morning Desk current every 30 minutes (session loop in the CLI, Scheduled Task in the desktop app).
---

Run the `desk-sync` skill.
```

- [ ] **Step 6: Run tests**

Run: `python3 -m pytest -v`
Expected: all tests pass, including `test_repo_is_clean`.

- [ ] **Step 7: Commit**

```bash
git add skills commands templates/config.example.yaml templates/style.default.md tests/test_plugin_layout.py
git commit -m "feat: add Morning Desk skills, commands and config template"
```

---

### Task 6: Docs

**Files:**
- Create: `README.md`, `docs/data-model.md`, `docs/privacy.md`

**Interfaces:**
- Consumes: commands, config keys, surfaces table from the spec.

- [ ] **Step 1: Write `docs/data-model.md`**

Document every collection and field exactly as listed in the spec's Data model section plus `meta/config` from Task 3, one table per collection (field | type | written by | meaning).

- [ ] **Step 2: Write `docs/privacy.md`**

Three sections: **Read** (Slack messages addressed to you or in your threads, your GitHub PRs/reviews, your tracker's assigned tickets, local Claude transcripts under `~/.claude/projects`); **Written to your desk** (short summaries, links, one-sentence session states, your daily-update drafts; private artifact visible only to you unless you share it); **Never stored** (raw transcripts, secrets, personal/HR/career topics, anything about people beyond what's needed to name an ask). State that nothing is ever sent or posted.

- [ ] **Step 3: Write `README.md`**

Sections: what it is (3 sentences + a screenshot placeholder line `![Morning Desk](docs/screenshot.png)` — leave out until a screenshot exists); **Install** (`/plugin marketplace add viveknigam3003/morning-desk` then `/plugin install morning-desk@morning-desk`, then `/desk-setup`); **Daily use** (`/desk-refresh`, `/desk-sync`, Copy for Slack); **Where it works** (the surfaces table from the spec verbatim); **Trackers** (pluggable, config block example); **What it never does** (the standing rules); **Privacy** (link); **Limits** (sync needs an open session; claude.ai/code cloud sessions aren't scanned); credit line "Built by Vivek Nigam with Claude Code"; MIT licence.

- [ ] **Step 4: Run the clean guard**

Run: `python3 -m pytest tests/test_repo_is_clean.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/data-model.md docs/privacy.md
git commit -m "docs: add README, data model and privacy notes"
```

---

### Task 7: CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/ci.yml`:
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: pip install pytest
      - run: python -m pytest -v
```

- [ ] **Step 2: Run the suite locally**

Run: `python3 -m pytest -v`
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run tests on push"
```

---

### Task 8: Verify, push, and dry-run install (with the user)

**Files:** none new.

- [ ] **Step 1: Final clean check across everything**

Run: `python3 -m pytest tests/test_repo_is_clean.py -v` (with your local `.clean-denylist` present)
Expected: no output.

- [ ] **Step 2: Push** (ask the user before pushing; the repo is public)

```bash
git push origin main
```
Expected: CI passes on GitHub (`gh run watch`).

- [ ] **Step 3: Dry-run install with the user**

In a fresh Claude Code session: `/plugin marketplace add viveknigam3003/morning-desk`, `/plugin install morning-desk@morning-desk`, `/desk-setup`. Use a throwaway desk (publish a new artifact; don't touch the user's real desk). Check: page renders, `meta/config` applied (header and channel name in the update prompt), sessions panel fills after one refresh, daily update drafts. Repeat the install check in the Claude desktop app Code tab and note in the README whether Artifact tools and plugin install work there.

- [ ] **Step 4: Tag**

```bash
git tag v0.1.0 && git push origin v0.1.0
```
