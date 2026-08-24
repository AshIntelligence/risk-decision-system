"""Fraud Signal Decision Engine.

Explainable synthetic risk scoring with ALLOW / REVIEW / BLOCK states,
policy thresholds, reason codes and batch tradeoff metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Iterable

WEIGHTS = {
    "velocity": .22,
    "device_novelty": .15,
    "payment_mismatch": .20,
    "identity_risk": .24,
    "behavior_anomaly": .19,
}


@dataclass(frozen=True)
class DecisionPolicy:
    review_threshold: float = .43
    block_threshold: float = .72


DEFAULT_POLICY = DecisionPolicy()


def _clean(signals: dict) -> dict[str, float]:
    return {k: max(0.0, min(1.0, float(signals.get(k, 0)))) for k in WEIGHTS}


def decide(signals: dict, policy: DecisionPolicy = DEFAULT_POLICY) -> dict:
    """Score one synthetic event and keep the decision explainable."""
    if not 0 <= policy.review_threshold < policy.block_threshold <= 1:
        raise ValueError("thresholds must satisfy 0 <= review < block <= 1")

    clean = _clean(signals)
    contributions = {k: clean[k] * w for k, w in WEIGHTS.items()}
    score = sum(contributions.values())
    action = (
        "BLOCK"
        if score >= policy.block_threshold
        else "REVIEW"
        if score >= policy.review_threshold
        else "ALLOW"
    )
    top = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
    reason_codes = [k for k, contribution in top if contribution > 0]
    return {
        "score": round(score, 3),
        "action": action,
        "top_contributors": reason_codes,
        "contributions": {k: round(v, 3) for k, v in contributions.items()},
        "thresholds": {
            "review": policy.review_threshold,
            "block": policy.block_threshold,
        },
    }


def batch_metrics(
    cases: Iterable[dict],
    policy: DecisionPolicy = DEFAULT_POLICY,
) -> dict:
    """Measure review load and false-positive/containment tradeoffs on labeled synthetic cases."""
    rows = list(cases)
    if not rows:
        raise ValueError("cases must not be empty")

    decisions = [(row, decide(row["signals"], policy)) for row in rows]
    blocked = [x for x in decisions if x[1]["action"] == "BLOCK"]
    reviewed = [x for x in decisions if x[1]["action"] == "REVIEW"]

    fraud_rows = [x for x in decisions if bool(x[0]["fraud"])]
    good_rows = [x for x in decisions if not bool(x[0]["fraud"])]

    contained_fraud = [
        x for x in fraud_rows if x[1]["action"] in {"REVIEW", "BLOCK"}
    ]
    good_user_blocks = [x for x in good_rows if x[1]["action"] == "BLOCK"]

    return {
        "cases": len(rows),
        "block_rate": round(len(blocked) / len(rows), 3),
        "review_rate": round(len(reviewed) / len(rows), 3),
        "fraud_containment_rate": round(
            len(contained_fraud) / max(1, len(fraud_rows)), 3
        ),
        "good_user_block_rate": round(
            len(good_user_blocks) / max(1, len(good_rows)), 3
        ),
    }


def self_test():
    assert decide({k: 1 for k in WEIGHTS})["action"] == "BLOCK"
    assert decide({})["action"] == "ALLOW"
    assert decide({"identity_risk": .9, "velocity": .8})["top_contributors"][0] == "identity_risk"

    sample = [
        {"signals": {k: .9 for k in WEIGHTS}, "fraud": True},
        {"signals": {"identity_risk": .65, "velocity": .55}, "fraud": True},
        {"signals": {"velocity": .1}, "fraud": False},
        {"signals": {"payment_mismatch": .4}, "fraud": False},
    ]
    metrics = batch_metrics(sample)
    assert metrics["fraud_containment_rate"] >= .5
    assert metrics["good_user_block_rate"] == 0.0


def demo():
    for signals in [
        {"velocity": .9, "identity_risk": .8, "payment_mismatch": .7},
        {"velocity": .1, "identity_risk": .1},
    ]:
        print(decide(signals))

    print(batch_metrics([
        {"signals": {k: .9 for k in WEIGHTS}, "fraud": True},
        {"signals": {"identity_risk": .65, "velocity": .55}, "fraud": True},
        {"signals": {"velocity": .1}, "fraud": False},
        {"signals": {"payment_mismatch": .4}, "fraud": False},
    ]))


if __name__ == "__main__":
    self_test() if "--test" in sys.argv else demo()
