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
  - **PayPal** ⛔ *(planned; blocked pending user decisions + credentials)*
    - Target: support either recurring subscriptions or one-time timed passes (TBD by user)
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
  - **Essay Audio** ✅ *(browser TTS narrator at top of every article; no API keys/costs)*
- Deliver admin + growth tooling ✅:
  - Traffic sources attribution + trends
  - Subscriber growth
  - Post attribution
  - Conversion funnels + plan split
  - Post conversion stats (“Essays that convert”)
  - CSV export
  - **Content Sync Tool (Preview → Production)** ✅ *(one-click admin sync for missing published posts)*
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
  - Author identity: Anish Pujari across UI and post metadata
  - Weekly briefing tooling: template + edition numbering + `/briefings` archive
  - Import existing writing (LinkedIn newsletter editions + LinkedIn articles)
  - **Hardcoded default content** ✅ *(real articles are hardcoded and self-heal on DB reset)*
- Improve editorial discovery ✅:
  - **Related essays by tags** (shared tags prioritized over category-only)
  - **Author/Editorial Series** ✅ (config-driven collections like “Trading Operations”)
- Growth/sharing UX ✅:
  - **LinkedIn Preview Cards / Social unfurls** ✅ (per-essay OG/Twitter meta served at `/api/share/{slug}`)
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests.
- **Stability** ✅: Modular backend (monolith `server.py` split into routers/services) with regression testing.

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
- Razorpay checkout (autopay detection + fallback to orders)
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
- Wednesday reminder loop + admin toggle

### Phase 14 — Article Import: “Freight Management and Tracking Visibility” ✅ COMPLETED
- Imported and verified under `category=tech-business` and published

### Phase 15 — Backend Modularization Refactor ✅ COMPLETED
- Split `server.py` into modules:
  - `config.py`, `db.py`, `utils.py`, `security.py`, `schemas.py`
  - `services/` (emailer, stripe, razorpay, digest)
  - `routers/` (auth, posts, billing, razorpay_routes, newsletter, analytics, community, admin, highlights)
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
  - Notes UI: StickyNote chip + pencil edit
  - “Add note” affordance on highlights without notes
  - Inline editor (Textarea + char counter + Save/Cancel) + toasts

#### B) Highlight Sharing ✅
- Frontend:
  - New component: `QuoteCardDialog` (`/app/frontend/src/components/QuoteCardDialog.js`)
  - Canvas quote card (1200×630 @2x) with:
    - Branded paper background, frame, masthead, accent square
    - Oversized quote mark
    - Adaptive serif quote sizing + word-wrap
    - Footer: essay title + “— Anish Pujari · {pillar}”
  - Actions: Copy image (ClipboardItem), Share (navigator.share w/ file, fallback), Download PNG
  - Share button added to each highlight card
- Testing:
  - Iteration_13: backend 12/12 (100%), frontend 100%
  - All test data cleaned (highlights purged; throwaway users removed; subscriber list intact)

### Phase 19 — PayPal Integration ⛔ NOT STARTED (blocked)
**Blocked on user decisions + credentials**
- Confirm:
  1) Recurring subscriptions vs one-time timed passes
  2) Sandbox vs Live credentials (Client ID + Secret)
  3) Placement on pricing page (always visible vs international-only)

**Planned steps (once unblocked)**
- Add env vars:
  - `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV` (sandbox/live)
- Backend:
  - Create PayPal service wrapper
  - Add endpoints:
    - checkout/create (order or subscription)
    - capture/verify (order capture or subscription activation)
    - webhooks for lifecycle events (if using subscriptions)
  - Map PayPal purchase → existing `payment_transactions` → `activate_premium_from_transaction`
- Frontend:
  - Add PayPal option on pricing page
  - Payment success/cancel routes consistent with current Stripe/Razorpay UX
- Testing:
  - Sandbox end-to-end flow

### Phase 20 — Production Content Bug Fix + Share From Article + Popular Highlights ✅ COMPLETED
#### A) Production content bug fix (Edition #1 missing; “random” demo articles) ✅
- User-reported bug: “where is my edition 1” and production showed only demo posts.
- Root cause: **production uses a separate fresh DB**, auto-seeded demo/sample essays; real content existed only in preview.
- Fix:
  1) Migrated **Edition #1 briefing** + **Freight Management** post to production via production admin API.
  2) Per user choice: demo/sample essays were **kept** on production for now.
  3) Patched `seed_database` so fresh DBs seed `SAMPLE_POSTS` as **draft** (`status='draft'`, `views=0`) so future deployments start with a clean public site.
