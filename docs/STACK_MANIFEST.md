# Stack Manifest — One Subscription, Four Seats

Canonical context for every seat. Version 2026-11-21. Owner: Ben (Ark95x).
Read this first in any seat before claiming a sibling seat does not exist.

## The stack

Ben operates **one stack**, sold going forward as **The X Subscription**:
one subscription / workspace / bill for **Grok + Cursor**, X benefits when a
personal X account is added, and **Grok Bot included on Premium, Super, and
Ultra** (not Plus). Grok, Grok Bot, and Cursor draw from one shared weekly
usage pool. Source: https://docs.x.ai/x-subscription/overview and
https://docs.x.ai/x-subscription/grok-bot

| Seat | What it is | What it can reach today | Seat type |
|---|---|---|---|
| Cursor (incl. this clippin chat) | Code / build / files / repo seat | This repo, git, PRs; X read via the connected X plugin (see Verified) | Brain / orchestration + Tools |
| X Premium (@ark95x) | Public signal + distribution seat | Posts, search, trends, bookmarks, mentions via official X tools | Tools / interfaces |
| Grok (grok.com / Grok app) | Reasoning / research seat | Grok connectors (Drive, Gmail, Calendar, Outlook, etc.) per https://docs.x.ai/grok/connectors — X awareness comes from the unified account + paste pack, not from Cursor | Inference / research |
| Grok Bot (phone thread / x.ai/bot) | Mobile agent seat | After its X Connector is on: search posts, timelines, mentions, trends, bookmarks via @bot / the official X plugin for Grok Bot | Automation / mobile agent |

## Verified from this Cursor seat (2026-11-21)

- X plugin connected here: account **@ark95x**, name Ark95x,
  `subscription_type: PremiumPlus` (read-only `get_users_me`). So Cursor
  already has a working X read path — do not claim Cursor "has no X."
- Cursor run owner: Ark95x (this workspace). Billing account identity for
  Cursor/Grok unification was **not** read from here — see Needs Ben.
- Grok, Grok Bot, and the X app were **not** opened from this seat. No tool
  in this session can sign in to grok.com/dashboard or the Grok Bot app.
  Their state below is `PREPARED`, not `LIVE`, until Ben confirms in-seat.

## Awareness rule for every seat

1. You are one seat of a four-seat stack, not a standalone product.
2. Name siblings by job: Cursor builds, X signals, Grok reasons/researches,
   Grok Bot acts on mobile / forwards via @bot.
3. If a task fits a sibling better, say so and hand off with a paste-ready
   brief (link + summary + exact ask). Never claim the sibling is
   unavailable without checking the Verified section / Ben's confirmation.
4. Information moves by **link + summary + draft**, by hand today. No seat
   auto-posts, auto-sends, or auto-publishes for another seat.
5. Red gates: posting to X, sending any message, publishing, deleting,
   paying, or changing a subscription requires Ben's explicit yes to the
   exact action. Unification itself is **permanent and cannot be undone**
   (https://docs.x.ai/x-subscription/unify-accounts) — never rush it.
6. Job 001 stays **NO-GO**. No media pipeline, no fake lead demo.
7. No secrets in chat, files, or posts. X connects by OAuth / plugin
   sign-in only — never a pasted bearer token or password.

## Routing (manual, today)

```text
X signal (link/post) -> paste into Cursor or Grok -> summary + draft
Cursor output        -> paste-ready brief -> Grok (reason) / Grok Bot (mobile)
Grok answer          -> paste back to Cursor to build / file / log
Anything outbound    -> DRAFT ONLY -> Ben approves exact text -> Ben sends
```

## Seat status

| Seat | Awareness established | How | Still needs Ben |
|---|---|---|---|
| Cursor | **LIVE in this repo** | `.cursor/rules/stack-awareness.mdc` (always-apply) + this manifest | Confirm the Cursor account shown at cursor.com/unify is the one to keep primary |
| X | **LIVE (read) from Cursor** | X plugin OAuth as @ark95x PremiumPlus, verified above | Nothing for read. Any post = Red, per-post approval |
| Grok | PREPARED | `docs/stack-paste/grok-custom-instructions.md` | Paste it in Grok (Ben, signed in), or attach this manifest to a Grok Project |
| Grok Bot | PREPARED | `docs/stack-paste/grokbot-starter-prompt.md` | Enable its X Connector in the Grok Bot app (exact clicks in `docs/FOUR_PROGRAM_AWARENESS.md`) |
| Subscription unification | PREPARED — NOT DONE | Exact clicks documented | Ben-only: permanent, checkout, plan choice (Premium+ for Grok Bot) |

## What cannot be done from Cursor (honest limits)

- Cannot flip Grok Bot's X Connector, Grok's settings, or X account
  settings from here; those toggles live in Ben's signed-in sessions.
- Cannot unify accounts from here: unification is a signed-in web
  checkout (cursor.com/unify, accounts.x.ai/unify, or x.com banner) and
  a permanent billing change = Red.
- Cannot prove Grok/Grok Bot "now know" anything until Ben pastes the
  pack there and tests with: "Which seats are in my stack and what is
  each for?" — expected answer lists all four seats above.
