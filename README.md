# sup-reports

The **store** for Sup's published signal reports. Each report is a
self-contained HTML page with its own CSS, charts and animations. Deployed to
Vercel on every push to `main`.

This repo is no longer the public address. **Reports are served from
`sup.co/research/…`** and this project sits behind it.

## Live URLs

| | |
|---|---|
| Canonical (what to publish, link and share) | `https://sup.co/research/<kind>/<slug>/<year>/<month>` |
| Cover image | same + `/cover.png` |
| Origin alias (serves the files; do not link) | `https://sup-reports.vercel.app/<kind>/<slug>/<year>/<month>` |
| Legacy host (301s to canonical) | `https://reports.sup.co/<slug>/<year>/<month>` |

`<kind>` is `brands` or `niches`:

- **brands** — a brand-framed audit. One subject company, written in the
  second person, ends in recommendations for them.
- **niches** — a market benchmark. No subject company: a league table of who
  is winning and losing in a category.

## How the routing works (read before editing `vercel.json`)

Reports moved on-domain on 2026-09-08. They used to live at
`reports.sup.co`, which put the most link-worthy content Sup publishes on a
host with no money pages on it — every earned citation built authority for the
subdomain instead of for `sup.co`, which is authority-bound. Only the address
moved; the files still live here.

`sup-site` proxies them with a Next.js rewrite (`next.config.mjs`), so Google
only ever sees the `sup.co` URL. That gives this project **two hosts with two
different jobs**:

- `reports.sup.co` → **301s everything** to the `sup.co` canonical.
- `sup-reports.vercel.app` → **still serves the files**. It is the proxy's
  origin, so it must never redirect.

That is why every redirect in `vercel.json` carries a `has` host condition
pinning it to `reports.sup.co`. **Removing that condition makes the alias
redirect to `sup.co`, which rewrites straight back here — an infinite loop.**

There is deliberately **no `X-Robots-Tag: noindex` on the alias.** Proxied
response headers pass through the rewrite, so a `noindex` here would deindex
the live `sup.co` page. Duplicate content on the alias is handled by the
`<link rel="canonical">` in each report's head instead.

`vercel.json` cannot hold comments — Vercel rejects unknown properties,
including `$comment`, and the deploy fails outright. This section is where
that explanation lives.

## Structure

```
reports/
  brands/<slug>/<year>/<month>/
    index.html      # the report
    cover.html      # reproducible cover source
    cover.png       # 1600×2400 retina cover
    logo.<ext>      # brand logo (not shown on wordmark-hero covers)
  niches/<slug>/<year>/<month>/
    …same shape
vercel.json         # host-scoped redirects + rewrites + cache headers
```

Report HTML contains **zero relative URLs** — every asset reference is
absolute. That is what makes the documents path-portable and let them move
under `/research/…` without a single edit to their markup. Keep it that way.

## Publishing

Use the `sup-audit-5-report-publish` Claude Code skill. It derives every path
and URL from `(kind, brand, year, month)`, renders the cover, injects the SEO
head block, commits, forces a prod deploy and registers the row in Sup Signals
(Convex).

Two things that are easy to get wrong:

1. **Publishing to a URL is not the same as listing it publicly.** A report is
   only public when its entry in `sup-site/lib/reports.ts` has `live: true`;
   that flag gates both the `/research` listing and the sitemap. Everything
   else resolves for anyone with the link but stays unlisted.
2. **Never trust the GitHub→Vercel auto-deploy.** It can be silently canceled.
   Force `vercel deploy --prod --yes` and md5-compare the live `cover.png`
   against the local file before writing URLs anywhere.

Notion and Framer are **out** of this pipeline as of 2026-09-08. Convex is the
only system of record.
