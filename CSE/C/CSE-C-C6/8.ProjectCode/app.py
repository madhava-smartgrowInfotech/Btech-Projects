"""Fake News Detection — Advanced Streamlit App (PCA + Firefly + MSVM)."""
import os
import sys
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import FakeNewsMSVMPipeline
from src.dataset import load_csv, build_demo_dataset
from src.preprocessing import LABELS, ID2LABEL

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "msvm_model.pkl")

st.set_page_config(page_title="Fake News Detection | PCA + Firefly + MSVM",
                   page_icon="📰", layout="wide")

COLORS = {"REAL": "#16a34a", "PARTIALLY TRUE": "#d97706", "FAKE": "#dc2626"}

st.markdown("""<style>
.big-title{font-size:2.1rem;font-weight:800;margin-bottom:0}
.sub{color:#64748b;margin-top:0}
.card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:16px}
.badge{display:inline-block;padding:4px 14px;border-radius:999px;color:#fff;font-weight:700}
</style>""", unsafe_allow_html=True)

st.markdown('<p class="big-title">📰 Fake News Detection System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">Feature-Based Optimised <b>MSVM</b> Classification &nbsp;|&nbsp; '
            'PCA feature extraction + Firefly feature selection</p>',
            unsafe_allow_html=True)


@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        return FakeNewsMSVMPipeline.load(MODEL_PATH)
    pipe = FakeNewsMSVMPipeline(max_tfidf=4000, n_fireflies=8, n_generations=8)
    texts, y = build_demo_dataset(n_per_class=250)
    pipe.fit(texts, y, verbose=False)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    pipe.save(MODEL_PATH)
    return pipe


pipe = load_model()

tabs = st.tabs(["🔍 Detect", "📦 Batch Check", "📊 Model Analytics", "🧪 Retrain", "ℹ️ About"])

