"""ER diagram (09): the four tables of backend/app/db/models.py plus the ciphertext objects the files table points to."""

from matplotlib.patches import Rectangle

from .dgm_lib import GREY, INK, NAVY, ORANGE, PALE_ORANGE, PALE_TEAL, PURPLE, TEAL, W, box, canvas, out, pline, save_min as save, txt

ROW = 2.75


def _table(ax, x, y_top, w, name, cols, hdr=NAVY):
    """cols: [(name, type, key)] -> returns dict col name -> y centre and the table rectangle."""
    h_head = 4.4
    h = h_head + ROW * len(cols) + 0.8
    ax.add_patch(Rectangle((x, y_top - h), w, h, fc="white", ec=NAVY, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, y_top - h_head), w, h_head, fc=hdr, ec=NAVY, lw=1.4, zorder=3))
    ax.text(x + w / 2, y_top - h_head / 2, name, ha="center", va="center", color="white", fontsize=10, fontweight="bold", zorder=4)
    ys = {}
    for i, (cn, ct, key) in enumerate(cols):
        y = y_top - h_head - ROW * (i + 0.5) - 0.4
        ys[cn] = y
        if key:
            ax.text(x + 0.8, y, key, ha="left", va="center", fontsize=8, color=ORANGE if key == "PK" else PURPLE, fontweight="bold", zorder=4)
        ax.text(x + 4.4, y, cn, ha="left", va="center", fontsize=8.2, color=INK, zorder=4, family="DejaVu Sans Mono")
        ax.text(x + w - 0.8, y, ct, ha="right", va="center", fontsize=7.8, color=GREY, zorder=4)
        if i:
            ax.plot([x, x + w], [y + ROW / 2, y + ROW / 2], color="#DDE3EC", lw=0.7, zorder=3)
    return ys, (x, y_top - h, w, h)


