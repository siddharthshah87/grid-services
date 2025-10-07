#!/usr/bin/env python3
"""Poll the VEN's /live endpoint and print a brief summary.

Usage:
  ./scripts/ven_http_live.py --base-url https://sim.gridcircuit.link --interval 2

Install: pip install requests

This script is defensive about JSON shapes. It tolerates endpoints that return
strings for status (e.g., "ok") or that flatten fields.
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

            ok = None
            power_kw = None
            shed_kw = None
            event_status = "idle"
            event_id = None

            if isinstance(j, dict):
                status_val = j.get("status")
                if isinstance(status_val, dict):
                    ok = status_val.get("ok")
                elif isinstance(status_val, bool):
                    ok = status_val
                elif isinstance(status_val, str):
                    ok = status_val.strip().lower() in ("ok", "true", "1", "yes")

                met = j.get("metering")
                if isinstance(met, dict):
                    power_kw = met.get("power_kw", met.get("powerKw"))
                    shed_kw = met.get("shedPowerKw", met.get("shed_kw"))
                # fallbacks for flattened responses
                power_kw = power_kw if power_kw is not None else j.get("power_kw", j.get("powerKw"))
                shed_kw = shed_kw if shed_kw is not None else j.get("shed_kw", j.get("shedPowerKw"))

                ev = j.get("activeEvent")
                if isinstance(ev, dict):
                    event_id = ev.get("eventId") or ev.get("id")
                else:
                    # Some responses may provide a flat event id
                    event_id = j.get("eventId") or j.get("event")
                event_status = "active" if event_id else j.get("event_status", "idle")
            else:
                # Non-dict top-level JSON (e.g., "ok"); attempt a sensible summary
                if isinstance(j, bool):
                    ok = j
                elif isinstance(j, str):
                    ok = j.strip().lower() in ("ok", "true", "1", "yes")

            print(json.dumps({
                "ok": ok,
                "power_kw": power_kw,
                "shed_kw": shed_kw,
                "event_status": event_status,
                "event": event_id,
            }))
            time.sleep(max(1, args.interval))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
