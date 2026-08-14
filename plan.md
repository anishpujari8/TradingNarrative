# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (**The Trading Narrative**) with an editorial reading experience, a freemium → premium conversion model, and a **premium community destination (Lounge)**.
- Support a unified, recognisable identity everywhere (site UI + share assets):
  - **Four core pillars/themes** (categories):
    - **Tech & AI** (`tech-business`)
    - **Trading, Business & Finance** (`finance`) ✅ *(renamed from “Business & Finance”)*
    - **Personal Growth** (`lifestyle`) *(DB slug; displayed as Personal Growth)*
    - **Delivery & Systems** (`delivery`) ✅
  - **Two section identities** (non-category destinations, styled like pillars):
    - **The Weekly Briefing** (`briefings`) ✅ *(Phase 64)*
    - **Bookshelf** (`books`) ✅ *(Phase 64)*

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
- Reading progress indicators ✅ *(Phase 56 enhanced with pillar accents; includes pillar-coloured progress bar and dot)*
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
  - ShareBar “Share anywhere”:
    - Uses native share sheet when available (iOS/Android)
    - Falls back to an all-platform dialog with WhatsApp/Telegram/X/LinkedIn/Facebook/Email/Copy Link
  - WhatsApp quick-share button
  - Quote-card sharing never dead-ends: native file share → link share → auto-download with guidance
- **Reading Streaks** ✅ *(Phase 37)*
  - Reward regular readers with a streak counter (current + longest)
  - Updates on article reads (logged-in users; local-calendar-day aware)
  - UI surfaced in Navbar + Account page
- **Streak Milestones + Badges** ✅ *(Phase 39)*
  - Milestones: **7 / 30 / 100** consecutive days
  - Backend persists `streak_badges` (computed from **longest** streak)
  - Article milestone celebration toast + deep-link to Account
  - Account page shows earned vs locked states
- **Early supporter promo** ✅ *(Phase 38)*
  - First 50 registered users flagged as early supporters
  - Early supporters can read the first 5 published essays fully
  - Badge shown on Account page
- **Early supporter promo counter** ✅ *(Phase 39)*
  - Public counter endpoint + homepage urgency banner
  - Hidden for premium members / already early supporters / when spots exhausted
  - **Reframed when 0 claimed** ✅ *(Phase 60)* to avoid negative social proof
- **Early bird premium offer (homepage surfaced)** ✅ *(Phase 46 add-on)*
  - Homepage banner links to `/pricing`
  - **Reframed when 0 claimed** ✅ *(Phase 60)* to avoid “50 of 50” negative social proof
- **Free sampling to reduce bounce** ✅ *(Phase 60)*
  - Homepage “Start here, free” strip shows 2–3 strong free essays prominently
- **Bookshelf → Archive linking (“Reading Notes”)** ✅ *(Phase 63)*
  - Each book can optionally link to a related essay in the archive.

### Newsletter & retention
- Weekly digest preview + send ✅
- **Highlight Digest Social Proof** ✅ *(digest includes “Most highlighted this week” when data exists)*
- **Weekly Listen Digest Social Proof** ✅ *(digest includes “Most listened this week” when data exists)*
- Weekly briefings archive + tooling ✅
- **Briefings rollout strategy (Editions 1–6 free)** ✅ *(Phase 38)*
- **Briefings weekly autosend** ✅ *(Phase 38)*
  - Every Wednesday **09:30 AM IST**
  - Once per ISO week guardrail
  - Toggle: `briefing_autosend` (default ON)
- **Free Edition Countdown banner** ✅ *(Phase 39)*
- **Streak reminder emails** ✅ *(Phase 41)*
  - 19:00–22:00 IST
  - Guardrails + toggle `streak_reminder`
- **Email capture conversion improvements** ✅ *(Phase 60)*
  - Inline hero email capture already present
  - Added on-page social proof copy under key forms

### Email sending (provider)
- **Gmail SMTP (LIVE)** ✅
- **Resend** ⛔ *(planned; blocked pending user decisions + API key + sender domain verification)*
- **Admin Alerts (Email Notifications)** ✅ *(Phase 37)*

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
  - **FREE full audio** for editions + Shipping-tag essays
  - **Trading, Business & Finance** (non-exempt): 20-second clip + one-time unlock ₹45/$0.50 ✅
  - **Premium pillars**: narration Premium-only; hide player for non-premium ✅

