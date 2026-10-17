# Q03 code notes (DV2a, the Q03 module lane)

> **Author-only.** Prediction answers, the evidence each was captured from, the hole
> gate results and the reference notes of the two delivery specimens that have no twin.
> Never quote, paraphrase or link any of it from a learner-visible file. The item plan is
> `QPLAN.md` §4 (learner-visible) and `Solutions/plans/Q01-Q03-author-notes.md` §4 (the
> plan lane's author notes); this file records what the module lane built and re-captured
> on the real files, 2026-10-04.

Every run below went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, or the `dvl` library functions they call), at the
course pins (Dafny 4.11.0, `--resource-limit 5000000`, `--cores 2`; Verus 0.2026.09.27,
`--rlimit 2`), one solver job at a time under the `dvl` caps. Probe files are lane scratch
under `/tmp/dvl0-dv2a-q03/probes/` and are not archived; raw outputs went to
`/tmp/dvl-1000/runs/`.

## 1. Files

| learner file | twin |
|---|---|
| `dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy` (5 holes: T1d, H1d–H4d) | `Solutions/dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy` |
| `dafny/checks/Q03_checks.dfy` (P9d) | `Solutions/dafny/checks/Q03_checks.dfy` |
| `dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy` (2 holes: X1d, X3d; X2d prompt-as-heading) | `Solutions/dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy` |
| `verus/q/q03_first_syntax_ii/src/lib.rs` (5 holes: T1v, H1v–H4v) | `Solutions/verus/q/q03_first_syntax_ii/src/lib.rs` |
| `verus/q/q03_first_syntax_ii/src/exit.rs` (3 holes: X1v, X2v, X3v) | `Solutions/verus/q/q03_first_syntax_ii/src/exit.rs` |
| `specimens/Q03/P3d.dfy.specimen`, `P10v.rs.specimen`, `P11d.dfy.specimen`, `P12d.dfy.specimen`, `P13v.rs.specimen`, `P14v.rs.specimen` | `Solutions/specimens/Q03/` (same names; the P11d and P13v twins were added in the DV2a fix round, §7) |
| `specimens/Q03/card-c{1,2,3,4}d.dfy.specimen`, `card-c{1,2,3,5}v.rs.specimen` (WRITE demos, in-file `// EXPECT`) | none (demos are given) |
| `specimens/Q03/card-c{6,7,8}dv-{d.dfy,v.rs}.specimen` (divergence demos) | none; sidecars `expected/specimens/Q03/*.expect` (five of them sealed by `// after:` lines, §7) |
| `slots/Q03.slots` (11 lines, unfilled) | `Solutions/slots/Q03.slots` |
| — | `expected/Q03.pins` (11 salted hashes), `expected/Q03.counts` (schema 2), `expected/Q03.freeze` |

## 2. Prediction answers, re-captured

