"""
Test suite for Union-Find Entity Resolution Engine.

Covers all acceptance criteria from ISSUE-003:
  - Path compression and union by rank
  - find() idempotency
  - Incremental union (new DB doesn't rebuild existing clusters)
  - Evidence/provenance tracking
  - Deterministic canonical entity builder
  - Integration: 3 DBs with known overlapping entities
  - JSON serialization/deserialization
  - Scale benchmark
"""
import unittest
import time
import tempfile
import os
import json
from aether_entity.union_find.core import UnionFind
from aether_entity.union_find.record_id import make_record_id, parse_record_id
from aether_entity.union_find.matching import ExactKeyMatch, FuzzyStringMatch
from aether_entity.union_find.canonical import build_canonical_entity, entity_to_text
from aether_entity.union_find.pipeline import resolve_entities


# ── Core Union-Find Tests ─────────────────────────────────────────────

class TestUnionFindBasic(unittest.TestCase):
    def test_add_and_find(self):
        uf = UnionFind()
        uf.add("a")
        uf.add("b")
        self.assertEqual(uf.find("a"), "a")
        self.assertEqual(uf.find("b"), "b")
        self.assertEqual(uf.num_records(), 2)
        self.assertEqual(uf.num_clusters(), 2)

    def test_union_merges(self):
        uf = UnionFind()
        uf.add("a")
        uf.add("b")
        result = uf.union("a", "b")
        self.assertTrue(result)
        self.assertEqual(uf.find("a"), uf.find("b"))
        self.assertEqual(uf.num_clusters(), 1)

    def test_union_idempotent(self):
        uf = UnionFind()
        uf.add("a")
        uf.add("b")
        uf.union("a", "b")
        result = uf.union("a", "b")
        self.assertFalse(result)  # Already merged

    def test_find_idempotent(self):
        """Acceptance: find() is idempotent."""
        uf = UnionFind()
        uf.add("x")
        uf.add("y")
        uf.union("x", "y")
        root1 = uf.find("x")
        root2 = uf.find("x")
        self.assertEqual(root1, root2)

    def test_find_unknown_raises(self):
        uf = UnionFind()
        with self.assertRaises(KeyError):
            uf.find("nonexistent")

    def test_auto_add_on_union(self):
        uf = UnionFind()
        uf.union("a", "b")
        self.assertEqual(uf.num_records(), 2)
        self.assertTrue(uf.connected("a", "b"))


class TestPathCompression(unittest.TestCase):
    """Acceptance: Path compression implemented and tested."""

    def test_deep_chain_is_compressed(self):
        uf = UnionFind()
        # Build a deep chain: a→b→c→d→e
        nodes = [f"n{i}" for i in range(100)]
        for n in nodes:
            uf.add(n)
        for i in range(len(nodes) - 1):
            uf.union(nodes[i], nodes[i + 1])

        # After find, all should point directly to root
        root = uf.find(nodes[0])
        for n in nodes:
            self.assertEqual(uf.find(n), root)
            # After path compression, parent should be root
            self.assertEqual(uf._parent[n], root)


class TestUnionByRank(unittest.TestCase):
    """Acceptance: Union by rank implemented and tested."""

    def test_smaller_attaches_to_larger(self):
        uf = UnionFind()
        # Build two clusters of different sizes
        # Cluster A: 5 nodes
        for i in range(5):
            uf.add(f"a{i}")
        for i in range(1, 5):
            uf.union("a0", f"a{i}")

        # Cluster B: 2 nodes
        uf.add("b0")
        uf.add("b1")
        uf.union("b0", "b1")

        # Merge — larger cluster's root should become the new root
        root_a = uf.find("a0")
        uf.union("a0", "b0")

        # The root of the larger cluster should dominate
        self.assertEqual(uf.find("b0"), root_a)
        self.assertEqual(uf.cluster_size("a0"), 7)


class TestEvidence(unittest.TestCase):
    """Acceptance: Evidence/provenance tracked for every union."""

    def test_evidence_recorded(self):
        uf = UnionFind()
        uf.add("rec_a")
        uf.add("rec_b")
        uf.union("rec_a", "rec_b", evidence=["exact_key_match::email::test@test.com"])

        all_ev = uf.get_evidence("rec_a")
        self.assertTrue(len(all_ev) > 0)
        # Check the evidence content
        found = False
        for ev in all_ev:
            for item in ev.get("evidence", []):
                if "exact_key_match" in item:
                    found = True
        self.assertTrue(found)

    def test_cluster_evidence(self):
        uf = UnionFind()
        uf.union("a", "b", evidence=["match1"])
        uf.union("b", "c", evidence=["match2"])

        ev = uf.get_cluster_evidence("a")
        # Should have evidence from both merges
        evidence_strings = []
        for e in ev:
            evidence_strings.extend(e.get("evidence", []))
        self.assertIn("match1", evidence_strings)
        self.assertIn("match2", evidence_strings)


