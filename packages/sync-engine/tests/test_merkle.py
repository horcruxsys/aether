import unittest
import os
import tempfile
import asyncio
from aether_sync.merkle.models import Partition
from aether_sync.merkle.engine import build_merkle_tree, find_changed_partitions, hash_partition
from aether_sync.merkle.async_engine import async_build_merkle_tree
from aether_sync.merkle.store import MerkleTreeStore


class TestHashPartition(unittest.TestCase):
    """Acceptance: Root hash is deterministic across multiple builds of identical data."""

    def test_deterministic_hash(self):
        data = [{"id": 1, "val": "A"}, {"id": 2, "val": "B"}]
        h1 = hash_partition(data)
        h2 = hash_partition(data)
        self.assertEqual(h1, h2)

    def test_order_independent(self):
        data = [{"id": 1, "val": "A"}, {"id": 2, "val": "B"}]
        h1 = hash_partition(data)
        h2 = hash_partition(list(reversed(data)))
        self.assertEqual(h1, h2)

    def test_different_data_different_hash(self):
        h1 = hash_partition([{"id": 1, "val": "A"}])
        h2 = hash_partition([{"id": 1, "val": "X"}])
        self.assertNotEqual(h1, h2)

    def test_empty_partition(self):
        h = hash_partition([])
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)  # SHA-256 hex length

    def test_single_record(self):
        h = hash_partition([{"id": 1}])
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)


class TestBuildMerkleTree(unittest.TestCase):
    """Acceptance: Merkle Tree builds correctly from any tabular source."""

    def test_empty_partitions(self):
        tree = build_merkle_tree([])
        self.assertIsNotNone(tree.hash)

    def test_single_partition(self):
        p = Partition(id="p1", records=[{"id": 1}])
        tree = build_merkle_tree([p])
        self.assertEqual(tree.partition_id, "p1")
        self.assertEqual(tree.record_count, 1)

    def test_two_partitions(self):
        tree = build_merkle_tree([
            Partition(id="p1", records=[{"id": 1}]),
            Partition(id="p2", records=[{"id": 2}]),
        ])
        self.assertIsNone(tree.partition_id)  # root is internal
        self.assertEqual(tree.record_count, 2)
        self.assertEqual(tree.left.partition_id, "p1")
        self.assertEqual(tree.right.partition_id, "p2")

    def test_odd_partitions(self):
        tree = build_merkle_tree([
            Partition(id="p1", records=[{"id": 1}]),
            Partition(id="p2", records=[{"id": 2}]),
            Partition(id="p3", records=[{"id": 3}]),
        ])
        self.assertEqual(tree.record_count, 3)

    def test_deterministic_root(self):
        parts = [
            Partition(id="p1", records=[{"id": 1, "val": "A"}]),
            Partition(id="p2", records=[{"id": 2, "val": "B"}]),
        ]
        t1 = build_merkle_tree(parts)
        t2 = build_merkle_tree(parts)
        self.assertEqual(t1.hash, t2.hash)


class TestDiff(unittest.TestCase):
    """Acceptance: Diff correctly identifies changed and unchanged partitions."""

    def setUp(self):
        self.parts = [
            Partition(id="p1", records=[{"id": 1, "val": "A"}, {"id": 2, "val": "B"}]),
            Partition(id="p2", records=[{"id": 3, "val": "C"}, {"id": 4, "val": "D"}]),
            Partition(id="p3", records=[{"id": 5, "val": "E"}, {"id": 6, "val": "F"}]),
            Partition(id="p4", records=[{"id": 7, "val": "G"}, {"id": 8, "val": "H"}]),
        ]

    def test_diff_unchanged(self):
        t1 = build_merkle_tree(self.parts)
        t2 = build_merkle_tree(self.parts)
        self.assertEqual(find_changed_partitions(t1, t2), [])

    def test_diff_single_change(self):
        t1 = build_merkle_tree(self.parts)
        modified = list(self.parts)
        modified[2] = Partition(id="p3", records=[{"id": 5, "val": "MODIFIED"}, {"id": 6, "val": "F"}])
        t2 = build_merkle_tree(modified)
        diff = find_changed_partitions(t1, t2)
        self.assertEqual(diff, ["p3"])

    def test_diff_all_changed(self):
        t1 = build_merkle_tree(self.parts)
        all_mod = [
            Partition(id=p.id, records=[{"id": r["id"], "val": "X"} for r in p.records])
            for p in self.parts
        ]
        t2 = build_merkle_tree(all_mod)
        diff = sorted(find_changed_partitions(t1, t2))
        self.assertEqual(diff, ["p1", "p2", "p3", "p4"])

    def test_diff_boundary_change(self):
        """Partition boundary: only last record in last partition changes."""
        t1 = build_merkle_tree(self.parts)
        modified = list(self.parts)
        modified[3] = Partition(id="p4", records=[{"id": 7, "val": "G"}, {"id": 8, "val": "CHANGED"}])
        t2 = build_merkle_tree(modified)
        diff = find_changed_partitions(t1, t2)
        self.assertEqual(diff, ["p4"])

    def test_diff_first_sync(self):
        """First sync: old_tree is None → all partitions are 'changed'."""
        t2 = build_merkle_tree(self.parts)
        diff = sorted(find_changed_partitions(None, t2))
        self.assertEqual(diff, ["p1", "p2", "p3", "p4"])


