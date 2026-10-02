import unittest
from src.mdm_engine import (
    Record, Condition, SourcePairPolicy,
    ClusterMembershipConstraint, EvaluatorEngine,
    tokenize_default, tokenize_bigram, tokenize_trigram,
    calc_jaccard, calc_cosine
)

class TestTokenizers(unittest.TestCase):
    def test_default_tokenizer(self):
        self.assertEqual(tokenize_default("hello world"), ["hello", "world"])

    def test_bigram_tokenizer(self):
        self.assertEqual(tokenize_bigram("abc"), ["ab", "bc"])

    def test_trigram_tokenizer(self):
        self.assertEqual(tokenize_trigram("abcd"), ["abc", "bcd"])

class TestAlgorithms(unittest.TestCase):
    def test_jaccard(self):
        tokens1 = ["a", "b", "c"]
        tokens2 = ["b", "c", "d"]
        # Intersection: b, c (2). Union: a, b, c, d (4). 2/4 = 0.5
        self.assertEqual(calc_jaccard(tokens1, tokens2), 0.5)

    def test_cosine(self):
        tokens1 = ["a", "b", "c"]
        tokens2 = ["b", "c", "d"]
        # Intersection: b, c. Numerator: 2. Denom: sqrt(3) * sqrt(3) = 3
        # 2 / 3 = 0.666...
        self.assertAlmostEqual(calc_cosine(tokens1, tokens2), 2/3)

class TestEvaluatorLogic(unittest.TestCase):
    def setUp(self):
        self.mdr1 = Record("mdr_1", "MDR", {"school_name": "Springfield High", "address": "123 Main St"})
        self.mdr2 = Record("mdr_2", "MDR", {"school_name": "Springfield High", "address": "123 Main St"})
        self.mdr3 = Record("mdr_3", "MDR", {"school_name": "Springfield Elementary", "address": "123 Main St"})

        self.dnb1 = Record("dnb_1", "DNB", {"school_name": "Springfield High School", "address": "123 Main Street"})

    def test_exact_match_condition(self):
        cond = Condition("school_name", "exact_match")
        self.assertTrue(cond.evaluate(self.mdr1, self.mdr2))
        self.assertFalse(cond.evaluate(self.mdr1, self.mdr3))

    def test_fuzzy_match_condition(self):
        # Cosine > 60%
        cond = Condition("school_name", ">", 0.60, algorithm="Cosine", tokenizer="Default")

        # "Springfield High" vs "Springfield High School"
        # T1: ["Springfield", "High"]
        # T2: ["Springfield", "High", "School"]
        # Intersection = 2, denom = sqrt(2) * sqrt(3) ~ 2.449
        # score ~ 0.816 > 0.60
        self.assertTrue(cond.evaluate(self.mdr1, self.dnb1))

    def test_source_pair_policy(self):
        # MDR-MDR must be exact match on school_name and address
        gate1 = Condition("school_name", "exact_match")
        gate2 = Condition("address", "exact_match")
        mdr_policy = SourcePairPolicy("MDR", "MDR", mandatory_gates=[gate1, gate2])

        self.assertTrue(mdr_policy.evaluate(self.mdr1, self.mdr2))
        self.assertFalse(mdr_policy.evaluate(self.mdr1, self.mdr3))

        # MDR-DNB allows fuzzy match on school_name OR exact match on address
        qual_clause1 = [Condition("school_name", ">", 0.80)] # fuzzy
        qual_clause2 = [Condition("address", "exact_match")] # exact
        dnb_policy = SourcePairPolicy("MDR", "DNB", qualifying_clauses=[qual_clause1, qual_clause2])

        # High School vs High School passes fuzzy (0.816 > 0.80)
        self.assertTrue(dnb_policy.evaluate(self.mdr1, self.dnb1))

class TestClusterConstraints(unittest.TestCase):
    def test_max_records_constraint(self):
        r1 = Record("mdr_1", "MDR", {})
        r2 = Record("mdr_2", "MDR", {})
        r3 = Record("dnb_1", "DNB", {})

        constraint = ClusterMembershipConstraint("MDR", max_records=1)

        # 1 MDR, 1 DNB -> passes
        self.assertTrue(constraint.validate([r1, r3]))

        # 2 distinct MDRs -> fails
        self.assertFalse(constraint.validate([r1, r2, r3]))

    def test_engine_integration(self):
        r1 = Record("mdr_1", "MDR", {"school_name": "Springfield High", "address": "123 Main St"})
        r2 = Record("mdr_2", "MDR", {"school_name": "Springfield High", "address": "123 Main St"})

        gate1 = Condition("school_name", "exact_match")
        mdr_policy = SourcePairPolicy("MDR", "MDR", mandatory_gates=[gate1])
        constraint = ClusterMembershipConstraint("MDR", max_records=1)

        engine = EvaluatorEngine(policies=[mdr_policy], constraints=[constraint])

        # evaluate_pair passes because they exactly match
        self.assertTrue(engine.evaluate_pair(r1, r2))

        # validate_cluster fails because we cannot have 2 distinct MDRs in the same cluster
        self.assertFalse(engine.validate_cluster([r1, r2]))

if __name__ == '__main__':
    unittest.main()
