"""Check that this machine and the .env file are ready to run SeatWise.

Uses only the Python standard library, so it works before setup.bat has
created the virtual environment.

    python scripts/check_env.py            # local checks
    python scripts/check_env.py --network  # also check the package registries
"""
from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECRET_PREFIX = "change-me"
ALLOWED_PORTS = {"API_PORT": 8113, "WEB_PORT": 5113}

results: list[tuple[str, str, str]] = []  # (status, check, detail)


def record(ok: bool | None, check: str, detail: str) -> None:
    status = "OK" if ok else ("WARN" if ok is None else "FAIL")
    results.append((status, check, detail))


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def tool_version(*cmd: str) -> str | None:
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        out = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (out.stdout or out.stderr).strip().splitlines()[0] if out.returncode == 0 else None


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def reachable(url: str) -> tuple[bool, str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "seatwise-check"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:  # the server answered, so it is reachable
        return exc.code < 500, f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return False, str(getattr(exc, "reason", exc))


def check_tools() -> None:
    major, minor = sys.version_info[:2]
    record((major, minor) == (3, 11) or None, "Python", f"{sys.version.split()[0]} ({sys.executable})")
    launcher = tool_version("py", "-3.11", "--version")
    record(launcher is not None, "Python 3.11 launcher", launcher or "py -3.11 not found - install Python 3.11")
    node = tool_version("node", "--version")
    record(node is not None, "Node.js", node or "not found - install the Node.js LTS from nodejs.org")
    npm = tool_version("npm.cmd" if sys.platform == "win32" else "npm", "--version")
    record(npm is not None, "npm", npm or "not found - it is installed together with Node.js")
    git = tool_version("git", "--version")
    record(git is not None or None, "Git", git or "not found (only needed to fetch updates)")
    free_gb = shutil.disk_usage(ROOT).free / 1024**3
    record(free_gb >= 2 or None, "Free disk space", f"{free_gb:.1f} GB (about 1.5 GB is needed)")


def check_env_file() -> dict[str, str]:
    example_path, env_path = ROOT / ".env.example", ROOT / ".env"
    if not env_path.exists():
        record(False, ".env file", "missing - run setup.bat (it copies .env.example to .env)")
        return {}
    env = parse_env(env_path)
    record(True, ".env file", str(env_path))

    missing = sorted(set(parse_env(example_path)) - set(env)) if example_path.exists() else []
    record(not missing, ".env keys", "all keys present" if not missing else f"missing: {', '.join(missing)}")

    secret = env.get("JWT_SECRET", "")
    strong = len(secret) >= 32 and not secret.startswith(DEFAULT_SECRET_PREFIX)
    record(strong, "JWT_SECRET", f"random, {len(secret)} characters" if strong
           else "still the placeholder or too short - run setup.bat to generate one")

    for key, expected in ALLOWED_PORTS.items():
        value = env.get(key, "")
        record(value == str(expected), key, value if value == str(expected)
               else f"{value!r} - SeatWise must use {expected}")

    url = urllib.parse.urlparse(env.get("PUBLIC_BASE_URL", ""))
    record(url.scheme in {"http", "https"} and bool(url.netloc), "PUBLIC_BASE_URL",
           env.get("PUBLIC_BASE_URL", "") or "empty")

    db_url = env.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        db_dir = (ROOT / db_url.removeprefix("sqlite:///")).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        probe = db_dir / ".write-test"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            record(True, "Database folder", f"{db_dir} is writable")
        except OSError as exc:
            record(False, "Database folder", f"{db_dir} is not writable: {exc}")
    else:
        record(False, "DATABASE_URL", f"{db_url!r} - expected sqlite:///data/app.db")
    return env


def check_ports(env: dict[str, str]) -> None:
    for key, default in ALLOWED_PORTS.items():
        port = int(env.get(key) or default)
        free = port_free(port)
        record(free or None, f"Port {port}", "free" if free
               else "in use - fine if SeatWise is already running, otherwise close the program using it")


def check_network() -> None:
    for name, url in (("Python package index", "https://pypi.org/simple/fastapi/"),
                      ("npm registry", "https://registry.npmjs.org/react")):
        ok, detail = reachable(url)
        record(ok, name, detail if ok else f"unreachable ({detail}) - setup.bat needs internet once")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--network", action="store_true", help="also check the package registries")
    args = parser.parse_args()

    check_tools()
    env = check_env_file()
    check_ports(env)
    if args.network:
        check_network()

    width = max(len(check) for _, check, _ in results)
    for status, check, detail in results:
        print(f"[{status:<4}] {check:<{width}}  {detail}")
    failures = sum(status == "FAIL" for status, _, _ in results)
    print("\nAll checks passed." if not failures else f"\n{failures} check(s) failed - see above.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