- Verification:
  - Verified live (read-only) on production endpoints:
    - `https://thetradingnarrative.com/api/briefings` includes Edition #1.
    - `https://thetradingnarrative.com/api/posts` includes both migrated posts.

#### B) Share From Article ✅
- Article selection popover is now a **two-button pill**: **Highlight | Share**
  - Test IDs: `selection-popover`, `selection-share-button`
- “Share” opens `QuoteCardDialog` directly with the selected text.
- Works for **anonymous** visitors (no need to save a highlight).

#### C) Popular Highlights ✅
- Backend:
  - Public endpoint: `GET /api/posts/{slug}/popular-highlights`
  - Aggregates by `(block_index, text)` counting **distinct users**
  - Threshold: `count >= 2`, returns **top 5**
- Frontend:
  - Article page fetches popular highlights and renders **Kindle-style** markers:
    - `mark.popular-highlight`: dotted accent underline + superscript count + tooltip
  - Personal highlights take precedence over popular markers.
- Testing:
  - Iteration_14: **100% backend (14/14)**, **100% frontend**

### Phase 21 — Hardcoded Real Content + Highlight Digest + Content Sync Tool ✅ COMPLETED
#### A) Hardcoded Real Content (self-healing default content) ✅
- `seed_data.py` includes a `REAL_POSTS` list containing the author’s real, provided content exported verbatim from DB.
- `seed_database()` **always** inserts any missing `REAL_POSTS` (matched by slug) as **PUBLISHED** on every startup.
- Verified self-healing: deleted Edition #1 in preview DB, restarted backend, and it restored automatically with no duplicates.
- Demo `SAMPLE_POSTS` remain and seed as **drafts** only on fresh DBs.

#### B) Highlight Digest (social proof section) ✅
- `services/digest_service.py`:
  - `get_week_top_highlights()` — last 7 days, >=2 distinct users, top 3
  - `_highlights_section()` — renders “Most highlighted this week” block
  - `build_digest_html(posts, top_highlights=...)` conditionally includes the section
- Wired into:
  - `do_send_digest()`
  - `GET /api/admin/newsletter/digest-preview` (returns `top_highlights`)
  - `POST /api/admin/newsletter/send-digest-preview`
- Graceful omission when no highlight data exists.

#### C) Content Sync Tool (Preview → Production) ✅
- Backend:
  - Router: `routers/sync.py`
    - `GET /api/admin/sync/diff`
    - `POST /api/admin/sync/push {password}`
  - Config: `PRODUCTION_SITE_URL` in `config.py` (defaults to `https://thetradingnarrative.com`)
- Frontend:
  - `components/SyncToProductionDialog.js`
  - Admin header button “Sync to production”
- Testing:
  - Iteration_15: **100% backend (10/10)**, **100% frontend**

### Phase 22 — Two Article Imports + Production Sync ✅ COMPLETED
#### A) Imports ✅
1) **Business & Finance**:
   - Title: **“The Shipping Industry Is Sitting on a $15 Billion Problem. And Nobody Is Talking About It Honestly.”**
   - Category: `finance`
   - Tier: `free`
   - Blocks: **41**
   - Tags: `[LNG, Demurrage, Shipping, Logistics, CTRM, Commodities]`
   - Slug: `the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a`

2) **Personal Growth** *(“highlight this article heading” implemented as FEATURED=true)*:
   - Title: **“170 Kilometres, One Green Enfield, and a Lesson in Strategic Momentum”**
   - Category: `lifestyle`
   - Tier: `free`
   - Blocks: **20**
   - Featured: **true**
   - Tags: `[Leadership, Clarity, Motorcycling, Product Management, Momentum]`
   - Slug: `170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum`

#### B) Default content durability ✅
- Both new posts appended to `REAL_POSTS` (now totals **4** real, hardcoded posts).

#### C) Production sync ✅
- Sync tool diff identified 2 missing → pushed **2/2** successfully.

