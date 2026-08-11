# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, a freemium → premium conversion model, and a **premium community destination (Lounge)**.
- Support **four pillars/themes**:
  - **Tech & AI** (`tech-business`)
  - **Business & Finance** (`finance`)
  - **Personal Growth** (`lifestyle`) *(DB slug; displayed as Personal Growth)*
  - **Delivery & Systems** (`delivery`) ✅
- Provide subscriptions via:
  - **Stripe (international recurring payments)** ✅
  - **Razorpay (India)** ✅
    - UPI Autopay/Subscriptions when enabled on Razorpay dashboard
    - Fallback to one-time Razorpay Orders when Subscriptions is not enabled
    - Live re-probe so Autopay switches on without restart
    - **Plan pricing cache hardening** ✅ *(Razorpay Plan cache key includes amount so price changes mint new Razorpay plans)*
  - **PayPal** ⛔ *(planned; still blocked pending user decisions + credentials)*
    - Target: **Recurring subscription** *(user intent indicated; must confirm definitively + provide credentials)*

### Reader experience & engagement
- Bookmarks/reading list ✅
- Reading progress indicators ✅
- Continue-reading strips ✅
- Notifications bell (incl. Lounge reply notifications + deep-link) ✅
- **Reader Highlights** ✅
  - Select-to-highlight in essays
  - Persistent inline highlight rendering
  - Highlights library page
  - **Highlight Notes** ✅ (attach/edit/clear a personal note)
  - **Highlight Sharing** ✅ (download/share/copy a branded quote card)
  - **Share From Article** ✅ (share quote card directly from selection popover)
  - **Popular Highlights** ✅ (Kindle-style most-highlighted markers)
- **Cross-platform sharing** ✅ *(Phase 36)*
  - ShareBar “Share anywhere” now:
    - Uses native share sheet when available (iOS/Android)
    - Falls back to an all-platform dialog with WhatsApp/Telegram/X/LinkedIn/Facebook/Email/Copy Link when native share is unavailable or fails
  - WhatsApp quick-share button added
  - Quote-card sharing never dead-ends: native file share → link share → auto-download with guidance
- **Reading Streaks** ✅ *(Phase 37)*
  - Reward regular readers with a streak counter (current + longest)
  - Updates on article reads (logged-in users; local-calendar-day aware)
  - UI surfaced in Navbar + Account page
- **Streak Milestones + Badges** ✅ *(Phase 39)*
  - Milestones: **7 / 30 / 100** consecutive days
  - Backend persists `streak_badges` (computed from **longest** streak so badges survive streak resets)
  - Article milestone celebration toast + “See badge” deep-link to Account
  - Account page shows badges with earned (accent) vs locked (muted) states
- **Early supporter promo** ✅ *(Phase 38)*
  - First 50 registered users are flagged as early supporters
  - Early supporters can read the first 5 published essays fully (even if premium)
  - Badge shown on Account page
- **Early supporter promo counter** ✅ *(Phase 39)*
  - Public counter endpoint + homepage urgency banner (“X of 50 spots left”) linking to /auth
  - Hidden for premium members / already early supporters / when spots exhausted

### Newsletter & retention
- Weekly digest preview + send ✅
- **Highlight Digest Social Proof** ✅ *(digest includes “Most highlighted this week” block when data exists)*
- **Weekly Listen Digest Social Proof** ✅ *(digest includes “Most listened this week” block when narration listen data exists)*
- Weekly briefings archive + tooling ✅
- **Briefings rollout strategy (Editions 1–6 free)** ✅ *(Phase 38)*
  - Editions ≤ 6 are free to maximize distribution/awareness
  - Briefing template defaults to **free** while `nextEdition <= 6`
- **Briefings weekly autosend** ✅ *(Phase 38)*
  - Every Wednesday **09:30 AM IST**
  - Sends latest briefing as high-level summary (title + intro + section headings + CTA link)
  - Once per ISO week guardrail
  - Toggle: `briefing_autosend` (default ON)
- **Free Edition Countdown banner** ✅ *(Phase 39)*
  - `/briefings` shows “Free through Edition #6” banner
  - Dynamic countdown: remaining free editions until #6 + “Go Premium early” CTA
