# R03 rubric — Modules and APIs

Apply CORE.md; predictions first, reference last. Grade the learner's words
and code, not similarity to this reference. Code-review bar: `it-reads`.
Live Claude calibration remains deferred under D45; compiled fixtures do not
stand in for a calibration session.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R03_solutions.tex  sha256 9f6a929d13259b739485ac5e86c1069f15efeece8dc7378c1c61ebd88960da10
paper/R03_problems.tex  sha256 d5837cff75180715a141adb5ccdd4f83523992bbd1c7828f709224321ae5eda6
Solutions/dafny/R/R03_Modules/core/R03_Modules.dfy  sha256 3a5ac69171b49998e3fb46541af835c0fc7a346434bc37c0d84af71c0425a06c
Solutions/verus/r/r03_modules/src/lib.rs  sha256 249dcf4dfc771ce308405cf9a4869d266a8b101b64f3daa43761ea7dcc189115
Solutions/dafny/R/R03_Modules/agent/R03_AgentApi.dfy  sha256 43aa3e08c71b60d737aff502690b1eb68694061c016082db6ea9ee8fe68878d4
Solutions/verus/r/r03_modules/src/agent.rs  sha256 e71a2e4d4db4b3cd412cb156d3633d530f1e22d6a313aca002c1a5ac39b5ddd0

## Verifier anchors

- **Probe A, source:** hash exactly the printed cheatsheet range. A mismatch
  needs an author re-pin. Do not penalize a learner for source drift.
- **Probe B, API:** reproduce a disputed client assertion in scratch with the
  same export/view boundary and only the claimed contracts. Run the R03 wrapper
  context and cite the actual obligation. An exec function's body is not its
  postcondition; a visibility change is not a strengthened contract.
- **Probe C, boundary:** encode a disputed minimum/maximum scalar or gap-neighbour
  case using the supplied model and helpers. Run it before claiming a verifier
  outcome. Do not add a trust specification for an unsupported conversion.
- **Probe D, deletion:** remove only a disputed learner step in scratch and run
  it. Unnecessary proof-reading aids are notes at this bar, not findings.
- **Probe F:** scripts/specfreeze --check R03; preserve given code, statements,
  export opacity and the representation. On the agent use the saved original
  snapshot with --against; a changed statement cannot be excused by a green gate.

## B1 — Paper card03.2 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields answer their questions. An empty field scores1.
- **CF.b:** a material contradiction scores at most2, with the actual learner
  sentence and supporting source line. Concise accurate paraphrases score4.
- **CF.c:** distinguish the user's intent judgement, example acceptance, mutant
  rejection and a universal formal proof. An example-relative measure does not
  establish a complete characterisation of all incorrect outputs.
- **CF.d:** distinguish a position paper's proposal from surveyed prior results.
  Absence of a common budget, new experiment, variance estimate or immutable
  artifact pin may be stated plainly; do not invent any of them.
- **CF.e:** the card grade is the minimum of the eight field grades. The Trust
  connection to the learner's API review must identify a concrete formal claim
  and its remaining intent/library judgement; prose style is not a dimension.

## Gate and API review

- Both completed exercise units gate with zero counted holes and clean audits.
  All four predictions are recorded/enabled; the strict firsttry report passes.
- The source freeze passes, including the export boundary. Only completed
  open-body API definitions gain provides entries; private representation and
  hidden helper bodies remain hidden.
- The API REVIEW identifies totality on valid inputs, client strength and the
  information available through contracts. Require evidence for a claimed
  omission; a stricter requires does not solve a totality obligation.
- The agent delivery passes its zero-hole gate, audit and unchanged-snapshot
  check. Its adversarial review covers empty/equal inputs and character
  boundaries, and cites the actual diff and transcript. No live transcript is
  inferred from scripted author controls.

## Code-review focus — it-reads

Preserve the public API. Explain recursive/loop progress with the actual
measure. Keep model values and runtime values distinct. Intermediate names
should identify the interval or partial result. Do not demand advanced proof
style, or call an unrun deletion experiment evidence of dead code. Supplied
Unicode conversion proves the existing vstd precondition and adds no trust
axiom; a delivery must retain that proof and its bounds.
