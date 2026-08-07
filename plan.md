# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium model.
- Support **four pillars/themes** (aligned with the updated author bio):
  - **Tech & AI** (`tech-business`)
  - **Business & Finance** (`finance`)
  - **Personal Growth** (`lifestyle`) *(DB slug; displayed as Personal Growth)*
  - **Delivery & Systems** (`delivery`) ✅ (replaces Travel)
- Provide subscriptions via:
  - **Stripe (international recurring payments)**
  - **Razorpay (India)** with automatic capability detection:
    - **UPI Autopay/Subscriptions** when enabled on the Razorpay dashboard
    - **Fallback to one-time Razorpay Orders** (time-bound access) when Subscriptions is not enabled
    - **Live Autopay switch-on**: throttled capability re-check so Autopay activates automatically once enabled (**no backend restart required**)
  - Locale detection + **manual currency toggle**.
- Deliver retention UX:
  - Bookmarks/reading list
  - Reading progress indicators
  - Continue-reading strips
  - Notifications bell (incl. **Lounge reply notifications + deep-linking**)
  - Weekly digest preview + send
- Deliver admin + growth tooling:
  - **Traffic Sources Analytics** (referrers + UTM attribution)
  - **Traffic Trends** (weekly source trend chart)
  - **Subscriber Growth Trend** (weekly new + cumulative subscribers)
  - **Post Attribution** (landing pages by source)
  - **Conversion Funnel analytics** (source → pricing → checkout-start → premium)
  - **Funnel Plan Split** (monthly vs annual conversions per source)
  - **Post Conversion Stats** (“Essays that convert”)
  - **CSV export** of traffic breakdown (sources/referrers/campaigns/landing pages)
- Deliver premium community:
  - **Private Community Lounge** (premium-only announcements + discussion threads)
  - Enhancements: **pinned discussions, thread lock, member profiles, Lounge reply notifications**
  - **Scheduled announcements** (publish later) + **announcement editing/rescheduling**
- Newsletter operations (production-ready):
  - Subscriber capture + account-level email preferences
  - **Real email sending via Gmail SMTP is LIVE** (App Password configured) + admin status
  - **One-click unsubscribe** on all marketing emails (digest/issue/welcome) with **List-Unsubscribe** header
  - **Pillar-personalized weekly digests** based on subscriber preferences
  - **Weekly digest autosend every Friday (UTC)** with admin toggle
  - **Digest preview email to admin** before sending to all subscribers
  - **Wednesday briefing reminder** email nudge if the week’s briefing isn’t published (admin toggle)
- Branding + content readiness:
  - Use the **official The Trading Narrative logo** across the UI (navbar/footer/mobile + favicon)
  - Use **Anish Pujari** author identity + updated About page + headshot across pages and post metadata
  - Import existing writing (LinkedIn newsletter + standalone LinkedIn articles) into posts
  - Add briefing operational tooling:
    - **Weekly briefing template** (THE BOARD + five numbered sections) ✅
    - **Edition numbering** (Edition #1, #2…) with UI badges ✅
    - **Briefings series archive page** `/briefings` ✅
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests.
- **Stability objective (COMPLETED)**: Remove large-file edit risk by modularizing the backend monolith (`/app/backend/server.py`) into routers/services with regression testing. ✅

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) (paywall + subscription state + preview API) ✅ DONE
**User stories**
1. As a reader, I can open a premium article and only receive a short preview when not subscribed.
2. As a reader, I can “upgrade” via a mock checkout and immediately unlock full premium content.
3. As a premium user, I always receive full content from the API (not just unblur UI).
4. As a user, I can cancel and immediately revert to preview-only.
5. As an admin, I can mark a post as free or premium and see gating change instantly.

**Steps**
- Backend-only POC in FastAPI.
- Minimal React POC page(s).
- POC test checklist.

