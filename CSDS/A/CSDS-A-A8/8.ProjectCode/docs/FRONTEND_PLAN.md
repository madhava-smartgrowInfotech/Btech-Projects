# BioSight - Frontend rebuild plan (Kit V3 "Depth Studio")

Status: **Rebuilt with kit V3 and verified (see section 5).** Ports: backend 8108, frontend 5108 (verified in `.env`, `run.bat`, `vite.config.js`, CORS in `backend/app/main.py`).

## 1. Backend endpoints (all JSON, `Authorization: Bearer <jwt>` unless noted)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, service}` (public) |
| POST | `/api/auth/register` | `{name, email, password}` (pw >= 6) | `{token, user:{id,name,email}}`; 400 with message |
| POST | `/api/auth/login` | `{email, password}` | `{token, user}`; 401 "Wrong email or password" |
| GET | `/api/auth/me` | - | `{id,name,email}` |
| GET | `/api/mri/models` | - | `[{key,label,available}]` (`jepa_10`, `jepa_100`, `unet_100`) |
| GET | `/api/mri/samples` | - | `[{file,patient,tumour_pixels}]` |
| GET | `/api/mri/samples/{name}` | - | PNG image (public, used in `<img>`) |
| POST | `/api/mri/segment` | multipart: `file`, `model`, `pixel_spacing_mm` (max 10 MB) | segmentation result + `overlay_png`, `mask_png` (data URIs) + `report` + `analysis_id` |
| POST | `/api/mri/segment-sample` | `{name, model, pixel_spacing_mm}` | same, plus `ground_truth:{area_pixels,dice,iou}`, `sample` |
| GET | `/api/dna/samples` | - | `[{name, sequence}]` (6 samples) |
| POST | `/api/dna/classify` | `{sequence, report=true}` | `{sequence:{id,length,gc_percent,counts,reverse_complement_preview,windows_analysed}, repeat_type:{prediction,confidence,probabilities,strongest_window,windows[],model_test_accuracy}, organism_class:{prediction,confidence,probabilities,model_test_accuracy,chance_accuracy,note}, repeat_scan:[{motif,period,start,end,copies}], report, analysis_id}` |
| GET | `/api/str/loci` | - | `{loci[20], alleles{locus:[...]}, database_size, frequency_source}` |
| GET | `/api/str/sample-query` | - | `{profile, note, source_id}` |
| POST | `/api/str/match` | `{profile:{locus:"a/b"}, report=true}` | `{query_loci, database_size, random_match_probability, log10_inverse_rmp, theta, typing_error_rate, candidates_with_positive_support, matches[10]:{id,log10_lr,lr_display,verbal,loci_compared,loci_matched,loci_mismatched,loci[]}, report, analysis_id}` |
| GET | `/api/metrics/label-efficiency` | - | `{data, finetune{method_pct:{dice,iou,...}}, pretrain}`; 404 if no metrics |
| GET | `/api/metrics/all` | - | `{mri, dna, eval}` (each may be `null`) |
| GET | `/api/metrics/plot/{name}` | - | PNG (`mri_label_efficiency.png`, `mri_pretrain_loss.png`, public) |
| GET | `/api/history` | - | last 50 `[{id,kind,title,created_at}]` |
| GET | `/api/history/{id}` | - | `{id,kind,title,summary,report,created_at}` |

Report object (all three analyses): `{source:"gemini"|"fallback", model, errors?, report:{title, summary, findings[], measurements[{name,value}], interpretation, limitations[], recommendation}}`.

## 2. Existing features / screens (README, `docs/01_OVERVIEW.md`, current UI)

| ID | Feature | Where it lives today |
|---|---|---|
| F1 | JEPA pre-training (shown through results/loss plot) | Label efficiency + Performance |
| F2 | Few-label MRI segmentation: upload or sample slice, model + pixel spacing, overlay, area px/mm2, % brain, location, confidence, max extent, Dice/IoU vs expert mask | MRI analysis |
| F3 | Label-efficiency comparison JEPA vs U-Net vs MAE vs scratch (Dice/IoU at 10% / 100%) + runs table + pre-training loss plot | Label efficiency |
| F4 | DNA classification: repeat type, organism class (with low-reliability note), GC, windows, exact tandem-repeat scan | DNA analysis |
| F5 | STR matching: 20-locus query form, sample query, ranked LR table, per-locus comparison | STR matching |
| F6 | Structured Gemini reports (gemini / fallback labelled) on MRI, DNA, STR | Report card on each result |
| - | Auth: sign in, register, demo account button, logout | Login |
| - | Model performance: MRI table + pretrain stats, DNA repeat chart/table/confusion matrix, organism table, STR evaluation, recent analyses | Performance |
| - | Analysis history (API exists; only a 15-row list in Performance) | Performance |
| - | Landing page | Landing |