| item | answer | evidence (this lane) |
|---|---|---|
| P1dv | `D:8 V:8` | `specimens/Q03/card-c6dv-d.dfy.specimen` under `dafny.test`: `expectation violation`; probe `p1d_print.dfy` (the same method with a `print`): `P1Print.SevenTest: Seven returned 8`. `card-c6dv-v.rs.specimen` under `verus.test`: `assertion left == right failed, left: 8, right: 7` |
| P2dv | `D:ok V:ok` | `vcheck --gate p2d.dfy`: verified, 1 verified; `vcheck --gate p2v.rs`: verified, 1 verified (also the C7dv demos) |
| P3d | `FAILS b d` | `pins.py --ref --module Q03` on the twin specimen (the obligation check passes); `[b]` and `[d]` fail `value does not satisfy the subset constraints of 'Limb'` |
| P4v | `d` | `vcheck --module Q03 p4v_{a,b,c,d}.rs`: [a] and [b] `cannot call function … with mode exec` (stage resolve); [c] `The Verus types 'nat' and 'int' can only be used in ghost code …` (stage parse); [d] verified, 3 verified. Re-run by the fix round's integration lane with the scenario's exec fn renamed `triple` (§7): the same four results |
| P5dv | `D:0 V:2` (re-posed in the DV2a fix round, §7; the first V half's answer was `absent`) | D: `dvl.dafny.audit` on `p5d.dfy` (one bodyless lemma): the raw `dafny audit` run exits 0 and prints `Dafny auditor completed with 1 findings`; re-run plainly in the fix round (`dafny audit p5d.dfy`, the pinned binary under the dvl cap): exit 0, `Dafny auditor completed with 1 findings`. V: the prompt's three proof fns run plainly (`verus p5v.rs --crate-type=lib`, the pinned binary under the dvl cap, `/tmp/dvl0-dv2afix-q03/probes/p5v/`): exit 0, `verification results:: 2 verified, 0 errors`; with `--output-json`: `verified: 2`, `errors: 0`, `success: true`. Controls: `lemma_a` + `lemma_b` gives `2 verified`, `lemma_a` + `lemma_c` gives `1 verified`: the `assume(false)` body is counted, the `external_body` fn is not |
| P6dv | `D:1 resolve V:1 resolve` | `vcheck p6d.dfy`: 1 error `RHS (of type int) not assignable to LHS (of type bool)`, stage resolve; `vcheck p6v.rs`: 1 error `mismatched types`, stage resolve |
| P7dv | `D:same V:same` | `vcheck --module Q03 p7d.dfy`: both lemmas `a postcondition could not be proved on this return path`; `vcheck --module Q03 p7v.rs`: both `postcondition not satisfied`. Control: under `--module Q02` (auto-induction) the true Dafny lemma verifies, so "in this unit" is load-bearing |
| P8dv | `a` | `vcheck --gate p8d.dfy` (5 verified): `x * 2 + 1 > 7 <==> x > 3` for every int, and b, c, d each differ from the wp at `x = 4` |
| P9d | `2` | `pins.py --ref --module Q03`: the twin check unit's `expect |FromNat(18446744073709551616)| == 2;` passes (`FromNat(BASE) == [0, 1]`) |
| P10v | `8` | `pins.py --ref --module Q03`: the twin specimen's `assert(… == 8) by (compute_only);` verifies (`limb_at` reads index −1 as 0) |
| P11d | `trusted audit` | copy of the specimen: `vcheck --gate` verified (4 verified, 0 holes); `vaudit`: 2 findings at the `assume {:axiom}` line (`assume-axiom` from the lint, `audit-assume-axiom` from `dafny audit`) |
| P12d | `weak reader` | copy: `vcheck --gate` verified, `vaudit` 0 findings; `ToNat(s) >= 0` holds for every natural |
| P13v | `hole gate` | copy with `--module Q03`: learner loop `1 hole external_body`; `--gate` fails (`1 hole(s)`) |
| P14v | `healthy none` | copy with `--module Q03`: `--gate` verified (1 verified), lint 0 findings |

Fix round (§7), with the `// planted:` markers in place: `vcheck --ref` and `vaudit --ref` on the
four delivery twins give P11d verified (4) with 2 audit findings at the planted line, P12d
verified with 0 findings, P13v failed with `1 hole` (`external_body`) and 2 audit findings,
P14v verified (1) with 0 findings; the same instruments on the learner specimens in the
simulation copy (first tries recorded) agree. The markers change no instrument's output.

`expected/Q03.pins` was written from `Solutions/slots/Q03.slots` by
`pins.py --update --ref --module Q03`; `pins.py --ref --module Q03` reports 14 checks, 0
problems. Since the fix round the pins are salted (`sha256("Q03:<item>:<answer>")`), so no
well-known short-string hash appears; P8dv (`a`) and P4v (`d`) still have tiny answer
spaces, so anyone who knows the salt rule can try every option: inherent to hash pins of
short verdicts.

## 3. Holes: references and the empty-body gate

Dafny (`dvl.dafny.empty_body`: the maximal-automation run plus seeds 1–3 as shipped):

| item | max-auto | seeds 1–3 | note |
|---|---|---|---|
| T1d `MaxLimb` | failed | failed ×3 | the ghost index is a method clause, not a necessity |
| H1d `AddLimbToNat` | verified (`lever-needed`) | failed ×3 | the Q03 unit's `manual-lemma-induction` is the lever (Δ45) |
| H2d `FromNatCorrect` | verified (`lever-needed`) | failed ×3 | same lever |
| H3d `ExistsCanonicalFive` | failed | failed ×3 | |
| H4d `TryLimb` | failed | failed ×3 | |
| X1d `FindAtLeast` | failed | failed ×3 | exit file, verified on the module chain with Q03's options |
| X3d `CheckedSub` | failed | failed ×3 | |

Verus: see §5 (the gate run of this lane). Hole references are the twins' bodies; each
twin docstring explains its proof.

## 4. Deviations from the plan (and why)

1. **Q03.H1v's given code is reordered.** In the loop body `i = i + 1;` now comes before
   `proof { c = c.push(carry as nat); }`, and the end of `add_limb` reads
   `let out = BigNat { limbs: res }; proof { lemma_add_limb_lift(a@, out@, c); } out`.
   Reason: `dvl.verus`'s E0/E0H/E1 variants strip a `proof { }` block only when it
   starts a statement; a block that directly follows an `if … { } else { }` statement is
   merged into it (`verus_spec._stmt_end` does not end the `if` statement before
   `proof`), so the spike order kept two proof blocks that use the stripped `c` and the
   variant failed to compile (`cannot find value c in this scope`, verdict `error`).
   Reproduced on a scratch copy with the spike order: `E0 seed=1: no-verify(cannot find
   value c in this scope)`, verdict `error`. With the reorder: `E0 fails(error)`,
   `INV fails(error)`, verdict `failed` (the hole passes). Everything Δ52 gives is still
   given. **Fix round:** the tools lane fixed `verus_spec._stmt_end` (a block-like
   statement ends at its closing brace), so QPLAN §6 Q9 is closed; the reorder stays (it
   is harmless) and §7 records the re-run on the shipped form.
2. **No twins for the P11d and P13v delivery specimens.** The twin of a delivery is the
   delivery itself plus an enabled switch, and the reference-mode lint flags the
   planted trust leap (`assume-axiom`) and the planted hole (`external-body`): the
   reference lint cannot pass with those twins. Their answers are pinned through
   `Solutions/slots/Q03.slots` and `expected/Q03.pins` (spec: specimen twins are
   optional). Reference notes: P11d `trusted audit` — the helper's body is an
   `assume {:axiom}`, silent in the gate (no hole counted) and listed by `scripts/vaudit`
   (lint and `dafny audit`); P13v `hole gate` — the helper is `external_body`, the
   course's exec-hole form, counted by `scripts/vcheck` under `--no-cheating`, so the
   gate fails. **Fix round:** resolved. Both twins now exist; the planted line of each
   delivery carries `// planted: <item id>`, which only the shipping lints honour, so
   `reference_lint.py` passes on them (§7).
3. **`firsttry.sh Q03 --lint-hollow` reports one problem:** `specimens/Q03/P11d.dfy.specimen`,
   `lint: assume-axiom`. The planted `assume {:axiom}` is P11d's lesson; every Dafny trust
   form that the gate misses is a learner-mode lint finding by design (Δ3), so no
   `trusted` Dafny delivery can be lint-clean (probed: a body-less `forall` statement and
   a body-less loop are lint-clean but warn, so the gate fails them). Tools owner:
   exempt the planted lines of S12 delivery specimens from `--lint-hollow` (for example
   a `// planted:` marker, or the lint skipped for verdict-P specimens). **Fix round:**
   resolved by the `// planted:` marker; `firsttry.sh Q03 --lint-hollow` passes.
4. **The Dafny exit twin's X2 declarations carry `// reference-only`** (`type Odd`,
   `method OddCheck`): the learner file ships the block empty (prompt-as-heading), so the
   reference lint otherwise reports them as `declaration-extra`.

