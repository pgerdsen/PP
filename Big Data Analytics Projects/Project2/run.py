#!/usr/bin/env python3
"""
DSCI-D 351 – Project 2: Locality-Sensitive Hashing (LSH)
Minimal, single-file implementation (no external LSH/minhash libs).

Usage examples:
  python run.py --file similarity.txt --k 3 --num-perm 100 --bands 20 --rows 5 --top 5
  python run.py --file "similarity (2).txt" --k 5 --num-perm 200 --bands 25 --rows 8 --top 10
  python run.py --file similarity.txt --sweep  

Outputs:
  - top_pairs.csv : CSV of the top-N most similar paragraph pairs (by exact Jaccard on shingles)
  - prints summary stats and example pairs to stdout

Notes:
  - Bands * rows must equal num-perm (hash functions).
  - Paragraphs are split on blank lines (>=1 empty line). Each paragraph becomes one document.
  - Word-shingle Jaccard is used for exact similarity; signature agreement gives an estimate.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import os
import random
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

# Utilities 

def read_paragraphs(path: str) -> List[str]:
    """Read the dataset and split into paragraphs by blank lines.
    Tries a few fallback filenames if the provided path doesn't exist.
    """
    candidates = [path, os.path.basename(path), "similarity.txt", "similarity (2).txt"]
    for p in candidates:
        if os.path.exists(p):
            path = p
            break
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find dataset. Tried: {candidates}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    # Normalize Windows newlines and trim
    raw = raw.replace("\r\n", "\n").strip()
    # Split on 1+ blank lines
    paras = re.split(r"\n\s*\n+", raw)
    # Strip whitespace per paragraph
    paras = [p.strip() for p in paras if p.strip()]
    return paras


def normalize_text(s: str) -> str:
    """Lowercase, strip punctuation (keep apostrophes inside words), collapse whitespace."""
    s = s.lower()
    # Replace fancy quotes/dashes
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("—", "-")
    # Keep alphanumerics and spaces; keep internal apostrophes in tokens (e.g., don't -> dont)
    s = re.sub(r"[^a-z0-9'\s-]", " ", s)  # drop punctuation to spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def word_shingles(tokens: List[str], k: int) -> Set[Tuple[str, ...]]:
    if k <= 0:
        raise ValueError("k must be positive")
    return {tuple(tokens[i:i+k]) for i in range(0, max(0, len(tokens)-k+1))}


def tokenize(s: str) -> List[str]:
    return s.split()

# Deterministic 64-bit hashing for shingles and band buckets

def stable_hash64(x: bytes) -> int:
    return int(hashlib.blake2b(x, digest_size=8).hexdigest(), 16)


# Minhash:
@dataclass
class MinHasher:
    num_perm: int
    seed: int = 42
    # Large prime for universal hashing
    _prime: int = (1 << 61) - 1  # a big 61-bit prime

    def __post_init__(self):
        random.seed(self.seed)
        # Generate (a, b) pairs for universal hash functions
        self.a = [random.randrange(1, self._prime - 1) for _ in range(self.num_perm)]
        self.b = [random.randrange(0, self._prime - 1) for _ in range(self.num_perm)]

    def _hash_shingle_id(self, shingle_id: int, j: int) -> int:
        # h_j(x) = (a_j * x + b_j) mod prime
        return (self.a[j] * shingle_id + self.b[j]) % self._prime

    def signature(self, shingle_ids: Iterable[int]) -> List[int]:
        sig = [sys.maxsize] * self.num_perm
        for sid in shingle_ids:
            for j in range(self.num_perm):
                hj = self._hash_shingle_id(sid, j)
                if hj < sig[j]:
                    sig[j] = hj
        return sig

# LSH (banding):

def lsh_candidates(signatures: List[List[int]], bands: int, rows: int, seed: int = 1234) -> Set[Tuple[int,int]]:
    assert bands * rows == len(signatures[0]), "bands * rows must equal signature length"
    random.seed(seed)
    num_docs = len(signatures)
    buckets: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for doc_id, sig in enumerate(signatures):
        for b in range(bands):
            start = b * rows
            band = tuple(sig[start:start + rows])
            # hash band with band index to avoid cross-band collisions
            band_bytes = (str(b).encode() + b"|" + ",".join(map(str, band)).encode())
            key = (b, stable_hash64(band_bytes))
            buckets[key].append(doc_id)
    # Generate candidate pairs from buckets with >=2 docs
    cand_pairs: Set[Tuple[int,int]] = set()
    for docs in buckets.values():
        if len(docs) >= 2:
            docs_sorted = sorted(set(docs))
            for i in range(len(docs_sorted)):
                for j in range(i+1, len(docs_sorted)):
                    cand_pairs.add((docs_sorted[i], docs_sorted[j]))
    return cand_pairs

# Similarities:

def jaccard(a: Set[int], b: Set[int]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def est_from_signatures(sigA: List[int], sigB: List[int]) -> float:
    matches = sum(1 for x, y in zip(sigA, sigB) if x == y)
    return matches / len(sigA)

# Pipeline:
@dataclass
class LSHConfig:
    k: int = 3
    num_perm: int = 100
    bands: int = 20
    rows: int = 5
    seed: int = 42
    top: int = 5


@dataclass
class DocData:
    text: str
    norm: str
    tokens: List[str]
    shingles: Set[Tuple[str, ...]]
    shingle_ids: Set[int]


def build_docs(paragraphs: List[str], k: int) -> Tuple[List[DocData], Dict[Tuple[str,...], int]]:
    docs: List[DocData] = []
    shingle_id_map: Dict[Tuple[str,...], int] = {}
    next_id = 0

    for p in paragraphs:
        norm = normalize_text(p)
        toks = tokenize(norm)
        sh = word_shingles(toks, k)
        ids: Set[int] = set()
        for shingle in sh:
            if shingle not in shingle_id_map:
                shingle_id_map[shingle] = next_id
                next_id += 1
            ids.add(shingle_id_map[shingle])
        docs.append(DocData(text=p, norm=norm, tokens=toks, shingles=sh, shingle_ids=ids))
    return docs, shingle_id_map


def run_lsh(paragraphs: List[str], cfg: LSHConfig):
    t0 = time.time()
    docs, shingle_map = build_docs(paragraphs, cfg.k)
    build_t = time.time() - t0

    mh = MinHasher(cfg.num_perm, seed=cfg.seed)
    sigs: List[List[int]] = [mh.signature(d.shingle_ids) for d in docs]
    sig_t = time.time() - t0 - build_t

    cands = lsh_candidates(sigs, cfg.bands, cfg.rows)
    lsh_t = time.time() - t0 - build_t - sig_t

    # Score candidates with exact Jaccard and estimated similarity
    scored: List[Tuple[int, int, float, float]] = []
    for i, j in cands:
        jac = jaccard(docs[i].shingle_ids, docs[j].shingle_ids)
        est = est_from_signatures(sigs[i], sigs[j])
        scored.append((i, j, jac, est))
    scored.sort(key=lambda x: (x[2], x[3]), reverse=True)

    # Write CSV of top pairs
    import csv
    with open("top_pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["doc_i", "doc_j", "jaccard", "est_sig_sim", "len_i", "len_j"]) 
        for i, (di, dj, jac, est) in enumerate(scored[: cfg.top]):
            w.writerow([di, dj, f"{jac:.4f}", f"{est:.4f}", len(docs[di].tokens), len(docs[dj].tokens)])

    # Pretty-print sample results
    print("\n===== LSH Summary =====")
    print(f"Docs: {len(docs)} | Unique shingles: {len(shingle_map)} | k={cfg.k}")
    print(f"num_perm={cfg.num_perm}, bands={cfg.bands}, rows={cfg.rows} (bands*rows={cfg.bands*cfg.rows})")
    print(f"Times: build={build_t:.2f}s, sig={sig_t:.2f}s, lsh={lsh_t:.2f}s, total={time.time()-t0:.2f}s")
    print(f"Candidates generated: {len(cands)}")

    def preview(idx: int, width: int = 120) -> str:
        t = re.sub(r"\s+", " ", docs[idx].text.strip())
        return (t[: width] + ("..." if len(t) > width else ""))

    print("\nTop pairs (by exact Jaccard on word-shingles):")
    for di, dj, jac, est in scored[: cfg.top]:
        print(f"  ({di:4d}, {dj:4d})  Jaccard={jac:.3f}  est={est:.3f}")
        print(f"    i: {preview(di)}")
        print(f"    j: {preview(dj)}")

    return scored, docs, sigs


# Experiment Sweeps: 

def sweep_experiments(paragraphs: List[str]):
    """Run a few default experiments to help answer the report questions.
    - k in {3, 5}
    - num_perm in {50, 100, 200} with a reasonable (bands, rows) factorization
    Prints summary lines and writes CSV files per setting.
    """
    settings = []
    # Factorizations for each num_perm: prefer ~5-10 rows per band
    fact = {50: (10,5), 100: (20,5), 200: (25,8)}
    for k in (3, 5):
        for num_perm in (50, 100, 200):
            bands, rows = fact[num_perm]
            settings.append(LSHConfig(k=k, num_perm=num_perm, bands=bands, rows=rows, top=5))

    print("\n===== Parameter Sweep =====")
    for cfg in settings:
        print(f"\n-- k={cfg.k}, num_perm={cfg.num_perm}, bands={cfg.bands}, rows={cfg.rows} --")
        start = time.time()
        scored, docs, sigs = run_lsh(paragraphs, cfg)
        elapsed = time.time() - start
        # Simple accuracy proxy: average |est - exact|
        if scored:
            mae = sum(abs(est - jac) for _,_,jac,est in scored[:cfg.top]) / min(cfg.top, len(scored))
        else:
            mae = float('nan')
        print(f"Runtime={elapsed:.2f}s | Top{cfg.top} MAE(|est-exact|)≈{mae:.3f}")


# CLI:

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Minimal LSH pipeline for similar paragraphs")
    ap.add_argument("--file", default="similarity.txt", help="Path to dataset (paragraphs)")
    ap.add_argument("--k", type=int, default=3, help="Word-shingle size k (e.g., 3 or 5)")
    ap.add_argument("--num-perm", type=int, default=100, help="Number of minhash functions")
    ap.add_argument("--bands", type=int, default=20, help="Number of bands (bands*rows=num_perm)")
    ap.add_argument("--rows", type=int, default=5, help="Rows per band (bands*rows=num_perm)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    ap.add_argument("--top", type=int, default=5, help="Top-N pairs to output")
    ap.add_argument("--sweep", action="store_true", help="Run a small parameter sweep (k and num_perm)")
    return ap.parse_args()


def main():
    args = parse_args()
    paragraphs = read_paragraphs(args.file)
    if args.sweep:
        sweep_experiments(paragraphs)
    else:
        cfg = LSHConfig(k=args.k, num_perm=args.num_perm, bands=args.bands, rows=args.rows,
                        seed=args.seed, top=args.top)
        run_lsh(paragraphs, cfg)


if __name__ == "__main__":
    main()