### Phase 2 — V1 App Development (bulk build) ✅ DONE
**User stories**
1. Browse homepage, filter by category, find recent posts.
2. Read an article with clean typography, read-time, author bio, related posts.
3. Clear paywall CTA and pricing page with monthly/annual toggle.
4. Account page showing premium badge + billing history.
5. Admin can create/edit/schedule/publish posts and set free/premium tier.

**Steps**
- Editorial UI (Tailwind + shadcn/ui).
- Backend CRUD, paywall, baseline analytics.
- Frontend pages + Admin Studio.
- Seed data.

### Phase 3 — Hardening + Feature Completion ✅ DONE
- Validation, loading/empty states.
- Security basics and anti-leak checks.
- Expanded tests.

### Phase 4 — Payments Integrations (Stripe + Razorpay) ✅ DONE
- Stripe Checkout + webhook entitlement.
- Razorpay: capability probe, fallback to orders, verification/webhook endpoints.
- Live Autopay switch-on via re-probe.
- Frontend supports both order/subscription checkout modes.

### Phase 5 — V2 Admin Analytics + Community ✅ DONE
- Traffic sources attribution + Admin tab UI.
- Community Lounge (/lounge) with announcements, threads, replies, access control.

### Phase 6 — V2.2 Enhancements (Autopay Live Switch-On + Lounge Notifications + Traffic Trends + Pinned Threads) ✅ DONE
- Autopay live re-probe.
- Lounge reply notifications + deep-link.
- Weekly traffic trend chart.
- Pinned discussions.

### Phase 7 — V2.3 Enhancements (Post Attribution + CSV Export + Digest Autosend + Thread Lock) ✅ DONE
- Landing pages by source.
- CSV export.
- Weekly digest autosend + toggle.
- Thread lock.

### Phase 8 — V2.4 Enhancements (Conversion Funnel + Gmail SMTP Email + Member Profiles + Scheduled Announcements) ✅ DONE
- Conversion funnel (sid-based) + Admin UI.
- Gmail SMTP integration (later made LIVE).
- Member profiles dialog.
- Scheduled announcements.

### Phase 9 — V2.5 Enhancements (Email LIVE + Pillar Digests + Announcement Editing + Funnel Plan Split) ✅ DONE
- Gmail SMTP live + verified.
- Pillar-personalized digests.
- Announcement edit/reschedule.
- Funnel split by plan.

### Phase 10 — V2.6 Enhancements (Unsubscribe + Subscriber Growth + Digest Preview Email + Post Conversion Stats) ✅ DONE
- One-click unsubscribe + List-Unsubscribe header.
- Subscriber growth chart.
- Digest preview-to-admin.
- Essays that convert.

### Phase 11 — Branding + Author Identity + Content Import ✅ DONE
- Official logo + favicon applied.
- About page rewritten with Anish Pujari bio + headshot.
- Author identity migrated across DB + seed.
- Imported LinkedIn newsletter Edition #1 as a free featured post.
- Added heading convention (`"## "`) support in article rendering.

### Phase 12 — Pillar Cleanup + Briefing Tooling ✅ DONE
**User stories**
1. As a reader, navigation and pillars match the publication’s real themes.
2. As the author, I can write a weekly briefing quickly with a consistent format.
3. As a reader, I can follow briefings by edition number.

**Steps (DONE)**
- **Travel pillar cleanup**:
  - Renamed Travel → **Delivery & Systems** (`delivery`) across backend + frontend.
  - Updated hero copy + SEO description to match the 4 themes.
  - Migrated 3 sample travel posts → drafts under `delivery` to avoid mismatched public content.
- **Weekly briefing template**:
  - Added one-click button in Admin Editor that loads a full weekly briefing skeleton:
    - THE BOARD strip
    - Five `##` numbered sections
    - Three signals to watch
    - Sign-off
  - Auto-computes the next edition number by scanning existing posts.
- **Edition numbers**:
  - Added optional `edition` field on posts (admin editor input + API serialization).
  - UI badges:
    - Article page: “Edition #N”
    - Post cards: “#N”
  - Set Edition #1 on the imported briefing.

