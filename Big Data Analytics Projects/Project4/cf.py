from __future__ import annotations
import pandas as pd
from collections import defaultdict
from typing import Dict, DefaultDict, Tuple
import random
from typing import List, Set, Tuple

DATA_PATH = "data/u.data"

def load_ratings(path: str = DATA_PATH) -> pd.DataFrame:
    # u.data columns: user_id, item_id, rating, timestamp (tab-separated)
    df = pd.read_csv(
        path,
        sep="\t",
        names=["user", "item", "rating", "timestamp"],
        engine="python",
    )
    return df

def quick_stats(df: pd.DataFrame) -> None:
    n_users = df["user"].nunique()
    n_items = df["item"].nunique()
    n_ratings = len(df)

    print("=== Quick Stats ===")
    print(f"Users:   {n_users}")
    print(f"Movies:  {n_items}")
    print(f"Ratings: {n_ratings}")

    print("\nRating value counts:")
    print(df["rating"].value_counts().sort_index())

    per_user = df.groupby("user")["rating"].count()
    print("\nPer-user ratings:")
    print(f"min={per_user.min()}, mean={per_user.mean():.2f}, max={per_user.max()}")

def build_maps(df: pd.DataFrame) -> Tuple[Dict[int, Dict[int, float]],
                                         Dict[int, Dict[int, float]],
                                         Dict[int, float]]:
    user_ratings: DefaultDict[int, Dict[int, float]] = defaultdict(dict)
    movie_ratings: DefaultDict[int, Dict[int, float]] = defaultdict(dict)

    # Fill maps
    for row in df.itertuples(index=False):
        u = int(row.user)
        m = int(row.item)
        r = float(row.rating)
        user_ratings[u][m] = r
        movie_ratings[m][u] = r

    # User means (for normalization + fallback prediction)
    user_mean: Dict[int, float] = {}
    for u, items in user_ratings.items():
        user_mean[u] = sum(items.values()) / len(items)

    return dict(user_ratings), dict(movie_ratings), user_mean

def sanity_check_maps(user_ratings, movie_ratings, user_mean) -> None:
    print("\n=== Map Sanity Checks ===")
    print(f"user_ratings users: {len(user_ratings)}")
    print(f"movie_ratings movies: {len(movie_ratings)}")

    # Check a couple users/movies deterministically
    sample_users = [1, 2, 943]
    for u in sample_users:
        if u in user_ratings:
            print(f"User {u}: {len(user_ratings[u])} ratings, mean={user_mean[u]:.3f}")

    sample_movies = [1, 50, 1682]
    for m in sample_movies:
        if m in movie_ratings:
            print(f"Movie {m}: {len(movie_ratings[m])} ratings")

    # Total count should equal 100000
    total = sum(len(v) for v in user_ratings.values())
    print(f"Total ratings in maps: {total}")

def make_user_holdout_split(
    user_ratings: dict[int, dict[int, float]],
    test_user_frac: float = 0.20,
    hide_frac: float = 0.20,
    seed: int = 42,
    min_visible: int = 5,
) -> tuple[
    set[int],                              # test_users
    dict[int, dict[int, float]],           # train_user_ratings (includes visible ratings for test users)
    dict[int, list[tuple[int, float]]],    # hidden_test (user -> list of (movie, true_rating))
]:
    rng = random.Random(seed)
    users = sorted(user_ratings.keys())
    n_test = int(round(test_user_frac * len(users)))
    test_users = set(rng.sample(users, n_test))

    train_user_ratings: dict[int, dict[int, float]] = {}
    hidden_test: dict[int, list[tuple[int, float]]] = {}

    for u in users:
        items = list(user_ratings[u].items())  # [(movie, rating), ...]
        if u not in test_users:
            train_user_ratings[u] = dict(items)
            continue

        # test user: hide a fraction, but keep at least min_visible ratings visible
        n_total = len(items)
        n_hide = int(round(hide_frac * n_total))
        n_hide = max(1, n_hide)
        n_hide = min(n_hide, n_total - min_visible)  # ensure enough visible

        # if user too small to satisfy min_visible, hide as much as possible but keep 1 visible
        if n_total - n_hide <= 0:
            n_hide = n_total - 1

        rng.shuffle(items)
        hidden = items[:n_hide]
        visible = items[n_hide:]

        hidden_test[u] = hidden
        train_user_ratings[u] = dict(visible)

    return test_users, train_user_ratings, hidden_test


