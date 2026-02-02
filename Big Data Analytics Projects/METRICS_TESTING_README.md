# Metrics Testing Guide

This document explains how to run the test files to generate metrics for your portfolio projects.

## LSH Metrics (Project 2)

**File:** `Project2/test_lsh_metrics.py`

**Metrics Generated:**
- % comparison reduction
- MAE (Mean Absolute Error) over X pairs

**Usage:**
```bash
cd "Big Data Analytics Projects/Project2"
python test_lsh_metrics.py --file similarity.txt --k 3 --num-perm 100 --bands 20 --rows 5
```

**Output:** `lsh_metrics.csv` containing:
- `comparison_reduction_pct`: Percentage reduction in comparisons
- `mae_over_pairs`: Mean absolute error between estimated and exact Jaccard similarity
- `num_pairs_evaluated`: Number of pairs used for MAE calculation
- Additional configuration and runtime metrics

## Collaborative Filtering Metrics (Project 4)

**File:** `Project4/test_cf_metrics.py`

**Metrics Generated:**
- Baseline improvement %
- Test split information

**Usage:**
```bash
cd "Big Data Analytics Projects/Project4"
python test_cf_metrics.py
```

**Output:** `cf_metrics.csv` containing:
- `baseline_improvement_pct`: Percentage improvement over baseline (global mean prediction)
- `test_split_pct`: Percentage of users in test set
- `hidden_ratings_pct`: Percentage of ratings in hidden test set
- Additional split statistics and performance metrics

## MapReduce Metrics (Project 1)

**File:** `Project1/test_mapreduce_metrics.py`

**Metrics Generated:**
- Runtime (seconds)
- Peak memory usage (MB)
- Spill threshold

**Usage:**
```bash
cd "Big Data Analytics Projects/Project1"
python test_mapreduce_metrics.py --input-dir inputs --batch 50000
```

**Output:** `mapreduce_metrics.csv` containing:
- `runtime_seconds`: Total execution time
- `peak_memory_mb`: Peak memory usage during execution
- `spill_threshold`: Number of files processed before spilling to disk
- Additional processing statistics

## Apriori Metrics (Project 3)

**File:** `Project3/test_apriori_metrics.py`

**Metrics Generated:**
- Runtime (seconds)
- Peak memory usage (MB)
- Number of frequent itemsets
- Number of association rules

**Usage:**
```bash
cd "Big Data Analytics Projects/Project3"
python3 test_apriori_metrics.py
```

**Output:** `apriori_metrics.csv` containing:
- `runtime_sec`: Total execution time
- `peak_memory_mb`: Peak memory usage during execution
- `num_transactions`: Number of market baskets processed
- `frequent_itemsets`: Count of itemsets above min_support threshold
- `max_itemset_size`: Largest itemset size found
- `num_rules`: Association rules generated
- `top_itemsets`: Top 5 itemsets by support
- `top_rules`: Top 3 rules by interestingness

## Notes

- All test files generate CSV output files with the metrics
- The scripts also print a summary to the console
- Make sure you have the required data files in place before running:
  - Project1: `data:/plain_v2/` directory with `.txt` files (run `parse_enron.py` first)
  - Project2: `similarity.txt` (or specify with `--file`)
  - Project3: `Groceries_dataset.csv` (from Kaggle)
  - Project4: `data:/u.data` and `data:/u.item`