## 3. Screen map (Depth Studio, kit V3)

| Route | Screen | Kit pieces | API |
|---|---|---|---|
| `/` | Landing: three.js hero, scroll story (JEPA -> segmentation -> DNA/STR -> reports), CTA | `HeroVisual`, `landing.css`, motion helpers, `CountUp` | health (status chip) |
| `/login` | Sign in / register + demo account | `Card`, `Input`, `Button`, `Toast` | auth/login, auth/register |
| `/app/mri` | MRI analysis (F2, F6) | `AppShell`, `FileDrop`, `Select`, sample grid, `StatCard`, report card | mri/models, samples, segment, segment-sample |
| `/app/label-efficiency` | Label efficiency (F1, F3) | chart wrappers, `Tabs` (Dice/IoU), `Table`, plot image | metrics/label-efficiency, plot |
| `/app/dna` | DNA analysis (F4, F6) | textarea, sample chips, probability bars, `Table` | dna/samples, classify |
| `/app/str` | STR matching (F5, F6) | 20-locus grid, `Table`, per-locus rows, `Modal`/inline detail | str/loci, sample-query, match |
| `/app/performance` | Model performance | `StatCard`, charts, `Table` (confusion matrix) | metrics/all |
| `/app/history` | Analysis history + detail drawer (new screen on existing API) | `Table`, `Modal`, report card | history, history/{id} |
| `*` | Not found | `EmptyState` | - |

Shared: topbar theme toggle (persisted), user menu/logout, sidebar -> drawer under 1024px, toasts, skeleton / empty / error / success for every data call.

## 4. Findings that affect the build (reported at the stop)

1. **A frontend already exists** (`frontend/`, Tailwind + axios, 5 pages). The brief says there is none. I will replace it in place with the kit (drop Tailwind/axios, use fetch + the kit's `useAsync`). Old `dist/` is build output.
2. **Trained models and metrics are not in the repo**: `models/` is empty and `experiments/` has no `mri_metrics.json` / `dna_metrics.json` / `eval/metrics.json`. Training logs stop at JEPA epoch 5/10 and DNA epoch 5/15. Consequently: MRI segmentation returns 400 ("model not found"), DNA classify returns 400, `/metrics/label-efficiency` returns 404, `/metrics/all` returns `{null,null,null}`. Only auth, STR matching, sample listing and history work against live data today.
3. The docs say the models are "committed"; they are not, and `scripts/smoke_test.py` expects them, so it cannot pass on this checkout.

## 5. Feature checklist (verified in Chrome via Playwright, 1440 / 768 / 360 px, dark + light)

"Live" = exercised against the real running API. "Fixture" = the backend cannot produce this output on this checkout (trained models / metrics files are missing), so the screen was checked against a test-only mocked response of the documented shape; the real-API failure path (clear error / empty state) was checked too.

- [x] Auth: sign in, register, demo account, logout, redirect to the saved page, expired-session notice - **live**
- [x] F2 MRI: model list (unavailable models disabled + warning), 200 sample slices (paged), upload with preview, pixel spacing validation, overlay / mask tabs, stats, ground-truth Dice/IoU - sample list and models **live**; segmentation result **fixture** (no `mri_seg_*.pt`)
- [x] F3 Label efficiency: stat tiles, Dice/IoU chart + tabs, runs table, loss plot - **fixture**; real API returns 404 -> "No MRI results yet" empty state (**live**)
- [x] F4 DNA: samples, raw/FASTA input, repeat type, organism class + reliability note, tandem scan, base counts - samples **live**; classification result **fixture** (no `dna_*_classifier.pt`); real 400 shown as an error state (**live**)
- [x] F5 STR: 20-locus form, sample query, <3 loci validation, clear, ranked table, row click -> per-locus detail - **live**
- [x] F6 Reports on STR (Gemini) - **live**; MRI / DNA report card - **fixture**
- [x] Model performance: MRI table + pretrain stats, DNA chart / table / confusion matrix, organism table, STR evaluation, recent analyses - **fixture** for metrics (real API returns nulls -> "Not available yet" states, **live**); recent analyses **live**
- [x] History list, kind filter, search, detail drawer with report, Escape closes - **live**
- [x] Landing (three.js helix hero, parallax depth layers, pinned scroll story, marquee, count-up), dark / light toggle persisted, `prefers-reduced-motion`, no horizontal overflow at 360 px, drawer nav on mobile, visible focus rings
- [ ] `scripts/smoke_test.py` - **fails on this checkout** for the pre-existing reason above (MRI models not installed); passes health / auth / history checks
