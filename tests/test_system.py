import unittest

from main import DecisionPolicy, WEIGHTS, batch_metrics, decide


class RiskDecisionTests(unittest.TestCase):
    def test_high_risk_case_blocks(self):
        self.assertEqual(decide({k: 1 for k in WEIGHTS})["action"], "BLOCK")

    def test_low_risk_case_allows(self):
        self.assertEqual(decide({})["action"], "ALLOW")

    def test_reason_codes_preserve_explanation(self):
        result = decide({"identity_risk": .9, "velocity": .8})
        self.assertEqual(result["top_contributors"][0], "identity_risk")
        self.assertGreater(result["contributions"]["identity_risk"], 0)

    def test_batch_metrics_surface_customer_tradeoff(self):
        cases = [
            {"signals": {k: .9 for k in WEIGHTS}, "fraud": True},
            {"signals": {"identity_risk": .65, "velocity": .55}, "fraud": True},
            {"signals": {"velocity": .1}, "fraud": False},
            {"signals": {"payment_mismatch": .4}, "fraud": False},
        ]
        metrics = batch_metrics(cases)
        self.assertGreaterEqual(metrics["fraud_containment_rate"], .5)
        self.assertEqual(metrics["good_user_block_rate"], 0.0)

    def test_policy_thresholds_are_configurable(self):
        policy = DecisionPolicy(review_threshold=.2, block_threshold=.5)
        result = decide({"identity_risk": 1, "velocity": 1, "payment_mismatch": 1}, policy)
        self.assertIn(result["action"], {"REVIEW", "BLOCK"})


if __name__ == "__main__":
    unittest.main()