- **Streak reminder emails** ✅ *(Phase 41)*
  - Evening email when a reader’s streak is about to break (19:00–22:00 IST)
  - Only for users with `current_streak >= 2` who read **yesterday** but not yet today
  - Once/reader/day guardrail via `last_streak_reminder_date`
  - Toggle: `streak_reminder` (default ON)

### Email sending (provider)
- **Gmail SMTP (LIVE)** ✅
- **Resend** ⛔ *(planned; blocked pending user decisions + API key + sender domain verification)*
- **Admin Alerts (Email Notifications)** ✅ *(Phase 37)*
  - Notify admin on:
    - newsletter subscribe
    - paid subscription activation (Stripe + Razorpay)
  - Subject: `tradingnarrative email subscriber`

### Audio narration (ElevenLabs)
- **Essay Audio Narration (ElevenLabs)** ✅ (cached)
- Listen analytics ✅
- Listen completion rate ✅
- Pre-generated narrations ✅ *(warm cache)*
- Narration Status Panel ✅
- Narration sync (Preview → Production) ✅
- Narration hardening (cache corruption protection) ✅
- Narration health alert ✅
- **Audio narration access policy** ✅ *(Phase 38)*
  - Logged-out visitors: narration requires sign-in (**401**)
  - Logged-in free users: **20-second preview clip** (byte-clipped from cached MP3; `X-Audio-Scope: clip`; **no extra ElevenLabs credits**)
  - Premium users: full narration (`X-Audio-Scope: full`)
  - Warmup now generates **full scope only**
- **ElevenLabs credit protection** ✅ *(Phase 41)*
  - Startup warmup caps **NEW narration generations** to **2 per run** (avoids draining credits after large publishes)
  - Admin “Generate missing narrations” action is high-cap (**100**) for deliberate bulk warming

**ElevenLabs operational caveats**
- Credits visibility requires ElevenLabs API key permission `user_read` (current key lacks it).
- Narrations can be restored to production **without new credits** by syncing preview cache to production.

### AI features (Gemini)
- **Gemini 2.5 Flash integration via emergentintegrations + EMERGENT_LLM_KEY** ✅
  - **Admin AI Writing Assistant** ✅ (draft / polish / expand; streaming)
  - **“Ask this essay” reader chat** ✅ (grounded in essay content; paywall-aware; streaming)
- **Ask-essay access model** ✅ *(Phase 40)*
  - Logged-out readers receive **401** (sign-in required)
- Note: Gemini usage consumes the Emergent LLM key credits.

### Admin & growth tooling
- Traffic sources attribution + trends ✅
- Subscriber growth ✅
- Post attribution ✅
- Conversion funnels + plan split ✅
- Post conversion stats (“Essays that convert”) ✅
- CSV export ✅
- **Content Sync Tool (Preview → Production)** ✅
  - Missing-post sync ✅
  - Update-mode sync ✅ (safe allowlist)
- Sync carries normalized author identity ✅

### Community (Premium Lounge)
- Private Community Lounge ✅
- Pins/locks/scheduled announcements/editing ✅
- Member profiles ✅
- **Premium Lounge Hub (hybrid)** ✅ *(Phase 40)*
  - **Market Narrative feed** (editor “raw takes”, reactions)
  - **Early access drafts** (premium-only scheduled posts readable before publish)
  - **Member discussions** (threads + replies)
- **Welcome Market Narrative take** ✅ *(Phase 41)*
  - Seeded once via `welcome_narrative_take_v1`
  - Author: admin (Anish)
  - Tag: `insight`
  - Topic: copper concentrate TC/RC sign flip

### Access model (SIGNED-IN READING)
- **Anonymous browsing allowed, but no essay content unless signed in** ✅ *(Phase 40)*
  - Logged-out users can browse: homepage/archive/briefings lists (titles/excerpts/SEO)
  - Opening any essay requires sign-in (no content blocks returned; `signin_required: true`)
  - Signed-in free users:
    - Full access to **Business & Finance** essays + briefings (Editions 1–6 free)
    - Premium pillars are preview-only (3 blocks) unless entitled
    - Early supporter perk stays (first 5 published essays fully readable for the first 50 readers)
  - Premium users: all pillars + Lounge hub

