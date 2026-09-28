import asyncio
import html
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Report, User, get_db
from ..services import attacks, cipher as C, metrics
from .common import key_or_new, load_input

router = APIRouter(prefix="/api", tags=["lab"])


@router.post("/lab/analyze")
async def analyze(file: Optional[UploadFile] = File(None), sample_kind: str = Form(""), sample_name: str = Form(""),
                  job_id: Optional[int] = Form(None), key: str = Form(""),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    img, name, source, resized = await load_input(db, user, file, sample_kind, sample_name, job_id)
    key = key_or_new(key)
    nonce = C.new_nonce()
    data = await asyncio.to_thread(metrics.analyze, img, key, nonce)
    data.update({"image_name": name, "source": source, "nonce": nonce, "key_fp": C.key_fingerprint(key),
                 "resized": resized})
    rep = Report(user_id=user.id, image_name=name, kind="security", data_json=json.dumps(data))
    db.add(rep)
    db.commit()
    return {"id": rep.id, "created_at": rep.created_at.isoformat(), **data}


@router.post("/attacks/run")
async def run_attacks(file: Optional[UploadFile] = File(None), sample_kind: str = Form(""), sample_name: str = Form(""),
                      job_id: Optional[int] = Form(None), key: str = Form(""), report_id: Optional[int] = Form(None),
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    img, name, source, resized = await load_input(db, user, file, sample_kind, sample_name, job_id)
    key = key_or_new(key)
    out = await asyncio.to_thread(attacks.run, img, key, C.new_nonce())
    out["image_name"] = name
    if report_id:  # attach the numbers (not the previews) to an existing security report
        rep = db.get(Report, report_id)
        if rep and rep.user_id == user.id:
            d = rep.data
            d["attacks"] = [{k: v for k, v in r.items() if not k.endswith("preview")} for r in out["results"]]
            rep.data_json = json.dumps(d)
            db.commit()
    return out


@router.get("/lab/reports")
def reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Report).filter(Report.user_id == user.id).order_by(Report.id.desc()).limit(50).all()
    out = []
    for r in rows:
        d = r.data
        out.append({"id": r.id, "image_name": r.image_name, "created_at": r.created_at.isoformat(),
                    "entropy": d["entropy"]["cipher"]["mean"], "npcr": d["differential"]["npcr"],
                    "uaci": d["differential"]["uaci"], "has_attacks": "attacks" in d})
    return out


def _get(db, user, rid) -> Report:
    r = db.get(Report, rid)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Report not found")
    return r


@router.get("/lab/reports/{rid}")
def report(rid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = _get(db, user, rid)
    return {"id": r.id, "created_at": r.created_at.isoformat(), **r.data}


@router.get("/lab/reports/{rid}/export")
def export(rid: int, fmt: str = "html", user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = _get(db, user, rid)
    d = r.data
    if fmt == "json":
        d = {k: v for k, v in d.items() if k != "thumbs"}
        return JSONResponse(d, headers={"Content-Disposition": f'attachment; filename="skycipher_report_{rid}.json"'})
    return HTMLResponse(render_html(r.id, r.created_at.isoformat(), d),
                        headers={"Content-Disposition": f'attachment; filename="skycipher_report_{rid}.html"'})


def _f(v, n=4):
    if v == "inf":
        return "&infin;"
    return f"{v:.{n}f}" if isinstance(v, (int, float)) else html.escape(str(v))


def render_html(rid, created, d) -> str:
    img = d["image"]
    ent, chi, cor = d["entropy"], d["chi_square"], d["correlation"]
    dif, q, ks = d["differential"], d["quality"], d["key_sensitivity"]
    rows = [
        ("Entropy (cipher, ideal 8)", _f(ent["cipher"]["mean"]), _f(ent["plain"]["mean"])),
        ("Chi-square (cipher, &lt; 293.25 = uniform)", ", ".join(_f(v, 1) for v in chi["cipher"]["per_channel"]),
         ", ".join(_f(v, 0) for v in chi["plain"]["per_channel"])),
        ("Correlation horizontal", _f(cor["cipher"]["horizontal"]), _f(cor["plain"]["horizontal"])),
        ("Correlation vertical", _f(cor["cipher"]["vertical"]), _f(cor["plain"]["vertical"])),
        ("Correlation diagonal", _f(cor["cipher"]["diagonal"]), _f(cor["plain"]["diagonal"])),
    ]
    table = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    keyrows = "".join(
        f"<tr><td>bit {t['bit']}</td><td>{_f(t['cipher_diff']['npcr'])}%</td><td>{_f(t['cipher_diff']['uaci'])}%</td>"
        f"<td>{_f(t['wrong_key_decrypt']['psnr'], 2)} dB</td></tr>" for t in ks["tests"])
    att = ""
    if d.get("attacks"):
        att = "<h2>Attack tests (cipher image damaged, then decrypted)</h2><table><tr><th>Attack</th><th>Recovered PSNR</th>" \
              "<th>SSIM</th><th>Pixels intact</th><th>PSNR after median filter</th></tr>" + "".join(
                  f"<tr><td>{html.escape(a['label'])}</td><td>{_f(a['recovered']['psnr'], 2)} dB</td>"
                  f"<td>{_f(a['recovered']['ssim'], 3)}</td><td>{_f(a['recovered']['intact_pct'], 2)}%</td>"
                  f"<td>{_f(a['median_filtered']['psnr'], 2)} dB</td></tr>" for a in d["attacks"]) + "</table>"
    th = d.get("thumbs", {})
    thumbs = "".join(f"<figure><img src='{th[k]}'/><figcaption>{t}</figcaption></figure>"
                     for k, t in (("plain", "Original"), ("cipher", "Cipher"), ("decrypted", "Decrypted"),
                                  ("wrong_key", "Decrypted with 1-bit-wrong key")) if k in th)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>SkyCipher security report #{rid}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:32px auto;padding:0 16px;color:#0f172a}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}td,th{{border:1px solid #cbd5e1;padding:6px 8px;text-align:left;font-size:14px}}
th{{background:#f1f5f9}}figure{{display:inline-block;margin:6px;text-align:center;font-size:12px}}img{{width:180px;image-rendering:pixelated}}
.ok{{color:#15803d;font-weight:600}}.bad{{color:#b91c1c;font-weight:600}}</style></head><body>
<h1>SkyCipher security report #{rid}</h1>
<p>Image: <b>{html.escape(d['image_name'])}</b> ({img['width']}&times;{img['height']}, {img['channels']} channel(s)) &middot; generated {created[:19].replace('T', ' ')} UTC<br>
Key fingerprint: <code>{d['key_fp']}</code> &middot; nonce <code>{d['nonce']}</code></p>
<div>{thumbs}</div>
<h2>Statistical analysis</h2><table><tr><th>Metric</th><th>Cipher image</th><th>Original image</th></tr>{table}</table>
<h2>Differential attack (1-pixel change)</h2><p>NPCR <b>{_f(dif['npcr'])}%</b> (ideal {dif['ideal_npcr']}%) &middot;
UACI <b>{_f(dif['uaci'])}%</b> (ideal {dif['ideal_uaci']}%)</p>
<h2>Decryption quality</h2><p>Decrypted vs original: MSE {_f(q['decrypted']['mse'])}, PSNR {_f(q['decrypted']['psnr'], 2)} dB,
SSIM {_f(q['decrypted']['ssim'])} &middot; <span class="{'ok' if q['decrypted']['identical'] else 'bad'}">
{'bit-identical (SHA-256 match)' if q['decrypted']['identical'] else 'NOT identical'}</span><br>
Cipher vs original: MSE {_f(q['cipher_vs_plain']['mse'], 1)}, PSNR {_f(q['cipher_vs_plain']['psnr'], 2)} dB, SSIM {_f(q['cipher_vs_plain']['ssim'])}</p>
<h2>Key sensitivity (single-bit key changes)</h2><table><tr><th>Flipped</th><th>Cipher NPCR</th><th>Cipher UACI</th>
<th>Wrong-key decryption PSNR</th></tr>{keyrows}</table>
<p>Key space: 2<sup>{d['key_space']['key_bits']}</sup> (plus a {d['key_space']['nonce_bits']}-bit public nonce per image).</p>
<h2>Timing</h2><p>Key setup (once per key) {_f(d['timing'].get('key_setup_ms', 0), 1)} ms &middot; encryption {_f(d['timing']['encrypt_ms'], 1)} ms &middot; decryption {_f(d['timing']['decrypt_ms'], 1)} ms
&middot; {_f(d['timing']['throughput_mbps'], 2)} MB/s</p>{att}
</body></html>"""
