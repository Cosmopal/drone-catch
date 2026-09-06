"""Render visual evidence for the joint corner that broke both M-B headline
results (substep=8, contact x0.33, seed=2), plus nominal-numerics renders
for the 4.5cm cell (never rendered before). Sets the SAME module globals
paired_converge/converge_cell themselves set for a perturbation -- no
reimplementation of the perturbation logic -- via render_quality's new
(additive) seed= and tag_suffix= parameters. Restores globals after each
call. Output goes to a directory clearly separated from the nominal
mb_frames/ set, with corner params baked into every filename."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

OUT = "docs/cage_frames/iter2/mb_corner_frames"
os.makedirs(OUT, exist_ok=True)

BASE_SS = ch.SUBSTEP
BASE_K = ch.CONTACT_STIFFNESS
BASE_C = ch.CONTACT_DAMPING


def set_corner():
    ch.SUBSTEP, ch.SIM_DT = 8, ch.DT / 8
    ch.CONTACT_STIFFNESS = BASE_K * 0.33
    ch.CONTACT_DAMPING = BASE_C * 0.33


def reset():
    ch.SUBSTEP, ch.SIM_DT = BASE_SS, ch.DT / BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C


jobs = sys.argv[1:] if len(sys.argv) > 1 else ["1", "2", "3", "4", "5", "6"]

if "1" in jobs:
    set_corner()
    ch.render_quality("prb", 4, 0.050, "finger", "splayed", OUT, video=True,
                      seed=2, tag_suffix="_CORNER_ss8_ctc033_seed2")
    reset()
    print("1 done")

if "2" in jobs:
    set_corner()
    ch.render_quality("prb_active", 4, 0.050, "finger", "splayed", OUT, video=True,
                      seed=2, tag_suffix="_CORNER_ss8_ctc033_seed2")
    reset()
    print("2 done")

if "3" in jobs:
    set_corner()
    ch.render_quality("prb", 4, 0.045, "finger", "splayed", OUT, video=True,
                      seed=2, tag_suffix="_CORNER_ss8_ctc033_seed2")
    reset()
    print("3 done")

if "4" in jobs:
    set_corner()
    ch.render_quality("prb_pulse", 4, 0.045, "finger", "splayed", OUT, video=True,
                      seed=2, tag_suffix="_CORNER_ss8_ctc033_seed2")
    reset()
    print("4 done")

if "5" in jobs:
    # nominal numerics: substep=4 (default), contact x1 (default), no seed
    ch.render_quality("prb", 4, 0.045, "finger", "splayed", OUT, video=True,
                      seed=None, tag_suffix="_NOMINAL")
    print("5 done")

if "6" in jobs:
    ch.render_quality("prb_pulse", 4, 0.045, "finger", "splayed", OUT, video=True,
                      seed=None, tag_suffix="_NOMINAL")
    print("6 done")
