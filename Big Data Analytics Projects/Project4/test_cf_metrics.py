#!/usr/bin/env python3
"""
Test script to generate Collaborative Filtering metrics:
- Baseline improvement %
- Test split information

Usage:
  python test_cf_metrics.py
"""

import sys
import os
import csv
import math

# Import from cf.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import (
    load_ratings, build_maps, make_user_holdout_split,
    build_movie_map_from_user_map, compute_user_means, compute_global_mean,
    evaluate_hidden_set, pearson_similarity, cosine_similarity
)


def calculate_cf_metrics(output_file: str = "cf_metrics.csv"):
    """
    Calculate and output CF metrics:
    1. Baseline improvement %
    2. Test split information
    """
    # Load data
    ratings = load_ratings()
    
    # Build full maps
    user_ratings, movie_ratings, user_mean_full = build_maps(ratings)
    
    # Make test split
    test_users, train_user_ratings, hidden_test = make_user_holdout_split(
        user_ratings,
        test_user_frac=0.20,
        hide_frac=0.20,
        seed=42,
        min_visible=5
    )
    
    # Build training-only maps
    train_movie_ratings = build_movie_map_from_user_map(train_user_ratings)
    train_user_mean = compute_user_means(train_user_ratings)
    global_mean = compute_global_mean(train_user_ratings)
    
    # Calculate baseline RMSE (predicting global mean)
    baseline_se = 0.0
    baseline_n = 0
    for u, hidden_list in hidden_test.items():
        for m, true_r in hidden_list:
            err = global_mean - true_r
            baseline_se += err * err
            baseline_n += 1
    baseline_rmse = math.sqrt(baseline_se / baseline_n) if baseline_n > 0 else 0.0
    
    # Evaluate best model (pearson, k=40)
    mse, rmse, worst, best = evaluate_hidden_set(
        hidden_test,
        k=40,
        train_user_ratings=train_user_ratings,
        train_movie_ratings=train_movie_ratings,
        user_mean=train_user_mean,
        global_mean=global_mean,
        sim_fn=pearson_similarity,
        min_sim=0.0,
        max_examples_to_track=5
    )
    
    # Calculate improvement
    improvement_pct = (baseline_rmse - rmse) / baseline_rmse * 100 if baseline_rmse > 0 else 0.0
    
    # Calculate test split statistics
    total_users = len(user_ratings)
    num_test_users = len(test_users)
    num_train_users = len(train_user_ratings)
    
    total_hidden_ratings = sum(len(v) for v in hidden_test.values())
    total_train_ratings = sum(len(v) for v in train_user_ratings.values())
    total_ratings = len(ratings)
    
    test_split_pct = (num_test_users / total_users) * 100 if total_users > 0 else 0.0
    hidden_ratings_pct = (total_hidden_ratings / total_ratings) * 100 if total_ratings > 0 else 0.0
    
    # Prepare metrics
    metrics = {
        "baseline_rmse": baseline_rmse,
        "best_model_rmse": rmse,
        "baseline_improvement_pct": improvement_pct,
        "best_model": "pearson_k40",
        "total_users": total_users,
        "test_users": num_test_users,
        "train_users": num_train_users,
        "test_split_pct": test_split_pct,
        "total_ratings": total_ratings,
        "train_ratings": total_train_ratings,
        "hidden_test_ratings": total_hidden_ratings,
        "hidden_ratings_pct": hidden_ratings_pct,
        "global_mean": global_mean
    }
    
    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=metrics.keys())
        w.writeheader()
        w.writerow(metrics)
    
    # Print summary
    print("\n" + "="*60)
    print("COLLABORATIVE FILTERING METRICS")
    print("="*60)
    print(f"\nTest Split Information:")
    print(f"  Total users: {total_users}")
    print(f"  Test users: {num_test_users} ({test_split_pct:.1f}%)")
    print(f"  Train users: {num_train_users}")
    print(f"  Total ratings: {total_ratings:,}")
    print(f"  Train ratings: {total_train_ratings:,}")
    print(f"  Hidden test ratings: {total_hidden_ratings:,} ({hidden_ratings_pct:.2f}%)")
    
    print(f"\nBaseline Performance:")
    print(f"  Baseline RMSE (global mean): {baseline_rmse:.4f}")
    
    print(f"\nBest Model Performance:")
    print(f"  Model: Pearson similarity, k=40")
    print(f"  RMSE: {rmse:.4f}")
    
    print(f"\nBaseline Improvement:")
    print(f"  Improvement: {improvement_pct:.2f}%")
    print(f"  (Lower RMSE is better, so positive improvement means better performance)")
    
    print(f"\nResults written to: {output_file}")
    print("="*60)
    
    return metrics


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Calculate CF metrics")
    parser.add_argument("--output", default="cf_metrics.csv", help="Output CSV file")
    args = parser.parse_args()
    
    calculate_cf_metrics(args.output)


if __name__ == "__main__":
    main()

