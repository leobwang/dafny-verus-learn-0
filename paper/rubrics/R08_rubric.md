# R08 rubric — Abstraction

Use CORE.md and code-review bar library-conventions. Fixture compilation is
local validation; live model grading and contractor sessions remain D45 debt.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R08_solutions.tex  sha256 7682ab5336b1d2d0b27e80b376dd7f1bee0f847e9e423fc2cbb86a07dba7cbb1
paper/R08_problems.tex  sha256 4fa1af4f361ce9030adda17eba88adbfcbcc3a03f7af2ce00ba44d611357102e
Solutions/dafny/R/R08_Abstraction/std/R08_Abstraction.dfy  sha256 9a7f37c9f9e30c8dd3833b2669c7f6880105553884a4b52e9390b7b40245a2d4
Solutions/verus/r/r08_abstraction/src/lib.rs  sha256 495c984eb6832301f2e909210eeed8e149613d190a7a5c529ca12d5151fd0d8d
Solutions/dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy  sha256 781659838dd9d9ae164eeae7637383349d2323f6ce74fae704998bc5324bf845
Solutions/verus/r/r08_abstraction/src/agent.rs  sha256 da5f50863eb1e667c1373cae81385dfeb821817ab1c6be669f167d693f63aef4

## Verifier anchors

- **Probe A:** reproduce the exact B1 local source hash; drift needs author re-pin.
- **Probe B:** instantiate the claimed model on the learner's distinguishing
  word in fresh native scratch, retaining the original interface and binding.
- **Probe C:** remove a reveal in a private scratch copy, preserving opacity;
  retain the actual diagnostic and stage rather than guessing what was hidden.
- **Probe D:** run the original snapshot comparison on the disputed semantic
  binding, even if the changed implementation passes a native gate.
- **Probe F:** full-file gate and audit of the faithful agent repair, not a
  filtered goal or a parser-only result. The source plant is verify-stage with
  zero holes; Verus reports both the trait and implementation promise.

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

## B2 — The abstraction square (proof; dimension: abstraction-rigour)

### abstraction-rigour

- **A.a:** identify original domain, fixed semantic binding, implementation,
  backend instantiation and client promise. Each arrow names its obligation.
- **A.b:** a concrete nonvacuous word distinguishes full and shortened input;
  both outcomes and the fixed target must be justified.
- **A.c:** original precondition implies implementation precondition; stronger
  implementation promises imply the original result relation on its domain.
  Reversing a direction scores at most2 with the failing input obligation.
- **A.d:** changing the model changes the task even if the new task verifies;
  snapshot comparison protects model definitions, not just visible signatures.
  A reveal exposes the existing body locally and does not redefine semantics.
  A contradictory claim scores at most2 with Probe B/C/D as appropriate.

## Code and semantic debugger

All hand references and final deliveries must gate at zero counted holes,
audit clean, and preserve original interface/model/imports. H1/H2 supply
implementations under fixed models; H3/H4 use local reveals. A provided
abstract module is a specification parameter, not a trusted concrete engine.
The class model recognises exactly one-character words: other lengths remain
in the input domain and return the result prescribed by that unchanged model.
Check library preconditions and instantiated arguments in each backend call.
The full-word versus shortened-word agent defect must be repaired in the
implementation; accepting the model substitution is a fidelity failure.
Retain original diagnostic stage and both native and snapshot results.
The seventh bench card is explicitly course-derived, with source identity;
it is not an independently unseen benchmark. All five predictions retain
first-try records. No live session or performance rate follows from author
reference checks or expected calibration grades.

## Calibration fixtures

Gold:4 in both dimensions. Flawed: B1 pools heterogeneous rates (CF.c) and B2
reverses the precondition direction, changes the fixed model and misstates
reveal (A.c/A.d), so both dimensions score at most2 with quoted learner lines.
These are expected outcomes, not completed live grading sessions.
