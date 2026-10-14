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