def sanity_check_split(test_users, train_user_ratings, hidden_test) -> None:
    print("\n=== Split Sanity Checks ===")
    print(f"Test users: {len(test_users)}")
    total_hidden = sum(len(v) for v in hidden_test.values())
    print(f"Total hidden ratings: {total_hidden}")

    # verify test users exist in hidden_test
    missing = [u for u in test_users if u not in hidden_test]
    print(f"Test users missing hidden list: {len(missing)}")

    # check visible counts for a few test users
    sample = list(sorted(test_users))[:5]
    for u in sample:
        vis = len(train_user_ratings[u])
        hid = len(hidden_test[u])
        print(f"User {u}: visible={vis}, hidden={hid}")

import math
from collections import defaultdict
from typing import Dict, DefaultDict

def build_movie_map_from_user_map(
    user_ratings: dict[int, dict[int, float]]
) -> dict[int, dict[int, float]]:
    movie_ratings: DefaultDict[int, Dict[int, float]] = defaultdict(dict)
    for u, items in user_ratings.items():
        for m, r in items.items():
            movie_ratings[m][u] = r
    return dict(movie_ratings)

def compute_user_means(user_ratings: dict[int, dict[int, float]]) -> dict[int, float]:
    means: dict[int, float] = {}
    for u, items in user_ratings.items():
        means[u] = sum(items.values()) / len(items)
    return means

def compute_global_mean(user_ratings: dict[int, dict[int, float]]) -> float:
    s = 0.0
    n = 0
    for items in user_ratings.values():
        for r in items.values():
            s += r
            n += 1
    return s / n if n else 3.0

def cosine_similarity(
    u: int,
    v: int,
    user_ratings: dict[int, dict[int, float]],
    min_common: int = 2
) -> float:
    ru = user_ratings.get(u, {})
    rv = user_ratings.get(v, {})
    if not ru or not rv:
        return 0.0

    # iterate over smaller dict for speed
    if len(ru) > len(rv):
        ru, rv = rv, ru

    dot = 0.0
    nu = 0.0
    nv = 0.0
    common = 0

    for m, r_u in ru.items():
        r_v = rv.get(m)
        if r_v is None:
            continue
        common += 1
        dot += r_u * r_v
        nu += r_u * r_u
        nv += r_v * r_v

    if common < min_common:
        return 0.0
    denom = math.sqrt(nu) * math.sqrt(nv)
    return dot / denom if denom != 0 else 0.0


def pearson_similarity(
    u: int,
    v: int,
    user_ratings: dict[int, dict[int, float]],
    min_common: int = 2
) -> float:
    ru = user_ratings.get(u, {})
    rv = user_ratings.get(v, {})
    if not ru or not rv:
        return 0.0

    # collect co-rated pairs
    if len(ru) > len(rv):
        ru, rv = rv, ru
        u, v = v, u  # keep ids aligned with dicts

    pairs = []
    for m, r_u in ru.items():
        r_v = rv.get(m)
        if r_v is not None:
            pairs.append((r_u, r_v))

    n = len(pairs)
    if n < min_common:
        return 0.0

    mean_u = sum(a for a, _ in pairs) / n
    mean_v = sum(b for _, b in pairs) / n

    num = 0.0
    du = 0.0
    dv = 0.0
    for a, b in pairs:
        xa = a - mean_u
        xb = b - mean_v
        num += xa * xb
        du += xa * xa
        dv += xb * xb

    denom = math.sqrt(du) * math.sqrt(dv)
    return num / denom if denom != 0 else 0.0

def clip_rating(x: float, lo: float = 1.0, hi: float = 5.0) -> float:
    return lo if x < lo else hi if x > hi else x


