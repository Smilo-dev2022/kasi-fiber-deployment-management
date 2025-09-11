import json
import os
from app.main import app


def main() -> None:
    spec = app.openapi()
    os.makedirs("artifacts", exist_ok=True)
    path = os.path.join("artifacts", "openapi.json")
    with open(path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

