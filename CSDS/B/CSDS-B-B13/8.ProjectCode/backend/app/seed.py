"""Seed a demo user and the two practice targets on first run."""
import json
from pathlib import Path

from .auth import hash_password
from .config import PROJECT_ROOT, settings
from .db import SessionLocal, Target, User
from .services.spec_parser import parse_spec

TARGETS_DIR = PROJECT_ROOT / "targets"


def _load_target_files(name: str):
    spec_text = (TARGETS_DIR / f"{name}_openapi.json").read_text(encoding="utf-8")
    meta = json.loads((TARGETS_DIR / f"{name}_vulns.json").read_text(encoding="utf-8"))
    base_url, endpoints, _ = parse_spec(spec_text)
    base_url = meta.get("base_url") or base_url
    return base_url, endpoints, meta


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.demo_email).first()
        if not user:
            user = User(email=settings.demo_email,
                        password_hash=hash_password(settings.demo_password))
            db.add(user)
            db.commit()
            db.refresh(user)

        for name, display in (("demopay", "DemoPay"), ("vulnbank", "VulnBank")):
            exists = db.query(Target).filter(
                Target.owner_id == user.id, Target.name == display).first()
            if exists:
                continue
            try:
                base_url, endpoints, meta = _load_target_files(name)
            except FileNotFoundError:
                continue
            db.add(Target(
                owner_id=user.id, name=display, base_url=base_url,
                endpoints_json=json.dumps(endpoints),
                auth_json=json.dumps(meta.get("auth", {})),
                known_vulns_json=json.dumps(meta.get("known_vulns", [])),
            ))
        db.commit()
    finally:
        db.close()
