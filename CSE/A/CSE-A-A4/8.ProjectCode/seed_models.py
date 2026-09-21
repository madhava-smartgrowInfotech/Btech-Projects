import pathlib, sys
sys.path.append(str(pathlib.Path(__file__).parent / "backend"))
from backend.synthetic_data import create_balanced_39k
from backend.preprocessing import full_pipeline
from backend.train import train_model
import joblib, json, pathlib

BASE = pathlib.Path(__file__).parent
DATA_PATH = BASE / "data" / "creditcard_synthetic.csv"
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(exist_ok=True)

if not DATA_PATH.exists():
    df = create_balanced_39k()
    df.to_csv(DATA_PATH, index=False)
    print(f"Generated {len(df)} rows")
else:
    import pandas as pd
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows")
# use subset for fast seeding (prototype)
if len(df) > 8000:
    df = df.sample(n=8000, random_state=42)
    print(f"Subsampled to {len(df)} for fast seeding")

print("Running preprocessing...")
res = full_pipeline(df, method='manual', top_k=18)
print(f"Train {res['X_train'].shape} Test {res['X_test'].shape}")

for mode in ['classical','sa','qa']:
    print(f"\n=== Training {mode} ===")
    mdl, hist = train_model(res['X_train'], res['y_train'], res['X_test'], res['y_test'], n_visible=res['X_train'].shape[1], mode=mode, epochs=10, verbose=True)
    joblib.dump(mdl, MODEL_DIR / f"grbmc_{mode}.pkl")
    with open(MODEL_DIR / f"history_{mode}.json","w") as f:
        json.dump(hist, f, indent=2)
    print(f"Saved {mode} with best F1 {max(hist['f1']):.3f}")

# save pipeline for backend startup
import joblib as jb
jb.dump(res, MODEL_DIR / "pipeline.pkl")
print("Pipeline saved to models/pipeline.pkl")
print("All models seeded!")
