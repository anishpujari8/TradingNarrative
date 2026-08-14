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
- **Growth Suite** ✅
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
  - **GSC compatibility (Phase 50):** `/sitemap.xml` is a valid XML sitemap **index** pointing to `/api/sitemap.xml` (avoids SPA/ingress HTML routing issues)
- **Robots** ✅ *(Phase 42 + Phase 48 additions)*
  - `frontend/public/robots.txt` disallows `/api/` while explicitly allowing:
    - `/api/sitemap.xml`, `/api/feed.xml`, `/api/share/`
  - Production sitemap URL referenced
  - **AI crawler policy sections added (Phase 48)** and a note to consult `/llms.txt`
  - Note: Preview domain may inject a platform-level robots.txt; localhost/production serve the app’s file
- **RSS feed** ✅ *(Phase 42)*
  - `/api/feed.xml`: full text for open/free essays; preview + link for locked
  - RSS discovery link injected in `public/index.html`
- **Topic hubs** ✅ *(Phase 42)*
  - `/topics/{pillar}` pages with 200–400 words of original intro copy
  - Chronological essay grids + archive links
  - Essay category badge links to hub
- **Keyword targeting** ✅ *(Phase 45)*
  - Keyword-rich defaults (title/description/keywords)
  - WebSite + Organization JSON-LD on homepage
  - Briefings + Archive tuned for “weekly briefing / newsletter / freight / trading”
  - Topic hubs already keyword-strong
  - Meta duplication fixed (static fallback tags removed on mount) so rendered pages have exactly one `description`, `keywords`, and `og:title`
- **Site title + dynamic essay meta descriptions** ✅ *(Phase 47)*
  - Site title: `The Trading Narrative | Commodity Trading & Tech Insights`
  - Default keywords emphasize: commodity trading, energy markets, trading technology, ETRM, market risk
  - Essay pages generate a dynamic meta description derived from article content
- **AI readiness** ✅ *(Phase 48)*
  - `/llms.txt` served with crawler-facing site overview
- **Social Preview Cards** ✅ *(Phase 50 + Phase 51)*
  - Every essay unfurls with a consistent, branded Open Graph image.
  - Implemented via backend-rendered OG images served at `GET /api/og/{slug}.png`.
  - **Phase 51:** cards are **pillar-coloured** and include distinct pillar signature motifs.

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
  - JWT stored in secure **httpOnly** cookie `ttn_session` (Secure, SameSite=Lax, 30d)
  - Migration: legacy Bearer tokens supported + `/api/auth/cookie-sync`
  - Logout: `/api/auth/logout`
  - **CORS compatibility for credentialed cookies:** `CORS_ORIGINS="*"` (platform requirement) verified to work

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
- Metered anonymous access (3 free full essays)
- Locked previews + paywall structured data
- RSS + sitemap + robots
- Topic hubs with original intro copy
- Hyphen cleanup

### Phase 43 — Per-Essay Audio Micro-Paywall (₹45 / $0.50) ✅ COMPLETED
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
- Premium pillars audio is hidden for non-premium; unlock checkout blocked

### Phase 45 — Keyword SEO Targeting ✅ COMPLETED
- Keyword-rich defaults (title/description/keywords)
- WebSite + Organization JSON-LD on homepage
- Briefings + Archive tuned for “weekly briefing / newsletter / freight / trading”

### Phase 46 — Growth Suite (Audio Sales + Manual Search Rank + Early Bird) ✅ COMPLETED
- Audio Sales Dashboard
- Manual Search Rank Tracker
- Early Bird Premium offer + homepage banner

### Phase 47 — Site Title + Dynamic Essay Meta Descriptions ✅ COMPLETED
- Site title set exactly
- Meta keywords tuned
- Essay meta description derived from article content

### Phase 48 — Deployment Fix + AI Assistant Readiness ✅ COMPLETED
- `/health` endpoint for K8s probes
- env fix for `EMERGENT_LLM_KEY`
- `llms.txt` + robots enhancements
- extra JSON-LD mapping (breadcrumbs, pricing offers, about person)

