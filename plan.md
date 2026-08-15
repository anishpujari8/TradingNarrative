# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (**The Trading Narrative**) with an editorial reading experience, a freemium → premium conversion model, and a **premium community destination (Lounge)**.
- Support a unified, recognisable identity everywhere (site UI + share assets):
  - **Four core pillars/themes** (categories):
    - **Tech & AI** (`tech-business`)
    - **Trading, Business & Finance** (`finance`) ✅ *(renamed from “Business & Finance”)*
    - **Personal Growth** (`lifestyle`) *(DB slug; displayed as Personal Growth)*
    - **Delivery & Systems** (`delivery`) ✅
  - **Three section identities** (non-category destinations, styled like pillars):
    - **The Weekly Briefing** (`briefings`) ✅ *(Phase 64)*
    - **Bookshelf** (`books`) ✅ *(Phase 64)*
    - **The Lounge** (`lounge`) ✅ *(Phase 66)*
  - **Mascot showcase hub**:
    - **Dedicated Pillars page** (`/pillars`) ✅ *(Phase 65; enhanced Phase 66)*
      - Presents the 4 pillars + section identities with mascots, motif branding, and lore.
      - Each pillar includes an extended **“Lore” tooltip** (Phase 66).

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
- **Lounge mascot + identity** ✅ *(Phase 66)*
  - Mascot added to locked and member views

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
  - Linked in footer ✅
  - Included in sitemap ✅
- **Books page** ✅ *(Phase 62)*
  - `/books` (crawlable) + ItemList/Book JSON-LD
  - Included in sitemap ✅
- **Pillars showcase page** ✅ *(Phase 65)*
  - `/pillars` (crawlable) + CollectionPage JSON-LD
  - Included in sitemap ✅

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
- **Dedicated Pillars mascot page** ✅ *(Phase 65; enhanced Phase 66)*
  - `/pillars` hub consolidating mascots + motif branding
  - **Lore tooltips** on each pillar card ✅ *(Phase 66)*

### Navigation + information architecture
- Navbar includes primary site sections ✅
- **Pillars nav dropdown (desktop)** ✅ *(Phase 63)*
  - Replaced the 4 pillar links with a single **“Pillars”** trigger.
  - Opens on **hover** (with 150ms close grace) and remains click/keyboard accessible.
  - Dropdown items show pillar color dot + pillar label + tagline.
  - Trigger highlights when on `/category/*` pages.
  - All other nav links remain **single-line** via `whitespace-nowrap` and are vertically centered (no wrapping).
- Mobile sheet nav groups pillars under a **“Pillars”** label ✅ *(Phase 63; refined in Phase 65)*
- **Per-pillar themed dropdown styling (light + dark)** ✅ *(Phase 64)*
  - Dropdown titles use pillar accent colours.
  - Hover/focus tint + left border adapt by theme:
    - Light mode ~12% accent tint
    - Dark mode ~22% accent tint
- **Pillars trigger navigation to mascot hub** ✅ *(Phase 65)*
  - Clicking “Pillars” navigates to `/pillars`.
  - Dropdown includes a footer CTA: “Meet all the mascots →”.
  - Mobile nav includes a “Pillars →” link to `/pillars`.
- **Footer discoverability for mascot hub** ✅ *(Phase 66)*
  - Added “Meet the Mascots” link in footer (under Site).

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
  - 9 term cards
  - DefinedTermSet JSON-LD, SEO meta
- Routed in `App.js` and linked in `Footer.js` (“Trading Glossary”).
- Included in sitemap (`backend/routers/posts.py`).

**59.3 About page “Pillar Branding” section:**
- Added “The Pillars” section with:
  - mascot medallions
  - lore names + story blurbs + links to the pillar hubs
  - motif backgrounds for continuity

**59.4 Build stability note:**
- `App.js` edit anomalies occurred (duplicate tail + missing route line). Fixed via deterministic patch. `esbuild` verified.

### Phase 60 — Conversion Feedback Batch ✅ COMPLETED (PREVIEW)
User request: address external review feedback to reduce bounce + increase trust/conversions.

### Phase 61 — Instagram Link + Book Showcase ✅ COMPLETED (PREVIEW)

### Phase 62 — Books Page + Admin Bookshelf ✅ COMPLETED (PREVIEW)

### Phase 63 — Pillars Dropdown Nav + Books “Reading Notes” Links ✅ COMPLETED (PREVIEW)

### Phase 64 — Briefings + Books Mascots & Palettes + Themed Pillars Dropdown ✅ COMPLETED (PREVIEW)

