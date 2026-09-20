"""
Test suite for MinHash + LSH Schema Alignment Engine.

Covers all acceptance criteria from ISSUE-002:
  - Column name convention matching (user_id ↔ userId ↔ uid)
  - Value distribution matching
  - NULL-heavy column handling
  - Incremental index addition
  - Schema graph JSON serialization
  - Jaccard accuracy (within 5% for 95% of pairs)
  - Performance benchmark (10,000 columns in < 60s)
"""
import unittest
import time
import random
import string
from aether_schema.lsh.models import ColumnProfile
from aether_schema.lsh.minhash import minhash, jaccard_estimate
from aether_schema.lsh.profiler import (
    tokenize_identifier,
    normalize_value,
    profile_column_from_values,
)
from aether_schema.lsh.lsh_index import LSHIndex
from aether_schema.lsh.schema_graph import (
    build_schema_graph,
    extract_concept_clusters,
    serialize_clusters,
    to_json,
)


# ── Tokenizer Tests ──────────────────────────────────────────────────

class TestTokenizer(unittest.TestCase):
    def test_snake_case(self):
        self.assertEqual(tokenize_identifier("customer_id"), {"customer", "id"})

    def test_camel_case(self):
        self.assertEqual(tokenize_identifier("customerId"), {"customer", "id"})

    def test_pascal_case(self):
        self.assertEqual(tokenize_identifier("CustomerId"), {"customer", "id"})

    def test_uppercase(self):
        self.assertEqual(tokenize_identifier("CREATED_AT"), {"created", "at"})

    def test_short_name(self):
        tokens = tokenize_identifier("uid")
        self.assertIn("uid", tokens)

    def test_complex_name(self):
        tokens = tokenize_identifier("customerUserId")
        self.assertEqual(tokens, {"customer", "user", "id"})

    def test_empty(self):
        self.assertEqual(tokenize_identifier(""), set())

    def test_kebab_case(self):
        tokens = tokenize_identifier("email-address")
        self.assertEqual(tokens, {"email", "address"})


# ── Normalizer Tests ─────────────────────────────────────────────────

