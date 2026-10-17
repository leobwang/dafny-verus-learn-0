# Q07 code notes (DV3b, the Q07 module lane)

> **Author-only.** Prediction answers, the evidence each was captured from, the hole
> gate results, the agent files' soft spots and every deviation from the plan. Never
> quote, paraphrase or link any of it from a learner-visible file. The item plan is
> `QPLAN.md` §14–§15 (learner-visible) and `Solutions/plans/Q07-Q09-author-notes.md` §0–§2,
> §5–§8 with Appendices A.3–A.6, A.12 and A.15 (the plan lane's author notes; exit
> statements in §2.8); this file records what the Q07 module lane built and re-captured
> on the real files, 2026-10-06. Where this file and the author notes disagree, this file
> holds (the author notes' Appendix A is the plan lane's scratch).

Every run below went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.py`, `scripts/specfreeze`,
`scripts/reference_lint.py`), at the course pins (Dafny 4.11.0 with its bundled Z3 4.12.1,
`--resource-limit 5000000`; Verus 0.2026.09.27, `--rlimit 2`), one solver job at a time
under the `dvl` caps (Dafny 8 GB, Verus 16 GB; the pools' flock slots serialize jobs), each
started with at least 31 GB available (`free -g` showed 83–93 GB), with
`DVL_SCRATCH=/tmp/dvl0-dv3b-q07/scratch`. Probes, the simulation root and the drivers are
lane scratch under `/tmp/dvl0-dv3b-q07/` (`probe/`, `sim/`, `leak/`) and are not
archived; the decisive ones are quoted or described below.

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy` (unit `dafny/Q/Q07_InternalsI/std`; `{:disableNonlinearArithmetic}`) | verified, 130 tasks, 4 holes (T1d, H1d, H2d, H3d, each `bodyless-method` with its label) | `Solutions/dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy` (134 tasks; count pin floor 9) |
| `dafny/checks/Q07_checks.dfy` (no item, no slot) | verified (gate: 128 tasks), 0 holes; `vcheck --test`: 2 passed | `Solutions/dafny/checks/Q07_checks.dfy` (the same file, reference header) |
| `verus/q/q07_internals_i/src/lib.rs` (crate root; `mod port;`) | verified, 4 holes (T1v, H4v, H5v `assume`; H6v `external_body`) | `Solutions/verus/q/q07_internals_i/src/lib.rs` (crate twin: 20 verified with `port.rs`; floor 10) |
| `verus/q/q07_internals_i/src/port.rs` (module `port`) | verified, 3 holes (H7v `external_body`, no `ensures`; H8v `uninterp`; H9v `assume`); H7's use-site check and the differential suite commented | `Solutions/verus/q/q07_internals_i/src/port.rs` (use-site check and suite live; the mutants as reference-only tests) |
| `dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy` (`{:disableNonlinearArithmetic}`) | verified, 124 tasks, 2 holes (X1d, X2d); the `EXPLAIN-BACK` block | `Solutions/dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy` (126 tasks) |
| `verus/q/q07_internals_i/src/exit.rs` | verified, 2 holes (X1v `external_body`, X2v `assume`) | `Solutions/verus/q/q07_internals_i/src/exit.rs` (3 verified) |
| `dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` (A1d, A2d) | verified, 126 tasks, 0 holes; `vaudit` 0 findings | `Solutions/…/agent/Q07_AgentRefactor.dfy` (the delivered refactor, 127 tasks) |
| `verus/q/q07_internals_i/src/agent.rs` (A1v) | verified, 0 holes; `vaudit` 0 findings | `Solutions/…/src/agent.rs` (the delivered refactor, 5 verified) |
| `specimens/Q07/card-c1d.dfy.specimen`, `card-c1v.rs.specimen`, `card-c2d.dfy.specimen`, `card-c2v.rs.specimen`, `card-c3v.rs.specimen` (WRITE failure demos, in-file `// EXPECT`) | red by design | none (demos are given) |
| `specimens/Q07/card-c4d.dfy.specimen`, `card-c5d.dfy.specimen`, `card-c6v.rs.specimen`, `card-c7dv-d.dfy.specimen`, `card-c7dv-v.rs.specimen` (RECOGNISE and divergence demos) | see §4 | none; sealed sidecars under `expected/specimens/Q07/` |
| `slots/Q07.slots` (7 lines, unfilled) | — | `Solutions/slots/Q07.slots` |
| — | — | `expected/Q07.pins` (7 salted hashes), `expected/Q07.counts` (schema 2: 2 units, 8 files), `expected/Q07.freeze` (65 statements in 18 files; `open_specs = ["from_u128"]` with its `spec_clauses`, `open_bodies = ["from_nat_mirror"]` in `port.rs`), 5 sealed sidecars. No `.audit` pin (QPLAN §15.1) |

