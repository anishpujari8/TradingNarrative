# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium model.
- Support **three content pillars**: **Tech & AI**, **Business & Finance**, **Personal Growth**.
- Provide international subscriptions via **Stripe (recurring)** and India-first subscriptions via **Razorpay (UPI Autopay/mandates)** with locale/IP or manual currency toggle.
- Deliver strong retention UX: bookmarks/reading list, reading progress, continue-reading strips, notifications, weekly digest previews.
- Add V2 admin + community capabilities:
  - **Traffic Sources Analytics** (referrers/UTM breakdown)
  - **Private Community Lounge** for premium members (announcements + discussion threads)
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests after each phase.

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) (paywall + subscription state + preview API)
**User stories**
1. As a reader, I can open a premium article and only receive a short preview when not subscribed.
2. As a reader, I can “upgrade” via a mock checkout and immediately unlock full premium content.
3. As a premium user, I always receive full content from the API (not just unblur UI).
4. As a user, I can cancel and immediately revert to preview-only.
5. As an admin, I can mark a post as free or premium and see gating change instantly.

**Steps**
- Backend-only POC in FastAPI:
  - Mongo models: User (roles, premium_status), Post (tier, preview_blocks/full_blocks).
  - Endpoints: `GET /api/posts/{slug}` returns preview vs full based on entitlement.
  - Mock subscription endpoints: `POST /api/billing/mock/checkout` (activate premium), `POST /api/billing/mock/cancel` (deactivate), record mock invoices.
- Minimal React POC page(s): Login + Post view verifying that page source never includes full premium content when not entitled.
- POC test checklist: unauth, free user, premium user; verify API responses and DB state transitions.

### Phase 2 — V1 App Development (bulk build)
**User stories**
1. As a visitor, I can browse the homepage, filter by category, and quickly find recent posts.
2. As a reader, I can read an article with clean typography, read-time, author bio, and related posts.
3. As a free user, I can see a clear paywall CTA and pricing page with monthly/annual toggle.
4. As a subscriber, I can access an account page showing premium badge + billing history.
5. As an admin, I can create/edit/schedule/publish posts and set free/premium tier.

**Design first (design_agent)**
- Editorial layout, one accent color, dark mode toggle, Tailwind + shadcn/ui components, responsive templates.

**Backend (FastAPI /api, Mongo)**
- Auth:
  - Email+password (bcrypt + JWT).
  - Magic link (dev-mode) supported.
- Content:
  - Posts CRUD, publish/schedule, categories/pillars, featured flag.
  - Server-side paywall logic: preview paragraphs only for non-premium on premium posts.
  - Search/filter endpoints.
- Newsletter:
  - Subscriber capture endpoints.
  - Weekly digest admin previews.
- SEO/ops:
  - `GET /sitemap.xml`, `GET /robots.txt`.
  - Analytics/events collector (baseline).
- Seed data:
  - Admin user + sample posts across the 3 pillars.

**Frontend (React)**
- Pages:
  - Home, Article, Pillar pages, Archive, Pricing, About.
  - Auth (login/register + magic link), Account/Billing.
  - Admin CMS (posts list, editor, schedule/publish, tier/category toggles).
- Social sharing:
  - Share URLs + Copy Link.
  - Quote-card generator.
- Reading UX:
  - Related-by-interest / For You.
  - Reply threads.
  - Bookmarks/reading list.
  - Reading progress indicator.
  - Continue-reading strip.
  - Notifications bell.

**End Phase 2**
- Run full E2E passes and fix blocking issues.

### Phase 3 — Hardening + Feature Completion
**User stories**
1. As a user, I can reset my password if I forget it.
2. As an admin, I can preview scheduled posts and confirm publish timing.
3. As a writer, I can see validation errors clearly when saving drafts.
4. As a subscriber, I can reliably see my entitlement reflected across devices after login.

**Steps**
- Improve validation, empty/error states, loading skeletons.
- Tighten security basics: token expiry, rate-limit magic link generation, sanitize HTML/markdown.
- Ensure paywall cannot leak full content via list endpoints (only summaries in grids).
- Expand tests.

### Phase 4 — Payments Integrations (Stripe + Razorpay)
**User stories**
1. As a global user, I can pay with real Stripe recurring checkout and return to unlocked premium.
2. As an Indian user, I can pay via Razorpay with UPI Autopay mandates (recurring) and keep access auto-renewed.
3. As a user, I can manage/cancel subscriptions cleanly and see status reflected.
4. As an admin, I can trust webhook-driven entitlement updates.

**Steps**
- Stripe (DONE):
  - Stripe Checkout with auto-renew enabled using real keys.
  - Webhook updates entitlement.
