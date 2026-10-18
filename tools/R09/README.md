# R09 compiled observations

Complete the hand tasks, then run the supplied tools through a capped native
lane, following the resource policy in CLAUDE.md:

```
python3 tools/R09/check_frontend.py
python3 tools/R09/check_port.py
```

The defaults read your hand files and escaped-atom agent files, respectively.
They never read reference trees. `--dafny-file` and `--verus-file` identify an
explicit alternative delivery; the retained JSON records each actual source,
case-file and driver digest. `--out` selects retained scratch. Nonzero exits
include incomplete source, native/compile failures and observed mismatches;
read the stored stage and holes before interpreting the result.

The frontend's 297 exposed cases compare full nested AST spans, raw canonical
class vectors (A2's u32 code-point ranges, read through its accessor; adjacent
ranges merge), exact scalar failure positions and actual lowered tree-node
counts. Existing parser AST records came from the checked original compiled
Dafny parser; cost expectations use an independent arithmetic interpretation
of those records, with additional hand-built ASTs for new cap cases. There is
no external class normalizer. Cases include exact/zero/full-u32 caps, huge
positive repetitions and unused huge operands under zero copies.

The port's 12 exposed cases compare escaped scalar values, exact failure
positions, final cursors and preserved input. Expected observations were fixed
before checking the port. Both tools compile the actual supplied files through
the pinned wrappers and retain generated test drivers and full native records.

These are finite, public, previously exposed observations. Passing them is not
a full grammar theorem, a hidden-test result, an independent unseen benchmark
or a live actor outcome. Keep native proofs, audits, original statement/model
snapshots and mirror-relative implications as separate evidence. The contract's
allowed-files rule does not permit changing the case files or checking tools.
