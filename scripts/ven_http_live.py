#!/usr/bin/env python3
"""Poll the VEN's /live endpoint and print a brief summary.

Usage:
  ./scripts/ven_http_live.py --base-url https://sim.gridcircuit.link --interval 2

Install: pip install requests
"""
import argparse
import json
import sys
import time

try:
    import requests
except Exception:
    print("Requires requests. Install with: pip install requests", file=sys.stderr)
    raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="Base URL of the VEN (e.g., https://sim.gridcircuit.link)")
    ap.add_argument("--interval", type=int, default=2, help="Poll interval seconds")
    args = ap.parse_args()

    url = args.base_url.rstrip("/") + "/live"
    try:
        while True:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            j = r.json()
            used = j.get("metering", {}).get("power_kw")
            shed = j.get("metering", {}).get("shedPowerKw")
            ev = j.get("activeEvent") or {}
            status = "active" if ev.get("eventId") else "idle"
            print(json.dumps({
                "ok": j.get("status", {}).get("ok"),
                "power_kw": used,
                "shed_kw": shed,
                "event_status": status,
                "event": ev.get("eventId"),
            }))
            time.sleep(max(1, args.interval))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

