"""Render visual evidence for the blow-up regime (stiff contact x fine
substep at 5.0cm) plus its bracketing controls, mirroring
paired_converge's own perturbation application exactly."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

OUT = "docs/cage_frames/iter2/mb_blowup_frames"
os.makedirs(OUT, exist_ok=True)

BASE_SS = ch.SUBSTEP
BASE_K = ch.CONTACT_STIFFNESS
BASE_C = ch.CONTACT_DAMPING


def set_cfg(substep, contact_scale):
    ch.SUBSTEP, ch.SIM_DT = substep, ch.DT / substep
    ch.CONTACT_STIFFNESS = BASE_K * contact_scale
    ch.CONTACT_DAMPING = BASE_C * contact_scale


def reset():
    ch.SUBSTEP, ch.SIM_DT = BASE_SS, ch.DT / BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C


jobs = sys.argv[1:] if len(sys.argv) > 1 else ["1", "2", "3", "4"]

if "1" in jobs:
    set_cfg(8, 3.0)
    ch.render_quality("prb", 4, 0.050, "finger", "splayed", OUT, video=True,
                      tag_suffix="_BLOWUP_ss8_ctc3")
    reset()
    print("1 done")

if "2" in jobs:
    set_cfg(16, 3.0)
    ch.render_quality("prb", 4, 0.050, "finger", "splayed", OUT, video=True,
                      tag_suffix="_BLOWUP_ss16_ctc3")
    reset()
    print("2 done")

if "3" in jobs:
    set_cfg(4, 3.0)
    ch.render_quality("prb", 4, 0.050, "finger", "splayed", OUT, video=True,
                      tag_suffix="_LASTSTABLE_ss4_ctc3")
    reset()
    print("3 done")

if "4" in jobs:
    set_cfg(16, 3.0)
    ch.render_quality("prb", 4, 0.045, "finger", "splayed", OUT, video=True,
                      tag_suffix="_NOBLOWUP_ss16_ctc3")
    reset()
    print("4 done")
