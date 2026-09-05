---
tags:
  - concept
---

# 14 — Hobbyist hardware envelope (sim vs buildable reality)

> Produced 2026-09-06 by a research subagent at the human's request ("can I
> even build this at hobbyist level?"). Purpose: the load-bearing feasibility
> ranges — NOT a BOM — that (a) give the realism critic numbers to check
> claims against, (b) supply [[loop-engineering-analysis|validity-ledger]]
> rows for sim assumptions outside the buildable envelope, and (c) name the
> triggers for when full BOM engineering becomes earned. Anchors the
> geometry-vs-control milestone's pre-registration (per the
> [[goal2-observer-notes|situation-fidelity]] rule: literature anchors must be
> applicability-checked against buildable configurations).
> Agent output preserved verbatim below; citations NOT independently
> verified — verify load-bearing numbers at use time. Raw transcript: NOT
> AVAILABLE (task transcript file empty at archive time — third instance of
> the transcript-flush defect; digest preserved from the completion
> notification).

---

# Hobbyist Hardware Envelope — Drone-Catch Sim vs. Buildable Reality

*Research pass, 2026-09-06. Not a BOM — ranges/floors/ceilings/scaling laws with sources, per the brief. Evidence tags: **[spec]** = manufacturer spec sheet, **[meas]** = community-measured/benchmarked, **[assert]** = blog/forum claim or engineering inference not directly sourced.*

## (a) Summary table

