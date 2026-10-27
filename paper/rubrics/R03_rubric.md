# R03 rubric — Modules and APIs

Apply CORE.md; predictions first, reference last. Grade the learner's words
and code, not similarity to this reference. Code-review bar: `it-reads`.
Live Claude calibration remains deferred under D45; compiled fixtures do not
stand in for a calibration session.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R03_solutions.tex  sha256 9f6a929d13259b739485ac5e86c1069f15efeece8dc7378c1c61ebd88960da10
paper/R03_problems.tex  sha256 d5837cff75180715a141adb5ccdd4f83523992bbd1c7828f709224321ae5eda6
Solutions/dafny/R/R03_Modules/core/R03_Modules.dfy  sha256 25a4b5da2d435d38e244c5eb46ad877fdfeceeba3c00e9fb9fc80d5e98010ba5
Solutions/verus/r/r03_modules/src/lib.rs  sha256 690b1ba0743ef449048a4a1d8821767113088582e6e0a5c75fb76bc52366aac3
Solutions/dafny/R/R03_Modules/agent/R03_AgentApi.dfy  sha256 2e5f146b35e5047203c2a6c83ff3a5cb1ec376911e90fded627c1aa2b82eb168
Solutions/verus/r/r03_modules/src/agent.rs  sha256 6035198ff4d308cdec6b6952d0799405ef0890f41145c22bd493ee8420f151db

## Verifier anchors

- **Probe A, source:** hash exactly the printed cheatsheet range. A mismatch
  needs an author re-pin. Do not penalize a learner for source drift.
- **Probe B, API:** reproduce a disputed client assertion in scratch with the
  same export/view boundary and only the claimed contracts. Run the R03 wrapper
  context and cite the actual obligation. An exec function's body is not its
  postcondition; a visibility change is not a strengthened contract.
- **Probe C, boundary:** encode a disputed code-boundary case (the codes 0 and
  `u32::MAX`, adjacent ranges, a range across the surrogate block) with the
  supplied model, and run it before claiming a verifier outcome. Ranges are
  code points; nothing converts a number to a char.
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

- Both completed exercise units gate with zero counted holes and clean audits,
  with no `GATED` attribute left in the Verus file (the strict report counts
  them). All four predictions are recorded/enabled; the strict report passes.
- The source freeze passes, including the export boundary. Only completed
  open-body API definitions gain provides entries, and in Verus only
  `class_range` and `class_union` gain `pub` (open visibility); private
  representation and hidden helper bodies remain hidden.
- H6v and H7v are `pub closed spec fn` over the private field (an `open` one is
  refused); a definition that lets the four GATED functions verify but changes
  the meaning (for instance a weaker `valid`) is a finding even when green.
- H2 builds the one range itself (ClassInsert is opaque; `class_insert` says
  nothing about the number of ranges); H4 is the union of a sequence, its
  recursion or loop invariant explained with the witness it needs.
- The API REVIEW identifies totality on valid inputs, client strength and the
  information available through contracts. Require evidence for a claimed
  omission; a stricter requires does not solve a totality obligation.
- The agent delivery passes its zero-hole gate, audit and unchanged-snapshot
  check. Its adversarial review covers empty/equal inputs and the code
  boundaries (0, `u32::MAX`, adjacency, the surrogate block), with the `a - 1`
  and `b + 1` guards, and cites the actual diff and transcript. No live transcript is
  inferred from scripted author controls.

## Code-review focus — it-reads

Preserve the public API. Explain recursive/loop progress with the actual
measure. Keep model values and runtime values distinct. Intermediate names
should identify the interval or partial result. Do not demand advanced proof
style, or call an unrun deletion experiment evidence of dead code. Code
arithmetic in a delivery is guarded (`lo < a` before `a - 1`, `b < hi` before
`b + 1`); an unguarded step is a finding even if no test hits it.
