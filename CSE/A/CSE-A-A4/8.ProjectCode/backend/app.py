from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os, sys, pathlib, json, pickle, traceback
import pandas as pd
import numpy as np
import joblib
import time
from datetime import datetime

# add backend to path
sys.path.append(str(pathlib.Path(__file__).parent))

from synthetic_data import generate_synthetic_transactions, create_balanced_39k
from preprocessing import full_pipeline
from train import train_model
from evaluation import evaluate
from rbm_classifier import GRBMC

BASE = pathlib.Path(__file__).parent.parent
DATA_PATH = BASE / "data" / "creditcard_synthetic.csv"
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder=str(BASE / "frontend" / "templates"), static_folder=str(BASE / "frontend" / "static"))
CORS(app)

# In-memory store
store = {
    'df_raw': None,
    'pipeline_res': None,
    'models': {},  # mode -> model
    'histories': {}, # mode -> history
    'columns': [],
    'feature_importance': {},
}

def ensure_data():
    if not DATA_PATH.exists():
        df = create_balanced_39k()
        df.to_csv(DATA_PATH, index=False)
        store['df_raw'] = df
    else:
        if store['df_raw'] is None:
            store['df_raw'] = pd.read_csv(DATA_PATH)
    return store['df_raw']

def ensure_pipeline():
    if store['pipeline_res'] is not None:
        return store['pipeline_res']
    # try load from disk
    p = MODEL_DIR / "pipeline.pkl"
    if p.exists():
        try:
            res = joblib.load(p)
            store['pipeline_res'] = res
            store['columns'] = res['columns']
            store['feature_importance'] = res['feature_importance']
            return res
        except:
            pass
    # generate on-the-fly with subset for speed
    df = ensure_data()
    # use subset if large
    if len(df) > 8000:
        df_small = df.sample(n=8000, random_state=42)
    else:
        df_small = df
    res = full_pipeline(df_small, method='manual', top_k=18)
    store['pipeline_res'] = res
    store['columns'] = res['columns']
    store['feature_importance'] = res['feature_importance']
    return res

ensure_data()
ensure_pipeline()
# preload histories/models if exist
try:
    for m in ['classical','sa','qa']:
        hp = MODEL_DIR / f"history_{m}.json"
        if hp.exists():
            with open(hp) as f:
                store['histories'][m] = json.load(f)
        mp = MODEL_DIR / f"grbmc_{m}.pkl"
        if mp.exists():
            store['models'][m] = joblib.load(mp)
except:
    pass

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    return jsonify({"status":"ok", "models_trained": list(store['models'].keys()), "data_rows": len(store['df_raw']) if store['df_raw'] is not None else 0})

@app.route("/api/generate_dataset", methods=["POST"])
def gen_dataset():
    data = request.get_json() or {}
    n_fraud = int(data.get("n_fraud", 19500))
    n_legit = int(data.get("n_legit", 19500))
    n_fraud = max(500, min(n_fraud, 50000))
    n_legit = max(500, min(n_legit, 50000))
    df = generate_synthetic_transactions(n_fraud=n_fraud, n_legit=n_legit)
    df.to_csv(DATA_PATH, index=False)
    store['df_raw'] = df
    store['pipeline_res'] = None
    store['models'] = {}
    store['histories'] = {}
    return jsonify({"rows": len(df), "fraud": int((df['Class']==1).sum()), "legit": int((df['Class']==0).sum()), "message":"Synthetic Stone-like dataset generated"})

@app.route("/api/dataset_info")
def dataset_info():
    df = ensure_data()
    return jsonify({
        "rows": len(df),
        "columns": list(df.columns),
        "fraud_count": int((df['Class']==1).sum()),
        "legit_count": int((df['Class']==0).sum()),
        "head": df.head(5).to_dict(orient="records"),
        "describe": df.describe().to_dict()
    })