- Razorpay (IN PROGRESS):
  - Implement Razorpay customer + plan + subscription creation flow for UPI Autopay.
  - If Subscriptions feature is not enabled or fails, fallback to one-time Razorpay Orders with a manual renew UX.
  - Wire INR checkout into `PricingPage.js` with locale/IP detection and a manual currency toggle.
  - Store references in DB (`rzp_customer_id`, subscription/order IDs) and update entitlement.
  - Implement/verify Razorpay webhooks.
- Testing:
  - Backend: python/curl tests to create plan/subscription/order, verify auth, verify DB updates.
  - Frontend: checkout initiation, success redirect, entitlement changes.

### Phase 5 — V2 Admin Analytics + Community
**User stories**
1. As an admin, I can see where readers come from (LinkedIn, Instagram, Google, Direct, etc.).
2. As a premium member, I can access a private lounge.
3. As a premium member, I can read admin announcements and participate in discussion threads (post + reply).

**Steps**
- Traffic Sources Analytics (P1):
  - Backend: log `Referer` + UTM parameters on key reads (article views, landing pages).
  - Create endpoint: `GET /api/admin/traffic` returning breakdown (domain → counts, plus “Direct/Unknown”).
  - Frontend: add Admin dashboard UI (in `AdminEditorPage.js` or dedicated admin dashboard) with table + simple chart.
  - Tests: verify referrer capture via curl with `-H 'Referer: ...'` and UI rendering.
- Private Community Lounge (P1):
  - Frontend page: `/app/frontend/src/pages/CommunityPage.js` premium-only.
  - Backend routes: `/api/community/*`:
    - Announcements CRUD (admin create/edit; members read)
    - Threads + replies (premium members create; all premium can reply)
  - Moderation basics: admin delete/hide, rate limiting on posting.
  - Tests: access control (free vs premium), thread/reply creation.

## 3) Next Actions
1. **Phase A (now): Fix Razorpay UPI Autopay**
   - Debug `Unauthorized` / `ServerError` from Razorpay Plan/Subscription APIs.
   - Confirm `razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))` initialization and correct payload formatting.
   - Implement fallback to one-time Orders if Subscriptions are disabled.
   - Wire INR checkout button on Pricing page.
2. **Phase B: Traffic Sources Analytics**
   - Add referrer/UTM logging and build `/api/admin/traffic` + admin UI.
3. **Phase C: Community Lounge**
   - Build premium-only lounge with announcements + discussion threads.
4. After each phase: run backend tests first, then frontend flow verification.

## 4) Success Criteria
- Premium posts never return full content to non-premium users from the API (verified via network + page source).
- Stripe recurring checkout works end-to-end and updates entitlements via webhook (DONE).
- Razorpay for INR users:
  - Subscriptions/UPI Autopay mandate creation works end-to-end OR falls back gracefully to one-time Orders.
  - Pricing page correctly routes users to Stripe vs Razorpay based on locale/toggle.
- Traffic sources visible in admin with meaningful referrer grouping (LinkedIn/Instagram/Google/Direct).
- Premium-only Community Lounge works with announcements + discussion threads (post/reply) and correct access control.
- Test suite/E2E checks pass after each major phase with no regressions.

---
## STATUS UPDATE (post Phase 2)
- Phase 1 (POC): DONE — server-side paywall, subscription transitions, magic link, newsletter, admin gating.
- Phase 2 (V1 app): DONE — full frontend + backend built and tested; share-bar testid issue fixed.

## STATUS UPDATE (post V1.1 feature batch)
- Password reset (mocked email, dev-mode link) DONE.
- Reading progress DONE.
- Premium comments DONE.
- E2E testing iterations passing.

## STATUS UPDATE (post V1.2 feature batch)
- Reply threads DONE.
- Bookmarks/reading list DONE.
- For-You recommendations / related-by-interest DONE.

## STATUS UPDATE (V2.0 — expanded spec applied)
- Notifications bell DONE.
- Continue-reading strip + resume DONE.
- Weekly digest admin previews DONE.
- Pillars relabeled to **Tech & AI**, **Business & Finance**, **Personal Growth** DONE.
- Tags + email preferences DONE.
- Quote-card generator in share dialog DONE.
- Pricing page: Razorpay placeholder + manual currency toggle DONE.
- Stripe auto-renew: enabled with real keys DONE.

## STATUS UPDATE (V2.1 — current focus)
- Razorpay backend skeleton added (razorpay-python installed) IN PROGRESS.
- **Blocking issue:** Razorpay Plan/Subscription creation returning `Unauthorized` / `ServerError` using test keys (`rzp_test_TMSwcg1LODuAH4` / `ZLBU0lyf5l96SuODeAxE09H5`).
- Next: fix Razorpay auth/payload and complete INR checkout wiring.
- Upcoming: Traffic Sources Analytics (P1) and Private Community Lounge (P1).

> Engineering note: `/app/backend/server.py` is large (>1000 LOC). Apply edits sequentially to avoid merge/conflict corruption.