def predict_user_based_knn(
    u: int,
    m: int,
    k: int,
    train_user_ratings: dict[int, dict[int, float]],
    train_movie_ratings: dict[int, dict[int, float]],
    user_mean: dict[int, float],
    global_mean: float,
    sim_fn,
    sim_cache: dict[tuple[int, int], float],
    min_sim: float = 0.0,   # set >0 to ignore weak/negative sims
) -> float:
    """
    Predict rating r(u,m) using user-based KNN on TRAINING data only.

    Normalized form:
      pred = mean_u + sum(sim(u,v) * (r(v,m) - mean_v)) / sum(|sim(u,v)|)
    Fallbacks:
      - if no neighbors: mean_u
      - if user mean missing: global mean
    """
    mean_u = user_mean.get(u, global_mean)

    # who rated movie m in training?
    raters = train_movie_ratings.get(m)
    if not raters:
        return clip_rating(mean_u)

    sims_and_devs = []
    for v, r_vm in raters.items():
        if v == u:
            continue

        key = (u, v) if u < v else (v, u)
        s = sim_cache.get(key)
        if s is None:
            s = sim_fn(u, v, train_user_ratings)
            sim_cache[key] = s

        if s <= min_sim:
            continue

        mean_v = user_mean.get(v, global_mean)
        sims_and_devs.append((s, r_vm - mean_v))

    if not sims_and_devs:
        return clip_rating(mean_u)

    # take top-k by similarity
    sims_and_devs.sort(key=lambda t: t[0], reverse=True)
    top = sims_and_devs[:k]

    num = 0.0
    den = 0.0
    for s, dev in top:
        num += s * dev
        den += abs(s)

    if den == 0.0:
        return clip_rating(mean_u)

    pred = mean_u + (num / den)
    return clip_rating(pred)


def evaluate_hidden_set(
    hidden_test: dict[int, list[tuple[int, float]]],
    k: int,
    train_user_ratings: dict[int, dict[int, float]],
    train_movie_ratings: dict[int, dict[int, float]],
    user_mean: dict[int, float],
    global_mean: float,
    sim_fn,
    min_sim: float = 0.0,
    max_examples_to_track: int = 5,
) -> tuple[
    float, float,
    list[tuple[float, int, int, float, float]],  # worst
    list[tuple[float, int, int, float, float]],  # best
]:
    sim_cache: dict[tuple[int, int], float] = {}

    se = 0.0
    n = 0
    worst: list[tuple[float, int, int, float, float]] = []
    best: list[tuple[float, int, int, float, float]] = []

    for u, hidden_list in hidden_test.items():
        for (m, true_r) in hidden_list:
            pred = predict_user_based_knn(
                u, m, k,
                train_user_ratings, train_movie_ratings,
                user_mean, global_mean,
                sim_fn, sim_cache,
                min_sim=min_sim
            )
            err = pred - true_r
            se += err * err
            n += 1

            ae = abs(err)
            worst.append((ae, u, m, true_r, pred))
            best.append((ae, u, m, true_r, pred))

    mse = se / n if n else 0.0
    rmse = math.sqrt(mse)

    worst.sort(reverse=True, key=lambda t: t[0])
    best.sort(key=lambda t: t[0])

    return mse, rmse, worst[:max_examples_to_track], best[:max_examples_to_track]


def run_experiments(
    hidden_test,
    train_user_ratings,
    train_movie_ratings,
    train_user_mean,
    global_mean
) -> None:
    ks = [5, 10, 20, 40]

    experiments = [
        ("cosine", cosine_similarity, 0.0),     # cosine is >= 0
        ("pearson>=0", pearson_similarity, 0.0) # keep only positive correlations
        # If you want: allow negatives (sometimes helps), use min_sim=-1.0
        # ("pearson_all", pearson_similarity, -1.0),
    ]

    print("\n=== Experiments (User-User KNN) ===")
    print("method,k,MSE,RMSE")
    for name, sim_fn, min_sim in experiments:
        for k in ks:
            mse, rmse, worst, best = evaluate_hidden_set(
                hidden_test,
                k=k,
                train_user_ratings=train_user_ratings,
                train_movie_ratings=train_movie_ratings,
                user_mean=train_user_mean,
                global_mean=global_mean,
                sim_fn=sim_fn,
                min_sim=min_sim,
                max_examples_to_track=3
            )
            print(f"{name},{k},{mse:.4f},{rmse:.4f}")

        # also print a couple examples for report
        mse, rmse, worst, best = evaluate_hidden_set(
            hidden_test,
            k=20,
            train_user_ratings=train_user_ratings,
            train_movie_ratings=train_movie_ratings,
            user_mean=train_user_mean,
            global_mean=global_mean,
            sim_fn=sim_fn,
            min_sim=min_sim,
            max_examples_to_track=3
        )
        print(f"\nExamples for {name} (k=20):")
        print("  Best (abs_err, user, movie, true, pred):")
        for ex in best:
            print("   ", ex)
        print("  Worst (abs_err, user, movie, true, pred):")
        for ex in worst:
            print("   ", ex)

