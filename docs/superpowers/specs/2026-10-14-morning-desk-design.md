# Morning Desk — design

Date: 2026-10-14 · Status: approved 2026-10-14

## Goal

A Claude Code plugin that gives any engineer a private "morning desk": one page that shows what needs them across Slack, GitHub, their ticket tracker (Jira, ClickUp, DevRev, Linear, GitHub Issues, …) and their own Claude Code sessions, keeps itself current, and drafts their daily standup update in their own voice. The user never adds items by hand; Claude does.

Success: a new user installs the plugin, runs one setup command, and within minutes has a populated desk and a draft daily update, without editing any file.

## Non-goals (v1)

- Sending or posting anything on the user's behalf.
- Shared or team desks (each desk is private to its owner).
- Running while the laptop is closed. Cloud routines are out of scope until someone asks; the sync runs in a Claude Code session the user keeps open.
- Teams, Discord or other chat connectors.

## Shape

A standalone public repo `viveknigam3003/morning-desk` that is both a plugin marketplace and the plugin itself.

```
.claude-plugin/
  marketplace.json          # lists the one plugin
  plugin.json
commands/
  desk-setup.md             # /desk-setup
  desk-refresh.md           # /desk-refresh  (full catch-up into the desk)
  desk-sync.md              # /desk-sync     (start the 30-min loop)
skills/
  morning-desk/SKILL.md     # router + standing rules
  desk-setup/SKILL.md
  desk-refresh/SKILL.md
  desk-sync/SKILL.md
  daily-update/SKILL.md     # drafting + style learning
templates/
  morning-desk.html         # the page, no personal data
scripts/
  scan_sessions.py          # stdlib-only session scanner
tests/
  test_scan_sessions.py
  fixtures/*.jsonl
docs/
  data-model.md
  privacy.md
README.md
LICENSE (MIT)
```

## Where it runs