### Phase 65 — Dedicated `/pillars` Page + Pillars Trigger Click Navigation ✅ COMPLETED (PREVIEW)

### Phase 66 — Footer Mascot Link + Lore Tooltips + Lounge Mascot ✅ COMPLETED (PREVIEW)
User request: strengthen discoverability of the mascot hub, add pillar “Lore” tooltips with provided copy, and create a Lounge mascot.

**66.1 Footer “Meet the Mascots” link:**
- `Footer.js`: added “Meet the Mascots” link → `/pillars` (`footer-mascots-link`) under **Site** after Trading Glossary.

**66.2 Pillars page lore tooltips:**
- `PillarsPage.js`: each of the 4 pillar cards includes a **Lore badge** (ScrollText icon) with accent-tinted chip.
- Tooltip (shadcn Tooltip) on hover shows the exact extended lore copy provided by the user (em-dashes preserved verbatim).
- Badge click uses `preventDefault()` + `stopPropagation()` so it never triggers the card navigation.
- Test IDs:
  - `pillars-lore-badge-{slug}`
  - `pillars-lore-tooltip-{slug}`

**66.3 Lounge mascot (“The Signal Wolf”):**
- Generated via `gemini-3.1-flash-image-preview` style-matched to existing emblems.
- Accent colour: plum magenta **#a04f86**.
- Optimized to `frontend/public/pillars/lounge.webp` (560×560 WebP).
- `lib/pillars.js`: added `lounge` to:
  - `PILLAR_ACCENTS`, `PILLAR_TAGLINES`, `PILLAR_MASCOT_ALTS`, `PILLAR_LORE`
  - `PillarMotif` (new howl-arc motif)
- Restored missing `briefings` and `books` entries in `PILLAR_MASCOT_ALTS` (previous edit regression).

**66.4 Pillars page section strip expanded:**
- “Also flying the flag” section changed to **3 cards** (Briefings, Books, Lounge) in a responsive grid.

**66.5 Lounge UI updated to show mascot:**
- `CommunityPage.js`:
  - Locked view: replaces generic Crown/Lock icon box with centered wolf medallion (`lounge-locked-mascot`).
  - Member lounge header: shows wolf medallion beside title (`lounge-mascot`).

**66.6 Verification / QA:**
- Playwright verified:
  - 4 Lore badges render and tooltips show correct copy
  - Badge click does not navigate away
  - 3 section cards render (includes lounge)
  - Footer link navigates to `/pillars`
  - Lounge mascot visible in locked and member views (admin login)
- `esbuild` clean.

**Requires redeploy:** to ship Phase 66 UI changes to production.

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

**Requires redeploy to ship UI/share/conversion changes (Phases 55–66 + Phase 56):**
1. Redeploy preview → production.
2. After deploy, spot-check:
   - Navbar: Pillars hover dropdown works; items don’t wrap; hover-open works on desktop.
   - Navbar: Clicking Pillars navigates to `/pillars`.
   - Navbar: per-pillar colour highlight works in both light and dark mode.
   - Navbar: dropdown contains “Meet all the mascots →”.
   - `/pillars`: page renders 4 pillar cards + 3 section cards (Briefings, Books, Lounge).
   - `/pillars`: Lore tooltips open and show the correct extended lore copy.
   - `/briefings`: banner shows crimson motif + falcon mascot.
   - `/books`: banner shows bronze motif + tortoise mascot.
   - `/lounge`: locked view shows wolf medallion; member view header shows wolf medallion.
   - Home hero: inline email capture + social proof line.
   - Home: author strip under hero.
   - Home: “Start here, free” section shows 3 free essays.
   - `/topics/{pillar}` shows mascot + motif header.
   - Article pages show pillar-tinted badge + progress bar and improved author byline.
   - Post cards show author byline + photo.
   - `/glossary` exists, is linked in footer, and is included in sitemap.
   - Footer under Site includes “Meet the Mascots”.
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

✅ Phase 65 targets met (PREVIEW)
- Dedicated `/pillars` mascot hub exists and is crawlable.
- Clicking “Pillars” navigates to `/pillars`.
- Hover dropdown still works and includes “Meet all the mascots →”.
- Sitemap includes `/pillars`.

✅ Phase 66 targets met (PREVIEW)
- Footer includes “Meet the Mascots” link to `/pillars`.
- Pillars cards show “Lore” tooltip badges with provided copy.
- Lounge has a dedicated mascot (Signal Wolf) shown in locked + member views.

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
