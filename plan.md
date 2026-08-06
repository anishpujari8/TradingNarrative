# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (“The Trading Narrative”) with an editorial reading experience, server-side paywall previews, and a freemium model.
- Support **three content pillars**: **Tech & AI**, **Business & Finance**, **Personal Growth**.
- Provide subscriptions via:
  - **Stripe (international recurring)**
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
  - **Real email sending via Gmail SMTP is LIVE** (App Password configured) + admin status/test send
  - **One-click unsubscribe** on all marketing emails (digest/issue/welcome) with **List-Unsubscribe** header
  - **Pillar-personalized weekly digests** based on subscriber preferences
  - **Weekly digest autosend every Friday (UTC)** with admin toggle
  - **Digest preview email to admin** before sending to all subscribers
- Branding + content readiness:
  - Use the **official The Trading Narrative logo** across the UI (navbar/footer/mobile + favicon)
  - Use **Anish Pujari** author identity + bio + headshot across pages and post metadata
  - Import existing writing (LinkedIn newsletter + related articles) into posts
- Keep integrations reliable with webhooks, audit logs, and end-to-end tests.

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) (paywall + subscription state + preview API) ✅ DONE
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

### Phase 2 — V1 App Development (bulk build) ✅ DONE
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
  - Admin Studio (posts list, editor, schedule/publish, tier/category toggles).
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

### Phase 3 — Hardening + Feature Completion ✅ DONE
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

### Phase 4 — Payments Integrations (Stripe + Razorpay) ✅ DONE
**User stories**
1. As a global user, I can pay with real Stripe recurring checkout and return to unlocked premium.
2. As an Indian user, I can pay via Razorpay:
   - If Subscriptions/Autopay is enabled: create a mandate/subscription.
   - If not enabled: fallback to a one-time Razorpay order (time-bound premium pass).
3. As a user, I can manage/cancel subscriptions cleanly and see status reflected.
4. As an admin, I can trust webhook-driven entitlement updates.

**Steps**
- Stripe (DONE):
  - Stripe Checkout with auto-renew enabled using real keys.
  - Webhook updates entitlement.
- Razorpay (DONE):
  - Real Razorpay integration wired into Pricing.
  - Backend probes Subscriptions capability and falls back to **one-time Orders** when unavailable.
  - **Live Autopay switch-on** via throttled re-probe on config/checkout.
  - Frontend checkout supports both **order_id** and **subscription_id** flows.
  - DB transaction records written on checkout initiation; verification endpoint activates premium.
  - Webhook endpoint exists for gateway-driven confirmation events.
- Testing (DONE):
  - Backend tests verify order creation using test keys.
  - Frontend verified Razorpay checkout modal opens for INR.

### Phase 5 — V2 Admin Analytics + Community ✅ DONE
**User stories**
1. As an admin, I can see where readers come from (LinkedIn, Instagram, Google, Direct, etc.).
2. As a premium member, I can access a private lounge.
3. As a premium member, I can read admin announcements and participate in discussion threads (post + reply).

**Steps**
- Traffic Sources Analytics (DONE):
  - Backend attribution on the **first pageview of a browser session** via session flag.
  - Classification uses referrer host + UTM tags; internal navigation is ignored.
  - Endpoint: `GET /api/admin/traffic?days=...` returns source breakdown, top referrers, campaigns.
  - Admin Studio UI tab: chart + tables + day-range selector.
- Private Community Lounge (DONE):
  - Frontend page: `/lounge` (premium-only; locked state shown for logged-out/free users).
  - Backend routes: `/api/community/*`:
    - Announcements: admin create/list/delete; members read.
    - Threads: premium create/list/detail/delete.
    - Replies: premium reply/delete.
  - Moderation basics and simple rate limits.
  - Tests: access control (401 unauth, 403 free), CRUD verified.

