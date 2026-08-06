# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a V1 subscription blog + newsletter platform (“The Trading Narrative”) with editorial UX, server-side paywall previews, mock subscription checkout (Stripe-ready), and an admin CMS.
- Support four pillars (Tech & Business, Finance, Lifestyle, Travel), SEO/meta, social sharing, and lightweight analytics.
- Ensure core workflows work end-to-end: read free vs premium, upgrade/downgrade, newsletter signup/issue send (mocked), admin publishing.

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) (paywall + subscription state + preview API)
**User stories**
1. As a reader, I can open a premium article and only receive a short preview when not subscribed.
2. As a reader, I can “upgrade” via a mock checkout and immediately unlock full premium content.
3. As a premium user, I always receive full content from the API (not just unblur UI).
4. As a user, I can cancel and immediately revert to preview-only.
5. As an admin, I can mark a post as free or premium and see gating change instantly.

**Steps**
- Websearch: best practices for server-side paywalls + Stripe subscription modeling (customer/subscription status, entitlement checks).
- Backend-only POC in FastAPI:
  - Mongo models: User (roles, premium_status), Post (tier, preview_blocks/full_blocks).
  - Endpoints: `GET /api/posts/{slug}` returns preview vs full based on entitlement.
  - Mock subscription endpoints: `POST /api/billing/mock/checkout` (activate premium), `POST /api/billing/mock/cancel` (deactivate), record mock invoices.
- Minimal React POC page(s): Login + Post view verifying that page source never includes full premium content when not entitled.
- POC test checklist: unauth, free user, premium user; verify API responses and DB state transitions.
- Fix until POC passes completely.

### Phase 2 — V1 App Development (bulk build; no extra integrations beyond mocks)
**User stories**
1. As a visitor, I can browse the homepage, filter by category, and quickly find recent posts.
2. As a reader, I can read an article with clean typography, read-time, author bio, and related posts.
3. As a free user, I can see a clear paywall CTA and pricing page with monthly/annual toggle.
4. As a subscriber, I can access an account page showing premium badge + mock billing history.
5. As an admin, I can create/edit/schedule/publish posts and set free/premium tier.

**Design first (design_agent)**
- Editorial layout, one accent color, dark mode toggle, Tailwind + shadcn/ui components, responsive templates.

**Backend (FastAPI /api, Mongo)**
- Auth:
  - Email+password (bcrypt + JWT).
  - Magic link (dev-mode): create token + return link in response + backend logs; UI displays “email mocked”.
- Content:
  - Posts CRUD, publish/schedule, categories, featured flag.
  - Server-side paywall logic: preview paragraphs only for non-premium on premium posts.
  - Archive search/filter endpoints.
- Subscriptions (mock Stripe-ready architecture):
  - Billing entities: Subscription, Invoice.
  - Routes under `/api/billing/*` with `MOCK_MODE=true` by default; env placeholders for Stripe (`STRIPE_SECRET_KEY`, `STRIPE_PRICE_MONTHLY`, etc.).
  - “Portal” endpoints: list invoices, cancel subscription.
- Newsletter (placeholder provider adapter):
  - Subscriber capture endpoints; welcome email mocked (logged + persisted).
  - Admin: create “issue from post”, send mocked (store recipients + log).
- SEO/ops:
  - `GET /sitemap.xml`, `GET /robots.txt`.
  - Analytics events collector (pageview, subscribe CTA click, checkout start/complete) stored in Mongo + admin stats.
- Seed data:
  - Admin user + 12 sample posts (3/category), mixed free/premium, 1 featured.

**Frontend (React 19)**
- Pages:
  - Home (hero, featured, filterable grid, newsletter signup).
  - Article (paywall preview, CTA, share bar, related).
  - Category x4, Archive (search + filters), Pricing, About.
  - Auth (login/register + magic link), Account/Billing.
  - Admin CMS (posts list, editor, schedule/publish, tier/category toggles, newsletter issue sender, analytics dashboard).