**Pricing note:** Stripe minimum: **$0.50** → final micro-paywall: **₹45 / $0.50** ✅

#### ElevenLabs credit protection ✅ *(Phase 41)*
- Startup warmup caps **NEW narration generations** to **2 per run**

### AI features (Gemini)
- **Gemini integration via emergentintegrations + EMERGENT_LLM_KEY** ✅
  - Admin AI Writing Assistant ✅
  - “Ask this essay” reader chat ✅
- Ask-essay requires sign-in ✅ *(Phase 40)*

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
  - **Cookie-auth compatible production login for sync** ✅ *(Phase 57)*
- **Growth Suite** ✅
  - Audio Sales Dashboard ✅
  - Manual Search Rank Tracker ✅
  - Early Bird Premium offer ✅
- **Bookshelf Admin Panel** ✅ *(Phase 62)*
  - Manage `/books` recommendations (add/edit/delete)
  - Link a book to an essay via the “Reading Notes” picker ✅ *(Phase 63)*

### Community (Premium Lounge)
- Private Community Lounge ✅
- Pins/locks/scheduled announcements/editing ✅
- Member profiles ✅
- **Premium Lounge Hub (hybrid)** ✅ *(Phase 40)*
  - Market Narrative feed
  - Early access drafts
  - Member discussions
- **Welcome Market Narrative take** ✅ *(Phase 41)*
  - Copper concentrate TC/RC sign flip

### Access model (METERED + PAYWALL, SEO-friendly)
- Archive index fully public ✅
- **Metered anonymous access (3 free full essays)** ✅ *(Phase 42)*
- Locked previews + paywall CTA ✅
- Hard-locked content rules ✅
- Signed-in free vs premium behavior ✅

### SEO infrastructure (React + FastAPI)
- No cloaking ✅
- Structured data ✅
- Dynamic sitemap ✅ (`/api/sitemap.xml`) + **GSC-compatible** `/sitemap.xml` index ✅ *(Phase 50)*
- robots.txt + llms.txt ✅
- RSS feed ✅
- Topic hubs ✅
- Keyword targeting ✅
- Dynamic essay meta descriptions ✅
- **Glossary hub page** ✅ *(Phase 59)*
  - `/glossary` (crawlable) + **DefinedTermSet JSON-LD**
  - Linked in footer
  - Included in sitemap
- **Books page** ✅ *(Phase 62)*
  - `/books` (crawlable) + ItemList/Book JSON-LD
  - Included in sitemap

### Social sharing (unfurls + branded assets)
- **Branded OG share cards** ✅ *(Phase 50)*
- **Pillar-coloured OG cards with signature motifs** ✅ *(Phase 51+)*
- **Pillar mascots generated + integrated (UI)** ✅ *(Phase 57)*
- **Quote-card sharing matches pillar accents + motifs** ✅ *(Phase 54 + Phase 55)*
- **Navbar pillar dots** ✅ *(Phase 58)*
- **OG share cards carry pillar mascot medallion** ✅ *(Phase 58, v4+)*
- **OG cards updated for pillar rename** ✅ *(Phase 59, v5)*

### Branding + content readiness
- Official logo + favicon ✅
- Author identity normalized ✅
- Catalog publish ✅
- Seed data self-healing ✅
- **Pillar branding on About page** ✅ *(Phase 59)*
  - Mascot medallions + lore names and story blurbs
- **Credibility surfaces throughout site** ✅ *(Phase 60)*
  - Author strip on homepage
  - Byline + photo on post cards
  - Strong author byline on article page
- **Book showcase on About page** ✅ *(Phase 61)*
- **Dedicated Books page + Admin bookshelf** ✅ *(Phase 62)*
- **Briefings + Books mascots + palettes (styled like pillars)** ✅ *(Phase 64)*
  - Dedicated mascots, accents, motifs
  - Pillar-style header banners on `/briefings` and `/books`

