# plan.md — The Trading Narrative (FARM)

## 1) Objectives
- Ship a modern, subscription-based blog + newsletter platform (**The Trading Narrative**) with an editorial reading experience, a freemium → premium conversion model, and a **premium community destination (Lounge)**.
- Support **four pillars/themes** with a unified, recognisable identity everywhere (site UI + share assets):
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
- Reading progress indicators ✅ *(Phase 56 enhanced with pillar accents)*
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
  - Public counter endpoint + homepage urgency banner (“X of 50 spots left”) linking to /auth
  - Hidden for premium members / already early supporters / when spots exhausted
- **Early bird premium offer (homepage surfaced)** ✅ *(Phase 46 add-on)*
  - Homepage banner links to `/pricing`

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
  - **Business & Finance** (non-exempt): 20-second clip + one-time unlock ₹45/$0.50 ✅
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

### Social sharing (unfurls + branded assets)
- **Branded OG share cards** ✅ *(Phase 50)*
- **Pillar-coloured OG cards with signature motifs (v3)** ✅ *(Phase 51)*
- **OG cards upgraded with pillar mascots (v4)** ✅ *(Phase 58)*
- **Quote-card sharing matches pillar accents + motifs** ✅ *(Phase 54 + Phase 55)*
- **Pillar mascots (emblems) integrated in hub headers + homepage** ✅ *(Phase 57)*

### Branding + content readiness
- Official logo + favicon ✅
- Author identity normalized ✅
- Seed data self-healing ✅
- Catalog publish ✅

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
- Sync now uses `resp.json().get('token')` OR `resp.cookies.get('ttn_session')` in both `sync_push` and `sync_narrations`.
- Ran sync push: **22 production posts updated** (category moves + Phase 53 intros + Phase 54 dash cleanup + ETRM excerpt).
- Verified via production API: the 3 essays are now `category=lifestyle` (Personal Growth) live.

**57.2 Pillar mascots (Gemini image gen):**
- Generated via `gemini-3.1-flash-image-preview` using `EMERGENT_LLM_KEY`.
- Mascots:
  - Tech & AI: **violet circuit owl**
  - Business & Finance: **teal sparkline bull**
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
- `Navbar.js`: desktop nav links + mobile sheet links now show pillar-colour dots (`pillarAccent`) before each category label.
- Verified via screenshot: violet/teal/amber/steel-blue dots visible.

**58.2 OG share cards (v4):**
- `services/og_service.py`: `_OG_VERSION` bumped to `v4` (cache auto-invalidates).
- Mascots copied to `backend/assets/mascots/*.webp`.
- New `_mascot_medallion()` renders a circular mascot with an accent ring (2× supersampled mask).
- Medallion is pasted top-right on every OG card.
- Verified: all four pillar cards render beautifully with the correct mascot.

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

**Requires redeploy to ship UI/share changes (Phases 55–58 + Phase 56):**
1. Redeploy preview → production.
2. After deploy, spot-check:
   - Navbar category links show colour dots
   - Home “Browse by pillar” banner shows mascot
   - `/topics/{pillar}` shows mascot + motif header
   - Article pages show pillar-tinted badge + progress bar
   - `https://thetradingnarrative.com/api/og/{slug}.png` shows the new v4 mascot medallion
3. Force-refresh social previews (LinkedIn Post Inspector) if any shares still show old images.

### C) Payments
- “Test mode” strips cannot be removed with code.
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

⚠️ Operational caveats
- ElevenLabs credits balance display requires `user_read` permission on key.
- Gemini usage consumes Emergent LLM credits.

⛔ Blockers
- PayPal: awaiting decisions + credentials.
- Resend: awaiting decisions + API key + sender domain verification.
