# Q01–Q03 author notes (DV2a item plan)

> **Author-only.** This file holds prediction answers, exit answers, reference proofs, gate results, the card demos' intended content and the planted soft spots of the agent files. Never quote, paraphrase or link any of it from a learner-visible file (`QPLAN.md`, the registry, exercise, check, exit and agent files, specimens, `slots/`, `expected/`, chapters, banks, rubrics). The learner-visible plan is `QPLAN.md`; item ids here are the same.

Written 2026-10-04 by the DV2a plan lane; revised the same day after the critique (§7 lists every finding and what was done). Every tool result quoted below was captured on the pins, through the course wrappers (`scripts/vcheck`, or the `dvl` library functions `dafny.verify`, `dafny.test`, `dafny.empty_body`, `verus.verify`, `verus.test`, `verus.empty_body`), at the course limits (Dafny `--resource-limit 5000000`, Verus `--rlimit 2`), one solver job at a time under the `dvl` caps. Probe files are lane scratch, **not archived**: the first pass under `/tmp/dvl0-dv2a-plan/{d,dp,dp2,v,vp,vp2,x,x2,x3,p1}/`, this revision under `/tmp/dvl0-dv2a-plan/r2/{d,v}/` (named `r2/…` below); raw outputs under `/tmp/dvl-1000/runs/`. The probes use inline copies of the layer text; `r2/d/L1.dfyfrag`, `r2/d/L2.dfyfrag` and `r2/v/base.rsfrag` are exactly the layer text QPLAN §1.2–§1.3 specify. **Every answer below is re-captured on the real files** by the lane that writes them (`scripts/pins.py --update --ref --module <ID>` for verdict hashes, `pins.py --ref` for specimen and value slots, `firsttry.sh <ID> --empty-body` for the gate). Where an answer rests on a `VERSIONS.md` row instead of a probe, the row is named.

**DV3a records lane, 2026-10-05.** QPLAN no longer carries any exit statement or prompt (QPLAN §6 Q25, DELTAS Δ133): §2.9, §3.6 and §4.5 below hold Q01's, Q02's and Q03's exit tables as they stood in QPLAN, verbatim, with the other QPLAN lines that described an exit statement.

## 0. What was and was not run

- **Dafny empty-body gate** (`dvl.dafny.empty_body`: the max-automation run plus seeds 1–3 as shipped): Q01.H1d, H2d, H3d, X4d; Q02.H1d (plain form of the statement), H5d, H6d, X3d; Q03.T1d, H1d, H2d, H3d, H4d, X1d (results per module). Q02.H3d, H4d rest on DV0's gate of the same spike lemmas.
- **Verus empty-body gate**, seed 1, light modes. Proof fns: E0, E0H, E1, NL, BV (BV under a 150 s wall clock): Q01.H2v, H3v, X3v; Q02.H1v, H7v, H8v, X3v; Q03.H3v, X2v. Exec holes: **TRIV on every Verus exec-hole reference** (a trivial body must fail the spec): Q01.H1v (first pass); Q02.H5v, H6v, X1v, X2v and Q03.T1v, H2v, H4v, X1v, X3v (`r2/v/exec.rs`, all `fails(error)`). Annotation holes **as shipped** (`r2/v/ship.rs`): Q02.H2v E0, E0H, E1 `fails(error)` (INV does not apply: no invariant ships); Q03.H1v INV `fails(error)`, while E0, E0H and E1 did not reach verification (§4.2; QPLAN §6 Q9), so the gate's verdict on it was `error` at plan time. The module lane reordered the given code and the DV2a fix round fixed `verus_spec._stmt_end`: on the shipped form E0, E0H, E1 and INV all reach verification and fail (`Q03-code-notes.md` §7).
- **What E0 shows on an exec hole.** On the shipped form `external_body` + `unimplemented!()`, E0 strips the lever and fails on `unimplemented!()` (`p1/unimpl.rs`: `precondition not satisfied` in `core/src/macros/mod.rs`): that run proves nothing. TRIV is the evidence that the spec is not vacuous, and it ran on every Verus exec hole.
- **Not run:** E2 and EM (memory-heavy: up to 7.5 and 14 GiB in DV0), EC (no course broadcast group before L3), Verus seeds 2–3, a region-level gate for annotation holes (none exists; Q02.H2d has the bare probe instead, §3.2). The CI gate runs the rest.
- **BV hang.** On every Verus proof-fn candidate the BV mode was killed by the wall clock (`killed(harness)`, which the gate counts as failing). A first run without the short wall clock spun for more than 13 minutes on Q01.H2v before the lane stopped it (Δ58's front-end hang on goals over `Seq`; QPLAN §6 Q5).
- **Relabelled first-pass evidence.** The first pass labelled two gate runs `Q02.T1d` / `Q02.T1v`. They gated an abandoned candidate, `lemma_two_append_zeros` (two scoped lemma calls; Verus E0, E0H, E1, NL failed), not today's T items, which are prompt-as-heading definitions with no hole. They are evidence for no item.

## 1. The spine layers (building L1 and L2 from the DV0 spikes)

**Dafny L1** = `Solutions/spikes/dafny/QG_L1_BigNat.dfy` lines 10–62 (`BASE`, `Valid`, `ToNat`, `Pow`, `Head`, `Tail`, `Drop`, `ToNatAppendZero`) without the `@hole-begin/@hole-end` markers, **plus** an explicit `decreases |s|` on `ToNat` and `ToNatAppendZero` and `decreases n` on `Pow` (the spike has none). **Dafny L2** = the spike L1 helpers (lines 64–141: `ToNatSingleton`, `ToNatCons`, `ToNatHeadTail`, `ValidTail`, `ValidCons`, `DropStep`, `{:induction false} ToNatBound`, the last **plus** `decreases |s|`), followed by the spike L2 definitions `Canonical`, `Normalize`, `FromNat`, `AddLimb` (spike L2 lines 9–36, which already state their measures). Everything else of the spike L2 (`NormalizeToNat`, `NormalizeCanonical`, `NormalizeIdempotent`, `FromNatCorrect`, `FromNatCanonical`, `AddLimbCorrect`, `NormalizeLoop`) is **not** in L2. Reference gate of exactly this text (`r2/d/l12.dfy`): verified, 22 tasks.

**Verus L1** = `Solutions/spikes/verus/qg_bignat_l1/src/lib.rs` as is (comments rewritten as given-file headers, spec §3.12; `decreases s.len()` is already on both recursive declarations). **Verus L2** = only `limb_at` and `lemma_add_limb_lift` from the spike L2 (lines 9–56 minus `lemma_seq_to_nat_drop_last_zero`). `normalize`, `from_u64`, `add_limb` and `lemma_seq_to_nat_drop_last_zero` go to the Q02/Q03 twins and later to L3.

No given crate has an `external_body`, an `assume` or an `admit`, so `expected/verus_trust.toml` stays absent (Δ95). Dafny L1/L2 contain no `{:axiom}` and no abstract module; `vaudit --mode given` must report 0.

**Leak checks on the layers (corrected).**
- Every recursive declaration of L1 and L2 states its `decreases`, in both languages, so no given declaration shows recursion verifying without one (Q01.P7dv). No layer holds a loop (Q02.P4dv).
- No layer evaluates `ToNat` / `seq_to_nat` of a non-empty literal (Q01.P3d, P4v, P5d, P6v). Residual hint, accepted: the worked lemmas' base cases need explicit steps (Dafny `assert s + [0] == [0];`; Verus `assert(seq_to_nat(Seq::<u64>::empty()) == 0);`), which suggests that evaluation is not automatic. Δ51 and design §10.1 fix L1's content; because Verus L1 shows the empty-sequence step, P4v has no empty-sequence label.
- L1's base-case steps reappear inside longer answers (Q02.X3v, Q03.H2v, Q03.H3v): a technique the worked lemma teaches, never an item's whole answer (QPLAN §1.1 rule 3, §1.6 step 3). The first pass's Q01.X3v was exactly those two lines and is replaced.
- `limb_at`'s docstring says "reading past the end as 0"; Q03.P10v asks about index −1 and an in-range index, so the definition, not the docstring, answers it.

**L3 re-supply list (forward, DV3a):** Dafny `ToNatDropLastZero`, `NormalizeToNat`, `NormalizeCanonical`, `NormalizeLoop`, `FromNatCorrect`, `FromNatCanonical`, `AddLimbToNat` + an `AddLimbValid` (together the spike's `AddLimbCorrect`); Verus `lemma_seq_to_nat_drop_last_zero`, `normalize`, `from_u64`, `add_limb`. The spike L4 and extras call `FromNatCorrect`, `from_u64`, `normalize` and `limb_at`, so at least those must be re-supplied by L3 or L4. See QPLAN F3 for the Q10 conflict.

**Unit options.** `dafny/options/core.toml` already carries the `Q03-Q18` override `manual-lemma-induction = true` (Δ45); Q01 and Q02 units have auto-induction. QPLAN no longer says either, because Q02.P3dv's D column is about the Q02 unit's behaviour.

## 2. Q01

### 2.1 Prediction answers

Vocabulary in every `D:<v> V:<v>` docstring: `ok` verifies; `fail` a verification error; `timeout` out of resource or time; `err:<stage>` refused before verification, with the stage `scripts/vcheck` prints (`parse`, `resolve`). Every Q01 verdict scenario ships as commented code in its docstring (*block*).

| item | answer (slot text, normalized) | evidence |
|---|---|---|
| P1dv | `D:fail V:fail` | `dp/p_q01_sub_exec.dfy`: `value does not satisfy the subset constraints of 'nat'` (verify stage); `vp/p_q01_sub_exec.rs`: `possible arithmetic underflow/overflow` |
| P2dv | `D:fail V:err:resolve` | `dp/p_q01_sub_spec.dfy`: the same subset-constraint error on the function body; `vp/p_q01_sub_spec.rs`: `mismatched types`, `stage resolve` (a Verus `nat - nat` is an `int`) |
| P3d | `FAILS none` | `dp/p_q01_literals.dfy`: all four literal asserts verify, five limbs included |
| P4v | `FAILS a b c d` | `vp/p_q01_literals.rs`: four `assertion failed`. The empty-sequence label [e] is dropped (Verus L1's worked lemma shows it) |
| P5d | `18446744073709551619` | `dp2/p_values.dfy` under `dafny.test`: `expect ToNat([3, 1]) == 18446744073709551619` PASSED |
| P6v | `55340232221128654849` | `r2/v/q.rs`: `assert(seq_to_nat(seq![1u64, 3u64]) == 55340232221128654849) by (compute_only)` verifies |
| P7dv | `D:ok V:err:resolve` | re-captured on the L1 text of QPLAN §1.2 with the worked lemma's `decreases` line removed: `r2/d/p7_nodec.dfy` verified (9 tasks); `r2/v/p7_nodec.rs`: `recursive function must have a decreases clause`, `stage resolve` |
| P8dv | `D:4 V:1` | `r2/d/x2d_weak.dfy` (one failing assertion): exit 4 from `dafny verify`; `r2/v/q_weak2.rs`: exit 1 from `verus`; `VERSIONS.md` §2.1 exit-code census (verification error → 4) and §2.2 (failing run, exit 1). The wrapper maps both to its own exit 1, the chapter's "doors" point |
| P9dv | `D:timeout V:fail` | `dp/p_q01_nonlinear.dfy` (`x * x * z < y * y * z`): `Verification out of resource`, vcheck verdict `inconclusive` (also corpus `G20`); `vp/p_q01_nonlinear.rs`: `postcondition not satisfied` |
| P10dv | `D:2 yes V:0 no` | `VERSIONS.md` §2.1 row D1 (bodyless lemma: W-D01, `verify` exit 2 with W-D04) and §2.2 row `admit()`, `assume(P)` (green normally, exit 0, no output about it) |
| P11dv | `D:ok V:ok` | `r2/d/p11.dfy` (`WeakMax(a: nat, b: nat) returns (m: nat)`, body `m := a + b`): verified; `vp/p_q01_weak.rs` (`weak_max` with `requires a <= 1000, b <= 1000`, body `a + b`): verifies. The prompt fixes `nat` for Dafny: over `int` the body fails `m >= a` for negative `b` |

**Leak checks (Q01).** No Q01 worked example, card demo or given declaration evaluates `ToNat` or `seq_to_nat` of a non-empty literal (P3d, P4v, P5d, P6v), omits a `decreases` (P7dv), subtracts naturals (P1dv, P2dv), shows a nonlinear goal (P9dv), shows a weak postcondition accepting a wrong body (P11dv), or shows a plain tool's exit code (P8dv, P10dv). The false-friends card C4dv has a `decreases` row whose demo pair is P7dv's two behaviours: final section, demo files `card-c4dv-5-{d,v}`, outcome only in the sidecar. The chapter's reveal of X6d gives only the letter, never the failing variants' messages: Q02.P7dv asks for the stage of exactly that rejection.

### 2.2 Holes: references, levers, gate results

| item | reference body | lever | gate |
|---|---|---|---|
| H1d `Max2` | `if a >= b { m := a; } else { m := b; }` | none | max-auto and seeds 1–3: failed (the hole passes) |
| H1v `max2` | `if a >= b { a } else { b }` | none | TRIV failed on the reference (non-vacuous); E0 on the shipped form fails on `unimplemented!()` by construction |
| H2d `ToNatAppendTwoZeros` | `assert s + [0, 0] == (s + [0]) + [0]; ToNatAppendZero(s + [0]); ToNatAppendZero(s);` | none | max-auto and seeds 1–3 failed |
| H2v `lemma_append_two_zeros` | `assert(s + seq![0u64, 0u64] =~= s.push(0).push(0)); lemma_seq_to_nat_push_zero(s.push(0)); lemma_seq_to_nat_push_zero(s);` | none | E0, E0H, NL `fails(error)`; E1 `fails(rlimit)`; BV `killed(harness)` |
| H3d `AllZeroToNat` | `if \|s\| > 0 { AllZeroToNat(s[1..]); }` | `{:induction false}` | **max-auto verified** (lever-needed); seeds 1–3 failed |
| H3v `lemma_all_zero` | `if s.len() > 0 { lemma_all_zero(s.drop_first()); }` | none | E0, E0H, E1, NL failed; BV killed |

All references verified together (`d/cand.dfy`: 40 verified; `v/cand.rs`: 18 verified).

### 2.3 Worked examples

- W1d / W1v: the L1 worked lemma's proof with an `assert` after every step, and its explicit `decreases`. Its asserts mention `ToNat` / `seq_to_nat` only of expressions built from `s` (the base case may restate L1's own two steps), never a non-empty literal limb list (P3d, P4v).
- W2d `LowLimb` / W2v `low_limb`: `d := s[0]` / `a.limbs[0]`. No `ToNat` literal (P3d, P4v), no subtraction (P1dv).

### 2.4 Exit answers and references

| item | answer or reference | evidence |
|---|---|---|
| X1v | `pub fn double(x: u64) -> (r: u64) requires x <= 1000, ensures r == 2 * x, { x * 2 }` (any precondition that keeps `2 * x` in `u64` and admits 21 passes) | `r2/v/q.rs` verified with the uncommented check; a weak `ensures r >= x` fails the check (`r2/v/q_weak2.rs`: `assertion failed`); no `requires` fails (`r2/v/q_noreq.rs`: `possible arithmetic underflow/overflow`) |
| X2d | `method Swap(a: nat, b: nat) returns (x: nat, y: nat) ensures x == b && y == a { x, y := b, a; }` | `r2/d/x2d_ref.dfy` verified with the check; `ensures x + y == a + b` fails it (`r2/d/x2d_weak.dfy`: `assertion might not hold`) |
| X3v | `assert(s + seq![0u64] =~= s.push(0)); lemma_seq_to_nat_push_zero(s);` | `r2/v/q.rs` verified; gate E0, E0H, E1, NL `fails(error)`, BV `killed(harness)` |
| X4d | `if n > 0 { assert seq(n, i => 0)[1..] == seq(n - 1, i => 0); ZerosToNat(n - 1); }` | `r2/d/x4d_ref.dfy` verified; without the assert it fails (`r2/d/x4d_noassert.dfy`: postcondition); gate (`r2/d/x4d_eb.dfy`): max-auto and seeds 1–3 failed. Its shape parallels L1's recursive case (a slice equality, then the recursive call): the S4 skill on a new goal; no layer holds this proof |
| X5dv | **re-posed in the DV2a fix round (§2.8)**: if `Q01_Map.dfy` imported L1 with `import QG_L1_BigNat` (no `opened`) and `exit.rs` had no `use qg_bignat_l1::*;` line, how would each file write the layer's value function applied to `s`? Options a) `ToNat(s)` and `seq_to_nat(s)`, as the files write it now b) `QG_L1_BigNat::ToNat(s)` and `qg_bignat_l1.seq_to_nat(s)` c) `QG_L1_BigNat.ToNat(s)` and `qg_bignat_l1.seq_to_nat(s)` d) `QG_L1_BigNat.ToNat(s)` and `qg_bignat_l1::seq_to_nat(s)`. Answer `d` | §2.8 (six probes through `scripts/vcheck --module Q01`). The first build's item ("the two keywords, then the prelude path", answer `import opened vstd::prelude`) was answerable from the exit files' own import lines |
| X6d | the method in the block: `method ZeroFirst(a: array<nat>)` / `ensures a.Length > 0 ==> a[0] == 0` / `{ if a.Length > 0 { a[0] := 0; } }`; options a) `requires a.Length > 0` b) `modifies a` c) `reads a` d) `ensures a.Length >= 0`. Answer `b` | `r2/d/x6_b.dfy` verifies; `x6_a.dfy`, `x6_d.dfy`: `assignment might update an array element not in the enclosing context's modifies clause`; `x6_c.dfy`: `reads clauses on methods are forbidden without the command-line flag --reads-clauses-on-methods`, stage resolve |
| X7v | `pub open spec fn sq(x: int) -> int { x * x }` and `pub fn sq3() -> (r: u64) ensures r == sq(3) { 9 }` | `r2/v/q.rs` verified with both checks; `sq` as `x + x` with `sq3` returning 6 fails the check (`r2/v/q_weak2.rs`) |
| X8dv | options a) `x > 5` b) `x > 4` c) `x > 6` d) `x + 5 > 1`, program `x := x + 1`, post `x > 5`. Answer `b` | arithmetic |
| X9dv | `--gate 0` | `scripts/vcheck` (Δ101 exit map) |
| X10dv | options a) Z3 b) the Dafny-to-Boogie translation c) the body of a lemma it verified d) the Python compiler, if you run the code. Answer `c` | — |
| X11dv | options a) faster runs b) the same verdict on every run and machine c) more proofs succeed d) no out-of-resource results. Answer `b` | Δ56, Δ59 |
| X12d | `2` | `VERSIONS.md` §2.1 row D12: one warning per `ensures` clause; Δ5 |
| X13v | options for `fn f(a: u64) -> (r: u64)` with the wrong body `0`: a) `r >= 0` b) `r > a` c) `r == a + 1` d) `r >= a`. Answer `a` | — |