### Navigation + information architecture
- Navbar includes primary site sections ✅
- **Pillars nav dropdown (desktop)** ✅ *(Phase 63)*
  - Replaced the 4 pillar links with a single **“Pillars”** trigger.
  - Opens on **hover** (with 150ms close grace) and remains click/keyboard accessible.
  - Dropdown items show pillar color dot + pillar label + tagline.
  - Trigger highlights when on `/category/*` pages.
  - All other nav links remain **single-line** via `whitespace-nowrap` and are vertically centered (no wrapping).
- Mobile sheet nav groups pillars under a **“Pillars”** label ✅ *(Phase 63)*
- **Per-pillar themed dropdown styling (light + dark)** ✅ *(Phase 64)*
  - Dropdown titles use pillar accent colours.
  - Hover/focus tint + left border adapt by theme:
    - Light mode ~12% accent tint
    - Dark mode ~22% accent tint

### Stability
- Modular backend ✅
- Regression testing discipline ✅

### Security hardening
- **Cookie auth upgrade (httpOnly session cookies)** ✅ *(Phase 50)*
  - JWT in httpOnly cookie `ttn_session`
  - Migration via `/api/auth/cookie-sync`
  - Logout `/api/auth/logout`
  - CORS compatible with credentials ✅

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC ✅ DONE

### Phase 2 — V1 App Development ✅ DONE

### Phase 3 — Hardening + Feature Completion ✅ DONE

### Phase 4 — Payments Integrations (Stripe + Razorpay) ✅ DONE

### Phase 5 — V2 Admin Analytics + Community ✅ DONE

### Phase 6 — V2.2 Enhancements ✅ DONE

### Phase 7 — V2.3 Enhancements ✅ DONE

### Phase 8 — V2.4 Enhancements ✅ DONE

### Phase 9 — V2.5 Enhancements ✅ DONE

### Phase 10 — V2.6 Enhancements ✅ DONE

### Phase 11 — Branding + Author Identity + Content Import ✅ DONE

### Phase 12 — Pillar Cleanup + Briefing Tooling ✅ DONE

### Phase 13 — Briefings Series Page + Wednesday Reminder ✅ DONE

### Phase 14 — Freight Visibility Import ✅ DONE

### Phase 15 — Backend Modularization Refactor ✅ DONE

### Phase 16 — Delivery Essay Import ✅ DONE (superseded)

### Phase 17 — Reader Highlights + Related ✅ DONE

### Phase 18 — Highlight Notes + Highlight Sharing ✅ DONE

### Phase 19 — PayPal Integration ⛔ NOT STARTED
**Blocked on user decisions + credentials**

### Phase 20 — Production Content Bug Fix + Share From Article + Popular Highlights ✅ DONE

### Phase 21 — Hardcoded Real Content + Highlight Digest + Content Sync Tool ✅ DONE

### Phase 22 — Additional Imports + Production Sync ✅ DONE

### Phase 23 — Series + Social Unfurls + Baseline Essay Audio ✅ DONE

### Phase 24 — ElevenLabs Narration + Caching ✅ DONE

### Phase 25 — Author Normalization + Spinning Logo + Listen Analytics ✅ DONE

### Phase 26 — Narration Status Panel + Demo Cleanup + Warmup ✅ DONE

### Phase 27 — Listen Completion Rate ✅ DONE

### Phase 28 — Weekly Listen Digest ✅ DONE

### Phase 29 — Gemini AI Integration ✅ DONE

### Phase 30 — Narration Bug RCA + Narration Sync Tool ✅ DONE

### Phase 31 — Resend Integration ⛔ NOT STARTED

### Phase 32 — Narration Corruption Hardening ✅ DONE

### Phase 33 — Narration Health Alert ✅ DONE

### Phase 34 — Delivery Essay + Premium Gating ✅ DONE

### Phase 35 — Premium Growth Batch ✅ DONE

### Phase 36 — Founding Member Wall + Cross-Platform Sharing ✅ DONE

### Phase 37 — Reader Engagement + Admin Alerts ✅ DONE

### Phase 38 — Growth Revamp ✅ COMPLETED

### Phase 39 — Engagement Boosters ✅ COMPLETED

### Phase 40 — Access Model + Premium Lounge Hub ✅ COMPLETED