class TestIncremental(unittest.TestCase):
    """Acceptance: Incremental union — adding new DB doesn't rebuild."""

    def test_incremental_addition(self):
        uf = UnionFind()
        # Phase 1: Resolve two databases
        uf.union("pg::customers::001", "mongo::orders::abc")
        self.assertEqual(uf.num_clusters(), 1)

        # Phase 2: Add a third database incrementally
        uf.add("cassandra::events::evt001")
        self.assertEqual(uf.num_clusters(), 2)

        # Phase 3: Link the new record to existing cluster
        uf.union("pg::customers::001", "cassandra::events::evt001")
        self.assertEqual(uf.num_clusters(), 1)
        self.assertEqual(uf.cluster_size("pg::customers::001"), 3)

        # Verify all three are in the same cluster
        cluster = uf.get_cluster("pg::customers::001")
        self.assertEqual(len(cluster), 3)
        self.assertIn("pg::customers::001", cluster)
        self.assertIn("mongo::orders::abc", cluster)
        self.assertIn("cassandra::events::evt001", cluster)


# ── Serialization Tests ───────────────────────────────────────────────

class TestSerialization(unittest.TestCase):
    """Acceptance: Serialize/deserialize Union-Find state to JSON."""

    def test_to_json_and_back(self):
        uf = UnionFind()
        uf.union("a", "b", evidence=["test_evidence"])
        uf.union("c", "d")
        uf.add("e")

        json_str = uf.to_json()
        uf2 = UnionFind.from_json(json_str)

        self.assertEqual(uf2.num_records(), uf.num_records())
        self.assertEqual(uf2.num_clusters(), uf.num_clusters())
        self.assertTrue(uf2.connected("a", "b"))
        self.assertTrue(uf2.connected("c", "d"))
        self.assertFalse(uf2.connected("a", "c"))

    def test_file_persistence(self):
        uf = UnionFind()
        uf.union("x", "y", evidence=["file_test"])

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            uf.save_to_file(path)
            uf2 = UnionFind.load_from_file(path)
            self.assertTrue(uf2.connected("x", "y"))
            self.assertEqual(uf2.num_records(), 2)
        finally:
            os.unlink(path)

    def test_json_is_valid(self):
        uf = UnionFind()
        uf.union("a", "b")
        data = json.loads(uf.to_json())
        self.assertIn("parent", data)
        self.assertIn("rank", data)
        self.assertIn("size", data)
        self.assertIn("num_records", data)
        self.assertIn("num_clusters", data)


# ── Record ID Tests ───────────────────────────────────────────────────

class TestRecordId(unittest.TestCase):
    def test_make_and_parse(self):
        rid = make_record_id("postgres", "customers", 12345)
        self.assertEqual(rid, "postgres::customers::12345")
        db, table, pk = parse_record_id(rid)
        self.assertEqual(db, "postgres")
        self.assertEqual(table, "customers")
        self.assertEqual(pk, "12345")

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            parse_record_id("invalid")


# ── Matching Strategy Tests ───────────────────────────────────────────

class TestExactKeyMatch(unittest.TestCase):
    def test_matching_keys(self):
        strategy = ExactKeyMatch()
        records_a = [
            {"id": "1", "customer_id": "C001", "name": "Alice"},
            {"id": "2", "customer_id": "C002", "name": "Bob"},
        ]
        records_b = [
            {"id": "10", "customerId": "C001", "email": "alice@test.com"},
            {"id": "11", "customerId": "C003", "email": "carol@test.com"},
        ]

        matches = strategy.find_matches(
            records_a, records_b,
            "pg", "mongo", "customers", "orders",
            "customer_id", "customerId",
        )

        self.assertEqual(len(matches), 1)
        self.assertIn("C001", matches[0][2][0])

    def test_no_matches(self):
        strategy = ExactKeyMatch()
        matches = strategy.find_matches(
            [{"id": "1", "x": "A"}], [{"id": "2", "y": "B"}],
            "a", "b", "t1", "t2", "x", "y",
        )
        self.assertEqual(len(matches), 0)


class TestFuzzyStringMatch(unittest.TestCase):
    def test_email_normalization(self):
        strategy = FuzzyStringMatch()
        records_a = [
            {"id": "1", "email": "Alice+work@Example.COM"},
        ]
        records_b = [
            {"id": "2", "contact_email": "alice@example.com"},
        ]

        matches = strategy.find_matches(
            records_a, records_b,
            "pg", "mongo", "users", "contacts",
            "email", "contact_email",
        )
        self.assertEqual(len(matches), 1)

    def test_null_handling(self):
        strategy = FuzzyStringMatch()
        matches = strategy.find_matches(
            [{"id": "1", "email": None}],
            [{"id": "2", "email": "test@test.com"}],
            "a", "b", "t1", "t2", "email", "email",
        )
        self.assertEqual(len(matches), 0)


# ── Canonical Entity Tests ────────────────────────────────────────────