### Phase 49 — Code Review Fixes ✅ COMPLETED
- Deleted hardcoded-credential test artifacts
- Replaced `random` with `secrets`
- Frontend loop keys fixed, memoization, catch logging

### Phase 50 — Cookie Auth Upgrade + Social Preview Cards + Sitemap GSC Fix ✅ COMPLETED
- JWT moved to secure httpOnly cookie (`ttn_session`)
- Added logout + cookie-sync migration
- Branded OG cards endpoint `/api/og/{slug}.png`
- `/sitemap.xml` sitemapindex → `/api/sitemap.xml`
- Testing: `/app/test_reports/iteration_36.json`

### Phase 51 — Distinct Pillar Share Cards (v3 motifs) ✅ COMPLETED
- Pillar accent palette + signature motif illustration per pillar
- Disk-cached, versioned cards auto-regenerate

### Phase 52 — Keyword Gap Map (research) ✅ COMPLETED
- Gap research documented in `SEO.md` (Phase 52)
- Identified Tier 1 “snippet-ready” targets + Tier 2 new essays to win

### Phase 53 — SEO Gap Execution ✅ COMPLETED (PREVIEW)
**Goal:** Convert keyword-gap research into on-page snippet wins + publish new high-intent SEO pages + seed tracker.

#### 53.1 Snippet-ready intros (answer-first) ✅
Prepended answer-first opening paragraphs to 4 Tier 1 essays:
- Yield curve: targets **“what is a yield curve inversion”**
- $15B shipping: targets **“how to reduce demurrage charges”**
- Power trading: targets **“how do power trading desks work”**
- Freight visibility: targets **“what is freight visibility in logistics”**

Applied in BOTH:
- `backend/seed_data.py` (source-of-truth for self-healing)
- Preview database (refreshed `read_time` + `updated_at`)

**Important production note:** seed restore does **not** overwrite existing production posts. To push these intro updates to production:
- redeploy, then run **Admin → Content Sync → Update Mode** (Preview → Production), OR
- manually edit the production posts in Admin Studio.

#### 53.2 New SEO essay: ETRM vs CTRM ✅
- Added to `REAL_POSTS` (self-heals on fresh deployments)
- Slug: `etrm-vs-ctrm-whats-the-difference-and-which-one-do-you-actually-need`
- Tier: **free**, category: **finance**, ~16 blocks with `##` headings and a selection checklist

#### 53.3 New SEO glossary essay: Demurrage vs Detention ✅
- Added to `REAL_POSTS` (self-heals on fresh deployments)
- Slug: `what-is-demurrage-vs-detention-a-plain-english-guide-for-commodity-traders`
- Tier: **free**, category: **finance**, ~13 blocks with `##` headings
- References and feeds internal linking into the existing “$15B demurrage” essay

#### 53.4 Tracker seeding ✅
Seeded baseline keywords (Tier 1 + Tier 2) into `seo_keyword_stats`.

#### 53.5 Verification ✅
Verified:
- New essays are free/unlocked via API
- New essays appear in dynamic sitemap
- `/api/share/{slug}` emits keyword-rich meta descriptions
- OG cards render correctly (pillar palette + motif)
- Admin tracker returns seeded keywords
- Frontend renders new essays; related-post cross-links appear via overlapping tags
- Metered paywall behavior on anonymous identities is expected

### Phase 54 — Pillar Identity + Dash Cleanup + New SEO Essays + Quote Card Motifs ✅ COMPLETED (PREVIEW)

#### 54.1 “Pillar color not showing on live site” investigation ✅
- Confirmed **NOT a CSS issue**: pillar cards are server-rendered PNGs at `GET /api/og/{slug}.png`.
- Verified production is serving the v3 pillar cards.
- Root cause of perceived mismatch: social platforms cache previews. Recommended LinkedIn Post Inspector to force re-scrape.