## 5. The empty-body gate on the shipped files (this lane)

`scripts/firsttry.sh Q03 --empty-body --eb-modes E0,E0H,E1,E2,EC,EM,NL,INV,TRIV` (every
pinned seed; EM under seed 1; EC applies to nothing, no course broadcast group exists
below L3): **15/15 holes pass** (exit 0, 1 min 41 s): T1d, H1d–H4d, X1d, X3d (Dafny,
H1d and H2d `lever-needed`), T1v, H1v–H4v, X1v, X2v, X3v (Verus).

BV, run apart with a 150 s wall clock (QPLAN §6 Q5): Q03.H3v seeds 1–3 `killed(harness)`
(the front-end hang on a `Seq` goal; counts as failing); Q03.X2v seeds 1–3
`no-verify(bit_vector prover cannot handle type vstd::seq::Seq<u64>)` (counts as failing
inside the full gate; alone it gives verdict `error`).

TRIV with a trivial body (firsttry passes none for a non-integer return) on every Verus
exec hole whose return type `_trivial_body` does not cover, seeds 1–3: H1v and H2v
(`BigNat { limbs: Vec::new() }`), H4v and X3v (`None`), X1v (`(false, Ghost(0))`): all
`fails(error)`, so no exec spec is vacuous. T1v's TRIV (`0`) ran inside the gate.
**Fix round:** these bodies are now `// triv:` lines in the twins' item blocks, so
`firsttry --empty-body` (and CI's empty-body job) runs them itself (§7).
H1v (annotation hole): E0 and INV `fails(error)` on the shipped form (§4 item 1).

## 6. Other runs

- `vcheck --ref` on all five twins: verified, silent (Dafny core 48, Verus crate 21,
  Dafny exit 28, Verus exit 4, check unit 23). `vaudit --ref`: 0 findings on each.
- `vcheck --ref --pin-counts Q03`: `expected/Q03.counts`, 14 symbols per unit.
- Learner loop `vcheck Q03`: both units verified, 5 + 5 labelled holes; the exit files
  2 and 3 labelled holes.
- `vcheck --brittleness` (seeds 1–3): both learner units stable; the twins, laid at their
  learner paths in a scratch copy, stable (widest resource spread: the C1v card's
  `count_zero_limbs`, CV 13.2 %, advisory).
- Learner simulation in a scratch copy (`/tmp/dvl0-dv2a-q03/sim`, not archived): every
  slot filled with the reference answer except P8dv (a wrong `b`), `firsttry --check`
  recorded 13 ✓ and P8dv ✗; with the twins laid over the learner files and the switches
  enabled, `firsttry --exit` scored 6/6 PASS, `--report --strict` passed, `vcheck --gate
  Q03` passed against the count pins (48 and 21), and `vaudit` was clean.

## 7. DV2a fix round (this lane, 2026-10-04)

Every run below went through the course wrappers or the `dvl` library, under a 16 GB
`systemd-run` scope, `DVL_SCRATCH=/tmp/dvl0-dv2afix-q03/dvl`, one solver job at a time.
Probe files are under `/tmp/dvl0-dv2afix-q03/probes/` (not archived).

1. **Planted markers.** Each of the four delivery specimens carries exactly one
   `// planted: <item id>`: P11d on the `assume {:axiom}` line, P13v on the
   `#[verifier::external_body]` attribute (where the reference lint reports
   `external-body`), and P12d and P14v on their `ensures` line. The healthy and weak
   deliveries carry a marker as well, so the marker's presence does not separate the species.
   Each specimen header gains three lines: the marker is course bookkeeping, present in
   every delivery whatever its species. The twins of P11d and P13v now exist (header lines
   22–25 rewritten as in the P12d twin, with no `SLOT:`, and the marker kept). Results:
   `firsttry.sh Q03 --lint-hollow` OK (25 files), `reference_lint.py` (CI=true) 0 findings
   on 11 twins. The instruments ignore the marker: §2's fix-round paragraph.
2. **P5dv re-posed (V half).** See §2. The learner loop and the gate run only with
   `--no-cheating`, so neither prints a plain run's count. `vcheck --test --json` prints a
   plain test build's `verified_count` (the c6dv-v sidecar showed `verified: 1` for an
   assume-bodied fn), so that demo now waits for P5dv.
