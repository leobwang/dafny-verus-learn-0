# R05 rubric — No goal state

Apply CORE.md. Code-review bar: **proof-shape**. Live model calibration is
deferred under D45, never inferred from local fixtures.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R05_solutions.tex  sha256 5024903c3980a0bed63640d9e6efccbb5d9dc326ab2295f79e7fa300576545f2
paper/R05_problems.tex  sha256 e3eafd5a817257ea545f492ffb1ca83a8a278bb7c9ebffb46e0a44b078b2684e
Solutions/dafny/R/R05_NoGoalState/core/R05_NoGoalState.dfy  sha256 fd9dd082da9f179f36a9dc4ec16c7391056d5706bffebfc579459fc202a0db07
Solutions/verus/r/r05_no_goal_state/src/lib.rs  sha256 23816a50a8d95870d0503a76c033a8cb9c23885c12f5b0d23ea58198384ce932
Solutions/harness/r/fvh_r/variance.py  sha256 edff314cf64487c12648da4c41ab06aaf1b04e479728df4dd4b4c786583977d7
Solutions/dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy  sha256 80ae327456f228e3207e25c274954473423f5d04efe93fc2fa32bb16a27c1a31
Solutions/verus/r/r05_no_goal_state/src/agent.rs  sha256 0203188c1a0a4486c3240bb3914767da2e9f602df261c1042fb6ede285d55b6e

## Verifier anchors

- **Probe A:** reproduce the exact local card source hash; drift requires author re-pin.
- **Probe B:** a disputed implication or deletion in B2 is tested in scratch with the pinned wrapper; retain hypotheses and command scope.
- **Probe C:** reproduce B3 arithmetic with standard-library statistics and the frozen quantile convention; preserve the prescribed resamples.
- **Probe D:** for a claimed proof simplification, delete one learner step in scratch and rerun the same selected symbol. A minimality claim needs more evidence.
- **Probe F:** snapshot freeze protects original agent statements; complete gates and clean audits remain required.

## B1 — Card 06.3 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields are filled, each accurate paraphrase scores 4; an empty field scores 1.
- **CF.b:** preserve164/189, the inclusion of assisted success, task categories and the 16 percent intervention scope. A material contradiction scores at most 2 with learner/source lines.
- **CF.c:** distinguish check counts from a time/token/dollar budget and one development from a cross-development estimate.
- **CF.d:** acknowledge absent agreement, model, baseline and reproduction evidence; grade the card by its minimum field score.

## B2 — Facts per line (proof; dimension: obligation-reading)

### obligation-reading

- **O.a:** identify the binding and the distinct asserted bounds/equality at every numbered line.
- **O.b:** justify each from available hypotheses and explain the bridge to the exact postcondition.
- **O.c:** describe what an assert-by block exports and the scope of a selected-symbol observation.
- **O.d:** distinguish a dependency account from a solver deletion result and a unique-minimality claim; use Probe B/D when formal assertions are disputed.

## B3 — First intervals (statistics; dimension: statistical-interpretation)

### statistical-interpretation

- **S.a:** use sample standard deviation with divisor n-1 and CV=sd/mean; show enough precision or formulas to check.
- **S.b:** give all five resampled means and both interpolated positions/endpoints under the specified convention.
- **S.c:** distinguish an interval for a population mean under sampling assumptions from a prediction/guarantee about an individual next duration. A false guarantee scores at most 2 even with correct arithmetic.
- **S.d:** state the fixed experiment, small sample/resample budget and plausible dependence or host effects; a seed does not remove them.

## Code and agent review

Both native hand units and the Python file gate at zero holes; audits and
freeze pass. H4 retains its given branch, choice and measure (the recursive call is the learner's, D84).
Helper contracts expose proof steps, assertions have reasons and recursion
has an intelligible decreasing argument. Missing or altered measurements
must not become fabricated zero values or silently dropped rows.

Review the actual VARIANCE, LATENCY and OBLIGATION logs. Keep languages,
tasks, command scopes and the two kinds of seed separate. The acceptance
tests cover parser/statistical composition, not provenance or experimental
comparability. The contractor's transcript must show per-edit fast-channel
runs and exactly one full final native gate, last. A later learner deletion
probe is separate post-run review. Check statements against the saved snapshot,
the gate's entire scope and every helper's hole status before accepting a delivery.

## Calibration fixtures

The gold fixture supplies all three arguments; expected4 in each dimension.
The flawed fixture retains the numerical calculation while falsely claiming
coverage of the next duration: B3 scores at most 2 at S.c, with quoted learner
lines. Contradictory caveats elsewhere do not erase that false claim. No live
Claude grading pass is claimed from compilation or this expected outcome.
