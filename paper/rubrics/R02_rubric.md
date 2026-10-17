# R02 rubric — Datatypes and recursion

Apply CORE.md. Predictions first, reference last; grade the learner's lines.
The code-review bar is `it-reads`. Live Claude calibration is deferred under
D45, never a passing result inferred from a compiled fixture.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R02_solutions.tex  sha256 e91c45c5f62d36f35cc94d5a6b9bec70512f9f6d43dbd72208652fc9e7af4fe8
paper/R02_problems.tex  sha256 8ca94d096236ce9547818cf05c14000e2d7922f66d581e88ea0812edd5bc6f11
Solutions/dafny/R/R02_Datatypes/core/R02_Datatypes.dfy  sha256 8e9dbac522c32d673483d32f1c7c0c413f0518233a35805949e1aa3900504329
Solutions/verus/r/r02_datatypes/src/lib.rs  sha256 8697e5bb78e17a2adc8417cd8f8484a3988adef3909f2697fbd559c93bf21bbb
Solutions/dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy  sha256 a80bf308936b06f8b520fa9e8b555df55d59eae3fcde231d3c143a3dfd64c10e
Solutions/verus/r/r02_datatypes/src/agent.rs  sha256 b5bac2f5035138f8c8a9fbea6900ff50382a44dcb558cbb10ab69261e3b2fcd9

## Verifier anchors

- **Probe A, source:** hash the exact cheatsheet range printed in B1. A source
  mismatch requires an author re-pin, not a learner finding.
- **Probe B, measure:** in scratch, reproduce the disputed recursive call with
  its claimed measure and the public A1 definitions. Run
  `scripts/vcheck --module R02 instructor/scratch/r02_measure.dfy` or `.rs`.
  Cite the actual strict-decrease obligation and the call's arguments. Do not
  turn a remembered prediction verdict into an unrun verifier claim.
- **Probe C, split:** encode the claimed regex/string/split in a scratch probe
  under the R02 wrapper context. Check both complete substrings. A single
  matching character inside a slice is insufficient for whole-string semantics.
- **Probe D, deletion:** remove only a disputed learner proof step in scratch
  and run it through the R02 wrapper context. An unused local or unnecessary
  exec step needs concrete evidence; proof reading aids are notes at this bar.
- **Probe F:** `scripts/specfreeze --check R02`; every supplied definition,
  statement and caller remains fixed.

## B1 — Paper card 05.6 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields answer the printed questions. An empty field scores 1.
- **CF.b:** judge substance against the pinned range, not wording. A material
  contradiction scores at most 2 with the learner sentence and exact source line.
- **CF.c:** separate the reference oracle, the generated specification and the
  implementation; distinguish compilation, specification proof, implementation
  proof and complete success. Conflating them requires the same concrete evidence.
- **CF.d:** a reported time allowance does not establish a shared token/call
  budget. An absent interval, immutable release pin or licence may be stated as
  absent; do not invent a measurement to fill a field.
- **CF.e:** the card grade is the minimum of the eight field grades. A concise,
  accurate paraphrase scores 4; a different conclusion needs source evidence.

## B2 — Termination (proof; dimension: termination)

### termination

- **T.a:** name the actual lexicographic measure and compare components in order.
- **T.b:** cover both recursive calls in the Star branch, not merely the calls
  on strict constructor children elsewhere.
- **T.c:** derive the slice-length comparison from the stated split bounds;
  identify exactly what is missing in each mutation. An unsupported slogan
  such as “recursion always gets smaller” scores at most 2 with its missing case.
- **T.d:** a concrete incorrect call comparison is a finding with Probe B;
  never report that the learner's code failed without running it.

## B3 — Concrete splits (proof; dimension: split-rigour)

### split-rigour

- **S.a:** list every legal successful outer index for each accepted string,
  its prefix, suffix and applicable alternative. A proposed index must be legal.
- **S.b:** cover every legal index when rejecting the third string. One failed
  candidate does not prove that no candidate works.
- **S.c:** use whole-string matching on both slices. A false slice equality or
  an unexamined index scores at most 2 with the concrete string/index as witness.
- **S.d:** a disputed constructor claim is checked by Probe C, not an invented run.

## Gate

- Both exercise units gate with zero tool-counted holes and clean audits.
- `scripts/firsttry.sh R02 --report --strict` passes: five predictions and both
  code test-outs recorded, prediction switches enabled, every supplied check kept.
- Probe F passes. The agent delivery gates and audits; the transcript respects
  the symbol-only editing channel and exactly one final full gate.
- The learner's adversarial checks address the prose; property-test results
  and latency evidence are reported. Finite tests are not universal theorems.

## Code-review focus — it-reads

- Recursive arguments and intermediate names make each smaller input legible.
- Supplied contracts stay fixed; no hole is closed with an assumption or a
  verification attribute. Specification values and compiled values have distinct roles.
- No abandoned attempts or unused learner locals. Apply Probe D before a
  substantive dead-step finding; do not demand advanced proof style.
- The agent's weak formal contracts and finite tests do not replace its prose.

## Audit debrief

Identify assumptions, abstract definitions and external bodies in the shipped
draft and show that the completed work has none left. Separate formal proof,
native sample tests, transcript compliance, latency observations and agreement
with the prose. State which claim each item of evidence supports.
