"""
test_bracket.py
Tests knockout bracket logic using simulated group results.
Run from repo root: python test_bracket.py
"""

import csv
import sys
import os
from collections import defaultdict

# Import canonical data from parse_results.py (one level up in .github/scripts/).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.github', 'scripts'))
from parse_results import GROUP_MATCHES, RANKINGS, GROUP_ORDER

# ── 495 combination table ─────────────────────────────────────────────────────
# Raw data from Wikipedia (Annex C)
# Format: "qualifying groups: 1A-opp, 1B-opp, 1D-opp, 1E-opp, 1G-opp, 1I-opp, 1K-opp, 1L-opp"
RAW_COMBOS = """E F G H I J K L: E J I F H G L K
D F G H I J K L: H G I D J F L K
D E G H I J K L: E J I D H G L K
D E F H I J K L: E J I D H F L K
D E F G I J K L: E G I D J F L K
D E F G H J K L: E G J D H F L K
D E F G H I K L: E G I D H F L K
D E F G H I J L: E G J D H F L I
D E F G H I J K: E G J D H F I K
C F G H I J K L: H G I C J F L K
C E G H I J K L: E J I C H G L K
C E F H I J K L: E J I C H F L K
C E F G I J K L: E G I C J F L K
C E F G H J K L: E G J C H F L K
C E F G H I K L: E G I C H F L K
C E F G H I J L: E G J C H F L I
C E F G H I J K: E G J C H F I K
C D G H I J K L: H G I C J D L K
C D F H I J K L: C J I D H F L K
C D F G I J K L: C G I D J F L K
C D F G H J K L: C G J D H F L K
C D F G H I K L: C G I D H F L K
C D F G H I J L: C G J D H F L I
C D F G H I J K: C G J D H F I K
C D E H I J K L: E J I C H D L K
C D E G I J K L: E G I C J D L K
C D E G H J K L: E G J C H D L K
C D E G H I K L: E G I C H D L K
C D E G H I J L: E G J C H D L I
C D E G H I J K: E G J C H D I K
C D E F I J K L: C J E D I F L K
C D E F H J K L: C J E D H F L K
C D E F H I K L: C E I D H F L K
C D E F H I J L: C J E D H F L I
C D E F H I J K: C J E D H F I K
C D E F G J K L: C G E D J F L K
C D E F G I K L: C G E D I F L K
C D E F G I J L: C G E D J F L I
C D E F G I J K: C G E D J F I K
C D E F G H K L: C G E D H F L K
C D E F G H J L: C G J D H F L E
C D E F G H J K: C G J D H F E K
C D E F G H I L: C G E D H F L I
C D E F G H I K: C G E D H F I K
C D E F G H I J: C G J D H F E I
B F G H I J K L: H J B F I G L K
B E G H I J K L: E J I B H G L K
B E F H I J K L: E J B F I H L K
B E F G I J K L: E J B F I G L K
B E F G H J K L: E J B F H G L K
B E F G H I K L: E G B F I H L K
B E F G H I J L: E J B F H G L I
B E F G H I J K: E J B F H G I K
B D G H I J K L: H J B D I G L K
B D F H I J K L: H J B D I F L K
B D F G I J K L: I G B D J F L K
B D F G H J K L: H G B D J F L K
B D F G H I K L: H G B D I F L K
B D F G H I J L: H G B D J F L I
B D F G H I J K: H G B D J F I K
B D E H I J K L: E J B D I H L K
B D E G I J K L: E J B D I G L K
B D E G H J K L: E J B D H G L K
B D E G H I K L: E G B D I H L K
B D E G H I J L: E J B D H G L I
B D E G H I J K: E J B D H G I K
B D E F I J K L: E J B D I F L K
B D E F H J K L: E J B D H F L K
B D E F H I K L: E I B D H F L K
B D E F H I J L: E J B D H F L I
B D E F H I J K: E J B D H F I K
B D E F G J K L: E G B D J F L K
B D E F G I K L: E G B D I F L K
B D E F G I J L: E G B D J F L I
B D E F G I J K: E G B D J F I K
B D E F G H K L: E G B D H F L K
B D E F G H J L: H G B D J F L E
B D E F G H J K: H G B D J F E K
B D E F G H I L: E G B D H F L I
B D E F G H I K: E G B D H F I K
B D E F G H I J: H G B D J F E I
B C G H I J K L: H J B C I G L K
B C F H I J K L: H J B C I F L K
B C F G I J K L: I G B C J F L K
B C F G H J K L: H G B C J F L K
B C F G H I K L: H G B C I F L K
B C F G H I J L: H G B C J F L I
B C F G H I J K: H G B C J F I K
B C E H I J K L: E J B C I H L K
B C E G I J K L: E J B C I G L K
B C E G H J K L: E J B C H G L K
B C E G H I K L: E G B C I H L K
B C E G H I J L: E J B C H G L I
B C E G H I J K: E J B C H G I K
B C E F I J K L: E J B C I F L K
B C E F H J K L: E J B C H F L K
B C E F H I K L: E I B C H F L K
B C E F H I J L: E J B C H F L I
B C E F H I J K: E J B C H F I K
B C E F G J K L: E G B C J F L K
B C E F G I K L: E G B C I F L K
B C E F G I J L: E G B C J F L I
B C E F G I J K: E G B C J F I K
B C E F G H K L: E G B C H F L K
B C E F G H J L: H G B C J F L E
B C E F G H J K: H G B C J F E K
B C E F G H I L: E G B C H F L I
B C E F G H I K: E G B C H F I K
B C E F G H I J: H G B C J F E I
B C D H I J K L: H J B C I D L K
B C D G I J K L: I G B C J D L K
B C D G H J K L: H G B C J D L K
B C D G H I K L: H G B C I D L K
B C D G H I J L: H G B C J D L I
B C D G H I J K: H G B C J D I K
B C D F I J K L: C J B D I F L K
B C D F H J K L: C J B D H F L K
B C D F H I K L: C I B D H F L K
B C D F H I J L: C J B D H F L I
B C D F H I J K: C J B D H F I K
B C D F G J K L: C G B D J F L K
B C D F G I K L: C G B D I F L K
B C D F G I J L: C G B D J F L I
B C D F G I J K: C G B D J F I K
B C D F G H K L: C G B D H F L K
B C D F G H J L: C G B D H F L J
B C D F G H J K: H G B C J F D K
B C D F G H I L: C G B D H F L I
B C D F G H I K: C G B D H F I K
B C D F G H I J: H G B C J F D I
B C D E I J K L: E J B C I D L K
B C D E H J K L: E J B C H D L K
B C D E H I K L: E I B C H D L K
B C D E H I J L: E J B C H D L I
B C D E H I J K: E J B C H D I K
B C D E G J K L: E G B C J D L K
B C D E G I K L: E G B C I D L K
B C D E G I J L: E G B C J D L I
B C D E G I J K: E G B C J D I K
B C D E G H K L: E G B C H D L K
B C D E G H J L: H G B C J D L E
B C D E G H J K: H G B C J D E K
B C D E G H I L: E G B C H D L I
B C D E G H I K: E G B C H D I K
B C D E G H I J: H G B C J D E I
B C D E F J K L: C J B D E F L K
B C D E F I K L: C E B D I F L K
B C D E F I J L: C J B D E F L I
B C D E F I J K: C J B D E F I K
B C D E F H K L: C E B D H F L K
B C D E F H J L: C J B D H F L E
B C D E F H J K: C J B D H F E K
B C D E F H I L: C E B D H F L I
B C D E F H I K: C E B D H F I K
B C D E F H I J: C J B D H F E I
B C D E F G K L: C E B D E F L K
B C D E F G J L: C J B D J F L E
B C D E F G J K: C J B D J F E K
B C D E F G I L: C E B D E F L I
B C D E F G I K: C E B D E F I K
B C D E F G I J: C E B D J F E I
B C D E F G H L: C G B D H F L E
B C D E F G H K: H G B C H F D K
B C D E F G H J: H G B C J F D E
B C D E F G H I: C G B D H F E I
A F G H I J K L: H J I F A G L K
A E G H I J K L: E J I A H G L K
A E F H I J K L: E J I F A H L K
A E F G I J K L: E J I F A G L K
A E F G H J K L: E G J F A H L K
A E F G H I K L: E G I F A H L K
A E F G H I J L: E G J F A H L I
A E F G H I J K: E G J F A H I K
A D G H I J K L: H J I D A G L K
A D F H I J K L: H J I D A F L K
A D F G I J K L: I G J D A F L K
A D F G H J K L: H G J D A F L K
A D F G H I K L: H G I D A F L K
A D F G H I J L: H G J D A F L I
A D F G H I J K: H G J D A F I K
A D E H I J K L: E J I D A H L K
A D E G I J K L: E J I D A G L K
A D E G H J K L: E G J D A H L K
A D E G H I K L: E G I D A H L K
A D E G H I J L: E G J D A H L I
A D E G H I J K: E G J D A H I K
A D E F I J K L: E J I D A F L K
A D E F H J K L: H J E D A F L K
A D E F H I K L: H E I D A F L K
A D E F H I J L: H J E D A F L I
A D E F H I J K: H J E D A F I K
A D E F G J K L: E G J D A F L K
A D E F G I K L: E G I D A F L K
A D E F G I J L: E G J D A F L I
A D E F G I J K: E G J D A F I K
A D E F G H K L: H G E D A F L K
A D E F G H J L: H G J D A F L E
A D E F G H J K: H G J D A F E K
A D E F G H I L: H G E D A F L I
A D E F G H I K: H G E D A F I K
A D E F G H I J: H G J D A F E I
A C G H I J K L: H J I C A G L K
A C F H I J K L: H J I C A F L K
A C F G I J K L: I G J C A F L K
A C F G H J K L: H G J C A F L K
A C F G H I K L: H G I C A F L K
A C F G H I J L: H G J C A F L I
A C F G H I J K: H G J C A F I K
A C E H I J K L: E J I C A H L K
A C E G I J K L: E J I C A G L K
A C E G H J K L: E G J C A H L K
A C E G H I K L: E G I C A H L K
A C E G H I J L: E G J C A H L I
A C E G H I J K: E G J C A H I K
A C E F I J K L: E J I C A F L K
A C E F H J K L: H J E C A F L K
A C E F H I K L: H E I C A F L K
A C E F H I J L: H J E C A F L I
A C E F H I J K: H J E C A F I K
A C E F G J K L: E G J C A F L K
A C E F G I K L: E G I C A F L K
A C E F G I J L: E G J C A F L I
A C E F G I J K: E G J C A F I K
A C E F G H K L: H G E C A F L K
A C E F G H J L: H G J C A F L E
A C E F G H J K: H G J C A F E K
A C E F G H I L: H G E C A F L I
A C E F G H I K: H G E C A F I K
A C E F G H I J: H G J C A F E I
A C D H I J K L: H J I C A D L K
A C D G I J K L: I G J C A D L K
A C D G H J K L: H G J C A D L K
A C D G H I K L: H G I C A D L K
A C D G H I J L: H G J C A D L I
A C D G H I J K: H G J C A D I K
A C D F I J K L: C J I D A F L K
A C D F H J K L: H J F C A D L K
A C D F H I K L: H F I C A D L K
A C D F H I J L: H J F C A D L I
A C D F H I J K: H J F C A D I K
A C D F G J K L: C G J D A F L K
A C D F G I K L: C G I D A F L K
A C D F G I J L: C G J D A F L I
A C D F G I J K: C G J D A F I K
A C D F G H K L: H G F C A D L K
A C D F G H J L: C G J D A F L H
A C D F G H J K: H G J C A F D K
A C D F G H I L: H G F C A D L I
A C D F G H I K: H G F C A D I K
A C D F G H I J: H G J C A F D I
A C D E I J K L: E J I C A D L K
A C D E H J K L: H J E C A D L K
A C D E H I K L: H E I C A D L K
A C D E H I J L: H J E C A D L I
A C D E H I J K: H J E C A D I K
A C D E G J K L: E G J C A D L K
A C D E G I K L: E G I C A D L K
A C D E G I J L: E G J C A D L I
A C D E G I J K: E G J C A D I K
A C D E G H K L: H G E C A D L K
A C D E G H J L: H G J C A D L E
A C D E G H J K: H G J C A D E K
A C D E G H I L: H G E C A D L I
A C D E G H I K: H G E C A D I K
A C D E G H I J: H G J C A D E I
A C D E F J K L: C J E D A F L K
A C D E F I K L: C E I D A F L K
A C D E F I J L: C J E D A F L I
A C D E F I J K: C J E D A F I K
A C D E F H K L: H E F C A D L K
A C D E F H J L: H J F C A D L E
A C D E F H J K: H J E C A F D K
A C D E F H I L: H E F C A D L I
A C D E F H I K: H E F C A D I K
A C D E F H I J: H J E C A F D I
A C D E F G K L: C G E D A F L K
A C D E F G J L: C G J D A F L E
A C D E F G J K: C G J D A F E K
A C D E F G I L: C G E D A F L I
A C D E F G I K: C G E D A F I K
A C D E F G I J: C G J D A F E I
A C D E F G H L: H G F C A D L E
A C D E F G H K: H G E C A F D K
A C D E F G H J: H G J C A F D E
A C D E F G H I: H G E C A F D I
A B G H I J K L: H J B A I G L K
A B F H I J K L: H J B A I F L K
A B F G I J K L: I J B F A G L K
A B F G H J K L: H J B F A G L K
A B F G H I K L: H G B A I F L K
A B F G H I J L: H J B F A G L I
A B F G H I J K: H J B F A G I K
A B E H I J K L: E J B A I H L K
A B E G I J K L: E J B A I G L K
A B E G H J K L: E J B A H G L K
A B E G H I K L: E G B A I H L K
A B E G H I J L: E J B A H G L I
A B E G H I J K: E J B A H G I K
A B E F I J K L: E J B A I F L K
A B E F H J K L: E J B F A H L K
A B E F H I K L: E I B F A H L K
A B E F H I J L: E J B F A H L I
A B E F H I J K: E J B F A H I K
A B E F G J K L: E J B F A G L K
A B E F G I K L: E G B A I F L K
A B E F G I J L: E J B F A G L I
A B E F G I J K: E J B F A G I K
A B E F G H K L: E G B F A H L K
A B E F G H J L: H J B F A G L E
A B E F G H J K: H J B F A G E K
A B E F G H I L: E G B F A H L I
A B E F G H I K: E G B F A H I K
A B E F G H I J: H J B F A G E I
A B D H I J K L: I J B D A H L K
A B D G I J K L: I J B D A G L K
A B D G H J K L: H J B D A G L K
A B D G H I K L: I G B D A H L K
A B D G H I J L: H J B D A G L I
A B D G H I J K: H J B D A G I K
A B D F I J K L: I J B D A F L K
A B D F H J K L: H J B D A F L K
A B D F H I K L: H I B D A F L K
A B D F H I J L: H J B D A F L I
A B D F H I J K: H J B D A F I K
A B D F G J K L: F J B D A G L K
A B D F G I K L: I G B D A F L K
A B D F G I J L: F J B D A G L I
A B D F G I J K: F J B D A G I K
A B D F G H K L: H G B D A F L K
A B D F G H J L: H G B D A F L J
A B D F G H J K: H G B D A F J K
A B D F G H I L: H G B D A F L I
A B D F G H I K: H G B D A F I K
A B D F G H I J: H G B D A F I J
A B D E I J K L: E J B A I D L K
A B D E H J K L: E J B D A H L K
A B D E H I K L: E I B D A H L K
A B D E H I J L: E J B D A H L I
A B D E H I J K: E J B D A H I K
A B D E G J K L: E J B D A G L K
A B D E G I K L: E G B A I D L K
A B D E G I J L: E J B D A G L I
A B D E G I J K: E J B D A G I K
A B D E G H K L: E G B D A H L K
A B D E G H J L: H J B D A G L E
A B D E G H J K: H J B D A G E K
A B D E G H I L: E G B D A H L I
A B D E G H I K: E G B D A H I K
A B D E G H I J: H J B D A G E I
A B D E F J K L: E J B D A F L K
A B D E F I K L: E I B D A F L K
A B D E F I J L: E J B D A F L I
A B D E F I J K: E J B D A F I K
A B D E F H K L: H E B D A F L K
A B D E F H J L: H J B D A F L E
A B D E F H J K: H J B D A F E K
A B D E F H I L: H E B D A F L I
A B D E F H I K: H E B D A F I K
A B D E F H I J: H J B D A F E I
A B D E F G K L: E G B D A F L K
A B D E F G J L: E G B D A F L J
A B D E F G J K: E G B D A F J K
A B D E F G I L: E G B D A F L I
A B D E F G I K: E G B D A F I K
A B D E F G I J: E G B D A F I J
A B D E F G H L: H G B D A F L E
A B D E F G H K: H G B D A F E K
A B D E F G H J: H G B D A F E J
A B D E F G H I: H G B D A F E I
A B C H I J K L: I J B C A H L K
A B C G I J K L: I J B C A G L K
A B C G H J K L: H J B C A G L K
A B C G H I K L: I G B C A H L K
A B C G H I J L: H J B C A G L I
A B C G H I J K: H J B C A G I K
A B C F I J K L: I J B C A F L K
A B C F H J K L: H J B C A F L K
A B C F H I K L: H I B C A F L K
A B C F H I J L: H J B C A F L I
A B C F H I J K: H J B C A F I K
A B C F G J K L: C J B F A G L K
A B C F G I K L: I G B C A F L K
A B C F G I J L: C J B F A G L I
A B C F G I J K: C J B F A G I K
A B C F G H K L: H G B C A F L K
A B C F G H J L: H G B C A F L J
A B C F G H J K: H G B C A F J K
A B C F G H I L: H G B C A F L I
A B C F G H I K: H G B C A F I K
A B C F G H I J: H G B C A F I J
A B C E I J K L: E J B A I C L K
A B C E H J K L: E J B C A H L K
A B C E H I K L: E I B C A H L K
A B C E H I J L: E J B C A H L I
A B C E H I J K: E J B C A H I K
A B C E G J K L: E J B C A G L K
A B C E G I K L: E G B A I C L K
A B C E G I J L: E J B C A G L I
A B C E G I J K: E J B C A G I K
A B C E G H K L: E G B C A H L K
A B C E G H J L: H J B C A G L E
A B C E G H J K: H J B C A G E K
A B C E G H I L: E G B C A H L I
A B C E G H I K: E G B C A H I K
A B C E G H I J: H J B C A G E I
A B C E F J K L: E J B C A F L K
A B C E F I K L: E I B C A F L K
A B C E F I J L: E J B C A F L I
A B C E F I J K: E J B C A F I K
A B C E F H K L: H E B C A F L K
A B C E F H J L: H J B C A F L E
A B C E F H J K: H J B C A F E K
A B C E F H I L: H E B C A F L I
A B C E F H I K: H E B C A F I K
A B C E F H I J: H J B C A F E I
A B C E F G K L: E G B C A F L K
A B C E F G J L: E G B C A F L J
A B C E F G J K: E G B C A F J K
A B C E F G I L: E G B C A F L I
A B C E F G I K: E G B C A F I K
A B C E F G I J: E G B C A F I J
A B C E F G H L: H G B C A F L E
A B C E F G H K: H G B C A F E K
A B C E F G H J: H G B C A F E J
A B C E F G H I: H G B C A F E I
A B C D I J K L: I J B C A D L K
A B C D G I J K L: I J B C A D L K
A B C D H J K L: H J B C A D L K
A B C D H I K L: H I B C A D L K
A B C D H I J L: H J B C A D L I
A B C D H I J K: H J B C A D I K
A B C D G J K L: C J B D A G L K
A B C D G I K L: I G B C A D L K
A B C D G I J L: C J B D A G L I
A B C D G I J K: C J B D A G I K
A B C D G H K L: H G B C A D L K
A B C D G H J L: H G B C A D L J
A B C D G H J K: H G B C A D J K
A B C D G H I L: H G B C A D L I
A B C D G H I K: H G B C A D I K
A B C D G H I J: H G B C A D I J
A B C D F J K L: C J B D A F L K
A B C D F I K L: C I B D A F L K
A B C D F I J L: C J B D A F L I
A B C D F I J K: C J B D A F I K
A B C D F H K L: H F B C A D L K
A B C D F H J L: C J B D A F L H
A B C D F H J K: H J B C A F D K
A B C D F H I L: H F B C A D L I
A B C D F H I K: H F B C A D I K
A B C D F H I J: H J B C A F D I
A B C D F G K L: C G B D A F L K
A B C D F G J L: C G B D A F L J
A B C D F G J K: C G B D A F J K
A B C D F G I L: C G B D A F L I
A B C D F G I K: C G B D A F I K
A B C D F G I J: C G B D A F I J
A B C D F G H L: C G B D A F L H
A B C D F G H K: H G B C A F D K
A B C D F G H J: H G B C A F D J
A B C D F G H I: H G B C A F D I
A B C D E J K L: E J B C A D L K
A B C D E I K L: E I B C A D L K
A B C D E I J L: E J B C A D L I
A B C D E I J K: E J B C A D I K
A B C D E H K L: H E B C A D L K
A B C D E H J L: H J B C A D L E
A B C D E H J K: H J B C A D E K
A B C D E H I L: H E B C A D L I
A B C D E H I K: H E B C A D I K
A B C D E H I J: H J B C A D E I
A B C D E G K L: E G B C A D L K
A B C D E G J L: E G B C A D L J
A B C D E G J K: E G B C A D J K
A B C D E G I L: E G B C A D L I
A B C D E G I K: E G B C A D I K
A B C D E G I J: E G B C A D I J
A B C D E G H L: H G B C A D L E
A B C D E G H K: H G B C A D E K
A B C D E G H J: H G B C A D E J
A B C D E G H I: H G B C A D E I
A B C D E F K L: C E B D A F L K
A B C D E F J L: C J B D A F L E
A B C D E F J K: C J B D A F E K
A B C D E F I L: C E B D A F L I
A B C D E F I K: C E B D A F I K
A B C D E F I J: C J B D A F E I
A B C D E F H L: H F B C A D L E
A B C D E F H K: H E B C A F D K
A B C D E F H J: H J B C A F D E
A B C D E F H I: H E B C A F D I
A B C D E F G L: C G B D A F L E
A B C D E F G K: C G B D A F E K
A B C D E F G J: C G B D A F E J
A B C D E F G I: C G B D A F E I
A B C D E F G H: H G B C A F D E"""

