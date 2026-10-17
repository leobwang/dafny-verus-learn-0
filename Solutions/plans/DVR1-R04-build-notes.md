# DVR1 R04 build checkpoint — 2026-10-17 UTC

Private coordination. Continue until Basic is done; challenges follow R core.
No model call. User D45 defers live Claude checks as debt, never as passes.
R03's separate OD8/Unicode-adapter packaging blocker is recorded and parked
under Solutions/plans/drafts/R03. No tier exception or gate weakening adopted.

## Canonical release/integration

Initial local Q Basic is39ba47b, sole parent main6f453d0, also basic-candidate.
Old Q authoring40a9b5a is preserved as authoring-q-archive-20261017. Canonical
../dafny-verus-learn-0-authoring branch authoring was recreated from Basic.
R01/R02 and tooling/draft checkpoint were transplanted by cherry-pick:
151bfa0,9366fd9,0d275c7,687e538,cad7034; integration metadata3482978.
Q18 shipped; R01/R02 candidate shipped; R03/R04 and later planned.

Canonical combined-tree CI is active at
build/ci/20261017T061521Z-1670472/; selected static,verify-r-dafny,
verify-r-verus,paper,rubric,harness, then R01/R02 pins on success. Driver
session57489, logs /tmp/dvl0-dv7-freeze/r-integration*. Basic waits at39ba47b
until that bar and final leak/settings checks pass. No external push.

## Active R04 draft

Worktree ../dafny-verus-learn-0-r04-authoring, branch authoring-r04 at659b565
(legacy R checkpoint, not yet transplanted onto canonical Basic history).
It is in AUTHORING mode; uncommitted core/specimen/slot files. Toolchain is
an ignored symlink to primary. Registry remains planned: do not run full
course-map/CI on this incomplete draft or claim module acceptance. Preserve
source bytes and transplant only the final R04 content onto canonical authoring.

- Paired six-hole cores (T1,H1–H5), A1-only. Unanchored Occurs is given.
- Both completed standalone references gate:17 verified,zero holes/errors each.
  Both standalone source drafts:verified,six holes,zero errors each.
  Canonical logs /tmp/dvl0-dvr1-r04/core-results-quantifier.log and JSONs.
- H4d definition hole has ensures true ONLY as a warning-bearing marker:
  no semantic guarantee is supplied. This avoids Dafny G4's silent no-ensures
  hole; three provided client checks constrain completion. H4v is uninterp.
- Reference H1/H2/H3 Dafny reuse protected spike RX_Items; Verus reference is
  authored/captured on the current pin. Verus concrete Star folds need explicit
  smaller Matches facts before the enclosing assertion. Given prefix-negative
  checks use concrete slice facts. The Verus forall proof uses implies, which
  brings antecedent bounds into its body; ==> did not justify its branch fact.
- All six predictions are drafted: P1/P2/P6 switches in core, P5 switch in its
  own planted Pos specimen, obligation P3/P4. Sixteen specimens/cards/audit
  deliveries exist, all unfilled. P6v now has the planned borrowed Re/Vec
  parameters, not a spec Seq as an exec input. Native prediction captures pending.

## Native work in progress

/tmp/dvl0-dvr1-r04/check_controls.py runs all five lemma T/H empty-body controls
per language (H4 definitions need separate false/true controls with given checks).
Session23532, log controls.log, 16GiB scope. All five Dafny controls fail as
required; Verus controls are still running. Do not start another R native lane
until it completes. The concurrent canonical integration lane is32GiB; combined
solver budget48GiB and host reserve remain in force.

Initial generator scripts build_core.py/build_verus_core.py/build_predictions.py
are STALE after native fixes and P5/P6 adjustments. Do not rerun them. Standalone
prototypes are private and include exact public A1. Main P5 marker was moved to
its specimen after those core captures; no proof semantics changed. Final
canonical generated units and module gate still required after completing kit.

## Next

1. Finish empty-body controls; capture all predictions, supplied tests and audit
   drill. Resolve any local failure rather than waiving it. Check H4 false/true
   definitions against the three fixed positive/negative/empty checks.
2. Build audited-prover agent with two true claims and one genuinely false
   planted statement; preserve the statement and capture a counterexample.
   Plan §6.4 and protected R-author-notes §5 govern its partial-delivery contract.
3. Paper12.5 plus classify-four-specs and wp/VC problems; rubric and fixtures;
   bank12/two disjoint draws/two bilingual parallels; chapter360min; bench-card3.
4. Canonical registry/units/counts/freeze/prediction/chapter pins; leak patterns;
   actual admission, completed-reference workflow, seed stability, focused CI.
5. Restore STUDY before staging/committing. Archive private native evidence.