The multiple-choice texts are fixed here so the answer hashes are stable; the exit lane copies the option lists verbatim. Shipped hole counts: `Q01_Map.dfy` 1 (X4d), `exit.rs` 1 (X3v). Verus prompt-as-heading headings are `//` comments.

### 2.5 Agent files (planted errors)

Four bugs per file, each in its own declaration, one diagnostic each, all reported by the verifier (one stage per file, so no bug masks another: the reason, kept here because it is Q03.P6dv's lesson). None is a nat subtraction or exec overflow (P1dv), a literal `ToNat` assert (P3d/P4v), a missing `decreases` (P7dv) or a nonlinear goal (P9dv). Avoid R01's midpoint (disjointness).

| bug | Dafny `Q01_AgentRepair.dfy` | fix | Verus `agent.rs` | fix |
|---|---|---|---|---|
| 1 postcondition | `method Succ(x: nat) returns (y: nat) ensures y == x + 1 { y := x + 2; }` | `y := x + 1;` | `fn succ(x: u64) -> (y: u64) requires x < 100 ensures y == x + 1 { x + 2 }` | `x + 1` |
| 2 index | `method Last(s: seq<nat>) returns (d: nat) requires \|s\| > 0 ensures d == s[\|s\| - 1] { d := s[\|s\|]; }` | `s[\|s\| - 1]` | `fn last(v: &Vec<u64>) -> (d: u64) requires v.len() > 0 ensures d == v@[v.len() - 1] { v[v.len()] }` | `v[v.len() - 1]` |
| 3 call precondition | `lemma Pos(n: nat) requires n > 0 ensures n * 1 == n {}` and a method calling `Pos(0)` | `Pos(1)` | `proof fn pos(n: nat) requires n > 0 ensures n * 1 == n {}` and a proof fn calling `pos(0)` | `pos(1)` |
| 4 assertion | `method Check() { var x := 3; assert x * 2 == 7; }` | `== 6` | `proof fn check() { assert(3 * 2 == 7); }` | `== 6` |

Not yet captured: each file's exact four-error output (the agent lane captures it for the chapter, spec §3.11.1, and pins the clean audit after repair in `expected/Q01_AgentRepair.audit` and `expected/q01_hello_agent.audit`, both empty).

### 2.6 Cards: intended demos and leak checks

Each WRITE card has one success (in the exercise file) and one failure demo (a specimen, pinned by in-file `// EXPECT @<line> "<fragment>"`; the fragments are captured by the card lane, never written from memory). Each row is checked against every P item of Q01 and later modules.

| card | success | failure demo | checked against |
|---|---|---|---|
| C1d / C1v `ensures` | `method Inc(x: nat) returns (y: nat) ensures y == x + 1 { y := x + 1; }`; Verus `fn inc(x: u64) -> (y: u64) requires x < 100 ensures y == x + 1 { x + 1 }` | the same with the body `y := x;` / `x` (postcondition) | P11dv (a weak postcondition that passes): the demo's postcondition is strong and fails; P1dv: the Verus `requires` rules out overflow |
| C2d / C2v `assert` | linear facts after a step (`var y := x + 2; assert y > x;`) | a false linear assert (`assert 2 + 2 == 5;`) | P9dv (nonlinear): linear only; P3d/P4v: no `ToNat` literal |
| C3d / C3v lemma-call | a call whose `requires` holds, then a fact from its `ensures` | a call whose `requires` fails (Verus wording W-V26) | no prediction concerns call preconditions; agent bug 3 is the same class, and the agent run follows the predictions |
| C4dv false friends | six rows (1 `calc`, 2 `assert`, 3 `forall`, 4 `old`, 5 `decreases`, 6 `==>`), one D/V demo pair each: `card-c4dv-<r>-{d,v}` | row 5 shows P7dv's two behaviours (the plan; as built, row 5 shows clause order, §2.7, with the demos' function renamed in §2.8) | final section; neutral names; outcome only in `expected/specimens/Q01/card-c4dv-5-{d.dfy,v.rs}.specimen.expect` |
| C5dv–C10dv Rosetta | success columns only; C6dv's columns state their `decreases` (as built after the DV2a fix round: `ReverseLimbs` / `reverse_limbs`, §2.8); C9dv says nothing about what happens to ghost code at run time (Q03.P1dv); C10dv's spec fn states its `decreases` | — | P7dv, Q03.P1dv |

