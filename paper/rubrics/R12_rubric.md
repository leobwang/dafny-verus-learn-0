# R12 rubric — Driving the verifier + Lab α

Use CORE.md and design-judgment review. Grade methods and original artifacts,
not favorable results. A prospective calibration fixture cannot unlock a batch.
D45 live work and unavailable containers remain recorded skips, never passes.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R12_solutions.tex  sha256 bbc1ed910cdda559914285ba2bafe66e998a15758012355eaf95304c5e2d651a
paper/R12_problems.tex  sha256 b304d28e8797d7d528c83cce44b84361ad2a9f6f5f61ef498054af24ebfcd8ae
Solutions/dafny/R/R12_Driving/std/R12_Driving.dfy  sha256 f3e694f3554bbc627414284bb3c9d05a59e6292868542c9e84c4a19a93a7ae96
Solutions/verus/r/r12_driving/src/lib.rs  sha256 a42fe3dc981b3b92960f05fb46be468facb6b05a9e8492cc165f15404f5353e1
Solutions/harness/r/fvh_r/engine.py  sha256 609b38656306280ad9786261ad3b3c04191eaae9fb2e11ea9a79dfefb508a8a5
Solutions/tools/R12/profiler.py  sha256 7e0dd3a13ec0820531e516fbd7b5605c96c41317bead68da9eeecadb241f4d15

## Verifier anchors

- **Probe H:** hash exactly the unique PREREG-BEGIN through PREREG-END block.
  Recompute the actual plan bytes and compare its single plan-sha256 binding,
  and recompute bench/local/r/labalpha/FREEZE.toml's sha256 against the block's
  single freeze-sha256 line (fvh refuses a lab plan whose registration names
  another frame). Require the newest genuine prereg row with the same hash and
  every method dimension ≥ 3. A prereg-fixture row or gold fixture is never an
  unlock.
- **Probe B:** recompute each plan's calls as tasks × arms × 3 repeats × 10
  node calls from the plan and the frame (confirmatory: the frame's
  confirmatory tasks × the two primary arms; descriptive: the frame's
  descriptive tasks × the other two regimes) and check the sum, with any Claude
  calls and sentinels, against R12's ceiling (10,700 Qwen calls, 80 GPU-hours)
  at a measured cost per call. Baseline verification is no model call; a failed
  node is one call.
- **Probe M:** run fvh.stats.mde_paired_clusters_sim with the cluster sizes of the
  stratum's confirmatory clusters and the frame's power_sim_cell arguments; the
  registration's pasted call and output must equal it and the frame's values.
- **Probe F:** tools/R12/admit_forms.py checks actual native model/header and
  executable skeleton identity, with each call bound to a local proof callee.
  Its native mode checks a zero-hole proof-stage failing baseline and clean
  audit. It does not establish completion, three-seed robustness or live success.
- **Probe S:** compare snapshots before actor edits, full gates, audits and
  specfreeze. Profiler isolation and finite tests are not full gates.
- **Probe C:** pin local06.10 lines2635–2673 and01.12 lines429–456 exactly as B3/B4.
  Re-pin changed source before grading; use only that excerpt for card claims.
- **Probe R:** execute the report's Reproduce command and re-judge every claimed
  success in the pinned container from its original task. Missing apparatus
  leaves the claim deferred; never move agent execution onto the host.

## B1 — pre-registration (inside the course-fixed frame, D51, D62)

The frame (bench/local/r/labalpha/FREEZE.toml) fixes the contrast, estimand,
test, budget axis, aggregation, missing-result rule, resource accounting,
corpus, composition and K. Score what the learner writes; a registration that
changes or re-chooses a frame field, or names no frame, is held on the
dimension that field belongs to.

### hypothesis-precision

- **HP.a:** the claim restates, in the learner's words, what the fixed contrast
  can show on this corpus, an expected direction with a reason, and the result
  that would refute it; crossings of the descriptive curves are never claimed.
- **HP.b:** an 80% prediction interval for theta is written before any data,
  on the AUC scale, and consistent with the MDE the learner reproduced.
- **HP.c:** the stopping rule is complete: a run stops at success, the node
  cap or an exhausted frontier; a batch pauses at R12's 80 GPU-hour ceiling and
  resumes; the study stops at the frame's fixed N, never at an arm's early lead.

### budget-parity

- **BP.a:** the learner explains why the four arms are one engine at fixed
  (width, depth, priority), why each budget point is a prefix of one run, and
  why a failed node consumes its call and its parent's slot.