3. **Card demos.** `// after:` lines: `card-c6dv-d` Q03.P1dv; `card-c6dv-v` Q03.P1dv and
   Q03.P5dv; `card-c7dv-d` and `card-c7dv-v` Q03.P2dv; `card-c8dv-d` Q01.P10dv (its warning
   line shows that the bodyless lemma is reported). `card-c8dv-v` (the `--no-cheating`
   record, which bore on the first P5dv) settles no current prediction and stays unsealed.
   `pins.py --update --module Q03` re-wrote all six sidecars from real runs: five
   sealed, c8dv-v identical to its previous content. Learner simulation (below): before
   any record, `vcheck` and `vcheck --test` refuse c6dv-v ("waits for Q03.P1dv,
   Q03.P5dv") and c8dv-d ("waits for Q01.P10dv"). Once Q03's tries are recorded, c6dv-v
   runs (`FAILED seven_test`) and c7dv-d verifies; c8dv-d still waits for Q01.
4. **H1v empty-body variants.** `dvl.verus.empty_body(verus/q/q03_first_syntax_ii, "Q03.H1v",
   modes=E0,E0H,E1,INV)`, seeds 1–3: verdict `failed`, all 12 runs `fails(error)`. The raw
   jobs reached verification: E0/E0H/E1 `postcondition not satisfied` and
   `precondition not satisfied` (`verified 0, errors 2`); INV `precondition not
   satisfied`.
5. **TRIV bodies.** The twins carry `// triv:` lines: H1v and H2v `{ BigNat { limbs:
   Vec::new() } }`, H4v and X3v `{ None }`, X1v `{ (false, Ghost(0)) }`.
   `firsttry.py Q03 --empty-body --eb-modes TRIV`: each of the five runs its declared body
   and fails in every run. H3v and X2v are proof fns, so TRIV does not apply: the narrowed
   run reports them `refused`, which is an artefact of the narrowing.
6. **Re-pins.** `pins.py --update --ref --module Q03`: 11 salted pins (checked by hand:
   `sha256("Q03:P5dv:D:0 V:2")` and `sha256("Q03:P8dv:a")` equal their pins).
   `vcheck --ref --pin-counts Q03`: schema 2. The units are unchanged (48 and 21 verified,
   14 + 14 symbols). Files: exercise 5 + 5 holes, check 0, exit 2 + 3, all `verified`,
   0 errors. `specfreeze --pin Q03`: byte-identical to the previous pins (87 statements,
   25 files), since no statement changed.
7. **Checks** (all green or in their shipped state):
   - `vcheck --shipped Q03`: 5 files, 0 problems.
   - The learner loop on `vcheck Q03` gives 5 + 5 labelled holes. `vcheck --gate` on the
     two learner units fails on exactly those holes, which is the shipped state.
   - `vcheck --gate dafny/checks/Q03_checks.dfy`: verified, 22.
   - `vcheck --ref` on the five unit, exit and check twins: 48, 21, 28, 4 and 23 verified.
   - `vaudit`: the learner files report their shipped holes (5, 5, 2, 3) and the check
     unit 0. `vaudit --ref` on the five twins: 0.
   - `pins.py --ci --module Q03`: 43 pins, 0 problems. `pins.py --ref --module Q03`: 14
     checks, 0 problems.
   - `specfreeze --check Q03`: 0. `reference_lint.py`: 0.
   - `firsttry.sh Q03 --lint-hollow`: OK. `--report`: 14 slots unfilled, 2 test-outs
     unattempted, 23 commented checks, 0 missing, 0 vacuous, exit 0.
   - `firsttry.sh Q03 --empty-body`, every default mode and seed with BV under the new
     120 s clock: 15/15 before the `triv:` lines (7 min 51 s), and 15/15 again after them (7 min 57 s; the five TRIV bodies ran).
8. **Learner simulation** (`/tmp/dvl0-dv2afix-q03/sim`, deleted afterwards because it held a copy of `Solutions/`: a copy of the worktree with a fresh
   git repository, `main` = the shipped state, a `learner` branch, `--root` pointing at it;
   nothing was written to the worktree's `instructor/`):
   - T1d and T1v were filled with the twins' bodies, their checks left commented, and
     `firsttry --check` ran: `✓ Q03.T1d`, `✓ Q03.T1v`, recorded `predict pass`.
   - Then every slot was filled with the reference answer (P5dv `D:0 V:2`) and the run
     repeated: 14 of 14 `✓ … first try passes`, against the salted pins.
   - The delivery specimens were then run through the instruments: P11d gate verified,
     vaudit 2 findings at the planted line; P13v gate failed, 1 hole, vaudit 1 finding.

**Integration lane, after this lane reported (2026-10-05).** The leak scan found that Q03.P4v's quoted scenario declared `fn double(x: u64) -> (r: u64) requires x < 1000, ensures r == 2 * x, { x * 2 }`, a whole answer of the Q01 exit item Q01.X1v (QPLAN §1.1 rule 3: an exit answer may appear only in `Solutions/` and in higher layers). The scenario, in the learner file and its twin, now declares `fn triple(x: u64) -> (r: u64) requires x < 1000, ensures r == 3 * x, { x * 3 }` and its calls use `triple(3)`. Real runs (`vcheck --module Q03 /tmp/dvl0-dv2afix-integ/p4v/p4v_{a,b,c,d}.rs`, deleted afterwards): [a] failed, 1 error `cannot call function `p4v_a::triple` with mode exec`, stage resolve; [b] the same for `p4v_b::triple`, stage resolve; [c] failed, 1 error `The Verus types 'nat' and 'int' can only be used in ghost code …`, stage parse; [d] verified, 3 verified. The reference answer and its pin are unchanged. The block is a comment, so `specfreeze --check Q03` still reports 0 findings.