| # | Sim assumption | Hobbyist-reality range | Verdict |
|---|---|---|---|
| 1 | Quad total mass 0.625 kg (`Drone.MASS`, must match URDF), body 0.18×0.18×0.04 m | Bare 5″ FPV frame+motors+FC+ESC AUW ≈ **580–700 g** [meas]; with a 6S 1300 mAh pack (~230 g) many builds land 620–700 g all-in [meas] | **Plausible but tight** — 0.625 kg already sits at the *top* of the bare-5″ range with **no line item for battery/FC/ESC/VTX**. Sim mass budget is silently incomplete for a real build. |
| 2 | Arm: 2× 0.20 m links, ~30 g each, throw sweep at high ω, catch needs a **back-drivable** shoulder with `torque_cap` | Geared hobby/digital servos (SG90/MG90S/DS3218/STS3215) are position-servo, not naturally back-drivable; true back-drivable = low-ratio BLDC+FOC (gimbal motor), which is much lower-torque | **Needs-change** — no single hobbyist actuator does both fast-sweep-throw and back-drivable-catch. Real build needs either a clutch/series-elastic element or accepting "backdrive via commanded low current," which no cheap servo firmware exposes cleanly. |
| 3 | 4-finger cage, 3–4 g/finger, constant-tension tendon (Yale-PRB style), contact sensing implicitly free | Printed finger mass of 3–4 g is physically plausible for small PLA/TPU links [assert]; Yale OpenHand hands use one servo + fishing-line/Spectra tendon [spec-ish, page confirms mechanism, not mass] — **exact total hand mass not found this session** | **Plausible (finger mass), NOT COVERED (total hand mass, contact-sensing gram cost)** |
| 4 | 5–10 min of active catch-play with manipulator aboard | 5″ builds get "a few minutes" of real flying on 6S 1100–1300 mAh [assert/meas]; every +100 g of battery buys only tens of seconds (1300→1800 mAh on 4S: +60 g for +30–60 s) [meas] | **Needs-change** — 5–10 min with a 150–300 g arm+hand payload aboard is optimistic; realistic hobbyist floor is closer to 3–5 min per pack, i.e. pack swaps mid-session. |
| 5 | Thrust-vectoring quad (parking-lot #11): 4 extra radial-tilt servos, "no thrust→attitude inversion" | Precedent exists (tilt-rotor quad/hexacopter research, e.g. Nemati et al. per-rotor tilt, 6-servo omnidirectional hex) but on **research-lab airframes**, not lightweight hobbyist FPV frames [assert] | **Needs-change / research-tier** — mass+complexity tax (4 tilt servos + linkages, conservatively 60–120 g) competes directly with the arm/hand payload budget on a 5″-class frame. |
| 6 | 10×10×3 m sim room | 3″ toothpicks explicitly recommended for "warehouses, gymnasiums, open halls," not living rooms [meas]; 5″ needs even more room | **Needs-change (labeling only)** — the sim room is a gym, not a home. Fine as a stated assumption, misleading if presented as "indoor" without qualification. |

## (b) Per-thread findings

### 1. Lift + mass budget
- 2207 2400KV-class motors on 6S with 5″ props: **~1400–1600 g static thrust per motor** [meas: RC community bench data]. Four motors → **5.6–6.4 kg total thrust**.
- Bare 5″ freestyle AUW: **580–700 g** [meas]; freestyle builds commonly run **TWR 6–10:1** static, i.e. well above the ≥2:1 *sustained* floor this project needs for 55–60° tilt maneuvers. Source: T-Motor Velox 2207/1750KV example, 6400 g thrust / 650 g AUW = 9.8:1.
- 3″ toothpick class: AUW **90–200 g**, TWR >10:1, but **absolute thrust is only ~150 g/motor** (1204 5000KV on 3S) → ~600 g total thrust [meas]. That's not enough absolute margin to also lift a 150–300 g manipulator; the class wins on agility/TWR-ratio, not payload capacity.
- **Answer to the class question**: 5″ (2207-class motor, ~580–700 g bare AUW) is the right class — it has ~5–6× its own bare weight in thrust headroom, i.e. plenty of *numerical* margin to add 150–300 g of arm+hand+ball, landing total AUW ~750–1000 g at TWR ≈ 6–8:1 static, still comfortably above the 2:1 sustained floor. The catch: sim's 0.625 kg drone mass is already *inside* the bare-AUW range before battery/avionics/arm/hand are added (see summary row 1) — the real build's total will be meaningfully heavier than the sim's number suggests unless the sim mass is reinterpreted as "airframe+propulsion+battery+arm+hand all-in," which the URDF doesn't document as such.
- Sources: [FPV Thrust-to-Weight Ratio Guide](https://www.unmannedtechshop.co.uk/blogs/knowledge-base/fpv-drone-thrust-to-weight-ratio-how-to-calculate-twr), [UAVMODEL motor sizing](https://blog.uavmodel.com/fpv-motor-sizing-guide-stator-volume-kv-selection-and-thrust-to-weight-ratio-by-build-type-2026-guide/), [Toothpick build guide](https://blog.uavmodel.com/toothpick-and-ultralight-3-inch-fpv-drone-build-guide-2026-parts-list-and-assembly/), [Oscar Liang 3″ toothpicks](https://oscarliang.com/3-inch-toothpicks/).

### 2. Arm + finger actuation
- **Micro servos** [spec]: SG90 — 9 g, 1.8 kg·cm stall @6V; MG90S — 13.5 g, 2.2 kg·cm @6V (metal gear); DS3218-class — 20 kg·cm digital metal-gear, 270°. None expose current/torque control; all are geared enough that "back-driving" them means grinding gear teeth, not compliant yield.
- **Serial bus servos with load feedback**: Feetech STS3215 — **55 g** [meas, servodatabase], 19.5 kg·cm@7.4V / 30 kg·cm@12V [spec], reports position/speed/voltage/current/load over serial, used in SO-ARM100-class arms. This is the closest hobbyist part to "torque-aware," but it's still a geared position servo doing torque *limiting* via current threshold, not true FOC torque control — good enough to cap force, not to feel like a compliant joint.
- **True back-drivable option**: low-ratio brushless gimbal motors + SimpleFOC (e.g. 2804 gimbal motor, ~300 g·cm torque, hollow-shaft, current-controlled) [spec/product listing]. Direct-drive/low-gearing brushless is explicitly called out as low-parasitic-torque/back-drivable in wearable/haptic literature [assert, PMC9041254]. Torque is an order of magnitude below the STS3215/DS3218 servos at similar mass, and needs an external FOC driver board + magnetic encoder (added mass + wiring + firmware work) — not a drop-in part.
- **The real tension** (flagged in summary row 2): throw-sweep wants high peak torque at speed (favors a geared servo); catch-absorption wants low-friction backdrive under load (favors direct-drive BLDC). No single cheap actuator does both. A real build likely needs either (a) a mechanical compliance element (torsion spring/series-elastic) between a geared servo and the joint — which the sim's rigid-arm model doesn't have — or (b) a lower-torque BLDC+FOC shoulder that can't hit the sim's throw ω without gearing that then defeats backdrivability.
- 2-link arm mass budget: sim's ~30 g/link (0.20 m) is plausible for a lightweight printed link *without* an actuator at the joint; the real mass driver is the actuator itself (55 g for one STS3215, ×2 for shoulder+elbow = 110 g) plus the arm structure — i.e., actuator mass, not link mass, dominates the arm's real weight budget.
- Sources: [SG90/MG90S comparison](https://zbotic.in/mg90s-vs-sg90-torque-accuracy-best-uses-compared/), [servodatabase SG90](https://servodatabase.com/servo/towerpro/sg90), [DS-series note](https://zbotic.in/high-torque-servo-motors-for-robotics-mg996r-to-ds3225/), [STS3215 spec/weight](https://servodatabase.com/servo/feetech/sts3215), [Feetech current feedback](https://www.robotshop.com/products/feetech-74v-19kg-serial-bus-servo-w-current-feedback), [2804 gimbal motor + SimpleFOC](https://www.amazon.com/Brushless-Outrunner-Magnetic-Encoder-SimpleFOCmini/dp/B0FXKN9YMJ), [backdrivable BLDC in wearables](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9041254/).

### 3. The hand
- Yale OpenHand project page confirms the mechanism (Model T42: two underactuated flexure-based fingers, each independently driven by a Dynamixel or hobby servo; Model O: differential/tendon topology matching commercial hands) but **does not publish part-mass or total-hand-weight figures** on the pages checked; CAD/fabrication PDFs would need to be opened individually to extract that (not done this session — **NOT COVERED**, exact hand mass).
- 3–4 g/finger (this project's sim value, also referenced in [[13-adaptive-underactuated-grasping|concepts/13]]) is dimensionally plausible for a small 3-segment PLA/TPU-scale finger [assert, engineering estimate — not a sourced measurement].
- Contact sensing cost not sourced quantitatively this session; qualitatively, the cheapest channel is current-sensing on the tendon servo (already "free" if using an STS3215-class servo with load feedback, per thread 2) vs. adding discrete FSRs/limit switches per finger (extra wiring + ADC channels + a few grams per sensor, cost scaling with finger count) — **NOT COVERED** with numbers.
- Sources: [Yale OpenHand Project](https://www.eng.yale.edu/grablab/openhand/), [Model M2 page](https://www.eng.yale.edu/grablab/openhand/model_m2.html), fabrication PDFs linked from that page (unopened).

### 4. Battery + endurance
- LiPo energy density: **140–250 Wh/kg pack-level** [assert/meas, ranges from multiple sources], mature packs commonly cited ~180–250 Wh/kg.
- 5″ freestyle on 6S 1100–1300 mAh (≈24 Wh) gets "a few minutes of real flying" [assert] — not a hard number, but consistent across sources.
- Payload penalty is steep and non-linear near the top of a pack's practical range: +60 g of battery (1300→1800 mAh on 4S) buys only **+30–60 s** [meas] — diminishing returns, meaning the fix for "+150–300 g manipulator payload eating flight time" is not "add more battery," it's accepting a shorter session or upsizing the whole airframe class.
- **Answer to the 5–10 min question**: not realistic on a single pack once carrying a 150–300 g manipulator; **2–4 min per pack is a more honest floor**, with pack swaps needed for a longer play session. This is a genuine sim-assumption risk if `main.py`'s scripted 22 s demo run were ever extended toward a "rally game" (parking-lot #5) that assumes indefinite endurance.
- Sources: [Grepow battery density blog](https://www.grepow.com/blog/grepow-high-energy-density-battery-solutions-for-commercial-drone.html), [Tyto Robotics LiPo guide](https://www.tytorobotics.com/blogs/articles/a-guide-to-lithium-polymer-batteries-for-drones), [6S 1100–1300 battery discussion](https://chinahobbyline.com/blogs/news/best-battery-for-5-inch-quad), [IntoFPV forum](https://intofpv.com/t-what-6s-lipo-capacity-for-a-5-quad).

### 5. Thrust-vectoring feasibility
- Per-rotor tilt designs exist in the research literature: independent per-rotor tilt quadcopters (Nemati et al.), a 6-servo omnidirectional tilt-hexacopter (first variable-tilt config for omnidirectional flight), paired-rotor-tilt quads (2 servos, front/rear arm pairs) [assert, summarized from search — papers not individually opened]. These are **research/lab prototypes**, generally on larger, more instrumented airframes than a 5″ FPV-class hobbyist build.
- No hobbyist/community precedent surfaced this session for a 5″-class *radial-tilt-per-rotor* build specifically (the geometry CLAUDE.md's #11 decided on). This is a real gap, not just an oversight — the search returned only academic hexacopter/quad tilt-rotor work.
- Mass/complexity tax: 4 tilt servos (order-of-magnitude 15–30 g each if using compact digital servos, more if using metal-gear high-torque units to fight gyroscopic loads from a spinning prop) + linkages + wiring harness to each arm tip. That's a conservative **60–150 g** tax before considering the control/allocation software work — directly competing with the 150–300 g arm+hand payload budget CLAUDE.md is trying to fit into the same airframe.
- Sources: [Design/Fabrication/Control of Tilt-Rotor Quadcopter](https://www.researchgate.net/publication/310327397_Design_Fabrication_and_Control_of_a_Tilt_Rotor_Quadcopter), [Over-Actuated Hexacopter Tilt-Rotor for Agriculture](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11768665/), [First Flight Tests, Quadrotor with Tilting Propellers](https://www.researchgate.net/publication/261503858_First_Flight_Tests_for_a_Quadrotor_UAV_with_Tilting_Propellers).

### 6. Indoor safety/practicality floor
- Prop guards: 4 PETG ring guards at ~12 g each add **~48 g (14–19% of AUW)** [meas], costing **8–12% flight time** and **10–15% top speed** [assert] — a non-trivial tax layered on top of the arm/hand/battery budget if guards are required for safety around a human-scale indoor "play" scenario.
- Room size: 3″ toothpicks are explicitly pitched as fitting "large indoor spaces like warehouses, gymnasiums, and open halls" [meas] — i.e., even the *smallest* hobbyist class wants gym-scale space, not a living room. The sim's 10×10×3 m room (walls at ±5, per CLAUDE.md's "Play area geometry") is consistent with a gym/warehouse assumption, not a home — worth stating explicitly rather than leaving "indoor" ambiguous.
- Noise: **NOT COVERED** — no quantitative dB data gathered this session; qualitatively well-known that 5″ props at flight RPM are loud enough to require hearing protection outdoors, which is a real practicality constraint indoors that wasn't quantified here.
- Sources: [PETG guard weight/performance](https://zbotic.in/drone-propeller-guard-design-3d-print-safety-frames/) (aggregated blog figures), [3″ toothpick space guidance](https://blog.uavmodel.com/toothpick-and-ultralight-3-inch-fpv-drone-build-guide-2026-parts-list-and-assembly/).

## (c) Sim parameters most at risk (ranked)

1. **`Drone.MASS = 0.625 kg`** — sits inside the bare-airframe AUW range for a 5″ hobbyist quad with no line item for battery, FC, ESC, or VTX. The sim's "total mass" almost certainly needs to be reinterpreted or increased once a real power/avionics stack is added; this is the single most consequential number in the whole envelope because everything else (thrust margin, tilt authority, hover time) scales off it.
2. **Back-drivable shoulder for compliant catch** (`torque_cap` in `spin_arm`) — no cheap hobbyist actuator is genuinely back-drivable at the torque/speed the throw sweep needs. This is a real mechanism gap, not just a tuning question; the sim's clean "torque cap" abstraction may not have a hobbyist hardware analog without adding a spring/clutch stage the sim doesn't model.
3. **Endurance assumption underlying any extended play session** (parking-lot #5, rally game) — real hobbyist flight time with a manipulator payload is likely 2–4 min/pack, not 5–10 min. Fine for the current 22 s scripted demo; a blocker if the rally-game idea is pursued without redesigning around pack swaps or a bigger/heavier (6″+) airframe.
4. **Thrust-vectoring platform (#11)** — the servo tax (60–150 g) competes directly, gram-for-gram, with the arm+hand payload budget on the same 5″-class frame; no hobbyist precedent found, only research-tier lab builds on larger airframes. This raises the bar on "earned complexity" for #11 considerably above what the CLAUDE.md's current framing ("blocked on nothing but the work") suggests.
5. **Finger/hand actuation reaction-torque assumption** ([[13-adaptive-underactuated-grasping|concepts/13]]'s "constant-tension tendon destabilizes a floating base") — real tendon actuation is one more servo (with its own mass, current draw, and reaction torque) stacked on top of an already tight mass/thrust budget; the sim's finding that active underactuation fights the flight controller will be *worse* in hardware, where the tendon servo also draws current the propulsion system needs.

## (d) Validity-ledger row candidates

- Sim assumes a 0.625 kg all-in drone mass; hardware floor is a **bare 5″ airframe alone already at 580–700 g**, before battery (~150–230 g for 6S 1100–1300 mAh) or the 2-link arm/hand payload — real AUW is likely 900 g–1.1 kg, not 625–700 g.
- Sim assumes the shoulder joint can be commanded with a clean `torque_cap` to yield smoothly under ball load; hardware floor is that **no sub-$50 geared hobby/digital servo is genuinely back-drivable** — real back-drivability requires a direct-drive BLDC+FOC joint at roughly 1/10th the torque of an equivalent-mass geared servo.
- Sim assumes 5–10 min of continuous catch-play; hardware floor is **~2–4 min of real flight time per pack** once a 150–300 g manipulator is aboard a 5″-class airframe, per the measured +60 g→+30–60 s battery-scaling curve.
- Sim assumes thrust-vectoring (#11) is "blocked on nothing but the work" (URDF + allocation matrix); hardware floor is a **60–150 g servo/linkage mass tax with no hobbyist-scale precedent**, only larger research-airframe tilt-rotor prototypes — the engineering lift is bigger than a software/URDF change.
- Sim assumes the 4-finger caging hand's 3–4 g/finger + contact-optional design is realistic; hardware floor is **NOT COVERED this session** for total hand mass and contact-sensing gram cost — flag as an open unknown, not a validated number, until the Yale OpenHand fabrication PDFs or an actual hobbyist replication build log are read.

## (e) Triggers for when full BOM engineering becomes earned

- **Trigger 1 — before any physical build decision**: once total AUW (bare airframe + battery + arm + hand + ball) is estimated to land within 20% of a chosen frame class's *sustained* (not static) thrust ceiling at the required ≥55–60° tilt angle, a full per-component BOM with measured (not spec-sheet) thrust curves at that tilt angle is earned — spec-sheet static thrust overstates available force at high tilt.
- **Trigger 2 — before choosing a shoulder actuator**: once the throw-sweep torque/speed requirement and the catch-absorption compliance requirement are both quantified in real units (Nm, deg/s, and a target yield force in N), a BOM comparing STS3215-class geared servos vs. gimbal-BLDC+FOC is earned — right now the choice is qualitative ("neither is quite right").
- **Trigger 3 — before extending session length past the current 22 s demo**: once a rally-game or multi-minute play session (parking-lot #5/#6) is actually scheduled for implementation, a battery/endurance BOM (pack chemistry, C-rating, swap cadence) is earned — not before, since it's pure overhead against the current scripted-demo scope.
- **Trigger 4 — before starting thrust-vectoring hardware work (#11)**: once a research-precedent tilt-rotor design at 5″-hobbyist scale (not lab-airframe scale) is found or independently designed, a servo/linkage BOM + mass-budget reconciliation against the arm+hand payload is earned — until then, #11 stays a design study, not a build candidate, per its own "decided but not built" status.
- **Trigger 5 — before finalizing the caging-hand mechanism for hardware**: once the Yale OpenHand fabrication PDFs (or a documented hobbyist replication) are actually read for mass/cost figures — closing the "NOT COVERED" gap in thread 3 — a finger/tendon/servo BOM for the hand specifically is earned.

---

**Not reached / explicitly NOT COVERED this session**: exact Yale OpenHand total hand mass and per-part breakdown (page lacked the data; fabrication PDFs unopened); quantitative contact-sensing gram/cost comparison (FSR vs. limit switch vs. tendon-servo current sensing); indoor noise dB figures; individual tilt-rotor paper mass/servo specs (summarized from search snippets, not read in full).
