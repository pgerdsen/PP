#!/usr/bin/env python3
"""
Test script to generate MapReduce metrics:
- Runtime
- Peak memory usage
- Spill threshold

Usage:
  python test_mapreduce_metrics.py --input-dir inputs --batch 50000
"""

import sys
import os
import argparse
import csv
import time
import resource
from pathlib import Path

# Import from main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import (
    map_stage, combine_stage, merge_into, spill_partial,
    merge_partials, write_all_counts, write_top_k
)


def get_peak_memory_mb():
    """Get peak memory usage in MB"""
    try:
        # On Unix systems, getrusage returns memory in KB
        usage = resource.getrusage(resource.RUSAGE_SELF)
        peak_memory_kb = usage.ru_maxrss
        # On macOS, ru_maxrss is in bytes, on Linux it's in KB
        # Try to detect: if it's > 1GB, assume bytes, else KB
        if peak_memory_kb > 1024 * 1024:
            peak_memory_mb = peak_memory_kb / (1024 * 1024)
        else:
            peak_memory_mb = peak_memory_kb / 1024
        return peak_memory_mb
    except:
        return 0.0


def run_mapreduce_with_metrics(input_dir: Path, batch_size: int, top_k: int = 20,
                               partials_dir: str = "partials",
                               output_file: str = "mapreduce_metrics.csv"):
    """
    Run MapReduce and track metrics:
    1. Runtime
    2. Peak memory
    3. Spill threshold
    """
    partdir = Path(partials_dir)
    
    # Clear stale partials
    if partdir.exists():
        for old in partdir.glob("part_*.csv"):
            try:
                old.unlink()
            except:
                pass
    partdir.mkdir(parents=True, exist_ok=True)
    
    # Track metrics
    start_time = time.time()
    start_memory = get_peak_memory_mb()
    
    # Stage A: MAP → COMBINE → batch REDUCE
    batch_counts = {}
    part_no = 0
    processed = 0
    num_spills = 0
    
    for processed, f in enumerate(input_dir.glob("*.txt"), 1):
        pairs = map_stage(f)
        local = combine_stage(pairs)
        merge_into(batch_counts, local)
        
        # Check if we need to spill
        if processed % batch_size == 0:
            part_no += 1
            num_spills += 1
            spill_partial(part_no, batch_counts, partdir)
            batch_counts.clear()
            current_memory = get_peak_memory_mb()
            print(f"Processed {processed} files... (spilled partial {part_no}, memory: {current_memory:.2f} MB)")
    
    # Spill any remainder
    if batch_counts:
        part_no += 1
        num_spills += 1
        spill_partial(part_no, batch_counts, partdir)
        batch_counts.clear()
    
    # Stage B: Final REDUCE
    final_counts = merge_partials(partdir)
    
    # Write outputs
    items = write_all_counts(Path("outputs/word_counts.csv"), final_counts)
    write_top_k(Path("outputs/top20.csv"), items, top_k)
    
    # Calculate final metrics
    end_time = time.time()
    runtime = end_time - start_time
    peak_memory = get_peak_memory_mb()
    
    # Count files processed
    num_files = processed
    
    # Prepare metrics
    metrics = {
        "runtime_seconds": runtime,
        "peak_memory_mb": peak_memory,
        "spill_threshold": batch_size,
        "num_files_processed": num_files,
        "num_spills": num_spills,
        "num_partial_files": part_no,
        "unique_words": len(final_counts),
        "total_word_count": sum(final_counts.values())
    }
    
    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=metrics.keys())
        w.writeheader()
        w.writerow(metrics)
    
    # Print summary
    print("\n" + "="*60)
    print("MAPREDUCE METRICS")
    print("="*60)
    print(f"Runtime: {runtime:.2f} seconds ({runtime/60:.2f} minutes)")
    print(f"Peak Memory: {peak_memory:.2f} MB")
    print(f"Spill Threshold: {batch_size} files per partial")
    print(f"\nProcessing Statistics:")
    print(f"  Files processed: {num_files:,}")
    print(f"  Number of spills: {num_spills}")
    print(f"  Partial files created: {part_no}")
    print(f"  Unique words: {len(final_counts):,}")
    print(f"  Total word count: {sum(final_counts.values()):,}")
    print(f"\nResults written to: {output_file}")
    print("="*60)
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Calculate MapReduce metrics")
    parser.add_argument("--input-dir", default="inputs", help="Directory of .txt files")
    parser.add_argument("--batch", type=int, default=50000, help="Spill threshold (files per partial)")
    parser.add_argument("--top-k", type=int, default=20, help="Top-K words to output")
    parser.add_argument("--partials", default="partials", help="Directory for partial CSVs")
    parser.add_argument("--output", default="mapreduce_metrics.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return
    
    run_mapreduce_with_metrics(
        input_dir=input_dir,
        batch_size=args.batch,
        top_k=args.top_k,
        partials_dir=args.partials,
        output_file=args.output
    )


if __name__ == "__main__":
    main()