- Social sharing:
  - LinkedIn + X share URLs, Copy Link w/toast, Web Share API on mobile.
  - IG image card generator (canvas) for 1080x1080 + 1080x1920 with logo/title/cover; download PNG.
- SEO meta:
  - react-helmet-async for title/description/OG/Twitter per route/post.
- Add `data-testid` for key flows.

**End Phase 2**
- Run testing_agent_v3 for 1 full E2E pass; fix blocking issues.

### Phase 3 — Hardening + Feature Completion
**User stories**
1. As a user, I can reset my password (basic flow) if I forget it.
2. As an admin, I can preview scheduled posts and confirm publish timing.
3. As a writer, I can see validation errors clearly when saving drafts.
4. As a subscriber, I can reliably see my entitlement reflected across devices after login.
5. As an admin, I can view analytics trends (last 7/30 days) and top posts.

**Steps**
- Improve validation, empty/error states, loading skeletons.
- Tighten security basics: token expiry, rate-limit magic link generation, sanitize HTML/markdown.
- Ensure paywall cannot leak full content via list endpoints (only summaries in grids).
- Expand tests: auth variants, admin role checks, newsletter send logs, sitemap correctness.
- Run testing_agent_v3 again; fix all regressions.

### Phase 4 — Stripe & Email Provider Swap (when keys provided)
**User stories**
1. As a user, I can pay with real Stripe checkout and return to unlocked premium.
2. As a user, I can manage/cancel in Stripe customer portal.
3. As an admin, I can see real subscription status reflected instantly.
4. As a subscriber, I receive real welcome/issue emails.
5. As an admin, I can switch provider via config without code changes.

**Steps**
- Replace mock billing with Stripe subscriptions + webhooks; keep same entitlement interface.
- Replace newsletter adapter with Mailchimp/ConvertKit; keep same app-level API.
- Final E2E test + webhook replay tests.

## 3) Next Actions
- Confirm accent color (hex) + author name/bio/photo (or placeholders acceptable).
- Start Phase 1: websearch + build isolated paywall/subscription POC endpoints + minimal React verifier.
- After POC passes: proceed to Phase 2 bulk build (design_agent → backend+frontend) and seed content.

## 4) Success Criteria
- Premium posts never return full content to non-premium users from the API (verified via network + page source).
- Mock checkout reliably toggles premium status and creates mock invoices; cancel reverts access.
- Admin can create/edit/schedule/publish posts and set tier/category; public pages reflect changes.
- Newsletter signup stored; welcome + issue sends recorded/logged; admin can view send history.
- Social share bar works; IG card generator exports valid PNG sizes; OG/Twitter meta present.
- Sitemap/robots served; analytics events stored and visible in admin.
- testing_agent_v3 passes core E2E flows with no critical bugs.

---
## STATUS UPDATE (post Phase 2)
- Phase 1 (POC): DONE — test_core.py 32/32 passed (server-side paywall, subscription transitions, magic link, newsletter, admin gating).
- Phase 2 (V1 app): DONE — full frontend + backend built; testing_agent iteration_1: backend 74/74, frontend 59/60; the 1 minor issue (duplicate share-bar testids on hidden mobile bar) FIXED and verified.
- Next: Phase 3 hardening (password reset, analytics trends) and Phase 4 (real Stripe + email provider when user supplies keys).

## STATUS UPDATE (post V1.1 feature batch)
- Real Stripe checkout (test mode, emergentintegrations, sk_test_emergent) LIVE — full E2E payment verified with 4242 card: paid → premium activated → invoice recorded. Claimable sandbox unavailable (account country IN unsupported), so one-time timed-access model used; user's own key swappable via STRIPE_API_KEY.
- Password reset (mocked email, dev-mode link) DONE. Premium comments DONE. Reading progress DONE.
- testing_agent iteration_2: backend 89/89, frontend 45/45 — all passing.