Header counts as built: 11 holes (Dafny 4; Verus 7: `lib.rs` 4, `port.rs` 3), 2 of them test-out items; 7 predictions (all verdicts); 4 exit items (2 + 2 shipped holes); agent files: no hole. `research/q07_frozen.dfy` and `.rs` are not shipped: the learner writes them (QPLAN §15.1).

## 2. Prediction answers, re-captured on the scenarios as the files state them

| item | answer | evidence (2026-10-06, `vcheck --json --module Q07 <probe>` unless stated) |
|---|---|---|
| P1dv | `D:fail ok V:fail fail` | `p1d.dfy` (module `{:disableNonlinearArithmetic}`, the two lemmas): `TwoLimbs` failed ("a postcondition could not be proved on this return path"), `TwoLimbsThen` verified. `p1v.rs` (`use qg_bignat_l4::*;`): both `postcondition not satisfied` |
| P2dv | `D:ok V:fail` | `p2d.dfy`: `Half` verified (24 tasks). `p2v.rs`: `half` failed, `postcondition not satisfied` |
| P3v | `b` | four crates `p3v_{a,b,c,d}.rs`, one each: [a] `assertion failed`; [b] verified; [c] the warning "Failed to simplify expression <<p >> 64 == p / 18446744073709551616>> before sending to Z3", then `assertion failed`; [d] `postcondition not satisfied`. (The plan lane's probe held the four in one crate.) |
| P4d | `D:timeout` | `p4d.dfy`: verdict `inconclusive`, "Verification out of resource (ProbeP4.SplitWide)" |
| P5dv | `D:ok fail V:ok fail` | **differs from the author notes** (`D:fail ok`, §7 deviation 1). `p5d.dfy` (module `{:disableNonlinearArithmetic}`, `Comm` and `Dist` with empty bodies): `Comm` verified, `Dist` failed; the same per-symbol verdicts under seeds 1–3 (`--seed`) and in all six rows of `vcheck --brittleness --solvers` (the file fails in each row, on `Dist`). Dafny's prelude axiomatizes the commutativity of its uninterpreted `Mul` (`.toolchain/dafny-4.11.0/dafny/DafnyPrelude.bpl` lines 1686–1688, `axiom (forall x, y: int :: { Mul(x, y) } Mul(x, y) == Mul(y, x));`), so commutativity survives nonlinear arithmetic off and distributivity does not. `p5v.rs` (a crate of its own, no `use` of vstd's arithmetic): `comm` verified, `dist` failed |
| P6v | `V:ok` | `p6v.rs` (`top` with `recommends`, `r1`): verified |
| P7d | `D:2 2 2` | `p7d.dfy`: six "assertion might not hold" errors, at the first two assertions of each lemma |

`pins.py --update --ref --module Q07` wrote the seven salted pins; `pins.py --ref --module Q07`: "7 check(s); 0 problem(s)".

## 3. Holes, test-out items and exits

References are in the twins; each verifies (§1). Body lines (non-blank, non-comment):

