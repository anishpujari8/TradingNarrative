# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium model.
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
  - **PayPal** ⛔ *(planned; still blocked pending user decisions + credentials)*
    - Target: **Recurring subscription** (user intent confirmed, exact config pending)
- Deliver retention UX:
  - Bookmarks/reading list ✅
  - Reading progress indicators ✅
  - Continue-reading strips ✅
  - Notifications bell (incl. Lounge reply notifications + deep-linking) ✅
  - **Reader Highlights** ✅
    - Select-to-highlight in essays
    - Persistent inline highlight rendering
    - Highlights library page
    - **Highlight Notes** ✅ (attach/edit/clear a personal note)
    - **Highlight Sharing** ✅ (download/share/copy a branded quote card)
    - **Share From Article** ✅ (share quote card directly from selection popover)
    - **Popular Highlights** ✅ (Kindle-style most-highlighted markers)
  - Weekly digest preview + send ✅
  - **Highlight Digest Social Proof** ✅ *(digest includes “Most highlighted this week” block when data exists)*
  - **Essay Audio Narration (ElevenLabs)** ✅ *(high-quality TTS; cached per essay; paywall-aware preview audio for non-entitled users)*
  - **Listen analytics for narration** ✅ *(count plays; show “Listens” in Admin analytics next to page views; one listen per essay visit)*
  - **Listen completion rate** ✅ *(milestone funnel: 25% / 50% / 75% / finish + completion % per essay in Admin Narrations)*
  - **Pre-generated narrations** ✅ *(warm cache on startup + when posts are published/updated so playback is instant when cached)*
    - **Operational constraint**: if ElevenLabs credits are exhausted, uncached essays return **502** on play until credits are topped up.
  - **Narration Status Panel** ✅ *(Admin self-service for narration coverage + warmup trigger)*
    - Shows narrated coverage (X/Y), cached/missing per essay, audio size, listens
    - Shows completion rate + milestone funnel tooltips
    - “Generate missing narrations” one-click warmup
    - Auto-refresh while warmup is running
    - Credits display depends on ElevenLabs API key permissions (see caveat below)
- Deliver admin + growth tooling ✅:
  - Traffic sources attribution + trends
  - Subscriber growth
  - Post attribution
  - Conversion funnels + plan split
  - Post conversion stats (“Essays that convert”)
  - CSV export
  - **Content Sync Tool (Preview → Production)** ✅ *(one-click admin sync for missing published posts)*
  - **Sync carries normalized author identity** ✅ *(author object is normalized to “Anish Pujari” by startup migration; production will self-heal on next redeploy)*
- Deliver premium community ✅:
  - Private Community Lounge
  - Pins/locks/scheduled announcements/editing
  - Member profiles
- Newsletter operations (production-ready) ✅:
  - Subscriber capture + preferences
  - **Real email sending via Gmail SMTP is LIVE**
  - One-click unsubscribe + List-Unsubscribe
  - Pillar-personalized weekly digests
  - Friday autosend toggle
  - Digest preview email to admin
  - Wednesday briefing reminder toggle
- Branding + content readiness ✅:
  - Official logo + favicon
  - Author identity: Anish Pujari across UI and post metadata ✅ *(enforced via startup migration)*
  - Weekly briefing tooling: template + edition numbering + `/briefings` archive
  - Import existing writing (LinkedIn newsletter editions + LinkedIn articles)
  - **Hardcoded default content** ✅ *(real articles are hardcoded and self-heal on DB reset)*
  - **Spinning logo** ✅ *(slow, elegant rotation ~9s per turn; respects reduced motion)*
  - **Demo Cleanup** ✅ *(sample/demo essays auto-drafted so credits are spent on real writing)*
- Improve editorial discovery ✅:
  - **Related essays by tags** (shared tags prioritized over category-only)
  - **Author/Editorial Series** ✅ (config-driven collections like “Trading Operations”)
- Growth/sharing UX ✅:
  - **LinkedIn Preview Cards / Social unfurls** ✅ (per-essay OG/Twitter meta served at `/api/share/{slug}`)
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests.
- **Stability** ✅: Modular backend (monolith `server.py` split into routers/services) with regression testing.

