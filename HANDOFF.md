# Reports system — handoff & next steps

Written 2026-04-15. This doc is your single source of truth for: where we are, what's blocking, what to do next, and how the auto-sync pipeline works end-to-end.

---

## TL;DR — where we're at

| Piece | Status | Notes |
|---|---|---|
| **Sup labs teamspace (Notion)** | ✅ Done | Reports DB moved under Sup Labs |
| **Notion schema** (faceted filtering) | ✅ Done | Industry / Sub-category / Location / Tags Text shadow |
| **GitHub repo** `supmg/sup-reports` | ✅ Done | Public |
| **Vercel hosting** | ✅ Deployed | `https://sup-reports.vercel.app/reports/gails` returns 200 |
| **First report end-to-end test** | ✅ Passing | GAIL's report live, Notion row populated |
| **Vercel GitHub App (push-to-deploy)** | ⚠️ **Blocked on you** | 30-sec browser install. See §5. |
| **Framer card design** | ⚠️ **Partial** — RPT-1 removed, rest needs polish | See §6 (click-by-click instructions) |
| **Framer detail page design** | ⏳ Not started | See §6 |
| **`/reports/*` proxy on sup.co** | ⚠️ **Blocked on your dev** | See §7 (message to send) |
| **Slug mismatch bug** | 🐛 **Found today** | Framer slug ≠ Vercel slug. See §8. |
| **`/publish-report` skill** | ⏳ Phase 2 | Build after design is done |

---

## 1 · The architecture, in plain English

Two surfaces, two stacks, glued together by one Notion DB:

```
                            ┌────────────────────────────┐
                            │   Notion — Reports DB       │   ← source of truth for
                            │   (Sup Labs teamspace)      │     all report metadata
                            └──────────────┬──────────────┘
                                           │  CMS sync (5-15 min polling)
                                           ▼
              ┌──────────────────────────────────────────────┐
              │   Framer site (various-designer-693318)      │
              │   /reports (index)                           │   ← Library card grid
              │   /reports/{framer-slug} (detail)            │   ← Landing page
              └──────────────┬───────────────────────────────┘
                             │  DNS proxy (CNAME on sup.co)
                             ▼
                    sup.co/reports                 ← what users see
                    sup.co/reports/{slug}
                             │
                             │  "Read the full report →" CTA button
                             ▼
              ┌──────────────────────────────────────────────┐
              │   Vercel — sup-reports.vercel.app            │
              │   /reports/{slug}  (full animated HTML)      │   ← 67KB self-contained
              └──────────────────────────────────────────────┘
                             ▲
                             │  git push to main
                             │
                     GitHub supmg/sup-reports
                             ▲
                             │  /publish-report skill writes + commits
                             │
                        Claude Code skill
```

**Why two surfaces:**

- **Framer (sup.co/reports + sup.co/reports/{slug})** = discovery / SEO / navigation. Cards, filtering by industry/location/sub-category, a nice landing page with the exec summary as a teaser, CTAs.
- **Vercel (sup-reports.vercel.app/reports/{slug})** = the actual animated deliverable. 60KB+ of inlined HTML/CSS/JS with all the animations, charts, data. Not something Framer can host well.

The Framer detail page's job is to get the user hooked (hero + summary + social proof) and hand them off to the Vercel page via a single CTA.

---

## 2 · Auto-sync flow (Notion → Framer → sup.co)

**Every time you publish a new report, this is what happens automatically:**

1. **You (or the `/publish-report` skill) create a Notion row** with:
   - Title, Brand, Industry, Sub-category, Location, Tags Text, Published Date, Cover, Exec Summary, Stats JSON, Full Report URL
2. **Framer polls Notion every 5–15 min** (its Notion CMS sync interval)
3. Framer writes the row to its internal CMS, mapped to your Reports collection
4. The `/reports` index and `/reports/{framer-slug}` detail page render automatically — no Framer edits needed
5. **The CNAME proxy** you've already set up for `sup.co/blog/*` (and need to set up for `sup.co/reports/*` — see §7) exposes the Framer pages under your domain

**You never touch Framer again after the initial design work.** New reports just appear.

---

## 3 · What's published where right now

- **Framer editor**: https://framer.com/projects/Sup--HEcSRmpz3wjYRH2TD6gj-3ttBl (project node `lBYRe5FwF` = `/reports` page)
- **Framer live**: various-designer-693318.framer.app/reports (what Framer publishes)
- **sup.co/reports**: **Not yet routable** — your dev needs to add the wildcard (§7)
- **Vercel**: https://sup-reports.vercel.app/reports/gails ✓ 200

---

## 4 · What I did in Framer today (via Chrome automation)

