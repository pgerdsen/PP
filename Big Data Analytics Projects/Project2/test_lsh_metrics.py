#!/usr/bin/env python3
"""
Test script to generate LSH metrics:
- % comparison reduction
- MAE over X pairs (all candidate pairs or a sample)

Usage:
  python test_lsh_metrics.py --file similarity.txt --k 3 --num-perm 100 --bands 20 --rows 5
"""

import sys
import os
import argparse
import csv
from pathlib import Path

# Import from the main run.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import (
    read_paragraphs, build_docs, MinHasher, lsh_candidates,
    jaccard, est_from_signatures, LSHConfig
)


def calculate_lsh_metrics(paragraphs, cfg: LSHConfig, output_file: str = "lsh_metrics.csv"):
    """
    Calculate and output LSH metrics:
    1. % comparison reduction
    2. MAE over all candidate pairs (or a sample if too many)
    """
    import time
    
    t0 = time.time()
    
    # Build documents
    docs, shingle_map = build_docs(paragraphs, cfg.k)
    
    # Generate minhash signatures
    mh = MinHasher(cfg.num_perm, seed=cfg.seed)
    sigs = [mh.signature(d.shingle_ids) for d in docs]
    
    # Get LSH candidates
    cands = lsh_candidates(sigs, cfg.bands, cfg.rows)
    
    # Calculate total possible pairs
    n = len(docs)
    total_pairs = n * (n - 1) // 2
    candidate_pairs = len(cands)
    reduction_pct = (1 - candidate_pairs / total_pairs) * 100 if total_pairs > 0 else 0.0
    
    # Calculate MAE over candidate pairs
    # If too many pairs, sample them (but report on all if feasible)
    max_pairs_for_mae = 10000  # Calculate MAE on up to 10k pairs
    pairs_to_evaluate = list(cands)
    
    if len(pairs_to_evaluate) > max_pairs_for_mae:
        import random
        random.seed(42)
        pairs_to_evaluate = random.sample(pairs_to_evaluate, max_pairs_for_mae)
        sample_note = f" (sampled {max_pairs_for_mae} from {len(cands)} total)"
    else:
        sample_note = ""
    
    # Calculate MAE: mean absolute error between estimated and exact Jaccard
    errors = []
    for i, j in pairs_to_evaluate:
        exact_jac = jaccard(docs[i].shingle_ids, docs[j].shingle_ids)
        est_jac = est_from_signatures(sigs[i], sigs[j])
        abs_error = abs(est_jac - exact_jac)
        errors.append(abs_error)
    
    mae = sum(errors) / len(errors) if errors else 0.0
    
    total_time = time.time() - t0
    
    # Write metrics to CSV
    metrics = {
        "num_documents": n,
        "total_possible_pairs": total_pairs,
        "candidate_pairs": len(cands),
        "comparison_reduction_pct": reduction_pct,
        "mae_over_pairs": mae,
        "num_pairs_evaluated": len(pairs_to_evaluate),
        "k": cfg.k,
        "num_perm": cfg.num_perm,
        "bands": cfg.bands,
        "rows": cfg.rows,
        "runtime_seconds": total_time
    }
    
    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=metrics.keys())
        w.writeheader()
        w.writerow(metrics)
    
    # Print summary
    print("\n" + "="*60)
    print("LSH METRICS")
    print("="*60)
    print(f"Documents: {n}")
    print(f"Total possible pairs: {total_pairs:,}")
    print(f"Candidate pairs (LSH): {len(cands):,}")
    print(f"Comparison Reduction: {reduction_pct:.2f}%")
    print(f"\nMAE (Mean Absolute Error): {mae:.4f}")
    print(f"  - Evaluated over {len(pairs_to_evaluate):,} pairs{sample_note}")
    print(f"  - Error = |estimated_jaccard - exact_jaccard|")
    print(f"\nConfiguration:")
    print(f"  k={cfg.k}, num_perm={cfg.num_perm}, bands={cfg.bands}, rows={cfg.rows}")
    print(f"Runtime: {total_time:.2f} seconds")
    print(f"\nResults written to: {output_file}")
    print("="*60)
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Calculate LSH metrics")
    parser.add_argument("--file", default="similarity.txt", help="Path to dataset")
    parser.add_argument("--k", type=int, default=3, help="Word-shingle size k")
    parser.add_argument("--num-perm", type=int, default=100, help="Number of minhash functions")
    parser.add_argument("--bands", type=int, default=20, help="Number of bands")
    parser.add_argument("--rows", type=int, default=5, help="Rows per band")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", default="lsh_metrics.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    # Read paragraphs
    paragraphs = read_paragraphs(args.file)
    
    # Create config
    cfg = LSHConfig(
        k=args.k,
        num_perm=args.num_perm,
        bands=args.bands,
        rows=args.rows,
        seed=args.seed
    )
    
    # Calculate metrics
    calculate_lsh_metrics(paragraphs, cfg, args.output)


if __name__ == "__main__":
    main()

