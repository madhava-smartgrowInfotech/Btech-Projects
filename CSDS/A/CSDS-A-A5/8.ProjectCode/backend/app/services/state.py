"""Holds the current pipeline result in memory and runs new ecosystem generations in the background."""
import logging
import os
import pickle
import threading
import time

from ml.pipeline import run_pipeline
from scripts.generate_gst_data import generate

from ..config import BASE_DATASET, MODEL_PATH, WORKSPACE
from ..db import PipelineRun, SessionLocal, now

log = logging.getLogger("taxsentinel")
STATE_FILE = os.path.join(WORKSPACE, "state.pkl")


class Store:
    def __init__(self):
        self.state = None
        self.lock = threading.Lock()
        self.status = dict(running=False, stage="idle", progress=0, message="", run_id=None, error=None)

    # ----- loading -----
    def load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "rb") as f:
                    self.state = pickle.load(f)
                log.info("Loaded pipeline state %s", self.state.get("run_key"))
                return
            except Exception as e:  # stale or incompatible file: rebuild below
                log.warning("Could not load saved state (%s); rebuilding", e)
        train = not os.path.exists(MODEL_PATH)
        state = run_pipeline(BASE_DATASET, model_path=MODEL_PATH, train=train,
                             save_model_to=MODEL_PATH if train else None)
        state.update(run_key="base-seed42", run_id=None, generated_at=time.time(), dataset="data/generated")
        self._save(state)

    def _save(self, state):
        os.makedirs(WORKSPACE, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, STATE_FILE)
        state["_index"] = {t["gstin"]: t["idx"] for t in state["taxpayers"]}
        self.state = state

    def get(self):
        if self.state is not None and "_index" not in self.state:
            self.state["_index"] = {t["gstin"]: t["idx"] for t in self.state["taxpayers"]}
        return self.state

    # ----- new generation -----
    def start_run(self, seed, n_taxpayers, user_id):
        with self.lock:
            if self.status["running"]:
                raise RuntimeError("A generation is already running")
            db = SessionLocal()
            run = PipelineRun(seed=seed, n_taxpayers=n_taxpayers, status="running", user_id=user_id)
            db.add(run)
            db.commit()
            run_id = run.id
            db.close()
            self.status = dict(running=True, stage="generate", progress=1, message="generating ecosystem",
                               run_id=run_id, error=None)
        threading.Thread(target=self._run, args=(run_id, seed, n_taxpayers), daemon=True).start()
        return run_id

    def _progress(self, stage, pct, msg):
        self.status.update(stage=stage, progress=round(pct), message=msg)

    def _run(self, run_id, seed, n_taxpayers):
        db = SessionLocal()
        run = db.get(PipelineRun, run_id)
        try:
            out = os.path.join(WORKSPACE, f"run_{run_id}")
            generate(seed, n_taxpayers, out)
            self._progress("features", 10, "ecosystem generated")
            state = run_pipeline(out, train=True, seed=seed, progress=self._progress,
                                 save_model_to=os.path.join(out, "jepa.pt"))
            state.update(run_key=f"run-{run_id}", run_id=run_id, generated_at=time.time(),
                         dataset=f"data/workspace/run_{run_id}")
            self._save(state)
            run.status, run.stats, run.message = "done", state["stats"], "complete"
            self.status.update(running=False, stage="done", progress=100, message="complete")
        except Exception as e:
            log.exception("Pipeline run failed")
            run.status, run.message = "failed", str(e)
            self.status.update(running=False, stage="failed", error=str(e), message=str(e))
        finally:
            run.finished_at = now()
            db.commit()
            db.close()


store = Store()