**ElevenLabs credits visibility caveat**
- The current ElevenLabs API key lacks the **`user_read`** permission, so the system cannot display credits remaining/used.
- Narration generation still works (when credits exist). To see credits in the Admin panel, enable **User → Read** permission for the key in ElevenLabs.

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (paywall + subscription state + preview API) ✅ DONE
- Backend-only POC in FastAPI
- Minimal React pages
- POC test checklist

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
- Razorpay checkout (autopay detection + fallback order if not enabled)
- Frontend supports both checkout modes

### Phase 5 — V2 Admin Analytics + Community ✅ DONE
- Traffic analytics + Admin UI
- Community Lounge (premium-only) with threads/announcements

### Phase 6 — V2.2 Enhancements ✅ DONE
- Autopay live re-probe
- Lounge reply notifications + deep-link
- Weekly traffic trend chart
- Pinned discussions

### Phase 7 — V2.3 Enhancements ✅ DONE
- Post attribution
- CSV export
- Weekly digest autosend + toggle
- Thread lock

### Phase 8 — V2.4 Enhancements ✅ DONE
- Conversion funnel analytics + Admin UI
- Gmail SMTP integration (later switched to LIVE)
- Member profiles
- Scheduled announcements

### Phase 9 — V2.5 Enhancements ✅ DONE
- Email LIVE + verified
- Pillar-personalized digests
- Announcement edit/reschedule
- Funnel plan split

### Phase 10 — V2.6 Enhancements ✅ DONE
- One-click unsubscribe + List-Unsubscribe
- Subscriber growth chart
- Digest preview-to-admin
- Post conversion stats

### Phase 11 — Branding + Author Identity + Content Import ✅ DONE
- Official logo + favicon
- About page rewritten with Anish Pujari bio + headshot
- Author identity seeded across DB
- Imported LinkedIn newsletter Edition #1
- Heading convention support for article rendering

### Phase 12 — Pillar Cleanup + Briefing Tooling ✅ DONE
- Travel pillar removed → Delivery & Systems (`delivery`)
- Weekly briefing template button
- Edition numbers in posts + badges in UI

### Phase 13 — Briefings Series Page + Wednesday Reminder ✅ DONE
- `/briefings` archive page
- `GET /api/briefings`
- Wednesday briefing reminder loop + admin toggle

### Phase 14 — Article Import: “Freight Management and Tracking Visibility” ✅ COMPLETED
- Imported and verified under `category=tech-business` and published

### Phase 15 — Backend Modularization Refactor ✅ COMPLETED
- Split `server.py` into modules:
  - `config.py`, `db.py`, `utils.py`, `security.py`, `schemas.py`
  - `services/` (emailer, stripe, razorpay, digest, tts)
  - `routers/` (auth, posts, billing, razorpay_routes, newsletter, analytics, community, admin, highlights, sync)
- Route parity verified; background loops confirmed running
- Regression testing complete; test data cleaned

### Phase 16 — Delivery & Systems Article Import ⛔ BLOCKED (waiting on user content)
- Awaiting user to paste delivery-focused essay text
- Import as `category="delivery"` and verify on frontend
- After import: append to `REAL_POSTS` for durability

### Phase 17 — Reader Highlights + Related By Tags ✅ COMPLETED
#### A) Reader Highlights ✅
- Backend routes:
  - `POST /api/highlights` (substring validation + paywall-aware)
  - `GET /api/highlights` (optional `?slug=`)
  - `DELETE /api/highlights/{id}`
- Frontend:
  - Floating selection UX
  - Inline `<mark class="reader-highlight">` rendering
  - `/highlights` library page + navbar link

#### B) Related By Tags ✅
- `GET /api/posts/{slug}` related posts now scored by shared tags (weighted) + category

### Phase 18 — Highlight Notes + Highlight Sharing ✅ COMPLETED
#### A) Highlight Notes ✅
- Backend:
  - `HighlightIn` schema gained optional `note` (max 500 chars) stored on create
  - New endpoint: `PUT /api/highlights/{id}/note` (owner-only; empty string clears; sets `note_updated_at`)