class TestAsyncEngine(unittest.TestCase):
    """Acceptance: Async engine produces identical results to sync engine."""

    def test_async_matches_sync(self):
        parts = [
            Partition(id="p1", records=[{"id": 1, "val": "A"}]),
            Partition(id="p2", records=[{"id": 2, "val": "B"}]),
        ]
        sync_tree = build_merkle_tree(parts)
        async_tree = asyncio.run(async_build_merkle_tree(parts, max_workers=2))
        self.assertEqual(sync_tree.hash, async_tree.hash)
        self.assertEqual(sync_tree.record_count, async_tree.record_count)


class TestMerkleTreeStore(unittest.TestCase):
    """Acceptance: Tree snapshots persist and load correctly."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.store = MerkleTreeStore(db_path=self.tmp.name)
        self.parts = [
            Partition(id="p1", records=[{"id": 1}]),
            Partition(id="p2", records=[{"id": 2}]),
        ]

    def tearDown(self):
        self.store.close()
        os.unlink(self.tmp.name)
        # WAL and SHM files
        for suffix in ("-wal", "-shm"):
            p = self.tmp.name + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_save_and_load(self):
        tree = build_merkle_tree(self.parts)
        self.store.save_snapshot("conn_1", tree)
        loaded = self.store.load_latest("conn_1")
        self.assertIsNotNone(loaded)
        self.assertEqual(tree.hash, loaded.hash)
        self.assertEqual(tree.record_count, loaded.record_count)
        self.assertEqual(loaded.left.partition_id, "p1")

    def test_load_nonexistent(self):
        self.assertIsNone(self.store.load_latest("nonexistent"))

    def test_snapshot_history(self):
        t1 = build_merkle_tree(self.parts)
        self.store.save_snapshot("conn_1", t1)

        parts_mod = [
            Partition(id="p1", records=[{"id": 1, "val": "X"}]),
            Partition(id="p2", records=[{"id": 2}]),
        ]
        t2 = build_merkle_tree(parts_mod)
        self.store.save_snapshot("conn_1", t2)

        latest = self.store.load_latest("conn_1")
        self.assertEqual(latest.hash, t2.hash)

        history = self.store.list_snapshots("conn_1")
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]["is_latest"])
        self.assertFalse(history[1]["is_latest"])

    def test_rollback(self):
        t1 = build_merkle_tree(self.parts)
        sid1 = self.store.save_snapshot("conn_1", t1)

        parts_mod = [Partition(id="p1", records=[{"id": 99}]), Partition(id="p2", records=[{"id": 2}])]
        t2 = build_merkle_tree(parts_mod)
        self.store.save_snapshot("conn_1", t2)

        self.store.rollback_to("conn_1", sid1)
        latest = self.store.load_latest("conn_1")
        self.assertEqual(latest.hash, t1.hash)

    def test_prune(self):
        for i in range(5):
            t = build_merkle_tree([Partition(id=f"p{i}", records=[{"id": i}])])
            self.store.save_snapshot("conn_1", t)
        deleted = self.store.prune_old_snapshots("conn_1", keep=2)
        self.assertEqual(deleted, 3)
        self.assertEqual(len(self.store.list_snapshots("conn_1")), 2)


class TestIntegrationSyncCycle(unittest.TestCase):
    """
    Acceptance: Integration test — full sync → partial change → incremental sync.
    Verifies that only changed partitions are flagged for re-embedding.
    """

    def test_full_cycle(self):
        # --- Initial ingest ---
        partitions_v1 = [
            Partition(id="customers_0_999", records=[{"id": i, "name": f"cust_{i}"} for i in range(100)]),
            Partition(id="customers_1000_1999", records=[{"id": i, "name": f"cust_{i}"} for i in range(100, 200)]),
            Partition(id="customers_2000_2999", records=[{"id": i, "name": f"cust_{i}"} for i in range(200, 300)]),
        ]
        tree_v1 = build_merkle_tree(partitions_v1)

        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        store = MerkleTreeStore(db_path=tmp.name)

        try:
            store.save_snapshot("postgres_prod", tree_v1)

            # --- Partial data change (only partition 1 changes) ---
            partitions_v2 = list(partitions_v1)
            partitions_v2[1] = Partition(
                id="customers_1000_1999",
                records=[{"id": i, "name": f"cust_{i}_UPDATED"} for i in range(100, 200)],
            )
            tree_v2 = build_merkle_tree(partitions_v2)

            # --- Incremental diff ---
            old_tree = store.load_latest("postgres_prod")
            changed = find_changed_partitions(old_tree, tree_v2)

            self.assertEqual(changed, ["customers_1000_1999"])
            # Only 1 of 3 partitions re-embedded → 66% cost savings

            store.save_snapshot("postgres_prod", tree_v2)
        finally:
            store.close()
            os.unlink(tmp.name)
            for s in ("-wal", "-shm"):
                p = tmp.name + s
                if os.path.exists(p):
                    os.unlink(p)


if __name__ == "__main__":
    unittest.main()
