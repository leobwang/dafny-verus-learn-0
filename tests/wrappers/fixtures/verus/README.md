# Verus wrapper fixtures (tests/wrappers/test_verus_*.py)

Tiny invented programs for `scripts/dvl/verus.py` and `scripts/dvl/verus_spec.py`.
None of it is course content, an exercise or an answer: no file here copies or
paraphrases a reference proof. Item markers (`// item: …`) only exercise the
item parser's block lookup; the ids name no registry item.

- `clean.rs`, `holes.rs`, `kinds.rs`, `rlimit.rs`, `stages_*.rs`: verify, the
  hole counter, the stage and verdict map.
- `chain/`: three crates (`tla` ← `tlb` ← `tmod`) for the direct layer chain
  (`--import`/`--extern`/`--export`), a `mod` file, a file no `mod` reaches
  (`exit.rs`), a `#[cfg(test)]` module and a broadcast group.
- `trusted/`: dependency holes and the trust allowlist: `tdep` (two
  `external_body` fns and an `assume`) and `tuse`, which calls each of them
  (`exit.rs`: a file no `mod` reaches, with its own hole beside a
  dependency's). Under `--no-cheating` a caller is shown a dependency's
  `external_body` fn once, never its `assume`.
- `eb.rs`, `eb_exec.rs`: the empty-body gate; `eb_ghost.rs`: an exec item whose ghost sequence is updated in `proof` blocks right after an if/else and after the loop (QPLAN §6 Q9: the E0 variants strip them with the ghost let).
- `eb_regions.rs`: the region mode RGN (QPLAN §6 Q18): an exec item whose learner region (one invariant clause) the given code needs, an exec item whose region holds its loop's whole `invariant` list (the variant drops the keyword, which would otherwise dangle before `decreases`), and a proof item whose region (an assertion) automation supplies; the markers stand where a reference twin's would.
- `eb_trait.rs`: trait-impl methods for the gate's qualified symbols (QPLAN §30
  Q65(a)): two impls of one trait and an inherent method of one of the types share a
  method name; `eb_named.rs`: a proof fn with a named return (the `{ arbitrary() }`
  body); `eb_tracked.rs`: an exec fn whose code consumes a permission bound by
  `let tracked` (the E0 variants keep those lines, QPLAN §30 Q65(b));
  `eb_trait_item.rs`: a trait-impl hole item shipped as the course ships exec holes,
  for firsttry's per-method gate.
- `lab/`: an invented lab task form (`task.rs`, a labelled-assume lemma) and a
  delivery that adds verifier attributes (`levered.rs`), for the lever check (QPLAN
  §30 Q63); `kept.rs`, a delivery that proves it with no attribute (the lab gate passes it,
  its assumption audit included), and `external_task.rs`, a task form that ships a
  `#[verifier::external_body]` proof fn its lemma calls, delivered unchanged (the
  user's decision D24).
- `tests.rs`: `test()` (libtest through `verus --compile --test`).
- `cli/`: `run_bin()` and `vcheck --bin` (the user's decision D16): the crate `tcli`, a
  verified library over `chain/tla` and one `[[bin]]` target `tally` (a command line
  outside `verus!`: `tally sum <a> <b>`, `tally twice <a>`, else a usage line and exit 2).
- `lint/`: one line per rule, each marked `// expect: <kind> …`.
- `freeze/`: statement-freeze pairs.
- `specimens/Q04/`: a `*.rs.specimen`.
- `captured/`: raw outputs captured from the pinned Verus by
  `python3 tests/wrappers/test_verus_tool.py --recapture` (each `.cmd` file
  records the command, paths relative to this directory).
