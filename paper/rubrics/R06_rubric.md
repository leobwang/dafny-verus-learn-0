# R06 rubric — Induction and loops

Use CORE.md and the **proof-shape** code-review bar. Live model calibration
remains D45 debt, not a consequence of fixture compilation.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R06_solutions.tex  sha256 00f97ab79978fb81dc6798588e652685249049b1ccd79e8d78c4573770bb936b
paper/R06_problems.tex  sha256 bfd8cb435bb5a4d92796f45e56828c650732c28de5cf0264c0c3a9d7c781cbfd
Solutions/dafny/R/R06_Induction/core/R06_Induction.dfy  sha256 c724c7dbc4783067d17ed08f5d2eb52149eb2d2caf55b5bcf7b43e4c072f319a
Solutions/verus/r/r06_induction/src/lib.rs  sha256 c418832187848e630674f1a8b2bd5b74f72f7d37207af719a127b3632c1ca165
Solutions/dafny/R/R06_Induction/exit/R06_Checkpoint.dfy  sha256 5e8e9f92920ebe0b1b3daf5b96497e6c4b2a23d789c5f36d90b7881fccec4aa0
Solutions/verus/r/r06_induction/src/exit.rs  sha256 8f8d4c9a01a5e2f442bc99b93f009a0b65e0ebfda6f0e9b824743745b9d15ee7
Solutions/dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy  sha256 930669c81be97c34b51a3e269843957be36dc9e1ebc60609763c876e3a60fed9
Solutions/verus/r/r06_induction/src/agent.rs  sha256 266a8be5306f5ba20c8a8e538226f79a94ce05ebdbc02f978845215013c69b49

## Verifier anchors

- **Probe A:** reproduce B1's exact local-source hash; drift requires author re-pin.
- **Probe B:** disputed Cat splits use the actual bounds and shifted slices in scratch, under the module's declared given layer. No imported learner proof.
- **Probe C:** weaken a disputed loop invariant in scratch, retaining code and command, and identify the lost postcondition direction.
- **Probe D:** delete a proposed helper or proof step in an independent scratch copy, then rerun the same scope/settings; preserve the observation and its limits.
- **Probe F:** frozen statements protect the exact target; H4 opens only requires, whose intended weakest repair needs a separate fidelity judgement.

## B1 — AutoSpec (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** eight fields answered; accurate paraphrase 4, an empty field 1. The grade is the minimum field grade.
- **CF.b:** separate retained annotations' provability from adequacy for the fixed target; the target is supplied/trusted.
- **CF.c:** retain199/251 and the exclusion of X509, task denominators, five-iteration budget and the scope of the manual-work comparison.
- **CF.d:** do not invent cost, confidence intervals, artifact pins or library coverage. A material contradiction scores at most 2 with source and learner lines.

## B2 — Nullable Cat and shifted splits (proof; dimension: induction-rigour)

### induction-rigour

- **I.a:** prove both directions, with a legal semantic split and the zero/positive distinction.
- **I.b:** justify the zero branch using the appropriate given fact, not an invented nonnullability assumption.
- **I.c:** state all index bounds, shifted slices and the induction hypothesis's exact arguments; a structural measure must justify every recursive call.
- **I.d:** cover both conditional/Alt operands in the converse. Omitting nullable left operands scores at most 2, with a nonvacuous counterexample or Probe B.

## B3 — The invariant as IH (proof; dimension: invariant-rigour)

### invariant-rigour

- **L.a:** relate the current suffix semantics to the original problem and keep bounds.
- **L.b:** prove entry, preservation and exit separately; give the decreasing quantity and legal index arithmetic.
- **L.c:** use the full relation needed for the exact Boolean result and identify the fact connecting the final test to semantics.
- **L.d:** a one-way invariant cannot establish both implications merely because actual execution was intended to be correct. A false sufficiency claim scores at most 2 with the missing direction and Probe C.

## H4 — statement fidelity beyond the native gate

The weakest repair permits every input on which the unchanged equivalence
holds. Reject an arbitrary sufficient restriction, including an impossible
precondition, exclusion of all empty inputs or a requirement that the operand
always be nullable. A successful gate under a stronger requires is narrower
evidence and does not satisfy this exercise. Ask for necessity outside the
proposed domain as well as sufficiency inside it; compare disputed predicates
with explicit counterexamples/native probes. Open requires does not open the
postcondition, parameters or return shape. Preserve the exact source claim.

## Code, exit and decomposer review

All hand, checkpoint and agent deliveries gate with zero holes, audit clean
and preserve their frozen/snapshot contracts. Verus X2's external-body marker
is one shipping placeholder, never finished trust: remove it and prove the
retained loop. Keep its given bounded counting support and immutable input
cap. H2 retains its loop, measure and supplied correctness call.

Check proof shape: induction parameters cover recursive calls, helpers expose
usable contracts, calc steps have reasons and invariants state a real IH.
The decomposer transcript introduces each helper as a hole and reaches a
green leaf stage before proving it. Draw actual dependency edges and deletion
observations, not an invented unique-minimality claim. Reference proofs may
have different legitimate decompositions. Check the final full-file scope,
assumptions and snapshot; a filtered local success is not final acceptance.

The exit is closed book, four unseen items, at least 3/4 with at least 1 in
each language; preserve the first exit record. Later successful observations
do not retroactively become first tries. No earlier learner solution is a
dependency. The fifth bench card is explicitly course-derived: label its
provenance rather than claim it is an independent unseen benchmark task.

## Calibration fixtures

Gold: 4 in all three dimensions. Flawed: B1 remains intact; B2 falsely omits
the zero/nullable case and B3 claims one direction suffices for equivalence,
so each scores at most 2 at its named clause with quoted learner lines. True
sentences elsewhere do not erase these contradictions. No live grading pass
is claimed from local compilation or these expected outcomes.
