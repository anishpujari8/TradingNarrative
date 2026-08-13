# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform ("The Trading Narrative") with an editorial reading experience, a freemium → premium conversion model, and a **premium community destination (Lounge)**.
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
    - **Plan pricing cache hardening** ✅ *(Razorpay plan cache key includes amount so price changes mint new Razorpay plans)*
  - **PayPal** ⛔ *(planned; blocked pending user decisions + credentials)*
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
- **Early bird premium offer (homepage surfaced)** ✅ *(Phase 46 add-on)*
  - Early bird Premium pricing is marketed directly on the homepage via a banner linking to `/pricing`

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

#### Audio narration access policy (UPDATED + IMPLEMENTED)
- Anonymous (logged-out): narration requires sign-in (**401**) ✅
- Premium members: **full narration** everywhere ✅
- Free signed-in users:
  - **FREE full audio** for:
    - **Newsletter editions**: posts with an `edition` field (Edition #1, #2, etc.)
    - **Shipping industry** essays: posts tagged with `Shipping` (case-insensitive match on tags)
  - **Business & Finance** (non-exempt essays):
    - default is **20-second preview clip** (`X-Audio-Scope: clip`) ✅
    - **one-time per-essay unlock** for **₹45 / $0.50** ✅
  - **Premium pillars (Tech & AI, Personal Growth, Delivery & Systems)**:
    - narration is **Premium-only**
    - **NO audio player at all** for non-premium readers ✅

**Pricing note (important):** The originally requested ₹39 / $0.41 was not possible via Stripe due to a hard minimum of **$0.50 USD-equivalent** per charge. Final pricing was user-approved: **₹45 (Razorpay) / $0.50 (Stripe)**.

- Warmup generates **full scope only** ✅

#### ElevenLabs credit protection ✅ *(Phase 41)*
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
- **Growth Suite** ✅ *(Phase 46, PREVIEW)*
  - Audio Sales Dashboard ✅
  - Manual Search Rank Tracker ✅
  - Early Bird Premium offer (first 50) ✅
  - **Early Bird homepage banner** ✅ *(Phase 46 add-on)*

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

### Access model (METERED + PAYWALL, SEO-friendly)
- **Archive index is fully public** ✅
  - /archive shows every essay (title, date, tags, ~40–60 word summary)
  - Includes Free/Premium filter tabs + badges ✅ *(already exists)*
- **Metered anonymous access** ✅ *(Phase 42)*
  - Anonymous visitors may read **3 full free-tier essays**
  - Tracking:
    - first-party cookie: `fv_slugs` (90 days, stores read slugs; derives remaining count)
    - server fallback: hashed key `sha256(ip + ua)` stored in `meter_reads` so it survives cookie/local resets
    - Union cookie + server; re-reads don’t consume quota
  - After quota is exhausted:
    - free-tier essays render preview-only with `lock_reason = 'meter'`
    - UI: meter paywall CTA block with price + sign-in link
- **Hard-locked content (never metered)** ✅ *(Phase 42)*
  - tag `lounge`
  - all `tier=premium`
  - latest-3 premium editions (by edition number)
  - Lock reason returned as `premium` (implementation keeps one stable reason; structured data still signals paywall)
- **Preview shape for locked essays** ✅ *(Phase 42)*
  - Headline + excerpt + hero + publish date + tags
  - First ~250 words OR first 2 paragraph blocks (whichever is shorter)
  - Gradient fade into paywall CTA
  - Preview text is outside `.paywalled-content`
  - Locked body wrapped in `.paywalled-content`
- **Meter UI** ✅ *(Phase 42)*
  - Persistent non-blocking banner: “X of 3 free essays remaining” + subscribe link
  - Never blocks reading
- **Signed-in users** ✅
  - Signed-in free users: full access to free-tier posts + 3-block premium previews + early supporter perk
  - Premium users bypass all gating

### SEO infrastructure (within React + FastAPI)
- **No cloaking** ✅ *(Phase 42)*
  - No user-agent sniffing; Googlebot sees same HTML as anonymous humans.
- **Structured data** ✅ *(Phase 42 + Phase 48 additions)*
  - Essay pages emit JSON-LD `NewsArticle` on-page (client via Helmet) and on `/api/share/{slug}` (server HTML)
  - `isAccessibleForFree: true` for open essays
  - `isAccessibleForFree: false` + `hasPart.cssSelector = '.paywalled-content'` for locked
  - **Added (Phase 48):**
    - Essays now emit `@graph` including `BreadcrumbList`
    - Topic hubs emit `CollectionPage`
    - Pricing emits `Product` with INR/USD `Offer` items
    - About emits `AboutPage` + `Person`
- **Sitemap** ✅ *(Phase 42, verified again in Phase 48; Phase 50 hardened)*
  - `/api/sitemap.xml` regenerates from MongoDB on each request (new essays/editions appear immediately)
  - Includes: homepage, archive, pricing, about, briefings, topic hubs, category pages, all published essays with `<lastmod>`
  - **GSC compatibility (Phase 50):** `/sitemap.xml` is now a valid XML sitemap **index** pointing to `/api/sitemap.xml` to avoid SPA/ingress HTML routing issues.
- **Robots** ✅ *(Phase 42 + Phase 48 additions)*
  - `frontend/public/robots.txt` disallows `/api/` while explicitly allowing:
    - `/api/sitemap.xml`, `/api/feed.xml`, `/api/share/`
  - Production sitemap URL referenced.
  - **AI crawler policy sections added (Phase 48)** and a note to consult `/llms.txt`.
  - Note: Preview domain may inject a platform-level robots.txt; localhost/production serve the app’s file.
- **RSS feed** ✅ *(Phase 42)*
  - `/api/feed.xml`: full text for open/free essays; preview + link for locked
  - RSS discovery link injected in `public/index.html`
- **Topic hubs** ✅ *(Phase 42)*
  - `/topics/{pillar}` pages with 200–400 words of original intro copy
  - Chronological essay grids + archive links
  - Essay category badge links to hub
- **Keyword targeting** ✅ *(Phase 45, PREVIEW)*
  - Keyword-rich defaults for title/description/keywords
  - WebSite + Organization JSON-LD on homepage
  - Briefings + Archive tuned for “weekly briefing / newsletter / freight / trading”
  - Topic hubs already keyword-strong
  - Meta duplication fixed (static fallback tags removed on mount) so rendered pages have exactly one `description`, `keywords`, and `og:title`
- **Site title + dynamic essay meta descriptions** ✅ *(Phase 47, PREVIEW)*
  - Site title set to **exact string**: `The Trading Narrative | Commodity Trading & Tech Insights`
  - Default keywords emphasize: commodity trading, energy markets, trading technology, ETRM, market risk
  - Essay pages generate a dynamic meta description derived from the actual article content
- **AI readiness** ✅ *(Phase 48)*
  - `/llms.txt` served with crawler-facing site overview
- **Social Preview Cards** ✅ *(Phase 50 + Phase 51)*
  - Every essay unfurls with a consistent, branded Open Graph image for LinkedIn/X.
  - Implemented via backend-rendered OG images served at `GET /api/og/{slug}.png`.
  - **Phase 51:** share cards are now **pillar-coloured** (pillar-specific accent palette) and have a richer v2 design.

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

### Security hardening
- **Cookie auth upgrade (httpOnly session cookies)** ✅ *(Phase 50)*
  - Moved sign-in JWT storage from localStorage to secure **httpOnly** cookies for XSS resistance.
  - Cookie: `ttn_session`, `Secure`, `SameSite=Lax`, 30-day expiry.
  - Migration: legacy Bearer tokens supported temporarily + `/api/auth/cookie-sync` exchanges them for cookie and frontend deletes localStorage token.
  - Logout: `/api/auth/logout` clears the cookie.
  - **CORS compatibility for credentialed cookies:**
    - Starlette CORS requires **not** using explicit origin lists when `allow_credentials` is enabled in this environment.
    - Deployment configuration uses `CORS_ORIGINS="*"` (platform requirement) and has been re-verified to work with cookie auth.

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

### Phase 39 — Engagement Boosters (Countdown + Milestones + Promo Counter) ✅ COMPLETED
**Verified by testing agent iteration_30**: backend 10/10 (100%), frontend 3/3 (100%).

### Phase 40 — Access Model + Premium Lounge Hub (Hybrid) ✅ COMPLETED
**Verified by testing agent iteration_31**: backend 30/30 (100%), frontend flows 100%.

### Phase 41 — Catalog Publish + Welcome Take + Streak Reminders ✅ COMPLETED
- All 12 demo essays published + categorized/tiered
- Welcome Market Narrative take seeded
- Evening streak reminders implemented + verified
- ElevenLabs warmup generation cap added

### Phase 42 — Metered Access + SEO Infrastructure + Hyphen Cleanup ✅ COMPLETED
**Verified by testing agent iteration_32**: backend 64/64 (100%), frontend 100%.

Delivered:
- Metered anonymous access (3 free full essays) using cookie `fv_slugs` (90 days) + `meter_reads` fallback keyed sha256(IP+UA);
  re-reads don’t consume quota.
- 4th free essay locks with `lock_reason='meter'` and returns a ~250-word/2-block preview.
- Premium essays + `lounge`-tagged posts + latest-3 premium editions are always preview-only for non-entitled.
- Persistent meter banner (“N of 3 free essays remaining”) + subscribe CTA.
- SEO: JSON-LD paywall schema, RSS `/api/feed.xml`, sitemap `/api/sitemap.xml`, robots.txt updated.
- Topic hubs with original intro copy.
- Hyphen cleanup.

### Phase 43 — Per-Essay Audio Micro-Paywall (₹45 / $0.50) ✅ COMPLETED
(As described in Objectives section above)

Includes:
- `GET /api/posts/{slug}/audio/access`
- Stripe + Razorpay one-time unlock flows
- Unlock persistence `users.purchased_audio_slugs`
- **My Audio Library** on Account page

Testing:
- `/app/test_reports/iteration_33.json` (micro-paywall)
- `/app/test_reports/iteration_34.json` (My Audio Library)

### Phase 44 — Premium Pillar Audio Exclusivity + Test Mode Decision ✅ COMPLETED (PREVIEW)
- Test mode strip cannot be removed without switching to LIVE keys
- Premium pillars audio is hidden for non-premium; non-premium requests get 403; unlock checkout blocked

### Phase 45 — Keyword SEO Targeting ✅ COMPLETED (PREVIEW)
**Goal:** Improve eligibility for head-term searches: Freight, Trading, Business and Finance, Narrative, Weekly briefing, Newsletter.

Delivered:
- `frontend/public/index.html`
  - Keyword-rich homepage title and description
  - Added `meta[name=keywords]`
  - Static fallback tags marked `data-rh="true"`
- `frontend/src/components/Seo.js`
  - Keyword-tuned defaults for title/description/keywords
  - Added `keywords` and `jsonLd` props
  - Removes static fallback tags (`meta[data-rh]`) on mount so rendered pages have exactly one description/keywords/og:title
- `frontend/src/pages/HomePage.js`
  - Added WebSite + Organization JSON-LD `@graph`
- `frontend/src/pages/BriefingsPage.js`
  - Keyword-optimized title/description/keywords for “weekly briefing newsletter” + “freight” + “commodity trading”
- `frontend/src/pages/ArchivePage.js`
  - Keyword-optimized title/description
- Topic hubs already optimized with long-form intro copy.
- `SEO.md`
  - Keyword → landing surface mapping
  - Meta-tag ownership convention notes for `react-helmet-async` v3

Verification:
- Headless Chromium verified single meta description + keywords + og:title on home/briefings/archive/topic pages.
- Essay pages still emit `NewsArticle` JSON-LD; `/api/share/{slug}` provides crawler HTML.

### Phase 46 — Growth Suite (Audio Sales + Manual Search Rank + Early Bird) ✅ COMPLETED (PREVIEW)

#### 46.1 Audio Sales Dashboard (Admin) ✅
Backend
- `GET /api/admin/audio-sales` (admin-only)
- Source: `payment_transactions` where `plan='audio_unlock'` and `payment_status='paid'`

Frontend
- Admin → **Growth** tab
- Stat cards + best sellers table + recent purchases table

#### 46.2 Search Rank Tracker (Admin, Manual Entry) ✅
User choice: **Skip Google Search Console connection** (manual entry).

Backend
- `seo_keyword_stats` collection
- Endpoints (admin-only):
  - `GET /api/admin/seo/keywords`
  - `POST /api/admin/seo/keywords`
  - `DELETE /api/admin/seo/keywords/{entry_id}`
- Keyword normalization: lowercase
- Validation: `noted_on` must be `YYYY-MM-DD`

Frontend
- Admin → Growth → Search rank tracker
- Keyword chips + entry form + table with deltas

#### 46.3 Early Bird Offer (first 50 premium subscribers) ✅
User choices:
- Eligibility: **first 50 premium subscribers**
- Discounts:
  - Monthly: **₹49 / $0.52** for first month
  - Annual: **₹499 / $5.25** for first year

Backend
- `GET /api/billing/early-bird` public state (spots/claimed/remaining)
- Stripe AUTO_RENEW: applies `duration='once'` coupon so renewals bill full price
- Razorpay: early bird always one-time order at discounted price (never Autopay)
- Founding plans never discounted

Frontend
- PricingPage shows:
  - Early bird badge (`remaining of 50`)
  - Discounted price + strikethrough regular
  - Note: “first month/year, then regular price”

#### 46.4 Early Bird Homepage Banner ✅ *(Phase 46 add-on)*
Context: show the early-bird premium deal on the homepage so visitors see it before the pricing page.

Delivered:
- `HomePage.js` fetches `GET /api/billing/early-bird` alongside `/early-supporters`.
- New banner rendered **above** the existing early-supporter strip.

### Phase 47 — Site Title + Dynamic Essay Meta Descriptions ✅ COMPLETED (PREVIEW)
User request:
- Exact site title: **"The Trading Narrative | Commodity Trading & Tech Insights"**
- Keywords: **commodity trading, energy markets, trading technology, ETRM, market risk**
- Each essay page must generate a **dynamic meta description** based on article content

Delivered:
- `frontend/public/index.html`: exact title + updated keyword-rich description/keywords/og tags.
- `frontend/src/components/Seo.js`:
  - Defaults updated around the five requested terms.
  - `metaDescription(post)` helper derives per-essay descriptions.
- `frontend/src/pages/ArticlePage.js`: uses `metaDescription(post)` for the essay meta description and tag-derived keywords.
- `backend/utils.py`: `meta_description(post)` mirror helper.
- `backend/routers/posts.py`: `/api/share/{slug}` uses `meta_description(post)` for crawler HTML + JSON-LD.
- `frontend/src/pages/HomePage.js`: WebSite/Organization JSON-LD updated for energy markets + market risk.
- `SEO.md`: Phase 47 section.

### Phase 48 — Deployment Fix + AI Assistant Readiness ✅ COMPLETED (PREVIEW)

#### 48.1 Production deploy failure fixed (health probes) ✅
- Root cause from logs: Kubernetes probes hit `GET /health` (no `/api` prefix) and got **404**, failing rollout.
- Fix: added `GET /health` and `GET /` to `backend/server.py` returning 200 quickly **without DB access**.
- Verified: `curl http://localhost:8001/health` returns 200; `/api/*` unaffected.

#### 48.2 Deployment agent blocker fixed ✅
- Blocker: malformed env value in `/app/backend/.env` for `EMERGENT_LLM_KEY`.
- Fix: value is now quoted. Re-scan: PASS.

#### 48.3 Dynamic sitemap request verified ✅
- User request: sitemap includes homepage, archive, and all essays, updates when new edition published.
- Verified: already satisfied by Phase 42 `/api/sitemap.xml` implementation.
- No code changes needed.

#### 48.4 AI assistant readiness ✅
- `frontend/public/llms.txt`: llmstxt.org-style site overview with production URLs.
- `frontend/public/robots.txt`: now includes explicit AI crawler user-agents plus a pointer to `/llms.txt`.
  - NOTE: preview domain may inject platform robots.txt; localhost/production serve the app’s file.
- Structured data additions (verified rendered via headless Chromium):
  - Home: WebSite + Organization
  - Essays: NewsArticle + BreadcrumbList (`@graph`), paywall signalling preserved
  - Topic hubs: CollectionPage
  - Pricing: Product with INR/USD Offers
  - About: AboutPage + Person
- Incident: `TopicPage.js` was corrupted by duplicated trailing JSX which broke webpack builds (esbuild still passed).
  - Fixed by removing orphaned lines and re-applying the `jsonLd` edit.
- `SEO.md`: Phase 48 AI readiness section added.

### Phase 49 — Code Review Fixes ✅ COMPLETED (PREVIEW)
Context: applied code-review recommendations that are safe/low-regression, focusing on deployment/security and removing test artifacts.

**APPLIED**
1. **Hardcoded secrets in test files**
   - Deleted all 11 obsolete test-agent artifact scripts from `/app/backend`.
2. **“Possibly undefined variables (17 instances)”**
   - Verified production backend via pyflakes; issues were in deleted test files.
   - Cleaned a few unused imports.
3. **Insecure random usage**
   - Replaced `random` with `secrets` for invoice-ish numbers.
4. **Empty catch blocks (frontend)**
   - Added lightweight debug logging.
5. **Array index as key (frontend)**
   - Fixed GrowthPanel table row keys.
6. **Expensive JSX computation**
   - Memoized AdminPage newsletter post picker.

**DEFERRED (WITH RATIONALE)**
- Missing hook dependencies (risk of loops)
- Massive component splitting (AdminPage/CommunityPage/ArticlePage/PricingPage)

### Phase 50 — Cookie Auth Upgrade + Social Preview Cards + Sitemap GSC Fix ✅ COMPLETED (PREVIEW)
Context: Session priorities:
- Strengthen auth against XSS by moving session tokens to secure httpOnly cookies.
- Improve social sharing by generating branded OG images per essay (LinkedIn/X).
- Resolve Google Search Console sitemap error: `/sitemap.xml` being detected as HTML.

#### 50.A Google Sitemap Fix (GSC “Sitemap is HTML”) ✅ DONE
Root cause:
- Search Console was submitted `/sitemap.xml`, but the platform routes that path to the React app (HTML), while the real sitemap is served by the backend at `/api/sitemap.xml`.

Delivered:
- Static `frontend/public/sitemap.xml` is now a valid XML sitemap **index** pointing to:
  - `https://thetradingnarrative.com/api/sitemap.xml`
- Verified: `/sitemap.xml` returns `application/xml` (not React HTML).

User action after Production redeploy:
- Resubmit `https://thetradingnarrative.com/sitemap.xml` in Google Search Console.

#### 50.B Social Preview Cards (Branded OG Images) ✅ DONE
Delivered:
- `backend/services/og_service.py` renders branded 1200×630 PNG (Pillow):
  - Dark navy `#101623`, teal `#2ba08a`
  - EB Garamond headline, wordmark eyebrow, category label, byline
  - Optional cover-image right panel with gradient fade; graceful fallback
- Fonts included at `backend/assets/fonts/`.
- Disk cache at `backend/cache/og_cards/` keyed by slug+title+updated_at+cover, auto-invalidates on edit and prunes stale versions.
- New endpoint:
  - `GET /api/og/{slug}.png` → `image/png` + `Cache-Control: public, max-age=86400`, 404 for unknown slug
- Wired into:
  - `/api/share/{slug}` meta tags (`og:image` + `twitter:image` + width/height/type)
  - `ArticlePage` SEO image (so canonical `/post/{slug}` unfurls branded too)
- JSON-LD preserves real cover photo for Google (prefers photos).

#### 50.C Cookie Auth Upgrade (httpOnly cookies) ✅ DONE
Delivered:
- JWT moved from localStorage → secure httpOnly cookie `ttn_session` (30d, Secure, SameSite=Lax).
- Backend:
  - `security.py` reads JWT from cookie **or** legacy Authorization Bearer header (migration).
  - `auth.py` endpoints now set cookie and **no longer return `token`** in JSON:
    - register/login/magic verify/password-reset confirm
  - New endpoints:
    - `POST /api/auth/logout` clears cookie
    - `POST /api/auth/cookie-sync` exchanges legacy Bearer session for cookie
- Frontend:
  - axios uses `withCredentials: true`
  - AuthContext:
    - `login(user)` signature
    - refreshUser migrates legacy localStorage token via `/auth/cookie-sync` then deletes it
    - logout calls backend
  - `aiStream.js` uses `credentials: 'include'`.

**CORS hardening required for cookie auth:**
- Initial assumption: `CORS_ORIGINS='*'` incompatible with `allow_credentials=True`.
- Final verified configuration: `CORS_ORIGINS="*"` works in this environment (Starlette echoes origin on credentialed requests); required by platform deployment rules.

#### 50.D Testing ✅ DONE
- Testing agent report: `/app/test_reports/iteration_36.json`
  - Backend: 15/15 passing
  - Frontend: flows pass; cookie persistence verified
- Manual/automated browser verification:
  - httpOnly cookie set
  - `localStorage.ttn_token` is `null`
  - session persists across reload
  - admin dashboard loads
- Cleanups:
  - Deleted temporary test artifact that contained credentials.
  - Cleaned test users.

### Phase 51 — Pillar-Coloured Share Cards (v2 design) ✅ COMPLETED (PREVIEW)
User request: give each pillar its own accent colour on OG share cards + make them more attractive.

Delivered in `backend/services/og_service.py` (v2; cache version bumped so old cards auto-regenerate):
- Pillar accent palette:
  - Tech & AI → **violet** `(129,122,244)`
  - Business & Finance → **brand teal** `(52,178,153)`
  - Personal Growth → **warm amber** `(222,158,66)`
  - Delivery & Systems → **steel blue** `(86,148,222)`
  - Unknown categories fall back to brand teal.
- Design upgrades:
  - Vertical vignette for depth
  - Soft radial accent glow behind headline
  - Subtle dot-grid texture
  - Rounded pillar chip (translucent accent fill + accent outline/text)
  - Accent wordmark tick + byline bar
  - Accent-tinted duotone cover panel with smoother eased gradient fade
  - Bottom accent strip that eases into the canvas
- QA bug fix:
  - 4-line titles without a cover overlapped the byline — adaptive sizing now also constrains vertical fit (shrinks down to 38px min and keeps clear of footer).
- Verified:
  - All 4 pillar variants render correctly (screenshots reviewed)
  - Long-title / no-cover / unknown-category edge cases pass
  - Live endpoint returns 200 `image/png` 1200×630 w/ Cache-Control
  - 404 for unknown slug
  - Logs clean
- Caching:
  - `_OG_VERSION='v2'` and `category` included in cache signature → production will mint new cards automatically after redeploy (no manual cache clearing).

**Requires redeploy to reach Production.**

---

## 3) Next Actions

### A) Production deployment status and environment clarity
If you are seeing an issue, confirm whether it is on:
- **Preview** (this dev environment) or
- **Production** (https://thetradingnarrative.com)

### B) Production rollouts pending redeploy (Preview → Production)
- Phase 44 (pillar audio exclusivity) requires a redeploy.
- Phase 45 (keyword SEO targeting) requires a redeploy.
- Phase 46 (growth suite + early bird + homepage banner) requires a redeploy.
- Phase 47 (site title + dynamic essay meta descriptions) requires a redeploy.
- Phase 48 (health probes + env fix + llms/robots/schema) requires a redeploy.
- Phase 49 (code review fixes) requires a redeploy.
- Phase 50 (sitemap index + OG images + cookie auth) requires a redeploy.
- **Phase 51 (pillar-coloured OG share cards v2)** requires a redeploy.

**After deploying Phase 50+51 to Production:**
- Resubmit `https://thetradingnarrative.com/sitemap.xml` in GSC.
- Validate social previews:
  - LinkedIn Post Inspector: paste a `/post/{slug}` URL
  - X Card Validator alternatives / WhatsApp share
- Readers should auto-migrate sessions; some may need to sign in again once depending on browser state.

### C) Payment gateways
- “Test mode” banners cannot be removed with code.
- To remove: switch to LIVE Stripe/Razorpay keys.

### D) Upcoming (still blocked)
- **PayPal Checkout** (recurring subscriptions) ⛔
  - Need PayPal client ID + secret and final flow decisions
- **Resend Integration** ⛔
  - Need Resend API key + verified sender domain

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe checkout works.
✅ Razorpay checkout works.
✅ Email sending is LIVE with unsubscribe + digest systems.
✅ Highlights system complete.
✅ Admin analytics complete.
✅ Narration ops are self-serve and hardened.
✅ AI features work (writing assistant + ask-essay).
✅ Cross-platform sharing works.
✅ Founding wall works.
✅ Lounge hub provides a premium community destination.

✅ Phase 42 success targets met
- Anonymous visitors can read 3 full free essays (metered) without sign-in
- Locked previews are visible and marked with paywall structured data
- No cloaking / UA sniffing
- Topic hubs exist and support discovery
- Sitemap/robots/RSS correct

✅ Phase 43 success targets met
- Business & Finance: newsletter editions + shipping essays have free full audio; other finance essays offer 20s preview + unlock.
- Unlock persists in `purchased_audio_slugs`.
- **My Audio Library** lists purchased narrations.

✅ Phase 44 success targets met (Preview)
- Premium pillars audio is Premium-only.
- Non-premium readers see no audio player on those pillar essays.

✅ Phase 45 success targets met (Preview)
- Keyword-rich defaults exist for title/description/keywords.
- Homepage emits WebSite + Organization JSON-LD.
- Briefings and Archive pages are tuned for “weekly briefing / newsletter / freight / trading”.
- Single meta description + keywords + og:title on rendered pages.

✅ Phase 46 success targets met (Preview)
- Admin Growth tab shows:
  - Audio narration unlock sales + revenue
  - Manual keyword rank tracker with history + deltas
  - Early bird claims remaining
- Pricing page surfaces Early Bird discount correctly and enforces **first 50 premium subscribers** cap.
- Homepage surfaces the early bird deal via banner above the hero.

✅ Phase 47 success targets met (Preview)
- Homepage site title is exactly: **The Trading Narrative | Commodity Trading & Tech Insights**
- Default meta keywords include: commodity trading, energy markets, trading technology, ETRM, market risk
- Each essay page generates a **dynamic meta description** derived from real essay content (excerpt or opening paragraphs)
- `/api/share/{slug}` crawler HTML mirrors the same dynamic description

✅ Phase 48 success targets met (Preview)
- Kubernetes liveness/readiness probes succeed (`GET /health` returns 200)
- Deployment agent scan passes (env fixed)
- `/llms.txt` is served and accurately describes the site
- robots policy exists for major AI crawlers and points to `/llms.txt`
- Structured data enhanced: breadcrumbs, topic collection pages, pricing offers, about person
- Sitemap verified dynamic and complete

✅ Phase 49 success targets met (Preview)
- No hardcoded secrets remain in backend test artifacts (deleted)
- Crypto-safe randomness used for invoice numbers
- Frontend silent catches now log debug info
- GrowthPanel row keys fixed
- AdminPage expensive filter memoized
- Backend code linted (pyflakes) with only intentional side-effect import in db.py

✅ Phase 50 success targets met (Preview)
- `GET /sitemap.xml` returns valid XML sitemap index (not React HTML)
- `GET /api/og/{slug}.png` returns branded OG image and is used by `/api/share/{slug}` and essay pages
- Auth tokens are stored in secure httpOnly cookie `ttn_session` (Authorization header supported temporarily for migration)
- Frontend uses `withCredentials` and removes localStorage token after migration
- CORS is compatible with credentialed cookies under platform deployment rules

✅ Phase 51 success targets met (Preview)
- OG cards are pillar-coloured and visually richer (v2)
- v2 auto-invalidates old cached cards via `_OG_VERSION='v2'`
- 4-line/no-cover title layout is stable (no byline overlap)

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
