#!/usr/bin/env python3
"""Prospect Intelligence Lab: transparent, rule-based prospect data quality checks."""
from __future__ import annotations
import csv, ipaddress, re, socket, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "prospects.csv"
OUT = ROOT / "reports"
FIELDS = ["company", "niche", "website", "decision_maker", "role", "linkedin_url", "source_url", "observed_signal", "service_fit", "notes"]
USER_AGENT = "ProspectIntelligenceLab/1.0 (public website availability check)"

def valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse((value or "").strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False

def public_hostname(hostname: str) -> bool:
    try:
        addresses = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)]
        except (OSError, ValueError):
            return False
    return bool(addresses) and all(address.is_global and not address.is_multicast for address in addresses)

def check_website(url: str) -> tuple[str, str]:
    url = (url or "").strip()
    if not valid_http_url(url):
        return "not checked: missing/invalid URL", ""
    host = urlparse(url).hostname or ""
    if not public_hostname(host):
        return "not checked: host is not publicly reachable", ""
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        with urlopen(request, timeout=8) as response:
            title = ""
            if "text/html" in response.headers.get("Content-Type", "").lower():
                sample = response.read(200_000).decode("utf-8", errors="replace")
                match = re.search(r"<title[^>]*>(.*?)</title\s*>", sample, re.I | re.S)
                if match:
                    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()
            return f"HTTP {response.status}", title[:180]
    except HTTPError as exc:
        return f"HTTP {exc.code}", ""
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return f"unreachable: {str(getattr(exc, 'reason', exc))[:120]}", ""

def score(row: dict[str, str], website_status: str) -> tuple[int, list[str]]:
    checks = [
        ("website URL", bool(row.get("website", "").strip()), 20),
        ("website responds", website_status.startswith(("HTTP 2", "HTTP 3")), 20),
        ("decision-maker name", bool(row.get("decision_maker", "").strip()), 15),
        ("decision-maker role", bool(row.get("role", "").strip()), 10),
        ("direct LinkedIn profile URL", valid_http_url(row.get("linkedin_url", "")), 15),
        ("supporting source URL", valid_http_url(row.get("source_url", "")), 10),
        ("specific observed business signal", bool(row.get("observed_signal", "").strip()), 10),
    ]
    return sum(weight for _, passed, weight in checks if passed), [label for label, passed, _ in checks if not passed]

def load_rows() -> list[dict[str, str]]:
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT}")
    with INPUT.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("CSV is missing required columns: " + ", ".join(FIELDS))
        return [{field: (row.get(field) or "").strip() for field in FIELDS} for row in reader if (row.get("company") or "").strip()]

def main() -> int:
    rows = load_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    results = []
    for row in rows:
        status, title = check_website(row["website"])
        points, missing = score(row, status)
        results.append({**row, "website_status": status, "website_title": title, "research_completeness_score": points, "missing_checks": "; ".join(missing), "checked_at_utc": checked_at})
    results.sort(key=lambda item: (-int(item["research_completeness_score"]), item["company"].lower()))
    columns = FIELDS + ["website_status", "website_title", "research_completeness_score", "missing_checks", "checked_at_utc"]
    with (OUT / "prospect-lab-results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    lines = [
        "# Prospect Intelligence Lab Report", "",
        f"- **Generated:** {checked_at}", f"- **Prospects processed:** {len(results)}",
        "- **Scoring:** research completeness only; it does not predict buying intent or guarantee accuracy.",
        "- **Outreach:** this experiment does not send messages or invitations.", ""
    ]
    if not results:
        lines += ["## Ready for your first run", "", "No prospects were processed because data/prospects.csv contains only its header.", "Add prospect rows, commit the CSV, and run the workflow again.", ""]
    else:
        lines += ["## Ranked research checklist", ""]
        for index, item in enumerate(results, 1):
            lines += [
                f"### {index}. {item['company']} — {item['research_completeness_score']}/100",
                f"- **Niche:** {item['niche'] or 'Not supplied'}",
                f"- **Website check:** {item['website_status']}",
                f"- **Page title observed:** {item['website_title'] or 'Not available'}",
                f"- **Decision-maker / role:** {item['decision_maker'] or 'Not supplied'} / {item['role'] or 'Not supplied'}",
                f"- **Service fit supplied by researcher:** {item['service_fit'] or 'Not assessed'}",
                f"- **Observed signal supplied by researcher:** {item['observed_signal'] or 'Not supplied'}",
                f"- **Source URL:** {item['source_url'] or 'Missing'}",
                f"- **Next research actions:** {item['missing_checks'] or 'Completeness checks passed; still manually verify facts.'}", ""
            ]
    lines += [
        "## Important limitations", "",
        "- A reachable website does not prove the business is a good prospect.",
        "- This tool does not verify a person's current employment or LinkedIn identity.",
        "- It does not check ad libraries, reviews, hiring, revenue, or ad spend.",
        "- Website results can vary due to bot blocking, redirects, network failures, or temporary outages.",
        "- Manually verify important facts and cite the original public source before outreach.", ""
    ]
    (OUT / "prospect-lab-report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Processed {len(results)} prospects.")
    print("Wrote reports/prospect-lab-results.csv and reports/prospect-lab-report.md")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