### Branding + content readiness
- Official logo + favicon ✅
- Author identity: Anish Pujari across UI and post metadata ✅
- Weekly briefing tooling: template + edition numbering + `/briefings` archive ✅
- Import existing writing ✅
  - Edition #1 ✅
  - Edition #2 ✅ *(Phase 38 import)*
- Hardcoded default content ✅ *(real articles are hardcoded and self-heal on DB reset)*
- Spinning logo ✅
- Demo cleanup ✅ *(but can be overridden by admin publishing)*
- Founding Member Wall ✅
- **Catalog publish (demo essays)** ✅ *(Phase 41)*
  - All 12 demo-draft essays published (user explicitly approved)
  - Tier policy applied on publish: `tech-business`/`delivery`/`lifestyle` → premium; `finance` mixed
  - Fully reconciled and synced to production (duplicate-suffix issue resolved; slugs now identical)

### Stability
- Modular backend (routers/services) ✅
- Regression testing discipline ✅
- DB hygiene ✅ *(purged accumulated test users + orphaned billing records)*

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (paywall + subscription state + preview API) ✅ DONE
- Backend-only POC in FastAPI
- Minimal React pages

### Phase 2 — V1 App Development (bulk build) ✅ DONE
- Editorial UI (Tailwind + shadcn/ui)
- Backend CRUD, paywall, baseline analytics
- Frontend pages + Admin Studio
- Seed data

### Phase 3 — Hardening + Feature Completion ✅ DONE
- Validation, loading/empty states
- Security basics
- Expanded tests

### Phase 4 — Payments Integrations (Stripe + Razorpay) ✅ DONE
- Stripe Checkout + entitlement via webhooks/status checks
- Razorpay checkout (autopay detection + fallback order)

### Phase 5 — V2 Admin Analytics + Community ✅ DONE
- Traffic analytics + Admin UI
- Community Lounge

### Phase 6 — V2.2 Enhancements ✅ DONE
- Autopay live re-probe
- Lounge reply notifications
- Weekly traffic trend chart

### Phase 7 — V2.3 Enhancements ✅ DONE
- Post attribution
- CSV export
- Weekly digest autosend + toggle

### Phase 8 — V2.4 Enhancements ✅ DONE
- Conversion funnel analytics
- Gmail SMTP integration
- Member profiles

### Phase 9 — V2.5 Enhancements ✅ DONE
- Email LIVE + verified
- Pillar-personalized digests

### Phase 10 — V2.6 Enhancements ✅ DONE
- One-click unsubscribe + List-Unsubscribe
- Subscriber growth chart
- Digest preview-to-admin

### Phase 11 — Branding + Author Identity + Content Import ✅ DONE
- Logo/favicon
- About page rewrite
- Author identity normalization
- Imported LinkedIn newsletter Edition #1

### Phase 12 — Pillar Cleanup + Briefing Tooling ✅ DONE
- Delivery & Systems pillar
- Weekly briefing template

### Phase 13 — Briefings Series Page + Wednesday Reminder ✅ DONE
- `/briefings` archive
- Reminder loop

### Phase 14 — Article Import: “Freight Management and Tracking Visibility” ✅ DONE

### Phase 15 — Backend Modularization Refactor ✅ DONE

### Phase 16 — Delivery Essay Import ✅ DONE (superseded by later Delivery essay)

### Phase 17 — Reader Highlights + Related ✅ DONE

### Phase 18 — Highlight Notes + Highlight Sharing ✅ DONE

### Phase 19 — PayPal Integration ⛔ NOT STARTED
**Blocked on user decisions + credentials**

### Phase 20 — Production Content Bug Fix + Share From Article + Popular Highlights ✅ DONE

### Phase 21 — Hardcoded Real Content + Highlight Digest + Content Sync Tool ✅ DONE

### Phase 22 — Additional Imports + Production Sync ✅ DONE