- Opened the `/reports` page
- Expanded the Layers panel → Desktop → Content → Reports (collection list) → Report (card template) → Text group
- **Deleted the "Report ID" layer** (the hardcoded "RPT-1" text under each title)
- Verified deletion (layer gone from tree, canvas re-rendered without it)

That's the only change that stuck. I stopped because Framer's canvas editor isn't great for browser automation — each layer interaction takes many round-trips, and building a multi-element card template this way would take hours. The design steps below you can do yourself in ~10 minutes.

---

## 5 · Vercel GitHub App install (30-sec user task)

Right now pushing to `main` doesn't auto-deploy — you have to `vercel --prod --yes` manually. Fix:

1. Open https://vercel.com/supmgs-projects/sup-reports/settings/git
2. Click **Connect Git Repository** → pick GitHub → authorize `supmg`
3. Select `supmg/sup-reports`, branch `main`
4. Done. Next `git push` auto-deploys.

After this, the `/publish-report` skill just does `git push` and you're live in ~30 seconds.

---

## 6 · Framer design — click-by-click

You're in the editor already. Here's the plan. **Ignore "RPT-1" — I already killed it.**

### 6a · Card template (what shows in the /reports grid)

Currently the card shows: cover image, title, date. We want it to be richer so the grid is scannable and filterable.

**Target layout:**
```
┌────────────────────────────────────────┐
│  [ cover image 16:9                  ] │
│                                        │
│  [F&B] [Bakeries]  ← pills             │
│  GAIL's Signal Report ← title          │
│  GAIL's Bakery · London · Apr 15, 2026 │
│                                        │
│  Signal strength is high but conv-     │
│  erting at creator tier, not macro…    │
│  ← 3-line exec summary (line-clamp)    │
│                                        │
│  [1.2M ]  [ +47% ]  [ 12 creators ]    │
│   reach    growth    found             │
│                                        │
│  Read report →                         │
└────────────────────────────────────────┘
```

**Steps inside Framer:**

1. Click the **Report** card in the layers panel (left side, under `Reports` collection)
2. In the canvas you'll see just [image + title + date]. Select the **Text** group (the vertical stack of text items)
3. Drag two new **Frame** elements **above** the Title, set to `flex-row gap 6px`, fill each with a small rounded Frame containing a Text:
   - Pill 1 → Text bound to `Industry` CMS field
   - Pill 2 → Text bound to `Sub-category` CMS field
   - Styling: 4px/10px padding, 999px radius, bg `rgba(0,0,0,0.08)`, text size 11px, weight 500
4. Under the Title, add a **single-line Text** with three segments separated by middle dots (`·`). Bind to `Brand`, `Location`, `Published Date`. Size 13px, color muted.
5. Below that, add a multi-line **Text** bound to `Exec Summary` CMS field. Size 14px, color 70% opacity. In the Text inspector, set **Line Clamp: 3** so it truncates at 3 lines.
6. Below that, a row of 3 **Stat Cards**:
   - Each is a Frame with two stacked Texts: big number (20px bold) + small label (11px muted)
   - Bind each Text to `Stat 1 / Stat 1 Label / Stat 2 / Stat 2 Label / Stat 3 / Stat 3 Label` CMS fields (these need to be added to Notion — see §9)
7. At the bottom, add a Text "Read report →" with arrow icon. Size 14px, color `var(--brand-primary)`.
8. Select the whole **Report** frame (outermost card). In the right inspector, **Link → Page or URL**, pick the `/reports/{slug}` detail page from the Framer dropdown. (Framer CMS lets you bind the link to the current item's detail page.)

### 6b · Detail page (/reports/{slug})

This is a new page you need to create (or might already exist — Framer usually auto-creates a "Detail Page" template for any CMS collection).

Navigate: **Pages** tab (top left) → look for something like `/reports/:slug` or a page with the CMS icon. If none exists, right-click Reports collection → **Create Detail Page**.

**Target layout:**
```
┌────────────────────────────────────────┐
│  ← Back to all reports                 │
│                                        │
│  [F&B] [Bakeries] [London]             │
│  GAIL's Signal Report                  │
│  GAIL's Bakery · Published Apr 15, 2026│
│                                        │
│  [ cover image — hero, 1200×600 ]      │
│                                        │
│  ┌──────┬──────┬──────┐                │
│  │ 1.2M │ +47% │  12  │  ← stats ribbon│
│  │reach │growth│creatr│                │
│  └──────┴──────┴──────┘                │
│                                        │
│  What's in this report                 │
│  ──────────────                        │
│  Lorem ipsum exec summary, 2–3 paras,  │
│  bound to `Exec Summary` CMS field.    │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │   Read the full report →          │  ← HUGE CTA
│  │                                   │     links to Full Report URL
│  └──────────────────────────────────┘  │
│                                        │
│  [ Book a strategy call today ... ]    │  ← existing CTA section
│                                        │
└────────────────────────────────────────┘
```

Critical: the "Read the full report →" button must be **linked to the `Full Report URL` CMS field**, not any Framer slug. In Framer, select the button → Link → **Use CMS field** → pick `Full Report URL`.

---

## 7 · Dev message — wildcard proxy (REVISED architecture)

**New plan:** Framer only owns the `/reports` grid. The detail pages (the full
report HTML with charts, narrative, stats) live on our Vercel project and need
to be proxied directly from sup.co — skipping Framer. Simpler, faster, and
covers look right out of the box.

Paste this to your dev:

> Hey — I need two proxy rules for `sup.co/reports*`, similar to `/blog/*`:
>
> 1. `sup.co/reports` (exactly) → `various-designer-693318.framer.app/reports`
>    (this is our Framer-hosted grid of report cards)
>
> 2. `sup.co/reports/{slug}` (any sub-path) → `sup-reports.vercel.app/reports/{slug}`
>    (these are static HTML reports we publish via GitHub → Vercel — covers,
>    charts, full analysis. The slug is arbitrary and will grow weekly.)
>
> So the **exact match** goes to Framer, the **wildcard** goes to Vercel.
> Let me know if you need anything — this is unblocking weekly report launches.

Why this is better than routing both through Framer: Framer's auto-generated
CMS detail page can't render our full HTML reports (charts, custom animations,
multi-column layouts). The Vercel-hosted HTML is the canonical report. Framer
stays on what it does best (the index grid).