### Phase 41 — Catalog Publish + Welcome Take + Streak Reminders ✅ COMPLETED

### Phase 42 — Metered Access + SEO Infrastructure ✅ COMPLETED

### Phase 43 — Per-Essay Audio Micro-Paywall ✅ COMPLETED

### Phase 44 — Premium Pillar Audio Exclusivity ✅ COMPLETED

### Phase 45 — Keyword SEO Targeting ✅ COMPLETED

### Phase 46 — Growth Suite ✅ COMPLETED

### Phase 47 — Site Title + Dynamic Meta Descriptions ✅ COMPLETED

### Phase 48 — Deployment Fix + AI Crawler Readiness ✅ COMPLETED

### Phase 49 — Code Review Fixes ✅ COMPLETED

### Phase 50 — Cookie Auth + OG Cards + Sitemap Fix ✅ COMPLETED

### Phase 51 — Pillar Share Cards v3 ✅ COMPLETED

### Phase 52 — Keyword Gap Map ✅ COMPLETED

### Phase 53 — SEO Gap Execution ✅ COMPLETED
- Answer-first intros
- New SEO essays: ETRM vs CTRM; Demurrage vs Detention
- Seeded search tracker keywords

### Phase 54 — Dash Cleanup + Laytime + TC/RC + Quote Card Accents ✅ COMPLETED
- Removed mid-paragraph em/en dashes from essays
- New SEO essays: Laytime; TC/RC
- Quote cards match pillar identity

### Phase 55 — Site-wide Pillar Identity + Recategorization ✅ COMPLETED (PREVIEW)
- Shared pillar identity module `lib/pillars.js`
- Post cards: borders + category tags adopt pillar colours
- Home: pillar tabs with dots + pillar header banner with motif
- Topic hubs: pillar header banners with motif
- Moved 3 essays delivery→personal growth (preview)

### Phase 56 — Article Page Accents ✅ COMPLETED (PREVIEW)
- Tinted category badge by pillar
- Pillar-coloured reading progress bar + pill dot

### Phase 57 — Production Category Sync + Sync Tool Fix + Pillar Mascots ✅ COMPLETED
**57.1 PRODUCTION FIX (live, no redeploy needed):**
- Root cause of repeated request: preview was fixed but production DB wasn’t synced.
- Also fixed a cookie-auth regression: `sync.py` expected `token` in production login response.
- Sync now uses `resp.json().get('token')` OR resp.cookies.get('ttn_session') in both `sync_push` and `sync_narrations`.
- Ran sync push: **22 production posts updated** (category moves + Phase 53 intros + Phase 54 dash cleanup + ETRM excerpt).
- Verified via production API: the 3 essays are now `category=lifestyle` (Personal Growth) live.

**57.2 Pillar mascots (Gemini image gen):**
- Generated via `gemini-3.1-flash-image-preview` using `EMERGENT_LLM_KEY`.
- Mascots:
  - Tech & AI: **violet circuit owl**
  - Trading, Business & Finance: **teal sparkline bull**
  - Personal Growth: **amber phoenix + sunrise rings**
  - Delivery & Systems: **steel-blue albatross + waypoint route**
- Center-cropped to 560×560, optimized to WebP (16–38KB) at `frontend/public/pillars/{slug}.webp`.

**57.3 UI integration:**
- `lib/pillars.js` exports `pillarMascot()` + alt text map.
- Topic hubs show mascot medallion beside the title; homepage pillar banner shows smaller medallion.
- Fixed HomePage edit anomaly (duplicated tail + dropped mascot img block) caught by `esbuild`.
- Verified: all 4 hubs + homepage show mascots.

### Phase 58 — Navbar Pillar Dots + Mascot Share Cards ✅ COMPLETED (PREVIEW)
**58.1 Navbar pillar dots:**
- `Navbar.js`: desktop nav links + mobile sheet links show pillar-colour dots (`pillarAccent`) before each category label.

**58.2 OG share cards (v4):**
- `services/og_service.py`: `_OG_VERSION` bumped to `v4` (cache auto-invalidates).
- Mascots copied to `backend/assets/mascots/*.webp`.
- New `_mascot_medallion()` renders a circular mascot with an accent ring (2× supersampled mask).
- Medallion is pasted top-right on every OG card.
- Verified: all four pillar cards render beautifully with the correct mascot.

