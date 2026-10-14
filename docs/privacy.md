# Privacy

Morning Desk never sends, posts, reacts or saves drafts in any tool. The only optional write is closing a ticket whose PRs have all merged, and it's off unless you turn on `writes.close_merged_tickets`.

## What it reads
- Slack messages addressed to you or mentioning you, your DMs and group DMs, and threads you're part of.
- Your GitHub PRs, review requests and their status (through `gh`).
- Tickets assigned to you in the tracker you configure, if any.
- Your local Claude Code transcripts under `~/.claude/projects`, through `scripts/scan_sessions.py`, on your machine.

## What it writes to your desk
- Short summaries of asks, with links.
- One-sentence states for your Claude sessions, with PR links and resume commands.
- Your daily-update drafts and, once posted, your post.

Your desk is a private claude.ai artifact: only you can open it unless you share it.

## What it never stores
- Raw transcripts or whole messages.
- Secrets: the scanner redacts common token and key shapes before anything leaves your machine.
- Personal, HR, career or interpersonal topics, from Slack or from sessions.

Local state lives in `~/.config/morning-desk/` (config, your learned style, the scanner's last-scan time and ignore list).