### 2.7 As built by the DV2a Q01 lane (2026-10-04)

Every answer below was re-captured on the real files (or, for the verdict scenarios, on probe files whose text is the scenario quoted in the item's docstring), through the course wrappers, one solver job at a time. Probes: `/tmp/dvl0-dv2a-q01/{p,ff,raw}/` (lane scratch, not archived). The answers are in `Solutions/slots/Q01.slots`; `expected/Q01.pins` was written from them by `pins.py --update --ref --module Q01`; `pins.py --ref --module Q01` passes 19 checks (15 verdict pins, P3d, P4v, P5d, P6v).

**Answers and evidence (as built).**

| item | answer | evidence on the pins |
|---|---|---|
| P1dv | `D:fail V:fail` | `vcheck --module Q01 p/p1d.dfy`: `value does not satisfy the subset constraints of 'nat'`; `p/p1v.rs`: `possible arithmetic underflow/overflow` |
| P2dv | `D:fail V:err:resolve` | the Verus scenario takes `nat` parameters (as the docstring shows): `mismatched types`, `stage resolve`; Dafny: the subset-constraint error on the function body |
| P7dv | `D:ok V:err:resolve` | copies of the real L1 files with only the worked lemma's `decreases` line removed: Dafny `verified — 9 verified`; Verus `recursive function must have a decreases clause`, `stage resolve` |
| P8dv | `D:4 V:1` | the exact commands `dafny verify p8d.dfy` and `verus p8v.rs --crate-type=lib`, run under `dvl.common.run_capped` with the pinned binaries (`raw/raw.py`): exit 4 (`assertion might not hold`), exit 1 (`assertion failed`) |
| P9dv | `D:timeout V:fail` | **scenario changed** from the plan probe's `x * x * z < y * y * z` (nat, `0 < z`), which on the pins fails quickly (`D:fail`), and from corpus G20's text (a learner-visible manifest pins G20's outcome): `ProductOrder(a, b, c: int) requires 0 < a < b && 1 < c ensures a * a * c < b * b * c`. Dafny `Verification out of resource` on seeds 1–3 (`vcheck --brittleness`: inconclusive ×3); Verus `postcondition not satisfied` on seeds 1–3. Nearby variants are brittle (`x * z * x < y * z * y` and `z * x * x < z * y * y` verify, `0 < z` fails quickly), so the docstring quotes the scenario exactly |
| P10dv | `D:2 yes V:0 no` | the exact commands, as P8dv: Dafny exit 2 with W-D01 and W-D04 in the output; Verus exit 0, output only `verification results:: 1 verified, 0 errors` |
| P11dv | `D:ok V:ok` | `p/p11d.dfy` verified; `p/p11v.rs` verified |
| P3d | `FAILS none` | the specimen as shipped (a Dafny specimen is verified alone, so it carries a verbatim copy of L1's `BASE` and `ToNat`): 6 verified, 0 errors; literals [a] `[7]`, [b] `[7, 2]`, [c] `[1, 0, 1]`, [d] `[0, 0, 0, 0, 1]` |
| P4v | `FAILS a b c d` | the specimen as shipped (Verus specimens get Q01's chain): four `assertion failed`, one per labelled line |
| P5d | `18446744073709551619` | `pins.py --ref` runs the twin check unit under `dafny test` |
| P6v | `55340232221128654849` | `pins.py --ref`; a wrong value fails at **stage resolve** with `expression simplifies to … which evaluates to false` (open tools issue below) |
| X5dv | `d` (re-posed in the DV2a fix round, §2.8; this lane's item asked for `import opened vstd::prelude`, which the exit files show in their own import lines) | §2.8 |
| X6d | `b` | `p/x6_{none,a,b,c,d}.dfy`: only b verifies; none, a, d: `assignment might update an array element not in the enclosing context's modifies clause`; c: `reads clauses on methods are forbidden without the command-line flag --reads-clauses-on-methods`, stage resolve |
| X8dv | `b` | `p/x8.dfy`: `(x + 1 > 5) <==> (x > 4)` verifies |
| X9dv | `--gate 0` | `scripts/vcheck` usage and exit map (Δ101) |
| X10dv | `c` | — (conceptual) |
| X11dv | `b` | Δ56, Δ59 |
| X12d | `2` | `p/x12.dfy` (one bodyless lemma, two `ensures`): `2 holes` |
| X13v | `a` | `p/x13v_req.rs` (`requires a < 100`, body `0`): only `ensures r >= 0` verifies; b, c, d `postcondition not satisfied` |

**Holes, references, gates (as built).** References as §2.2, with one statement change: **H3d ships `decreases |s|`** (the plan listed none). A given statement without a `decreases` while its Verus pair has one is the asymmetry §2.1's leak check forbids (P7dv). Empty-body gate (`firsttry.sh Q01 --empty-body --eb-modes E0,E0H,E1,E2,NL,TRIV --eb-seeds 1,2,3`): 8/8 holes pass (H1d, H2d, H3d, X4d at max-auto and seeds 1–3; H3d `lever-needed`, as planned; H1v, H2v, H3v, X3v every listed mode, 3 seeds). Then through `dvl.verus.empty_body` directly: EM (seed 1, as the gate runs it) fails on all four Verus holes (H1v, H3v `fails(error)`; H2v, X3v `fails(rlimit)`), and BV under a 150 s wall clock is `killed(harness)` on seeds 1–3 for H2v, H3v and X3v (counted as failing, Δ58). EC does not apply (no broadcast group before L3), nor INV (no shipped invariant). The learner docstrings of H3d and X4d no longer explain `{:induction false}` (that would hint at Q02.P3dv); the twins' explanations keep it. A full learner flow was simulated in a scratch course root (`/tmp/dvl0-dv2a-q01/sim*`): `firsttry --check` records all 11 reference predictions as passes; wrong answers record as fails except a wrong P6v (open tools issue); `--exit` with the twin bodies scores 13/13; `--report --strict` OK once the filled slots are enabled; `vcheck --gate Q01` and `vaudit Q01` clean; a weak X2d spec and an X1v with its check left commented both fail their blocks. Reference gates: Dafny unit twin 31 verified, Verus crate twin 16, check unit 10, Dafny exit twin 13, Verus exit twin 6, agent twins 15 / 6; every `vaudit --ref` 0 findings. Count pins: Dafny 31 (12 symbols), Verus 16 (11 symbols).

**Cards as built.** C3d's card lemma is `HeadOfNonEmpty(s) requires |s| > 0 ensures Head(s) == s[0]` (no `Valid`, no quantifier: Q02.P5d [a] asks about an empty-bodied lemma over `Valid`); C3v's is `lemma_wf_push(s, d) requires d != 0 ensures seq_wf(s.push(d))`. No card or worked example subtracts naturals, evaluates a non-empty literal `ToNat`, shows a nonlinear goal, omits a `decreases`, or shows an empty-bodied inductive lemma. Dafny demo specimens are self-contained (dvl.dafny verifies a `.dfy.specimen` alone; C3d's demo carries a copy of `Head`). WRITE demos' EXPECT pins: C1d `@8 "a postcondition could not be proved on this return path"`, C2d `@9 "assertion might not hold"`, C3d `@21 "a precondition for this call could not be proved"`, C1v `@13 "postcondition not satisfied"`, C2v `@14 "assertion failed"`, C3v `@19 "precondition not satisfied"`.

**C4dv rows as built** (each D side verifies; outcome pinned in `expected/specimens/Q01/card-c4dv-<r>-<d|v>.*.specimen.expect`):
1. `calc`: Dafny `calc { x + 0; x; }` (no relation, default `==`) verifies; Verus `calc! { (==) x + 0; {} x; }` with the prelude only: `cannot find macro calc in this scope`, stage parse (calc! is a vstd macro outside the prelude; Q04 brings it).
2. `assert`: an `assert` inside a Dafny `function` body verifies; in a Verus `spec fn` body: `expected pure mathematical expression`, stage resolve.
3. `forall`: `ensures forall x: int :: x + 1 > x` verifies in Dafny with a trigger **warning**; Verus: `Could not automatically infer triggers for this quantifier`, stage resolve.
4. `old`: Dafny `old(x)` on a value parameter verifies with the warning `Argument to 'old' does not dereference the mutable heap, so this use of 'old' has no effect`; Verus `old(x)` on a non-`&mut` parameter: `mismatched types`, stage resolve.
5. `decreases`: **changed from the plan** (which made row 5 P7dv's own scenario, so its sidecar would hold P7dv's answer in `expected/`): clause order. Dafny accepts `decreases` before `ensures` on a recursive lemma; Verus: `expected curly braces`, stage parse. Neither demo omits a `decreases`. The DV2a fix round replaced the demos' `SumLimbs` / `sum_limbs` (a Q02 agent delivery) with `ReverseLimbs` / `reverse_limbs` and a recursive length lemma; the outcome is unchanged (§2.8).
6. `==>`: Dafny `c := a ==> b;` in compiled code verifies; Verus `a ==> b` as an exec fn's result: `expression has mode spec, expected mode exec`, stage resolve.

**Agent files as built.** Dafny as §2.5; `scripts/vcheck <file>` exits 1 with 11 verified, 0 holes, 4 errors: `a postcondition could not be proved on this return path` (+ related), `index out of range`, `a precondition for this call could not be proved` (+ related), `assertion might not hold`. **Verus Bug 2 changed**: `v[v.len()]` gave two diagnostics (`precondition not satisfied` at the index, then `postcondition not satisfied`), and an out-of-range `Vec` index is reported as a failed precondition of the indexing call, the same message as Bug 3. Bug 2 is now `count_up(n)`, a counting loop whose step is `i = i * 1` (fix `i = i + 1;`): one diagnostic, `decreases not satisfied at end of loop`. `scripts/vcheck <file>` exits 1 with 2 verified, 0 holes, 4 errors: `postcondition not satisfied`, `decreases not satisfied at end of loop`, `precondition not satisfied`, `assertion failed` (`--gate` adds its own summary error). The repaired twins pass `vcheck --gate` printing only the summary line (15 / 6 verified), and `expected/Q01_AgentRepair.audit` and `expected/q01_hello_agent.audit` were written by `vaudit --write` from the repaired files laid at their learner paths in a scratch course root (0 findings each). No sidecar pins the agent files' RED output: a learner's repaired file would then fail `pins.py --ci`.

### 2.8 DV2a fix round (Q01 lane, 2026-10-04)

Captured in the authoring worktree through the course wrappers, one solver job at a time inside a 16 GB `systemd-run` scope (`DVL_SCRATCH=/tmp/dvl0-dv2afix-q01/dvl`); probes under `/tmp/dvl0-dv2afix-q01/p/`, the learner-flow simulation under `/tmp/dvl0-dv2afix-q01/sim/` (lane scratch, not archived).

- **C6dv's Rosetta example renamed.** `SumLimbs` / `sum_limbs` was, line for line, the delivery of one of Q02's spec-first agent definitions (Q02.A1d / A1v). C6dv now shows a recursive reversal, in the learner files and the twins: Dafny `function ReverseLimbs(s: seq<nat>): seq<nat> decreases |s|` with body `if |s| == 0 then [] else ReverseLimbs(s[1..]) + [s[0]]`; Verus `pub open spec fn reverse_limbs(s: Seq<u64>) -> Seq<u64> decreases s.len()` with body `Seq::empty()` / `reverse_limbs(s.drop_first()).push(s[0])`. A reversal is no hole, exit, test-out or agent definition of Q01–Q03 (Q02's agent files define `CountZeroLimbs`, `TopIndex`, `SumLimbs`), no layer declaration, and no planned target of a later module (no design document names one). The C4dv row-5 demos carried the same `SumLimbs` / `sum_limbs` and a push-zero lemma; they now carry `ReverseLimbs` / `reverse_limbs` and a recursive length lemma (`ReverseLimbsLength` / `lemma_reverse_limbs_len`), still with `decreases` before `ensures`: the Dafny side verifies (2 verified), the Verus side stops with `expected curly braces` at the `ensures` line, stage parse, as before.
- **X5dv re-posed** (strand S5, verdict, one letter of four, 1.25 min as before; the options are in §2.4). The first build asked for `import opened vstd::prelude`, which the exit files show in their own import lines. Evidence, each probe with Q01's chain (`scripts/vcheck --module Q01 <probe>`): Dafny `import QG_L1_BigNat` (no `opened`) with `QG_L1_BigNat.ToNat(s)` verified (10 verified); with `ToNat(s)`, `unresolved identifier: ToNat`, stage resolve; with `QG_L1_BigNat::ToNat(s)`, `rbrace expected`, stage parse. Verus with no `use qg_bignat_l1::*;`: `qg_bignat_l1::seq_to_nat(s)` verified (1 verified); `seq_to_nat(s)`, `cannot find function seq_to_nat in this scope`, stage resolve; `qg_bignat_l1.seq_to_nat(s)`, `expected value, found crate qg_bignat_l1`, stage resolve. Only d) holds in both languages. Outside `Solutions/`, no file writes a qualified L1 name (one tools-suite dictionary key, `QG_L1_BigNat.BASE`, is a symbol name), and the files open during the exit (the exit files and the spine) show only the `opened` / glob forms. The item touches no prediction (Q02.P10dv is about standard-library staging). In the simulation a wrong letter fails its pin (`pins.py Q01`: `✗ Q01.X5dv`), and the reference letter passes `firsttry --exit` (13/13).
- **P8dv and the card demos.** Every Verus C4dv demo stops with an error, so its sidecar recorded the raw exit code, which is P8dv's V answer. Every WRITE-card failure demo (C1–C3, both languages) fails verification, so a run of it shows P8dv's D or V answer through `vcheck --json` (`exit_code`), the run's raw output directory (`exit.txt`) and, for Verus, the gate's failure reason (`exit 1`). All twelve now carry `// after: Q01.P8dv` (the six C4dv Verus demos and the six WRITE failure demos): `vcheck` and `vaudit` refuse them until P8dv's first try is recorded (checked: `refused … waits for Q01.P8dv`; after a recorded `--check` in the simulation they run), and the six C4dv Verus sidecars are sealed (diagnostics only, the outcome hashed). The six Dafny C4dv demos verify and stay unsealed: their output answers no Q01 prediction. The WRITE demos' EXPECT lines moved down one line with the marker (C1d `@9`, C2d `@10`, C3d `@22`, C1v `@14`, C2v `@15`, C3v `@20`). The plain learner-loop output of the shipped files names no exit code; the open tool-level exposure is in the lane report.
- **Re-pins.** `pins.py --update --ref --module Q01`: 15 salted verdict pins (Δ117; X5dv's is new). `vcheck --ref --pin-counts Q01`: schema 2, units Dafny 31 (12 symbols, `ReverseLimbs` in place of `SumLimbs`) and Verus 16 (11 symbols), and 7 files as shipped: exercise 3 + 3 holes, check unit 0, exits 1 + 1, agent files `failed` with 0 holes and 4 errors each. `specfreeze --pin Q01`: 77 statements in 28 files; only the six renamed statements changed. `pins.py --update --module Q01`: 12 sidecars, the 6 Verus ones sealed.
- **Checks, all green** (after the edits and re-pins): `firsttry.sh Q01 --lint-hollow` OK (26 files); `firsttry.sh Q01 --report` (11 slots unfilled and unrecorded, 2 commented checks, nothing missing); `specfreeze --check Q01` 0 findings; `pins.py --ci --module Q01` 57 pins, 0 problems; `vcheck --shipped Q01` 7 files, 0 problems; `pins.py --ref --module Q01` 19 checks, 0 problems; `CI=true reference_lint.py --module Q01` 0 findings over 8 twins; `vcheck --ref` and `vaudit --ref` on all seven twins (units 31 / 16, check unit 10, exits 13 / 6, agents 15 / 6 verified, 0 holes, 0 findings); the learner loop `vcheck Q01` (27 verified with 3 holes; 3 holes in Verus); `vcheck --gate` and `vaudit` on the check unit as shipped (9 verified, 0 findings), and `vaudit --compare` on both agent files (match, 0 findings); in the simulation with every twin at its learner path, `vcheck --gate` and `vaudit` on all seven learner targets (31, 16, 10, 13, 6, 15, 6 verified; 0 findings), `firsttry --check` 11 ✓ with the salted pins, `firsttry --exit` 13/13; `firsttry.sh Q01 --empty-body` 8/8 holes pass (H3d `lever-needed`, as planned; 22 min with `BV` killed at the 120 s clock); `check_course_map.py` and `gen_units.py --check` OK.
- **Open (tools owner).** Any failing run of any file shows the raw tool exit code, which is P8dv's answer (Dafny 4 on a verification failure, Verus 1): `vcheck --json`'s `exit_code` (a Dafny WRITE demo in the simulation: `exit_code 4`), the run's raw directory (`exit.txt`, which `vcheck` prints the path of), and the Verus gate's failure reason (`…; exit 1`, seen on C2v's demo). Q01's demos now wait for P8dv, and the module's flow records every prediction before any run, so only a learner who runs a failing file of their own before recording P8dv sees it. Hiding the raw code in the learner context would close it.

### 2.9 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §2.2's exit table now names each Q01 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §2.2's exit table, as it stood:

**Exit (the map, one item per strand; closed book; 13 items; ≥ 10/13).** Five code items of at most three lines each, eight verdicts.

| id | strand | file | form | uses | need | prompt |
|---|---|---|---|---|---|---|
| Q01.X1v | S1 | `exit.rs` | prompt-as-heading, commented check `fn double_check() { let r = double(21); assert(r == 42); }` | ensures, requires | `fn double(x: u64) -> (r: u64)`; `let r = double(21); assert(r == 42);` | write `double`: a precondition that rules out overflow, a postcondition, the body; then uncomment the check |
| Q01.X2d | S2 | `Q01_Map.dfy` | prompt-as-heading, commented check `method SwapCheck() { var p, q := Swap(1, 2); assert p == 2 && q == 1; }` | ensures | `method Swap(a: nat, b: nat) returns (x: nat, y: nat)`; `var p, q := Swap(1, 2); assert p == 2 && q == 1;` | write `Swap` with a postcondition that lets the check verify; then uncomment the check |
| Q01.X3v | S3 | `exit.rs` | statement-shipped, `proof_note` assume | assert, lemma-call | `pub proof fn lemma_append_one_zero(s: Seq<u64>)`; `seq_to_nat(s + seq![0u64]) == seq_to_nat(s)` | prove it |
| Q01.X4d | S4 | `Q01_Map.dfy` | statement-shipped, bodyless lemma | assert, lemma-call | `lemma {:induction false} ZerosToNat(n: nat)`; `ensures ToNat(seq(n, i => 0)) == 0` | prove it by recursion on `n` (`decreases n` ships) |
| Q01.X5dv | S5 | `Q01_Map.dfy` | verdict | — | — | one letter of four: how the two exit files would write L1's value function applied to `s` if `Q01_Map.dfy` imported the layer without `opened` and `exit.rs` had no `use qg_bignat_l1::*;` line |
| Q01.X6d | S6 | `Q01_Map.dfy` | verdict | — | — | one letter of four: which single line, added to the header of the method quoted in the block, makes it verify |
| Q01.X7v | S7 | `exit.rs` | prompt-as-heading, commented checks `fn sq3_check() { let r = sq3(); assert(r == 9); }` and `proof fn sq_check() { assert(sq(4) == 16); }` | ghost, ensures | `spec fn sq(x: int) -> int`; `fn sq3() -> (r: u64)`; `let r = sq3(); assert(r == 9);`; `assert(sq(4) == 16);` | write a spec fn `sq` (the square) and an exec fn `sq3` whose postcondition states its result through `sq`; then uncomment the checks |
| Q01.X8dv | S8 | `Q01_Map.dfy` | verdict | — | — | one letter of four: the weakest precondition of an assignment for a given postcondition |
| Q01.X9dv | S9 | `Q01_Map.dfy` | verdict | — | — | the `scripts/vcheck` flag that runs the done gate, and the exit code that means verified. Answer form `<flag> <code>`, the flag with its leading dashes |
| Q01.X10dv | S10 | `Q01_Map.dfy` | verdict | — | — | one letter of four: which item a green Dafny run does not ask you to trust |
| Q01.X11dv | S11 | `Q01_Map.dfy` | verdict | — | — | one letter of four: what pinning a resource limit instead of a time limit buys |
| Q01.X12d | S12 | `Q01_Map.dfy` | verdict | — | — | how many tool-counted holes a bodyless lemma with two `ensures` clauses produces. Answer form: numeral |
| Q01.X13v | S13 | `exit.rs` | verdict | — | — | one letter of four: which postcondition also accepts a wrong body |

Other QPLAN lines that described a Q01 exit statement, as they stood (QPLAN now points here):

- §1.6, the table rows of Q01.X3v and Q01.X4d:

```text
| Q01.X3v | lemma, one appended zero limb as a sequence concatenation | no / not imported | none (L1's worked lemma is about `push`) |
| Q01.X4d | recursive lemma, the value of `n` zero limbs | no / not imported | none |
```

- §1.7 F2:

```text
- **F2.** Q01's holes and exit targets (`Max2`/`max2`, `ToNatAppendTwoZeros`/`lemma_append_two_zeros`, `AllZeroToNat`/`lemma_all_zero`, `ZerosToNat`, `lemma_append_one_zero`) are Q01-owned: never re-supplied, never re-posed, and no later learner-visible file contains their proofs.
```

## 3. Q02

### 3.1 Prediction answers

> **Superseded for Q02** by `Solutions/plans/Q02-author-notes.md` wherever the two differ (the obligation letters, P8dv's Dafny lemma, the card demos). Current obligation answers: P1d `FAILS a d` (DV2a fix round: the `decreases` clause moved before the invariants and labelled [b], so the answer is no longer the generic example `FAILS a c`), P2v `FAILS b e`, P5d and P6v `FAILS d`. The P1d and P2v rows below keep the plan lane's letters for the record.

Every Q02 verdict scenario ships as commented code in its docstring (*block*).

| item | answer | evidence |
|---|---|---|
| P1d | `FAILS b c`, with labels [a] the bound invariant `0 <= j <= a.Length`, [b] the one-short invariant `forall i \| 0 <= i < j - 1 :: a[i] == 0`, [c] the `ensures` | re-captured with the explicit `decreases a.Length - j` (`r2/d/p1d_dec.dfy`): `this invariant could not be proved to be maintained by the loop` on [b], and `a postcondition could not be proved on this return path` with its related location on the [c] line |
| P2v | `FAILS c d`, labels [a] `j <= v@.len()`, [b] `v@.len() == old(v)@.len()`, [c] the short `forall`, [d] the `forall` ensures | `vp2/p_q02_inv_short.rs`: `invariant not satisfied at end of loop body` on the short invariant, `postcondition not satisfied`. **Check the label set with `pins.py --ref`**: the probe's postcondition error was reported at the function's opening line, so the specimen must put [d] where `pins.py` maps a Verus postcondition failure, or use `proof_note` labels |
| P3dv | `D:ok D-off:fail V:fail` | `dp2/p_q02_count.dfy`: `CountId` verifies with `{}` under default auto-induction, the `{:induction false}` copy fails; `vp2/p_q02_count.rs`: `postcondition not satisfied` |
| P4dv | `D:ok V:err:resolve` | `dp2/loops_nodec.dfy`: four loops without `decreases` verify (guards `n > 0 && s[n-1] == 0`, `\|s\| < n`, `j < a.Length`, `\|s\| != n`); `vp2/p_q02_loop_nodec.rs`: `loop must have a decreases clause`, `stage resolve` (W-V13) |
| P5d | `FAILS d` | `dp2/p_q02_quant.dfy`: only the existential over sequences with no witness term fails |
| P6v | `FAILS d` | `vp2/p_q02_quant.rs`, `p_q02_quant2.rs`: [a]–[c] verify; the witness-free existential fails (`postcondition not satisfied`) |
| P7dv | `D:verify V:resolve` | `dp2/p_q02_frame.dfy` (and `r2/d/x6_a.dfy`): `assignment might update an array element not in the enclosing context's modifies clause`, a verification error (vcheck prints no stage); `vp2/p_q02_frame.rs`: `` cannot borrow `*v` as mutable, as it is behind a `&` reference ``, `stage resolve` |
| P8dv | `D:fail V:fail` | `dp2/p_q02_scope.dfy`: `assertion might not hold` on the second assert; `vp2/p_q02_scope.rs`: `assertion failed` |
| P9d | `2` | `dp2/p_values.dfy`: `expect \|Normalize([0, 5, 0, 0])\| == 2` PASSED |
| P10dv | `D:err:resolve V:ok` | `dp2/unit/` (a core-tier project, no `standard-libraries`): `module Std does not exist`, `stage resolve`; `vp2/p_q02_seqlib.rs` (`use vstd::seq_lib::*;`) verifies. A loose file outside a unit gets `standard-libraries` added by `dvl` and verifies, so the real capture must be in the real Q02 unit |

**Leak checks (Q02).** The prediction block precedes every W, C and H item. W1d/W1v (first zero) hold no one-short invariant, state an explicit `decreases`, use no `assert … by` and no existential. H5d/H6d carry `uses: decreases` and a method clause requiring an explicit `decreases`, the same as H5v/H6v; `NormalizeLoop` ships with its `decreases n`, like `normalize`; the P1d specimen's loop states its `decreases`; so no marker, given code or `uses:` tag is asymmetric between the languages (P4dv). Q01.X5dv no longer mentions the standard library (P10dv). P7dv now asks for the stage, because Q01.X6d settles whether the write is rejected. The two divergence cards' slugs (`q02-c6`, `q02-c7`) and demo names carry no topic; their demos are P7dv's and P3dv's scenarios. Hand before automation (design §6.3): Q01.H3d is a `{:induction false}` lemma by hand, before P3dv and C7dv.

Extra fact for the chapter (probe `dp2/unit/q.dfy`): Dafny proves `(s + [0])[1..] == s[1..] + [0]` with an empty body; the worked lemma's assert is needed as a trigger for the `ToNat` step, not because the equality is hard. Verus likewise proves `s.push(0).drop_first() == s.drop_first().push(0)` with an empty body (`vp2/p_q02_quant3.rs`).

### 3.2 Holes and test-out items

| item | reference | lever | gate |
|---|---|---|---|
| T1d `PadZeros` | `decreases k - \|s\|` then `if \|s\| >= k then s else PadZeros(s + [0], k)` | — (prompt-as-heading) | no hole. The shipped check `lemma PadZerosCheck() ensures PadZeros([7], 3) == [7, 0, 0] {}` verifies over the reference (`r2/d/q02.dfy`). Without the `decreases`: `cannot prove termination; try supplying a decreases clause` (`dp2/loops_nodec.dfy`), so the clause is enforced |
| T1v `pad_zeros` | `decreases k - s.len()` then the same shape | — | no hole; the shipped check `assert(pad_zeros(seq![7u64], 3) =~= seq![7u64, 0u64, 0u64]) by (compute_only)` verifies over the reference (`r2/v/q.rs`); a body pushing `1u64` fails it (`r2/v/q_weak.rs`: `expression simplifies to false`, stage resolve) |
| H1d `ToNatDropLastZero` | `var p := s[..\|s\| - 1]; assert ToNat(p + [0]) == ToNat(p) by { ToNatAppendZero(p); } assert p + [0] == s;` (`x3/h1d.dfy`) | none | the empty body failed at max-auto and seeds 1–3 (gated on the plain form of the same statement) |
| H1v `lemma_seq_to_nat_drop_last_zero` | `assert(seq_to_nat(s.drop_last().push(0)) == seq_to_nat(s.drop_last())) by { lemma_seq_to_nat_push_zero(s.drop_last()); } assert(s.drop_last().push(0) =~= s);` (`x3/h1v.rs`) | none | E0, E0H, E1, NL failed; BV killed |
| H2d `NormalizeLoop` | spike L2 lines 125–141: `assert s[..n] == s;` before the loop; invariants `0 <= n <= \|s\|`, `Normalize(s[..n]) == Normalize(s)`; `assert s[..n][..n - 1] == s[..n - 1];` in the body. `decreases n` ships | none | shipped form (code, `decreases n`, `assume false;` first) verified with 1 hole (`r2/d/q02.dfy`); the reference with the given `decreases` verified (same file). **Bare probe**: the shipped code with neither the hole line nor annotations fails (`r2/d/h2d_bare.dfy`: `a postcondition could not be proved on this return path`, `upper bound below lower bound or above length of sequence`). The whole-body gate would only show the method is not vacuous (QPLAN §6 Q6) |
| H2v `normalize` | invariant `a.to_nat() == old(a).to_nat()` (one clause; the `proof { lemma_seq_to_nat_drop_last_zero(a@); }` call and `decreases a.limbs.len()` ship) | none | reference verified (`r2/v/h2v_ref.rs`); shipped form verified with 1 hole labelled `Q02.H2v` (`r2/v/ship.rs`); gate on the shipped form E0, E0H, E1 `fails(error)` |
| H3d `NormalizeToNat` | spike L2 lines 43–48 | none | DV0: fails at max-auto |
| H4d `NormalizeCanonical` | spike L2 lines 58–60 | `{:induction false}` | DV0: max-auto verifies (lever-needed), as shipped fails 3/3 |
| H5d `Zeros` | `s := []; while \|s\| < n invariant \|s\| <= n invariant forall i \| 0 <= i < \|s\| :: s[i] == 0 decreases n - \|s\| { s := s + [0]; }` | none | failed at max-auto and seeds 1–3; with the explicit `decreases` verified (`r2/d/q02.dfy`). Method clause "a `while` loop with an explicit `decreases`": without it `s := seq(n, i => 0);` would close the item. Dafny infers the measure, so the clause is enforced by review, not by the verifier |
| H5v `zeros` | `Vec::new()`, loop with `k <= n`, `v@.len() == k`, the `forall`, `decreases n - k` | none | TRIV (`Vec::new()`) `fails(error)` |
| H6d `ClearFrom` | `var j := k; while j < a.Length invariant k <= j invariant forall i \| 0 <= i < a.Length :: a[i] == (if i < k \|\| i >= j then old(a[i]) else 0) decreases a.Length - j { a[j] := 0; j := j + 1; }` | none | failed at max-auto and seeds 1–3; verified with the `decreases` (`r2/d/q02.dfy`). Method clause as H5d (an aggregate `forall` statement would close it otherwise) |
| H6v `clear_from` | `let mut j = k; while j < v.len()` with `k <= j`, `v@.len() == old(v)@.len()`, the `forall` with `i < k \|\| i >= j`, `decreases v@.len() - j`, body `v.set(j, 0); j = j + 1;` | none | TRIV (`{}`) `fails(error)` |
| H7v `lemma_wf_value_pos` | `if s.len() > 1 { assert(s.drop_first().last() == s.last()); lemma_wf_value_pos(s.drop_first()); } else { assert(seq_to_nat(s.drop_first()) == 0); }` | none | E0, E0H, E1, NL failed; BV killed |
| H8v `lemma_push_zeros` | `if k == 0 { assert(s + Seq::new(k, \|i: int\| 0u64) =~= s); } else { let z = Seq::new((k - 1) as nat, \|i: int\| 0u64); lemma_push_zeros(s, (k - 1) as nat); assert(s + Seq::new(k, \|i: int\| 0u64) =~= (s + z).push(0)); lemma_seq_to_nat_push_zero(s + z); }` | none | E0, E0H, E1, NL failed; BV killed |

**Region markers (Δ98).** The twins mark exactly the learner-written regions with `// @hole-begin <id>` / `// @hole-end <id>`: Q02.H2d the pre-loop assert, the two invariants and the in-body assert (the spike already marks the same three regions); Q02.H2v the invariant clause; Q03.H1v the invariant clauses after `n == a@.len()`.

### 3.3 Exit answers and references

| item | reference | evidence |
|---|---|---|
| X1d | `function Upto(i: nat, n: nat): seq<nat> decreases n - i { if i >= n then [] else [i] + Upto(i + 1, n) }` | `r2/d/q02.dfy`: verified with `lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4] {}`; a body recursing on `Upto(i, n - 1)` fails the check (`r2/d/q02_weak.dfy`). The `decreases` is enforced (Dafny's default measure is the parameters, and `i` grows) |
| X2d | `method ZeroAt(a: array<nat>, i: nat) modifies a ensures forall j \| 0 <= j < a.Length :: a[j] == (if j == i then 0 else old(a[j])) { if i < a.Length { a[i] := 0; } }` (three lines) | `r2/d/q02.dfy`: verified with the check `method ZeroAtCheck() { var a := new nat[3](_ => 7); ZeroAt(a, 1); assert a[0] == 7 && a[1] == 0 && a[2] == 7; }`; `ensures i < a.Length ==> a[i] == 0` alone fails it (`r2/d/q02_weak.dfy`) |
| X3d | `var p := s[..\|s\| - 2]; assert ToNat(p + [0]) == ToNat(p) by { ToNatAppendZero(p); } assert ToNat(p + [0] + [0]) == ToNat(p + [0]) by { ToNatAppendZero(p + [0]); } assert s == p + [0] + [0];` | verified; gate failed at max-auto and seeds 1–3 |
| X1v | loop with `i <= v.len()`, `forall\|j: int\| 0 <= j < i ==> v@[j] != 0`, `decreases v.len() - i`, early `return false` | `r2/v/exec.rs` verified; TRIV (`false`) `fails(error)` |
| X2v | `let x = a.limbs[0]; a.limbs.set(0, x + 1);` with `requires old(a)@.len() > 0, old(a)@[0] < u64::MAX` | `r2/v/exec.rs` verified; TRIV (`{}`) `fails(error)` |
| X3v | `let s = seq![a, b]; assert(seq_to_nat(s.drop_first()) == b as nat) by { assert(s.drop_first() =~= seq![b]); assert(seq![b].drop_first() =~= Seq::<u64>::empty()); assert(seq_to_nat(Seq::<u64>::empty()) == 0); }` | verified; gate E0, E0H, E1, NL failed. Without the third inner assert it fails (`assertion failed`) |

Shipped hole counts: `Q02_Exit.dfy` 1 (X3d), `exit.rs` 3 (X1v, X2v, X3v).

### 3.4 Agent file: checks, domain, soft spots (spec-first; author-only)

Dafny functions with partial `ensures`; Verus `uninterp spec fn`s plus one bound lemma each. **Domain:** the prose contracts range over every limb sequence (any `seq<nat>` in Dafny, so a limb may be `BASE` or more; any `Seq<u64>` in Verus), so the Dafny `% BASE` soft spots are real contract violations.

**Shipped checks** (two per definition, none implied by the partial contract): count `[0, 5, 0]` → 2, `[7]` → 0; top index `[1, 0]` → 0, `[0, 7]` → 1; sum `[2, 3]` → 5, `[4]` → 4. Dafny: all six fail over the three bodyless functions (`r2/d/q02_agent.dfy`: six `assertion might not hold`, three `bodyless-function` holes). Verus: a `compute_only` check over an `uninterp spec fn` cannot simplify (`vp2/p_q02_agent_uninterp.rs`: `assert_by_compute_only failed to simplify down to true`), so all six fail by that mechanism; they were not re-run one by one. The first pass's `[]` checks were implied by the partial contracts and are gone.

| definition | partial formal contract | soft spot (a wrong body that passes every shipped check) | adversarial check the learner should find |
|---|---|---|---|
| zero-limb count | `<= \|s\|` | D: counts `s[i] % BASE == 0` (a limb equal to `BASE` counts as zero); V: counts zeros at even indices only | D: `[BASE]` → 0; V: `seq![5u64, 0u64]` → 1 |
| top non-zero index | `-1 <= r < \|s\|` | scanning down and stopping at index 0 returns 0 for `[0, 0]` | `[0, 0]` → −1; `[]` → −1 |
| limb sum | `\|s\| == 0 ==> r == 0` | D: sums `s[i] % BASE`; V: sums only the first two limbs | D: `[BASE, 1]` → `BASE + 1`; V: three limbs |

Verus shipping form: `pub uninterp spec fn count_zero_limbs(s: Seq<u64>) -> nat decreases s.len();` is accepted and counted as one hole (`vp2/p_uninterp_dec.rs`). With `open_bodies` applied, the filled `open spec fn` still hashes differently from the shipped form (`vp2/fz_ship.rs` vs `fz_open.rs`): QPLAN §6 Q7. The agent twin's reference section holds the reference definitions, the six shipped checks verbatim, these adversarial checks and this note. Q02's exit, holes and worked examples define none of the three functions.

### 3.5 Cards: intended demos and leak checks

| card | success | failure demo | checked against |
|---|---|---|---|
| C1d / C1v `assert … by` | `assert P by { L(); }`, then a later step that uses `P` | the by-block without the call: the asserted fact is not proved | P8dv: neither demo asserts `L`'s own postcondition after the block. QPLAN no longer calls the block "scoped" |
| C2d / C2v invariant | a loop whose invariant holds on entry and is maintained | an invariant false on entry (`invariant i == 1` with `i := 0`): the entry obligation fails | P1d / P2v: the demo fails on entry, not maintenance, and shows no postcondition failure |
| C3d / C3v `decreases` | a recursion with its measure | a recursion whose stated measure does not decrease (`decreases n` while recursing on `n + 1`) | P4dv: recursions with a stated measure only, never a loop, never an omitted clause |
| C4d / C4v quantified `ensures` | a `forall` postcondition established by a loop | a `forall` postcondition the body does not establish | P5d / P6v: no existential, no empty lemma body |
| C5d frame | a method with `modifies a` writing `a[i]`, postcondition with `old` | a caller asserts `a[1]` unchanged after calling a method that `modifies a` and says nothing about `a[1]` (`assertion might not hold`) | P7dv: no demo omits `modifies` or shows the frame error itself |
| C6v (divergence) | Dafny frames vs Verus `&` / `&mut`; demos `card-c6v-{d,v}` = P7dv's two rejections | — | final section of the Verus file; outcome only in the sidecars |
| C7dv (divergence) | empty-bodied lemmas; demos `card-c7dv-{d,v}` = P3dv's D and V columns | — | final section of the Dafny file; sidecars |
| C8dv `old` Rosetta | `old` in Dafny, `old` / `final` in Verus | — | none |
| C9dv `exists` Rosetta | an existential proved with an explicit witness step | — | P5d / P6v [c], [d]: the card always gives the witness explicitly and shows no empty body |

### 3.6 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §3.2's exit table now names each Q02 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §3.2's exit table, as it stood:

**Exit (closed book; 6 items; ≥ 5/6, 3 per language).**

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q02.X1d | S4 | decreases | `function Upto(i: nat, n: nat): seq<nat>`; `lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4]` | write the function returning `[i, i+1, …, n-1]` by recursion that counts `i` up; then uncomment the check `lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4] {}` | prompt-as-heading + commented check |
| Q02.X2d | S6 | frame, quantified-ensures | `method ZeroAt(a: array<nat>, i: nat)`; `ZeroAt(a, 1); assert a[0] == 7 && a[1] == 0 && a[2] == 7;` | write `ZeroAt`, which zeroes `a[i]` when `i < a.Length`, with what Dafny needs to accept the write and a postcondition that lets the check verify; then uncomment the check `method ZeroAtCheck() { var a := new nat[3](_ => 7); ZeroAt(a, 1); assert a[0] == 7 && a[1] == 0 && a[2] == 7; }` | prompt-as-heading + commented check |
| Q02.X3d | S3 | assert-by | `lemma ToNatDropTwoZeros(s: seq<nat>)`; `ensures ToNat(s[..\|s\| - 2]) == ToNat(s)` | prove it (requires: at least two limbs, the top two zero), one `assert … by` per dropped limb | statement-shipped, bodyless lemma |
| Q02.X1v | S4 | invariant, decreases, quantified-ensures | `pub fn all_nonzero(v: &Vec<u64>) -> (b: bool)`; `b == (forall\|i: int\| 0 <= i < v.len() ==> v@[i] != 0)` | implement it with a loop | statement-shipped, `external_body` hole |
| Q02.X2v | S6 | — | `pub fn bump_low(a: &mut BigNat)`; `final(a)@ == old(a)@.update(0, (old(a)@[0] + 1) as u64)` | implement it (requires: a non-empty limb vector whose low limb is below `u64::MAX`) | statement-shipped, `external_body` hole |
| Q02.X3v | S3 | assert-by | `pub proof fn lemma_two_limbs(a: u64, b: u64)`; `seq_to_nat(seq![a, b]) == a + BASE * b` | prove it with `assert … by` steps | statement-shipped, `proof_note` assume |

Other QPLAN lines that described a Q02 exit statement, as they stood (QPLAN now points here):

- §8.6 step 5 (it named two Q02 exit statements):

```text
5. **No layer holds the answer of a Q01–Q03 exit or test-out item.** Checked against §2.2–§4.2's exit and T rows: L3 states neither `ToNatDropTwoZeros` (Q02.X3d), nor `lemma_two_limbs` (Q02.X3v), nor any other exit or T target.
```

## 4. Q03

### 4.1 Prediction answers

| item | answer | scenario | evidence |
|---|---|---|---|
| P1dv | `D:8 V:8` | block | `dp2/p_q03_erased.dfy` under `dafny.test`: compiled with the `assume` warning, the test fails with `expectation violation` (the method returns 8); `vp2/p_q03_erased.rs` under `verus.test`: `left: 8`, `right: 7` |
| P2dv | `D:ok V:ok` | block | `VERSIONS.md` §2.1 row G12 (plain `verify` exits 0 on a contradictory `requires`) and §2.2 row V12 (verifies, `verified 1`) |
| P3d | `FAILS b d` | specimen | `dp2/p_q03_subset.dfy`: `value does not satisfy the subset constraints of 'Limb'` for `BASE` and for `x + y`; `BASE - 1` and `5 + 5` verify |
| P4v | `d` | block | `vp2/m_a.rs`, `m_b.rs`: `cannot call function … with mode exec` (`stage resolve`); `m_c.rs`: `The Verus types 'nat' and 'int' can only be used in ghost code …` (`stage parse`); `m_d.rs`: verifies. One crate per label, because the stages differ and an early stage masks the rest |
| P5dv | `D:0 V:2` | block | Δ4 (`dafny audit` always exits 0). **Re-posed in the DV2a fix round:** the first V half (whether a `--no-cheating --output-json` run with a hole carries `verified`; answer `absent`) was printed by every Verus learner-loop summary (`- verified`). The V half now asks for N in the `verification results:: N verified, E errors` line of a plain `verus <file> --crate-type=lib` run over three proof fns (honest, `assume(false)` body, `#[verifier::external_body]`): 2, since the assumed fn counts and the trusted one does not (real runs and controls in `Q03-code-notes.md` §2; `VERSIONS.md` §2.2 rows on `assume` and `external_body` agree). Strand S9 and the predicts minutes are unchanged |
| P6dv | `D:1 resolve V:1 resolve` | block | `dp2/p_q03_stage.dfy`: `RHS (of type int) not assignable to LHS (of type bool)`, `stage resolve`, the false assert not reported; `vp2/p_q03_stage.rs`: `mismatched types`, `stage resolve` |
| P7dv | `D:same V:same` | block | `dp2/p_q03_samemsg.dfy` (`{:induction false}` on each lemma, which Δ45 found equivalent to the Q03 unit's option; the real capture runs in the Q03 unit with no attribute): both lemmas `a postcondition could not be proved on this return path`; `vp2/p_q03_samemsg.rs`: both `postcondition not satisfied` |
| P8dv | `a`, options a) `x > 3` b) `x > 7` c) `x + 1 > 7` d) `x > 6` for `x := x * 2; y := x + 1` and post `y > 7` | block | arithmetic |
| P9d | `2` | check unit | `dp2/p_values.dfy`: `expect \|FromNat(18446744073709551616)\| == 2` PASSED |
| P10v | `8` | specimen | `r2/v/q.rs`: `assert(limb_at(seq![7u64, 8u64], -1) + limb_at(seq![7u64, 8u64], 1) == 8) by (compute_only)` verifies |
| P11d | `trusted audit` | specimen | delivery: a lemma whose helper's body is `assume {:axiom} …` (`x3/p11d.dfy`: `vcheck --gate` exit 0, `21 verified`; `scripts/vaudit`: 2 findings, `assume-axiom` from the lint and `audit-assume-axiom` from `dafny audit`) |
| P12d | `weak reader` | specimen | delivery: a correct, green lemma whose statement says nothing useful (`ToNat(s) >= 0`) |
| P13v | `hole gate` | specimen | delivery: a proof fn calling a `#[verifier::external_body]` helper (`x3/h1v.rs`: `scripts/vcheck` reports `hole external_body helper`; `--gate` fails). **Re-keyed** from `trusted gate`: by the species definitions (QPLAN §4.2, repeated in every specimen docstring) an `external_body` is the course's exec-hole form, which the hole counter reports |
| P14v | `healthy none` | specimen | decoy: a small correct proof fn unrelated to every hole and exit item (for example `2 * x > x` from `x > 0`) |

The four keys are four different species. Checked against the definitions: P11d's `assume {:axiom}` is silent in the gate and listed only by the audit (trusted); P13v's `external_body` is listed by `vcheck` itself (hole). DV2a fix round: every delivery carries exactly one `// planted: <item id>` marker (P11d on its `assume {:axiom}` line, P13v on its `external_body` attribute, P12d and P14v on their `ensures` line), and each specimen header says the marker is course bookkeeping present in every delivery, so its presence says nothing about the species. Only the shipping lints honour it; `vcheck` and `vaudit` still report both leaps. The P11d and P13v twins now exist.

**Leak checks (Q03).** The Dafny prediction block (P1dv, P2dv, P5dv, P6dv, P7dv, P8dv) and the Verus one (P4v) precede W1d/W1v and every card, so W1v's `proof { }` call (P4v [d]) and C5v come after P4v is recorded. W1v's mode triangle uses `succ_spec`, not `sq` (Q01.X7v) nor `twice_spec` (X3v). No delivery answers a hole (P13v's helper statement is not Q01.H2v's). The three divergence cards are in the final section under neutral slugs (`q03-c6`, `q03-c7`, `q03-c8`); their demos are P1dv's and P2dv's scenarios and a loud-versus-silent hole pair (C8dv; it bore on P5dv's first V half, which the DV2a fix round re-posed). DV2a fix round: the demos carry `// after:` lines (c6dv-d `Q03.P1dv`; c6dv-v `Q03.P1dv` and `Q03.P5dv`, since its plain test build counts an assume-bodied fn as verified; c7dv-d and c7dv-v `Q03.P2dv`; c8dv-d `Q01.P10dv`, since its diagnostics show the bodyless-lemma warning), so `vcheck`, `vaudit` and `vcheck --test` refuse them until those first tries are recorded, and their sidecars are sealed. c8dv-v (the `--no-cheating` record) settles no prediction and stays unsealed. The WRITE demo C3 (`card-c3d`, `card-c3v`) shows its in-file `EXPECT` message for a true lemma with an empty body, which bears on P7dv; it follows the prediction block, and an `after:` line cannot hide in-file text. The concept keys of P1dv, P2dv and P7dv are neutral (`S10.compiled-code`, `S13.spec-assumptions`, `S11.failure-messages`): the first-pass names stated what those predictions test.

### 4.2 Holes and test-out items

Unit options: the Q03 unit runs with `manual-lemma-induction = true` (the `core.toml` override).

| item | reference | lever | gate |
|---|---|---|---|
| T1d `MaxLimb` | loop with `ghost var w`, invariants `1 <= i <= \|s\| && 0 <= w < \|s\| && s[w] == m` and the prefix `forall` | none | failed at max-auto and seeds 1–3. The version without the ghost variable also verifies (`d/cand.dfy` `MaxLimbNoGhost`), so the ghost variable is a method clause, not a necessity; the chapter says so |
| T1v `max_limb` | the same with `let ghost mut w: int` and `proof { w = i as int; }` | none | TRIV (`0`) `fails(error)` |
| H1d `AddLimbToNat` | `if \|s\| == 0 { ToNatSingleton(d); } else if s[0] + d < BASE { ToNatCons(s[0] + d, s[1..]); } else { ValidTail(s); AddLimbToNat(s[1..], 1); ToNatCons(s[0] + d - BASE, AddLimb(s[1..], 1)); }` (9 lines; the validity half the spike's 12-line `AddLimbCorrect` also proved is left to L3) | unit `manual-lemma-induction` (the probe used `{:induction false}`, same verdict, Δ45) | **max-auto verified** (lever-needed); seeds 1–3 failed |
| H1v `add_limb` | spike L2 lines 177–188: `i <= n`, `res@.len() == i`, `c.len() == i + 1`, `c[0] == x`, `c[i as int] == carry`, `i > 0 ==> carry <= 1`, the `forall` per-limb relation (`n == a@.len()` ships) | none | shipped form verified with 1 hole labelled `Q03.H1v` (`r2/v/ship.rs`); with no invariant at all the body's index fails (`vp2/p_addlimb_ship.rs`), which is why `n == a@.len()` ships. Gate on the shipped form: INV `fails(error)`; E0, E0H, E1 `no-verify(cannot find value c in this scope)`, verdict `error`. The E0 variant (printed without a solver) strips `let ghost mut c` and the `proof { c = c.push(0); }` inside `if carry != 0`, but keeps the loop body's `proof { c = c.push(carry as nat); }` and the final `proof { lemma_add_limb_lift(a@, res@, c); }`; both kept blocks directly follow a closing `}` (an observation, not a diagnosis). Tools owner: QPLAN §6 Q9 |
| H2d `FromNatCorrect` | spike L2 lines 80–84 | unit `manual-lemma-induction` | **max-auto verified** (lever-needed); seeds 1–3 failed |
| H2v `from_u64` | spike L2 lines 153–161 | none | TRIV (`BigNat { limbs: Vec::new() }`) `fails(error)` (DV0 on the reference: E2 7.5 GiB, EM 14.0 GiB, both rlimit) |
| H3d `ExistsCanonicalFive` | `ToNatSingleton(5); assert Canonical([5]) && ToNat([5]) == 5;` | none | failed at max-auto and seeds 1–3 |
| H3v `lemma_exists_canonical_five` | `let w = seq![5u64]; assert(w.drop_first() =~= Seq::<u64>::empty()); assert(seq_to_nat(w.drop_first()) == 0); assert(seq_wf(w) && seq_to_nat(w) == 5);` | none | E0, E0H, E1, NL failed; BV killed |
| H4d `TryLimb` | `if x < BASE { r := Some(x); } else { r := None; }` | none | failed at max-auto and seeds 1–3 |
| H4v `try_limb` | `if x < 0x1_0000_0000_0000_0000u128 { Some(x as u64) } else { None }` | none | TRIV (`None`) `fails(error)` |

DV2a fix round: `firsttry --check` now records the first try of code T items, so both Q03 file headers (step 1) say to write T1 without its hints, run `scripts/firsttry.sh Q03 --check` and only then uncomment T1's checks; the learner simulation recorded T1d and T1v as `predict pass` (`Q03-code-notes.md` §7). The TRIV bodies above are now `// triv:` lines in the Verus twins' blocks (H1v, H2v, H4v, X1v, X3v), so `firsttry --empty-body` runs them itself.

### 4.3 Exit answers and references

| item | reference | evidence |
|---|---|---|
| X1d `FindAtLeast` | `found, w := false, 0; var i := 0; while i < \|s\| invariant 0 <= i <= \|s\| invariant forall j \| 0 <= j < i :: s[j] < b decreases \|s\| - i { if s[i] >= b { found, w := true, i; return; } i := i + 1; }` | `r2/d/q03.dfy` verified; gate (marker `Q03.X1d`): max-auto and seeds 1–3 failed |
| X1v `find_at_least` | loop with `i <= v.len()` and the prefix `forall`, `decreases v.len() - i`, `return (true, Ghost(i as int));` on a hit, `(false, Ghost(0))` at the end | `r2/v/exec.rs` verified; TRIV (`(false, Ghost(0))`) `fails(error)` |
| X2d | `type Odd = x: nat \| x % 2 == 1 witness 1` | `r2/d/q03.dfy` verified with the check; without the witness: `cannot find witness that shows type is inhabited (only tried 0)` (`r2/d/wit_odd.dfy`); a predicate admitting 0 fails the check (`r2/d/q03_weak.dfy`) |
| X2v | `assert(seq_wf(seq![0u64, 1u64]) && seq![0u64, 1u64].len() == 2);` | verified; gate E0, E0H, E1, NL failed |
| X3d | `if b <= a { r := Some(a - b); } else { r := None; }` against `ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)` | verified |
| X3v | `if x <= u64::MAX / 2 { Some(x * 2) } else { None }` | `r2/v/exec.rs` verified; TRIV (`None`) `fails(error)`. `twice_spec` must sit above the X3v marker: when it opened the block, the gate refused (the block's first fn was the spec fn) |

Shipped hole counts: `Q03_Exit.dfy` 2 (X1d, X3d), `exit.rs` 3 (X1v, X2v, X3v).

### 4.4 Cards and worked examples: intended demos and leak checks

| item | success | failure demo | checked against |
|---|---|---|---|
| W1d | `type NZDigit = x: nat \| 1 <= x <= 9 witness 1`, a function over it, a `ghost` helper | — | `r2/d/wit_nz.dfy`: without the witness, `cannot find witness … (only tried 0)`; with it, verifies. The first pass's `x < 10 witness 3` needed no witness (0 qualifies: `r2/d/wit_digit.dfy`, `wit_even.dfy` verify without one). No claim about ghost code at run time (P1dv) |
| W1v | the mode triangle with `succ_spec` | — | after the prediction block (P4v [d]) |
| C1d / C1v ghost | a ghost sequence that records the limbs a loop has summed | Dafny: a ghost variable used in compiled code; Verus: a `let ghost` value used in exec code | T1d / X1d (ghost witness indices): the card holds no witness index; P1dv: no claim about run time |
| C2d / C2v exec-check | `safe_div` returning `Option` after checking `b != 0` | the unchecked division (the divisor precondition fails) | H4 (limb range), X3 (checked subtraction, checked doubling): different operation |
| C3d / C3v witness | `exists i: nat :: i * i == 4` with the witness step; a subset type's `witness`; a lemma called on concrete arguments | the same existential with an empty body | H3d / H3v (canonical five), X2v (well-formed pair): different goals |
| C4d subset type | `type Small = x: nat \| x < 10` and `function Twice(x: Small): nat ensures Twice(x) < 20` | `type Pos = x: nat \| x > 0 witness 0` (a witness outside the predicate) | P3d (assignments into `Limb`): no demo assigns into a subset type |
| C5v modes | an exec fn whose `ensures` uses a spec fn, and a proof fn about that spec fn | an exec variable assigned inside a `proof { }` block | P4v: neither demo is one of [a]–[d] |
| C6dv, C7dv, C8dv (divergence) | demos `card-c6dv-{d,v}` (P1dv's scenario), `card-c7dv-{d,v}` (P2dv's), `card-c8dv-{d,v}` (loud vs silent holes; shows the `--no-cheating` record) | — | final section; neutral slugs and names; outcomes only in the sidecars, sealed by `// after:` lines where a demo settles a prediction (§4.1 leak checks) |
| C9dv trigger Rosetta | success columns | — | P7dv: no failing lemma |
| C10dv audit Rosetta | the audit commands and one finding line | — | P5dv: never an exit code, never a `verified` count |

### 4.5 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §4.2's exit table now names each Q03 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §4.2's exit table, as it stood:

**Exit (closed book; 6 items; ≥ 5/6).**

| id | strand | pair | uses | need | prompt | shipped |
|---|---|---|---|---|---|---|
| Q03.X1d | S7 | Q03.X1v | ghost, witness | `method FindAtLeast(s: seq<nat>, b: nat) returns (found: bool, ghost w: nat)`; its two `ensures` (`found ==> w < \|s\| && s[w] >= b`; `!found ==> forall j \| 0 <= j < \|s\| :: s[j] < b`) | implement it | statement-shipped, exec hole |
| Q03.X1v | S7 | Q03.X1d | ghost | `pub fn find_at_least(v: &Vec<u64>, b: u64) -> (r: (bool, Ghost<int>))`; its two `ensures` (the same, over `v@`, with `r.1@` the witness) | implement it | statement-shipped, `external_body` hole |
| Q03.X2d | S7 | — | subset-type, witness | `type Odd`; `method OddCheck(o: Odd) { assert o % 2 == 1; }` | declare the subset type `Odd` of the odd naturals, with whatever Dafny needs to accept it; then uncomment the check `method OddCheck(o: Odd) { assert o % 2 == 1; }` | prompt-as-heading + commented check |
| Q03.X2v | S13 | — | witness | `pub proof fn lemma_exists_wf_pair()`; `exists\|s: Seq<u64>\| seq_wf(s) && s.len() == 2` | prove it | statement-shipped, `proof_note` assume |
| Q03.X3d | S7 | Q03.X3v | exec-check | `method CheckedSub(a: nat, b: nat) returns (r: Opt<nat>)`; `ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)` | implement the checked subtraction (`Opt` is given in the exit file) | statement-shipped, exec hole |
| Q03.X3v | S7 | Q03.X3d | exec-check, modes | `pub fn checked_twice(x: u64) -> (r: Option<u64>)`; `r.is_some() <==> 2 * x <= u64::MAX`; `r.is_some() ==> r.unwrap() == twice_spec(x as int)` | implement it against the given spec fn | statement-shipped, `external_body` hole |

Other QPLAN lines that described a Q03 exit statement, as they stood (QPLAN now points here):

- §1.7 F4:

```text
- **F4.** Q02 and Q03 are one tier: neither module's files may hold the other's answers. Q03's given code (the `add_limb` loop body and ghost updates, the `Limb` subset type, the `Opt` datatype, the worked examples) answers no Q02 item, and Q02's given code (the `NormalizeLoop` and `normalize` loop code, the first-zero worked examples) answers no Q03 item. Q03.X1d / X1v search for a limb at least a bound and return a ghost witness; they share a linear-search shape with Q02.W1d / W1v, never their code.
```

- §4.1, the exit row of the files table:

```text
| exit | `dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy` (`module Q03_Exit`, holds the given `datatype Opt<T>`): 3 blocks, **2 shipped holes** (X1d, X3d). `verus/q/q03_first_syntax_ii/src/exit.rs` (holds the given `twice_spec` above the X3v block): 3 blocks, **3 shipped holes** (X1v, X2v, X3v) | green |
```

## 5. Minutes and calibration notes

- The design's "cards" line is read as the module's comparative (Rosetta, divergence, false-friends) cards; WRITE cards sit in "worked" (spec §2.5); the research card (`card` field) is in "paper".
- Q03's four diagnoses are P items budgeted on the "fake-green specimens" line, not on "predicts".
- Rates used: W 3–4.75 min (Q03's two W items at 3 min are below the 4–5.5 rate; the 26-minute line leaves 6 after the 20 minutes of WRITE cards), predictions 2.25–2.5, holes 4, Q01 map code items 3 (at most three lines each) and verdicts 1.25, intro exit items ≈ 4.2, test-out items 5.

## 6. Notes moved out of QPLAN (they described prediction answers)

- **Hand before automation** (design §6.3): Q01.H3d (`{:induction false}`, by hand) precedes Q02.P3dv and Q02.C7dv, which are about auto-induction.
- **One stage per agent file** (Δ14): every planted bug of an agent file is reported by the verifier, so no bug masks another; that masking is Q03.P6dv's lesson.
- **Library staging**: a Q02 core unit has no `standard-libraries`; whether an `import opened Std…` resolves there is Q02.P10dv's D column.
- **Exec holes compile** under `--allow-warnings` (Δ2, Δ98); compiled code with an assumption runs (Q03.P1dv).

## 7. The critique and what was done

All 2 blockers and 12 majors were applied; the minors were applied too. Where a fix departs from the critique's suggestion, the reason is given.

| # | finding | done |
|---|---|---|
| B1 | Dafny L1 omits `decreases` and answers Q01.P7dv | applied: explicit `decreases` on `ToNat`, `Pow`, `ToNatAppendZero`, `ToNatBound` and W1d; QPLAN §1.2–§1.3 list them; layer gate re-run (22 tasks); P7dv re-captured on the specified layer text (§2.1). **Partial**: the real layer files do not exist yet, so `pins.py --ref` on them is the spine lane's |
| B2 | QPLAN leaks Q02/Q03 answers | applied: the §1.4, §2.3, §2.4 and §0 remarks and the §5 row are gone (moved to §6 here); the README rule is adopted verbatim; the induction-setting notes are out of QPLAN; QPLAN §6 Q12 asks the integration lane to neutralise `dafny/options/core.toml` (not this lane's file) |
| M3 | `need:` on T items | applied: no `need:` on T items; coverage re-run on stubs generated from the revised tables (slugs as listed) |
| M4 | exit `need:` lines quote answers; three-line limit; Q01 map minutes | applied: `need:` quotes only declarations and shipped checks; spec-writing items ship a commented use-site check (QPLAN §0); body items are statement-shipped; Q01's map has five code items of at most three lines and eight verdicts |
| M5 | Q01 exit needs `exists` and `frame` | applied by rewriting: X2d is `Swap` (ensures), X6d is a verdict, X4d is a recursive lemma (assert, lemma-call). `uses: function` is moot |
| M6 | WRITE demos and worked examples vs predictions | applied: §2.6, §3.5, §4.4 fix every demo with its checks. **Deviation**: C5d's failure is a caller-side frame failure, not the suggested missing `reads`: a missing `reads` is a frame error reported by the verifier, a hint for P7dv's re-targeted stage question |
| M7 | divergence demos record answers | applied: neutral slugs and demo names, outcomes in `.expect` sidecars, header line, every demo file listed; tool request for an H5-style refusal (QPLAN §6 Q10), built in the DV2a fix round: Q02's divergence demos carry `// after: Q02.P7dv` (C6v) and `// after: Q02.P3dv` (C7dv), `vcheck`/`vaudit`/`vcheck --test` refuse them until that first try is recorded, and their sidecars are sealed (the diagnostics stay visible, and for these demos they settle the prediction: `Q02-author-notes.md` §7). The alternative "move Q02's divergence demos into Q03" was not taken: the design places them in Q02, and naming, sidecars and ordering cover it |
| M8 | Q02 markers give P4dv away | applied: H5d/H6d method clause and `uses: decreases`; `NormalizeLoop` and the P1d specimen state their measures; the prediction block precedes the holes |
| M9 | Q01.X3v answered by the spine | applied: X3v replaced (`lemma_append_one_zero`); P4v's [e] dropped |
| M10 | Q01.X5dv answers Q02.P10dv; X6d settles P7dv | applied: X5dv asks `import opened` and the prelude path; P7dv asks the stage. The DV2a fix round re-posed X5dv again (§2.8: qualified names without `opened` or the glob `use`), because the exit files show the first build's answer in their import lines; the new item still names no standard library |
| M11 | Q03.P13v key | applied: re-keyed `hole gate`; species defined in QPLAN and in each specimen docstring; P11d re-checked |
| M12 | Q01.P11dv's D half not captured | applied: prompt fixes `nat`; captured (`r2/d/p11.dfy`) |
| M13 | gate evidence missing | applied: TRIV on every Verus exec hole; E0/E0H/E1 (and INV where it applies) on both Verus annotation holes as shipped; the Q02.H2d bare probe; QPLAN §0 promises only admission after the gate. Found a tool issue on Q03.H1v (QPLAN §6 Q9; fixed in the DV2a fix round, `Q03-code-notes.md` §7) |
| M14 | Q02 T items check nothing | applied: each T block ships a commented check, so the strict gate fails until the target is written; the first run stays the learner's note (QPLAN §0, §6 Q4). DV2a fix round: `firsttry --check` now records code T first tries, so Q02's T prompts and file headers say to record the try with `scripts/firsttry.sh Q02 --check` before uncommenting the check, and the CALIBRATION block's test-out line is gone (evidence in `Q02-author-notes.md` §2). **Partial** on "a second enforced Dafny `decreases`": H5d/H6d's clause is enforced by review (Dafny infers loop measures); the verifier-enforced Dafny uses are T1d (through its check) and X1d |
| m15 | stated hole counts | applied (Q03: 5 per file; Q02 exits D 1 / V 3; every exit file's count stated) |
| m16 | near-copy exits | applied: Q03.X1d / X1v search for a limb at least a bound with a ghost witness; the old `min_limb` is gone; F4 reworded |
| m17 | agent checks implied by the contracts | applied (§3.4) |
| m18 | P6v duplicates P5d; P10v answered by the docstring | applied: P6v uses `[1, 3]`; P10v uses index −1 and 1 |
| m19 | witness `0` | applied after probing: W1d and X2d use predicates 0 fails |
| m20 | H5d/H6d shortcuts | applied (method clause) |
| m21 | H2v vs the §0 form; H2d prompt | applied: H2v ships the proof call; H2d asks for the invariants and the assertions they need |
| m22 | nominal citations | applied (`# nominal:` comments) |
| m23 | agent bug 3 overlaps P1dv | applied: Verus bug 3 is a call precondition |
| m24 | Δ98 markers, Δ102 thresholds | applied: markers specified (§3.2); thresholds recorded as an open decision (QPLAN §6 Q11) |
| m25 | evidence labels | applied (§0, relabelled; stubs regenerated) |
| m26 | verdict spellings and scenario homes | applied: exact commands and token spellings; every verdict's scenario home is stated (*block* or *specimen*) |

Also changed without a finding: three Q03 concept keys renamed (§4.1), because their names stated what the predictions test.