### Phase 13 — Briefings Series Page + Wednesday Reminder ✅ DONE
**User stories**
1. As a reader, I can browse all weekly briefing editions in one place.
2. As the author, I get a simple reminder if I miss the Wednesday cadence.

**Steps (DONE)**
- **Series archive**:
  - Backend: `GET /api/briefings` returns published posts with `edition` sorted by edition desc.
  - Frontend: `/briefings` page showing edition tiles + metadata, with navigation link (desktop + mobile).
  - Article edition badge now links into `/briefings`.
- **Wednesday reminder**:
  - Background loop emails owner Wednesday ≥07:00 UTC if the week’s briefing (post with `edition`) isn’t published.
  - Runs at most once per ISO week.
  - Admin toggle in Admin → Newsletter tab (ON by default):
    - `GET/POST /api/admin/newsletter/briefing-reminder`

### Phase 14 — Article Import: “Freight Management and Tracking Visibility” (Tech & AI) ✅ COMPLETED
**What was done**
- Executed `python /tmp/import_freight.py`.
- Verified via API that the post exists and is published:
  - `slug`: `freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr`
  - `category`: `tech-business`
  - `tier`: `free`
  - Correct author + 46 content blocks.
- Verified via frontend screenshots that:
  - The article renders correctly at `/post/{slug}` with Tech & AI badge, cover image, tags, author.
  - It appears in `/category/tech-business` (and effectively at the top of the listing).

**Exit criteria met**
- Script exits cleanly.
- Post visible on the site and renders correctly.

### Phase 15 — Backend Modularization Refactor (server.py → routers/services) ✅ COMPLETED
**Goal**: Reduce merge/conflict risk and improve maintainability by extracting the ~2170-line monolith into modules.

**What was done**
- Split backend into modules (behavior preserved):
  - `/app/backend/server.py` now a slim entrypoint (app assembly, seed, startup loops, CORS).
  - New modules:
    - `config.py`, `db.py`, `utils.py`, `security.py`, `schemas.py`
    - `services/`:
      - `emailer.py` (Gmail SMTP live + unsubscribe)
      - `razorpay_service.py` (capability probe + plans)
      - `stripe_service.py` (stripe config + entitlement activation)
      - `digest_service.py` (digest build/send + background loops)
    - `routers/`:
      - `auth.py`, `posts.py`, `billing.py`, `razorpay_routes.py`, `newsletter.py`, `analytics.py`, `community.py`, `admin.py`
- **Route parity verified exactly**: 71/71 routes matched vs the monolith.
- **Background loops confirmed running**:
  - Friday digest autosend loop
  - Wednesday briefing reminder loop

**Regression testing**
- Comprehensive regression test “iteration_12”:
  - Backend: **63/66 passed** (remaining 3 were test artifacts: Stripe timeout in the test harness later verified OK; plus two incorrect test assumptions)
  - Frontend: **100% pass** on critical pages (home, category, article, briefings, pricing, lounge)
- Housekeeping: cleaned all leftover test data from DB (throwaway subscribers, test threads/replies, test announcements, test users, stale notifications). Subscriber list restored to only the real subscriber.

**Exit criteria met**
- No route paths changed.
- Backend + frontend smoke/regression tests pass.
- `server.py` reduced to a small entrypoint.

### Phase 16 — Delivery & Systems Article Import ⛔ BLOCKED (waiting on user content)
**Context**: User will paste a Delivery-focused article after the freight import.

**User stories**
1. As a reader, the **Delivery & Systems** pillar is populated with at least one real essay.
2. As the author, I can continue importing additional editions/articles reliably.

**Steps (once content is provided)**
- Receive full text + title from the user.
- Import into `posts` with `category = "delivery"`.
- Verify frontend listing + article render.

---

## 3) Next Actions

### A) Immediate (this week)
1. **Phase 16**: Import the first real **Delivery & Systems** article (blocked until you paste the text).
2. Continue importing additional LinkedIn editions/articles you paste (choose pillar + free/premium per post).

