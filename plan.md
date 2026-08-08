# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium → premium conversion model.
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
- Notifications bell (incl. Lounge reply notifications + deep-linking) ✅
- **Reader Highlights** ✅
  - Select-to-highlight in essays
  - Persistent inline highlight rendering
  - Highlights library page
  - **Highlight Notes** ✅ (attach/edit/clear a personal note)
  - **Highlight Sharing** ✅ (download/share/copy a branded quote card)
  - **Share From Article** ✅ (share quote card directly from selection popover)
  - **Popular Highlights** ✅ (Kindle-style most-highlighted markers)

### Newsletter & retention
- Weekly digest preview + send ✅
- **Highlight Digest Social Proof** ✅ *(digest includes “Most highlighted this week” block when data exists)*
- **Weekly Listen Digest Social Proof** ✅ *(digest includes “Most listened this week” block when narration listen data exists)*
- Weekly briefings archive + tooling ✅
  - **Briefings are premium-only** ✅ *(Edition #1 set to premium; new briefing template defaults to premium)*

### Email sending (provider)
- **Gmail SMTP (LIVE)** ✅
- **Resend** ⛔ *(planned; blocked pending user decisions + API key + sender domain verification)*

### Audio narration (ElevenLabs)
- **Essay Audio Narration (ElevenLabs)** ✅ *(high-quality TTS; cached per essay; paywall-aware preview audio for non-entitled users)*
- **Listen analytics** ✅ *(count narration plays; show “Listens” in Admin analytics next to page views; one listen per essay visit)*
- **Listen completion rate** ✅ *(milestone funnel: 25% / 50% / 75% / finish + completion % per essay in Admin Narrations)*
- **Pre-generated narrations** ✅ *(warm cache on startup + when posts are published/updated so playback is instant when cached; quota-aware)*
- **Narration Status Panel** ✅ *(Admin self-service for narration coverage + warmup trigger)*
  - Shows narrated coverage (X/Y), cached/missing per essay, audio size, listens
  - Shows completion rate + milestone funnel tooltips
  - “Generate missing narrations” one-click warmup
  - Auto-refresh while warmup is running
- **Narration sync (Preview → Production)** ✅ *(push cached audio blobs to live site without spending new ElevenLabs credits)*
  - Admin endpoint to import cached audio on the receiver
  - Admin sync endpoint to push preview cache to production
  - Frontend button + dialog in Admin → Narrations
- **Narration hardening (cache corruption protection)** ✅
  - Import endpoint rejects non-MP3 / tiny payloads and refuses suspicious overwrites
  - Serving path auto-purges corrupt cache entries
  - Sync sender skips corrupt/tiny cache entries
- **Narration health alert** ✅ *(warns in Admin when any essay’s audio is missing or corrupt)*
  - Red alert banner on Admin overview + red dot on Narrations tab
  - Distinguishes `missing` vs `corrupt` in Narrations table

**ElevenLabs operational caveats**
- Credits visibility requires ElevenLabs API key permission `user_read` (current key lacks it).
- Narrations can be restored to production **without new credits** by syncing preview cache to production.

**Current audio state (preview)** ✅
- **Phase 35: user credits recharged; warmup completed** ✅
- **All published essays are cached**: **5/5 cached**, **0 health issues**.

### AI features (Gemini)
- **Gemini 2.5 Flash integration via emergentintegrations + EMERGENT_LLM_KEY** ✅
  - **Admin AI Writing Assistant** ✅ (draft / polish / expand; streaming)
  - **“Ask this essay” reader chat** ✅ (grounded in essay content; paywall-aware; streaming)
- Note: Gemini usage consumes the Emergent LLM key credits.

### Admin & growth tooling
- Traffic sources attribution + trends ✅
- Subscriber growth ✅
- Post attribution ✅
- Conversion funnels + plan split ✅
- Post conversion stats (“Essays that convert”) ✅
- CSV export ✅
- **Content Sync Tool (Preview → Production)** ✅
  - **Missing-post sync** ✅
  - **Update-mode sync** ✅ *(Phase 35)*: can update already-live posts (tier/content/featured/etc.) using a safe allowlist
  - Diff endpoint now returns both **missing** and **outdated** posts
  - UI shows New/Update badges and per-action results
- **Sync carries normalized author identity** ✅ *(author object normalized to “Anish Pujari” by startup migration; production self-heals on redeploy)*

### Community
- Private Community Lounge ✅
- Pins/locks/scheduled announcements/editing ✅
- Member profiles ✅

### Branding + content readiness
- Official logo + favicon ✅
- Author identity: Anish Pujari across UI and post metadata ✅ *(enforced via startup migration)*
- Weekly briefing tooling: template + edition numbering + `/briefings` archive ✅
- Import existing writing (LinkedIn newsletter editions + LinkedIn articles) ✅ *(Edition #1 done; #2 pending)*
- **Hardcoded default content** ✅ *(real articles are hardcoded and self-heal on DB reset)*
- **Spinning logo** ✅ *(slow, elegant rotation ~9s per turn; respects reduced motion)*
- **Demo Cleanup** ✅ *(sample/demo essays auto-drafted/unpublished so credits are spent on real writing)*
- **New Delivery essay imported** ✅ *(durable + premium-gated; see Phase 34)*

### Stability
- Modular backend (monolith `server.py` split into routers/services) ✅
- Regression testing discipline ✅

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
  - `routers/` (auth, posts, billing, razorpay_routes, newsletter, analytics, community, admin, highlights, sync, ai)
- Route parity verified; background loops confirmed running
- Regression testing complete; test data cleaned

### Phase 16 — Delivery & Systems Article Import ✅ COMPLETED (superseded by Phase 34)
- ✅ User pasted the delivery essay
- ✅ Imported under `category="delivery"` and published
- ✅ Appended to `REAL_POSTS` for durability

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
- Related posts scored by shared tags + category

### Phase 18 — Highlight Notes + Highlight Sharing ✅ COMPLETED
#### A) Highlight Notes ✅
- Backend: `PUT /api/highlights/{id}/note`
- Frontend: notes UI + inline editor

#### B) Highlight Sharing ✅
- Branded quote card sharing (download/copy/share)

### Phase 19 — PayPal Integration ⛔ NOT STARTED (still blocked)
**Blocked on user decisions + credentials**
- Confirm:
  1) Recurring subscription (confirm definitively)
  2) Sandbox vs Live
  3) PayPal Client ID + Secret
  4) Placement on pricing page

