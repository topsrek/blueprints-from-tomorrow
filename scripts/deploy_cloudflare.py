#!/usr/bin/env python3
"""Deploy the static site to Cloudflare as an assets-only Worker (`cf deploy`).

Stages every tracked or untracked-but-not-ignored file from the working tree
into a temp folder, adds a Cloudflare `_headers` file, and runs
`cf deploy site` from a folder whose cloudflare.config.ts names the Worker and,
for the canonical URL, attaches the custom domain.

Until the real domain is attached, pass --base-url with the workers.dev URL so
every absolute link (llms.txt, SKILL.md, era guides, ...) points at the live
preview and an AI agent can follow the whole link chain.

Auth: `cf auth login` once (or set CLOUDFLARE_API_TOKEN).
Install: `npm install --global cf`.

Usage:
  python scripts/deploy_cloudflare.py                       # canonical domain
  python scripts/deploy_cloudflare.py --base-url https://blueprints-from-tomorrow.<subdomain>.workers.dev
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_URL = "https://blueprintsfromtomorrow.com"
PROJECT = "blueprints-from-tomorrow"
ACCOUNT_ID = "e8fb6164ae3e9c3e973ad03149d83f47"
SKIP = {".gitignore", "requirements.txt"}
TEXT_SUFFIXES = {".md", ".txt", ".html", ".xml", ".yaml", ".yml", ".json", ".svg", ".py"}

CF_CONFIG = """import { defineConfig } from "cf/config";

export default defineConfig({
  accountId: %(account)s,
  worker: {
    name: %(name)s,
    compatibilityDate: "2026-11-19",
    domains: %(domains)s,
  },
});
"""

HEADERS = """\
/*
  Access-Control-Allow-Origin: *
  X-Content-Type-Options: nosniff

/*.md
  Content-Type: text/markdown; charset=utf-8

/llms.txt
  Content-Type: text/plain; charset=utf-8

/robots.txt
  Content-Type: text/plain; charset=utf-8
"""


def site_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout.decode("utf-8")
    return [f for f in out.split("\0") if f and f not in SKIP and (ROOT / f).is_file()]


def stage(dest: Path, base_url: str) -> int:
    count = 0
    for rel in site_files():
        src, dst = ROOT / rel, dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if base_url != CANONICAL_URL and src.suffix in TEXT_SUFFIXES:
            text = src.read_text(encoding="utf-8")
            dst.write_text(text.replace(CANONICAL_URL, base_url), encoding="utf-8", newline="")
        else:
            shutil.copy2(src, dst)
        count += 1
    (dest / "_headers").write_text(HEADERS, encoding="utf-8")
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=CANONICAL_URL, help="absolute URL the site is served at")
    ap.add_argument("--project", default=PROJECT, help="Cloudflare Worker name")
    ap.add_argument("--account-id", default=os.environ.get("CLOUDFLARE_ACCOUNT_ID", ACCOUNT_ID))
    ap.add_argument("--dry-run", action="store_true", help="stage only, print the folder")
    args = ap.parse_args()
    base_url = args.base_url.rstrip("/")

    tmp = Path(tempfile.mkdtemp(prefix="bft-deploy-"))
    (tmp / "package.json").write_text(json.dumps({"name": args.project, "private": True, "type": "module"}), encoding="utf-8")
    # www only needs DNS + a certificate; the zone redirect rule sends it to the apex with a 301.
    host = CANONICAL_URL.split("://", 1)[1]
    domains = [host, f"www.{host}"] if base_url == CANONICAL_URL else []
    (tmp / "cloudflare.config.ts").write_text(CF_CONFIG % {
        "account": json.dumps(args.account_id), "name": json.dumps(args.project), "domains": json.dumps(domains),
    }, encoding="utf-8")
    cf_pkg = Path(shutil.which("cf") or "").resolve().parent / "node_modules" / "cf"
    if cf_pkg.is_dir():  # let cloudflare.config.ts resolve `cf/config` from the global install
        (tmp / "node_modules").mkdir()
        subprocess.run(["cmd", "/c", "mklink", "/J", str(tmp / "node_modules" / "cf"), str(cf_pkg)]
                       if os.name == "nt" else ["ln", "-s", str(cf_pkg), str(tmp / "node_modules" / "cf")],
                       check=True, capture_output=True)
    n = stage(tmp / "site", base_url)
    print(f"Staged {n} files for {base_url} in {tmp / 'site'}")
    cf = shutil.which("cf") or "cf"
    cmd = [cf, "deploy", "site"] + (["--dry-run"] if args.dry_run else [])
    try:
        return subprocess.run(cmd, cwd=tmp).returncode
    finally:
        link = tmp / "node_modules" / "cf"
        if link.exists() or link.is_symlink():
            os.unlink(link) if os.name != "nt" else os.rmdir(link)  # remove the link, not the global package
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
