"""Create .env from .env.example when missing, and replace a placeholder JWT secret.

Standard library only; setup.bat runs it. Existing values are never overwritten.
"""
from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    env_path, example_path = ROOT / ".env", ROOT / ".env.example"
    if not env_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example")

    lines = env_path.read_text(encoding="utf-8").splitlines()
    present = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.lstrip().startswith("#")}
    changed = False
    for i, line in enumerate(lines):
        if line.startswith("JWT_SECRET="):
            value = line.split("=", 1)[1].strip()
            if len(value) < 32 or value.startswith("change-me"):
                lines[i] = f"JWT_SECRET={secrets.token_urlsafe(48)}"
                changed = True
                print("Generated a new random JWT_SECRET")

    # Add keys introduced by newer versions of .env.example.
    for line in example_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key not in present:
                lines.append(line if key != "JWT_SECRET" else f"JWT_SECRET={secrets.token_urlsafe(48)}")
                changed = True
                print(f"Added missing setting {key}")

    if changed:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(".env is ready")


if __name__ == "__main__":
    main()
