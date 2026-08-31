---
tags:
  - research-digest
---

# Research digest: World models for robotics/control + METR long-horizon agent measurement

> Raw output of research subagent `aba33050494e20b90` (session d155edbe, 2026-07-04),
> spawned for the loop-engineering meta-analysis. Unedited final message;
> synthesis and corrections live in ../[[loop-engineering-analysis|loop-engineering-analysis.md]].
> Full transcript: `transcripts/08-world-models-metr-horizons.jsonl`.

# Research Digest: World Models for Robotics + Long-Horizon Agents & Oversight

Compiled from primary-source verification (arXiv, metr.org, DeepMind/Meta official pages). One sub-thread (scalable oversight, Section B.3–B.4) was still in flight when I was stopped — marked **NOT COVERED** rather than filled from memory.

---

## SECTION A — World models for robotics/control (2023–2026)

### A.1 Current state of the field

| System | Source + date | Specific finding | Takeaway |
|---|---|---|---|
| **DreamerV3** | Hafner et al., [arXiv:2301.04104](https://arxiv.org/abs/2301.04104) (Jan 2023); journal version "Mastering Diverse Control Tasks through World Models," [Nature 2025](https://www.nature.com/articles/s41586-025-08744-2) | Outperforms specialized methods across 150+ tasks with a *single configuration*; first algorithm to collect Minecraft diamonds from scratch without human data | One model-based RL recipe transfers across domains without per-task tuning — the learned-model counterpart to hand-tuned cascades |
| **Genie / Genie 2 / Genie 3** | Bruce et al., [arXiv:2402.15391](https://arxiv.org/abs/2402.15391) (Feb 2024, ICML); [Genie 2 blog](https://deepmind.google/blog/genie-2-a-large-scale-foundation-world-model/) (Dec 2024); [Genie 3 blog](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/) (Aug 2025) | Genie 2's own stated limit: "consistent worlds for up to a minute, with the majority of examples lasting 10–20s"; Genie 3: 24 fps, consistency "several minutes," visual memory ~1 min | Video-generative *environment* models for embodied-agent training — not dynamics models you plan against at control rates |
| **V-JEPA 2** | Assran et al. (Meta), [arXiv:2506.09985](https://arxiv.org/abs/2506.09985) + [Meta blog](https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks/) (Jun 2025) | Pretrained on >1M hours of video + <62h robot video; zero-shot Franka pick-and-place at 65–80% success in unseen environments | Real evidence of video-pretrained world models doing manipulation planning — but MPC over learned latents is slow, nowhere near reactive catch rates |
| **TD-MPC2** | Hansen, Su, Wang, [arXiv:2310.16828](https://arxiv.org/abs/2310.16828), ICLR 2024 | 104 online RL tasks, single hyperparameter set; one 317M-param agent performs 80 tasks | Latent world model + MPC — conceptually closest to classical control; the most practical to run at this project's scale |
| **UniSim** | Yang et al., [arXiv:2310.06114](https://arxiv.org/abs/2310.06114), [ICLR 2024 Outstanding Paper](https://blog.iclr.cc/2024/05/06/iclr-2024-outstanding-paper-awards/) | Policies trained purely in the learned simulator deploy zero-shot in the real world | Proof-of-concept that a learned sim can substitute for a physics engine — at enormous compute cost, and at visual-outcome (not force/contact) fidelity |
| **DayDreamer** | Wu, Escontrela, Hafner et al., [arXiv:2206.14176](https://arxiv.org/abs/2206.14176), CoRL 2022 | A1 quadruped learns to walk from scratch in **1 hour on real hardware, no simulator, no resets**; adapts to pushes in 10 min; same hyperparameters across 4 robots | World-model RL is sample-efficient enough to skip the analytic sim entirely — *on hardware* |

### A.2 The strongest case FOR learned models (the attempted refutation)

This is where your first-principles judgment takes real damage — not from Dreamer/Genie-class models, but from **residual/hybrid** work:

- **TossingBot** (Zeng et al., RSS 2019 / T-RO 2020 Best Paper, [arXiv:1903.11239](https://arxiv.org/abs/1903.11239)) — *the closest comparable to drone-catch: ballistic throwing to a target.* Real-robot throw accuracy: **residual physics 84.7% vs analytic ballistics alone 61.3% vs pure learning 54.2%**. Drag on light objects and off-COM grasps make the analytic release velocity *systematically biased*. **Takeaway: in your exact task family, analytic-prior + learned residual beat analytics alone by 23 points.**
- **NeuroBEM** (Bauersfeld et al., RSS 2021, [arXiv:2106.08015](https://arxiv.org/abs/2106.08015)) — *your exact vehicle class.* Blade-element analytic model + learned residual: **~50% force/torque RMSE reduction**; closed-loop tracking 0.8 m → <0.3 m. Ablation: hybrid beats both pure analytic AND pure learned (learned-only fails to generalize). **Takeaway: for quadrotors, first principles leave half the force error on the table.**
- **Neural-Fly** (O'Connell et al., Science Robotics May 2022, [DOI](https://www.science.org/doi/10.1126/scirobotics.abm6597)) — learned residual aerodynamics from **12 minutes** of flight data: tracking error in 12.1 m/s wind **8.7 cm vs 21.6 cm** nonlinear baseline (66% better). **Takeaway: the winning architecture is "analytic where it's right, learned where it's wrong."**
- **Contact specifically** — the part most relevant to your rigid-contact artifact:
  - **Bauza & Rodriguez** (ICRA 2017, [arXiv:1704.03033](https://arxiv.org/abs/1704.03033)) + the "Million Ways to Be Pushed" dataset: real frictional contact is **stochastic and analytic models are biased on average**; a learned GP model beats the analytic pushing model after **<100 real samples**.
  - **ContactNets** (Pfrommer, Halm, Posa, CoRL 2020, [arXiv:2009.11193](https://arxiv.org/abs/2009.11193)): structured learning (implicit signed distance + contact Jacobians) predicts real tossed-cube impacts/stiction from **60 seconds of data** where end-to-end nets fail.
  - **Parmar, Halm, Posa** (IROS 2021, [arXiv:2103.15406](https://arxiv.org/abs/2103.15406)): stiff contact breaks *naive* deep learning — but the same paper flags that the compliant-contact settings sims use for numerical stability **don't reflect rigid hardware either**. Neither side is ground truth for contact.
  - **NeuralSim** (Heiden, Millard, **Coumans** et al., ICRA 2021, [arXiv:2011.04217](https://arxiv.org/abs/2011.04217)): neural augmentation *inside* a differentiable rigid-body engine — co-authored by PyBullet's own creator, who argues analytic engines "can only predict systems for which they have been designed."

**The honest boundary of the refutation:** every quantitative win above is a learned residual **fit to real-world data**, correcting an analytic-model/reality gap. *No paper shows a learned model beating PyBullet at predicting PyBullet.* Inside a pure-sim project, the analytic sim is tautologically ground truth; a learned copy can only add error (plus rollout speed, the actual argument for learned models in pure-sim settings).

### A.3 The case against / limits

| Finding | Source + date | Number | Takeaway |
|---|---|---|---|
| Compounding rollout error | Janner et al., MBPO, NeurIPS 2019, [arXiv:1906.08253](https://arxiv.org/abs/1906.08253) | Return-gap bound grows linearly in rollout length × model error; MBPO uses rollouts of **k = 1–15 steps** | Even flagship MBRL trusts its learned model for ~1–15 steps; the analytic sim is trusted for the full horizon |
| Objective mismatch | Lambert et al., L4DC 2020, [arXiv:2002.04523](https://arxiv.org/abs/2002.04523) | One-step prediction likelihood "not always correlated with control performance" | A learned model can ace its training metric and still be wrong for control — a failure mode analytic sims don't have |
| Hallucinated physics | Physics-IQ (Motamed et al., DeepMind, Jan 2025, [arXiv:2501.09038](https://arxiv.org/abs/2501.09038)) | Best video model scores **29.5/100** on physical understanding; Sora **10.0** — and realism is *uncorrelated* with physics | The most convincing-looking rollouts can be the most physically wrong |
| Conservation-law violations | WorldModelBench (Li et al., Feb 2025, [arXiv:2502.20694](https://arxiv.org/abs/2502.20694)) | Best model: 12% of rollouts violate mass conservation, 11% show interpenetration; across models impenetrability violated ~23% | Learned "world models" break laws an analytic sim satisfies by construction |
| Case-based, not law-based | Kang et al. (ByteDance), Nov 2024/ICML 2025, [arXiv:2411.02385](https://arxiv.org/abs/2411.02385) | Near-perfect in-distribution, fails OOD; generalizes by nearest-training-case with priority **color > size > velocity > shape**; "scaling alone is insufficient" | Learned dynamics interpolate memorized cases — failing precisely in the novel states where you need a simulator most |
| Data cost | Genie: 30k hours video used ([arXiv:2402.15391](https://arxiv.org/abs/2402.15391)); V-JEPA 2: >1M hours; TD-MPC2 multi-task: 545M transitions from 240 trained agents ([tdmpc2.com/dataset](https://www.tdmpc2.com/dataset)) | 10⁴–10⁶ hours of data | vs. zero for `setGravity(0,0,-9.81)` on known rigid-body dynamics |
| Survey position | Wang et al., manipulation world-model survey, May 2026, [arXiv:2606.00113](https://arxiv.org/abs/2606.00113); Long et al., Jul 2025, [arXiv:2507.00917](https://arxiv.org/abs/2507.00917) | "Rollouts can look coherent while violating physical constraints"; policies "may exploit model artifacts"; sims and world models framed as **complementary** | No survey says learned models replace analytic sims for known dynamics |

### A.4 Verdict

**Your judgment survives, but narrower than stated.** For a small classical-control prototyping project on known rigid-body dynamics in pure simulation, nothing in the literature recommends a Dreamer/Genie/JEPA-class learned world model — the field's own evidence (short trusted-rollout lengths, conservation-law violations, case-based generalization, 10⁴⁺-hour data costs, no ground-truth eval) supports "the sim IS the world model" *in-sim*. **Where it breaks:** the claim "known rigid-body dynamics" is false at exactly the two places your project physically lives — aerodynamics (NeuroBEM: 50% of quadrotor force error is unmodeled; TossingBot: drag bias costs 23 points of throw accuracy) and contact (real contact is stochastic, analytic models biased, and the soft-contact settings sims need for stability misrepresent rigid hardware — your rigid-contact artifact is a documented class of problem, and the literature's fix is *structured/residual learning on real data*, e.g. ContactNets, not more solver faith). The field's recommended architecture at the sim2real boundary is unambiguous: **analytic prior + learned residual**, which beat both parents in every head-to-head found. So: correct verdict for today's pure-PyBullet scope; the moment the project touches propwash, Re-dependent drag, or real hardware, the literature says add a learned residual — not a learned world model.

---

## SECTION B — Long-horizon agent capability + scalable oversight

### B.1 METR time-horizon metric + trend

- **"Measuring AI Ability to Complete Long Tasks"** — Kwa, West et al., METR, [blog Mar 19 2025](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/) + [arXiv:2503.14499](https://arxiv.org/abs/2503.14499) (v3 Feb 2026). Metric: the human-time length of tasks a model completes at 50% success. **Doubling ~every 7 months since 2019** ("may have accelerated in 2024"). Claude 3.7 Sonnet ≈ **1 hour** (TH1.1 re-estimate: 60.4 min [33–104]). Extrapolation: 1-month (167 work-hour) tasks between **mid-2028 and mid-2031**. *Takeaway: horizon growth is exponential and measured, not vibes.*
- **2025–2026 updates** ([metr.org/time-horizons](https://metr.org/time-horizons/), updated May 2026; [TH1.1, Jan 2026](https://metr.org/blog/2026-1-29-time-horizon-1-1/); [GPT-5 report, Aug 2025](https://metr.org/evaluations/gpt-5-report/)): post-2023 doubling re-estimated at **131 days**, post-2024 **89 days**. Frontier 50%-horizons: GPT-5 3h23m, Claude Opus 4.5 **4h53m**, Gemini 3.1 Pro 6h24m, Claude Opus 4.6 ~12h [5.3–60h] — with METR's own caveat that **measurements above 16h are unreliable** on the current suite. *Takeaway: mid-2026 frontier 50%-horizons are ~5–12h, doubling every ~3–4.5 months — with wide error bars METR itself flags.*

### B.2 Reliability falloff and the 50%→99% gap

- **80% horizons are 4–6× shorter than 50% horizons** (paper v1: "roughly 5×"; v3: "4–6×"), with the same doubling rate. Current 80%-horizons: ~25–90 min for most frontier models (e.g., GPT-5 ~38 min, Opus 4.5 ~49 min vs its 4h53m 50%-horizon). *Takeaway: each reliability step costs ~5× in horizon.*
- **99% horizons cannot be measured**: METR's [limitations note (Jan 22, 2026)](https://metr.org/notes/2026-01-22-time-horizon-limitations/) — "time horizons at 99%+ reliability levels cannot be fit at all without much larger and higher-quality benchmarks," and "a 50% time horizon of X hours does not mean we can delegate tasks under X hours." *Takeaway: reliability, not raw capability, is the binding constraint for delegation.*
- **Falloff shape/mechanism**: METR fits a logistic in log task length (R²≈0.80); **HCAST** ([arXiv:2503.17354](https://arxiv.org/abs/2503.17354), Mar 2025): agents succeed 70–80% on <1h tasks, <20% on >4h tasks. **Sinha et al.** ([arXiv:2509.09677](https://arxiv.org/abs/2509.09677), Sep 2025, ICLR 2026): small per-step accuracy gains compound exponentially into task length; identifies **self-conditioning** — models get *more* error-prone with their own past mistakes in context. *Takeaway: failure at long horizons is compounding per-step error amplified by self-conditioning.*
- **Implication for a ~10h agent case** (derived from the above, not a METR quote): 10h sits at/above the best mid-2026 50%-horizons and 3–10× beyond 80%-horizons — an unsupervised 10h block implies coin-flip-or-worse completion odds; METR's framing (incl. the [Claude Code/Codex note, Feb 2026](https://metr.org/notes/2026-02-13-measuring-time-horizon-using-claude-code-and-codex/), which observes these tools are used interactively with human check-ins) points to sizing check-in cadence to the **80% horizon (~1–3h)**, not the 50% one.

### B.3 Scalable oversight (recursive reward modeling, weak-to-strong, critique models, human+AI)

**NOT COVERED.** The search sub-thread for this material (Leike et al. 2018; Burns et al. 2023 weak-to-strong; Saunders et al. 2022 self-critiquing; McAleese et al. 2024 CriticGPT; Bowman et al. 2022 sandwiching; debate results) had not returned verified primary-source findings when compilation was cut off. I am not filling these in from memory — the specific numbers (PGR percentages, critique-assisted flaw-detection rates) need primary-source confirmation before citing.

### B.4 Human-oversight bottleneck / oversight cost vs agent throughput

**NOT COVERED** (same sub-thread). Partial adjacent material from the METR thread, verified: METR's limitations note explicitly states time horizon ≠ autonomous-run duration and that converting to delegation requires accounting for "how much time a human spends prompting AIs, waiting for generations, checking AI output… This process is nontrivial"; and METR found **no published recommended oversight interval or max-unattended-runtime measurement**. The AI-control literature (Greenblatt et al., auditing budgets) was queued in the uncovered sub-thread.

---

**Source count**: Section A — 13 primary sources verified; Section B — 7 primary sources verified (B.1–B.2); B.3–B.4 uncovered. Known soft spots flagged inline: DreamerV3 Nature volume/pages from metadata only; the literal "59 min" Claude 3.7 figure not confirmed (confirmed: ~50 min/~1h/60.4 min); no METR "4-month doubling" verbatim quote (confirmed figures: 131/89-day doubling estimates).