def parse_combinations():
    """Parse the raw combination table into a lookup dict."""
    combos = {}
    for line in RAW_COMBOS.strip().split('\n'):
        parts = line.split(':')
        groups_part = parts[0].strip().split()
        assignments_part = [x.strip() for x in parts[1].strip().split()]
        key = ''.join(sorted(groups_part))
        # assignments[i] is the group whose 3rd place team plays against:
        # [0]=1A, [1]=1B, [2]=1D, [3]=1E, [4]=1G, [5]=1I, [6]=1K, [7]=1L
        combos[key] = assignments_part
    return combos

# ── Load and compute group standings ─────────────────────────────────────────
def load_results(path='results/group_results.csv'):
    results = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                num = int(row['match'])
                results[num] = {
                    'home': int(row['home_score']),
                    'away': int(row['away_score']),
                    'outcome': row['outcome'].strip()
                }
    except FileNotFoundError:
        print(f"Warning: {path} not found")
    return results

def h2h(teamA, teamB, grp_matches, results):
    Pts = GF = GA = 0
    for num, g, t1, t2 in grp_matches:
        r = results.get(num)
        if not r: continue
        if t1 == teamA and t2 == teamB:
            GF += r['home']; GA += r['away']
            if r['outcome'] == 'W1': Pts += 3
            elif r['outcome'] == 'Draw': Pts += 1
        elif t1 == teamB and t2 == teamA:
            GF += r['away']; GA += r['home']
            if r['outcome'] == 'W2': Pts += 3
            elif r['outcome'] == 'Draw': Pts += 1
    return Pts, GF, GA