#### 54.2 Dash cleanup ✅
- Removed remaining mid-paragraph em/en dashes from essays (e.g., `60–90` → `60 to 90`).
- Rephrased one em-dash excerpt line in the ETRM excerpt.
- Applied in **DB + `seed_data.py`**.
- Verified: **zero em/en dashes remain** in excerpts and bodies.
- Intentionally kept correct compound-word hyphens (e.g., “day-ahead”, “plain-English”).

#### 54.3 New SEO glossary: Laytime ✅
- New free essay added to `REAL_POSTS`:
  - `what-is-laytime-in-shipping-the-clock-that-decides-demurrage`
  - Answer-first, includes NOR, berth vs port, exceptions/pauses, despatch, “once on demurrage always on demurrage”.
- Verified: renders, appears in sitemap.

#### 54.4 New SEO glossary: TC/RC ✅
- New free essay added to `REAL_POSTS`:
  - `what-does-tc-rc-mean-in-metals-trading-treatment-and-refining-charges-explained`
  - Expanded from Lounge take; includes negative TC/RC explanation and CTRM sign-flip modelling warning.
- Verified: renders, appears in sitemap.

#### 54.5 Quote card accents + motifs ✅
- `QuoteCardDialog.js` updated to mirror pillar identity:
  - Pillar accent palette + signature motifs (circuits / sparkline / sunrise arcs / route)
- `ArticlePage` passes `post.category` into quote-share payload.
- Verified visually: all 4 pillar variants render correctly.

**Important production note (Phase 54):**
- New essays + quote card changes require a redeploy to appear in production.
- Dash cleanup for already-published production posts requires **Admin → Content Sync → Update Mode**.

### Phase 55 — Site-wide Pillar Identity + Essay Recategorization ✅ COMPLETED (PREVIEW)

#### 55.1 Shared pillar identity module ✅
- Added `frontend/src/lib/pillars.js` with:
  - `PILLAR_ACCENTS` (v3 palette): violet `#7a73e8`, teal `#1c8570`, amber `#c4872e`, steel blue `#3f7cc4`
  - `PILLAR_TAGLINES`
  - `withAlpha()` helper
  - `PillarMotif` SVG component (currentColor-stroked motifs: circuits / sparkline / arcs / route)

#### 55.2 PostCard styling ✅
- `PostCard.js` updated:
  - pillar-tinted card border (alpha 0.32; hover alpha 0.7)
  - 3px accent strip under the cover image
  - category badge coloured by pillar
- This affects all grids that use `PostCard`: homepage, topic hubs, archive, recommendations.

#### 55.3 Home page pillar identity ✅
- `HomePage.js` updated:
  - latest-list category labels coloured by pillar
  - Browse-by-pillar tabs include accent dots
  - selecting a pillar shows an accent-tinted header banner with motif background + tagline + hub link

#### 55.4 Topic hub headers ✅
- `TopicPage.js` updated:
  - header rebuilt as accent-tinted banner with motif background + accent underline bar
  - coloured marker on the essays heading
- **Bug fixed:** runtime error due to missing import after edit anomaly; fixed + verified.

#### 55.5 Essay recategorization ✅
- Moved 3 essays from **Delivery** → **Personal Growth** in **DB + `seed_data.py`**:
  - `slow-travel-the-month-long-stay-changes-everything`
  - `the-shoulder-season-playbook-same-trip-half-the-price`
  - `working-from-anywhere-a-field-tested-remote-setup`
- Delivery pillar now contains only **“Delivering a Power Trading Desk”**.
- OG cards auto-regenerated with amber identity for moved essays (verified).

#### 55.6 Verification ✅
- Verified via screenshots:
  - homepage All/Tech/Personal Growth/Delivery views
  - topic hubs (Delivery + Personal Growth)
  - dark mode
  - moved essays appear under Personal Growth
