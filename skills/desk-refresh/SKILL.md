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
5. **Sessions:** run `MORNING_DESK_HOME=~/.config/morning-desk python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_sessions.py` (add `--since-hours 168` on the first run, or `--since-hours N` to match a longer window) and update `sessions/<first 8 chars of id>` with a one-sentence `state`, `prs`, `resume`, `itemIds`. Skip sessions about personal topics and add them to `ignore.txt`. Once the desk writes succeed, run `MORNING_DESK_HOME=~/.config/morning-desk python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_sessions.py --commit` so the next scan starts from here; if the refresh fails, skip the commit and the sessions are picked up next time.
6. **Items:** for each new ask add an item (`kind`: reply, commit, waiting, quiet or hygiene; `due` when a date or "by Friday" is known). Close items the user has clearly handled with a one-line "Closed by Claude:" note. Never reopen done/won't-do items.
7. **Brief:** write `meta/pulse` with a one-line headline and up to 5 bullets with links.
8. **Daily update:** run the `daily-update` skill to draft today's update if it isn't posted.
9. **Reply** in under 10 lines: what needs the user, what you closed, coverage gaps.
