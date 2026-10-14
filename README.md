# Morning Desk

A private morning triage desk for Claude Code. One page shows what needs you across Slack, GitHub, your ticket tracker and your Claude Code sessions. Claude keeps it current and drafts your daily standup update in your own style, ready to copy into Slack.

It never sends anything on your behalf.

## Install

```
/plugin marketplace add viveknigam3003/morning-desk
/plugin install morning-desk@morning-desk
/desk-setup
```

Setup checks your connectors, asks a few questions, publishes your private desk page, learns your update style from your recent posts, and runs the first refresh.

## Daily use

- `/desk-refresh`: catch up now (`/desk-refresh light` for a quick pass).
- `/desk-sync`: keep the desk current every 30 minutes.
- On the desk: mark items done, won't do or snoozed, leave notes for Claude, sort by due date, and **Copy for Slack** to paste your update. In Slack, press `cmd+shift+f` to format the Markdown.

## Where it works

| Surface | Desk page + data | Session scanning | Keeping it fresh |
|---|---|---|---|
| Claude Code CLI | yes | yes (`~/.claude/projects`) | `/desk-sync` starts a 30-min loop (CronCreate) in a session the user keeps open |
| Claude desktop app, Code tab | yes, if the Artifact tools are available there (verify in the first manual test) | yes, local sessions use the same files | a desktop Scheduled Task that runs `/desk-refresh` every 30 min (CronCreate isn't available there); app must stay open |
| claude.ai/code (cloud) | yes | no local transcripts, so cloud sessions aren't scanned | not in v1 |
| Codex (CLI/app) | no: it can't publish or write claude.ai artifacts | v1.1: the scanner can read Codex session logs as an extra source, so Codex work still shows up on the desk | n/a |

## Ticket trackers

Any tracker with an MCP connector works: Jira, ClickUp, DevRev, Linear, GitHub Issues, or others. Add a `tracker` block to `~/.config/morning-desk/config.yaml`:

```yaml
tracker:
  type: clickup
  connector: clickup
  link_pattern: https://app.clickup.com/t/{key}
  my_open_query: "tasks assigned to me that are open"
```

No tracker? Leave the block out; tickets are skipped.

## What it never does

- Send, post, react or save drafts in Slack.
- Edit tickets or GitHub (except closing tickets whose PRs all merged, if you turn on `writes.close_merged_tickets`).
- Reopen items you marked done or won't do.
- Store personal, HR or career topics, or secrets.

See [privacy](docs/privacy.md) and the [data model](docs/data-model.md).

## Limits

- The sync runs only while a Claude Code session (or the desktop app) stays open.
- Sessions on claude.ai/code aren't scanned; they have no local transcripts.

Built by Vivek Nigam with Claude Code. MIT licence.