- Frontend build passes (`esbuild`).

**Important production note (Phase 55):**
- Requires redeploy for the site-wide UI changes to ship.
- Recategorization on production can be pushed via **Admin → Content Sync (Update Mode)** because `category` is in `SYNC_FIELDS`.

### Phase 56 — Article Page Pillar Accents ✅ COMPLETED (PREVIEW)
User request: carry the pillar colour into the essay page with a tinted category badge and reading progress bar.

Delivered:
- `ReadingProgress.js`: added optional `accent` prop
  - Top progress bar uses pillar accent colour
  - “≈ N min left” pill gains a pillar-coloured dot
- `ArticlePage.js`:
  - Category badge now pillar-tinted (accent bg 12%, accent text, accent border 30%); still links to the topic hub
  - Passes `pillarAccent(post.category)` into `ReadingProgress`
  - Imports `pillarAccent`/`withAlpha` from `lib/pillars`

Verification:
- Browser-verified on a Personal Growth essay:
  - badge text + progress bar computed colour match `#c4872e` (rgb(196,135,46))
  - pill visible with dot
- Frontend compiles cleanly (`esbuild`).

Production note:
- Ships with next redeploy.

---

## 3) Next Actions

### A) Environment clarity
If you report any issue, confirm whether it is on:
- **Preview** (dev) or
- **Production** (https://thetradingnarrative.com)

### B) Production rollout checklist (recommended order)
1. **Redeploy** to ship Phase 55–56 UI updates (site-wide + article-page pillar identity) + new SEO essays.
2. Run **Admin → Content Sync (Update Mode)** to apply to production:
   - Phase 53 snippet-ready intros
   - Phase 54 dash cleanup
   - Phase 55 recategorization
3. **Resubmit sitemap** in Google Search Console:
   - `https://thetradingnarrative.com/sitemap.xml`
4. **Force refresh social previews** for key URLs:
   - Use LinkedIn Post Inspector to re-scrape; platform caches may mask changes.
5. **Seed tracker with real data weekly**
   - Add positions/clicks/impressions for seeded keywords each week (new `noted_on`).

### C) Payments
- “Test mode” banners cannot be removed with code.
- To remove: switch to LIVE Stripe/Razorpay keys.

### D) Still blocked
- PayPal recurring subscriptions: needs credentials + final decision
- Resend: needs API key + verified sender domain

---

## 4) Success Criteria
✅ Premium posts never return full content to non-premium users from the API.
✅ Stripe checkout works.
✅ Razorpay checkout works.
✅ Email sending is LIVE with unsubscribe + digest systems.
✅ Highlights system complete (including shareable quote cards).
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

✅ Phase 50–51 success targets met
- Cookie auth: httpOnly cookie sessions, migration path, logout
- `/sitemap.xml` is valid XML sitemapindex
- Branded OG cards for every essay, with pillar-coloured + motif variants

✅ Phase 53 success targets met (PREVIEW)
- Answer-first intros implemented for Tier 1 targets
- New free SEO essays published via `REAL_POSTS` and verified in sitemap/share/OG
- Baseline keyword tracker seeded and visible in Admin

✅ Phase 54 success targets met (PREVIEW)
- Live pillar-card “missing CSS” concern debunked (cards are server PNGs; production verified)
- All mid-paragraph em/en dashes removed from excerpts/bodies (DB + seed)
- Laytime + TC/RC public SEO essays added and verified
- Quote cards updated to match pillar colour + motif identity and verified visually

✅ Phase 55 success targets met (PREVIEW)
- Site-wide pillar identity applied via shared module (accents + motifs)
- Post cards, homepage browse-by-pillar UI, and topic hub headers all use pillar styling
- Delivery pillar now contains only the Power Trading Desk essay; other three moved to Personal Growth

✅ Phase 56 success targets met (PREVIEW)
- Article page category badge + reading progress UI adopt pillar accents
- Verified visually and compiled cleanly

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
