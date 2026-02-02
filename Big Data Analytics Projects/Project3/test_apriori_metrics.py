#!/usr/bin/env python3
"""
Apriori Algorithm Metrics Test
Runs the Apriori implementation and captures performance metrics to CSV.
"""

import time
import resource
import csv
from pathlib import Path
from project3 import load_transactions, apriori, generate_rules

def get_peak_memory_mb():
    """Get peak memory usage in MB (macOS/Linux)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # macOS returns bytes, Linux returns KB
    import sys
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024

def main():
    data_file = "Groceries_dataset.csv"
    min_support = 0.005
    min_confidence = 0.0
    
    print(f"Loading transactions from {data_file}...")
    
    # Track runtime
    start_time = time.time()
    
    # Load and process
    transactions = load_transactions(data_file)
    num_transactions = len(transactions)
    
    # Run Apriori
    support_counts, support = apriori(transactions, min_support=min_support)
    
    # Generate rules
    rules = generate_rules(support_counts, support, min_confidence=min_confidence)
    
    end_time = time.time()
    runtime = end_time - start_time
    
    # Gather metrics
    total_itemsets = len(support_counts)
    max_itemset_size = max(len(s) for s in support_counts) if support_counts else 0
    num_rules = len(rules)
    peak_memory_mb = get_peak_memory_mb()
    
    # Get top itemset info
    top_itemsets = sorted(support.items(), key=lambda x: x[1], reverse=True)[:5]
    top_itemset_str = "; ".join([f"{set(i)}:{s:.4f}" for i, s in top_itemsets])
    
    # Get top rule info
    top_rules = rules[:3] if rules else []
    top_rule_str = "; ".join([
        f"{set(r['lhs'])}->{set(r['rhs'])}(conf={r['confidence']:.3f})"
        for r in top_rules
    ])
    
    # Print results
    print("\n" + "="*60)
    print("APRIORI ALGORITHM METRICS")
    print("="*60)
    print(f"Data file:              {data_file}")
    print(f"Min support:            {min_support}")
    print(f"Min confidence:         {min_confidence}")
    print(f"Runtime:                {runtime:.2f} seconds")
    print(f"Peak memory:            {peak_memory_mb:.2f} MB")
    print(f"Transactions processed: {num_transactions}")
    print(f"Frequent itemsets:      {total_itemsets}")
    print(f"Max itemset size:       {max_itemset_size}")
    print(f"Association rules:      {num_rules}")
    print("="*60)
    
    # Save to CSV
    output_file = Path("apriori_metrics.csv")
    file_exists = output_file.exists()
    
    with open(output_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "data_file",
                "min_support",
                "min_confidence",
                "runtime_sec",
                "peak_memory_mb",
                "num_transactions",
                "frequent_itemsets",
                "max_itemset_size",
                "num_rules",
                "top_itemsets",
                "top_rules"
            ])
        writer.writerow([
            data_file,
            min_support,
            min_confidence,
            f"{runtime:.2f}",
            f"{peak_memory_mb:.2f}",
            num_transactions,
            total_itemsets,
            max_itemset_size,
            num_rules,
            top_itemset_str,
            top_rule_str
        ])
    
    print(f"\nMetrics saved to {output_file}")

if __name__ == "__main__":
    main()
