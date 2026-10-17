# R12 rubric — Driving the verifier + Lab α

Use CORE.md and design-judgment review. Grade methods and original artifacts,
not favorable results. A prospective calibration fixture cannot unlock a batch.
D45 live work and unavailable containers remain recorded skips, never passes.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R12_solutions.tex  sha256 bbc1ed910cdda559914285ba2bafe66e998a15758012355eaf95304c5e2d651a
paper/R12_problems.tex  sha256 b304d28e8797d7d528c83cce44b84361ad2a9f6f5f61ef498054af24ebfcd8ae
Solutions/dafny/R/R12_Driving/std/R12_Driving.dfy  sha256 fc09a5fa307b2afca91dd98b3ae2fa8d290fdace65a03203fbf21533124893f6
Solutions/verus/r/r12_driving/src/lib.rs  sha256 e2d8c76d32ee777f1c32f91525485adab5cef83458b0185ff7dd667177b4db0c
Solutions/harness/r/fvh_r/engine.py  sha256 609b38656306280ad9786261ad3b3c04191eaae9fb2e11ea9a79dfefb508a8a5
Solutions/tools/R12/profiler.py  sha256 7e0dd3a13ec0820531e516fbd7b5605c96c41317bead68da9eeecadb241f4d15

## Verifier anchors

- **Probe H:** hash exactly the unique PREREG-BEGIN through PREREG-END block.
  Recompute the actual plan bytes and compare its single plan-sha256 binding.
  Require the newest genuine prereg row with the same hash and every method
  dimension≥3. A prereg-fixture row or gold fixture is never an unlock.
- **Probe B:** recompute40×4×3=480runs,480×10=4800calls,1200calls per Qwen arm;
  Claude10×10+≤10sentinels≤110calls. Check pilots/public slices within the
  registered totals, and each arm's tokens/GPU/wall cost within10GPU-hours.
  Baseline verification is no model call; malformed generation is one node.
- **Probe M:** run fvh.stats.mde_two_proportions at the registration's actual
  algorithm-cluster n, baseline, pairing and family-adjusted alpha. Repeats do not
  create independent tasks. Reproduce Holm and bootstrap from the same logs.
- **Probe F:** tools/R12/admit_forms.py checks actual native model/header and
  executable skeleton identity, with each call bound to a local proof callee.
  Its native mode checks a zero-hole proof-stage failing baseline and clean
  audit. It does not establish completion, three-seed robustness or live success.
- **Probe S:** compare snapshots before actor edits, full gates, audits and
  specfreeze. tools/R12/check_clients.py gates actual source before compiling
  finite observations. Profiler isolation and finite tests are not full gates.
- **Probe C:** pin local06.10 lines2635–2673 and01.12 lines429–456 exactly as B3/B4.
  Re-pin changed source before grading; use only that excerpt for card claims.
- **Probe R:** execute the report's Reproduce command and re-judge every claimed
  success in the pinned container from its original task. Missing apparatus
  leaves the claim deferred; never move agent execution onto the host.

## B1 — pre-registration

### hypothesis-precision

- **HP.a:** name primary localized-minus-raw best-first contrasts, budget points,
  secondary regime comparisons, direction, refutation and unresolved crossings.
- **HP.b:** define cumulative success from the full original-task gate and exact
  algorithm-cluster paired estimator. Score0, missing diagnostics or empty obligations
  cannot mean accepted. Native source/model/code/context bindings stay explicit.
- **HP.c:** state80%prediction intervals before data and all stopping rules.
  Stop on fixed cap, success or exhausted frontier, never an arm's early lead.

### budget-parity

- **BP.a:** one fixed parametric engine, independent10/1/fifo, repair1/10/lifo,
  best3/10/best and the identical best config with raw feedback. Each budget
  point is a prefix of one ten-node run; no prefix-specific tuning or reruns.
- **BP.b:** malformed samples count nodes/width; failed calls remain metered.
  Distinguish ten model generations from initial baseline and closure turns.
