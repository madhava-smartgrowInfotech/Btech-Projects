"""UML class diagram (06): the four ORM classes of db/models.py and the service / core modules around them."""

from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, PURPLE, TEAL, W, arrow, canvas, out, pline, save_min as save, txt, uml_class


def _mult(ax, x, y, s, ha="center"):
    txt(ax, x, y, s, 8, INK, ha=ha)


def d_uml():
    fig, ax = canvas(W, 8.8, 100)          # height 80
    H_ = 100 * 8.8 / W
    TOP, LH = 70.0, 2.0
    ux, uw = 1.5, 22
    fx, fw = 29.5, 22.5
    px, pw = 58, 20.5
    ax_, aw = 82.5, 16.5
    user = uml_class(ax, ux, TOP, uw, "User", [
        "+id: int  PK", "+name: str(120)", "+email: str(255)  unique", "-password_hash: str(255)", "+role: str = 'user'",
        "+public_key: text?", "+encrypted_private_key: text?", "+private_key_salt: str(64)?", "+is_active: bool",
        "+created_at: datetime", "+updated_at: datetime", "files: FileRecord [*]", "audit_events: AuditLog [*]"], [], hdr=NAVY, lh=LH)
    fr = uml_class(ax, fx, TOP, fw, "FileRecord", [
        "+id: int  PK", "+owner_id: int  FK users", "+original_filename: str(512)", "+stored_filename: str(128)  unique", "+mime_type: str(255)",
        "+encrypted_size: int", "+original_size: int", "+iv: str(64)  (12 bytes, b64)", "+owner_wrapped_fek: text", "+plaintext_sha256: str(64)",
        "+created_at, updated_at", "owner: User", "permissions: FilePermission [*]"], [], hdr=NAVY, lh=LH)
    fp = uml_class(ax, px, TOP, pw, "FilePermission", [
        "+id: int  PK", "+file_id: int  FK files", "+user_id: int  FK users", "+role: 'viewer' | 'editor'", "+wrapped_fek: text",
        "+created_at, updated_at", "file: FileRecord", "unique(file_id, user_id)"], [], hdr=NAVY, lh=LH)
    al = uml_class(ax, ax_, TOP, aw, "AuditLog", [
        "+id: int  PK", "+timestamp_utc: dt", "+user_id: int?  FK", "+file_id: int?  FK", "+action: str(64)", "+success: bool",
        "+ip_address: str(64)?", "+details: text (2000)", "+previous_hash: str(64)", "+current_hash: str(64)", "user: User"], [], hdr=NAVY, lh=LH)
    # ---- row 2: modules
    R2 = 29.0
    sec = uml_class(ax, ux, R2, uw, "core.security", ["bcrypt cost 12", "JWT HS256, 120 min"],
                    ["+hash_password()", "+verify_password()", "+create_access_token()", "+decode_access_token()"], hdr=BLUE, stereotype="module", lh=LH)
    cfg = uml_class(ax, 25.5, R2, 29, "Settings", ["+DATABASE_URL: str  (SQLite default)", "+JWT_SECRET, JWT_ALGORITHM = HS256", "+ACCESS_TOKEN_EXPIRE_MINUTES = 120",
                                                  "+MAX_UPLOAD_MB = 25", "+LOGIN_MAX_ATTEMPTS = 20 / 300 s", "+APP_PORT = 8413"],
                    ["+max_upload_bytes", "+storage_path"], hdr=BLUE, stereotype="pydantic BaseSettings", lh=LH)
    perm = uml_class(ax, 58, R2, 21, "permission_service", ["VALID_SHARE_ROLES"],
                     ["+get_effective_role()", "+can_read(role)", "+can_write(role)", "+can_delete(role)", "+can_share(role)"], hdr=TEAL, stereotype="service", lh=LH)
    aud = uml_class(ax, 81, R2, 18, "audit_service", ["GENESIS"], ["+record_event()", "+verify_chain()", "-_hash_event()"], hdr=TEAL, stereotype="service", lh=LH)
    # ---- associations (top routes)
    ym = TOP - 4.0
    ax.plot([ux + uw, fx], [ym, ym], color=NAVY, lw=1.5, zorder=3)
    _mult(ax, ux + uw + 1.0, ym + 1.4, "1")
    _mult(ax, fx - 1.4, ym + 1.4, "*")
    ax.plot([fx + fw, px], [ym, ym], color=NAVY, lw=1.5, zorder=3)
    _mult(ax, fx + fw + 1.0, ym + 1.4, "1")
    _mult(ax, px - 1.4, ym + 1.4, "*")
    txt(ax, (ux + uw + fx) / 2, ym - 2.4, "owns", 8, GREY)
    txt(ax, (fx + fw + px) / 2, ym - 2.4, "grants", 8, GREY)
    pline(ax, [(13, TOP + 0.2), (13, TOP + 4.2), (77, TOP + 4.2), (77, TOP + 0.2)], color=NAVY, head=False, label="User 1 - * FilePermission  (user_id, ON DELETE CASCADE)", lpos=(40, TOP + 4.2))
    pline(ax, [(6, TOP + 0.2), (6, TOP + 8.2), (91, TOP + 8.2), (91, TOP + 0.2)], color=PURPLE, head=False, label="User 0..1 - * AuditLog  (user_id, ON DELETE SET NULL)", lpos=(48, TOP + 8.2))
    pline(ax, [(44, TOP + 0.2), (44, TOP + 2.1), (86, TOP + 2.1), (86, TOP + 0.2)], color=ORANGE, head=False, label="FileRecord 0..1 - * AuditLog (file_id)", lpos=(63, TOP + 2.1))
    # ---- dependencies (dashed)
    arrow(ax, (12, R2 + 0.2), (12, user[1] - 0.2), color=GREY, ls="--", lw=1.2)
    arrow(ax, (40, R2 + 0.2), (40, fr[1] - 0.2), color=GREY, ls="--", lw=1.2)
    txt(ax, 41.2, (R2 + fr[1]) / 2, "upload limit", 8, GREY, ha="left")
    arrow(ax, (68, R2 + 0.2), (68, fp[1] - 0.2), color=GREY, ls="--", lw=1.2)
    arrow(ax, (59.5, R2 + 0.2), (50, fr[1] - 0.2), color=GREY, ls="--", lw=1.2)
    arrow(ax, (90, R2 + 0.2), (90, al[1] - 0.2), color=GREY, ls="--", lw=1.2)
    ax.set_ylim(0, H_)
    save(fig, out("06_uml_class.png"))


DRAWERS = {"uml": d_uml}
