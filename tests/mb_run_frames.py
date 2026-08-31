"""M-B: video + stills (non-rotating dir docs/cage_frames/iter2/mb_frames/)
for the headline cells, both adaptive strategies. Requirement #3: video
alongside stills -- re-centering is a temporal process."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

OUT = "docs/cage_frames/iter2/mb_frames"
os.makedirs(OUT, exist_ok=True)

CELLS = [
    (4, "finger", 0.025, "n4_finger_2.5cm"),
    (4, "gap",    0.035, "n4_gap_3.5cm"),
    (4, "finger", 0.050, "n4_finger_5.0cm"),
]
STRATS = ["prb_pulse", "prb_active"]

for n, direction, offset, tag in CELLS:
    for strat in STRATS:
        print(f"rendering {strat} {tag} ...")
        ch.render_quality(strat, n, offset, direction, "splayed", OUT, video=True)
print("DONE")