# ---------------- TAB 1 : single detection ----------------
with tabs[0]:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Analyse a news article")
        title = st.text_input("Headline (optional)", "")
        body = st.text_area("Article text", height=200,
                            placeholder="Paste the full news text here...")
        go_btn = st.button("🚀 Detect Fake News", type="primary", use_container_width=True)
    with c2:
        st.subheader("How it works")
        st.markdown('<div class="card">1️⃣ Clean + TF-IDF (1–2 grams) + 25 stylometric signals<br>'
                    '2️⃣ Standardise → <b>PCA</b> (95% variance)<br>'
                    '3️⃣ <b>Firefly algorithm</b> selects PCA components & tunes C, γ<br>'
                    '4️⃣ <b>MSVM</b> (RBF, OvR, balanced weights) → REAL / PARTIALLY TRUE / FAKE</div>',
                    unsafe_allow_html=True)
    if go_btn:
        full = (title + " " + body).strip()
        if len(full.split()) < 5:
            st.warning("Please enter at least a few words of news text.")
        else:
            t0 = time.time()
            ids, proba = pipe.predict([full])
            dt = (time.time() - t0) * 1000
            label = ID2LABEL[int(ids[0])]
            color = COLORS[label]
            st.markdown(f'<span class="badge" style="background:{color};font-size:1.2rem">'
                        f'{label}</span> &nbsp; <small>⏱ {dt:.0f} ms</small>', unsafe_allow_html=True)
            if proba is not None:
                probs = proba[0]
                fig = go.Figure([go.Bar(x=LABELS, y=probs,
                                        marker_color=[COLORS[l] for l in LABELS])])
                fig.update_layout(title="Class probabilities", yaxis_range=[0, 1],
                                  height=320, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.progress(float(np.max(probs)),
                            text=f"Confidence: {np.max(probs)*100:.1f}%")
            # explainability: matched sensational / trust cues
            from src.preprocessing import clean_text, stylometric_features
            toks = clean_text(full).split()
            try:
                vocab = pipe.vectorizer.get_feature_names_out()
                scores = np.asarray(pipe.clf.dual_coef_).sum(axis=0) \
                    if hasattr(pipe.clf, "dual_coef_") else None
            except Exception:
                scores = None
            hit = [w for w in toks if w in
                   {"shocking", "secret", "unbelievable", "miracle", "hoax",
                    "conspiracy", "exposed", "urgent", "breaking", "viral",
                    "click", "banned", "hidden"}][:10]
            trust = [w for w in toks if w in
                     {"official", "confirmed", "verified", "evidence",
                      "report", "data", "expert", "audit"}][:10]
            e1, e2 = st.columns(2)
            with e1:
                st.markdown("⚠️ **Sensational cues:** " + (", ".join(hit) if hit else "none"))
            with e2:
                st.markdown("✅ **Credibility cues:** " + (", ".join(trust) if trust else "none"))
            st.caption("Tip: PARTIALLY TRUE means the text mixes verified facts with "
                       "unverified/exaggerated claims — verify the flagged phrases.")

# ---------------- TAB 2 : batch ----------------
with tabs[1]:
    st.subheader("Batch screening (CSV)")
    st.caption("Upload a CSV with a text column (text/news/content/statement) "
               "and optional label column for accuracy scoring.")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        st.dataframe(df.head(10), use_container_width=True)
        col = st.selectbox("Text column", df.columns.tolist(),
                           index=next((i for i, c in enumerate(df.columns)
                                       if c.lower() in ("text", "news", "content",
                                                        "statement", "article")), 0))
        if st.button("Run batch detection", type="primary"):
            texts = df[col].fillna("").tolist()
            ids, proba = pipe.predict(texts)
            df["predicted"] = [ID2LABEL[int(i)] for i in ids]
            if proba is not None:
                df["confidence"] = proba.max(axis=1).round(3)
            st.success(f"Screened {len(df)} articles")
            st.dataframe(df[[col, "predicted"] +
                             (["confidence"] if "confidence" in df.columns else [])].head(50),
                         use_container_width=True)
            dist = df["predicted"].value_counts()
            fig = px.pie(values=dist.values, names=dist.index,
                         color=dist.index,
                         color_discrete_map=COLORS, title="Batch verdict distribution")
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("⬇ Download results CSV",
                               df.to_csv(index=False).encode(),
                               "fake_news_results.csv", "text/csv")

# ---------------- TAB 3 : analytics ----------------
with tabs[2]:
    st.subheader("Model analytics")
    s = pipe.stats_
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{s.get('accuracy', 0)*100:.2f}%")
    m2.metric("Macro F1", f"{s.get('f1_macro', 0):.4f}")
    m3.metric("Features", f"{s.get('n_total_features', 0)} → {s.get('n_selected', 0)}")
    m4.metric("Train time", f"{s.get('train_time_s', 0):.1f}s")
    st.caption(f"PCA kept {s.get('n_pca')} components "
               f"({s.get('pca_variance', 0)*100:.1f}% variance) → Firefly selected "
               f"{s.get('n_selected')} · C={s.get('best_C'):.3f}, "
               f"γ={s.get('best_gamma'):.5f} · "
               f"Baseline SVM acc={s.get('baseline_accuracy', 0)*100:.2f}% "
               f"(+{ (s.get('accuracy',0)-s.get('baseline_accuracy',0))*100:.2f} pp from optimisation)")
    c1, c2 = st.columns(2)
    with c1:
        cm = np.array(s.get("confusion_matrix", [[0]*3]*3))
        fig = px.imshow(cm, x=LABELS, y=LABELS, text_auto=True,
                        color_continuous_scale="Blues",
                        title="Confusion matrix (test split)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        hist = s.get("firefly_history", [])
        if hist:
            fig2 = px.line(y=hist, markers=True, title="Firefly optimisation curve",
                           labels={"x": "generation", "y": "best CV fitness"})
            st.plotly_chart(fig2, use_container_width=True)
    st.text("Classification report (test split)")
    st.code(s.get("report_str", "n/a"))
    comp = pd.DataFrame([
        {"Model": "Baseline SVM (PCA, no tuning)", "Accuracy": s.get("baseline_accuracy"),
         "Macro-F1": s.get("baseline_f1")},
        {"Model": "Proposed PCA + Firefly + MSVM", "Accuracy": s.get("accuracy"),
         "Macro-F1": s.get("f1_macro")},
    ])
    st.dataframe(comp, use_container_width=True)

# ---------------- TAB 4 : retrain ----------------
with tabs[3]:
    st.subheader("Retrain on your data")
    st.caption("Upload a labelled CSV, or retrain on the built-in demo corpus with "
               "custom Firefly budgets.")
    rcsv = st.file_uploader("Labelled CSV (text + label)", type=["csv"], key="r")
    cc1, cc2, cc3 = st.columns(3)
    ff = cc1.slider("Fireflies", 4, 20, 10)
    gg = cc2.slider("Generations", 3, 30, 12)
    tf = cc3.slider("Max TF-IDF", 1000, 8000, 4000, step=500)
    if st.button("🧠 Retrain model", type="primary"):
        with st.spinner("Training PCA + Firefly + MSVM ..."):
            if rcsv is not None:
                rcsv.seek(0)
                tmp = os.path.join(BASE, "data", "_upload.csv")
                os.makedirs(os.path.dirname(tmp), exist_ok=True)
                with open(tmp, "wb") as f:
                    f.write(rcsv.read())
                texts, y = load_csv(tmp)
            else:
                texts, y = build_demo_dataset(n_per_class=300)
            new_pipe = FakeNewsMSVMPipeline(max_tfidf=tf, n_fireflies=ff,
                                            n_generations=gg)
            new_pipe.fit(texts, y, verbose=False)
            new_pipe.save(MODEL_PATH)
            st.cache_resource.clear()
        st.success(f"Retrained ✔ Accuracy={new_pipe.stats_['accuracy']*100:.2f}% · "
                   f"F1={new_pipe.stats_['f1_macro']:.4f} · "
                   f"Reload the page to use the new model.")

# ---------------- TAB 5 : about ----------------
with tabs[4]:
    st.subheader("About")
    st.markdown("""
**Fake News Detection System Using Feature-Based Optimised MSVM Classification**

| Item | Detail |
|---|---|
| Pipeline | Text cleaning → TF-IDF + stylometric features → PCA extraction → **Firefly** feature-selection & (C, γ) tuning → **MSVM** (RBF, OvR, balanced class weights) |
| Output classes | **REAL** · **PARTIALLY TRUE** (mix of verified facts with unverified/exaggerated claims) · **FAKE** |
| Keywords | Fake News Detection, MSVM, PCA, Firefly Algorithm, Feature Optimisation, Misinformation Filtering |
""")
    st.info("Run locally: `pip install -r requirements.txt` → `python train.py` → "
            "`streamlit run app.py`", icon="💡")

st.divider()
st.caption("Fake News Detection System · PCA + Firefly + MSVM")