### Phase 59 — Glossary Hub + Mascot Branding + Pillar Rename ✅ COMPLETED (PREVIEW)
**59.1 Pillar rename (finance):**
- `'finance'` label changed to **“Trading, Business & Finance”** in:
  - `backend/config.py` CATEGORIES
  - `frontend/src/lib/api.js` CATEGORIES
  - `frontend/src/pages/TopicPage.js` intro copy
  - `frontend/src/lib/pillars.js` mascot alt
- OG cards: `_OG_VERSION` bumped to **v5** so chips regenerate with new label (verified chip fits).
- RSS/JSON-LD escaping already safe (`_xml_escape` exists in `routers/posts.py`).

**59.2 Glossary Hub at `/glossary`:**
- `frontend/src/pages/GlossaryPage.js`
  - 9 term cards (Demurrage, Detention, Laytime, TC/RC, ETRM, CTRM, Freight Visibility, Yield Curve Inversion, Power Trading Desk)
  - one-breath definition + pillar dot/accent + motif background + link to essay
  - DefinedTermSet JSON-LD, SEO meta
- Routed in `App.js` and linked in `Footer.js` (“Trading Glossary”).
- Included in sitemap (`backend/routers/posts.py`).

**59.3 About page “Pillar Branding” section:**
- Added “The Pillars” section with:
  - mascot medallions
  - lore names: The Circuit Owl / The Sparkline Bull / The Rising Phoenix / The Route Albatross
  - story blurbs + links to the pillar hubs
  - motif backgrounds for continuity

**59.4 Build stability note:**
- `App.js` edit anomalies occurred (duplicate tail + missing route line). Fixed via deterministic patch. `esbuild` verified.

### Phase 60 — Conversion Feedback Batch ✅ COMPLETED (PREVIEW)
User request: address external review feedback to reduce bounce + increase trust/conversions.

**60.1 Free reads sampler:**
- Homepage “Start here, free” section (`home-free-reads-section`) showing 3 strong free essays (preferred order: **ETRM vs CTRM**, **$15B Shipping**, **Boring Portfolio**; falls back to any free tier).

**60.2 Author credibility:**
- ArticlePage byline upgraded: “By Anish Pujari · 12 years delivering ETRM & trading systems” with avatar fallback to `/anish.jpg`.
- PostCard meta row: tiny author photo + “Anish Pujari” on every card.

**60.3 Homepage author strip:**
- Added under hero: photo + credibility line (“ETRM product leader … author of How Trading Can Make You Money”), About link, and LinkedIn newsletter subscribe link.

**60.4 Scarcity reframe:**
- Early-bird banner hides the counter when 0 claimed (shows “early-bird pricing for the first 50 members” instead of “50 of 50”).
- Early supporter banner shows counter only when taken > 0 (currently genuine 49/50). Counters reappear automatically once sales/claims exist.

**60.5 Footer:**
- LinkedIn icon points to real profile (`linkedin.com/in/anish-pujari-69174b6a`).
- Added “Subscribe on LinkedIn →” (newsletter URL), book mention line, and social proof under newsletter form.
- Instagram was generic (`instagram.com`) — blocker cleared in Phase 61.

**60.6 Social proof copy:**
- “Join 500+ commodity trading professionals” under hero form, home newsletter block, and footer form.

**Already satisfied pre-review:**
- Inline hero email capture already present.
- Featured article has a strong visual (cover image + gradient card).
- Pillar colour coding on cards already implemented.
- Dark mode toggle already exists.

**Verified:** screenshots for banners, author strip, free reads grid, footer links, and article byline; `esbuild` clean.

### Phase 61 — Instagram Link + Book Showcase ✅ COMPLETED (PREVIEW)
**61.1 Instagram link:**
- Footer Instagram icon + About “Follow on Instagram” button now point to **https://www.instagram.com/anishpujari8** (user handle **@anishpujari8**).