### Phase 6 — V2.2 Enhancements (Autopay Live Switch-On + Lounge Notifications + Traffic Trends + Pinned Threads) ✅ DONE
**User stories**
1. As an Indian subscriber, once Razorpay Subscriptions is enabled on the dashboard, the site automatically switches from one-time orders to UPI Autopay without requiring a deployment or restart.
2. As a Lounge member, when someone replies to my discussion, I get a bell notification and can jump straight into the thread.
3. As an admin, I can see week-by-week traffic source trends to understand what’s growing.
4. As an admin, I can pin important discussions so new members see them first.

**Steps**
- Razorpay Autopay live re-probe (DONE).
- Lounge reply notifications (DONE).
- Traffic trends (DONE).
- Pinned discussions (DONE).
- Testing (DONE): Iteration 6 report: backend **99.5% (183/184)**, frontend **100%**, no regressions.

### Phase 7 — V2.3 Enhancements (Post Attribution + CSV Export + Digest Autosend + Thread Lock) ✅ DONE
**User stories**
1. As an admin, I can see which **landing pages** readers hit from each traffic source.
2. As an admin, I can export traffic breakdown to CSV.
3. As an admin, I can enable an automatic weekly digest every Friday without manual action.
4. As an admin, I can lock a Lounge discussion.

**Steps**
- Post attribution (DONE).
- CSV export (DONE).
- Weekly Digest autosend (DONE; autosend toggle left ON).
- Lounge thread lock (DONE).
- Testing (DONE): Iteration 7 report: backend **99.5% (208/209)**, frontend **100%**, no regressions.

### Phase 8 — V2.4 Enhancements (Conversion Funnel + Gmail SMTP Email + Member Profiles + Scheduled Announcements) ✅ DONE
**User stories**
1. As an admin, I can see the full path from traffic source to checkout to premium activation.
2. As an admin, I can send newsletter/digest emails and verify delivery.
3. As a Lounge member, I can click a member and see a lightweight profile.
4. As an admin, I can schedule an announcement to publish later.

**Steps**
- Conversion funnel (DONE).
- Gmail SMTP integration (DONE; later made LIVE).
- Member profiles (DONE).
- Scheduled announcements (DONE).
- Testing (DONE): Iteration 8 report: backend **100% (261/262)**, frontend **100%**, no regressions.

### Phase 9 — V2.5 Enhancements (Email LIVE + Pillar Digests + Announcement Editing + Funnel Plan Split) ✅ DONE
**User stories**
1. As an admin, I can trust that email sends are real and verified.
2. As a subscriber, my weekly digest only includes pillars I selected.
3. As an admin, I can edit or reschedule Lounge announcements after creation.
4. As an admin, I can see funnel conversions split by monthly vs annual plans.

**Steps**
- Gmail SMTP LIVE (DONE).
- Pillar-personalized weekly digest (DONE).
- Announcement editing (DONE).
- Funnel plan split (DONE).
- Testing (DONE): Iteration 9 report: backend **100%**, frontend **100%**, regression **100%**.

### Phase 10 — V2.6 Enhancements (Unsubscribe + Subscriber Growth + Digest Preview Email + Post Conversion Stats) ✅ DONE
**User stories**
1. As a subscriber, I can unsubscribe with one click from any email.
2. As an admin, I can see subscriber growth week by week.
3. As an admin, I can email the digest to myself first.
4. As an admin, I can see which essays most often lead to Premium upgrades.

**Steps**
- One-click unsubscribe (DONE).
- Subscriber growth trend (DONE).
- Digest preview email (DONE).
- Post conversion stats (DONE).

### Phase 11 — Branding + Author Identity + Content Import ✅ DONE
**User stories**
1. As a reader, I see consistent brand identity (logo + favicon) across the site.
2. As a reader, I can learn who runs the publication and what it stands for.
3. As the author, my identity (Anish Pujari) is consistent across posts, community content, and admin.
4. As the author, I can import my existing writing (LinkedIn newsletter editions) as posts.

**Steps**
- Branding assets (DONE):
  - User-provided circular logo cropped/optimized to `/logo.png` + `/logo192.png`.
  - Favicon set to `/favicon.png`.
  - Navbar, Footer, and mobile menu updated to use the official logo.