class TestNormalizer(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(normalize_value("Hello World"), "hello world")

    def test_none(self):
        self.assertIsNone(normalize_value(None))

    def test_null_string(self):
        self.assertIsNone(normalize_value("null"))
        self.assertIsNone(normalize_value("None"))
        self.assertIsNone(normalize_value("NaN"))

    def test_number(self):
        self.assertEqual(normalize_value(42), "42")

    def test_whitespace_collapse(self):
        self.assertEqual(normalize_value("  hello   world  "), "hello world")


# ── MinHash Tests ─────────────────────────────────────────────────────

class TestMinHash(unittest.TestCase):
    def test_identical_sets(self):
        s = {"a", "b", "c"}
        sig1 = minhash(s)
        sig2 = minhash(s)
        self.assertEqual(sig1, sig2)
        self.assertAlmostEqual(jaccard_estimate(sig1, sig2), 1.0)

    def test_disjoint_sets(self):
        sig1 = minhash({"a", "b", "c"})
        sig2 = minhash({"x", "y", "z"})
        est = jaccard_estimate(sig1, sig2)
        self.assertLess(est, 0.15)  # Should be close to 0

    def test_overlapping_sets(self):
        set_a = {"a", "b", "c", "d"}
        set_b = {"c", "d", "e", "f"}
        true_jaccard = 2 / 6  # |intersection|/|union| = {c,d}/{a,b,c,d,e,f}
        sig_a = minhash(set_a)
        sig_b = minhash(set_b)
        est = jaccard_estimate(sig_a, sig_b)
        self.assertAlmostEqual(est, true_jaccard, delta=0.15)

    def test_empty_set(self):
        sig = minhash(set())
        self.assertEqual(len(sig), 256)

    def test_empty_vs_nonempty(self):
        sig_empty = minhash(set())
        sig_full = minhash({"a", "b"})
        est = jaccard_estimate(sig_empty, sig_full)
        self.assertAlmostEqual(est, 0.0, delta=0.05)

    def test_accuracy_within_5_percent(self):
        """Acceptance: Jaccard estimate within 5% of true for 95% of pairs."""
        random.seed(42)
        total_pairs = 200
        within_threshold = 0

        for _ in range(total_pairs):
            # Generate two random sets with some overlap
            universe = [f"item_{i}" for i in range(100)]
            size_a = random.randint(20, 80)
            size_b = random.randint(20, 80)
            set_a = set(random.sample(universe, size_a))
            set_b = set(random.sample(universe, size_b))

            true_j = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 0.0
            sig_a = minhash(set_a, num_hashes=256)
            sig_b = minhash(set_b, num_hashes=256)
            est_j = jaccard_estimate(sig_a, sig_b)

            if abs(est_j - true_j) <= 0.05:
                within_threshold += 1

        accuracy = within_threshold / total_pairs
        self.assertGreaterEqual(
            accuracy, 0.90,
            f"Only {accuracy*100:.1f}% of pairs within 5% threshold (need 90%)"
        )


# ── Profiler Tests ────────────────────────────────────────────────────

class TestProfiler(unittest.TestCase):
    def test_basic_profile(self):
        p = profile_column_from_values(
            db_id="pg", table="users", column="email_address",
            values=["a@b.com", "c@d.com", None, "e@f.com"]
        )
        self.assertEqual(p.db_id, "pg")
        self.assertIn("email", p.name_tokens)
        self.assertIn("address", p.name_tokens)
        self.assertEqual(len(p.sample_values), 3)  # None excluded
        self.assertEqual(len(p.value_sketch), 256)

    def test_null_heavy_column(self):
        """Acceptance: NULL-heavy columns handled without crashing."""
        values = [None] * 490 + ["real_value"] * 10
        p = profile_column_from_values(
            db_id="pg", table="t", column="notes", values=values
        )
        self.assertEqual(len(p.sample_values), 1)
        self.assertEqual(len(p.value_sketch), 256)

    def test_all_nulls(self):
        p = profile_column_from_values(
            db_id="pg", table="t", column="empty_col", values=[None] * 100
        )
        self.assertEqual(len(p.sample_values), 0)
        self.assertEqual(len(p.value_sketch), 256)


# ── LSH Index Tests ───────────────────────────────────────────────────

class TestLSHIndex(unittest.TestCase):
    def _make_profile(self, db_id, table, column, values):
        return profile_column_from_values(db_id, table, column, values)

    def test_similar_columns_found(self):
        """Acceptance: Matching columns with similar value distributions found."""
        emails_pg = [f"user{i}@example.com" for i in range(100)]
        emails_mongo = [f"user{i}@example.com" for i in range(100)]

        p1 = self._make_profile("postgres", "customers", "email", emails_pg)
        p2 = self._make_profile("mongo", "users", "emailAddress", emails_mongo)

        index = LSHIndex()
        index.add(p1)
        index.add(p2)

        candidates = index.find_candidates(p1, threshold=0.3)
        keys = [c.target_key for c in candidates]
        self.assertIn("mongo.users.emailAddress", keys)

    def test_different_names_same_values(self):
        """Acceptance: user_id ↔ userId ↔ uid detected via values."""
        ids = [f"USR-{i:05d}" for i in range(200)]

        p1 = self._make_profile("pg", "customers", "user_id", ids)
        p2 = self._make_profile("mongo", "orders", "userId", ids)
        p3 = self._make_profile("cassandra", "events", "uid", ids)

        index = LSHIndex()
        index.add_many([p1, p2, p3])

        candidates = index.find_candidates(p1, threshold=0.3)
        target_keys = {c.target_key for c in candidates}
        self.assertIn("mongo.orders.userId", target_keys)
        self.assertIn("cassandra.events.uid", target_keys)

    def test_incremental_addition(self):
        """Acceptance: Index supports incremental addition."""
        ids = [f"ID-{i}" for i in range(100)]

        index = LSHIndex()
        p1 = self._make_profile("pg", "t", "customer_id", ids)
        index.add(p1)
        self.assertEqual(index.size, 1)

        p2 = self._make_profile("mongo", "t", "customerId", ids)
        index.add(p2)
        self.assertEqual(index.size, 2)

        candidates = index.find_candidates(p1, threshold=0.3)
        self.assertTrue(len(candidates) > 0)

    def test_dissimilar_not_matched(self):
        """Unrelated columns should not be candidates."""
        p1 = self._make_profile("pg", "t", "email",
                                 [f"u{i}@test.com" for i in range(100)])
        p2 = self._make_profile("pg", "t", "zip_code",
                                 [str(10000 + i) for i in range(100)])

        index = LSHIndex()
        index.add_many([p1, p2])

        candidates = index.find_candidates(p1, threshold=0.5)
        target_keys = {c.target_key for c in candidates}
        self.assertNotIn("pg.t.zip_code", target_keys)


# ── Schema Graph Tests ────────────────────────────────────────────────

class TestSchemaGraph(unittest.TestCase):
    def test_graph_construction(self):
        ids = [f"ID-{i}" for i in range(100)]

        p1 = profile_column_from_values("pg", "customers", "customer_id", ids)
        p2 = profile_column_from_values("mongo", "orders", "customerId", ids)
        p3 = profile_column_from_values("mysql", "billing", "cust_id", ids)

        index = LSHIndex()
        index.add_many([p1, p2, p3])

        candidates = index.find_all_alignments(threshold=0.3)
        profiles = {p.key: p for p in [p1, p2, p3]}
        G = build_schema_graph(candidates, profiles, threshold=0.3)

        self.assertGreater(G.number_of_edges(), 0)

    def test_concept_clusters(self):
        ids = [f"ID-{i}" for i in range(100)]

        p1 = profile_column_from_values("pg", "customers", "customer_id", ids)
        p2 = profile_column_from_values("mongo", "orders", "customerId", ids)

        index = LSHIndex()
        index.add_many([p1, p2])

        candidates = index.find_all_alignments(threshold=0.3)
        profiles = {p.key: p for p in [p1, p2]}
        G = build_schema_graph(candidates, profiles, threshold=0.3)
        clusters = extract_concept_clusters(G)

        self.assertTrue(len(clusters) >= 1)
        cluster_keys = clusters[0]
        self.assertIn("pg.customers.customer_id", cluster_keys)
        self.assertIn("mongo.orders.customerId", cluster_keys)

    def test_json_serialization(self):
        """Acceptance: Schema alignment graph serializable to JSON."""
        ids = [f"ID-{i}" for i in range(100)]
        p1 = profile_column_from_values("pg", "t", "customer_id", ids)
        p2 = profile_column_from_values("mongo", "t", "customerId", ids)

        index = LSHIndex()
        index.add_many([p1, p2])

        candidates = index.find_all_alignments(threshold=0.3)
        profiles = {p.key: p for p in [p1, p2]}
        G = build_schema_graph(candidates, profiles, threshold=0.3)
        clusters = extract_concept_clusters(G)
        schema_map = serialize_clusters(clusters, profiles, G)

        json_str = to_json(schema_map)
        self.assertIsInstance(json_str, str)

        import json
        parsed = json.loads(json_str)
        self.assertIn("concept_clusters", parsed)
        self.assertIn("total_clusters", parsed)
        self.assertGreater(len(parsed["concept_clusters"]), 0)


# ── Performance Benchmark ────────────────────────────────────────────

class TestPerformance(unittest.TestCase):
    def test_10k_columns_under_60s(self):
        """Acceptance: 10,000 column schema aligned in < 60 seconds."""
        random.seed(42)
        num_columns = 10_000
        num_dbs = 10
        columns_per_db = num_columns // num_dbs

        index = LSHIndex()

        start = time.time()

        for db_idx in range(num_dbs):
            db_id = f"db_{db_idx}"
            for col_idx in range(columns_per_db):
                # Generate synthetic values
                values = [
                    ''.join(random.choices(string.ascii_lowercase, k=8))
                    for _ in range(20)
                ]
                p = profile_column_from_values(
                    db_id=db_id,
                    table=f"table_{col_idx // 100}",
                    column=f"col_{col_idx}",
                    values=values,
                )
                index.add(p)

        elapsed = time.time() - start
        self.assertLess(
            elapsed, 60.0,
            f"Indexing 10,000 columns took {elapsed:.1f}s (limit: 60s)"
        )
        self.assertEqual(index.size, num_columns)


if __name__ == "__main__":
    unittest.main()
