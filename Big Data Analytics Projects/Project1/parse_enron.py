#!/usr/bin/env python3
"""
parse_enron_v2.py
Preprocess raw CMU Enron maildir into plain-text documents for Map→Shuffle→Reduce.

What this does (allowed by the assignment because your *input* to MapReduce
is “one or more plain text files”):
  • Prefer text/plain; fallback to text/html with tag-stripping
  • Remove quoted reply blocks ("> ..." lines, and “Original Message” sections)
  • Collapse whitespace
  • Deduplicate by SHA-1 hash of the cleaned body
Output directory: data/plain_v2/
"""

import os, re, hashlib, email, pathlib

RAW_DIR = "data/maildir"      # raw CMU maildir root
OUT_DIR = "data/plain_v2"     # cleaned, deduped outputs here
INDEX   = "outputs/plain_v2_index.csv"

# HTML handling (very light): strip tags, convert <br>/<p> to newlines
HTML_TAGS = re.compile(r"<[^>]+>")
BR2NL     = re.compile(r"(?i)<\s*br\s*/?>|</\s*p\s*>|<\s*p\s*>")

# Quoted-reply detection
ORIG_SPLIT= re.compile(r"(?im)^\s*[-]{2,}\s*original message\s*[-]{2,}\s*$")
ARROW_Q   = re.compile(r"(?m)^\s*>.*$")   # lines beginning with '>'

def html_to_text(html: str) -> str:
    html = BR2NL.sub("\n", html)
    html = HTML_TAGS.sub(" ", html)
    return html

def extract_body(msg):
    """Prefer text/plain; fallback to text/html (converted to text)."""
    if msg.is_multipart():
        txt = None
        html = None
        for part in msg.walk():
            ctype = part.get_content_type()
            if part.get_filename():    # skip attachments
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            try:
                text = payload.decode(errors="ignore")
            except Exception:
                continue
            if ctype == "text/plain" and txt is None:
                txt = text
            elif ctype == "text/html" and html is None:
                html = text
        if txt is not None:
            return txt
        if html is not None:
            return html_to_text(html)
        return ""
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, (bytes, bytearray)):
            text = payload.decode(errors="ignore")
        else:
            text = str(payload or "")
        # heuristic: looks like HTML? strip tags
        if "<html" in text.lower() or "<body" in text.lower() or "</" in text:
            return html_to_text(text)
        return text

def strip_quotes(text: str) -> str:
    """Drop quoted/replied blocks and collapse noise."""
    parts = ORIG_SPLIT.split(text)
    text  = parts[0]
    text  = ARROW_Q.sub("", text)        # remove lines starting with '>'
    text  = re.sub(r"[ \t]+", " ", text) # normalize spaces
    text  = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def main():
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    seen = set()  # hashes for dedup
    idx_lines = ["hash,relpath,bytes"]
    count_in = 0
    count_out= 0

    for dp, _, fs in os.walk(RAW_DIR):
        for f in fs:
            src = os.path.join(dp, f)
            count_in += 1
            try:
                with open(src, "rb") as fh:
                    msg = email.message_from_bytes(fh.read())
                body = extract_body(msg)
                if not body: continue
                body = strip_quotes(body)
                if not body: continue
                h = hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest()
                if h in seen:  # deduplicate exact bodies
                    continue
                seen.add(h)
                outp = os.path.join(OUT_DIR, f"{h}.txt")
                with open(outp, "w", encoding="utf-8", errors="ignore") as w:
                    w.write(body)
                count_out += 1
                if count_out % 50000 == 0:
                    print(f"wrote {count_out} unique docs...")
                idx_lines.append(f"{h},{os.path.relpath(src, RAW_DIR)},{len(body.encode('utf-8','ignore'))}")
            except Exception:
                # lenient: skip malformed emails
                continue

    with open(INDEX, "w", encoding="utf-8") as ix:
        ix.write("\n".join(idx_lines))
    print(f"Done. Scanned {count_in} raw files; wrote {count_out} deduped, cleaned docs to {OUT_DIR}")

if __name__ == "__main__":
    main()

