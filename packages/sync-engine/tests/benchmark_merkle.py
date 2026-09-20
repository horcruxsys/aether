import time
import hashlib
from aether_sync.merkle.models import Partition
from aether_sync.merkle.engine import build_merkle_tree

def benchmark():
    num_partitions = 1000
    records_per_partition = 1000  # Total 1M records
    
    print(f"Generating {num_partitions * records_per_partition:,} records in {num_partitions} partitions...")
    
    partitions = []
    for i in range(num_partitions):
        records = [{"id": j, "data": f"some data {j}"} for j in range(i*1000, (i+1)*1000)]
        partitions.append(Partition(id=f"part_{i}", records=records))
        
    print("Building Merkle Tree...")
    start_time = time.time()
    tree = build_merkle_tree(partitions)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Tree Build Complete in {duration:.2f} seconds.")
    print(f"Root Hash: {tree.hash}")
    print(f"Total Records: {tree.record_count}")
    
    if duration < 30:
        print("✅ Performance benchmark PASSED (target < 30s)")
    else:
        print("❌ Performance benchmark FAILED (target < 30s)")

if __name__ == "__main__":
    benchmark()
