# sup-reports

Static hosting for Sup's published signal reports. Each report is a self-contained HTML file with animations, charts, and all assets inlined. Deployed to Vercel on every push to `main`.

## Live

- Library (Framer): https://sup.co/reports
- Full reports (Vercel): https://sup-reports.vercel.app/reports/{slug}

## Structure

```
reports/
  {slug}/
    index.html      # the full animated HTML report
manifest.json       # list of all published reports (source of truth for metadata)
vercel.json         # clean URLs + cache headers
```

## Adding a report

Reports are published via the `/publish-report` Claude Code skill. The skill:

1. Parses metadata from the finished HTML (title, brand, industry, stats, exec summary)
2. Slugifies the brand name (`GAIL's Bakery` → `gails`)
3. Copies the HTML to `reports/{slug}/index.html`
4. Updates `manifest.json` with the new entry
5. Commits + pushes to `main` (triggers Vercel auto-deploy)
6. Writes a new row to the Notion Reports database with the live URL
7. Framer's Notion CMS sync picks up the new row and renders a card on `sup.co/reports`

## Manual publish (fallback)

```bash
# Place the finished HTML file
cp MyBrand_Signal_Report.html ~/sup-reports/reports/my-brand/index.html

# Update manifest.json with the new entry

# Commit + push
cd ~/sup-reports
git add .
git commit -m "Publish: My Brand signal report"
git push

# Vercel auto-deploys within ~30s. URL:
# https://sup-reports.vercel.app/reports/my-brand
```

Then manually create the Notion row and paste the URL into `Full Report URL`.
