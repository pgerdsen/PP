#!/usr/bin/env python3
"""
Project 1 — Enron Word Count
Entry script:

MAP emits (word, 1) pairs per file
- SHUFFLE/COMBINE aggregates per-file term frequencies (true TF) using dict
- REDUCE is two-stage: (A) batch accumulator spilled to CSV "partials",
  then (B) final global merge over all partial CSVs
- Outputs:
    - outputs/top20.csv        (header + Top-K rows)
    - outputs/word_counts.csv  (full vocabulary, sorted by count desc)

Usage
  python3 main_mapreduce.py
  python3 main_mapreduce.py --input-dir inputs --top-k 20 --batch 50000

Assumptions:
- ./inputs/ contains many .txt email bodies (e.g., symlink to data/plain_v2)
- No external dependencies beyond the standard library
"""

from pathlib import Path
import argparse, re, csv

# ---------- Cleaning & tokenization ----------
# We remove addresses/URLs/domains/non-ASCII first, then tokenize on letters/apostrophes.
EMAIL_RE  = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE    = re.compile(r"https?://\S+|www\.\S+")
DOMAIN_RE = re.compile(r"\b[A-Za-z0-9.-]+\.(com|net|org|gov|edu)\b")
NONASCII  = re.compile(r"[^\x00-\x7F]+")
TOKEN     = re.compile(r"[A-Za-z']+")

# General stopwords plus Enron-specific boilerplate (months/days, org tokens).
BASE_STOP = set("""
the and for that you with this have from are was not but all your can has any our will its
they there their been were what who when how why subject fw re http www com
""".split())
EXTRA_STOP = set("""
enron ect hou corp message mail email mailto pm am
january february march april may june july august september october november december
mon tue wed thu thur thurs fri sat sun monday tuesday wednesday thursday friday saturday sunday
""".split())
STOP = BASE_STOP | EXTRA_STOP


def clean_text(t: str) -> str:
    """
    Normalize text before tokenization:
    - lowercase
    - strip emails/URLs/domains
    - strip non-ASCII artifacts from HTML decodes, etc.
    """
    t = t.lower()
    t = EMAIL_RE.sub(" ", t)
    t = URL_RE.sub(" ", t)
    t = DOMAIN_RE.sub(" ", t)
    t = NONASCII.sub(" ", t)
    return t


# ---------- MAP ----------
def map_stage(path: Path):
    """
    MAP: Read one file and emit a list of (word, 1) pairs.
    We intentionally emit unit counts to mirror classic MapReduce examples.
    """
    try:
        text = clean_text(path.read_text("utf-8", errors="ignore"))
    except Exception:
        return []
    pairs = []
    for w in TOKEN.findall(text):
        if len(w) > 2 and w not in STOP:
            pairs.append((w, 1))
    return pairs


# ---------- SHUFFLE / COMBINE ----------
def combine_stage(pairs):
    """
    SHUFFLE/COMBINE (local, per-file):
    Convert [(word, 1), (word, 1), ...] into a local dict[word] = tf_in_this_file.
    This reduces volume before sending to the global reducer.
    """
    local = {}
    for w, _ in pairs:
        local[w] = local.get(w, 0) + 1  # true term frequency inside this file
    return local  # dict[str,int]


# ---------- REDUCE helpers ----------
def merge_into(accum: dict, local: dict) -> None:
    """
    In-memory reducer: add local (per-file) counts into a batch accumulator.
    """
    for w, c in local.items():
        accum[w] = accum.get(w, 0) + c


def spill_partial(part_no: int, counts: dict, outdir: Path) -> None:
    """
    Spill a batch accumulator to CSV:
      partials/part_0001.csv, each line: word,count
    Rationale: keeps memory bounded and makes the reduce explicitly multi-stage.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    outp = outdir / f"part_{part_no:04d}.csv"
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for k, v in counts.items():
            w.writerow([k, v])


def merge_partials(partdir: Path) -> dict:
    """
    Final REDUCE: read all partial CSVs and sum counts per word into a global dict.
    """
    total = {}
    for p in sorted(partdir.glob("part_*.csv")):
        with open(p, newline="", encoding="utf-8") as fh:
            r = csv.reader(fh)
            for row in r:
                if len(row) != 2:
                    continue
                k, v = row[0], int(row[1])
                total[k] = total.get(k, 0) + v
    return total


def write_all_counts(all_csv: Path, counts: dict):
    """
    Write full vocabulary sorted by count descending, then word ascending (stable tie-break).
    Returns the sorted list for reuse when writing Top-K.
    """
    all_csv.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    with open(all_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["word", "count"])
        for k, v in items:
            w.writerow([k, v])
    return items


def write_top_k(top_csv: Path, items, k: int) -> None:
    """
    Write the top-K rows (header + K).
    """
    top_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(top_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["word", "count"])
        for k_v in items[:k]:
            w.writerow(k_v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="inputs", help="Directory of .txt emails (e.g., inputs -> data/plain_v2)")
    ap.add_argument("--top-k", type=int, default=20, help="How many top words to write")
    ap.add_argument("--top20", default="outputs/top20.csv", help="Path to write the top-K CSV")
    ap.add_argument("--all",   default="outputs/word_counts.csv", help="Path to write the full vocabulary CSV")
    ap.add_argument("--partials", default="partials", help="Directory to store partial spilled CSVs")
    ap.add_argument("--batch", type=int, default=50000, help="Spill a partial after N files")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    partdir = Path(args.partials)

    # Safety: clear stale partials so re-runs don't double-count
    if partdir.exists():
        for old in partdir.glob("part_*.csv"):
            try:
                old.unlink()
            except:
                pass
    partdir.mkdir(parents=True, exist_ok=True)

    # Stage A: MAP → COMBINE → batch REDUCE; spill partials every --batch files
    batch_counts = {}
    part_no = 0
    processed = 0

    for processed, f in enumerate(in_dir.glob("*.txt"), 1):
        pairs = map_stage(f)           # MAP: emit (word,1) pairs
        local = combine_stage(pairs)   # COMBINE: per-file TF dict
        merge_into(batch_counts, local)
        if processed % args.batch == 0:
            part_no += 1
            spill_partial(part_no, batch_counts, partdir)
            batch_counts.clear()
            print(f"processed {processed} files... (spilled partial {part_no})")

    # Spill any remainder
    if batch_counts:
        part_no += 1
        spill_partial(part_no, batch_counts, partdir)
        batch_counts.clear()

    # Stage B: Final REDUCE over all partial CSVs
    final_counts = merge_partials(partdir)

    # Outputs
    items = write_all_counts(Path(args.all), final_counts)
    write_top_k(Path(args.top20), items, args.top_k)

    # Minimal console summary (helps graders)
    print("Top words:")
    for w, c in items[:args.top_k]:
        print(f"{w:<15}{c}")


if __name__ == "__main__":
    main()

