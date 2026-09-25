# Certified Federated Unlearning Lab

This repository is an end-to-end, Python-only research demonstrator for the
project **“Privacy-Preserving Machine Unlearning in Federated LLMs: A Certified
Right-to-Be-Forgotten Framework.”** It implements the workflow specified in the
provided abstract and project review material:

1. federated training across isolated clients;
2. contribution tracking;
3. parameter-level client unlearning without full retraining;
4. a differential-privacy bound;
5. membership-inference and reference-retraining verification;
6. retained-model utility measurement; and
7. a tamper-evident compliance audit trail.

The included model is deliberately small enough to run offline on a classroom
computer. It is a character-level language-model proxy whose parameter vector
stands in for an LLM adapter update (such as LoRA). The orchestration and
verification boundaries are separated from the model, so the proxy can later
be replaced by a PyTorch/Flower/Hugging Face backend.

## Run the application

Python 3.10 or newer is sufficient. There are no third-party dependencies.

```powershell
python app.py
```

Then open **http://127.0.0.1:8000**. The localhost interface contains four tabs:

- **Federated Training** trains and evaluates the global language model.
- **Certified Unlearning** removes a selected client and produces a certificate.
- **Model Explorer** samples the model and displays per-client contribution data.
- **Compliance Audit** displays and verifies the hash-chained audit ledger.

To use another local port:

```powershell
python app.py --port 8080
```

The original native desktop interface is also available:

```powershell
python app.py --desktop
```

For a terminal-only demonstration (also useful on a headless server):

```powershell
python app.py --demo
```

Run the automated verification suite with:

```powershell
python -m unittest discover -s tests -v
```

## What the certificate means

Every client update is L2-clipped. Training releases an aggregate with Gaussian
noise, and reports the standard one-shot Gaussian-mechanism bound
`epsilon = sqrt(2 ln(1.25 / delta)) / noise_multiplier`. Unlearning subtracts
the tracked clipped update from the noisy aggregate and renormalizes over the
remaining clients. The application then verifies that result against a clean
recomputation from all retained updates, measures empirical membership leakage,
and records retained utility.

This is a demonstrator, not a legal compliance product or a claim that a
general-purpose LLM has been formally erased. For a production LLM, use
accounted DP-SGD, secure authenticated contribution storage, signed audit
records, and an independently reviewed unlearning proof.

## Project structure

```text
app.py                         GUI and command-line entry point
certified_unlearning/          federated model, certification, audit, sample data
tests/                         deterministic end-to-end tests
reference_material/            supplied abstract, paper metadata, and review files
data/                           runtime audit records (created automatically)
```
