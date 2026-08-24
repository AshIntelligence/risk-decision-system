# Risk Decision System

[![System checks](https://github.com/AshIntelligence/risk-decision-system/actions/workflows/tests.yml/badge.svg)](https://github.com/AshIntelligence/risk-decision-system/actions/workflows/tests.yml)

`Python · risk decisioning · policy tradeoffs · human review`

This project combines behavioral, payment and identity signals into explainable **ALLOW / REVIEW / BLOCK** states while keeping policy thresholds separate from signal scoring.

The goal is not to maximize blocking. A risk system can reduce fraud and still be a poor product if false positives hurt good users or if too much traffic is pushed into manual review.

## What the code models

`DecisionPolicy` keeps review and block thresholds separate from signal weights, so policy can change without rewriting scoring logic.

`decide(...)` returns the score, action, top reason codes, per-signal contributions and the thresholds that produced the decision.

`batch_metrics(...)` runs labeled synthetic cases and exposes four product-level tradeoffs:

- block rate
- review rate
- fraud containment rate
- good-user block rate

That keeps customer harm and operational load visible alongside containment.

## Decision flow

```mermaid
flowchart LR
  S[Behavior + payment + identity signals] --> W[Weighted contributions]
  W --> P{Decision policy}
  P --> A[ALLOW]
  P --> R[REVIEW]
  P --> B[BLOCK]
  A --> M[Batch tradeoff metrics]
  R --> M
  B --> M
```

## Run

```bash
python main.py
python main.py --test
python -m unittest discover -s tests -v
```

No external services or API keys are required. The cases are synthetic; this is a policy/decisioning prototype, not a trained production fraud model.

## Next

The next iteration is threshold calibration against a versioned labeled dataset, review-capacity modeling, cohort-level false-positive analysis and expected-loss-versus-conversion tradeoffs.

This is one flagship from the broader [Ash Intelligence systems lab](https://github.com/AshIntelligence/agenticmine).