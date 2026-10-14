---
name: desk-sync
description: Keep the Morning Desk current automatically every 30 minutes: sessions, new Slack asks, and today's daily-update draft. Picks the scheduler for the surface — a session loop (CronCreate) in the Claude Code CLI, or a Scheduled Task in the Claude desktop app. Use for "start desk sync", "keep my desk updated", "keep monitoring".
---

# Desk sync

Never send anything. The sync only reads sources and writes the user's own desk.

1. **Pick the scheduler.**
   - If the `CronCreate` tool is available (Claude Code CLI): create a recurring job at minutes 13 and 43 of every hour with the light-refresh prompt below. Tell the user it runs only while this session stays open and the machine is awake, and expires after 7 days.
   - Otherwise (Claude desktop app): tell the user to add a desktop Scheduled Task that runs `/desk-refresh light` every 30 minutes, and that the app must stay open.
2. **Light-refresh prompt.** Use it verbatim, except replace `<SCANNER>` with the absolute path of this plugin's `scripts/scan_sessions.py` (expand `${CLAUDE_PLUGIN_ROOT}` now; the stored prompt runs later, where it may not resolve):
   > Morning Desk sync. Work quietly; reply with ONE short line. Read ~/.config/morning-desk/config.yaml. Sessions: run `MORNING_DESK_HOME=~/.config/morning-desk python3 <SCANNER>` and update changed `sessions/<id8>` docs, then run it again with `--commit`. Slack: since the last sync, find new asks of the user and replies in this week's update thread; add or close items. If anything changed and today's update isn't posted, refresh it with the daily-update rules. If the user posted today's update, mark it posted and learn from it. Never send, never reopen done/won't-do items, skip personal topics, pin every write. Reply "Desk sync: <what changed>" or "Desk sync: nothing new."
3. **Confirm** in 2 lines: which scheduler, when it next runs, how to stop it.