def load_movie_titles(path: str = "data/u.item") -> dict[int, str]:
    import pandas as pd
    df = pd.read_csv(path, sep="|", header=None, encoding="latin-1", engine="python")
    # col 0 = movie id, col 1 = title
    return {int(row[0]): str(row[1]) for row in df[[0,1]].itertuples(index=False)}

import math

def adjusted_cosine_item_sim(i, j, train_movie_ratings, user_mean, global_mean, min_common=2):
    """
    Adjusted cosine similarity between items i and j:
    center each user's ratings by that user's mean before computing cosine.
    """
    ri = train_movie_ratings.get(i, {})
    rj = train_movie_ratings.get(j, {})
    if not ri or not rj:
        return 0.0

    # iterate over smaller dict for speed
    if len(ri) > len(rj):
        ri, rj = rj, ri
        i, j = j, i

    num = 0.0
    di = 0.0
    dj = 0.0
    common = 0

    for u, r_ui in ri.items():
        r_uj = rj.get(u)
        if r_uj is None:
            continue
        common += 1
        mu = user_mean.get(u, global_mean)
        xi = r_ui - mu
        xj = r_uj - mu
        num += xi * xj
        di += xi * xi
        dj += xj * xj

    if common < min_common:
        return 0.0

    denom = math.sqrt(di) * math.sqrt(dj)
    return (num / denom) if denom != 0.0 else 0.0


def predict_item_item_knn(u, target_m, k,
                         train_user_ratings, train_movie_ratings,
                         user_mean, global_mean,
                         sim_cache, min_sim=0.0):
    """
    Predict r(u, target_m) using item-item KNN:
    - compute similarity between target_m and each movie the user rated
    - take top-k by similarity
    - weighted average of the user's ratings
    """
    ru = train_user_ratings.get(u)
    if not ru:
        return max(1.0, min(5.0, global_mean))

    mean_u = user_mean.get(u, global_mean)

    sims = []
    for m_j, r_uj in ru.items():
        if m_j == target_m:
            continue

        key = (target_m, m_j) if target_m < m_j else (m_j, target_m)
        s = sim_cache.get(key)
        if s is None:
            s = adjusted_cosine_item_sim(target_m, m_j, train_movie_ratings, user_mean, global_mean)
            sim_cache[key] = s

        if s <= min_sim:
            continue
        sims.append((s, r_uj))

    if not sims:
        return max(1.0, min(5.0, mean_u))

    sims.sort(key=lambda x: x[0], reverse=True)
    top = sims[:k]

    num = 0.0
    den = 0.0
    for s, r in top:
        num += s * r
        den += abs(s)

    if den == 0.0:
        return max(1.0, min(5.0, mean_u))

    pred = num / den
    return max(1.0, min(5.0, pred))


def eval_item_item(hidden_test, k,
                   train_user_ratings, train_movie_ratings,
                   user_mean, global_mean,
                   titles=None):
    """
    Returns (mse, rmse, best_examples, worst_examples)
    """
    sim_cache = {}
    se = 0.0
    n = 0
    examples = []

    for u, hidden_list in hidden_test.items():
        for m, true_r in hidden_list:
            pred = predict_item_item_knn(
                u, m, k,
                train_user_ratings, train_movie_ratings,
                user_mean, global_mean,
                sim_cache
            )
            err = pred - true_r
            ae = abs(err)
            se += err * err
            n += 1
            if titles is not None:
                examples.append((ae, u, m, titles.get(m, "UNKNOWN"), true_r, pred))
            else:
                examples.append((ae, u, m, true_r, pred))

    mse = se / n
    rmse = math.sqrt(mse)

    examples.sort(key=lambda x: x[0])
    best = examples[:3]
    worst = examples[-3:][::-1]
    return mse, rmse, best, worst


