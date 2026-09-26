"""Real-time URL classification (Objective 6).

Decision order for a submitted URL:
    1. Crowdsourced intelligence - a confirmed community/feed verdict wins
       immediately (this is what catches zero-day URLs the model has never seen).
    2. ML model - the best trained classifier scores the URL.
    3. Pending community reports nudge the ML probability (soft evidence).
"""
from __future__ import annotations

import threading

import joblib
import numpy as np

from . import config
from .features import (FEATURE_NAMES, explain_features, extract_features,
                       features_to_vector, normalize_url)
from .threat_intel import ThreatIntel
from .train import load_metrics


class Detector:
    def __init__(self, ti: ThreatIntel | None = None):
        self.ti = ti or ThreatIntel()
        self._lock = threading.Lock()
        self.model = None
        self.model_name = None
        self.model_version = None
        self.reload()

    # ------------------------------------------------------------------ #
    def reload(self) -> bool:
        """(Re)load the best model from disk; called after every retrain."""
        if not config.BEST_MODEL_FILE.exists():
            return False
        bundle = joblib.load(config.BEST_MODEL_FILE)
        with self._lock:
            self.model = bundle["model"]
            self.model_name = bundle["name"]
            self.model_version = load_metrics().get("model_version")
        return True

    @property
    def ready(self) -> bool:
        return self.model is not None

    # ------------------------------------------------------------------ #
    def ml_probability(self, url: str) -> float:
        feats = extract_features(url)
        X = features_to_vector(feats).reshape(1, -1)
        with self._lock:
            return float(self.model.predict_proba(X)[0, 1])

    def check(self, url: str, log: bool = True) -> dict:
        url_norm = normalize_url(url)
        if not url_norm:
            raise ValueError("Please enter a URL.")
        feats = extract_features(url_norm)
        flags = explain_features(feats)
        result = {
            "url": url.strip(),
            "normalized_url": url_norm,
            "red_flags": flags,
            "features": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in feats.items()},
            "model": self.model_name,
            "model_version": self.model_version,
        }

        # 1. crowdsourced intelligence
        intel = self.ti.lookup(url_norm) or self.ti.lookup_host(url_norm)
        ml_prob = self.ml_probability(url_norm) if self.ready else None
        result["ml_probability"] = None if ml_prob is None else round(ml_prob, 4)
        result["community"] = None
        if intel:
            result["community"] = {
                "status": intel["status"],
                "phishing_votes": intel["phishing_votes"],
                "safe_votes": intel["safe_votes"],
                "source": intel["source"],
                "last_updated": intel["last_updated"],
            }
        if intel and intel["status"] == "confirmed_phishing":
            result.update(verdict="phishing", probability=max(0.97, ml_prob or 0),
                          decided_by="community", reason=(
                              f"Confirmed phishing by crowdsourced threat intelligence "
                              f"({intel['phishing_votes']} phishing vs {intel['safe_votes']} safe "
                              f"reports, source: {intel['source']})."))
        elif intel and intel["status"] == "confirmed_safe":
            result.update(verdict="safe", probability=min(0.03, ml_prob or 0),
                          decided_by="community",
                          reason="Confirmed legitimate by community consensus.")
        elif ml_prob is None:
            result.update(verdict="unknown", probability=None, decided_by="none",
                          reason="No trained model found - run `python run.py train` first.")
        else:
            # 2./3. ML with soft community evidence
            prob = ml_prob
            reputable = feats["is_popular_domain"] and (feats["is_common_tld"] or feats["tld_length"] > 2)
            if reputable:  # domain-reputation adjustment for well-known registered domains
                prob *= 0.4
            if intel:
                net = intel["phishing_votes"] - intel["safe_votes"]
                prob = float(np.clip(prob + 0.15 * net, 0.0, 1.0))
            if prob >= config.PHISHING_THRESHOLD:
                verdict = "phishing"
            elif prob >= config.SUSPICIOUS_THRESHOLD:
                verdict = "suspicious"
            else:
                verdict = "safe"
            reason = (f"{self.model_name.replace('_', ' ').title()} estimates a "
                      f"{prob*100:.1f}% phishing probability from {len(FEATURE_NAMES)} "
                      f"lexical, structural and domain features.")
            if reputable:
                reason += " Reduced because the registered domain is a well-known legitimate site."
            if intel:
                reason += (f" Adjusted by {intel['phishing_votes']} phishing / "
                           f"{intel['safe_votes']} safe pending community reports.")
            result.update(verdict=verdict, probability=round(prob, 4), decided_by="ml",
                          reason=reason)

        if log:
            self.ti.log_check(url_norm, result["verdict"], result["probability"],
                              result["decided_by"])
        return result
