# Data model

Everything lives in your desk artifact's database. Claude writes through `ArtifactData`, pinning every write to the version it read; the page writes through `window.claude` `db`.

## `items/<slug>` — things that need you

| Field | Type | Written by | Meaning |
|---|---|---|---|
| title | string | Claude / you | What needs doing |
| detail | string | Claude / you | One or two lines of context |
| kind | `reply` \| `commit` \| `waiting` \| `quiet` \| `hygiene` | Claude / you | Reply owed, your commitment, waiting on others, gone quiet, tickets & PRs |
| source | string | Claude / you | Where it came from (channel, repo, tracker) |
| link | url | Claude / you | Thread, PR or ticket |
| since | YYYY-MM-DD | Claude / you | When it started |
| due | YYYY-MM-DD | Claude / you | Deadline, if known |
| priority | `high` \| `normal` | Claude / you | |
| status | `open` \| `snoozed` \| `done` \| `wontdo` | page / Claude | Claude never reopens `done` or `wontdo` |
| snoozeUntil | YYYY-MM-DD | page | |
| doneAt | ISO time | page / Claude | |
| note | string | you / Claude | Your note is an instruction to Claude |
| initiative | string | Claude | Optional group label |
| addedBy | `claude` \| `you` | | |
| updatedAt | ISO time | both | |

## `sessions/<first 8 chars of id>` — your Claude Code sessions

| Field | Type | Meaning |
|---|---|---|
| title | string | Session title |
| repo, branch | string | Where it ran |
| lastAt | ISO time | Last activity |
| state | string | One sentence: what it's doing, results, blockers |
| prs | url[] | PRs mentioned |
| resume | string | `cd "<dir>" && claude --resume <id>` |
| sessionId | string | Full id |
| itemIds | string[] | Desk items it relates to |
| updatedAt | ISO time | |

## `updates/<YYYY-MM-DD>` — daily updates

| Field | Type | Meaning |
|---|---|---|
| date | YYYY-MM-DD | |
| status | `draft` \| `posted` | The page stops refreshing posted updates |
| text | Markdown | Current draft |
| postedText | Markdown | What you actually posted (used to learn your style) |
| postedLink | url | The Slack message |
| generatedAt | ISO time | The page refreshes when the desk changed after this |
| generatedBy | `claude-code` \| `page` | |

## `meta/*`

| Doc | Fields | Meaning |
|---|---|---|
| `meta/config` | ownerName, channelName, teamName, updateHeader, trackerName, trackerLinkPattern, githubOrgs, styleRules | Settings the page needs; written by `/desk-setup`; all optional |
| `meta/pulse` | generatedAt, headline, bullets[{text, link}] | The morning brief |
| `meta/asks` | text, updatedAt | Your notes for Claude, read at every refresh |
| `meta/dailyThread` | weekOf, link | This week's update thread |
