from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.rag.pipeline import Pipeline

def main():
    p = Pipeline()
    print(f"Index ready. FAISS total: {p.faiss.index.ntotal if p.faiss.index else 0}, embedding mode: {p.embeddings.mode}")

if __name__ == "__main__":
    main()