### Phase 23 — Series + Social Unfurls + Baseline Essay Audio ✅ DONE

### Phase 24 — ElevenLabs Essay Narration + Caching ✅ DONE

### Phase 25 — Author Normalization + Spinning Logo + Listen Analytics + Pre-Generated Narrations ✅ DONE

### Phase 26 — Narration Status Panel + Demo Cleanup + Warmup ✅ DONE

### Phase 27 — Listen Completion Rate ✅ DONE

### Phase 28 — Weekly Listen Digest ✅ DONE

### Phase 29 — Gemini AI Integration ✅ DONE

### Phase 30 — Narration Bug RCA + Narration Sync Tool ✅ DONE

### Phase 31 — Resend Integration ⛔ NOT STARTED
**Blocked on user decisions + credentials**

### Phase 32 — Narration Corruption Hardening ✅ DONE

### Phase 33 — Narration Health Alert ✅ DONE

### Phase 34 — Delivery Essay Import + Premium Gating ✅ DONE

### Phase 35 — Premium Growth Batch (Plans + Checkout Auth Fix + Narration Restore + Sync Updates) ✅ DONE

### Phase 36 — Founding Member Wall + Cross-Platform Sharing ✅ DONE

### Phase 37 — Reader Engagement + Admin Alerts ✅ DONE
- Reading streaks
- Admin alerts on newsletter signup + paid activation

### Phase 38 — Growth Revamp (Pricing + Briefings + Premium Mix + Early Supporters + Audio Gating) ✅ COMPLETED
**Verified by testing agent iteration_29**: backend 37/37 (100%), frontend 18/19 (95% — one selector skipped, unrelated).

#### A) Edition #2 import ✅
- Imported `The Trading Narrative #2` into briefings archive as **Edition #2**
- Canonical slug fixed to match `slugify()` output:
  - `oil-s-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners`
- Stored in DB + appended to `REAL_POSTS` for durability
- Narration generated and cached

#### B) Briefings free through edition 6 ✅
- Edition #1 flipped back to **free**
- One-time migration: `phase38_tier_strategy_v1`

#### C) Wednesday briefing autosend ✅
- `briefing_autosend_loop` registered (Wed 09:30 IST)
- Sends high-level briefing summary + CTA link
- Once per ISO week; toggle `briefing_autosend` default ON

#### D) Pricing overhaul ✅
- Backend plans:
  - Monthly ₹99 / $1.04
  - Annual ₹999 / $10.50
  - Founding monthly ₹458 / $4.80 (`founding_monthly`)
  - Founding annual ₹5,499 / $57.69 (`founding`)
- Frontend PricingPage updated; founding card respects monthly/annual toggle
- Razorpay plan minting now interval-driven
- Founding wall includes `founding_monthly`

#### E) Premium mix by category ✅
- Published essays in `tech-business`, `delivery`, `lifestyle` are premium
- Finance remains mixed
- Seed tiers updated for durability

#### F) Early supporter promo ✅
- First 50 registered users flagged (startup top-up + register + magic-link)
- Early supporter unlock of first 5 published essays implemented via `early_unlock`
- `public_user()` exposes flag; Account page badge added

#### G) Audio gating ✅
- Anonymous: 401 sign-in required
- Free logged-in: 20s clip (160000 bytes) with `X-Audio-Scope: clip`
- Premium: full audio
- Warmup now full-only; admin narration health expects only full
- Frontend narrator: lock icon + sign-in toast + “free preview” label + upgrade CTA

#### H) Production content ops ✅
- Production sync executed:
  - Edition #2 created on production
  - Tier flips pushed (Ed1 free; categories premium)
  - Narrations pushed (including Ed2)
- Slug mismatch issue resolved (no duplicate risk on redeploy)

### Phase 39 — Engagement Boosters (Countdown + Milestones + Promo Counter) ✅ COMPLETED
**Verified by testing agent iteration_30**: backend 10/10 (100%), frontend 3/3 (100%).

#### A) Free Edition Countdown banner ✅
- `/briefings` page shows a “Free through Edition #6” banner (`briefings-free-banner`)
- Dynamic countdown of remaining free editions until #6
- “Go Premium early” CTA links to `/pricing`

