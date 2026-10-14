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
2. Compare it with the draft. Append a dated entry under "Learned from posts" in `style.md`: what they kept, cut, added or reworded. Keep entries to 2–4 bullets, no names of other people. Then rewrite the desk's `meta/config.styleRules` from the updated rules so the page's Refresh uses them.
3. If they replied in the thread after posting, those replies are not part of the update.
