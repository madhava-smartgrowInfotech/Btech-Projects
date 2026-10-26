"""Looks up bibliographic records in Crossref for the reference list (used once while writing refs.py)."""
import json
import sys
import requests

Q = [
    "Compound facial expressions of emotion Du Tao Martinez",
    "Challenges in representation learning: A report on three machine learning contests Goodfellow",
    "Rapid object detection using a boosted cascade of simple features Viola Jones",
    "Dropout: a simple way to prevent neural networks from overfitting Srivastava",
    "A review on multi-label learning algorithms Zhang Zhou",
    "Deep facial expression recognition: A survey Li Deng",
    "Reliable crowdsourcing and deep locality-preserving learning for expression recognition in the wild",
    "The Extended Cohn-Kanade Dataset (CK+): A complete dataset for action unit and emotion-specified expression",
    "AffectNet: A database for facial expression, valence, and arousal computing in the wild",
    "StarGAN: Unified generative adversarial networks for multi-domain image-to-image translation",
    "GANimation: anatomically-aware facial animation from a single image",
    "Constants across cultures in the face and emotion Ekman Friesen",
    "Generative adversarial nets Goodfellow Pouget-Abadie",
]
for q in Q:
    try:
        r = requests.get("https://api.crossref.org/works", params={"query.bibliographic": q, "rows": 2,
                         "select": "title,author,container-title,volume,issue,page,issued,DOI"}, timeout=30).json()
        print("##", q)
        for it in r["message"]["items"]:
            a = ", ".join(f"{x.get('given', '')} {x.get('family', '')}" for x in it.get("author", [])[:6])
            print("  ", it["title"][0][:90], "|", a, "|", (it.get("container-title") or [""])[0], it.get("volume"), it.get("issue"), it.get("page"), it["issued"]["date-parts"][0][0], it["DOI"])
    except Exception as e:  # noqa: BLE001
        print("ERR", q, e)