- **BP.b:** the plans' arithmetic recomputes (Probe B) against the ceiling with
  a measured cost per call (about 72 GPU-seconds on this corpus) and a
  truncation sensitivity line; an infeasible plan stays locked or is amended
  and re-graded.
- **BP.c:** each executed plan has its own binding and grade; no pilot or
  extra arm is free.

### variance

- **VA.a:** the justification of the fixed test is correct: clusters are the
  unit (repeats and budget points stay inside a cluster), one paired sign-flip
  test replaces per-budget tests so no multiplicity correction is needed, the
  interval is a whole-cluster bootstrap, and one test cannot locate crossings.
- **VA.b:** the MDE reproduction equals Probe M to the digits printed; the
  learner says which effects the design cannot detect and why more repeats
  barely move the bound (effect heterogeneity and the number of clusters
  dominate).
- **VA.c:** the learner's descriptive analyses use fvh.stats (bands from
  cluster_bootstrap_ci) and call pointwise bands pointwise.

### contamination

- **CT.a:** the regex and public strata are kept apart; the regex forms are
  course-derived (written after the pinned model's release, still previously
  exposed to the learner), the public ones possibly seen; the sealed R13/R14
  clusters are outside every plan.
- **CT.b:** draw exclusions, the walk's record and the deferred perturbation
  probe are cited by path, not re-derived; no unseen claim follows from fresh
  filenames.

### cheat-audit

- **CA.a:** the cheat surface names changed statements or levers, empty or
  unknown scores, malformed replies, host fallback and re-issued scored
  attempts, each with the gate that stops it (the lab gate's lever check, the
  source-frame guard, the full gate, container provenance, the ledger).
- **CA.b:** every accepted candidate is re-judged in the container; the
  learner's own engine cannot mark success.

### disclosure

- **DI.a:** freeze-sha256 and each plan-sha256 are actual, single and match
  (Probe H); seeds, settings and measured costs are filled before grading.
- **DI.b:** limitations are explicit: one model and hardware pin, the corpus,
  prompts and B = 10, Claude as subject and grader, the token-axis line as the
  only separation of localization from a shorter prompt. Frame fields are cited,
  not re-stated as the learner's own design choices.

## B2 — report; dimension: reproducibility

- **RP.a:** one command regenerates theta, its interval and test, the
  sensitivity line, the four curves with bands, the strata and language views,
  costs and truncation rates from immutable logs (fvh report R12 --labalpha).
- **RP.b:** original-task container re-judgement, audit/frame/freeze evidence for
  every claimed success; 20 transcript moments with actual artifact references.
- **RP.c:** list every deviation, score the prediction interval and retain all
  registered unrun/deferred ids. Software replay does not supply a live result.
- **RP.d:** the small Claude subset is descriptive; no crossing becomes a
  tested finding through post-hoc budget or family selection.

## B3–B4 — paper cards; dimension: card-fidelity

- **CF.a:** score all eight fields; minimum is the card score. Empty1, accurate
  source-bound sentence4. Silent fields should state what the excerpt lacks.
- **CF.b:** Cobblestone keeps checked prefixes and repairs prover-supplied goals;
  admit marks in-progress only. Four samples/invocation, depth≤5, invocations≤5,
  samples≤20; no transfer of those units to this lab's ten-node loop.
- **CF.c:** keep each benchmark/system denominator and union separate. Small
  subsets/no variance, oracle human hints, Coq/GPT-4-era context are limitations.
- **CF.d:** HyperTree uses AND-hyperedges, product child values and online
  policy/critic training. A critic is no oracle. Cumulative transductive versus
  fixed pass@k and huge training compute stay distinct from this course lab.
- **CF.e:** checker exploitation/misformalization show separate trust failures.
  Neither paper promises all task intents, zero variance or this native API.

## Code and oral review

Require native T1/H1/H2 each language and all five Python holes, exact original
contracts and zero-hole full gates. Native site texts name the witness, branch or
induction call the obligation lacks; statements and skeletons stay as shipped.
One Python file owns all holes because the frozen reference adapter overlays
one file: API facades may test provided types without discharging any hole.
Inspect stage/observe accounting, stable frontier selection, failure propagation,
strict schema handling, localization ambiguity, pure rendering and independent
frame checks. Do not read native success from stdout text or an exit code alone.
The toolwright's profiler keeps exact symbol/repeat/failed-result scope and
unavailable resources, immutable document snapshots and CLI/model frame hashes.
Keep two disjoint six-question viva draws and two paired PP subjects.

Gold is an author method exemplar, expected 4 where populated; actual unlock still
requires every final artifact. Flawed is expected ≤ 2 from quoted contradictions
and the probes above. Expected fixture scores are not measured grading sessions.
