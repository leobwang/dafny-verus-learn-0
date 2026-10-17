# R10 local checks

Run from the repository root after committing the five predictions. Defaults
read only the learner's actual files. An explicit `--dafny-file PATH` or
`--verus-file PATH` selects another source; no tool locates reference answers.
Use a native lane capped at16GiB, no swap, with GATE_WORKERS=1 and at most
three Verus jobs. Keep all concurrent solver lanes within48GiB.

```sh
python3 tools/R10/check_normalizer.py
python3 tools/R10/check_statements.py
python3 tools/R10/check_constructors.py
```

The normalizer checker first runs complete zero-hole native gates, then
compiles120fixed cases in each language and checks exact trees, normality,
node counts and11matching words per case. It also checks the concrete Rust
packet layout. Generated Dafny Python is copied before normal wrapper cleanup
so you can inspect the packet fields and actual builder bodies. The observer
itself computes node counts; distinguish that traversal from erased evidence
in the builders. This finite corpus is supplied regression evidence, not a
general language-preservation theorem or an unseen evaluation set.

The statement checker extracts proposed requires/ensures using the course's
native parsers. It generates consumers over arbitrary normal inputs and a
fresh arbitrary normal result. The original domain must establish the proposed
preconditions; together the preconditions and postconditions must establish
the printed raw-constructor language relation. No constructor body is assumed.
This is a guided specification-strength exercise: the desired consumer relation
is visible. A native failure says the consumer was not proved. A contradictory
postcondition can imply anything, so sufficiency is only one requirement.

The constructor checker runs complete zero-hole gates and compiles27fixed
normal-input cases per language, each checked on11words. It observes actual
constructor results. Combine it with your own positive and negative witnesses,
original human statement snapshots, audit and native gates. Finite agreement
does not establish universal strength or prove that a contractor participated.

Before any actor body edits, copy each human-completed agent source to a
snapshot file under your own `research/R10/` directory. Keep that copy fixed.
Then compare a delivery with the original copy:

```sh
scripts/specfreeze --against research/R10/human-original.dfy dafny/R/R10_TypeInvariants/agent/R10_AgentFlagship.dfy
scripts/specfreeze --against research/R10/human-original.rs verus/r/r10_type_invariants/src/agent.rs
```

Each tool retains its drivers, source/tool hashes, native JSON and raw-log paths
under private temporary scratch, printed at completion. `--out DIRECTORY`
selects a retained directory. Inspect the native stage before interpreting any
failure. An empty-body error, runtime mismatch, failed proof and resource kill
are distinct outcomes. None supplies the deferred live actor or grading result.
