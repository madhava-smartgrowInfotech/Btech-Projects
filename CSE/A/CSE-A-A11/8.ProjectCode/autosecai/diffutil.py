"""Pull-request ingestion: unified diffs, before/after versions, GitHub PR URLs, zip repositories, patches."""
from __future__ import annotations

import difflib
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

CODE_EXT = {".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".php", ".java", ".kt", ".go", ".rb", ".cs", ".html", ".vue",
            ".yml", ".yaml", ".json", ".env", ".ini", ".cfg", ".properties", ".toml", ".sh", ".sql", ".css", ".md"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea", ".mypy_cache", ".pytest_cache",
             "site-packages", ".tox", "artifacts"}


@dataclass
class ChangedFile:
    path: str
    status: str = "modified"          # added | modified | deleted | scanned
    added: set = field(default_factory=set)   # new-file line numbers that were added/changed
    n_added: int = 0
    n_removed: int = 0
    hunks: list = field(default_factory=list)  # [(new_start, [text lines])] new-side text
    new_source: str | None = None     # full new file when known
    old_source: str | None = None

    @property
    def language(self):
        return LANG.get(Path(self.path).suffix.lower(), "text")


LANG = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".php": "PHP", ".java": "Java", ".kt": "Kotlin", ".go": "Go", ".rb": "Ruby", ".cs": "C#", ".html": "HTML",
        ".vue": "Vue", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".sh": "Shell", ".sql": "SQL", ".css": "CSS",
        ".md": "Markdown", ".env": "Config", ".ini": "Config", ".cfg": "Config", ".toml": "Config", ".properties": "Config"}

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    cur: ChangedFile | None = None
    hunk = None
    new_ln = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git"):
            m = re.search(r" b/(.+)$", raw)
            cur = ChangedFile(m.group(1).strip() if m else "unknown")
            files.append(cur)
            hunk = None
            continue
        if raw.startswith("--- ") and (cur is None or hunk is None):
            if raw.strip() == "--- /dev/null" and cur:
                cur.status = "added"
            elif cur is None:
                cur = ChangedFile("unknown")
                files.append(cur)
            continue
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if path == "/dev/null":
                if cur:
                    cur.status = "deleted"
            else:
                path = path[2:] if path.startswith("b/") else path
                if cur is None or (cur.hunks and cur.path != path):
                    cur = ChangedFile(path)
                    files.append(cur)
                cur.path = path
            hunk = None
            continue
        m = HUNK.match(raw)
        if m and cur is not None:
            new_ln = int(m.group(3))
            hunk = (new_ln, [])
            cur.hunks.append(hunk)
            continue
        if hunk is None or cur is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            cur.added.add(new_ln)
            cur.n_added += 1
            hunk[1].append(raw[1:])
            new_ln += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            cur.n_removed += 1
        elif raw.startswith("\\"):
            continue
        else:
            hunk[1].append(raw[1:] if raw.startswith(" ") else raw)
            new_ln += 1
    return [f for f in files if f.status != "deleted"]


def diff_from_versions(old: str | None, new: str, path: str) -> ChangedFile:
    old_lines = (old or "").splitlines()
    new_lines = new.splitlines()
    sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    cf = ChangedFile(path, "modified" if old else "added", new_source=new, old_source=old)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            cf.added.update(range(j1 + 1, j2 + 1))
            cf.n_added += j2 - j1
        if tag in ("replace", "delete"):
            cf.n_removed += i2 - i1
    return cf


def full_files_to_changed(files: dict[str, str]) -> list[ChangedFile]:
    out = []
    for p, t in files.items():
        n = len(t.splitlines())
        out.append(ChangedFile(p, "scanned", added=set(range(1, n + 1)), n_added=n, new_source=t))
    return out


def attach_sources(changed: list[ChangedFile], sources: dict[str, str]):
    """If the repo's full files are known (e.g. zip + diff), give each ChangedFile its full text."""
    for cf in changed:
        if cf.path in sources:
            cf.new_source = sources[cf.path]