**61.2 Book showcase on About page:**
- Added a book showcase section (`data-testid="about-book-section"`) inserted between the author section and The Pillars.
- Optimized user-provided flat-lay image to `frontend/public/book-cover.webp` (~135KB).
- Copy included:
  - Title: **How Trading Can Make You Money**
  - Subtitle: **An Honest Beginner's Roadmap: Strategies, AI Prompts & a 12-Month Plan**
  - User blurb: SEBI F&O 90% stat + risk/process promise (dash-free phrasing)
- CTAs:
  - “Get the book” button now points to canonical Amazon dp URL: **https://www.amazon.in/dp/B0HBR9THSX** ✅ *(blocker cleared in Phase 62)*
  - “Subscribe on LinkedIn” points to the LinkedIn newsletter follow URL.

**Verified:** screenshot confirms the section renders beautifully above The Pillars; Instagram hrefs correct; `esbuild` clean.

### Phase 62 — Books Page + Admin Bookshelf ✅ COMPLETED (PREVIEW)
User request: dedicated `/books` page with scalable recommendations managed from admin.

**62.1 Backend (routers/books.py):**
- Public: `GET /api/books`.
- Admin CRUD (guarded by `get_admin_user`):
  - `POST /api/admin/books`
  - `PUT /api/admin/books/{id}`
  - `DELETE /api/admin/books/{id}`
- Sorting: featured-first → sort → created_at.
- Seed-on-startup via `ensure_seed_books()`:
  - `seed_key`: `how-trading-can-make-you-money-v1`
  - Title: **How Trading Can Make You Money**
  - Author: **Anish Pujari**
  - Cover: `/book-cover.webp`
  - Buy link: **https://www.amazon.in/dp/B0HBR9THSX**
  - `featured=True` (shows “By the author” badge)
- Router registered in `server.py` and seeded in the startup hook.

**62.2 Frontend `/books` page (BooksPage.js):**
- Grid layout of book cards (cover, title, author, description, “Buy on Amazon” button).
- Loading skeletons + empty state.
- SEO meta + ItemList/Book JSON-LD.
- Routed in `App.js`.

**62.3 Navbar:**
- Desktop: “Books” link (`nav-books-link`).
- Mobile: “Books” link (`nav-mobile-books-link`).

**62.4 Admin:**
- New “Books” tab (`admin-tab-books`) in `AdminPage` rendering `components/admin/BooksPanel.js`:
  - Add/edit form: title, author, description, cover URL, buy URL, featured switch, sort.
  - Shelf list with edit + delete (confirm).

**62.5 SEO plumbing:**
- `/books` added to dynamic sitemap.

**Verification:**
- API seed + CRUD smoke test (create/update/delete 200, unauthed 401).
- `/books` page + navbar link + admin panel verified visually; `esbuild` clean.

**Requires redeploy:** to ship live (seed will self-heal into production on startup).

### Phase 63 — Pillars Dropdown Nav + Books “Reading Notes” Links ✅ COMPLETED (PREVIEW)
User request: streamline navbar + make book shelf feed the archive.

**63.1 Pillars dropdown (Navbar desktop):**
- Replaced the four desktop pillar links with a single **“Pillars”** trigger (`data-testid="nav-pillars-trigger"`).
- Implemented with shadcn **DropdownMenu** using controlled open state:
  - Opens on **hover**.
  - Closes with a **150ms grace** (prevents accidental close when moving into menu).
  - Remains click/keyboard accessible.
- Dropdown entries show:
  - Pillar colour dot (`pillarAccent`)
  - Pillar label (`CATEGORIES`)
  - Tagline (from `PILLAR_TAGLINES`)
- Trigger highlights automatically when on `/category/*` pages.
- All other nav links remain **single-line** and vertically centered (no more wrapping) via `whitespace-nowrap`.

**63.2 Pillars in mobile Sheet nav:**
- Pillars remain a list but are grouped under a **“Pillars”** label.
- All other mobile links unchanged.

**63.3 Book “Reading Notes →” links (Books → related essay):**
- Backend `books.py`:
  - Added optional fields: `related_slug`, `related_title` to `BookIn`.
  - Included fields in public serializer `_public()`.
  - Seed book updated to include:
    - `related_slug`: `the-boring-portfolio-that-beats-your-broker`
    - `related_title`: `The Boring Portfolio That Beats Your Broker`