def d_er():
    HI = 9.0
    fig, ax = canvas(W, HI, 100)          # height 76.4
    H_ = 100 * HI / W
    top = H_ - 5.0
    uy, ub = _table(ax, 1, top, 30, "users", [
        ("id", "INTEGER", "PK"), ("name", "VARCHAR(120)", ""), ("email", "VARCHAR(255)", "UQ"), ("password_hash", "VARCHAR(255)", ""), ("role", "VARCHAR(20)", ""),
        ("public_key", "TEXT", ""), ("encrypted_private_key", "TEXT", ""), ("private_key_salt", "VARCHAR(64)", ""), ("is_active", "BOOLEAN", ""),
        ("created_at", "DATETIME", ""), ("updated_at", "DATETIME", "")])
    fy, fb = _table(ax, 38, top, 31, "files", [
        ("id", "INTEGER", "PK"), ("owner_id", "INTEGER", "FK"), ("original_filename", "VARCHAR(512)", ""), ("stored_filename", "VARCHAR(128)", "UQ"),
        ("mime_type", "VARCHAR(255)", ""), ("encrypted_size", "INTEGER", ""), ("original_size", "INTEGER", ""), ("iv", "VARCHAR(64)", ""),
        ("owner_wrapped_fek", "TEXT", ""), ("plaintext_sha256", "VARCHAR(64)", ""), ("created_at", "DATETIME", ""), ("updated_at", "DATETIME", "")])
    py, pb = _table(ax, 75, top, 24, "file_permissions", [
        ("id", "INTEGER", "PK"), ("file_id", "INTEGER", "FK"), ("user_id", "INTEGER", "FK"), ("role", "VARCHAR(20)", ""), ("wrapped_fek", "TEXT", ""),
        ("created_at", "DATETIME", ""), ("updated_at", "DATETIME", "")], hdr=NAVY)
    ay, ab = _table(ax, 1, ub[1] - 4.5, 30, "audit_logs", [
        ("id", "INTEGER", "PK"), ("timestamp_utc", "DATETIME", ""), ("user_id", "INTEGER, NULL", "FK"), ("file_id", "INTEGER, NULL", "FK"),
        ("action", "VARCHAR(64)", ""), ("success", "BOOLEAN", ""), ("ip_address", "VARCHAR(64)", ""), ("details", "TEXT", ""),
        ("previous_hash", "VARCHAR(64)", ""), ("current_hash", "VARCHAR(64)", "")], hdr=TEAL)
    # relationships (labels: 1 at the parent, 0..* at the child)
    ax.plot([31, 38], [uy["id"], fy["owner_id"]], color=ORANGE, lw=1.6, zorder=3)
    txt(ax, 32.2, uy["id"] + 1.6, "1", 9.5, ORANGE, bold=True)
    txt(ax, 36.6, fy["owner_id"] + 1.6, "0..*", 8.5, ORANGE, bold=True)
    txt(ax, 34.5, (uy["id"] + fy["owner_id"]) / 2 - 2.6, "owns", 8, GREY)
    ax.plot([69, 75], [fy["id"], py["file_id"]], color=ORANGE, lw=1.6, zorder=3)
    txt(ax, 70.2, fy["id"] + 1.6, "1", 9.5, ORANGE, bold=True)
    txt(ax, 73.7, py["file_id"] + 1.6, "0..*", 8.5, ORANGE, bold=True)
    txt(ax, 72, (fy["id"] + py["file_id"]) / 2 - 2.6, "shared as", 8, GREY)
    pline(ax, [(15, top + 0.1), (15, top + 3.3), (92, top + 3.3), (92, top + 0.1)], color=ORANGE, head=False,
          label="users 1 - 0..* file_permissions  (user_id)  - recipient of a wrapped key", lpos=(54, top + 3.3))
    # users -> audit_logs
    ax.plot([8, 8], [ub[1], ay["id"] + 2.4], color=TEAL, lw=1.6, zorder=3)
    ax.plot([8, 8], [ub[1], ub[1]], color=TEAL)
    txt(ax, 9.2, ub[1] - 1.2, "1", 9, TEAL, bold=True, ha="left")
    txt(ax, 9.2, ab[1] + ab[3] + 1.2, "0..*", 8.5, TEAL, bold=True, ha="left")
    txt(ax, 24, ub[1] - 2.2, "user_id may be NULL", 8, GREY)
    # files -> audit_logs
    pline(ax, [(38, fy["id"] - 14), (34.5, fy["id"] - 14), (34.5, ay["file_id"]), (31, ay["file_id"])], color=TEAL, head=False)
    txt(ax, 36.8, fy["id"] - 17.2, "1", 9, TEAL, bold=True)
    txt(ax, 33.0, ay["file_id"] + 1.8, "0..*", 8.5, TEAL, bold=True, ha="center")
    # ciphertext objects
    box(ax, 53.5, 21, 31, 6.2, "storage/encrypted/<stored_filename>\nAES-GCM ciphertext object, unlinked on delete", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8, r=0.6)
    pline(ax, [(53.5, 24.2), (53.5, fb[1] - 0.1)], color=TEAL, head=True)
    txt(ax, 55, 28.6, "stored_filename", 8, TEAL, ha="left", style="italic")
    box(ax, 87, 30, 24, 15.2, "unique(file_id, user_id):\none permission per user\nand file. Revoke deletes\nthe row, so the wrapped\nFEK copy is gone.", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.6)
    box(ax, 62, 8.0, 56, 11.4, "Indexes: users.email (unique); files(owner_id, created_at), files.stored_filename (unique);\nfile_permissions.file_id, .user_id; audit_logs.timestamp_utc, .user_id, .file_id, .action,\n(file_id, timestamp_utc). Chain fields previous_hash / current_hash are plain columns:\nnothing in the database itself enforces the hash chain.", fc="#F6F8FB", tc=INK, ec="#B7C3D3", fs=8, r=0.6)
    ax.set_ylim(0, H_)
    save(fig, out("09_er_diagram.png"))


DRAWERS = {"er": d_er}
