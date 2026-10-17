# FRONTEND PROMPT - Multi-Disease Prediction Using Machine Learning

> Open this folder (`8.ProjectCode`) as its own workspace, start a session and say:
> *"Read FRONTEND_PROMPT.md completely and follow it exactly."*

**Batch:** CSE-A-A3 (CSE-A)  ·  **Project:** Multi-Disease Prediction Using Machine Learning
**Design:** **V3 - Depth Studio**  ·  **Ports:** backend 8303, frontend 5303
**Pre-built kit:** `D:\abstracts\Frontend_Kits\V3`  (19 files, JavaScript (.jsx))

---

## 0. What this job is

The backend works; the frontend does not do it justice. You are **not designing a new look** - the design is
already built and sitting in the kit folder above. Your job is to **copy that kit in, then wire this product's
screens to its own API**, and prove nothing broke.

The current interface is **Streamlit or Flask templates**. Leave that app untouched and working, and build a **new React frontend** in `frontend/`. If the Python code has no HTTP API, add a thin FastAPI layer in `backend/` that imports and exposes the **existing functions** - do not rewrite the logic.


**Three hard boundaries**
- **Do not change backend logic or API contracts.** If the UI needs data that no endpoint returns, add a thin
  additive read-only endpoint and say so in your summary.
- **Do not edit the kit folder** at `D:\abstracts\Frontend_Kits\V3` - it is shared with other projects. Copy out of it, never into it.
- **This project must end up self-contained.** The kit files are **copied into `frontend/src/`**. No imports from
  outside this folder, no shared package, no symlinks. A student must be able to take this one folder and run it.

---

## 1. Step 1 - inventory, then one stop

1. List **every backend endpoint**: method, path, request shape, response shape.
2. List **every feature and screen** the product already has (README, `docs/`, existing UI).
3. Write both lists into `docs/FRONTEND_PLAN.md`, then the screen map you will build - every existing feature must
   appear in it.
4. Confirm the backend starts and the ports in `.env` are 8303 / 5303.

Show a **10-line summary** and **wait for "proceed"**. That is the only stop.

---

## 2. Step 2 - bring in the kit (do this before writing any screen)

1. Copy everything under `D:\abstracts\Frontend_Kits\V3\src\` into this project's `frontend/src/`, keeping the folder paths
   (`components/ui`, `components/motion`, `components/charts`, `components/three`, `lib/`, `styles/`).
2. Copy any config files at the top of the kit folder (Tailwind/PostCSS config) into `frontend/`.
3. Install the kit's dependencies:
   ```
   npm i @react-three/drei @react-three/fiber framer-motion gsap lenis lucide-react react react-dom react-router-dom recharts three
   ```
4. This kit is plain JavaScript (`.jsx`), so it drops into a JavaScript Vite project as is.
5. Import the kit's token stylesheet once in your entry file (for example `import './styles/tokens.css'`).
6. Read `D:\abstracts\Frontend_Kits\V3\MANIFEST.md` for the component list, then **open the components themselves** so you know what
   is available before you build screens.

The kit is product-neutral. If a kit component expects something this product does not have, adapt the **copy**
in this project - never the original.

---

## 3. Step 3 - build this product's screens

Use the kit's components for everything: `AppShell`, `Button`, `Card`, `StatCard`, `Table`, `Modal`, `Toast`,
`FileDrop`, `Tabs`, `EmptyState`, `Skeleton`, the chart wrappers, and the motion helpers
(`FadeIn`, `SlideUp`, `Stagger`, `Reveal`, `PageTransition`, `CountUp`, `MagneticButton`).

Build **every screen from your Step 1 map**, wired to the real API, plus a **landing page** using the kit's
landing and motion pieces. The design character is **Depth Studio** - *Cinematic dark with real depth and scroll-driven storytelling (three.js hero).*

**Non-negotiables**
1. Every state designed: skeleton while loading, a real empty state with an action, an error state that says what
   failed and what to do, and visible success feedback.
2. Dark mode works (the kit ships the theme helper) - toggle in the topbar, persisted.
3. `prefers-reduced-motion` respected; anything heavy is lazy-loaded.
4. Responsive from 360px: sidebar becomes a drawer, wide tables scroll or become cards.
5. Keyboard and focus: visible focus rings, Escape closes overlays, inputs labelled.
6. **Real data only** - no lorem ipsum, no invented numbers, no screen that is not wired to the API.

---

## 4. Step 4 - prove it still works

1. `npm run build` succeeds with no errors.
2. Start everything (`run.bat`) and **walk every screen**: trigger each feature, confirm the call reaches the API
   and the response renders. Fix what is broken.
3. Run `scripts/smoke_test.py` if it exists; if not, write a short one covering the main flow.
3b. **Capture screenshots while you are here** - the documentation stage needs them later and the app is
   already running. `pip install playwright` then `playwright install chromium` (the browser downloads once
   per machine, not per project). Write `scripts/capture_screens.py` that logs in, navigates to **every**
   screen, puts real data on it (not an empty dashboard) and saves a 1440x900 PNG per screen to
   `docs/screenshots/<nn>_<screen-name>.png`. Capture the landing page in both light and dark mode. Commit them.
4. Console clean: no errors, no unhandled rejections, no 404s on assets.
5. Check 360px, 768px and 1440px, in light and dark mode.
6. Tick off **every feature from Step 1** in `docs/FRONTEND_PLAN.md` as still working.
7. Update `docs/03_HOW_TO_RUN.md` if anything about running it changed.

Commit from this folder: `git add -A .` then `git commit -m "Rebuild frontend with kit V3" -- .`
(3-5 word messages, no co-author lines, never a bare `git commit`), then `git push`.

---

## 5. Done when

- Every screen in the inventory exists, uses the kit, and is wired to the real API.
- The landing page carries the Depth Studio character.
- Dark mode, reduced-motion, 360px and keyboard access all verified.
- `npm run build` passes, the smoke test passes, the console is clean.
- `frontend/src` contains its own copy of the kit - nothing imported from outside this folder.
- `docs/FRONTEND_PLAN.md` shows every original feature ticked off.

Finish with a short summary: screens built, anything you could not do, defaults you chose.
