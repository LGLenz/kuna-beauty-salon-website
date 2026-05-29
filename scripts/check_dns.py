#!/usr/bin/env python3
"""Compare expected DNS records (dns/records.yaml) against live DNS.

Usage:
  python3 scripts/check_dns.py dns/records.yaml

Exits 0 on full match, 1 on drift, 2 on internal error.
Uses `dig +short` — requires `dnsutils` (apt-get install -y dnsutils).
No secrets, read-only.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. apt-get install -y python3-yaml", file=sys.stderr)
    sys.exit(2)


def dig(name: str, rtype: str) -> list[str]:
    """Return a sorted list of live record values, lowercased."""
    if not shutil.which("dig"):
        print("ERROR: dig not found on PATH", file=sys.stderr)
        sys.exit(2)
    try:
        out = subprocess.run(
            ["dig", "+short", "+time=5", "+tries=2", name, rtype],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return []
    values = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip wrapping quotes from TXT records.
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        values.append(line.lower())
    return sorted(values)


def fqdn(domain: str, name: str) -> str:
    if name == "@":
        return domain
    if name.endswith("."):
        return name.rstrip(".")
    return f"{name}.{domain}"


def normalise_expected(values: list[str]) -> list[str]:
    out = []
    for v in values:
        v = str(v).strip().lower()
        # Strip trailing dot for comparison with dig output (which keeps the
        # trailing dot for CNAME/NS values).
        out.append(v)
    return sorted(out)


def compare(live: list[str], expected: list[str]) -> bool:
    """True if live ⊇ expected (every expected value appears live)."""
    live_set = {v.rstrip(".") for v in live}
    expected_set = {v.rstrip(".") for v in expected}
    return expected_set.issubset(live_set)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_dns.py dns/records.yaml", file=sys.stderr)
        return 2
    spec_path = Path(sys.argv[1])
    if not spec_path.is_file():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        return 2
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    domain = spec["domain"]
    records = spec.get("records", [])

    print(f"DNS check for {domain}")
    print(f"Comparing {len(records)} expected record group(s) against live DNS.")
    print("-" * 60)

    drift = 0
    for rec in records:
        name = rec["name"]
        rtype = rec["type"]
        host = fqdn(domain, name)
        live = dig(host, rtype)

        if "expected" in rec:
            expected = normalise_expected(rec["expected"])
            ok = compare(live, expected)
            status = "OK " if ok else "FAIL"
            print(f"[{status}] {rtype:5s} {host}")
            print(f"        expected: {expected}")
            print(f"        live:     {live}")
            if not ok:
                drift += 1
        elif "expected_contains" in rec:
            substrings = [s.lower() for s in rec["expected_contains"]]
            missing = [s for s in substrings if not any(s in v for v in live)]
            ok = not missing
            status = "OK " if ok else "FAIL"
            print(f"[{status}] {rtype:5s} {host}")
            print(f"        expected_contains: {substrings}")
            print(f"        live:              {live}")
            if missing:
                print(f"        missing substrings: {missing}")
                drift += 1
        else:
            print(f"[SKIP] {rtype} {host} — no 'expected' or 'expected_contains'")

    print("-" * 60)
    if drift:
        print(f"DNS DRIFT: {drift} record group(s) do not match expectations.")
        return 1
    print("DNS OK: all expected records match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