### Phase 23 — Essay Audio + LinkedIn Preview Cards + Trading Operations Series ✅ COMPLETED
#### A) Essay Audio ✅
- New component: `frontend/src/components/AudioNarrator.js`
- Uses browser `speechSynthesis` (no external APIs / keys).
- UX:
  - Play/Pause/Resume
  - Restart
  - Speed select: `0.85×`, `1×`, `1.25×`, `1.5×` (re-speaks current paragraph)
  - Paragraph-by-paragraph utterances (avoids Chrome long-text bug)
  - Progress bar + status label
  - Cancels narration on unmount
- Rendered at the top of every article.

#### B) Trading Operations Series ✅
- New config: `SERIES` in `backend/config.py`
  - Series `trading-operations` contains (in order):
    1) Edition #1 briefing
    2) Freight Management
    3) Demurrage ($15B) essay
- Backend:
  - `GET /api/series` (list)
  - `GET /api/series/{slug}` (ordered posts)
  - `GET /api/posts/{slug}` returns `series: {slug,title}` for member essays
- Frontend:
  - New page: `frontend/src/pages/SeriesPage.js`
  - Route: `/series/:slug`
  - Member article pages show a “Part of the Trading Operations series” banner linking to the series.

#### C) LinkedIn Preview Cards ✅
- Backend:
  - `GET /api/share/{slug}` returns crawler-readable HTML with per-essay OG/Twitter meta
  - Includes meta-refresh + JS redirect for humans
- Frontend:
  - `ShareBar` now shares the `/api/share/{slug}` URL so LinkedIn/X unfurl the correct card
  - `public/index.html` default OG description updated to current pillars (removed “travel”)
- Testing:
  - Iteration_16: **100% backend (29/29)**, **100% frontend (23/23)**

---

## 3) Next Actions

### A) Immediate
1. **More Editions**: Import LinkedIn newsletter editions as numbered briefings
   - ⛔ Blocked until you paste Edition #2 text.
   - After import: append to `REAL_POSTS` for durability.
2. **Delivery & Systems**: Import a real delivery-focused essay
   - ⛔ Blocked until you paste the article text.
   - After import: append to `REAL_POSTS` for durability.
3. **PayPal**: Proceed after you answer:
   - subscriptions vs one-time
   - sandbox/live credentials
   - pricing-page placement

### B) Production note (workflow)
- The app is deployed to production at a custom domain.
- **Two environments exist**:
  - **Preview** (dev): changes are implemented + tested here.
  - **Production** (`https://thetradingnarrative.com`): code changes require **redeploy** to go live.
- Content migrations/imports can be pushed via the **Sync to production** tool.
- Note: Phase 23 code (series, share/unfurl endpoint, audio narrator) is **preview-only until redeploy**; production currently has the content, but will 404 these routes until redeploy.

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe recurring checkout works and updates entitlements.
✅ Razorpay INR checkout works (autopay if enabled, fallback order if not).
✅ Email sending is LIVE (Gmail SMTP) with unsubscribe + digest systems.
✅ Community lounge features work.
✅ Briefings tooling and `/briefings` archive works.
✅ Backend modularization complete with regression tests.
✅ Related essays scored by tags.
✅ Highlights system complete:
- Highlight create/list/delete
- Paywall-aware validation
- Inline mark rendering
- Highlights page
- Notes + quote-card sharing
- Share-from-article
- Popular highlights
✅ Highlight Digest:
- Weekly digest includes “Most highlighted this week” section when highlight data exists
✅ Content Sync Tool:
- Admin can diff and push missing published preview posts to production without manual scripts
✅ Default content durability:
- Real provided articles are hardcoded in `seed_data.py` as `REAL_POSTS`
- Backend self-heals and restores missing `REAL_POSTS` on startup
✅ Trading Operations Series:
- `/series/:slug` page exists and member essays show series banner
✅ Social preview cards:
- `/api/share/{slug}` returns OG/Twitter meta suitable for LinkedIn/X unfurl
✅ Essay audio:
- Each article includes an audio narrator bar (browser TTS)

⛔ PayPal integration: blocked until credentials + mode decisions.
⛔ Content imports: blocked until you paste Edition #2 text and the Delivery essay.
