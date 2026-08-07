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
  - Weekly digest preview + send ✅
- Deliver admin + growth tooling ✅:
  - Traffic sources attribution + trends
  - Subscriber growth
  - Post attribution
  - Conversion funnels + plan split
  - Post conversion stats (“Essays that convert”)
  - CSV export
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
- Improve editorial discovery ✅:
  - **Related essays by tags** (shared tags prioritized over category-only)
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

### Phase 17 — Reader Highlights + Related By Tags ✅ COMPLETED
#### A) Reader Highlights ✅
- Backend routes:
  - `POST /api/highlights` (substring validation + paywall-aware)
  - `GET /api/highlights` (optional `?slug=`)
  - `DELETE /api/highlights/{id}`
- Frontend:
  - Floating “Highlight” pill on text selection
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

---

## 3) Next Actions

### A) Immediate
1. **More Editions**: Import LinkedIn newsletter editions as numbered briefings
   - ⛔ Blocked until you paste the next edition text (we’ll publish as Edition #2).
2. **Delivery & Systems**: Import a real delivery-focused essay
   - ⛔ Blocked until you paste the article text.
3. **PayPal**: Proceed after you answer:
   - subscriptions vs one-time
   - sandbox/live credentials
   - pricing-page placement

### B) Production note (workflow)
- The app is deployed to production at a custom domain.
- Changes are implemented and tested in preview; you will need to redeploy for production to pick them up.

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe recurring checkout works and updates entitlements.
✅ Razorpay INR checkout works (autopay if enabled, fallback order if not).
✅ Email sending is LIVE (Gmail SMTP) with unsubscribe + digest systems.
✅ Community lounge features work.
✅ Briefings tooling and `/briefings` archive works.
✅ Freight article imported and renders correctly.
✅ Backend modularization complete with regression tests.
✅ Related essays scored by tags.
✅ Highlights system complete:
- Highlight create/list/delete
- Paywall-aware validation
- Inline mark rendering
- Highlights page
- Notes + quote-card sharing

⛔ PayPal integration: blocked until credentials + mode decisions.
⛔ Content imports: blocked until you paste Edition #2 text and the Delivery essay.