- Frontend `/highlights`:
  - Notes UI + inline editor + toasts

#### B) Highlight Sharing ✅
- Frontend:
  - `QuoteCardDialog` with branded share card
  - Actions: Copy image, Share, Download PNG
  - Share-from-article + share-from-highlights
- Testing:
  - Iteration_13: backend 12/12 (100%), frontend 100%

### Phase 19 — PayPal Integration ⛔ NOT STARTED (still blocked)
**Blocked on user decisions + credentials**
- Confirm:
  1) **Recurring subscription** vs one-time timed passes *(user intent: recurring; please confirm definitively)*
  2) Sandbox vs Live credentials (**Client ID + Secret**)
  3) Placement on pricing page (always visible vs international-only)

**Planned steps (once unblocked)**
- Add env vars:
  - `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV` (sandbox/live)
- Backend:
  - Create PayPal service wrapper
  - Add endpoints:
    - create subscription
    - capture/verify
    - webhooks for lifecycle events
- Frontend:
  - Add PayPal option on pricing page
- Testing:
  - Sandbox end-to-end flow

### Phase 20 — Production Content Bug Fix + Share From Article + Popular Highlights ✅ COMPLETED
- Fixed production content visibility via production migration
- Share-from-article popover: Highlight | Share
- Popular highlights markers + backend aggregation

### Phase 21 — Hardcoded Real Content + Highlight Digest + Content Sync Tool ✅ COMPLETED
- `REAL_POSTS` self-healing content
- Digest includes “Most highlighted this week” section
- Admin Sync Tool: preview → production diff + push

### Phase 22 — Two Article Imports + Production Sync ✅ COMPLETED
- Imported 2 essays, appended to `REAL_POSTS`, synced to production

### Phase 23 — Series + Social Unfurls + Baseline Essay Audio ✅ COMPLETED
- Series page + series banner
- `/api/share/{slug}` unfurl HTML
- Baseline audio (superseded by ElevenLabs)

### Phase 24 — ElevenLabs Essay Narration + Caching ✅ COMPLETED
- High-quality narration via ElevenLabs
- MongoDB caching keyed by `(slug, voice, scope)`
- Paywall-aware preview vs full audio

### Phase 25 — Author Normalization + Spinning Logo + Listen Analytics + Pre-Generated Narrations ✅ COMPLETED
- Author normalized to “Anish Pujari” via startup migration
- Spinning logo (9s) in navbar + footer
- Listen tracking endpoint + admin analytics display
- Startup warmup + publish/update warm hooks; quota-aware

### Phase 26 — Narration Status Panel + Demo Cleanup + Credit Refill Warmup ✅ COMPLETED
> Goal: make narration ops fully self-serve for admin and reduce credit burn.

#### A) Narration Status Panel (Admin → Narrations tab) ✅
- Backend:
  - `GET /api/admin/narrations` returns warmup state + cache coverage + per-essay narration status
  - `POST /api/admin/narrations/warm` triggers background warmup (`warm_all_narrations`) guarded by `WARMUP_STATE`
- Frontend:
  - New Narrations tab
  - Table: Cached/Missing status, audio size, listens
  - Button: Generate missing narrations
  - Auto-refresh while warming

#### B) Demo Cleanup ✅
- One-time migration:
  - Uses `db.migrations` marker `unpublish_demo_posts_v1`
  - Unpublishes demo/sample essays (sets to `draft`) so they don’t consume narration credits
- Status:
  - Preview: unpublished 9 demo essays; now only **4 real essays** are published
  - Production: same migration will apply once after redeploy

#### C) Credit Refill Warmup ✅
- Workflow:
  - Top up ElevenLabs credits
  - Admin clicks Generate missing narrations
  - Warmup fills missing caches
- Current state (preview): **3/4** published essays have cached narration; 1 remains missing and will generate after credit top-up.

### Phase 27 — Listen Completion Rate ✅ COMPLETED
> Goal: understand how far readers listen into narrations.