- Admin `BooksPanel.js`:
  - Added “Reading Notes essay (optional)” **Select** fed from `GET /posts?limit=100`.
  - Persisted into book record: `related_slug` + `related_title`.
  - Shelf rows show `Notes: {related_title}` when set.
- Frontend `BooksPage.js`:
  - Renders “Reading Notes →” link to `/post/{related_slug}` under the Buy button when configured.

**63.4 Verification / QA:**
- Frontend build: `esbuild` clean.
- Backend API smoke:
  - Authenticated PUT/GET with new fields: **200**
  - Unauthenticated PUT: **401**
- Playwright verification:
  - Hover open/close + click navigation works for Pillars dropdown.
  - Admin picker saves and persists.
  - Mobile sheet layout verified.
- Seeded book’s **Preview DB record** links to the essay.

**Requires redeploy:** to ship UI changes to production.
**Optional:** books DB data can be synced Preview → Production using the existing sync tool/endpoint (content-only), without redeploy.

### Phase 64 — Briefings + Books Mascots & Palettes + Themed Pillars Dropdown ✅ COMPLETED (PREVIEW)
User request: add mascots and distinct colour identities for Weekly Briefing + Books, and colour the pillar dropdown per pillar in both light and dark mode.

**64.1 New section mascots (Gemini image gen):**
- Generated via `gemini-3.1-flash-image-preview` using `EMERGENT_LLM_KEY`.
- Style-matched against the existing pillar emblems using the **finance bull** as the reference.
- New mascots:
  - **Weekly Briefing** (`briefings`): *The Wire Falcon* — crimson accent **#c14953**, falcon carrying a rolled briefing over signal lines.
  - **Bookshelf** (`books`): *The Ledger Tortoise* — bronze accent **#9a6b3f**, tortoise with book-spine shell.
- Optimized to 560×560 WebP (~20–22KB) at:
  - `frontend/public/pillars/briefings.webp`
  - `frontend/public/pillars/books.webp`

**64.2 Section palettes + motifs in the pillar identity engine:**
- `frontend/src/lib/pillars.js`:
  - Added `briefings` and `books` to:
    - `PILLAR_ACCENTS`
    - `PILLAR_TAGLINES`
    - `PILLAR_MASCOT_ALTS`
  - Added new motif variants to `PillarMotif`:
    - `briefings`: telegraph pulses
    - `books`: book spines/shelf
  - `pillarAccent()` + `pillarMascot()` now support these section slugs.

**64.3 Pillar-style banners on /briefings and /books:**
- `BriefingsPage.js`:
  - Added pillar-style header banner:
    - accent border + background tint
    - motif background
    - accent underline bar
    - mascot medallion
  - Test IDs: `briefings-header-banner`, `briefings-mascot`
- `BooksPage.js`:
  - Added matching pillar-style header banner
  - Test IDs: `books-header-banner`, `books-mascot`

**64.4 Per-pillar themed dropdown styling (light + dark):**
- `Navbar.js`:
  - Each dropdown item sets a CSS var `--pillar-accent` for its own accent.
  - Added classes `pillar-dd-item` + `pillar-dd-title`.
- `index.css`:
  - Added theme-aware rules:
    - Title colour uses pillar accent (slightly brightened in dark mode)
    - Hover/focus background tint uses `color-mix()` (12% light / 22% dark)
    - Accent left border

**64.5 Verification / QA:**
- `esbuild` clean.
- Screenshots verified for:
  - `/briefings` banner + mascot
  - `/books` banner + mascot
  - Pillars dropdown hover styling in both light and dark mode (Playwright)

**Requires redeploy:** to ship Phase 64 UI changes to production.

---

## 3) Next Actions

