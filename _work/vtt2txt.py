#!/usr/bin/env python3
"""YouTube auto-sub .vtt -> plain text, one line per ~30 s, prefixed [mm:ss].

Usage: vtt2txt.py in.vtt out.txt
Auto subs repeat each line in rolling cues; keep only new words.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
cues = []  # (start_seconds, text)
cur = None
for line in open(src, encoding="utf-8"):
    line = line.rstrip("\n")
    m = re.match(r"(?:(\d+):)?(\d+):(\d+)\.\d+ -->", line)
    if m:
        h, mi, s = m.groups()
        cur = int(h or 0) * 3600 + int(mi) * 60 + int(s)
        continue
    if cur is None or not line.strip():
        continue
    text = re.sub(r"<[^>]+>", "", line).strip()
    if text:
        cues.append((cur, text))

# drop exact repeats of the previous line (rolling captions)
words = []  # (t, text)
last = None
for t, text in cues:
    if text == last:
        continue
    if last and text.startswith(last):
        text = text[len(last):].strip()
    last_full = text
    if text:
        words.append((t, text))
    last = cues and text or last
    last = last_full if last_full else last

out = []
bucket_t, bucket = None, []
for t, text in words:
    if bucket_t is None:
        bucket_t = t
    if t - bucket_t >= 30 and bucket:
        out.append((bucket_t, " ".join(bucket)))
        bucket_t, bucket = t, []
    bucket.append(text)
if bucket:
    out.append((bucket_t, " ".join(bucket)))

with open(dst, "w", encoding="utf-8") as f:
    for t, text in out:
        f.write(f"[{t // 60:02d}:{t % 60:02d}] {text}\n")