def files_from_zip(data: bytes, max_files=1500, max_bytes=800_000) -> dict[str, str]:
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        prefix = ""
        tops = {n.split("/", 1)[0] for n in names}
        if len(tops) == 1 and all("/" in n for n in names):
            prefix = tops.pop() + "/"
        for n in names:
            rel = n[len(prefix):] if prefix and n.startswith(prefix) else n
            parts = rel.split("/")
            if any(p in SKIP_DIRS for p in parts) or Path(rel).suffix.lower() not in CODE_EXT and Path(rel).name not in (".env",):
                continue
            info = z.getinfo(n)
            if info.file_size > max_bytes:
                continue
            try:
                out[rel] = z.read(n).decode("utf-8", errors="replace")
            except Exception:
                continue
            if len(out) >= max_files:
                break
    return out


def files_from_dir(root: str, max_files=1500, max_bytes=800_000) -> dict[str, str]:
    base = Path(root)
    out = {}
    for p in base.rglob("*"):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(base).parts):
            continue
        if p.suffix.lower() not in CODE_EXT and p.name != ".env":
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
            out[p.relative_to(base).as_posix()] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(out) >= max_files:
            break
    return out


GH_PR = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
GH_REPO = re.compile(r"github\.com/([^/]+)/([^/#?]+)")


def fetch_github_pr_diff(url: str, token: str | None = None, timeout=20) -> tuple[str, dict]:
    import requests
    m = GH_PR.search(url)
    if not m:
        raise ValueError("Not a GitHub pull request URL (expected https://github.com/<owner>/<repo>/pull/<n>)")
    owner, repo, num = m.groups()
    h = {"User-Agent": "AutoSecAI"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    meta = requests.get(api, headers={**h, "Accept": "application/vnd.github+json"}, timeout=timeout)
    if meta.status_code != 200:
        raise RuntimeError(f"GitHub API returned {meta.status_code}: {meta.json().get('message', meta.text[:120])}")
    j = meta.json()
    d = requests.get(api, headers={**h, "Accept": "application/vnd.github.v3.diff"}, timeout=timeout)
    d.raise_for_status()
    info = dict(title=j.get("title"), author=(j.get("user") or {}).get("login"), head=j["head"]["sha"],
                repo=f"{owner}/{repo}", number=int(num), additions=j.get("additions"), deletions=j.get("deletions"),
                changed_files=j.get("changed_files"), body=(j.get("body") or "")[:600])
    return d.text, info


def fetch_github_repo_zip(url: str, token: str | None = None, timeout=40) -> dict[str, str]:
    import requests
    m = GH_REPO.search(url)
    if not m:
        raise ValueError("Not a GitHub repository URL")
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    h = {"User-Agent": "AutoSecAI"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/zipball", headers=h, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"GitHub returned {r.status_code} while downloading the repository")
    return files_from_zip(r.content)


# ---------------------------------------------------------------- patching
def apply_fixes(source: str, fixes: list[dict]) -> tuple[str, list[dict]]:
    """Apply non-overlapping fixes ({start:(line,col), end:(line,col), text}); returns (new_source, applied)."""
    lines = source.splitlines(keepends=True)
    applied, last_start = [], None
    for fx in sorted(fixes, key=lambda f: f["start"], reverse=True):
        (sl, sc), (el, ec) = fx["start"], fx["end"]
        if last_start is not None and (el, ec) > last_start:
            continue  # overlaps a later fix
        if not (1 <= sl <= len(lines) and 1 <= el <= len(lines)):
            continue
        head = lines[sl - 1].encode("utf-8")[:sc].decode("utf-8", errors="ignore")
        tail = lines[el - 1].encode("utf-8")[ec:].decode("utf-8", errors="ignore")
        lines[sl - 1:el] = [head + fx["text"] + tail]
        last_start = (sl, sc)
        applied.append(fx)
    return "".join(lines), applied


def make_patch(path: str, old: str, new: str, context=3) -> str:
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        f"a/{path}", f"b/{path}", n=context))