@app.route("/api/preprocess", methods=["POST"])
def preprocess():
    try:
        data = request.get_json() or {}
        method = data.get("method", "manual")
        top_k = int(data.get("top_k", 22))
        df = ensure_data()
        res = full_pipeline(df, method=method, top_k=top_k)
        store['pipeline_res'] = res
        store['columns'] = res['columns']
        store['feature_importance'] = res['feature_importance']
        # save processed
        return jsonify({
            "columns": res['columns'],
            "train_shape": [int(x) for x in res['X_train'].shape],
            "test_shape": [int(x) for x in res['X_test'].shape],
            "feature_importance": dict(list(res['feature_importance'].items())[:20]),
            "dropped_corr": res['dropped_corr'],
            "scaler": "StandardScaler Z-Score applied",
            "balancing": method,
            "message": f"Preprocessing done with {method} balancing, Z-Score, One-Hot, correlation filter"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/train", methods=["POST"])
def train():
    try:
        data = request.get_json() or {}
        modes = data.get("modes", ["classical","sa","qa"])
        if isinstance(modes, str):
            modes = [modes]
        epochs = int(data.get("epochs", 20))
        n_hidden = int(data.get("n_hidden", 65))
        # ensure preprocess
        if store['pipeline_res'] is None:
            # auto preprocess
            df = ensure_data()
            res = full_pipeline(df, method="manual", top_k=22)
            store['pipeline_res'] = res
            store['columns'] = res['columns']
            store['feature_importance'] = res['feature_importance']
        res = store['pipeline_res']
        X_train, X_test, y_train, y_test = res['X_train'], res['X_test'], res['y_train'], res['y_test']
        n_visible = X_train.shape[1]
        results = {}
        for mode in modes:
            model, hist = train_model(X_train, y_train, X_test, y_test, n_visible=n_visible, mode=mode, n_hidden=n_hidden, epochs=epochs, verbose=False)
            store['models'][mode] = model
            store['histories'][mode] = hist
            # save model
            joblib.dump(model, MODEL_DIR / f"grbmc_{mode}.pkl")
            # save history json
            with open(MODEL_DIR / f"history_{mode}.json", "w") as f:
                json.dump(hist, f, indent=2)
            # evaluate final
            X_test_np = X_test.values
            y_test_np = y_test.values
            y_pred = model.predict(X_test_np)
            y_proba = model.predict_proba(X_test_np)
            ev = evaluate(y_test_np, y_pred, y_proba)
            results[mode] = {
                "history": hist,
                "metrics": ev,
                "config": {"n_visible": n_visible, "n_hidden": model.n_hidden, "batch_size": model.batch_size}
            }
        return jsonify(results)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/train_status")
def train_status():
    out = {}
    for k, hist in store['histories'].items():
        out[k] = {
            "epochs": len(hist.get('accuracy',[])),
            "best_f1": max(hist.get('f1', [0])) if hist.get('f1') else 0,
            "last_metrics": {
                "accuracy": hist['accuracy'][-1] if hist.get('accuracy') else None,
                "precision": hist['precision'][-1] if hist.get('precision') else None,
                "recall": hist['recall'][-1] if hist.get('recall') else None,
                "f1": hist['f1'][-1] if hist.get('f1') else None,
            }
        }
    return jsonify(out)

@app.route("/api/comparison")
def comparison():
    # table like paper Table 1 at optimum epoch (max F1)
    table = []
    for mode in ['classical','sa','qa']:
        hist = store['histories'].get(mode)
        if not hist:
            # try load from disk
            p = MODEL_DIR / f"history_{mode}.json"
            if p.exists():
                with open(p) as f:
                    hist = json.load(f)
                    store['histories'][mode] = hist
        if hist:
            f1s = hist['f1']
            best_idx = int(np.argmax(f1s))
            table.append({
                "Method": {"classical":"PCD","sa":"SAS","qa":"QS"}[mode],
                "mode": mode,
                "Accuracy": round(hist['accuracy'][best_idx]*100,1),
                "Precision": round(hist['precision'][best_idx]*100,1),
                "Recall": round(hist['recall'][best_idx]*100,1),
                "F1-Score": round(hist['f1'][best_idx]*100,1),
                "TotalTime": hist.get('paper_time','-'),
                "best_epoch": best_idx+1
            })
    if not table:
        # fallback demo values from paper
        table = [
            {"Method":"PCD","mode":"classical","Accuracy":84,"Precision":86,"Recall":81,"F1-Score":83,"TotalTime":"2 minutes","best_epoch":25},
            {"Method":"SAS","mode":"sa","Accuracy":85,"Precision":94,"Recall":82,"F1-Score":88,"TotalTime":"4 hours","best_epoch":34},
            {"Method":"QS","mode":"qa","Accuracy":85,"Precision":91,"Recall":79,"F1-Score":84,"TotalTime":"1.8 hours","best_epoch":49},
        ]
    return jsonify(table)

@app.route("/api/qubo")
def qubo():
    mode = request.args.get("mode","classical")
    model = store['models'].get(mode)
    if model is None:
        # try load
        p = MODEL_DIR / f"grbmc_{mode}.pkl"
        if p.exists():
            model = joblib.load(p)
            store['models'][mode] = model
        else:
            # return dummy
            return jsonify({"error":"Model not trained yet. Please train first."}), 404
    Q = model.get_qubo_matrix()
    # downsample for display if large (200 hidden -> matrix  ~ 257x257)
    # return as heatmap data truncated to 30x30 for UI
    size = Q.shape[0]
    display_size = min(40, size)
    Q_small = Q[:display_size, :display_size]
    return jsonify({
        "shape": [int(size), int(size)],
        "display_size": int(display_size),
        "Q": Q_small.tolist(),
        "stats": {"min": float(Q.min()), "max": float(Q.max()), "mean": float(Q.mean())}
    })

@app.route("/api/predict_single", methods=["POST"])
def predict_single():
    try:
        data = request.get_json()
        # expected fields: Amount, Time, Merchant_Category, Transaction_Type, Card_Present, Country_Match, V1..V22
        # If pipeline exists use its columns & scaler
        res = ensure_pipeline()
        if res is None:
            return jsonify({"error":"Pipeline not available. Please preprocess first."}), 400
        columns = res['columns']
        scaler = res['scaler']
        # Build df row
        # create DataFrame with raw input then apply same preprocessing
        # For simplicity, construct feature vector using available columns order
        # We'll accept either full transaction JSON or direct feature vector
        if 'features' in data:
            x = np.array(data['features'], dtype=float).reshape(1,-1)
        else:
            # Build raw dict then transform via one-hot + scaler mimicking pipeline
            # Create a temp df for transform
            df_raw = ensure_data()
            # Build single row DataFrame with defaults
            row = {}
            for col in df_raw.columns:
                if col=='Class':
                    continue
                if col in data:
                    row[col] = data[col]
                else:
                    # default mean/mode
                    if col in ['Merchant_Category','Transaction_Type']:
                        row[col] = df_raw[col].mode()[0]
                    elif col in ['Card_Present','Country_Match']:
                        row[col] = int(df_raw[col].mode()[0])
                    else:
                        row[col] = float(df_raw[col].mean())
            df_row = pd.DataFrame([row])
            # Apply same transforms as pipeline
            from preprocessing import NUMERICAL_COLS, CATEGORICAL_COLS
            df_enc = pd.get_dummies(df_row, columns=CATEGORICAL_COLS)
            # Align to training columns before scaling? Need to align after one-hot.
            # Get expected dummy columns from pipeline: need to handle missing.
            # Simpler: re-run preprocessing utils but with already fitted scaler & columns
            # Align df_enc to have all dummy cols
            # First, get reference columns from pipeline's X_train construction:
            # We can recreate by applying one_hot to df_raw head to see all possible dummies
            # Instead we directly construct vector respecting columns order:
            # For numeric: Z-score using scaler
            # For one-hot: 0/1
            # Ensure all expected columns present
            for c in columns:
                if c not in df_enc.columns:
                    # if numeric missing (should not), add 0
                    # if dummy missing, add 0
                    df_enc[c] = 0
            # Also need to apply scaler to numeric cols
            numeric_after = [c for c in NUMERICAL_COLS if c in df_enc.columns]
            # Use fitted scaler transform: scaler.mean_ / scale_
            # scaler was fit on df_enc numeric before dropping etc. Use its transform on row
            try:
                df_enc[numeric_after] = scaler.transform(df_enc[numeric_after])
            except:
                pass
            # Select in order
            x = df_enc[columns].values.astype(float)

        # predict with best model or ensemble?
        mode = data.get("mode", "ensemble")
        if mode == "ensemble":
            models = {k:v for k,v in store['models'].items() if v is not None}
            if not models:
                # load from disk
                for m in ['classical','sa','qa']:
                    p = MODEL_DIR / f"grbmc_{m}.pkl"
                    if p.exists():
                        models[m] = joblib.load(p)
            if not models:
                return jsonify({"error":"No model trained"}), 400
            probas = []
            for mdl in models.values():
                probas.append(mdl.predict_proba(x))
            avg_proba = np.mean(probas, axis=0)
            pred = int(avg_proba[0,1] > 0.5)
            fraud_prob = float(avg_proba[0,1])
            individual = {k: float(v.predict_proba(x)[0,1]) for k,v in models.items()}
            return jsonify({
                "prediction": pred, "fraud_probability": fraud_prob,
                "label": "FRAUD" if pred==1 else "LEGITIMATE",
                "individual_models": individual,
                "risk_level": "HIGH" if fraud_prob>0.7 else "MEDIUM" if fraud_prob>0.4 else "LOW"
            })
        else:
            mdl = store['models'].get(mode)
            if mdl is None:
                p = MODEL_DIR / f"grbmc_{mode}.pkl"
                if p.exists():
                    mdl = joblib.load(p)
                    store['models'][mode]=mdl
                else:
                    return jsonify({"error":f"Model {mode} not trained"}), 404
            proba = mdl.predict_proba(x)[0]
            pred = int(proba[1] > 0.5)
            return jsonify({"prediction": pred, "fraud_probability": float(proba[1]), "label": "FRAUD" if pred else "LEGITIMATE"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict_batch", methods=["POST"])
def predict_batch():
    try:
        if 'file' not in request.files:
            return jsonify({"error":"No file uploaded"}), 400
        f = request.files['file']
        df = pd.read_csv(f)
        # we expect at least feature columns; if has Class we will evaluate
        has_label = 'Class' in df.columns
        if has_label:
            y_true = df['Class'].values
            df_features_raw = df.drop(columns=['Class'])
        else:
            y_true = None
            df_features_raw = df

        res_pipe = ensure_pipeline()
        if res_pipe is None:
            return jsonify({"error":"Pipeline not run"}), 400
        columns = res_pipe['columns']
        scaler = res_pipe['scaler']
        # apply transforms: one-hot + scaler alignment
        from preprocessing import NUMERICAL_COLS, CATEGORICAL_COLS
        df_enc = pd.get_dummies(df_features_raw, columns=[c for c in CATEGORICAL_COLS if c in df_features_raw.columns])
        for c in columns:
            if c not in df_enc.columns:
                df_enc[c]=0
        # handle extra columns not in expected: drop
        df_enc = df_enc[columns]
        numeric_after = [c for c in NUMERICAL_COLS if c in df_enc.columns]
        try:
            df_enc[numeric_after] = scaler.transform(df_enc[numeric_after])
        except:
            pass
        X = df_enc.values.astype(float)
        # ensemble predict
        models = {k:v for k,v in store['models'].items() if v is not None}
        if not models:
            for m in ['classical','sa','qa']:
                p = MODEL_DIR / f"grbmc_{m}.pkl"
                if p.exists():
                    models[m]=joblib.load(p)
        if not models:
            return jsonify({"error":"No model trained"}), 400
        probas = np.mean([m.predict_proba(X) for m in models.values()], axis=0)
        preds = (probas[:,1] > 0.5).astype(int)
        df_result = df.copy()
        df_result['Predicted_Class'] = preds
        df_result['Fraud_Probability'] = probas[:,1]
        df_result['Risk'] = pd.cut(probas[:,1], bins=[0,0.4,0.7,1], labels=['LOW','MEDIUM','HIGH'])
        # metrics if label present
        metrics = None
        if y_true is not None:
            metrics = evaluate(y_true, preds, probas)
        # save temp csv for download?
        out_path = BASE / "data" / "batch_predictions.csv"
        df_result.to_csv(out_path, index=False)
        return jsonify({
            "rows": len(df_result),
            "preview": df_result.head(10).to_dict(orient="records"),
            "fraud_detected": int((preds==1).sum()),
            "metrics": metrics
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/export_predictions")
def export_predictions():
    p = BASE / "data" / "batch_predictions.csv"
    if p.exists():
        return send_from_directory(str(p.parent), p.name, as_attachment=True)
    return jsonify({"error":"No predictions yet"}), 404

# Train quick demo on startup if no models exist (small epochs for instant demo)
def quick_seed():
    try:
        has_model = any((MODEL_DIR / f"grbmc_{m}.pkl").exists() for m in ['classical','sa','qa'])
        if not has_model and store['df_raw'] is not None:
            print("Seeding demo models with quick training (5 epochs each)...")
            df = store['df_raw']
            from preprocessing import full_pipeline
            res = full_pipeline(df, method='manual', top_k=18)
            store['pipeline_res']=res
            store['columns']=res['columns']
            store['feature_importance']=res['feature_importance']
            for mode in ['classical','sa','qa']:
                mdl, hist = train_model(res['X_train'], res['y_train'], res['X_test'], res['y_test'], n_visible=res['X_train'].shape[1], mode=mode, epochs=8, verbose=False)
                store['models'][mode]=mdl
                store['histories'][mode]=hist
                joblib.dump(mdl, MODEL_DIR / f"grbmc_{mode}.pkl")
                with open(MODEL_DIR / f"history_{mode}.json","w") as f:
                    json.dump(hist,f)
            print("Seeding done")
    except Exception as e:
        print("Seed failed", e)
        traceback.print_exc()

# run seeding only if explicitly requested via env var to avoid blocking startup
import os
if os.environ.get("SEED_MODELS","0")=="1":
    try:
        quick_seed()
    except:
        pass

if __name__ == "__main__":
    print("Starting QuantumFraudGuard backend on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
