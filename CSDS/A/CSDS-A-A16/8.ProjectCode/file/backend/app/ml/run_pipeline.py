"""Runs the full training pipeline in order: basic backbone -> cEmoGAN -> final
multi-label classifier. Run from backend/: python -m app.ml.run_pipeline
"""
import time

from app.ml import train_classifier_stage1, train_gan, train_final_classifier
from app.config import CHECKPOINT_DIR

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
log_path = CHECKPOINT_DIR / "training_log.txt"
log_path.write_text("")  # fresh log for this run

t0 = time.time()
print("=== Stage 1: basic emotion backbone ===")
train_classifier_stage1.main()

print("\n=== Stage 2: cEmoGAN conditional generator ===")
train_gan.main()

print("\n=== Stage 3: final 18-label multi-label classifier ===")
train_final_classifier.main()

print(f"\nPipeline complete in {(time.time()-t0)/60:.1f} min.")