#### A) Backend ✅
- New schema: `AudioProgressIn` in `schemas.py`
- New endpoint: `POST /api/posts/{slug}/audio/progress` with `{ milestone: 25|50|75|100 }`
  - Increments `posts.listen_milestones.{milestone}`
  - Validations:
    - 400 on invalid milestone
    - 404 on bad slug
- `GET /api/admin/narrations` now returns per-essay:
  - `milestones: {25,50,75,100}`
  - `completion` = `round(100 * min(finished, listens) / listens)` (None if listens=0)

#### B) Frontend ✅
- `AudioNarrator` reports milestones **once per essay visit**:
  - 25/50/75 triggered in `ontimeupdate`
  - 100 triggered on `onended`
- Admin → Narrations table gained **Completion** column:
  - Shows `{completion}% finish` or “No listens yet”
  - Hover tooltip shows the full milestone funnel counts

#### C) Verification ✅
- End-to-end verified:
  - Playback fired 1 listen + 4 milestone calls
  - Admin displayed completion (example observed: 67% finish)

---

## 3) Next Actions

### A) Immediate
1) **Production rollout**
   - Redeploy backend + frontend to `thetradingnarrative.com` to pick up Phases **25–27**.
   - After redeploy, production will:
     - Normalize author identity automatically on startup
     - Draft demo essays via demo cleanup migration
     - Enable narration status panel + warmup endpoints + completion tracking

2) **ElevenLabs operations**
   - Top up ElevenLabs credits.
   - (Optional) Update the ElevenLabs API key permissions to include **User → Read** so credits show in the Narrations panel.
   - Then use **Admin → Narrations → Generate missing narrations** to warm everything.

3) **Delivery & Systems**: Import a real delivery-focused essay ⛔
   - Blocked until you paste the article text
   - After import:
     - publish under `category="delivery"`
     - append to `REAL_POSTS` for durability
     - (optional) sync to production via the Sync tool

4) **More Editions**: Import LinkedIn newsletter editions as numbered briefings
   - ⛔ Blocked until you paste Edition #2 text.
   - After import: append to `REAL_POSTS` for durability.

5) **PayPal (Recurring subscriptions)**
   - Still blocked until you provide:
     - Confirm recurring subscription (yes/no)
     - Sandbox vs Live
     - PayPal Client ID + Secret
     - Pricing page placement preference

### B) Production note (workflow)
- Two environments exist:
  - **Preview** (dev)
  - **Production** (`https://thetradingnarrative.com`) — requires **redeploy** for code changes.
- Content migrations/imports can be pushed via the **Sync to production** tool.
- Ensure production has `ELEVENLABS_API_KEY` set; otherwise narration endpoints return **503**.

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe recurring checkout works and updates entitlements.
✅ Razorpay INR checkout works (autopay if enabled, fallback order if not).
✅ Email sending is LIVE (Gmail SMTP) with unsubscribe + digest systems.
✅ Community lounge features work.
✅ Briefings tooling and `/briefings` archive works.
✅ Backend modularization complete with regression tests.
✅ Highlights system complete (create/list/delete, notes, sharing, popular highlights, digest social proof).
✅ Content Sync Tool works (preview → production).
✅ Default content durability via `REAL_POSTS`.
✅ Series pages and social preview cards work.
✅ Essay audio narration works with:
- Paywall-aware scopes (preview vs full)
- Caching
- Listen analytics
- Completion milestones + completion %
- Pre-generation hooks
✅ Phase 26–27 success criteria
- Admin can view narration coverage and cached/missing status per essay.
- Admin can view completion rate per essay (finish % + milestone funnel).
- Admin can start a warmup run from the UI.
- Demo essays do not consume narration credits (auto-drafted once).
- Credits display is available when ElevenLabs API key includes `user_read` permission.

⚠️ Operational caveat (ElevenLabs quota)
- If credits are exhausted, uncached essays will 502 on narration play until credits are topped up.

⛔ PayPal integration: blocked until credentials + final decisions.
⛔ Content imports: blocked until you paste Edition #2 text and the Delivery essay.
