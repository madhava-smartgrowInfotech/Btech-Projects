"""One-shot pipeline: synthesize dataset -> pretrain JEPA encoder -> train fusion
classifier -> write all artifacts consumed by the API.

Run once before starting the server: `python ml/build_pipeline.py`
"""
import subprocess
import sys
from pathlib import Path

STEPS = ["generate_dataset.py", "train_encoder.py", "train_classifier.py"]


def main():
    ml_dir = Path(__file__).resolve().parent
    for step in STEPS:
        print(f"\n=== Running {step} ===")
        result = subprocess.run([sys.executable, str(ml_dir / step)])
        if result.returncode != 0:
            print(f"Pipeline failed at {step}")
            sys.exit(result.returncode)
    print("\nPipeline complete. Artifacts written to backend/artifacts/.")


if __name__ == "__main__":
    main()
