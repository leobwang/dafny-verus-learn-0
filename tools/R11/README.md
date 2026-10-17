# R11 rule fidelity

Commit all five predictions before running the checks. The default rule-binding
tool reads the learner's actual agent files, extracts their pure definitions
with the course's native parsers, and checks those definitions against canonical
A4 validity over arbitrary original subjects. It assumes no transport theorem
or proof body. Use a native lane capped at16GiB with no swap, GATE_WORKERS=1
and at most3Verus jobs; aggregate concurrent solver lanes stay within48GiB.

```sh
python3 tools/R11/check_rule_binding.py
```

The character-replacement theorem is forward only. Replacement can merge two
letters, so an inverse preservation claim needs additional hypotheses. Its
formal transport property can hold for a wrong rule system too. Rule equality,
correct transport, original model snapshots and compiled behavior are separate
requirements. A native failure here means rule equality was not proved; inspect
the native stage before interpreting the result.

`--dafny-file PATH` and `--verus-file PATH` select explicit candidate files;
`--lang d|v|both` narrows the language. No reference is located automatically.
`--out DIRECTORY` selects retained scratch; the default uses private temporary
scratch. Reports include exact source/tool hashes and full native results.
The generated consumers keep the actual pure definitions in their root files.
Their fixed canonical parameter and model paths prevent a candidate's local
rule name from changing the comparison's target.

Before actor edits, copy the two original agent files into your own
`research/R11/` snapshot directory. Keep those copies fixed. After delivery,
compare each original against its corresponding learner file with
`scripts/specfreeze --against ORIGINAL DELIVERY`, then run complete zero-hole
gates and audits. The snapshot protects replacement models and rule bindings;
this consumer checks the specified rule relation independently. A scripted
author control is not a live contractor, learner or grading result.

## Compiled observations

```sh
python3 tools/R11/check_runtime.py
```

This tool first gates the actual specified core implementation with zero holes,
then compiles it. It checks120syntax patterns against11words using an independent
finite language interpreter, inspects returned certificates with the actual
checker, and checks every prefix flag plus final acceptance. The fixed29explicit
certificate cases cover constructors, malformed trees, invalid tails, zero and
oversized splits. Verus uses shifted slices and also checks invalid slice bounds
and Vec-arena append/link frames. The pattern input corpus contains syntax only;
it does not contain a learner solution or expected proof body.

`--lang d|v|both`, explicit source paths and `--out DIRECTORY` select scope and
retained evidence. The defaults never locate reference material. A typed learner
hole causes the gate to reject the run before executable observations. Reports
retain source/tool/corpus hashes, independent finite expectations, generated
actual-source test roots and full native results. Dafny implementation bodies
are embedded in the root so they are actually verified. The ghost and tracked
evidence disappears from execution; ordinary runtime derivation trees remain.
These are finite checks, not a decision procedure or a universal proof of rule
soundness, complete search, metatheory or memory safety beyond the stated model.
