# Four-Program Awareness — Per-Seat Load Steps

Companion to the canonical `docs/STACK_MANIFEST.md`. Honest status only:
**LIVE** = established and evidenced, **PREPARED** = file ready, Ben must
load it in that seat, **BEN-ONLY** = signed-in dashboard action no agent
here can perform.

## 1. Cursor — LIVE

- `.cursor/rules/stack-awareness.mdc` (`alwaysApply: true`) loads the stack
  into every Cursor session opened on this repo, including clippin chats.
- `docs/STACK_MANIFEST.md` is the long-form source it points to.
- X read verified 2026-11-21: plugin account @ark95x, PremiumPlus.
- Test in any new Cursor chat: "Which seats are in my stack?" — it should
  answer from the rule without being re-briefed.

## 2. Grok (grok.com / app) — PREPARED, Ben loads

Grok has no file in this repo it can read on its own. Ben, signed in:

1. Open Grok → Settings → Custom Instructions (label may read
   "Customize Grok" / profile customisation; if labels differ, stop and
   note the actual label).
2. Paste all of `docs/stack-paste/grok-custom-instructions.md`.
3. Save. New chat → ask: "Which seats are in my stack and what is each
   for?" Expected: Cursor builds, X signals, Grok reasons, Grok Bot mobile.
4. Optional stronger seat: create a Grok Project, attach
   `docs/STACK_MANIFEST.md` as project knowledge, same test question.

Note: Grok's own connectors list (Drive, Gmail, Calendar, Outlook,
SharePoint, OneDrive, Teams, Salesforce, custom MCP) is documented at
https://docs.x.ai/grok/connectors — X access for Grok comes via the
unified X Subscription / its built-in X awareness, not a repo file.

## 3. Grok Bot (phone thread) + X Connector — BEN-ONLY enablement

This is the "GrokBot needs X Connector enabled" step. It lives in the
**Grok Bot app**, not in Cursor and not in this repo. Per X Help
(https://help.x.com/en/using-x/about-bot):

1. Open the Grok Bot app on the phone.
2. Open **Marketplace** or **Settings → Plugins**.
3. Add the official **"X for Grok Bot"** plugin.
4. Sign in with the X account to use — should be **@ark95x** to match the
   verified seat. Connecting may create an X developer account; paid
   Grok Bot users may receive X API credits.
5. Verify (read-only): mention **@bot** in a post/reply with a harmless
   research ask, or ask Grok Bot to search X for a topic. Do NOT test by
   posting announcements.
6. Then paste `docs/stack-paste/grokbot-starter-prompt.md` as the first
   message of the working phone thread so the thread carries the stack.

Groks's subscription dashboard (grok.com/dashboard) manages plan/usage
after unification; it is not where the Grok Bot X plugin is toggled.

## 4. X Premium — LIVE read, no settings change made

- X has no custom-instructions seat to load a manifest into. Awareness on
  X is expressed only by what Ben posts — posting is Red, so nothing was
  posted and no profile text was changed.
- Working path today: X → Cursor/Grok by link. In the X app, copy a post
  link → paste into Cursor (this seat can read it via the plugin) or Grok.
- `docs/stack-paste/x-seat-note.md` is a draft-only bio/pinned text Ben
  may use later; publishing it needs his explicit yes.

## 5. Subscription unification — BEN-ONLY, permanent, Red

Do NOT treat "unify us" as a click an agent can do. Official facts
(https://docs.x.ai/x-subscription/unify-accounts):

- Switching unifies eligible Cursor + Grok accounts into one account,
  workspace, plan, and bill; adding a personal X account adds X benefits.
- **A completed unification is permanent. It can't be undone, and Support
  can't undo it.** Old subscriptions on combined accounts are cancelled
  at checkout with prorated refunds (App Store / Google Play exceptions).
- Grok Bot requires **Premium, Super, or Ultra** — Plus excludes it.
- Account emails do not need to match; Ben must sign in to the *exact*
  accounts he means to combine and check each before confirming.

Exact clicks (starting from Cursor, individual plan):

1. Go to **cursor.com/unify** → **Get started**.
2. Select **Grok** and **X** to add → **Start linking accounts**.
3. Grok: sign in, confirm it is the correct Grok account.
4. X: sign in / authorize as **@ark95x**.
5. If multiple Cursor accounts appear, choose the primary carefully —
   this is the irreversible merge point.
6. Choose plan **Premium or higher** (required for Grok Bot).
7. Review accounts + price on the final screen. **Stop here unless every
   account shown is the intended one.** Then checkout.
8. After "Your unified subscription is ready": manage plan/usage at
   **grok.com/dashboard → Usage**; check Grok Bot draws from the shared
   weekly pool there.

Alternatives: start at accounts.x.ai/unify (from Grok: Settings › Billing
→ Get started) or via the x.com in-product banner. Team path differs
(cursor.com/unify/team, billing admins only) — not assumed for Ben.

Still unknown from this seat (Ben checks at step 3–5): which email/account
each of Grok and Cursor is currently billed under, current plan tiers,
and App Store / Google Play billing exceptions.

## Test / health command

```bash
python3 scripts/check_stack_awareness.py
```

Checks the manifest, Cursor rule, paste packs, safety gates, and that no
secret-shaped strings were committed. It does not (and cannot) prove
Grok/Grok Bot in-app state — that proof is Ben's test question in-seat.
