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
3. **Publish the page.** Copy `${CLAUDE_PLUGIN_ROOT}/templates/morning-desk.html` to `~/.config/morning-desk/page.html` and publish it as a new private artifact (capabilities `db` and `sample`, icon "checklist", title "Morning Desk"). Record the URL. Later page updates: edit `page.html` and publish with `url` set to the desk URL.
4. **Write config.** Write `~/.config/morning-desk/config.yaml` following `${CLAUDE_PLUGIN_ROOT}/templates/config.example.yaml`, with `writes.close_merged_tickets: false` unless the user opts in. Write the desk's `meta/config` doc with `ownerName`, `channelName`, `teamName`, `updateHeader`, `trackerName`, `trackerLinkPattern`, `githubOrgs`, and `styleRules` (the rules section of `style.md` as plain text; rewrite it whenever `style.md` changes).
5. **Seed style.** Copy `${CLAUDE_PLUGIN_ROOT}/templates/style.default.md` to `~/.config/morning-desk/style.md`. Search Slack for the user's last 5 posts in the update channel that look like daily updates; add a short "Learned from posts" entry describing their real format (header, workstream names, length, how they @mention). Never copy other people's names into the style.
6. **Ignore this session.** Append the current session id to `~/.config/morning-desk/ignore.txt` so the desk doesn't summarise itself.
7. **First refresh.** Run the `desk-refresh` skill with a 7-day window, then offer `/desk-sync`.
8. **Report** in 3–4 lines: desk URL, what was found, what's configured, how to keep it current.
