# Dafny wrapper fixtures (tests/wrappers)

Tiny invented programs for `tests/wrappers/test_dafny_*.py`. None of it is course
content, an exercise or an answer, and nothing here is copied from `Solutions/`.
Each file exercises one wrapper behaviour (hole kinds, silent kinds, verdicts,
filters, projects, refinement freeze, the empty-body gate, the lint). Expected
outputs in the tests were captured from the pinned Dafny 4.11.0 on 2026-10-04.

`lint/*.dfy` mark every line that must produce a lint finding with a trailing
`// expect: <kind> [<kind>…]` comment; the suite reads those marks.
`captured/` holds raw stdout of real runs, for the tool-free parser tests.
`captured/verify_filter_*.jsonl` are the stdout of `sym.dfy` runs with
`--filter-position sym.dfy:5` (W-D08, assertions), `--filter-position sym.dfy:99`
and `--filter-symbol Nope` (filters that match nothing, exit 0).
`captured/test_print_*.txt` are the stdout of `dafny test` on `tests_print.dfy`
(2026-10-05): `_pass` and `_fail` run one printing test each through
`--methods-to-test` (`PrintsThenPasses`, exit 0; `PrintsThenFails`, exit 3), `_all`
runs the file (exit 3). A test's own output sits between `<Name>: ` and its
status, glued to the status when it ends without a newline.

`eb_regions.dfy` exercises the empty-body gate on a `function … by method` item and its
region mode (QPLAN §6 Q18): a by-method loop's invariants, a header clause, and an
assertion that automation supplies, each between `@hole-begin`/`@hole-end` markers as in
a reference twin (captured 2026-10-05).

`given/*.dfy` are invented frozen abstract specs for the given-role lint (Δ3,
Δ44): `refined.dfy` (a concrete module refines every member; verifies under the
gate), `chain.dfy` (through an abstract middle module), `partial.dfy` (one
statement left without a body), `unrefined.dfy` (nothing concrete refines it,
plus a trait), and `spec_only.dfy` with its refiner in `impl_only.dfy` (the
lint's program context).

`lab/` holds an invented lab task form and two deliveries for the lab gate's lever
check (QPLAN §30 Q63; `dvl.levers`, `specfreeze --lab`, `vcheck --gate --lab-task`):
`task.dfy` ships a bodyless lemma under `{:induction false}` in a module with nonlinear
arithmetic off; `kept.dfy` proves it by hand and keeps both levers; `levered.dfy`
drops the induction switch and adds `{:vcs_split_on_every_assert}`. Two more task forms for the
lab gate's assumption audit (vaudit's rules, the user's decision D24), each delivered
unchanged: `axiom_task.dfy` ships `assume {:axiom} false;` (the gate counts no hole),
`axiom_lemma_task.dfy` a bodyless `{:axiom}` lemma its lemma calls (a lever the lever
check allows because the task form ships it).
