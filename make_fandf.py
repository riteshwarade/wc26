#!/usr/bin/env python3
"""
make_fandf.py — regenerate WC2026_Pool_Leaderboard_FandF.html from Swiftly.

Never edit FandF directly. Edit the Swiftly leaderboard, then run this script.

Usage:
  python3 make_fandf.py
"""

SRC  = 'WC2026_Pool_Leaderboard_Swiftly.html'
DEST = 'WC2026_Pool_Leaderboard_FandF.html'

SUBSTITUTIONS = [
    (
        '<title>World Cup 2026 Pool · Leaderboard – Swiftly</title>',
        '<title>World Cup 2026 Pool · Leaderboard – Friends &amp; Family</title>',
    ),
    (
        '<div class="header-title">World Cup 2026 Pool · Swiftly Leaderboard</div>',
        '<div class="header-title">World Cup 2026 Pool · Friends &amp; Family Leaderboard</div>',
    ),
    (
        "const POOL_ID   = 'swiftly';",
        "const POOL_ID   = 'fandf';",
    ),
]

with open(SRC, 'r') as f:
    content = f.read()

for old, new in SUBSTITUTIONS:
    if old not in content:
        raise ValueError(f'Pattern not found in {SRC!r}:\n  {old!r}')
    content = content.replace(old, new)

with open(DEST, 'w') as f:
    f.write(content)

print(f'✅  {DEST} regenerated from {SRC} ({len(SUBSTITUTIONS)} substitutions applied)')
