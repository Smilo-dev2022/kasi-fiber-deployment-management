import importlib
import json
import sys
import pathlib

target = sys.argv[1] if len(sys.argv) > 1 else "app.main:app"
out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "integration/openapi.json")

mod_name, app_attr = target.split(":")
app = getattr(importlib.import_module(mod_name), app_attr)
schema = app.openapi()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(schema, indent=2))
print(f"Wrote {out}")

