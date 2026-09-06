import imageio.v2 as imageio
import os
path = "docs/cage_frames/iter2/mb_blowup_frames/cageQ_prb_n4_finger_50mm_BLOWUP_ss8_ctc3_slowmo.mp4"
r = imageio.get_reader(path)
out_dir = "docs/cage_frames/iter2/mb_blowup_frames/early_frames"
os.makedirs(out_dir, exist_ok=True)
# sample every 4th frame of the first 80 frames (close phase)
for i in range(0, 80, 4):
    frame = r.get_data(i)
    imageio.imwrite(os.path.join(out_dir, f"frame_{i:03d}.png"), frame)
print("done, extracted frames 0-79 step 4 to", out_dir)
r.close()
