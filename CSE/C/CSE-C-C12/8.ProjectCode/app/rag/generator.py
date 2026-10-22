"""Local grounded response generation with deterministic fallback."""

DISCLAIMER = ("CareLens AI provides preliminary health information and is not a medical diagnosis. "
              "Consult a qualified healthcare professional for diagnosis and treatment.")

class Generator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.pipe = None
        self.available = False
        self._load()

    def _load(self):
        try:
            from transformers import pipeline
            try:
                self.pipe = pipeline("text2text-generation", model=self.model_name, device=-1)
            except Exception:
                self.pipe = pipeline("text-generation", model=self.model_name, device=-1)
            self.available = True
        except Exception as e:
            print(f"[generator] local model unavailable ({e}); using evidence-based fallback.")
            self.available = False

    def _prompt(self, query: str, evidence: list[dict]) -> str:
        ctx_lines = []
        for i, c in enumerate(evidence, 1):
            r = c["record"]
            ctx_lines.append(f"[{i}] Condition: {r.get('disease','')}; Symptoms: {r.get('symptoms','')}; "
                             f"Description: {r.get('description','')}; Guidance: {r.get('guidance','')}")
        ctx = "\n".join(ctx_lines)
        return (
            "Answer only from the retrieved context below. Avoid definitive diagnosis. "
            "Avoid prescribing medication. Mention uncertainty. Recommend professional care when appropriate. "
            "Keep the answer concise and understandable.\n"
            f"User symptoms: {query}\nRetrieved medical information:\n{ctx}\nAnswer:"
        )

    def fallback_answer(self, query: str, evidence: list[dict]) -> str:
        if not evidence:
            return ("I could not find closely matching information for those symptoms in the local "
                    "medical knowledge base. " + DISCLAIMER)
        parts = []
        for i, c in enumerate(evidence, 1):
            r = c["record"]
            parts.append(f"{i}. {r.get('disease','Unknown')} — commonly associated with: {r.get('symptoms','')}.")
        conds = "; ".join(parts)
        guide_bits = []
        for c in evidence[:3]:
            g = c["record"].get("guidance", "").strip()
            if g:
                guide_bits.append(g)
        guides = " ".join(guide_bits)
        return (
            f"Your symptoms most closely match information associated with: {evidence[0]['record'].get('disease','')}. "
            f"This is a preliminary information result, not a diagnosis. "
            f"Possible conditions suggested by matching medical information include: {conds} "
            f"Relevant health guidance from the matched records: {guides} "
            "If symptoms are severe, rapidly worsening, or you are worried, seek professional medical care promptly. "
            + DISCLAIMER
        )

    def generate(self, query: str, evidence: list[dict]) -> tuple[str, str]:
        """Returns (answer, generated_by)."""
        if self.available and self.pipe is not None:
            try:
                out = self.pipe(self._prompt(query, evidence), max_new_tokens=220, do_sample=False)
                text = out[0]["generated_text"].strip() if out else ""
                if not text:
                    raise RuntimeError("empty generation")
                # safety post-check: strip any definitive-diagnosis phrasing
                text = text.replace("You have ", "Information most closely associated with ")
                if "not a diagnosis" not in text.lower():
                    text += " This information is not a diagnosis; consult a qualified healthcare professional."
                return text, f"local-generator:{self.model_name}"
            except Exception as e:
                print(f"[generator] generation failed: {e}")
        return self.fallback_answer(query, evidence), "evidence-fallback"