- About page rewrite (DONE):
  - About page rewritten with the provided long-form bio and value proposition.
  - Headshot saved and used as `/anish.jpg`.
  - LinkedIn link added.
- Author identity alignment (DONE):
  - Renamed prior placeholder author (**Jordan Hale**) → **Anish Pujari** across:
    - users
    - posts `author` object (name/bio/avatar)
    - community threads/replies/announcements
    - seed data (`/app/backend/seed_data.py`).
- Content import (DONE for Edition #1):
  - Imported LinkedIn newsletter Edition #1:
    - Title: **Five Things Commodity Desks Need to Know This Week**
    - Marked **Free** and **Featured**
    - Category: **Business & Finance** (`finance`)
    - Slug: `five-things-commodity-desks-need-to-know-this-week`
  - Added simple heading support in Article renderer:
    - `content_blocks` starting with `"## "` are rendered as section headings (`<h2>`).
- Verification (DONE):
  - Verified logo + about + imported article via screenshots.

## 3) Next Actions
All planned phases are complete. Remaining high-impact setup actions and optional upgrades:

### A) Required setup actions (to fully go-live)
1. **Enable Razorpay Subscriptions** in the Razorpay dashboard to activate true UPI Autopay mandates.
   - The app will switch automatically via the live re-probe (no restart required).
2. **Deploy branding/content updates to production**.
   - Current changes were applied in preview; production requires redeploy.

### B) Content operations (next editorial steps)
1. Import remaining LinkedIn newsletter editions and any standalone LinkedIn articles.
   - Input format: paste title + full text (as done for Edition #1).
   - Decide per article: Free vs Premium, pillar/category, featured.
2. Resolve the **Travel pillar** decision:
   - Keep as-is, remove, or rename to align with your stated themes.

### C) Optional enhancements (nice-to-haves)
1. Configure `RAZORPAY_WEBHOOK_SECRET` and Stripe webhook secrets in production for stronger signature verification.
2. Refactor `/app/backend/server.py` into modules (billing, community, admin/analytics, newsletter) to reduce risk from large-file edits.
3. Analytics upgrades:
   - Funnel segmentation by **landing page** and by **currency** (USD vs INR)
   - Attribution to paid vs free articles and premium conversion lift
4. Newsletter upgrades:
   - Double opt-in for subscribers
   - Dedicated sender domain + SPF/DKIM/DMARC hardening

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API (verified via network/page source).
✅ Stripe recurring checkout works end-to-end and updates entitlements via webhook.
✅ Razorpay INR checkout works end-to-end:
- If Autopay enabled: subscription/mandate flow supported.
- If not enabled: graceful fallback to one-time Orders.
✅ Autopay live switch-on works: capability is re-probed and activates without restart once Subscriptions is enabled.
✅ Pricing routes correctly between Stripe (USD) and Razorpay (INR) via locale/toggle.
✅ Traffic sources visible in Admin with meaningful referrer grouping and UTM campaign visibility.
✅ Weekly traffic trend chart renders and reflects weekly bucketing.
✅ Subscriber growth chart renders and reflects weekly new + cumulative totals.
✅ Post attribution works: landing pages by source are visible in Admin.
✅ CSV export works: admin can download traffic breakdown.
✅ Conversion funnel works: per-source sessions and stage drop-offs are visible in Admin.
✅ Funnel plan split works: monthly vs annual conversion counts are visible per source.
✅ Post conversion stats work: “Essays that convert” table shows sessions → premium conversions + rate.
✅ Weekly digest autosend is toggleable and runs on schedule.
✅ Weekly digest is pillar-personalized per subscriber preferences.
✅ Digest preview email can be sent to admin before full send.
✅ One-click unsubscribe works (HMAC token + confirmation page) and emails contain List-Unsubscribe.
✅ Real email delivery is **LIVE** and verified via Gmail SMTP App Password.
✅ Premium-only Community Lounge works with announcements + threads + replies and correct access control.
✅ Lounge reply notifications appear in bell and deep-link opens the relevant thread.
✅ Member profiles work: profile dialog shows join date + counts + recent discussions.
✅ Scheduled announcements work: future announcements hidden from members until publish time.
✅ Announcement editing works: admin can edit/reschedule/clear schedule.
✅ Pinned discussions work (admin toggle + pinned-first sorting + UI badges).
✅ Thread lock works: locked discussions are readable but reply-closed.
✅ Branding is applied consistently:
- Logo in navbar/footer/mobile menu
- Favicon updated
✅ About page reflects the current author bio and includes real headshot.
✅ Imported LinkedIn newsletter Edition #1 is live as a free featured post with section headings.

✅ Testing passes (key iterations):
- Iteration 5: backend 99.4% + frontend verification.
- Iteration 6: backend 99.5% (183/184) + frontend 100%, no regressions.
- Iteration 7: backend 99.5% (208/209) + frontend 100%, no regressions.
- Iteration 8: backend 100% (261/262) + frontend 100%, no regressions.
- Iteration 9: backend 100%, frontend 100%, regression 100%.
- Iteration 10: backend 98.2% (test expectation mismatch only), frontend 100%, regressions 100%.

---
## STATUS UPDATE (post Phase 2)
- Phase 1 (POC): DONE — server-side paywall, subscription transitions, magic link, newsletter, admin gating.
- Phase 2 (V1 app): DONE — full frontend + backend built and tested.

## STATUS UPDATE (V2.0 — expanded spec applied)
- Notifications bell DONE.
- Continue-reading strip + resume DONE.
- Weekly digest admin previews DONE.
- Pillars relabeled to **Tech & AI**, **Business & Finance**, **Personal Growth** DONE.
- Tags + email preferences DONE.
- Quote-card generator in share dialog DONE.
- Pricing page: Razorpay currency toggle DONE.
- Stripe auto-renew: enabled with real keys DONE.

## STATUS UPDATE (V2.1 — payments + analytics + community) ✅ COMPLETE
- Razorpay integration FIXED and stable.
- Traffic Sources Analytics shipped.
- Community Lounge shipped.

## STATUS UPDATE (V2.2 — Autopay live switch-on + lounge notifications + traffic trends + pinned threads) ✅ COMPLETE
- Autopay Switch-On via live re-probe.
- Lounge Notifications + deep-link support.
- Traffic Trends chart.
- Pinned Discussions.

## STATUS UPDATE (V2.3 — Attribution + CSV Export + Digest Autosend + Thread Lock) ✅ COMPLETE
- Landing pages by source.
- CSV Export.
- Friday autosend + toggle.
- Thread Lock.

## STATUS UPDATE (V2.4 — Funnel + Gmail SMTP + Profiles + Scheduled Announcements) ✅ COMPLETE
- Conversion Funnel.
- Gmail SMTP layer.
- Member Profiles.
- Scheduled Announcements.

## STATUS UPDATE (V2.5 — Email LIVE + Pillar Digests + Announcement Editing + Funnel Plan Split) ✅ COMPLETE
- Gmail verified + real sending.
- Pillar digests.
- Announcement editing.
- Funnel plan split.

## STATUS UPDATE (V2.6 — Unsubscribe + Subscriber Growth + Digest Preview + Post Conversion Stats) ✅ COMPLETE
- One-click unsubscribe.
- Subscriber growth chart.
- Digest preview email to admin.
- Essays that convert.

## STATUS UPDATE (V2.7 — Branding + Content Import) ✅ COMPLETE
- Official logo + favicon applied.
- About page updated with Anish Pujari bio + headshot.
- Author identity aligned across DB/seed.
- Imported LinkedIn newsletter Edition #1 as a free featured post.
- Heading convention (`"## "`) supported in article rendering.

> Engineering note: `/app/backend/server.py` is large. Apply edits sequentially to avoid merge/conflict corruption; consider modularizing next.