### A) Environment clarity
If you report any issue, confirm whether it is on:
- **Preview** (dev) or
- **Production** (https://thetradingnarrative.com)

### B) Production rollout checklist (updated)
**Already live without redeploy:**
- Category changes for the 3 essays (Delivery → Personal Growth)
- Answer-first intros
- Dash cleanup

**Requires redeploy to ship UI/share/conversion changes (Phases 55–64 + Phase 56):**
1. Redeploy preview → production.
2. After deploy, spot-check:
   - Navbar: “Pillars” dropdown works; items don’t wrap; hover-open works on desktop.
   - Navbar: per-pillar colour highlight works in both light and dark mode.
   - Navbar: still includes “Books”, “Archive”, “Briefings”, “Lounge”, “About”.
   - `/briefings`: banner shows crimson motif + falcon mascot.
   - `/books`: banner shows bronze motif + tortoise mascot.
   - Home hero: inline email capture + social proof line.
   - Home: author strip under hero.
   - Home: “Start here, free” section shows 3 free essays.
   - `/topics/{pillar}` shows mascot + motif header.
   - Article pages show pillar-tinted badge + progress bar and improved author byline.
   - Post cards show author byline + photo.
   - `/glossary` exists, is linked in footer, and is included in sitemap.
   - `/books`: each configured book shows “Reading Notes →” linking into the archive.
   - Footer links: real LinkedIn profile + LinkedIn newsletter follow link + book mention + real Instagram profile.
   - About page: book showcase section visible above The Pillars; “Get the book” goes to https://www.amazon.in/dp/B0HBR9THSX.
   - `https://thetradingnarrative.com/api/og/{slug}.png` shows the latest share cards (v5 chips + mascot medallion).
3. Force-refresh social previews (LinkedIn Post Inspector) if any shares still show old images.

### C) Marketing copy accuracy
- Replace “Join 500+ commodity trading professionals” with a true number as soon as you have it.

### D) Payments
- “Test mode” strips cannot be removed with code.
- To remove: switch to LIVE Stripe/Razorpay keys.

### E) Still blocked
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
- Metered anonymous access works
- Locked previews + paywall structured data works
- Sitemap/robots/RSS correct

✅ Phase 50–51 success targets met
- Cookie auth sessions
- `/sitemap.xml` sitemapindex
- Branded OG cards with pillar motifs

✅ Phase 53–54 SEO execution targets met
- Snippet-ready intros
- SEO glossary essays published (Demurrage vs Detention, Laytime, TC/RC)
- Keyword tracker seeded
- Dash cleanup applied

✅ Phase 55–56 design targets met (PREVIEW)
- Site-wide pillar colours + motifs
- Post cards, topic hubs, homepage pillar section, and article page accents

✅ Phase 57 production + identity targets met
- Production content synced (category moves + intros + dash cleanup) ✅ LIVE
- Sync tool compatible with cookie auth ✅
- Pillar mascots generated + integrated (preview; deploy to ship UI) ✅

✅ Phase 58 identity targets met (PREVIEW)
- Navbar category links carry pillar dots
- OG share cards carry pillar mascot medallion

✅ Phase 59 SEO + branding targets met (PREVIEW)
- Glossary hub page with DefinedTermSet JSON-LD
- About page pillar branding section
- Finance pillar renamed to “Trading, Business & Finance”

✅ Phase 60 conversion targets addressed (PREVIEW)
- Free reads prominently shown
- Author credibility surfaced on cards + article pages + homepage
- Scarcity copy avoids negative “50 of 50”
- Footer links corrected (LinkedIn + LinkedIn newsletter) and book mentioned
- Social proof added under signup

✅ Phase 61 content/links addressed (PREVIEW)
- Instagram profile linked everywhere
- About page includes book showcase with cover + promise
- “Get the book” uses canonical Amazon dp URL

✅ Phase 62 Bookshelf targets met (PREVIEW)
- Dedicated `/books` page (SEO + JSON-LD)
- Admin-managed bookshelf (CRUD)
- Navbar includes Books link
- Seeded first book (B0HBR9THSX)

✅ Phase 63 targets met (PREVIEW)
- Desktop navbar: “Pillars” hover dropdown replaces the 4 pillar links; nav items remain single-line and centered.
- Books page: optional “Reading Notes →” links each book to a related essay.
- Admin: can attach a related essay to a book via picker.

✅ Phase 64 targets met (PREVIEW)
- Briefings and Books now have mascots + their own colour palette + motifs.
- `/briefings` and `/books` have pillar-style header banners.
- Pillars dropdown now tints items per pillar in both light and dark mode.

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