def run_item_item_experiments(hidden_test,
                              train_user_ratings, train_movie_ratings,
                              user_mean, global_mean,
                              titles):
    print("\n=== Bonus: Item-Item KNN (Adjusted Cosine) ===")
    print("method,k,MSE,RMSE")
    for k in [5, 10, 20, 40]:
        mse, rmse, best, worst = eval_item_item(
            hidden_test, k,
            train_user_ratings, train_movie_ratings,
            user_mean, global_mean,
            titles=titles
        )
        print(f"item_adjcos,{k},{mse:.4f},{rmse:.4f}")

    # show best/worst for best k (=40)
    mse, rmse, best, worst = eval_item_item(
        hidden_test, 40,
        train_user_ratings, train_movie_ratings,
        user_mean, global_mean,
        titles=titles
    )
    print(f"\nExamples for item_adjcos (k=40): MSE={mse:.4f}, RMSE={rmse:.4f}")
    print("  Best:")
    for ex in best:
        ae, u, m, title, tr, pr = ex
        print(f"    (abs_err={ae:.3f}) user={u}, movie={m} ({title}), true={tr}, pred={pr:.3f}")
    print("  Worst:")
    for ex in worst:
        ae, u, m, title, tr, pr = ex
        print(f"    (abs_err={ae:.3f}) user={u}, movie={m} ({title}), true={tr}, pred={pr:.3f}")


def main():
    # Step 1: load ratings + quick stats
    ratings = load_ratings()
    quick_stats(ratings)

    # (Optional) movie titles for nicer examples
    titles = load_movie_titles()

    # Step 2: build full maps (sanity checks)
    user_ratings, movie_ratings, user_mean_full = build_maps(ratings)
    sanity_check_maps(user_ratings, movie_ratings, user_mean_full)

    # Step 3: make required split
    test_users, train_user_ratings, hidden_test = make_user_holdout_split(
        user_ratings,
        test_user_frac=0.20,
        hide_frac=0.20,
        seed=42,
        min_visible=5
    )
    sanity_check_split(test_users, train_user_ratings, hidden_test)

    # Step 4: build TRAINING-only maps + means (no leakage)
    train_movie_ratings = build_movie_map_from_user_map(train_user_ratings)
    train_user_mean = compute_user_means(train_user_ratings)
    global_mean = compute_global_mean(train_user_ratings)
    run_item_item_experiments(hidden_test, train_user_ratings, train_movie_ratings, train_user_mean, global_mean, titles)

    print("\n=== Training Map Checks ===")
    print(f"Train users: {len(train_user_ratings)} (should be 943)")
    print(f"Train movies: {len(train_movie_ratings)} (<= 1682)")
    print(f"Global mean (train): {global_mean:.4f}")

    # quick similarity sanity
    u, v = 4, 7
    print(f"\nSim check users {u} vs {v}:")
    print(f"cosine  = {cosine_similarity(u, v, train_user_ratings):.4f}")
    print(f"pearson = {pearson_similarity(u, v, train_user_ratings):.4f}")

    # Step 6: experiments (k sweep + cosine vs pearson)
    run_experiments(
        hidden_test,
        train_user_ratings,
        train_movie_ratings,
        train_user_mean,
        global_mean
    )

    # Report-friendly: show one best + one worst with titles for best config
    print("\n=== Report Examples (best config: pearson>=0, k=40) ===")
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
    print(f"pearson>=0, k=40: MSE={mse:.4f}, RMSE={rmse:.4f}")

    ae, uu, mm, true_r, pred = best[0]
    print("\nNailed it:")
    print(f"user={uu}, movie={mm} ({titles.get(mm, 'UNKNOWN')}), true={true_r}, pred={pred:.3f}, abs_err={ae:.3f}")

    ae, uu, mm, true_r, pred = worst[0]
    print("\nWay off:")
    print(f"user={uu}, movie={mm} ({titles.get(mm, 'UNKNOWN')}), true={true_r}, pred={pred:.3f}, abs_err={ae:.3f}")


if __name__ == "__main__":
    main()

