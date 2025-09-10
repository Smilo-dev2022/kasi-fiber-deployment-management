#!/usr/bin/env python3
import os
import sys
import json
from urllib.request import urlopen, Request


def main():
    base = os.environ.get("BASE_URL", "http://localhost:8000")
    url = f"{base.rstrip('/')}/ops/readiness"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to fetch readiness: {exc}")
        sys.exit(2)

    overall = data.get("overall")
    print(json.dumps(data, indent=2))
    if overall == "ok":
        sys.exit(0)
    elif overall == "warn":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

