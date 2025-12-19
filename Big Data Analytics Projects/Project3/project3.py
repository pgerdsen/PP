import pandas as pd

def load_transactions(path="Groceries_dataset.csv"):
    """
    Load the groceries dataset and convert it into a list of transactions.
    Each transaction = all items bought by a member on a given date.
    """
    df = pd.read_csv(path)

    print("Columns in CSV:", df.columns.tolist())

    # Group by (Member_number, Date) so each row in 'transactions'
    # is a basket: list of itemDescription strings.
    grouped = (
        df.groupby(["Member_number", "Date"])["itemDescription"]
          .apply(list)
          .tolist()
    )

    return grouped

import itertools
import math
from collections import defaultdict

def apriori(transactions, min_support=0.005):
    """
    Basic Apriori implementation.
    Returns:
      support_counts: dict[frozenset -> int]
      support:        dict[frozenset -> float]
    """
    n_trans = len(transactions)
    min_count = math.ceil(min_support * n_trans)

    # L1: frequent 1-itemsets
    item_counts = defaultdict(int)
    for basket in transactions:
        for item in set(basket):  # set() to avoid duplicates in same basket
            item_counts[frozenset([item])] += 1

    Lk = {i for i, c in item_counts.items() if c >= min_count}
    support_counts = {i: item_counts[i] for i in Lk}

    k = 2
    # Lk for k >= 2
    while Lk:
        Lk_list = list(Lk)
        candidates = set()

        # Join step: generate candidate k-itemsets
        for i in range(len(Lk_list)):
            for j in range(i + 1, len(Lk_list)):
                union = Lk_list[i] | Lk_list[j]
                if len(union) == k:
                    # Prune: all (k-1)-subsets must be frequent
                    if all(frozenset(sub) in Lk
                           for sub in itertools.combinations(union, k - 1)):
                        candidates.add(union)

        # Count candidates
        cand_counts = defaultdict(int)
        for basket in transactions:
            bset = set(basket)
            for cand in candidates:
                if cand.issubset(bset):
                    cand_counts[cand] += 1

        # Keep frequent ones
        Lk = {c for c, cnt in cand_counts.items() if cnt >= min_count}
        for c in Lk:
            support_counts[c] = cand_counts[c]

        k += 1

    support = {s: cnt / n_trans for s, cnt in support_counts.items()}
    return support_counts, support


def generate_rules(support_counts, support, min_confidence=0.0):
    """
    Generate association rules from frequent itemsets.
    For this project, we don't enforce a 0.3 confidence cutoff.
    We care about interestingness = |conf - prior|.
    """
    rules = []

    for itemset in support:
        if len(itemset) < 2:
            continue  # can't form a rule from 1-itemset

        for r in range(1, len(itemset)):
            for lhs_tuple in itertools.combinations(itemset, r):
                lhs = frozenset(lhs_tuple)
                rhs = itemset - lhs

                supp_itemset = support[itemset]
                supp_lhs = support.get(lhs, 0.0)
                supp_rhs = support.get(rhs, 0.0)

                if supp_lhs == 0 or supp_rhs == 0:
                    continue

                conf = supp_itemset / supp_lhs
                if conf < min_confidence:
                    continue

                prior = supp_rhs
                interestingness = abs(conf - prior)

                rules.append({
                    "lhs": lhs,
                    "rhs": rhs,
                    "support": supp_itemset,
                    "confidence": conf,
                    "prior": prior,
                    "interestingness": interestingness,
                })

    # Sort by interestingness descending
    rules.sort(key=lambda r: r["interestingness"], reverse=True)
    return rules


def main():
    transactions = load_transactions("Groceries_dataset.csv")
    print("Number of transactions:", len(transactions))
    print("First basket (up to 10 items):", transactions[0][:10])

    # Run Apriori with min_support = 0.005 (as required)
    support_counts, support = apriori(transactions, min_support=0.005)
    print("Total frequent itemsets:", len(support_counts))

    # Show that we only get 1- and 2-itemsets
    max_size = max(len(s) for s in support_counts)
    print("Max frequent itemset size:", max_size)

    # Top 10 frequent itemsets by support
    top_itemsets = sorted(support.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 frequent itemsets:")
    for itemset, supp in top_itemsets:
        print(f"{set(itemset)}  support={supp:.4f}")

    # Generate rules, but don't filter by high confidence
    rules = generate_rules(support_counts, support, min_confidence=0.0)
    print("\nNumber of rules generated:", len(rules))

    print("\nTop 5 rules by interestingness:")
    for r in rules[:5]:
        print(
            f"{set(r['lhs'])} -> {set(r['rhs'])} | "
            f"support={r['support']:.4f}, "
            f"conf={r['confidence']:.3f}, "
            f"prior={r['prior']:.3f}, "
            f"|conf-prior|={r['interestingness']:.3f}"
        )

if __name__ == "__main__":
    main()

