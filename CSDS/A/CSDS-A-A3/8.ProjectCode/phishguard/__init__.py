"""PhishGuard - A Dynamic Phishing URL Detection System integrating
machine learning with crowdsourced threat intelligence.

Three-stage design (adopted from the base paper):
    1. URL feature extraction      -> phishguard.features
    2. ML classification           -> phishguard.train / phishguard.detector
    3. Crowdsourced TI refinement  -> phishguard.threat_intel / phishguard.retrain
"""

__version__ = "1.0.0"
