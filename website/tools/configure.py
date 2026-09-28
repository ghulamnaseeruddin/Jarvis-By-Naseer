#!/usr/bin/env python3
"""
website/tools/configure.py — fills in the placeholders across the website in
one go, so you don't have to hand-edit every HTML file.

Usage:
    python website/tools/configure.py \\
        --repo YOUR-USERNAME/Mark-LIV \\
        --url  https://your-domain.com \\
        --email you@example.com \\
        --owner "Your Name"

Any option you leave out keeps its current value. Safe to re-run any time
(for example after you register a domain, to swap the URL in).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WEBSITE = Path(__file__).resolve().parent.parent
CONFIG_JS = WEBSITE / "assets" / "js" / "config.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def set_js_field(text: str, field: str, value: str) -> str:
    # Matches:  field: "old value",   (also handles nested "assets": { ... } untouched)
    pattern = re.compile(rf'({re.escape(field)}:\s*)"([^"]*)"')
    if not pattern.search(text):
        print(f"  ! could not find '{field}:' in config.js — leaving it untouched", file=sys.stderr)
        return text
    return pattern.sub(lambda m: f'{m.group(1)}"{value}"', text, count=1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help='GitHub repo as "owner/name", e.g. jane-doe/Mark-LIV')
    ap.add_argument("--url", help='Site URL, e.g. https://jarvis.example.com (no trailing slash)')
    ap.add_argument("--email", help="Contact email shown on the site")
    ap.add_argument("--owner", help='Your name or org, e.g. "Jane Doe"')
    ap.add_argument("--form-endpoint", help="Optional: a Formspree-style URL for the contact form")
    args = ap.parse_args()

    if not any([args.repo, args.url, args.email, args.owner, args.form_endpoint]):
        ap.print_help()
        return 0

    if args.repo and not re.match(r"^[\w.-]+/[\w.-]+$", args.repo):
        print(f'--repo should look like "owner/name", got: {args.repo}', file=sys.stderr)
        return 2

    if not CONFIG_JS.exists():
        print(f"Could not find {CONFIG_JS}", file=sys.stderr)
        return 2

    text = read(CONFIG_JS)
    if args.repo:
        text = set_js_field(text, "repo", args.repo)
    if args.url:
        text = set_js_field(text, "url", args.url.rstrip("/"))
    if args.email:
        text = set_js_field(text, "email", args.email)
    if args.owner:
        text = set_js_field(text, "owner", args.owner)
    if args.form_endpoint:
        text = set_js_field(text, "formEndpoint", args.form_endpoint)
    write(CONFIG_JS, text)
    print(f"Updated {CONFIG_JS.relative_to(WEBSITE.parent)}")

    # Canonical / og:url / sitemap / robots also carry the URL as static text
    # (kept static, not read from config.js, so pages work with no JS too).
    if args.url:
        url = args.url.rstrip("/")
        n = 0
        for html in WEBSITE.glob("*.html"):
            t = read(html)
            t2 = re.sub(r"https://example\.com", url, t)
            if t2 != t:
                write(html, t2); n += 1
        for extra in ("sitemap.xml", "robots.txt"):
            p = WEBSITE / extra
            if p.exists():
                t = read(p); t2 = t.replace("https://example.com", url)
                if t2 != t:
                    write(p, t2); n += 1
        print(f"Replaced https://example.com with {url} in {n} file(s)")

    if any([args.repo, args.email, args.owner]):
        print("\nNote: version.py at the project root also has a GITHUB_REPO")
        print("placeholder used by the in-app 'update available' check — update")
        print("that one by hand to match, if you set --repo.")

    print("\nDone. Rebuilding nothing else is required — the site reads config.js at runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