Further draft work: agent source pair has3 holes each and the original false
third statement. Protected references are explicitly author analyses: proofs
of two true claims and a counterexample theorem, with the false original
quoted, not a changed learner delivery. Copying them over the source must
fail snapshot freeze; capture that negative control, never call it an accepted
full-file completion. Protected R04-agent-refutation-report.md explains scope.

firsttry's marker parser now accepts exactly R04.P5d's runtime-check specimen
and R04.A1d/v's agent placement metadata. The latter yields no covered-line
exemption, so ordinary lints and native instruments remain active.117 existing
and new static tool tests pass, one skip. P5's marker trails the actual expect
line. The final three-line test cleanup changed no covered behaviour.

Paper card12.5 source range5297–5333 is pinned; B2 uses Chr('m')/mn, distinct
from P2's pair; B3 derives an integer wp across a conditional. Learner pair,
reference and gold/flawed fixtures all compile (paper.log,5/5). Rubric drafted.
H4 definition twins now carry false/true cfree controls; all three supplied
positive/negative/empty-prefix checks remain. Their native controls follow.

Full prototype empty-body sweeps include every applicable automation mode,
including BV's120-second cap at three seeds. T1v/H1v/H2v all fail the gate's
variants; BV harness kills count only as the documented bounded-mode failure,
not successful proof. This explains the long run; it is not a model call.
Do not start a second R solver lane. Queued prediction driver session1507
waits for control parent1660159 to finish before starting its16GiB scope.

Canonical R integration first run failed only37 stale Q chapter input pins
caused by R-only additions to the shared options files. All37 were recaptured
through normal tools and every chapter byte stayed identical. Δ252 records
that evidence. Canonical authoring405a9cf runs static again at
20261017T062822Z-1716277, then R01/R02 pins; driver17726. Native R,paper,
rubric,harness already pass on3482978. Basic remains39ba47b pending final bar.

## Current packaging state — supersedes the initial worktree/registry notes

Local Basic and canonical authoring are66987d9: Q01–Q18 and R01/R02 shipped,
main remains6f453d0 clean, initial Q squash39ba47b remains basic-candidate.
R04 worktree branch authoring-r04 has been rebased onto66987d9 via a temporary
stash, reapplied cleanly. It is AUTHORING with R04 now registered authoring;
R03 remains planned/parked. No legacy ancestry will be merged for R04.

All415 static tests pass/one skip in69s. New clause-free Verus definition
comparison preserves the old bodyless signature hash while omitting the
completed body; changed signatures/contracts still fail. Reference lint is
clean after fixing Reference Solution headers, cfree placement and explicit
reference-only annotations on enabled supplied checks. Native instruments are
unchanged. Six guarded runtime/assumption specimens use P5 planting metadata
only with both P1/P5 guards; the A1 markers grant no exemption. Ten focused
marker/hash regressions pass. Initial packaging test failures remain private.

Actual generated-unit reference counts: Dafny17/min9, Verus10/min7. Sources
verify with6holes/errors0 each; agents verify with3holes/errors0 each. All
six reference predictions pass,20 chapter entries captured,13 non-P sidecars
captured. Chapter lint is6306 words/6predicts/3diagrams/20fences. One shipped-v
capture was recaptured after the agent CONTRACT's comment spacing changed,
since the crate capture pins every source file. No native body changed there.

Native core references were aligned to practise their declared forall-intro
and exists-elim constructs in both H2/H3 proofs; full current references gate
at17 tasks each in self-contained prototypes (V's generated unit excludes
its compiled A1 dependency tasks and reports10). The prior empty-body variants
erase those annotation regions completely. Canonical admission remains required.
Both agent author analyses gate/audit; report-as-delivery rejection is confirmed
for each language. This is not a successful proof of the original false claim.

P2's four forcing/permission claims were separately proved in both languages:
p2-d.log/p2-v.log each11verified/0holes. Predictions native captures are in
prediction-checks; final card-c1v/c2v/c2d replacements reach verification rather
than failing trigger inference. post-controls-final.log includes all four
H4constant-definition controls, six bank probes and both snapshot rejections.
No live model. All five paper documents compile; minor numerical spacing was
then corrected, and final CI/fixture compilation will cover those current bytes.

Next: finish staging checks/leak scan, commit source-hollow candidate in STUDY;
start canonical admission, focused CI and completed-reference study workflow
under a combined48GiB solver budget (e.g. separate16GiB scopes). Do not copy
the agent analysis over the original task as a passing delivery. Firsttry's
report excludes A outcomes; retain original agent source in the study workflow,
verify the author analyses separately and assert the frozen replacement fails.
Archive final evidence; integrate R04 by fast-forward/cherry-pick only after
its complete local bar. Then continue R05. No external push or Claude call.