### Phase 20 — Production Content Bug Fix + Share From Article + Popular Highlights ✅ COMPLETED
- Production content visibility fixed
- Share-from-article popover
- Popular highlights markers

### Phase 21 — Hardcoded Real Content + Highlight Digest + Content Sync Tool ✅ COMPLETED
- `REAL_POSTS` self-healing content
- Digest includes “Most highlighted this week”
- Sync tool preview → production

### Phase 22 — Two Article Imports + Production Sync ✅ COMPLETED
- Imported 2 essays, appended to `REAL_POSTS`, synced to production

### Phase 23 — Series + Social Unfurls + Baseline Essay Audio ✅ COMPLETED
- Series page + series banner
- `/api/share/{slug}` unfurl HTML

### Phase 24 — ElevenLabs Essay Narration + Caching ✅ COMPLETED
- ElevenLabs narration + cache
- Paywall-aware audio scope

### Phase 25 — Author Normalization + Spinning Logo + Listen Analytics + Pre-Generated Narrations ✅ COMPLETED
- Author normalized
- Spinning logo
- Listen tracking
- Startup warmup + publish/update warm hooks

### Phase 26 — Narration Status Panel + Demo Cleanup + Credit Refill Warmup ✅ COMPLETED
- Narrations tab + warm trigger
- One-time demo unpublish migration
- Self-service warmup flow

### Phase 27 — Listen Completion Rate ✅ COMPLETED
- Milestone reporting endpoints + UI completion column

### Phase 28 — Weekly Listen Digest ✅ COMPLETED
- Digest includes “Most listened this week” based on narration listen analytics

### Phase 29 — Gemini AI Integration (Gemini 2.5 Flash) ✅ COMPLETED
> Two features: Admin writing assistant + “Ask this essay” reader chat.

#### A) Backend ✅
- Added `EMERGENT_LLM_KEY` to backend env and config flags:
  - `AI_ENABLED`, `AI_PROVIDER='gemini'`, `AI_MODEL='gemini-2.5-flash'`
- New router: `/app/backend/routers/ai.py`
  - `GET /api/ai/status`
  - `POST /api/admin/ai/assist` (admin-only; `draft|polish|expand`; SSE streaming)
  - `POST /api/posts/{slug}/ask` (public; essay-grounded; paywall-aware; SSE streaming)

#### B) Frontend ✅
- `src/lib/aiStream.js`: fetch-based SSE consumer
- Admin editor:
  - `AiAssistantDialog` wired into `AdminEditorPage` via an “AI assistant” button next to Content
  - Streams output; actions: Replace draft / Append / Copy
- Reader:
  - `AskEssayWidget` on `ArticlePage` (hidden when AI disabled)
  - Streams assistant replies; keeps short client-side history

### Phase 30 — Narration Bug RCA + Narration Sync Tool ✅ COMPLETED
- Production restore path built: push cached preview audio to production without spending new credits.