#### B) Streak Milestone badges ✅
- Backend:
  - Streak endpoint returns `milestone` when hitting **7 / 30 / 100**
  - Persists `streak_badges` based on **longest streak** (badges survive streak resets)
  - Exposed via `public_user()` and `/auth/me`
- Frontend:
  - ArticlePage shows celebration toast on milestone + “See badge” action to `/account`
  - AccountPage displays 3 badges with earned vs locked states

#### C) Early supporter promo counter + homepage banner ✅
- Backend:
  - Public `GET /api/early-supporters` returns `{limit, taken, left}`
- Frontend:
  - Homepage accent banner: “Early supporter offer — X of 50 spots left” (`early-supporter-banner`)
  - Links to `/auth`
  - Hidden when:
    - spots are exhausted
    - user is already an early supporter
    - user is premium

### Phase 40 — Access Model + Premium Lounge Hub (Hybrid) ✅ COMPLETED
**Verified by testing agent iteration_31**: backend 30/30 (100%), frontend flows 100%.

#### A) Anonymous essay gate (no content blocks when logged out) ✅
- Backend (`posts.get_post`):
  - When `user is None`, returns `signin_required: true` with **zero** content blocks for all essays
  - Keeps SEO/unfurl fields intact: title/excerpt/tags/cover
  - Listings unchanged (homepage/archive/briefings still show titles/excerpts)
- Backend (AI): `ask-essay` requires sign-in (401 logged-out)
- Frontend (`ArticlePage`):
  - Logged-out visitors see a dedicated sign-in gate card (`signin-gate-container`)
  - Copy varies depending on free vs premium tier (free reads vs premium unlock)
  - Premium paywall copy refreshed to mention Lounge perks + ₹99 entry pricing
- Frontend (`AskEssayWidget`):
  - Logged-out visitors see locked sign-in card (`ask-essay-widget-locked`)

#### B) Market Narrative feed (Premium Lounge) ✅
- Backend:
  - New collection: `narrative_takes`
  - Endpoints:
    - `GET /api/community/narrative` (premium)
    - `POST /api/community/narrative` (admin only: body + optional tag)
    - `DELETE /api/community/narrative/{id}` (admin)
    - `POST /api/community/narrative/{id}/react` (premium: toggle reaction)
  - Reactions supported: 📈 / 📉 / 💡
  - One reaction per member; toggle removes; switching updates
  - Tags supported: `bullish` / `bearish` / `insight`
- Frontend:
  - “Market Narrative” tab in Lounge
  - Reaction buttons with live counts
  - Admin composer + tag chips

#### C) Early Access drafts (Premium Lounge) ✅
- Backend:
  - `GET /api/community/early-access` lists scheduled posts (`status=scheduled`, `publish_at > now`) for premium
  - `get_post`: premium + admin can read scheduled posts before publish with:
    - `early_access: true`
    - `publish_at` returned
- Frontend:
  - “Early access” tab lists upcoming drafts
  - Article page displays early-access notice banner (`early-access-notice`)

#### D) Lounge hub UI as a hybrid destination ✅
- Frontend (`CommunityPage`):
  - Announcements remain left column
  - Main column is a tabbed hub:
    - Market Narrative
    - Discussions
    - Early access
  - Locked-gate copy updated to sell the new perks

#### E) Testing + hygiene ✅
- Automated testing agent: iteration_31
- Test data cleaned (11 real users preserved)

### Phase 41 — Catalog Publish + Welcome Take + Streak Reminders ✅ COMPLETED
**Status: COMPLETED (content + ops), with production reconciled.**

#### A) Publish all demo-draft essays ✅
- User explicitly approved publishing all 12 demo essays.
- In preview DB, promoted the 12 demo posts from `draft` → `published`.
- Applied tier policy on publish:
  - `tech-business` / `delivery` / `lifestyle` → `premium`
  - `finance` → mixed (some free, some premium)