def compute_standings(results):
    groups = defaultdict(lambda: defaultdict(lambda: {'P':0,'W':0,'D':0,'L':0,'GF':0,'GA':0,'Pts':0}))
    grp_matches = defaultdict(list)

    for num, grp, t1, t2 in GROUP_MATCHES:
        grp_matches[grp].append((num, grp, t1, t2))
        r = results.get(num)
        if not r: continue
        groups[grp][t1]['P'] += 1; groups[grp][t2]['P'] += 1
        groups[grp][t1]['GF'] += r['home']; groups[grp][t1]['GA'] += r['away']
        groups[grp][t2]['GF'] += r['away']; groups[grp][t2]['GA'] += r['home']
        if r['outcome'] == 'W1':
            groups[grp][t1]['W'] += 1; groups[grp][t1]['Pts'] += 3; groups[grp][t2]['L'] += 1
        elif r['outcome'] == 'W2':
            groups[grp][t2]['W'] += 1; groups[grp][t2]['Pts'] += 3; groups[grp][t1]['L'] += 1
        else:
            groups[grp][t1]['D'] += 1; groups[grp][t1]['Pts'] += 1
            groups[grp][t2]['D'] += 1; groups[grp][t2]['Pts'] += 1

    standings = {}
    for grp in sorted(groups.keys()):
        order = GROUP_ORDER[grp]
        gm = grp_matches[grp]
        teams = sorted(order, key=lambda t: (
            -groups[grp][t]['Pts'],
            -(groups[grp][t]['GF'] - groups[grp][t]['GA']),
            -groups[grp][t]['GF'],
            RANKINGS.get(t, 999)
        ))
        standings[grp] = [(t, groups[grp][t]) for t in teams]
    return standings