| item | reference | lines | vs the author notes |
|---|---|---|---|
| T1d | `{:fuel ToNat, 4}` on the lemma, empty body (the by-hand alternative, the two slices and `ToNat([c]) == c`, verified in a probe) | 0 | as planned |
| T1v | `reveal_with_fuel(seq_to_nat, 4);` alone | 1 | the notes add three `drop_first` assertions; the call alone verifies |
| H1d | `{:fuel AddC, 3}` on the lemma, `reveal AddC();` | 1 | the notes: fuel 4. Probed (`h1var.dfy`): reveal alone failed, `{:fuel AddC, 4}` without the reveal failed, reveal with fuel 3 verified |
| H2d | `LemmaMultiplyDivideLt(v, d, BASE);` | 1 | as planned |
| H3d | `LemmaMulInequality(r + 1, d, BASE); LemmaMulIsDistributiveAddOtherWay(BASE, r, 1); LemmaMultiplyDivideLt(r * BASE + x, d, BASE);` | 3 | the notes' two commutativity calls are not needed (P5dv's axiom) |
| H4v | `reveal_with_fuel(seq_to_nat, 3);` and the two extensionality assertions | 3 | as planned |
| H5v | `lemma_weight_succ(n); lemma_weight_zero(); lemma_weight_mono(0, n); lemma_mul_is_commutative(BASE, weight(n)); lemma_div_denominator(v, weight(n), BASE);` | 5 | as planned; `form: no-nl` |
| H6v | two `bit_vector` facts in `proof { }`, then the shift and the mask | 2 + 3 | as planned; `form: bv-exec`, `triv: { (0u64, 0u64) }`, two `cfree:` lines |
| H7v | `ensures r.wf(), r.to_nat() == x`; `lo = x as u64`, `hi = (x >> 64u128) as u64`, two `bit_vector` facts, push `lo` and `hi` when `hi != 0`, `lo` alone when `lo != 0`; `reveal_with_fuel(seq_to_nat, 3)` / `(…, 2)` with the `drop_first` facts | 17 | as planned (A.5); `form: bv-exec`, `triv: { BigNat { limbs: Vec::new() } }`, one `cfree:` answer (the split by `/` and `%`, with the same proof) |
| H8v | `if n == 0 { Seq::empty() } else { seq![(n % BASE) as u64] + from_nat_mirror(n / BASE) }` | 5 | the shipped `uninterp` form carries `decreases n` (§7 deviation 7) |
| H9v | A.5's `lemma_mirror_meets_port_spec`, renamed `lemma_mirror_meets_port` | 16 | as planned |
| X1d | `assert Pow(k + 1) == BASE * Pow(k);` two associativity and two commutativity calls, `LemmaModMultiplesBasic(x * Pow(k), BASE);` | 6 | as planned (A.6) |
| X2d | `ToNatCons(a, [b]); ToNatSingleton(b); assert ToNat([a, b]) == a + BASE * b; LemmaMulIsCommutative(BASE, b); LemmaFundamentalDivModConverse(ToNat([a, b]), BASE, b, a);` | 5 | as planned |
| X1v | one `bit_vector` fact, then `((hi as u128) << 64u128) \| (lo as u128)` | 1 + 1 | as planned; `form: bv-exec`, `triv: { 0u128 }`, two `cfree:` lines |
| X2v | `lemma_weight_add(k, n - k); lemma_weight_zero(); lemma_weight_mono(0, k); lemma_mul_is_commutative(…); lemma_div_multiples_vanish(…);` | 5 | as planned; `form: no-nl`, one `cfree:` line |

