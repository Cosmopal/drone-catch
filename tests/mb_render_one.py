import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

strat = sys.argv[1]
n = int(sys.argv[2])
direction = sys.argv[3]
offset = float(sys.argv[4])
OUT = "docs/cage_frames/iter2/mb_frames"
os.makedirs(OUT, exist_ok=True)
ch.render_quality(strat, n, offset, direction, "splayed", OUT, video=True)
print("DONE")