class TestCanonicalEntity(unittest.TestCase):
    """Acceptance: Canonical entity builder produces deterministic output."""

    def test_deterministic_output(self):
        cluster = {"pg::customers::1", "mongo::orders::abc"}
        records = {
            "pg::customers::1": {"name": "Alice", "age": 30},
            "mongo::orders::abc": {"email": "alice@test.com", "city": "NYC"},
        }

        e1 = build_canonical_entity(cluster, records)
        e2 = build_canonical_entity(cluster, records)

        self.assertEqual(e1["_entity_id"], e2["_entity_id"])
        self.assertEqual(e1["name"], "Alice")
        self.assertEqual(e1["email"], "alice@test.com")
        self.assertEqual(e1["_cluster_size"], 2)

    def test_priority_ordering(self):
        cluster = {"pg::t::1", "mongo::t::2"}
        records = {
            "pg::t::1": {"name": "alice_pg"},
            "mongo::t::2": {"name": "alice_mongo"},
        }

        entity = build_canonical_entity(
            cluster, records, priority_order=["pg", "mongo"]
        )
        # mongo is higher priority → its name wins
        self.assertEqual(entity["name"], "alice_mongo")

    def test_entity_to_text(self):
        entity = {"name": "Alice", "age": 30, "_entity_id": "xxx"}
        text = entity_to_text(entity)
        self.assertIn("name: Alice", text)
        self.assertIn("age: 30", text)
        self.assertNotIn("_entity_id", text)


# ── Integration Test: 3 DBs ──────────────────────────────────────────

class TestIntegration3DB(unittest.TestCase):
    """
    Acceptance: 3 DBs with known overlapping entities → all correctly clustered.
    """

    def test_full_resolution_pipeline(self):
        databases = {
            "postgres_crm": {
                "customers": [
                    {"id": "1", "customer_id": "C001", "name": "Alice", "email": "alice@example.com"},
                    {"id": "2", "customer_id": "C002", "name": "Bob", "email": "bob@example.com"},
                    {"id": "3", "customer_id": "C003", "name": "Carol", "email": "carol@example.com"},
                ]
            },
            "mongo_orders": {
                "orders": [
                    {"id": "10", "customerId": "C001", "product": "Widget A"},
                    {"id": "11", "customerId": "C002", "product": "Widget B"},
                    {"id": "12", "customerId": "C999", "product": "Widget C"},
                ]
            },
            "cassandra_events": {
                "clickstream": [
                    {"id": "100", "uid": "C001", "event": "page_view"},
                    {"id": "101", "uid": "C003", "event": "purchase"},
                    {"id": "102", "uid": "C004", "event": "page_view"},
                ]
            },
        }

        alignments = [
            {
                "db_a": "postgres_crm", "table_a": "customers", "column_a": "customer_id",
                "db_b": "mongo_orders", "table_b": "orders", "column_b": "customerId",
            },
            {
                "db_a": "postgres_crm", "table_a": "customers", "column_a": "customer_id",
                "db_b": "cassandra_events", "table_b": "clickstream", "column_b": "uid",
            },
        ]

        strategies = [ExactKeyMatch()]
        uf = resolve_entities(databases, alignments, strategies)

        # C001 should link pg:1 ↔ mongo:10 ↔ cassandra:100
        self.assertTrue(uf.connected(
            "postgres_crm::customers::1",
            "mongo_orders::orders::10",
        ))
        self.assertTrue(uf.connected(
            "postgres_crm::customers::1",
            "cassandra_events::clickstream::100",
        ))
        cluster_c001 = uf.get_cluster("postgres_crm::customers::1")
        self.assertEqual(len(cluster_c001), 3)

        # C002 should link pg:2 ↔ mongo:11 (no cassandra match)
        self.assertTrue(uf.connected(
            "postgres_crm::customers::2",
            "mongo_orders::orders::11",
        ))
        cluster_c002 = uf.get_cluster("postgres_crm::customers::2")
        self.assertEqual(len(cluster_c002), 2)

        # C003 should link pg:3 ↔ cassandra:101 (no mongo match)
        self.assertTrue(uf.connected(
            "postgres_crm::customers::3",
            "cassandra_events::clickstream::101",
        ))

        # Unmatched records should be singletons
        cluster_c999 = uf.get_cluster("mongo_orders::orders::12")
        self.assertEqual(len(cluster_c999), 1)

        # Verify total cluster count
        all_clusters = uf.all_clusters()
        multi_clusters = [c for c in all_clusters if len(c) > 1]
        self.assertEqual(len(multi_clusters), 3)  # C001(3), C002(2), C003(2)


# ── Scale Benchmark ───────────────────────────────────────────────────

class TestScaleBenchmark(unittest.TestCase):
    def test_1m_unions_under_5s(self):
        """Acceptance: 1M union operations complete in < 5s."""
        uf = UnionFind()
        n = 1_000_000

        # Add all records
        for i in range(n):
            uf.add(f"r{i}")

        start = time.time()
        # Chain unions — worst case for non-optimized implementations
        for i in range(n - 1):
            uf.union(f"r{i}", f"r{i + 1}")
        elapsed = time.time() - start

        self.assertLess(elapsed, 5.0, f"1M unions took {elapsed:.2f}s (limit: 5s)")
        self.assertEqual(uf.num_clusters(), 1)
        self.assertEqual(uf.cluster_size("r0"), n)


if __name__ == "__main__":
    unittest.main()