Exit `need:` lines quote each shipped declaration and its clauses, `requires` included (the author notes' §2.8 need column); X1v and X2v carry their `form:` lines, as H5v, H6v and H7v do. Exit headers allow the pinned standard library's and vstd's source to be open beside the given spine (X1, X2v ask for library lemmas by name), as Q04's do.

## 4. Cards: what each demo shows

WRITE cards: the success in the exercise file, the failure demo pinned by an in-file `// EXPECT` (checked by `pins.py --ci`).

| card | success (file) | failure demo | pinned diagnostic | `after:` |
|---|---|---|---|---|
| C1d | `TwoLimbsByHand` (the slice and `ToNat([b]) == b`), `TwoLimbsByFuel` (`{:fuel ToNat, 3}`) | the same statement, empty body, in a `{:disableNonlinearArithmetic}` module with copies of L1's `BASE` and `ToNat` | "a postcondition could not be proved on this return path" @26 | Q07.P1dv |
| C1v | `lemma_two_limbs_by_hand`, `lemma_two_limbs_by_fuel` (`reveal_with_fuel(seq_to_nat, 3)`) | empty body | `postcondition not satisfied` @15 | Q07.P1dv |
| C2d | `LimbProductBelow`: `x * y < BASE * BASE` by one `LemmaMulUpperBound` call | no call (copy of `BASE`) | "a postcondition could not be proved on this return path" @18 | Q07.P5dv |
| C2v | `lemma_limb_product_at_most`: `x * y <= (BASE - 1) * (BASE - 1)` by one `lemma_mul_upper_bound` call | no call | `postcondition not satisfied` @14 | Q07.P5dv |
| C3v | `lemma_low_byte_value`: `x & 0xFF == x % 256` by `bit_vector`, carried to `nat` | the same assertion `by (nonlinear_arith)` | `assertion failed` @15 | Q07.P3v |

RECOGNISE cards C4d, C5d, C6v and divergence card C7dv: card text in the files, demos with sealed sidecars (`pins.py --update`, 2026-10-06):

| demo | content | outcome (sealed in the sidecar) | `after:` |
|---|---|---|---|
| card-c4d | P7d's three lemmas | failed, 2 errors per lemma (the first two assertions) | Q07.P7d |
| card-c5d | `MaskIsMod` (a `bv64` mask equals a remainder, empty body) and P4d's `SplitWide`, copy of `BASE` | `MaskIsMod` verified; `SplitWide` out of resource; verdict inconclusive | Q07.P4d |
| card-c6v | `top` with `recommends`; `r1` (P6v); `r2` (`ensures top(s) > 0`, no `requires`); `spec(checked) fn below_top` calling `top(s.drop_last())` | `r1` and `below_top` verified, `r2` `postcondition not satisfied` with an `info` "recommendation not met" beside it, two `warning: recommendation not met` at `below_top` | Q07.P6v |
| card-c7dv-d | `(-7) / 2 == -4 && (-7) % 2 == 1` (verified), `HalfOfMinusSeven` (`requires x == -7 ensures r == -4`, body `x / 2`: verified), `function Ratio(x, d) { x / d }` | failed: one error, "possible division by zero" at `Ratio` | Q07.P2dv |
| card-c7dv-v | the same Euclidean facts in spec (verified), `half_of_minus_seven` (`requires x == -7 ensures r == -3`, body `x / 2` on `i64`: verified), `spec fn ratio(x, d) { x / d }` (accepted) | verified | Q07.P2dv |

The C6v card says to run its demo with `--json` (QPLAN §6 Q30: the text output does not print the `info` note).

## 5. The port

- **Sample** (the check unit's `SampleRun` and the commented differential suite): `0`, `5`, `2^64 - 1`, `2^64 + 7`, `3 * 2^64 + 2`, `2^128 - 1`, as the author notes §2.4 list; no `2^64`, no `ToNat([3, 1])`, no `Normalize([0, 5, 0, 0])`.
- **Mutants.** The learner file's `MUTANTS` block states each mutant as one change to the learner's own `from_u128` (M1 push both limbs, M2 high limb first, M3 high limb from `x >> 63u128`), not as a full body (§7 deviation 9). The check unit's `MutantEvaluation` computes the matching Dafny outputs from `FromNat`'s result and prints `Valid` and `ToNat` per sample row; its run (raw `stdout.txt`, 2026-10-06): every output `Valid true`; M1's value right on every row; M2's wrong on `2^64 + 7` and `3 * 2^64 + 2`; M3's wrong on `2^64 - 1`, `2^64 + 7` and `3 * 2^64 + 2`. So the Dafny contract accepts M1 and rejects M2 and M3. The twin's reference-only tests show the Verus side: M1's output is never `wf` below 2^64 (its value right), M2 and M3 change the value. M1 is the fidelity finding the `FIDELITY` block's last line should state: the port promises canonical limbs, the source only `Valid` ones (and `FromNat` happens to produce canonical ones, which the mirror shows relative to the mirror).
- **Use-site check** under H7v: `0x2_0000_0000_0000_0005`, `0` and `u128::MAX` (author notes §2.4), live in the twin.

## 6. The agent files (rung 7)

- **Dafny** (A.15's `m2_agent_mono.dfy`, with the course header and the CONTRACT): `FROZEN` `ScaledSum`, `ScaledSumThree`; `API` `ScaleTwice`, `AddScaled`; empty `HELPERS`; `REFACTOR` bound 3 lines; `REVIEW` and `COMPARISON` blocks; markers `Q07.A1d` (after the imports) and `Q07.A2d` (after `HELPERS`, with the pending replay command). The twin is A.15's `m2_agent_refactored.dfy`: the helper `AddScaledValue` under `HELPERS`, after the loud heading, with the soft spots (author notes §2.5).
- **Verus** (A.15's `m2_agent_mono.rs`, names kept): `FROZEN` `scaled_sum`, `scaled_sum_three`; `API` `scale_twice`, `add_scaled`; `REFACTOR` bound 4 lines (the reference refactor's exec bodies are 4: two lets, one `proof { }` line, the result); the CONTRACT's last line is "no `reveal_with_fuel` call is added" (the Verus counterpart of the Dafny `{:fuel}` line). The twin: `lemma_sum_scaled` under `HELPERS`, after the heading.
- **The CONTRACT lines** classify as DV4 §6's forms (`dvl.contract_local.classify_line`): the gate (`vcheck-gate`), "zero tool-counted holes" (`zero-holes`), `specfreeze --against research/q07_frozen.{dfy,rs}` (`specfreeze-against`), `vaudit <file>` (`vaudit`), the `git diff` line (`git-diff`, evidence `patch.diff`); "re-verify after every edit" and the fuel line are audit lines.

**Runs** (the simulation root, §9): with `research/q07_frozen.dfy` and `.rs` cut from the shipped files as the headers say (the module line and imports, or the `use` lines and `verus! {`; then `### FROZEN` through `ScaledSumThree` / `scaled_sum_three`; then the closing brace) and committed: the shipped files against their snapshots, 0 findings each. The twins laid at the learner paths: `vcheck --gate` verified (127 tasks; 5), only the summary line, 0 holes; `specfreeze --against` 0 findings each; `vaudit` 0 findings each. `ScaleTwice`'s validity `ensures` deleted: gate, freeze and audit all pass (the designed catch); `ScaledSum`'s deleted: `freeze-changed — Q07_AgentRefactor.ScaledSum`. Verus: `scale_twice`'s value `ensures` relaxed to `>=`: gate, freeze and audit pass; `scaled_sum`'s: `freeze-changed — the statement of scaled_sum changed`. `scripts/contract_local.sh Q07 --available`: exit 3, "not available" (the apparatus pins are not built; Docker refused, H1 not done). `--file dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy --dry-run`: exit 0; starting state = the snapshot's commit; manifest 32 files; the seven acceptance lines sorted as `audit`, `vcheck-gate`, `zero-holes`, `specfreeze-against`, `vaudit`, `git-diff`, `audit`; self-test OK; "not yet available" for the images, the apparatus and Docker.

## 7. Deviations from the plan

1. **P5dv's answer is `D:ok fail V:ok fail`**, not the author notes' `D:fail ok V:ok fail` (§2). The scenario is unchanged; only the answer (re-captured, swept over seeds and both solvers) differs. The Dafny and Verus halves now agree; the prediction still separates commutativity from distributivity, and C2's demos and the agent files' distributivity calls stand. The P5dv docstring states nothing either way.
2. **H1d's reference fuel is 3** (the notes: 4), the least that verifies (§3).
3. **T1v's reference is the fuel call alone; H3d's reference drops two commutativity calls** (§3).
4. **W1d** is `NonzeroLimbProduct` (`0 < x * y <= (BASE - 1) * (BASE - 1)` for two nonzero limbs, by `LemmaMulStrictlyPositive` and `LemmaMulStrictUpperBound`, one call per fact), not a `LemmaMulUpperBound` bound: that call is C2's success, and the notes forbid naming `LemmaMulInequality` in a learner-visible file (§2.7), so the stepwise version of `LemmaMulUpperBound` was not available. Not Q09.H1d's statement (no power), not Q09.X1's (no further term).
5. **C2v's statement is `x * y <= (BASE - 1) * (BASE - 1)`**, not "below `BASE * BASE`": with one `lemma_mul_upper_bound` call the Verus goal `x * y < BASE * BASE` failed (probe `vcards.rs`: Verus does not close `(BASE - 1) * (BASE - 1) < BASE * BASE` for the spec constant without a nonlinear step). C2d keeps `< BASE * BASE` (Dafny closes the constant step).
6. **The Dafny card demos carry verbatim copies of L1's definitions** (`BASE`, and `ToNat` for C1d), as Q06's P3d does: a Dafny specimen is verified without the given layers (the first versions imported `QG_L1_BigNat` and stopped at resolve: "module QG_L1_BigNat does not exist").
7. **H8v ships `pub uninterp spec fn from_nat_mirror(n: nat) -> Seq<u64> decreases n, ;`** (QPLAN's statement column lists `decreases n`): without the measure in the shipped statement, the twin's `decreases n` made `reference_lint` report `statement-differs`, and a learner's correct answer would be `freeze-changed`. Verus accepts `decreases` on an `uninterp` spec fn (probe `uninterp_dec.rs`: one `uninterp` hole). The learner replaces `uninterp` by `open` and the `;` by a body.
8. **C1v's by-hand success avoids Q02.X3v's idiom.** Its first version (`seq![b].drop_first() =~= Seq::<u64>::empty()`) matched Q02's leak pattern `seq!\[b\]\.drop_first\(\)\s*=~=` (the leak verifier's one Q07 hit); the shipped version names the one-limb tail's value instead (`assert(seq![a, b].drop_first() =~= seq![b]); assert(seq_to_nat(seq![b].drop_first()) == 0); assert(seq_to_nat(seq![b]) == b);`, verified; the leak verifier then reports no Q07 hit).
9. **MUTANTS ship as one-line changes to the learner's own `from_u128`**, not as full bodies: a full mutant body would spell H7's exec code (the split and the canonical pushes) in the hole's own file, and a body without the learner's proof fails verification whatever the mutant, so the Verus column would say nothing. The check unit's Dafny mirrors are written from `FromNat`'s result for the same reason, and match the Verus mutants on the sample's rows (M3 differs from its Verus mutant only on inputs in `[2^127, 2^127 + 2^63)`, none in the sample).
10. **`vcheck --test` prints no test output**, so the check unit's header tells the learner to read the printed lines from the `stdout.txt` of the `--json` run's `raw_dir` (§8 item 3).
11. **The check unit holds a `Sample()` function and a `Show` method** besides the two tests (the mutant test loops over the sample).
12. **The Verus agent file's bound is 4 lines and its fuel line names `reveal_with_fuel`** (§6).

## 8. Tool problems (for the tools owner)

1. **High (blocks `firsttry Q07 --lint-hollow` in the static job): `firsttry`'s static hole finder does not know the Verus spec-definition hole.** `static_holes` (scripts/firsttry.py) matches `assume(`, `admit(` and `external_body` only, so `--lint-hollow` reports `verus/q/q07_internals_i/src/port.rs:64: Q07.H8v: an H item ships a hole form` although `vcheck` counts the hole (`kind: uninterp`, labelled `Q07.H8v`) and `dvl.verus` lists `uninterp` among its hole kinds. Consequences: lint-hollow fails (1 problem); `--empty-body` and `--report` do not see H8v as a hole (the report lists it as an ordinary H item); and the CI verify jobs' hole comparison (`ci.sh`'s helper `holes`, which compares the tool's count with `static_holes` per file and item) reports, run directly on Q07's `vcheck --shipped --json Q07 v` document, `verus/q/q07_internals_i/src/port.rs: Q07.H8v: the tool counts 1 hole(s), the file ships 0 hole form(s)` (1 mismatch, exit 1), so `verify-q-verus` fails on Q07 (the Dafny comparison: 4 = 4, 0 mismatches). Fix: add `\buninterp\b` (on a spec fn header) to the Verus branch of `static_holes`, as QPLAN §14.0's "spec-definition hole" row requires.
2. **High (blocks `firsttry Q07 --empty-body`): the gate runs an open-statement exec hole on its shipped form.** Q07.H7v ships with no `ensures` (QPLAN §14.0, §6 Q44), so on the shipped form every body verifies: the gate reports `✗ Q07.H7v FALLS TO AUTOMATION: the empty body verifies in TRIV seed=1, TRIV seed=2, TRIV seed=3` and `Q07 empty-body: 13/14 hole(s) pass the gate`, exit 1. Fix: for a symbol under `open_specs`, lay the twin's added `requires`/`ensures` over the shipped declaration before the variants run (the freeze pin already names the symbol). The gate on the intended statement passes (§10).
3. **Low: `vcheck --test` prints only PASSED/FAILED lines**, never a test's own output; Q07's mutant evaluation prints its results (by design, QPLAN §15.5), so the learner reads them from the raw run directory. A `--show-output` option, or printing the test binary's stdout under the PASSED line, would serve the port's audit.
4. **Low (advisory flag outside Q07's files): `QG_L2_BigNat.ToNatBound` spreads above the 20% flag in Q07's `std` unit.** `vcheck --brittleness --solvers dafny/Q/Q07_InternalsI/std`: stable in all six rows, and `spread above 20%: 2 symbol(s), flagged, never gating: QG_L2_BigNat.ToNatBound (CV 64.9%, solver 4.14.1), QG_L2_BigNat.ToNatBound (CV 49.3%, solver 4.12.1)` (56,402..200,891). A given layer's lemma, so no Q07 change; the Q09 lane's `stable` sweeps of `std` units will show the same flag (it never gates).
5. **Low: `--ref` on an exit twin needs the learner file at its path**: before the learner exit file existed, `vcheck --ref` on the Dafny exit twin stopped at resolve ("module QG_L1_BigNat does not exist"), as a loose file with no chain. Once the learner file existed it ran in the module's context (126 verified).

## 9. Verification runs (authoring worktree and the simulation root, 2026-10-06)

- **Reference gates** (`vcheck --ref`): Dafny `std` twin 134 verified, check twin 128, Dafny exit twin 126, Dafny agent twin 127; Verus crate twin 20 (with `port.rs`), Verus exit twin 3, Verus agent twin 5; all 0 holes, silent. `vaudit --ref --mode reference` on each of the seven twins: 0 findings.
- **Learner files** (learner loop): `vcheck --module Q07`: "2 unit(s): 2 verified, 0 not; 11 hole(s) in all" (`std` 130 tasks, 4 holes; crate 7 holes: `lib.rs` 4, `port.rs` 3, each labelled with its item id); exits 2 + 2 holes; check unit 0; agent files 0. `vaudit`: one finding per hole (`audit-bodyless-ghost`; `hole-assume`, `hole-external-body`, `hole-uninterp`), 0 on the check unit and on both agent files.
- **Pins:** `vcheck --ref --pin-counts Q07` (Dafny 134, 9 contract declarations, floor 9; Verus 20, 10, floor 10; 8 file pins); `vcheck --shipped Q07`: 8 files, 0 problems. `specfreeze --pin Q07`: 65 statements in 18 files, `open specs (QPLAN §6 Q44): verus/q/q07_internals_i/src/port.rs: from_u128`; `--check`: 0 findings. `pins.py --update --ref --module Q07` (7 salted); `pins.py --update` on the five demos (each "sealed … one hash, no output line"); `pins.py --ci --module Q07`: 34 pins, 0 problems (the five in-file `EXPECT` pins included); `pins.py --ref --module Q07`: 7 checks, 0 problems.
- **Lints:** `CI=true reference_lint.py --module Q07`: 0 findings (6 twins). `firsttry Q07 --lint-hollow`: 1 problem, H8v (§8 item 1). `firsttry Q07 --report` as shipped: 7 unfilled slots, 2 unattempted test-outs, 19 commented checks (H7's use-site check and suite), forms not met 0. `check_course_map.py`: no Q07 error (the run's errors are Q09's, in progress); `--only registry` OK; `gen_units.py --check` OK.
- **Compiled checks:** `vcheck --test dafny/checks/Q07_checks.dfy`: 2 passed. The crate as shipped has no live test (`vcheck --test verus/q/q07_internals_i`: "no test ran", as designed until H7's suite is uncommented); with the port twin laid at the learner path (simulation): 4 passed (the suite and the three reference-only mutant tests).
- **Brittleness** (`vcheck --ref --brittleness`, Dafny with `--solvers`): every twin `stable` (Dafny `std`, exit, agent: six rows each; Verus crate, exit, agent: seeds 1–3); the only flag is item 4 of §8.
- **Learner-flow simulation** (`/tmp/dvl0-dv3b-q07/sim`: a git copy of the worktree without `Solutions/` and `bench/public/`, `main` = shipped, branch `work`): T1d and T1v written first: `--check` refused both ("waits for the module's predictions (7 P item(s) unrecorded …)", nothing recorded, exit 1); the seven slots filled with the reference answers: 7/7 first-try passes, the T items refused again in that run; the next `--check`: T1d and T1v `predict pass`; the `after:` demos then ran (`card-c1d`: the pinned error at 26; `card-c4d`: six errors); `--exit` on the shipped exits: 0/4, nothing recorded (every block `unattempted: hole`); with the exit twins: "Q07 exit: 4/4 (threshold 3; per language Dafny 2/2 (≥1), Verus 2/2 (≥1)) PASS"; with every hole filled from the twins, the slots enabled and the checks live: `--report --strict` "strict: OK (…, forms not met 0, …, failing property-test runs 0, unrecorded first tries 0)" with "property tests (Q07.H7v): verus/q/q07_internals_i: verified — 4 passed, 0 failed"; `vcheck --gate` 134, 20, 126 and 3 verified with 0 holes; `vaudit` 0 findings on each; `specfreeze --check Q07` 0 findings (the port's added `ensures` accepted under `open_specs`); `pins.py Q07` 7 pass.
- **Negative checks** (simulation): H5 answered by `nonlinear_arith` (its `cfree:` answer) verifies (gate 21 verified) and `--report --strict` fails with `form: Q07.H5v: form no-nl not met`; in a fresh exit run with X1v answered by `*` (its first `cfree:` answer): "Q07.X1v now ✗ form bv-exec not met (`*` in exec code at line 32)", "3/4 … PASS".
- **Construct-free answers measured** (`vcheck --module Q07` probes): H6v's `/`-`%` split verified; H7v's split by `/` and `%` (with the twin's proof) verified; X1v's multiplication verified; X2v's `nonlinear_arith` step verified; H5v's (above) verified. Each is stopped only by its form (the forms gate, §10). H6v's shift-and-cast and X1v's shift-and-or without a proof fail verification.
- **Leak checks:** the leak-pattern README's verifier: no Q07 hit (the remaining FAIL lines are hits in `bench/public/`, the installed third-party sets: not Q07 files); a line scan of every tier reference line (the author notes' Appendix A code blocks for Q07–Q09 and the backticked references of §2–§4) and of every Q07 twin's answer lines against all Q07 learner-visible files: only shipped statements, the prediction scenarios, the planned use-site check and suite rows, the agent files' own (A.15) lines, and C1's two-limb steps (`seq![a, b].drop_first() =~= seq![b]`, which the Q09 Verus bank's true lemma `lemma_two_limbs_value` also uses: the bank's proof is the contractor's, in Q09; and `reveal_with_fuel(seq_to_nat, 3)`, the count a two-limb literal needs, which H4v's answer also uses with its extensionality facts: the plan's own C1 design). No learner-visible Q07 file names `LemmaMultiplyDivideLt`, `LemmaMulInequality`, `lemma_div_denominator`, `lemma_fundamental_div_mod`, `lemma_div_multiples_vanish`, `LemmaModMultiplesBasic`, `LemmaFundamentalDivModConverse` or a hole's fuel count in a hole's block. L4 (as built) holds none of those calls, no `fuel`, no `bit_vector` and no shift. No Q07 file states a Q08 or Q09 item's statement (QPLAN §16.2, §17.2 and the exits of the author notes §3.7, §4.8); shared techniques: W1d's tight bound `(BASE - 1) * (BASE - 1)` with constant bounds (L4's `MulLimbDigit` idiom; Q09.X1's needs a symbolic bound and an expansion), the agent files' distributivity call (Q08.H4v uses a sibling lemma in a loop through a trait).
- **Memory:** every job under the `dvl` caps, one at a time; `free -g` showed 83–93 GB available before each batch; no job killed.

## 10. Empty-body gate (`firsttry.py Q07 --empty-body`, 2026-10-06, 18 min 44 s)

`Q07 empty-body: 13/14 hole(s) pass the gate`, exit 1 (H7v: §8 item 2; H8v is not seen as a hole: §8 item 1).

| item | result |
|---|---|
| T1d, H1d | the empty body fails in every run (maxauto and seeds 1–3 as shipped: no attribute) |
| H2d, H3d | fail in every run; `lever-needed` (maxauto turns nonlinear arithmetic on), as planned |
| X1d | fails in every run; `empty-body-inconclusive` (maxauto) |
| X2d | fails in every run |
| T1v, H4v | every mode fails |
| H5v | every mode fails; forms gate: the twin meets `no-nl`; `cfree` answer 1 fails its forms (`nonlinear_arith` at line 212) |
| H6v | every mode fails (TRIV runs `{ (0u64, 0u64) }`); the twin meets `bv-exec`; `cfree` 1 fails its forms (`/` in exec code), `cfree` 2 fails verification |
| H7v | **FALLS TO AUTOMATION on the shipped form** (TRIV verifies, seeds 1–3: no `ensures` ships); the twin meets `bv-exec`; `cfree` 1 fails its forms (`/` in exec code). On the intended statement (the simulation root, the twin's `ensures` laid over the shipped `external_body` form, `dvl.verus.empty_body` with the twin's `triv:` body): verdict `failed` — E0, E0H, E1, E2, EC (seeds 1–3), EM (seed 1) fail with "precondition not satisfied", TRIV (seeds 1–3) with "postcondition not satisfied": the gate passes |
| H8v | not run (not a static hole form, §8 item 1). A spec-definition hole has no statement to falsify; H9v's gate (below) runs with the mirror uninterpreted |
| H9v | every mode fails |
| X1v | every mode fails (TRIV `{ 0u128 }`); the twin meets `bv-exec`; `cfree` 1 fails its forms (`*`), `cfree` 2 fails verification |
| X2v | every mode fails; the twin meets `no-nl`; `cfree` 1 fails its forms |

No Q07 hole is an annotation hole, so no twin carries `@hole-begin` regions and no region gate applies.

## 11. Open

- Tools owner: §8 items 1 and 2 (high), item 3 (low).
- Records lane: an as-built entry for Q07's code (this file's §1, §7, §8, §10), and P5dv's re-captured answer recorded against the author notes' table.
- Chapter lane: the chapter quotes no replay output (A2d pending, Δ156); the P5dv paragraph follows §2's answer; the port section explains where the check unit's printed lines are (§7 item 10); `docs/Q07_InternalsI.md` does not exist yet, so `chapter_lint.py --all` fails on Q07.
- Kit lane: the leak patterns for Q07 (`tests/instructor/leak_patterns/Q07.txt`) should avoid C1's and C2's given lines (§9 leak checks); the rubric's A5 line names `from_u128` as an open statement (QPLAN §6 Q44).
- DV4 (step 3b): lifts A2d's pending mark; `contract_local.sh --dry-run` already parses Q07's CONTRACT and finds the starting state (§6).
