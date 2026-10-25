# R07 rubric — Libraries: what they cost

Apply CORE.md; code-review bar `library-conventions`. Grade the learner's
actual evidence. Live Claude calibration and retriever-race runs remain D45
debt; native author controls are not experimental success rates.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R07_solutions.tex  sha256 fb97dac6165a04f0f508f2ff24bae9532149441623def93103fb2d8706a8ef5a
paper/R07_problems.tex  sha256 83e96a6c9771ee3984d5898f305292c41471f7b6a6234b491b1c3876fbdf7b9b
Solutions/dafny/R/R07_Libraries/std/R07_Libraries.dfy  sha256 15eed8189eb3e7f3b947637f55e023e53f440623f98ddbe3623906ffa210ef13
Solutions/verus/r/r07_libraries/src/lib.rs  sha256 2e4c6bac461bba34cd082309c81e6164a5049d4c39fb1b2b11237423ffc28b5d
Solutions/dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy  sha256 afd6370a3cc7f6aeb9dbedee6426137a7b98198776e813129f2740c09f1f3832
Solutions/verus/r/r07_libraries/src/agent.rs  sha256 2a7e647880f0deca576ae46fa41244ea33622be4d9c05c134aa59c44547c80eb

## Verifier anchors

- **Probe A:** hash the exact B1 source range; drift requires author re-pin.
- **Probe B:** instantiate the disputed library contract on the printed class
  or sample in native scratch. Keep type arguments and preconditions visible.
- **Probe C:** inspect the pinned library source and its native audit. Distinguish
  a proved lemma body from an external specification and an allowed dependency.
- **Probe D:** check the synthetic table with frozen fvh.stats.pass_at_k. Retain
  each task's n, c and k; reject invalid k rather than silently changing it.
- **Probe F:** source freeze and the agent's original task snapshot. A changed
  contract or an arm that saw a protected completion is not a matched delivery.

## B1 — Paper card06.5 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields answered; each field is graded separately, minimum
  is the card score. Empty field scores1; accurate paraphrase scores4.
- **CF.b:** identify Coq tactics, per-step finished-proof retrieval and the
  completed-proof acceptance oracle. Parsing or a single accepted tactic is
  not enough. A material contradiction scores at most2 with source lines.
- **CF.c:** preserve benchmark/subset/ablation denominators, project split,
  eligibility of retrieved proofs, time, hardware and prompt allocations.
  Relative improvements and percentage-point changes must remain distinct.
- **CF.d:** name the actual trust boundary and missing evidence. Do not infer
  assumption-free projects, matched baseline hardware or a measured course
  race. Unsupported generalisation scores at most2 with its missing premise.

## Gate, audit and first tries

Both hand units and completed agent files must gate at zero counted holes,
audit clean and preserve frozen contracts/imports. All five predictions and
both T1 test-outs have genuine first-try records; strict report passes. Named
library calls and their arguments are present, with exact qualified symbols
and reproducible found-by notes. A local broadcast version follows the named
call version; its group and scope are explicit. No broad unmotivated group
imports, added trust or solver overrides replace a missing proof step.

## Code-review focus — library-conventions

Read the actual lemma statement, instantiate each parameter, and justify its
preconditions. Distinguish finite Set from ISet views. Explain the transition
between the two flattening definitions instead of guessing a similar name.
Search-ladder notes cite the pinned source and the rung used; they do not
claim a source search proved a theorem. Delete a disputed step only in private
native scratch and retain the observation's scope.

## Audit debrief and evaluation evidence

The mismatch lab preserves native refusal and installed tool hashes; a failed
tool setup is not a theorem failure. The trust audit separates verified library
code, external specs and compiler/solver trust. The learner writes EVAL.md R-v0
by hand, stating task/attempt budgets, complete failure accounting, retrieval
allowance, per-task pass@k and aggregation, uncertainty, costs and exclusions.
The synthetic worksheet is labelled synthetic. A deferred race has no measured
winner; do not substitute protected reference success for model performance.
