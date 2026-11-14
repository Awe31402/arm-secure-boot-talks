#!/usr/bin/env python3
"""setstatus.py NN '狀態文字' ['附註行'] — update PROGRESS.md row NN status cell."""
import sys
nn, st = sys.argv[1], sys.argv[2]
p = "PROGRESS.md"; lines = open(p, encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if l.startswith(f"| {nn} |"):
        c = l.split(" | "); c[8] = st; lines[i] = " | ".join(c)
s = "\n".join(lines)
if len(sys.argv) > 3:
    s = s.rstrip("\n") + "\n" + sys.argv[3] + "\n"
open(p, "w", encoding="utf-8").write(s)