#### B) Sync to production + duplicate reconciliation ✅
- First sync created **suffixed duplicate slugs** because production still held the originals as drafts.
- Fixed safely by:
  - Deleting the **12 suffixed duplicates** on production via production admin API
  - Deleting the **12 old drafts** on production via production admin API
  - Re-syncing from preview → production
- Final state:
  - **18 published posts** in preview and production
  - **No missing/outdated drift**
  - **Identical slugs** confirmed

#### C) Welcome Market Narrative take seeded ✅
- One-time migration: `welcome_narrative_take_v1`
- Ensures Lounge isn’t empty after redeploy / DB reset

#### D) Streak reminder emails ✅
- Implemented `send_streak_reminders()` + `streak_reminder_loop`
- Window: **19:00–22:00 IST**, checks every 15 minutes
- Guardrails:
  - Once/reader/day via `last_streak_reminder_date`
  - Only `current_streak >= 2`, read **yesterday** but not today
  - Direct-tested: sends once, idempotent, skips users who already read today

#### E) ElevenLabs credit protection ✅
- Startup narration warmup capped at **2 new generations per run**
- Admin-triggered warmup allowed up to **100**
- After publishing 12 new essays, narrations will fill:
  - 2 per restart automatically, and/or
  - on first play (listener-triggered)

---

## 3) Next Actions

### A) Production rollout (required)
- **Redeploy production** to ship the Phase 37–41 code changes to https://thetradingnarrative.com:
  - Anonymous essay gate
  - Ask-essay sign-in gate
  - Lounge hub tabs + Market Narrative + Early access
  - Streaks + milestone badges
  - Pricing updates + audio gating + early supporters
  - Streak reminder loop
  - ElevenLabs warmup generation cap

### B) Post-publish ops (recommended)
- In Admin Studio, quickly review:
  - Each newly published demo essay category + tier
  - Cover images + excerpts
  - Ensure no unintended “featured” flags

### C) Narration ops
- Option 1 (safe): allow narrations to fill on first play.
- Option 2 (controlled): use Admin “Generate missing narrations” and stop if credits begin to drop.

### D) Lounge operational playbook (content cadence)
- Create a weekly rhythm:
  - 2–3 Market Narrative takes per week (mid-week + expiry after close)
  - 24h early draft posting before public publish
  - One pinned “discussion prompt of the week” thread

### E) Upcoming (still blocked)
- **PayPal Checkout** (recurring subscriptions) ⛔
  - Need PayPal client ID + secret and final flow decisions
- **Resend Integration** ⛔
  - Need Resend API key + verified sender domain

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe checkout works.
✅ Razorpay checkout works; plan cache mints new plans on price changes.
✅ Email sending is LIVE with unsubscribe + digest systems.
✅ Highlights system complete.
✅ Admin analytics complete.
✅ Narration ops are self-serve and hardened.
✅ AI features work (writing assistant + ask-essay).
✅ Cross-platform sharing works.
✅ Founding wall works.

✅ Phase 37 delivered
- Reading streaks visible and correct
- Admin alerts on newsletter + paid activations (subject exactly `tradingnarrative email subscriber`)

✅ Phase 38 delivered
- Edition #2 imported + archived
- Briefings free through edition 6
- Wednesday 09:30 IST briefing autosend
- New pricing + founding monthly plan
- Category premium strategy applied
- Early supporters entitlement live
- Audio gating live (401 anon, 20s clip free, full premium)
- Production content synced; slug mismatch resolved

✅ Phase 39 delivered
- Free Edition Countdown banner on briefings
- Streak milestone badges (7/30/100) with celebration + account display
- Promo counter endpoint + homepage urgency banner

✅ Phase 40 delivered
- Logged-out users can browse but cannot read any essay content (sign-in required)
- Ask-essay AI requires sign-in
- Premium Lounge hub includes:
  - Market Narrative feed (admin posts + reactions)
  - Early access drafts (scheduled posts readable early)
  - Discussions (threads + replies)

✅ Phase 41 delivered
- All 12 demo essays published and categorized/tiered
- Production duplicates resolved; preview/prod slugs identical; diff clean
- Welcome Market Narrative take seeded
- Evening streak reminder email system implemented and tested
- ElevenLabs warmup generation cap added

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
