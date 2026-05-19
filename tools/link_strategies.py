"""Wrap every mention of a named influencer-marketing play in an audit report
with a hyperlink to its explainer in the Signals Playbook.

The Signals Playbook lives at:
    https://signals.sup.co/strategies

Every strategy has a stable anchor — S01 … S25. This script walks each audit
report, finds every textual mention of a named play, and wraps it in:
    <a class="sx-link" href="https://signals.sup.co/strategies#sNN">…</a>

Skips matches that are already inside an <a> tag, so re-running the script
is idempotent. Injects a small `.sx-link` CSS rule once per file so the
underline is subtle (dotted) until hover (solid).

Run:
    python3 tools/link_strategies.py             # all reports
    python3 tools/link_strategies.py PATH ...    # specific report file(s)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS = sorted(ROOT.glob("reports/*/*/*/index.html"))

LINK_BASE = "https://signals.sup.co/strategies#"

# Each entry: (regex pattern, anchor slug). Patterns are case-sensitive by
# default — duplicate where case variations exist. List ORDER MATTERS: more
# specific phrasings come first so they wrap before a shorter substring
# could match. Once a phrase is wrapped in <a>, the wrap pass skips it,
# so the shorter substring won't double-link the same span.
STRATEGIES: list[tuple[str, str]] = [
    # Longest / most specific first
    (r"Alt-Handle / Brand-Affiliated Creator Channel", "s04"),
    (r"Creator Collective / Volume Model", "s05"),
    (r"Geo-Clustered Micro-Creators", "s18"),
    (r"Geo-Clustered Micro-Creator", "s18"),
    (r"High-Value Gifting &amp; Seeding", "s07"),
    (r"Long-Term Brand Ambassadors", "s10"),
    (r"Long-Term Brand Ambassador", "s10"),
    (r"Always-On Creator Retainers", "s03"),
    (r"Earned Organic Mentions", "s22"),
    (r"Press &amp; Brand Trips", "s17"),
    (r"UGC for Brand Feed", "s02"),
    (r"UGC for Paid Ads", "s01"),
    (r"Brand Trips", "s17"),
    (r"Brand Trip", "s17"),
    (r"Brand Ambassadors", "s10"),
    (r"Brand Ambassador", "s10"),
    (r"Alt-Handle", "s04"),
    (r"Geo-Cluster", "s18"),
    (r"Earned Organic", "s22"),
    # Lowercase / shorthand narrative phrasings
    (r"always-on retainers", "s03"),
    (r"always-on retainer", "s03"),
    (r"earned-mention engine", "s22"),
    (r"earned-mention pattern", "s22"),
    (r"earned-mentions pattern", "s22"),
    (r"earned organic mentions", "s22"),
    (r"earned organic mention", "s22"),
    (r"earned mention", "s22"),
    (r"creator collective", "s05"),
    (r"geo-clustered micro-creators", "s18"),
    (r"geo-clustered micro-creator", "s18"),
    (r"geo-clustered", "s18"),
    (r"geo-clusters", "s18"),
    (r"geo-cluster", "s18"),
    (r"alt-handle", "s04"),
    (r"brand trips", "s17"),
    (r"brand trip", "s17"),
    (r"press trips", "s17"),
    (r"press trip", "s17"),
    (r"long-term ambassadors", "s10"),
    (r"long-term ambassador", "s10"),
]


# `<a ...>` open and `</a>` close — used to skip matches inside existing links.
A_OPEN = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
A_CLOSE = re.compile(r"</a\s*>", re.IGNORECASE)


def wrap_pattern(html: str, pattern: str, anchor: str) -> tuple[str, int]:
    """Wrap every match of `pattern` in `html` with a link to the anchor.

    Skips matches inside an existing `<a>…</a>` block (so re-running is safe
    and so we don't nest links). Returns (new_html, num_wraps).
    """
    # Word-boundary lookarounds so "alt-handle" doesn't match inside a
    # CSS class name like "alt-handle-card", and "brand trip" doesn't
    # match "brand tripod" etc. We allow apostrophes after for "trip's".
    boundary_pat = re.compile(
        r"(?<![A-Za-z0-9_/-])" + pattern + r"(?![A-Za-z0-9_/-])"
    )

    out: list[str] = []
    pos = 0
    wraps = 0
    while pos < len(html):
        a_match = A_OPEN.search(html, pos)
        # Outside-anchor segment runs from `pos` to start of next <a>
        outside_end = a_match.start() if a_match else len(html)

        # Replace within the outside-anchor segment
        def repl(m: re.Match[str]) -> str:
            nonlocal wraps
            wraps += 1
            return (
                f'<a class="sx-link" href="{LINK_BASE}{anchor}" '
                f'target="_blank" rel="noopener">{m.group(0)}</a>'
            )

        out.append(boundary_pat.sub(repl, html[pos:outside_end]))

        if a_match is None:
            break

        # Find matching </a>; emit the inside-anchor block verbatim.
        close = A_CLOSE.search(html, a_match.end())
        if close is None:
            out.append(html[a_match.start():])
            break
        out.append(html[a_match.start():close.end()])
        pos = close.end()

    return "".join(out), wraps


SX_CSS = """
/* sx-link — subtle dotted underline that signals deep-link to the Signals
   Playbook strategy explainer. Hover lifts to a solid underline + brand colour.
   Injected by tools/link_strategies.py. Safe to leave; the linker is idempotent. */
.sx-link{
  color:inherit;
  text-decoration:underline;
  text-decoration-color:var(--brand-primary,#0F172A);
  text-decoration-style:dotted;
  text-decoration-thickness:1px;
  text-underline-offset:3px;
  transition:color 150ms ease,text-decoration-style 150ms ease;
}
.sx-link:hover{
  color:var(--brand-primary,#0F172A);
  text-decoration-style:solid;
}
"""


def inject_css(html: str) -> tuple[str, bool]:
    """Inject the .sx-link rule into the file's first <style> block once.

    Returns (new_html, injected_now).
    """
    if ".sx-link" in html:
        return html, False
    m = re.search(r"</style>", html, re.IGNORECASE)
    if m is None:
        return html, False
    return html[:m.start()] + SX_CSS + html[m.start():], True


def link_report(path: Path) -> dict:
    """Apply linking + CSS injection in place. Returns a stats dict."""
    html = path.read_text(encoding="utf-8")
    original_len = len(html)

    html, css_injected = inject_css(html)

    total_wraps = 0
    per_anchor: dict[str, int] = {}
    for pattern, anchor in STRATEGIES:
        html, wraps = wrap_pattern(html, pattern, anchor)
        if wraps:
            total_wraps += wraps
            per_anchor[anchor] = per_anchor.get(anchor, 0) + wraps

    if total_wraps == 0 and not css_injected:
        return {"path": str(path), "skipped": True}

    path.write_text(html, encoding="utf-8")

    return {
        "path": str(path),
        "css_injected": css_injected,
        "wraps": total_wraps,
        "per_anchor": dict(sorted(per_anchor.items())),
        "delta_bytes": len(html) - original_len,
    }


def main(argv: list[str]) -> int:
    targets: Iterable[Path]
    if argv:
        targets = [Path(a).expanduser().resolve() for a in argv]
    else:
        targets = DEFAULT_REPORTS

    any_changed = False
    for path in targets:
        if not path.exists():
            print(f"SKIP (missing) {path}")
            continue
        result = link_report(path)
        if result.get("skipped"):
            print(f"SKIP (already linked) {result['path']}")
            continue
        any_changed = True
        slug = Path(result["path"]).parent.parent.parent.name + "/" + Path(result["path"]).parent.parent.name + "/" + Path(result["path"]).parent.name
        print(
            f"OK   {slug}  +{result['wraps']} links across "
            f"{len(result['per_anchor'])} strategies "
            f"({'css injected' if result['css_injected'] else 'css already present'}, "
            f"+{result['delta_bytes']} bytes)"
        )
        for anchor, count in result["per_anchor"].items():
            print(f"       {anchor}: {count}")

    return 0 if any_changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