---

## 8 · 🐛 Slug mismatch — found today

When I opened GAIL's CMS item in Framer, its slug is `gail-s-signal-report` (Framer auto-slugifies from Title and treats the apostrophe as a separator). But in our Vercel repo the folder is `reports/gails/`.

This matters because:

- **Framer URL** (detail page) = `/reports/gail-s-signal-report` ← what users land on from the index
- **Vercel URL** (full report) = `/reports/gails` ← what the CTA button goes to

These don't need to match! The Framer detail page just needs to link to the Vercel URL via the `Full Report URL` field, which we already populate in Notion. As long as §6b step "Read the full report →" is bound to `Full Report URL`, not to Framer's slug, we're fine.

**Action:** when you implement §6b, make sure the big CTA button uses the `Full Report URL` CMS binding, not Framer's auto-slug.

Optional future fix: add a custom `slug` field in the Notion DB that overrides Framer's auto-slugifier, so the Framer URL stays short and matches the Vercel slug. Not blocking.

---

## 9 · Notion schema — already complete ✓

Schema audit done 2026-04-15. **All required fields exist** in the Reports DB:

| Field | Type | GAIL's value (already populated) |
|---|---|---|
| Title | Title | GAIL's Signal Report |
| Brand | Text | GAIL's Bakery |
| Industry | Select | F&B |
| Sub-category | Select | Bakeries |
| Location | Select | London |
| Tags | Multi-select | Influencer, Brand Health, Content Strategy |
| Tags Text | Text (shadow for Framer) | "Influencer, Brand Health, Content Strategy" |
| Status | Select | Published |
| Slug | Text | gails |
| Full Report URL | URL | https://sup-reports.vercel.app/reports/gails |
| Published Date | Date | 2026-04-15 |
| Executive Summary | Text | (200-word summary, populated) |
| Stat 1 Number | Text | 1.7M |
| Stat 1 Label | Text | impressions across 318 posts |
| Stat 2 Number | Text | 55% |
| Stat 2 Label | Text | share of voice in London bakery category |
| Stat 3 Number | Text | 40 |
| Stat 3 Label | Text | creators activated organically |
| Cover Image | URL | ⚠️ **empty** — paste an image URL |
| Brand Logo | URL | ⚠️ **empty** — paste the GAIL's logo URL |

**Action:** add Cover Image + Brand Logo URLs to the GAIL's row. Anything else gets a placeholder in Framer.

Note on §6 binding: when you bind stat fields in Framer, the field names are `Stat 1 Number` / `Stat 1 Label` (not `Stat 1` like I wrote earlier). Same pattern for 2 and 3.

---

## 10 · What I'd do next, in order

1. **You:** 30-sec Vercel GitHub App install (§5)
2. **You:** add the 7 new Notion fields (§9) — or say the word and I'll do it
3. **You:** do the Framer card + detail page design (§6). ~10 min if you're comfortable in Framer
4. **You:** send the dev the `/reports/*` proxy message (§7)
5. **Me:** build the `/publish-report` Claude Code skill once design is stable. It'll: parse HTML → slugify → copy to `reports/{slug}/` → commit + push → create Notion row → done in one command
6. Publish a second report to validate end-to-end through all four systems (Notion → Framer → sup.co → Vercel)

Steps 1 and 4 are unblocking prerequisites — you can do them in the next 2 minutes. Steps 2, 3, 5 run in parallel.
