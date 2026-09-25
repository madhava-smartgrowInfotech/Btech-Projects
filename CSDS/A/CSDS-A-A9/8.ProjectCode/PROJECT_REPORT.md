# Project Design and Requirement Traceability

## Project title

**Privacy-Preserving Machine Unlearning in Federated LLMs: A Certified
Right-to-Be-Forgotten Framework**

## How the supplied material was used

The supplied abstract defines the application problem and its required outcome:
a client contribution must be removable from a federated model without a full
retraining cycle, the removal must have measurable privacy evidence, retained
model quality must be checked, and each request must leave an auditable record.

The supplied base-paper metadata points to a 2025 survey of continuous sign
language recognition. Its technical subject is different from federated
unlearning, so no sign-language algorithm was copied into this application.
The project material explicitly says to adopt the paper's review method:
organize approaches into a taxonomy, compare strengths and limitations, and
identify a research gap. That method led to the following design choice:

| Approach class | Strength | Limitation | Application decision |
|---|---|---|---|
| Full retraining | Strong removal baseline | Computationally expensive | Used only as a recomputation reference |
| Gradient/weight heuristics | Fast | No exact removal evidence | Not used for certification |
| Sharded/SISA retraining | Limits retraining scope | Adds training architecture complexity | Left as a future backend |
| Differentially private training | Bounds contribution leakage | Privacy/utility trade-off | Gaussian release bound included |
| Tracked additive updates | Efficient exact subtraction | Requires protected update storage | Used by this demonstrator |

The identified gap is addressed by joining tracked parameter removal, a formal
DP release bound, deterministic recomputation, empirical attack evaluation,
utility evaluation, and a chained compliance log in one workflow.

## System architecture

```text
Client text records (remain local to client objects)
       │
       ├── Character bigram update ── L2 clipping ──┐
       ├── Character bigram update ── L2 clipping ──┤
       └── Character bigram update ── L2 clipping ──┤
                                                    ▼
                                    Federated sum + Gaussian noise
                                                    │
                                                    ▼
                                          Global language model
                                                    │
                    ┌───────────────────────────────┴────────────────────┐
                    ▼                                                    ▼
       Unlearning request                                  Utility / attack metrics
                    │
                    ▼
       Subtract tracked client update
                    │
                    ▼
       Renormalize retained clients
                    │
                    ├── compare with retained-only recomputation
                    ├── membership-inference evaluation
                    ├── retained-utility evaluation
                    └── certificate → SHA-256 chained audit ledger
```

## Requirement-to-code mapping

| Abstract/objective requirement | Implementation |
|---|---|
| Federated fine-tuning across clients | `FederatedUnlearningEngine.train()` creates and aggregates isolated client updates |
| Parameter-level unlearning | `FederatedUnlearningEngine.unlearn()` subtracts the selected clipped update |
| Differential-privacy guarantee | Gaussian noise and the one-shot `(epsilon, delta)` calculation |
| Membership-inference verification | Loss-based attack AUC before and after removal |
| Compare against retraining | Retained updates plus the original DP randomness are recomputed independently |
| Preserve model utility | Public-set perplexity, next-character accuracy, and a retention score |
| Auditable compliance record | Append-only JSONL ledger with sequence and SHA-256 predecessor hashes |
| User-facing application | Standard-library Tkinter desktop interface and JSON certificate export |

## Unlearning and certification algorithm

For client updates `u_i`, client count `n`, and sampled Gaussian noise `z`, the
released parameter vector is:

```text
theta = (sum(u_i) + z) / n
```

Each `u_i` has L2 norm at most the configured clipping norm `C`. For noise
standard deviation `sigma * C`, the demonstrator reports the conventional
single Gaussian-mechanism bound:

```text
epsilon = sqrt(2 * ln(1.25 / delta)) / sigma
```

When client `j` requests deletion, the new model is computed without accessing
any of its raw records:

```text
theta_without_j = (sum(u_i) + z - u_j) / (n - 1), for i over all clients
```

An independent retained-only computation is produced and its L2 distance from
`theta_without_j` is recorded. A certificate is marked `CERTIFIED` when this
distance is within floating-point tolerance and retained utility remains above
the configured demonstration floor.

## Privacy and security boundaries

- This implementation is a reproducible academic prototype, not a production
  LLM or a legal compliance determination.
- The DP value describes the noisy aggregate release under the stated one-shot
  Gaussian-mechanism assumptions. Repeated production releases require a
  privacy accountant.
- Membership-inference AUC is an empirical diagnostic, not a formal proof.
- SHA-256 chaining exposes later changes to the audit file; production records
  should additionally use authenticated storage and organizational signatures.
- Tracked updates are sensitive artifacts. A deployment should encrypt them,
  apply strict access controls, and define a retention policy.

## Production extension path

The proxy update in `certified_unlearning/model.py` can be replaced with a LoRA
adapter tensor from a small Hugging Face model. Flower can transport client
updates, Opacus can perform accounted DP-SGD, and secure aggregation can protect
updates in transit. The coordinator API, verification sequence, certificate
schema, and audit workflow can remain the same.

