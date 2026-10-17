# R01 rubric — Hello, two verifiers

Apply CORE.md. Predictions first; reference last. Grade only this learner's lines.
The review bar is `it-reads`. Live Claude calibration is deferred under D45, not passed.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R01_solutions.tex  sha256 6d245ce85fdae9a220aae4a1d29356e78966be5265a19b63e6d9392dbc147493
paper/R01_problems.tex  sha256 fd97bd6b26ec5a21f0ae1b6526733d28f11fa56e54b903373b6533385d025a88
Solutions/dafny/R/R01_Hello/core/R01_Hello.dfy  sha256 0990375acd8f9bb2fcf8b3c0377201541495d719707d354372d301c5f935defc
Solutions/verus/r/r01_hello/src/lib.rs  sha256 cb638ddb83a572f8e069958da1b91683e38e11865c16cd684d14a04fe23fec13
Solutions/dafny/R/R01_Hello/agent/R01_AgentRepair.dfy  sha256 b5445c8b5e54952d56e477d2defa17f8b14a2a75bd03e8934381bd6b0f9095b0
Solutions/verus/r/r01_hello/src/agent.rs  sha256 76c8cd6e176038d876fc6e86b78c00f80e1245f971eca7aec9f804e0e4b780d0

## Verifier anchors

- **Probe A, source pin:** `sed -n '5480,5506p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print B1's hash. A mismatch refuses the card, not a learner finding.
- **Probe B, dead step:** copy the declaration and its given definitions to `instructor/scratch/r01_probe.dfy` or `.rs`, delete the disputed learner step, and run `scripts/vcheck --module R01 instructor/scratch/r01_probe.<ext>`. Quote the actual result. Proof reading aids are notes at this bar; an unnecessary exec step is a finding only with this evidence.
- **Probe C, admitted inputs:** give a concrete caller of the learner's declaration on an input its written intent covers. Run it through `scripts/vcheck --module R01`; an actual refused precondition or unproved stated result is evidence. Never invent a failing result.
- **Probe F, freeze:** `scripts/specfreeze --check R01` must pass. H3's added precondition is an open part, while every supplied clause and caller stays fixed.

## B1 — Paper card 12.11 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a:** all eight fields answer the problem's questions; an empty field scores 1.
- **CF.b:** a field agrees with the pinned source by substance, not wording. A contradiction scores at most 2 with the field's sentence and the exact pinned line beside it.
- **CF.c:** distinguish a proposal, an aspiration, a criterion and an experimental measurement. An aspiration presented as an observed rate is a contradiction, exhibited against the pinned range.
- **CF.d:** a field may correctly state that the source supplies no experiment, interval, per-task budget or released implementation. Do not invent a finding because the paper lacks an empirical field.
- **CF.e:** an invented figure, trial count, release or guarantee scores at most 2 only with the relevant quoted absence. The card grade is the minimum of the eight field grades. Correct concise paraphrases score 4.

## Gate

- Both exercise units: `scripts/vcheck --gate dafny/R/R01_Hello/core` and `scripts/vcheck --gate verus/r/r01_hello` exit 0 with zero holes; both `scripts/vaudit` calls report zero findings.
- `scripts/firsttry.sh R01 --report --strict` passes: both code test-outs recorded, six predictions recorded and enabled, every shipped check uncommented, no check deleted.
- Probe F passes. Both repaired agent files pass their gate and compare to their expected audit baseline. Prediction specimens and card/scenario demos are not reviewed as learner code.

## Code-review focus — band: it-reads

- Names introduced by the learner describe their values or proof facts. Shipped names are not findings.
- Supplied contracts stay fixed. H3 adds the requested precondition and preserves the supplied callers; a hidden extra restriction needs Probe C's concrete evidence before becoming a finding.
- Exec code computes; proof code establishes facts. Do not demand an advanced proof style or a later module's technique.
- No abandoned attempts, unused learner locals or uncalled invented helpers. A proof assert explaining the available fact is a reading aid, not a finding.
- Wrong first predictions are historical records, not code defects. TRIAGE, CALIBRATION, THREE DOORS and R-v0 are the learner's prose; no gate proves them.

## Audit debrief — after /contract R01

Ask whether the contractor re-verified after every edit, changed only one body line per bug, preserved signatures and specifications, kept the allowlist exact, and left no assumption or hole. Compare the audit, diff and actual transcript; a green run alone proves none of those process claims. Then ask which of the learner's R-v0 rules a verifier, audit or human reader can check. Do not write the rules for them. The three guard-door observations must be actual refusals with rule/layer attribution; absent observations stay unvalidated.
