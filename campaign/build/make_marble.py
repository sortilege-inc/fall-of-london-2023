#!/usr/bin/env python3
"""
make_marble.py — the ivory marble's veins (campaign/assets/marble.svg), after the cracked-marble
ground of the *Laws of the Night* cover: a few long hairline cracks that wander and fork, in warm
grey at low opacity, on a transparent tile the page's ivory shows through. Seeded, so a rerun
writes the same file.

    python3 campaign/build/make_marble.py
"""
import math
import os
import random

W, H = 1400, 1400
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "marble.svg")
rng = random.Random(1666)  # the Great Fire; any fixed seed will do


def crack(x, y, ang, steps, width, depth, out):
    pts = [(x, y)]
    for _ in range(steps):
        ang += rng.gauss(0, 0.32)
        step = rng.uniform(8, 22)
        x += math.cos(ang) * step
        y += math.sin(ang) * step
        pts.append((x, y))
        if depth < 2 and rng.random() < 0.05:
            crack(x, y, ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1), int(steps * 0.45), width * 0.6, depth + 1, out)
    d = "M" + " L".join("%.1f %.1f" % p for p in pts)
    out.append((d, width, 0.22 if depth == 0 else 0.15))


paths = []
for _ in range(7):
    crack(rng.uniform(-100, W), rng.uniform(-100, H), rng.uniform(0, 2 * math.pi), rng.randint(40, 90), rng.uniform(0.9, 1.6), 0, paths)
body = "\n".join('<path d="%s" stroke-width="%.2f" stroke-opacity="%.2f"/>' % p for p in paths)
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n'
       '<g fill="none" stroke="#8a8174" stroke-linecap="round" stroke-linejoin="round">\n%s\n</g>\n</svg>\n' % (W, H, W, H, body))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(svg)
print("make_marble: %d veins → %s (%d bytes)" % (len(paths), os.path.relpath(OUT), len(svg)))
