# R08 rubric — Abstraction

Use CORE.md and code-review bar library-conventions. Fixture compilation is
local validation; live model grading and contractor sessions remain D45 debt.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R08_solutions.tex  sha256 b02d56103f8076cb10f3a25b5cfc61c843482535a4412684242cf11c99438801
paper/R08_problems.tex  sha256 7fd6855e551a72f428c28eaab424f6166dd3b9c4333ca1e9e8e660f53fc4c29c
Solutions/dafny/R/R08_Abstraction/std/R08_Abstraction.dfy  sha256 9533e71d9b5d498fec4fd8294b68ec3c43a499358797c6e711e743e1c3c9fbf0
Solutions/verus/r/r08_abstraction/src/lib.rs  sha256 b5cb28400d349a5436f06a409ceb553290cf5cf20344cc768b00faa2d6b00650
Solutions/dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy  sha256 5304f661af07633faa2ba9fcac79e225aa8df1feb9364b08499c71d729dd6e62
Solutions/verus/r/r08_abstraction/src/agent.rs  sha256 8cf139beb333088a2d8535c93a5567b4c40ddf7329571830c9a40b5d883868c9

## Verifier anchors

- **Probe A:** reproduce the exact B1 local source hash; drift needs an author re-pin.
- **Probe B:** evaluate the learner's B2(b) counterexample in fresh native scratch: the
  derivative, the trimmed term, and both `Matches` facts as `ensures` of one lemma
  (`Matches(st, [c] + w)` true, the trimmed derivative's match false).
- **Probe C:** a refinement of the step-matcher interface that adds a `requires` to
  `MatchWord`, and one that adds an `ensures`; retain both stages (resolve, verify).
- **Probe D:** run the original snapshot comparison on a delivery that changes `Lang`,
  even if the changed engine passes the native gate.
- **Probe F:** full-file gate, audit and `scripts/specfreeze --check R08` of the faithful
  agent repair, never a filtered goal. The source plant is verify-stage with zero holes
  and one error, at the pruning function's language-preservation postcondition.

## B1 — QED at Large (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** grade all eight fields separately; the minimum is the card score.
  Empty fields score1 and accurate source-bounded paraphrases score4.
- **CF.b:** identify a survey and the kernel/proof-object acceptance distinction;
  distinguish tactics producing subgoals from an accepted completed proof.
- **CF.c:** preserve the heterogeneous denominators and pre-LLM scope. A common
  agent rate, uniform budget or interval invented from the numbers scores at
  most2, quoting source and learner lines.
- **CF.d:** retain information hiding, refinement and maintenance intent without
  claiming the survey directly evaluated these Dafny/Verus exercises. Missing
  artifact and runtime evidence must be labelled unavailable.

## B2 — Refinement obligations (proof; dimension: obligation-rigour)

### obligation-rigour

- **O.a:** all four obligations listed with the engine's definitions substituted
  (StartLaw, FeedLaw, FinalLaw, `MatchWord`'s postcondition), each with the side
  that discharges it (engine, layer lemma, interface) and the instrument (verification;
  the statements also by the freeze). A missing obligation, or `MatchWord` said to be
  re-proved by the engine, scores at most 2.
- **O.b:** a concrete counterexample to FeedLaw on which `Trim` fires (a
  `Star(Empty)` that a derivative exposes), both sides evaluated, the false one named;
  the failure located in the engine's lemma or FeedLaw against the postcondition stated
  in the given interface file. An instance on which `Trim` does not fire, or no
  evaluation, scores at most 2 (Probe B).
- **O.c:** a changed `Lang` proves a different task: the client or the frozen statement
  is the reference, and `scripts/specfreeze --against` refuses the delivery. Calling the
  changed engine a repair scores at most 2 (Probe D).
- **O.d:** postconditions may be added and are checked (Dafny against the inherited
  body, Verus against the implementation's); preconditions may not (both refuse at
  resolution), with the client argument. A reversed direction scores at most 2 (Probe C).

## Code and semantic debugger

All hand references and final deliveries gate at zero counted holes, audit clean, and
preserve the shipped statements (`scripts/specfreeze --check R08`). H1 is the range-star
engine's start fact over A2's class API, H2 `PartsLaw`, H3 the alternative-set step law,
H4 its final law with the engine's own opaque model revealed in H4 alone. Under
library-conventions, look for: given helpers used as given (no re-implementation of
`Parts`, `FeedAll`, `RangesClass`), reveals scoped to the proof that needs them, witness
indices named rather than left to the solver, and no lever (`{:induction}`, resource
attributes) added. The agent's defect is in the engine (`Prune` / `prune_exec` drops `Eps`
alternatives); the faithful repair edits the pruning rule and keeps `Lang`, `Res` and the model;
accepting a changed `Lang` is a fidelity failure. Retain the original diagnostic and both
the native and the freeze results. The seventh bench card is course-derived, with its
source identity, not an unseen benchmark. All five predictions keep their first-try
records. No live session or rate follows from author reference checks.

## Calibration fixtures

Gold: 4 in both dimensions. Flawed: B1 pools heterogeneous rates (CF.c), and B2 omits
`MatchWord`'s obligation, gives a counterexample on which `Trim` does not fire, accepts a
changed `Lang` as a repair and reverses the precondition direction (O.a–O.d), so both
dimensions score at most 2 with quoted learner lines. These are expected outcomes, not
completed live grading sessions.