| Surface | Desk page + data | Session scanning | Keeping it fresh |
|---|---|---|---|
| Claude Code CLI | yes | yes (`~/.claude/projects`) | `/desk-sync` starts a 30-min loop (CronCreate) in a session the user keeps open |
| Claude desktop app, Code tab | yes, if the Artifact tools are available there (verify in the first manual test) | yes, local sessions use the same files | a desktop Scheduled Task that runs `/desk-refresh` every 30 min (CronCreate isn't available there); app must stay open |
| claude.ai/code (cloud) | yes | no local transcripts, so cloud sessions aren't scanned | not in v1 |
| Codex (CLI/app) | no: it can't publish or write claude.ai artifacts | v1.1: the scanner can read Codex session logs as an extra source, so Codex work still shows up on the desk | n/a |

`desk-sync` detects the surface and picks the right scheduler. If the plugin can't be installed in the desktop app directly, the README covers installing it from the CLI first (shared `~/.claude`).

## Components

### Page (`templates/morning-desk.html`)
The current Morning Desk page with every personal value removed. Sections: brief, daily update (Copy for Slack, Refresh, open-this-week's-thread), Claude sessions, items grouped by kind (reply owed, your commitments, waiting on others, gone quiet, tickets & PRs) with done / won't do / snooze / note, sort by due date, search, notes for Claude, add item. Capabilities: `db` and `sample`. All text that names a team, product or person is replaced by neutral copy. The Refresh prompt reads its rules (format, length, channel name) from `meta/config` in the db instead of hard-coding them.

### Data model (`docs/data-model.md`)
Unchanged from today:
- `items/<slug>`: title, detail, kind (`reply|commit|waiting|quiet|hygiene`), source, link, since, due, priority, status (`open|snoozed|done|wontdo`), snoozeUntil, doneAt, note, initiative, addedBy, updatedAt.
- `sessions/<id8>`: title, repo, branch, lastAt, state, prs, resume, sessionId, itemIds, updatedAt.
- `updates/<YYYY-MM-DD>`: date, status, text, postedText, postedLink, generatedAt, generatedBy.
- `meta/pulse`, `meta/asks`, `meta/dailyThread`.
- New: `meta/config` — display-only settings the page needs (update header format, channel name, timezone).

### Local config (`~/.config/morning-desk/`)
- `config.yaml`: desk URL, Slack user id, workspace domain, team channel id/name, daily-update channel and cadence (e.g. Monday top-level, replies Tue–Fri), timezone, GitHub org(s), and an optional `tracker` block: `type` (jira, clickup, devrev, linear, github-issues, other), the MCP connector to use, a URL pattern for linking ticket keys (e.g. `https://<site>/browse/{key}`), and how to find "my open tickets" in that tool.
- `style.md`: the user's learned daily-update style (keeps/cuts/adds, length, format). Starts from defaults, then grows.
- `ignore.txt`, `last_scan.json`: scanner state.
- `page.html`: the user's copy of the template, used for republishing.

### Session scanner (`scripts/scan_sessions.py`)
The current scanner, made portable: reads `~/.claude/projects/*/*.jsonl` changed since the last scan, filters by real activity time, skips ignored ids, redacts common secret shapes, and prints short summaries (title, repo, branch, recent prompts, last reply excerpt, PRs, resume command). Python 3 stdlib only.

### Skills
- **morning-desk** (router): when to use which command; the standing rules below.
- **desk-setup**: checks connectors (Slack required; GitHub via `gh` required; any ticket tracker optional, detected from the user's connected MCP servers and confirmed with them), asks the few things it can't detect, publishes the page from the template as the user's private artifact, writes `config.yaml` and `meta/config`, reads the user's last few posted daily updates to seed `style.md`, then runs a first refresh.
- **desk-refresh**: the catch-up: mentions, DMs, threads they're in, review requests, tickets assigned to them in whatever tracker is configured (read through that tracker's MCP connector; skipped cleanly if none), Claude sessions; adds/updates/closes items with evidence; writes the brief; drafts today's update.
- **desk-sync**: starts a 30-minute CronCreate loop inside the current session that runs a light refresh (sessions + Slack since last sync + today's draft). Explains the 7-day expiry and the "only while this session is open" limit.
- **daily-update**: drafts in the user's format from `style.md`; after the user posts, stores `postedText`, diffs it against the draft and appends new lessons to `style.md`.

## Standing rules (enforced in every skill)
- Never send, post, react or save drafts in Slack; never comment on or edit tickets or GitHub unless the user turns that on in config.
- Never reopen items the user marked done or won't do; treat their notes as instructions.
- Skip personal, HR and career topics, in both Slack and sessions; add such sessions to `ignore.txt`.
- Never copy secrets into the desk.
- Updates are short and crisp (3–5 workstreams, one sentence each, ≤2 sub-points), Markdown with links, facts only.
- Pin every db write to the version read; on conflict, re-read and merge.

## Privacy
Desk data lives in the user's own private artifact. The scanner and config stay on their machine. `docs/privacy.md` states exactly what is read, what is written to the desk, and what is never stored.

## De-personalisation checklist (before the first push)
- No Slack user/channel ids, workspace domains, tracker sites or ids, artifact URLs, people's names, company or product names, or learned style from the original setup.
- `tests/test_repo_is_clean.py` must pass: generic patterns (Slack ids, artifact URLs, tracker sites) in the test, real names of people, companies and internal projects in an untracked `.clean-denylist`.

## Testing
- `tests/test_scan_sessions.py`: fixture transcripts cover activity filtering, ignore list, secret redaction, PR extraction, and missing fields.
- Page script parses (`node --check` on the extracted script) in CI.
- Manual: run `/desk-setup` end to end against a throwaway artifact before tagging v0.1.0.

## Opt-in write actions
`config.yaml` has `writes.close_merged_tickets: false` by default. When the user turns it on, refresh moves a ticket to done once every PR linked to it has merged, and notes this on the desk item. All other writes to trackers and GitHub stay off.