### Phase 31 — Resend Integration ⛔ NOT STARTED (blocked)
**Blocked on user decisions + credentials**
- Need:
  1) Scope: replace Gmail SMTP for everything vs only newsletter sends
  2) Fallback behavior: keep Gmail SMTP as fallback or Resend-only
  3) Resend API key (`re_...`)
  4) Sender domain status: verified `thetradingnarrative.com` vs `onboarding@resend.dev` test sender

### Phase 32 — Recurring Narration Bug: True Root Cause + Permanent Hardening ✅ COMPLETED
- Import endpoint hardened; serving path purges corrupt cache; sync skips tiny entries.

### Phase 33 — Narration Health Alert ✅ COMPLETED
- Admin alert banner + tab dot; backend health flags and issues.

### Phase 34 — Delivery Essay Import + Premium Gating ✅ COMPLETED
- Delivery longform essay imported, premium-only.
- Weekly briefing edition #1 made premium-only.

### Phase 35 — Premium Growth Batch (Plans + Checkout Auth Fix + Narration Restore + Sync Updates) ✅ COMPLETED
**Verified by testing agent iteration_26 (frontend 100%; backend pass; one tester probe targeted a nonexistent endpoint).**

1) **Narration resolved** ✅
- User recharged ElevenLabs credits (paid).
- Warmup regenerated missing narrations; preview now has **5/5 cached**, **0 issues**.
- Paywall-aware audio confirmed for premium posts (preview scope for anonymous).
- Note: credits balance display still shows `—` because key lacks `user_read` permission (harmless).

2) **Checkout auth bug fixed** ✅
- “Go Premium annual” when logged out now redirects to **/auth?next=/pricing** with a friendly toast.
- Expired session (401/403) triggers logout + “session expired” toast + auth redirect.

3) **Premium pricing updated per growth plan** ✅
- Backend `PLANS`:
  - Monthly: **$10 / ₹399**
  - Annual: **$100 / ₹3,999**
  - Founding Member: **$250 / ₹9,999**
- Pricing UI: 3 cards (Free / Premium / Founding) + comparison table with Founding-exclusive benefits.

4) **Sync update mode added** ✅
- Sync now updates already-live production posts using a safe allowlist.
- Diff endpoint returns both `missing` and `outdated`.
- UI updated to show New vs Update items and per-action results.
- Verified: diff flags the briefing tier drift on production (five-things should be premium).

---

## 3) Next Actions

### A) Immediate
1) **Production: run “Sync to production” (now includes updates)** ⛔ *(user action)*
   - This will:
     - Create any missing published posts on production
     - **Update existing production posts** whose fields drifted (e.g., Edition #1 briefing tier → premium)

2) **Production: run “Send narrations to live site”** ⛔ *(user action)*
   - Now that preview has 5/5 cached, this will push all cached audio to production without spending new ElevenLabs credits.

3) **Redeploy production** ⛔ *(user action)*
   - Required for:
     - New pricing tiers and amounts
     - Checkout auth redirect fix
     - Sync update mode UI and server code

### B) Upcoming
4) **Edition #2 import** ⛔
   - Paste Edition #2 newsletter text.

5) **PayPal (recurring subscriptions)** ⛔
   - Provide PayPal decisions + credentials (Phase 19).

6) **Resend integration** ⛔
   - Answer the 4 setup decisions + provide Resend API key.

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe checkout works (recurring capability ready; test URLs verified).
✅ Razorpay INR checkout works and mints correct-priced plans after price changes.
✅ Email sending is LIVE with unsubscribe + digest systems.
✅ Community lounge features work.
✅ Highlights system complete (highlights, notes, quote cards, popular highlights).
✅ Admin analytics complete (traffic, funnels, conversions, listens, completion).
✅ Narration ops are self-serve (status + warmup) and digest includes:
- “Most highlighted this week”
- “Most listened this week”
✅ Narration production restore path works:
- Production can receive cached audio via narration sync without spending new ElevenLabs credits.
✅ Narration cache is protected against corruption:
- Import rejects invalid/tiny audio
- Serving path purges corrupt cache
- Sync skips corrupt cache
✅ Narration health visibility:
- Admin receives a clear warning whenever any essay is missing/corrupt
✅ AI features:
- Admin AI writing assistant works (draft/polish/expand; streaming)
- “Ask this essay” is grounded + paywall-aware; streaming
✅ Growth-plan pricing:
- Monthly $10/₹399, Annual $100/₹3,999, Founding $250/₹9,999 (UI + backend)
✅ Checkout UX:
- Logged-out users are redirected to /auth instead of seeing “Not authenticated”
✅ Production sync:
- New posts AND drift updates (tier flips, edits) can be synced safely

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on the key.
- Gemini usage consumes Emergent LLM key credits.
- Deployments can be rate-limited; retry after cooldown.

⛔ Blockers
- Edition #2 import: awaiting text.
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