- **BP.c:** every product and per-arm cost recomputes. Pin a measured throughput
  assumption;7.5GPU-seconds/call is a ceiling calculation, not observed speed.
  An infeasible plan stays locked/deferred or is amended and re-graded.
- **BP.d:** pilots and the unused public slice are not extra free calls. A
  changed or separately executed plan needs its own exact binding and grade.

### variance

- **VA.a:** the20paired-language algorithm clusters are the uncertainty units; keep all repeats/budgets/arms
  paired inside a task. Register repeated runs and actual request seeds;
  Claude repeated runs are not controllable seeds.
- **VA.b:** use fvh.stats for paired permutation tests, Holm over the registered
  family and bootstrap intervals. State resampling counts/seeds. Pointwise
  intervals cannot be described as simultaneous bands without a valid method.
- **VA.c:** MDE matches Probe M at independent n=20algorithm clusters and adjusted alpha. Name
  approximation/correlation limits and report uncertainty around crossings. At
  n20/baseline0.5/alpha0.05÷40/pairedTrue the frozen call returns infinity;
  a truthful exploratory/underpowered disclosure is required. No finite value
  or post-hoc multiplicity reduction is accepted as a repair.

### contamination

- **CT.a:**40admitted local forms,20per language, exact hashes and provenance;
  previously seen course-derived goals remain disclosed as such.
- **CT.b:** public slice is from an unused pinned pool and possibly seen by the
  models; record draw exclusions, source commits and any novelty/perturbation
  audit. No claim of unseen tasks follows from fresh filenames or authorship.

### cheat-audit

- **CA.a:** original model/spec/code/levers preserved; renderer and independent
  source-frame guard are separate. Approve only local proof callees at proof
  sites. No model-returned verdict or tool flag controls acceptance.
- **CA.b:** localized signals use only candidate-native documents and trusted
  spans, never hidden references. Unknown paths remain unlocalized; unavailable
  phase/count/score remains unavailable. Frozen provenance and container rules
  bind every accepted candidate and final re-judgement.
- **CA.c:** infra failures, malformed, killed, truncated and deferred attempts
  follow frozen accounting; truncation sensitivity is disclosed. No favorable
  retrying or fabricated grade/event unlocks. Administrative skips stay unrun.

### disclosure

- **DI.a:** small-scale model substitution, one hardware/solver pin, task exposure,
  Claude subject/grader and missing live apparatus are explicit limitations.
- **DI.b:** final prompt/task/engine/adapter/config hashes, generation settings,
  seeds, intervals, plan digest and current measured cost are actually filled
  before grading. A prospective exemplar with missing material stays locked.

## B2 — report; dimension: reproducibility

- **RP.a:** one command regenerates all curves, language strata, paired effects,
  corrected tests, intervals, costs and truncation rates from immutable logs.
- **RP.b:** original-task container re-judgement, audit/frame/freeze evidence for
  every claimed success;20transcript moments with actual artifact references.
- **RP.c:** list every deviation, score prediction intervals and retain all
  registered unrun/deferred ids. Software replay does not supply a live result.
- **RP.d:** small Claude subset is descriptive; uncertainty does not become a
  significant crossing through post-hoc budget or family selection.

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
contracts and zero-hole full gates. Invariants connect count/first rejection to
original flags; executable bodies and termination annotations remain provided.
One Python file owns all holes because the frozen reference adapter overlays
one file: API facades may test provided types without discharging any hole.
Inspect stage/observe accounting, stable frontier selection, failure propagation,
strict schema handling, localization ambiguity, pure rendering and independent
frame checks. Do not read native success from stdout text or an exit code alone.
The toolwright's profiler keeps exact symbol/repeat/failed-result scope and
unavailable resources, immutable document snapshots and CLI/model frame hashes.
Keep two disjoint six-question viva draws and two paired PP subjects.

Gold is an author method exemplar, expected4where populated; actual unlock still
requires every final artifact. Flawed is expected≤2from quoted contradictions
and the probes above. Expected fixture scores are not measured grading sessions.