### B) Required setup actions (to fully go-live)
1. **Enable Razorpay Subscriptions** in the Razorpay dashboard to activate true UPI Autopay mandates.
   - The app will switch automatically via the live re-probe (no restart required).
2. **Redeploy to production** (https://insight-hub-484.emergent.host)
   - Current updates were implemented in preview; production requires a redeploy.
3. **Operational safety (email is live)**:
   - Keep Friday digest autosend ON only if you intend to email real subscribers.
   - Keep subscriber list clean (no test emails) to avoid bounces.

### C) Content operations (next editorial steps)
1. Import remaining LinkedIn newsletter editions and any standalone LinkedIn articles.
   - Input format: paste title + full text.
   - Choose per article: Free vs Premium, pillar/category, featured flag, edition number.
2. Fill the new **Delivery & Systems** pillar with real essays (currently drafts only).
3. Establish “Weekly Briefing” cadence:
   - Use template in Admin Editor.
   - Ensure edition increments (Edition #2, #3…).
   - Use **Briefings series page** `/briefings` as the canonical archive.

### D) Optional enhancements (nice-to-haves)
1. Configure `RAZORPAY_WEBHOOK_SECRET` and Stripe webhook secrets in production for stronger signature verification.
2. Analytics upgrades:
   - Funnel segmentation by landing page and currency (USD vs INR)
   - Premium conversion lift per pillar
3. Newsletter upgrades:
   - Double opt-in
   - Dedicated sender domain + SPF/DKIM/DMARC hardening

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe recurring checkout works and updates entitlements via webhook.
✅ Razorpay INR checkout works with:
- Autopay if Subscriptions enabled
- One-time Orders fallback if not
✅ Autopay live switch-on works without restart.
✅ Pricing routes correctly between Stripe (USD) and Razorpay (INR).
✅ Traffic sources visible in Admin with meaningful grouping and UTM campaign visibility.
✅ Weekly traffic trend chart renders and reflects weekly bucketing.
✅ Subscriber growth chart renders and reflects weekly new + cumulative totals.
✅ Post attribution works: landing pages by source.
✅ CSV export works.
✅ Conversion funnel works + plan split.
✅ Post conversion stats (“Essays that convert”) render.
✅ Weekly digest autosend is toggleable and runs on schedule.
✅ Weekly digest is pillar-personalized.
✅ Digest preview email works.
✅ One-click unsubscribe works and emails contain List-Unsubscribe.
✅ Real email delivery is LIVE and verified via Gmail SMTP App Password.
✅ Community Lounge works + pinned threads + locks + member profiles.
✅ Scheduled announcements + editing/rescheduling work.
✅ Branding is consistent: logo in navbar/footer/mobile and favicon updated.
✅ About page reflects the updated Anish Pujari bio and includes real headshot.
✅ Imported LinkedIn newsletter Edition #1 is live as a free featured post with section headings.
✅ Pillar cleanup complete: Travel removed, Delivery & Systems active.
✅ Weekly briefing template exists and auto-suggests the next edition.
✅ Edition badges display on briefings.
✅ Briefings archive page `/briefings` is live and navigable.
✅ Wednesday reminder toggle exists and reminder system is enabled by default.

✅ Freight article import complete:
- Script executed without errors
- Post exists in DB under `tech-business`
- Post renders correctly on frontend

✅ Backend modularization complete:
- `server.py` split into routers/services
- Route parity verified (71/71)
- Background loops confirmed running
- Backend + frontend smoke/regression tests pass

⛔ Delivery & Systems import:
- Blocked until user provides the article text

✅ Testing passes (key iterations):
- Iteration 5–11: feature-level tests from earlier work
- **Iteration 12**: modularization regression test (backend 63/66 with remaining items as test artifacts; frontend 100%)

---

> Engineering note (updated): Backend monolith risk resolved. Continue implementing new features via `routers/` + `services/` to avoid large merge conflicts.