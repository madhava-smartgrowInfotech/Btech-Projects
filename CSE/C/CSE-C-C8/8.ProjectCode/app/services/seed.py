"""PeerScope demo reviewer seed data (clearly marked demo identities)."""
from __future__ import annotations

DEMO_REVIEWERS = [
    {"display_name": "Reviewer Alpha", "affiliation": "Northbridge Institute of Computing",
     "expertise_description": "Deep learning for computer vision including convolutional networks, object detection, and image classification with benchmark evaluation.",
     "research_topics": "vision, learning, data", "methods": "cnn, classification, evaluation, dataset",
     "keywords": "computer vision, object detection, image classification, deep learning",
     "publication_titles": "Robust Object Detection at Scale; Efficient Image Classification",
     "current_load": 1, "maximum_load": 5, "is_active": True, "conflict_terms": "northbridge-internal-xyz"},
    {"display_name": "Reviewer Beta", "affiliation": "Harborview Language Lab",
     "expertise_description": "Natural language processing, transformer models, text classification, and retrieval-augmented generation with human evaluation.",
     "research_topics": "language, nlp, retrieval, learning", "methods": "transformer, classification, evaluation, statistical",
     "keywords": "nlp, transformers, text classification, retrieval",
     "publication_titles": "Grounding Language Models with Retrieval; Reliable Text Evaluation",
     "current_load": 2, "maximum_load": 5, "is_active": True, "conflict_terms": "harborview-internal-xyz"},
    {"display_name": "Reviewer Gamma", "affiliation": "Civic Systems Research Group",
     "expertise_description": "Applied machine learning, gradient boosting, experimental design, statistical testing, and reproducibility auditing.",
     "research_topics": "learning, data, systems", "methods": "gradient boosting, cross-validation, statistical, experiment",
     "keywords": "applied ml, experimental design, reproducibility, statistics",
     "publication_titles": "Reproducible Experiments in Applied ML",
     "current_load": 0, "maximum_load": 4, "is_active": True, "conflict_terms": "civic-internal-xyz"},
    {"display_name": "Reviewer Delta", "affiliation": "Westfield Security Lab",
     "expertise_description": "Systems and network security, anomaly detection, graph mining, and large-scale measurement studies.",
     "research_topics": "security, systems, graph, mining", "methods": "clustering, evaluation, dataset, optimization",
     "keywords": "security, anomaly detection, networks, measurement",
     "publication_titles": "Measuring Anomalies in Enterprise Networks",
     "current_load": 4, "maximum_load": 5, "is_active": True, "conflict_terms": "westfield-internal-xyz"},
    {"display_name": "Reviewer Epsilon", "affiliation": "Lakeside Medical Informatics Unit",
     "expertise_description": "Medical data analysis, Bayesian methods, clinical evaluation protocols, and responsible AI assessment.",
     "research_topics": "medical, data, learning", "methods": "bayesian, validation, statistical, experiment",
     "keywords": "medical informatics, bayesian methods, clinical evaluation",
     "publication_titles": "Evaluating Predictive Models for Clinical Data",
     "current_load": 1, "maximum_load": 3, "is_active": False, "conflict_terms": "lakeside-internal-xyz"},
    {"display_name": "Reviewer Zeta", "affiliation": "Open Robotics Collective",
     "expertise_description": "Robotics perception, optimization, reinforcement-style control evaluation, and software systems for autonomy.",
     "research_topics": "robotics, systems, learning", "methods": "optimization, evaluation, neural, training",
     "keywords": "robotics, perception, control, autonomy",
     "publication_titles": "Reliable Perception for Mobile Robots",
     "current_load": 0, "maximum_load": 5, "is_active": True, "conflict_terms": "robotics-internal-xyz"},
]


def seed_if_empty(db) -> int:
    from app.models import Reviewer

    if db.query(Reviewer).count() > 0:
        return 0
    for d in DEMO_REVIEWERS:
        db.add(Reviewer(**d))
    db.commit()
    return len(DEMO_REVIEWERS)