def get_best_thirds(standings):
    thirds = []
    for grp, teams in standings.items():
        if len(teams) >= 3:
            team, s = teams[2]
            thirds.append((grp, team, s))
    thirds.sort(key=lambda x: (-x[2]['Pts'], -(x[2]['GF']-x[2]['GA']), -x[2]['GF'], RANKINGS.get(x[1],999)))
    return thirds

# ── Build bracket ─────────────────────────────────────────────────────────────
def build_bracket(standings, qualified_thirds, combos):
    # Get 1st, 2nd, 3rd per group
    pos = {}
    for grp, teams in standings.items():
        if len(teams) >= 1: pos[f'1{grp}'] = teams[0][0]
        if len(teams) >= 2: pos[f'2{grp}'] = teams[1][0]
        if len(teams) >= 3: pos[f'3{grp}'] = teams[2][0]

    # Determine which groups' 3rd teams qualified
    qual_groups = sorted([g for g, _, _ in qualified_thirds[:8]])
    key = ''.join(qual_groups)
    assignment = combos.get(key)

    print(f"\n=== Qualified 3rd-place teams ===")
    for grp, team, s in qualified_thirds[:8]:
        print(f"  3{grp}: {team} ({s['Pts']}pts, GD={s['GF']-s['GA']}, GF={s['GF']})")

    print(f"\n=== 3rd place combination key: '{key}' ===")
    if assignment:
        slots = ['1A vs','1B vs','1D vs','1E vs','1G vs','1I vs','1K vs','1L vs']
        match_nums = [79, 85, 81, 74, 82, 77, 87, 80]
        third_map = {}
        for i, (slot, m, grp) in enumerate(zip(slots, match_nums, assignment)):
            team = pos.get(f'3{grp}', f'3{grp}')
            third_map[m] = team
            print(f"  {slot} 3{grp} = {team}")
    else:
        print(f"  ERROR: Combination '{key}' not found!")
        third_map = {}
        for m in [79,85,81,74,82,77,87,80]:
            third_map[m] = 'TBD'

    # Fixed R32 matchups
    r32 = {
        73: (pos.get('2A','2A'), pos.get('2B','2B')),
        74: (pos.get('1E','1E'), third_map.get(74,'TBD')),
        75: (pos.get('1F','1F'), pos.get('2C','2C')),
        76: (pos.get('1C','1C'), pos.get('2F','2F')),
        77: (pos.get('1I','1I'), third_map.get(77,'TBD')),
        78: (pos.get('2E','2E'), pos.get('2I','2I')),
        79: (pos.get('1A','1A'), third_map.get(79,'TBD')),
        80: (pos.get('1L','1L'), third_map.get(80,'TBD')),
        81: (pos.get('1D','1D'), third_map.get(81,'TBD')),
        82: (pos.get('1G','1G'), third_map.get(82,'TBD')),
        83: (pos.get('2K','2K'), pos.get('2L','2L')),
        84: (pos.get('1H','1H'), pos.get('2J','2J')),
        85: (pos.get('1B','1B'), third_map.get(85,'TBD')),
        86: (pos.get('1J','1J'), pos.get('2H','2H')),
        87: (pos.get('1K','1K'), third_map.get(87,'TBD')),
        88: (pos.get('2D','2D'), pos.get('2G','2G')),
    }

    print("\n=== Group standings (1st / 2nd / 3rd / 4th) ===")
    for grp in sorted(standings.keys()):
        teams = standings[grp]
        row = ' | '.join(f"{t}({s['Pts']})" for t,s in teams)
        print(f"  Group {grp}: {row}")

    print("\n=== Round of 32 ===")
    for m in range(73, 89):
        h, a = r32[m]
        print(f"  M{m}: {h} vs {a}")

    print("\n=== Round of 16 ===")
    r16 = {89:(74,77), 90:(73,75), 91:(76,78), 92:(79,80),
           93:(83,84), 94:(81,82), 95:(86,88), 96:(85,87)}
    for m, (a,b) in sorted(r16.items()):
        h_team = f"W{a}({r32[a][0]}/{r32[a][1]})"
        a_team = f"W{b}({r32[b][0]}/{r32[b][1]})"
        print(f"  M{m}: {h_team} vs {a_team}")

    print("\n=== Quarterfinals ===")
    qf = {97:(89,90), 98:(93,94), 99:(91,92), 100:(95,96)}
    for m, (a,b) in sorted(qf.items()):
        print(f"  M{m}: W{a} vs W{b}")

    print("\n=== Semifinals ===")
    print("  M101: W97 vs W98")
    print("  M102: W99 vs W100")
    print("\n=== 3rd Place & Final ===")
    print("  M103: L101 vs L102  (3rd place)")
    print("  M104: W101 vs W102  (Final)")

if __name__ == '__main__':
    print("Loading combination table...")
    combos = parse_combinations()
    print(f"  Loaded {len(combos)} combinations")

    print("Loading group results...")
    results = load_results()
    print(f"  Loaded {len(results)} match results")

    print("Computing standings...")
    standings = compute_standings(results)

    print("Finding best 8 third-place teams...")
    thirds = get_best_thirds(standings)

    print("\nBuilding bracket...")
    build_bracket(standings, thirds, combos)
