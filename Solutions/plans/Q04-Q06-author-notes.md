# Q04–Q06 author notes (DV3a item plan)

> **Author-only.** This file holds prediction answers, exit answers, reference proofs, gate results, the card demos' intended content and the planted failures and soft spots of the agent files. Never quote, paraphrase or link any of it from a learner-visible file (`QPLAN.md`, the registry, exercise, check, exit and agent files, specimens, `slots/`, `expected/`, chapters, banks, rubrics). The learner-visible plan is `QPLAN.md` §8–§11, with §5.1 (the Q04–Q06 checks) and §6 Q13–Q25 (the open questions); item ids here are the same.

Written 2026-10-05 by the DV3a plan lane and revised the same day by the revise lane after review (§7 lists each review finding and what became of it). Every tool result quoted below was captured on the pins through the course wrappers (`scripts/vcheck`, `scripts/vaudit`, `scripts/vcheck --test`, `scripts/specfreeze`, and the `dvl` library functions `dafny.empty_body` / `verus.empty_body` through a small driver), at the course limits (Dafny `--resource-limit 5000000`, Verus `--rlimit 2`), one solver job at a time, each started only with at least 24 GB available (`free -g`), under the `dvl` caps (Dafny 8G, Verus 16G). Three kinds of run went through `dvl.common.run_capped` directly with an 8 GB cap, because the wrapper refuses their flags by design: the mismatch lab's plain-binary runs (§2.6), Q06.P1dv's plain-binary runs (§4.1), and Q04.P7v's scenario, run through `dvl.verus.verify` with the job cap clamped to 8 GB (§2.1). Higher-limit runs used a per-declaration resource attribute (`{:resource_limit 50000000}`, `#[verifier::rlimit(20)]`), which `vcheck`'s learner loop runs and `vaudit` flags. Probe files are lane scratch, **not archived**: the plan lane's under `/tmp/dvl0-dv3a-plan/` and the revise lane's under `/tmp/dvl0-dv3a-revise/` (`root/` a scratch copy of the needed tree with the candidate files at their planned paths; `probe/`, `d/`, `agent/`, `lab/`, `freeze/` standalone probes; `py/` the drivers; `stub/` the marker-level check; raw outputs under `dvl/runs/`). **The candidate files and the decisive probes are reproduced in Appendices A and B**, so nothing below depends on the scratch trees surviving. **Every answer below is re-captured on the real files** by the lane that writes them (`scripts/pins.py --update --ref --module <ID>` for verdict hashes, `pins.py --ref` for specimen and value slots, `firsttry.sh <ID> --empty-body` for the gate). Where an answer rests on a `VERSIONS.md` row or a DELTAS entry instead of a probe, it is named.

**DV3a records lane, 2026-10-05.** The orchestrator decided QPLAN §6 Q13–Q25 (DELTAS Δ130–Δ135). QPLAN no longer carries any exit statement or prompt (Q25, Δ133): §2.8, §3.5 and §4.7 below hold Q04's, Q05's and Q06's exit tables as they stood in QPLAN, verbatim, with the other QPLAN lines that described an exit statement. The marks *Decided (Δ…)* below are this lane's.

## 0. What was and was not run

### 0.1 Verification of the candidates

All verified with 0 holes and 0 errors in the learner loop unless stated: L3 Dafny inside the Q04 std unit (30 tasks); L3 Verus crate (11); Q04 core file (T1d, H1d, H2d, X1d filled), Q04 library file (H3d, H4d, X2d filled), Q04 check unit (`vcheck --test`: P2 PASSED); Q04 Verus crate split into `lib.rs` and `library.rs` (9 verified; the `--gate` run fails only on the scratch tree's missing count pin), Q04 `exit.rs` (`--gate`, 3), Q04 agent files (Dafny 35; Verus `--gate` 3, the replaced goals); Q05 std file (48), Q05 exit file (36), Q05 check unit (`--test`: PASSED), Q05 `lib.rs` (12), Q05 `exit.rs` (`--gate`, 3, with `transfer`); Q06 std unit (46; `--test`: 2 passed), Q06 Dafny exit file (`--gate`, 35), Q06 `lib.rs` (9; `--test`: 2 passed), Q06 `exit.rs` (`--gate`, 3), the Q06 Dafny agent twin (`--gate`, 35). The shipped forms checked: Q05.H1d, H2d, H4d, H5d (each green with one `assume` hole), Q04.H4v (green with one hole), the Q06 agent file as shipped (green, 1 hole) and with the reference skeleton (green, 3 holes).

### 0.2 Empty-body gate

`dvl.*.empty_body`; Dafny: the max-automation run plus seeds 1–3 as shipped; Verus: modes E0, E0H, E1, E2, EC, NL, BV (BV bounded at 120 s), INV for loops, TRIV for exec holes, seeds 1–3 unless stated. "pass" = the gate's verdict is that the hole fails as required. A Verus exec hole is gated on its **shipped** form (`firsttry` runs the learner file): on a reference with no proof spans the E-modes reproduce the reference, so only TRIV and INV are meaningful there.

| item | configuration | result | lane |
|---|---|---|---|
| Q04.T1d `ZeroValueZeroLimbs` | Dafny core | maxauto verified, seeds failed: **lever-needed** (manual induction, the unit's options) | plan |
| Q04.H1d `PowAdd`, H2d `PrefixBounds`, X1d `ToNatAppend` | Dafny core (the exit file has the same induction option) | maxauto failed, seeds failed: pass | plan |
| Q04.H3d `ShiftBound`, H4d `CmpCorrect`, X2d `PowsBelow` | Dafny std | each lever-needed (manual induction) | plan |
| Q04.T1v, H1v, H2v, H3v, H5v, X1v | Verus light modes seed 1 (H1v, H3v, H5v also seeds 2–3); E2 seeds 1–3 | all fail: pass. BV `no-verify` or `killed(harness)`, both counted as failing | plan; E2 revise |
| Q04.H4v `cmp` (restructured) | shipped form, E0, E0H, E1, E2, EC, INV, TRIV `{ Ordering::Equal }`, seeds 1–3 | all fail: pass. The plan's shape **shipped RED** (§2.2) | revise |
| Q04.X2v `fits_one_limb` | TRIV (default `false`) | fails: pass | plan |
| Q04 agent, Dafny | `ScaleStrict` lever-needed (nonlinear off is the module's own attribute); `HighLimbOfShift`, `ProductMod` maxauto inconclusive, seeds failed | admissible (the gate flags `empty-body-inconclusive` on the last two) | plan |
| Q04 agent, Verus (old goals) | `lemma_pow_split`, `lemma_pow_shift_down`: **E2 verifies 3/3** (the review was right); `lemma_pow_mod_base`: every mode fails | the two goals are replaced | revise |
| Q04 agent, Verus (new goals) | `lemma_pow_of_pow` (E0, E0H, E1, E2, NL fail; BV no-verify), `lemma_low_limb_of_power` (E0, E0H, E1, E2, NL fail); rejected: `lemma_div_both_ordered` and `lemma_div_twice` (NL verifies), `lemma_power_positive` (passes, but a one-call positivity fact) | pass | revise |
| Q05.H1d `Push`, H2d `Pop`, H4d `CountOnes`, H5d `ParseDecimal`, X2d `ParseTwo` | Dafny std, whole-body emptying | maxauto failed, seeds failed: pass. The new annotation and code forms are gated by the same whole-body emptying (QPLAN §6 Q18) | plan |
| Q05.H3d `CmpFast`, X1d `CountFull` | Dafny std | **gate verdict `error`** (the gate cannot empty a `by method` body, QPLAN §6 Q18). Bare probes instead: `CmpFast`'s by-method body without the annotations fails its postcondition; `CountFull` with an empty by-method body fails "a postcondition could not be proved on this return path" | plan |
| Q05.H1v, H2v (`{ Err(Full) }`), H4v (TRIV and INV), H5v (`{ Err(ParseError::Empty) }`), X2v (`{ Err(ParseError::Empty) }`) | Verus TRIV | all fail: pass | plan |
| Q05.X1v `transfer` | TRIV `{ Err(Short) }` | fails 3/3: pass | revise |
| Q06.T1d, H1d, H2d, H3d | Dafny std | maxauto failed, seeds failed: pass | plan |
| Q06.H4d `CheckSplit` (two-sided), X1d `FirstDisagreement` | Dafny std | maxauto failed, seeds failed: pass. `ok := false` fails the two-sided `CheckSplit` | revise |
| Q06.X2d `LowOfShift` | Dafny exit options | maxauto (opacity stripped) **inconclusive**, seeds failed: pass with `empty-body-inconclusive` | revise |
| Q06.T1v, H1v, H2v, H3v | Verus light modes; E2 seeds 1–3 | all fail: pass | plan; E2 revise |
| Q06.H4v `check_split_results` (two-sided), X1v `first_disagreement` | E0, E0H, E1, E2, EC, INV, TRIV (default `false`; X1v `{ None }`), seeds 1–3 | all fail: pass | revise |
| Q06.X2v `lemma_low_of_shift` | E0, E0H, E1, E2, EC, NL; BV `no-verify` | all fail: pass | revise |
| Q06 agent (Dafny): `PowMono`, `ToNatLowerBound`, `CanonicalLengthOrder` (the reference leaves), `CanonicalUnique` (the top lemma) | the agent file's options (std tier, manual induction) | the three leaves lever-needed (maxauto verified, seeds failed); the top lemma maxauto failed, seeds failed | revise |
| Python H5py–H7py | — | not gated (no Python adapter yet, QPLAN §6 Q19); §4.6's sketch shows the reference passes its checks | plan |

### 0.3 Not run

EM (the heavy `group_mul_properties` mode, Δ57: up to 14 GiB; this lane's share was 8 GB); the Verus `BV` mode beyond its bounded runs; a region-level gate for annotation holes (none exists); the mismatch lab's `--solver-path` run on a missing path (the guard refuses it in a Claude session, §2.6); `scripts/ci.sh` (no real module files exist yet). The module lanes run `firsttry.sh <ID> --empty-body` with every mode and seed on the real files.

### 0.4 Marker-level check

`/tmp/dvl0-dv3a-revise/stub/`: marker-only stubs of every revised Q04–Q06 item at the planned paths (Q04's `library.rs` included, the Q05 agent stubs carrying the planted wiring lines of §3.4, no Q06 Verus agent file), the L3 candidates, and the registry fields of QPLAN §9.7, §10.6 and §11.6 applied to a fresh copy of the worktree's `MODULES.toml`. `gen_units.py`: "13 unit(s); 7 file(s) written", then `--check`: "13 unit(s) and verus/Cargo.toml match the registry". `check_course_map.py`: "course map OK: 49 modules (33 Q, 16 R; 0 shipped, 6 authoring, 43 planned); imports: 48 files; coverage: 81 rows (193 pending)", and each group alone: `import-tiers: 48 files in 5 tiers, all within their allowlists`; `isolation: 48 Q file(s), 0 R file(s); no cross-track or reference reach, every declaration prefixed, …`; `coverage: 6 module(s) past planned (Q01, Q02, Q03, Q04, Q05, Q06)`. `--items` parses Q04 to 41 items (9 slots), Q05 to 37 (8) and Q06 to 39 (9). With `use vstd::calc;` in the stub `lib.rs`: `verus/q/q04_proof_craft/src/lib.rs:4: uses vstd::calc but its tier is prelude` (QPLAN §6 Q16).

## 1. Layer L3

**Candidates:** Appendix A.1 (Dafny) and A.2 (Verus). Both verified. Each holds exactly QPLAN §8.2–§8.3. Unchanged by the revision.

- **Design choices beyond DV0.** DV0's report lists `PowIsStdPow`, `PowMono`, `ToNatLowerBound`, `CanonicalLengthOrder` and the Verus bounds group and `lemma_lt_at` as hole *candidates* (homes "Q04", "Q04–Q06"). This plan gives `PowIsStdPow`, the three bounds lemmas with their group, and `lemma_lt_at` in L3, because Q04.H3d, H4v, X2d, X2v, P9v and Q06.H3d build on them; posing them would make those items depend on the learner's own versions (re-supply rule). `PowMono`, `ToNatLowerBound` and `CanonicalLengthOrder` are not in L3: they are the reference leaves of Q06's audited-prover skeleton (§4.5).
- **`Cmp`** recurses on `Tail`/`Head` with `decreases |a| + |b|`, so `Cmp([5, 1], [7, 0, 0])` compares the most significant limbs first through the recursion (P2d's answer is 1).
- **`weight`** is opaque; `lemma_weight_zero` and `lemma_weight_succ` reveal it inside their bodies only. `lemma_weight_mono` needs both triggers (`#[trigger] weight(m) <= #[trigger] weight(n)`); P9v [b] shows what happens without the group.
- **`add_limb`** (re-supplied Q03.H1v) uses the index step before the ghost push, as Q03's twin does.
- **F3** (QPLAN §8.5): `NormalizeLoop` is a method no layer calls, and Verus `normalize` is not needed by L4's known needs; keeping them out lets DV5 keep Q10's normalize invariant pair. `FromNatCorrect`/`from_u64` are needed by L4 (`NatLike`, the abstract spec), so they are in. `FromNatCanonical` was never posed (QPLAN §8.5).
- **§1.1 rule 3 and the leak patterns** (QPLAN §6 Q15). L3 holds the whole answers of Q02.H1d, H3d, H4d, Q03.H1d (value half plus validity), Q03.H2d, Q02.H1v, Q03.H1v (the whole `add_limb`, invariant included) and Q03.H2v. None is an exit or test-out answer: checked against QPLAN §2.2–§4.2 (Q02.X3d is two dropped zero limbs, Q02.X3v two limbs, Q03.X1d/X1v a ghost witness search; none is a single L3 lemma). The reviewer ran the leak-pattern verifier (`tests/instructor/leak_patterns/`) over the L3 candidates: the patterns of **Q02.H4d** and **Q03.H2d** match `QG_L3_BigNat.dfy`, and the pattern of **Q03.H1v** matches the Verus `lib.rs`; under the README's rule 2 (every given layer is public) the verifier would report `pub>0` once L3 lands. The patterns cannot be re-cut away from a verbatim proof. The decision (amend rule 3 and exempt the layers above a pattern's module) is the orchestrator's, before L3 is written; this lane cannot write DELTAS. *Decided (Δ130, 2026-10-05):* L3 keeps the proofs; rule 3 is amended, the leak patterns' rule 2 exempts a given layer of a tier above the pattern's module, and a leak check of an instructor session for module M applies only the patterns of modules at M's tier or higher. The README's verifier is re-run once it is amended (Δ130, Open).
- **Header text** (for the module lane): name the layer, "provided, complete", the importers (Q04–Q18), and the instruction not to open it before Q04 because it re-supplies earlier targets; nothing about tiers, `Std`, measures, induction attributes or broadcast mechanics (Δ110).

## 2. Q04

### 2.1 Prediction answers

| item | answer | evidence |
|---|---|---|
| P1dv | `D:ok V:fail` | `d/p/p1dv_d.dfy` verified (Dafny `nat` `%` and `/`); Verus (u128 sum, `as u64`, `>> 64`): postcondition not satisfied. The Verus probe file was not retained; the module lane re-captures |
| P2d | `1` | `dafny/checks/Q04_checks.dfy`, `vcheck --test`: PASSED with `== 1` |
| P3dv | `D:3 yes V:1 no` | Dafny: three errors, each at the step's target line, "the calculation step between the previous line and this line could not be proved"; Verus (`p5v_calc*.rs`): one error, "assertion failed", located in `calc_macro.rs:52` of the vstd source, not in the learner file |
| P4d | `FAILS a c` | `d/p/p4d_spec.dfy` (Appendix B.1): errors at the lines of [a] (`ToNat(s + [0])` to `ToNat(s)`: a fact, but a `calc` step gets no lemma call, so the hint-less step fails) and [c] (the index form multiplies the wrong term: `s[0] * BASE + …` is false); [b] and [d] hold |
| P5d | `FAILS b` | `d/p/p6d.dfy` (lemmas A, B, C, G of Appendix B.2), run as a standalone specimen (auto-induction on): `Pow(n) >= 1`, `ToNatBound`'s statement and the `AddLimb` length bound verify; `NormalizeToNat`'s statement fails |
| P6v | `a b` | `p7_empty.rs` fails; `p7_nl.rs` verifies; `p7_bv.rs` verifies; `p7_compute.rs` fails ("Failed to simplify") |
| P7v | `V:ok` | **re-posed and captured** (revise lane): `p7v_base3.rs` (`at_least_low_limb`, empty body) verified; `p7v_mul3.rs` (the same with `broadcast use vstd::arithmetic::mul::group_mul_properties;` as the body's only line) **verified**, 1 verified, in 3.7 s wall time for the whole run, under an 8 GB clamp of the job cap; a 1-second sampler never saw a z3 process (it lived under a second). The plan lane's answer `V:timeout` was never captured: it was carried over from Δ57, whose measured job (DV0 `spike-verus/run3/group-cost-mul`) was a different scenario, an **empty body that does not verify** (L2's `lemma_seq_to_nat_drop_last_zero`) with the group broadcast at module level (rlimit exceeded after 36 s, 7.1 GB maximum RSS). A second captured scenario agrees: `p7v_mul.rs` (`two_steps`, two `lemma_weight_succ` calls) verifies with the group in 3.7 s. The chapter quotes the DV0 record (a recorded quote) for the contrast after P7v's box: the group costs nothing while the goal is easy and floods the solver when it must search |
| P8dv | `D:err:resolve V:ok` | `d/p/p9dv_d.dfy`: "The name Pow ambiguously refers to a static member in one of the modules QG_L1_BigNat, Power" (resolve); Verus `p9dv_v.rs` (local `pow` beside `use vstd::arithmetic::power::*`): verified (the local item shadows the glob import) |
| P9v | `FAILS b` | `p9v.rs` (Appendix B.3): one error, at [b]'s `ensures` |

### 2.2 Holes, test-out items and exits: references and sizes

References: Appendix A.3 (core), A.4 (library), A.5 (check unit), A.6 (`lib.rs`, `library.rs`, `exit.rs`). Body lines (non-blank, non-comment) as measured on the candidates:

| item | strand | reference (summary) | lines |
|---|---|---|---|
| T1d | S4 | recursion on `s[1..]` with `ToNat(s) == 0` forcing `s[0] == 0` and `ToNat(s[1..]) == 0`; a `forall` statement with `assert s[i] == s[1..][i - 1]` | 10 |
| T1v | S4 | the same with `assert forall … by` | 8 |
| H1d | S4 (was S3) | `PowAdd(m - 1, n)` and a four-step `calc` | 13 |
| H1v | S5 (was S3; `library.rs`) | `lemma_weight_add(m - 1, n)`, `lemma_weight_succ`, a `calc!`; needs `lemma_mul_is_associative` (without it the chain fails) | 20 |
| H2d | S2 | `forall k | 0 <= k <= |s| ensures … { ToNatBound(s[..k]); }` | 5 |
| H2v | S2 | `assert forall … by { lemma_lt_at(a, b, i); }` | 5 |
| H3d | S5 | `PowIsStdPow(n)`, `(m)`, `(n + m)`; `Power.LemmaPowAdds(BASE, n, m)`; `Power.LemmaPowPositive(BASE, m)`; `Mul.LemmaMulStrictInequality(x, Pow(n), Pow(m))` (without the last call: out of resource) | 6 |
| H3v | S5 | `lemma_weight_add(n, m)`, `lemma_weight_zero()`, `lemma_weight_mono(0, m)`, `lemma_mul_strict_inequality` | 4 |
| H4d | S4 | `ValidTail(a)`, `ValidTail(b)`, the recursive call on the tails, `ToNatHeadTail(a)`, `(b)` | 7 |
| H4v | S5 (was S4) | region 1: `broadcast use group_bignat_bounds;` at the top of the body; region 2: the invariant clause `forall|j: int| i <= j < n ==> a@[j] == b@[j]` | 2 learner lines (≈ 40 lines of function, given) |
| H5v | S5 (was S1) | `lemma_weight_succ(n)` and one `nonlinear_arith` assertion with its `requires` | 7 |
| X1d | S4 | recursion on `a` with `ToNatCons` and a `calc` | 13 |
| X2d | S5 | `forall k | 0 <= k < n ensures Pow(k) < Pow(n) { PowIsStdPow(k); PowIsStdPow(n); Power.LemmaPowStrictlyIncreases(BASE, k, n); }` · lever: the exit file's manual induction (the empty body verifies under auto-induction) | 7 |
| X1v | S5 (was S1) | weight equations, then `calc!` whose **first** step is closed by `nonlinear_arith`, followed by two equalities (the prompt now says "one of whose steps") | 12 |
| X2v | S5 | `broadcast use group_bignat_bounds;`, `lemma_weight_zero()`, `lemma_weight_succ(0)`, body `a.limbs.len() <= 1` | 6 |

- **Q04.H4v restructured (a plan-lane defect the review missed).** The plan's `cmp` (early `return`s inside the loop, `lemma_lt_at` calls in the loop body, the whole invariant but `n == …` missing) ships **RED**: `h4v_ship.rs` (Appendix B.8) gives 5 errors, index preconditions in the loop body and postconditions at the early returns, because Verus checks a loop body (and a `return` inside it) from the loop's invariant alone; the labelled `assume(false)` before the loop does not reach it. The new shape (Appendix A.6, `library.rs`) scans down while the limbs agree (`while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]`, body `i = i - 1;`), then compares once after the loop with the `lemma_lt_at` calls there; the shipped form carries the labelled `assume(false)` as the **first statement** and the invariant clauses `i <= n`, `n == a@.len()`, `n == b@.len()`. Reference and shipped form both verify; the gate on the shipped form fails every mode. QPLAN §8.0's "Verus annotation-hole shape" row states the authoring rule.
- **Strands** follow design §7.3's usage rule (QPLAN §9.3): every Verus item that uses the library, a group or `nonlinear_arith` is S5 and lives in `library.rs` or the exit file; H1d moves to S4 because it uses lemma recursion (S4's card). `S4.loop-invariants@v` cites H4v with a `# nominal` comment.
- **Library staging.** `lib.rs` (S1–S4: T1v, H2v, W1v, the C1v–C3v cards, the prediction block) has no `vstd::arithmetic` import; `library.rs` (`mod library;` from `lib.rs`; C4v–C6v, H1v, H3v, H4v, H5v, C9dv) has `use vstd::arithmetic::mul::*` and its own `use qg_bignat_l3::*`. Both use `calc!`, so both are `all` until QPLAN §6 Q16 is built. The per-file shipped-state pins (`vcheck --shipped`) attribute each hole to its file, since `library.rs` is an exercise file of the crate's unit.
- **Rejected on the gate:** the first H2v (`prefix_bounds`, closed by EC: the group alone proves it) and a carry bound via `lemma_mul_upper_bound` (closed by NL, Δ49's pattern). **Hand before automation:** H1d precedes every `Std` call (core file, read first); in `library.rs`, H3v's `lemma_mul_strict_inequality` precedes H5v's `nonlinear_arith`, and the C5v and C6v cards show the hand form first (§2.3).

**Worked examples:** W1d `PowSucc` (`Pow(n + 1) == Pow(n) * BASE`: unfold, then commute) and W1v `lemma_weight_succ_comm` (the same from `lemma_weight_succ`) are short chains that answer nothing (L1's definition is `BASE * Pow(n - 1)`; L3's equation is `BASE * weight(n)`).

### 2.3 Cards: intended demos, `// after:` lines, leak constraints

- **C1d / C1v `write:calc`**: success = W1-style chain; failure demo = a chain with one false step. Dafny's demo shows the per-step error at the step line, Verus's shows the vstd-located error: both settle P3dv, so both carry `// after: Q04.P3dv`. No chain over `Pow(m + n)` or `ToNat(a + b)` (H1d, X1d).
- **C2d / C2v `write:forall`**: success = a `forall` statement / `assert forall … by` over limbs; failure = the same without the per-index call. **Must not** call `ToNatBound` (H2d) or `lemma_lt_at` (H2v) inside the `forall`, and must not quantify over prefixes or over a first difference. No prediction settled.
- **C3d / C3v `write:lemma-recursion`**: success = a recursive lemma on a smaller argument; failure = the call omitted under manual induction. The Dafny demo carries `{:induction false}` explicitly (a specimen runs with no unit options, so auto-induction is on otherwise) and states none of P5d's four lemmas. **Must not** take `ToNat` of a concatenation (X1d) or state a zero-value fact (T1d). It must not show a recursive *function* without `decreases` (that settles Q05.P2dv): keep every demo's `decreases` explicit.
- **C4d / C4v `write:library-call`**: success = one `Std.Arithmetic.Mul` / `vstd::arithmetic::mul` call; failure = the call's precondition unmet. Must not use `LemmaMulModNoop`, `LemmaFundamentalDivModConverse`, `LemmaMulStrictInequality`, `lemma_pow_multiplies`, `lemma_pow_mod_noop`, `lemma_pow_adds`, `lemma_pow1`, `lemma_mod_multiples_basic` (the agent goals' answers), `LemmaPowStrictlyIncreases` (X2d), `lemma_mul_strict_inequality` (H3v), or any `mod_multiples_vanish` lemma (Q06.X2).
- **C5v `write:broadcast-use`**: success = the same weight order first by named calls (`lemma_weight_zero`, `lemma_weight_mono(…)`), then by `broadcast use group_bignat_bounds;`; failure = the group-only version with the `broadcast use` line missing. Settles P9v [b]: `// after: Q04.P9v`. Not the one-limb test of X2v.
- **C6v `write:nonlinear-arith`**: success = a product bound first by a hand proof with one `vstd::arithmetic::mul` lemma, then by `assert … by (nonlinear_arith) requires …`; failure = the `nonlinear_arith` assertion without its `requires`. Settles P6v's [a]: `// after: Q04.P6v`. Not `x * d < weight(n + 1)` (H5v) and not a square of a limb (X1v).
- **C7d `recognise:induction-auto`**: comment-only (no demo), after the prediction block.
- **C8dv `diverge:q04-c8`** (false friends refreshed), rows: 1 `calc` (Dafny per-step errors vs Verus `calc!` reporting in vstd, `(==)` vs relation-first syntax) — `// after: Q04.P3dv`; 2 `forall` (Dafny `forall` statement vs Verus `assert forall … by`, and `implies`); 3 lemma recursion (Dafny's manual-induction unit vs Verus, which never inducts automatically; explicit `decreases` in both, see C3); 4 bringing in a library (`import opened` vs `use …::*` and the name clash) — `// after: Q04.P8dv`.
- **C9dv `diverge:q04-c9`**: library staging. Dafny: the library is a per-unit option (`standard-libraries`), so the core unit cannot see `Std` at all (a resolve error), and the std tier excludes `LittleEndianNat` by the checker only; Verus: `vstd` is always linked, and only the course checker enforces the tiers (here: `lib.rs` versus `library.rs`). No prediction settled (no `// after:`).

### 2.4 Exit answers

X1d, X2d, X1v, X2v: §2.2's rows. `need:` lines quote only the declaration and the `ensures`. X2v's twin declares `// triv: { false }` explicitly (the default) and the gate failed on it. X1v exit uses `calc!`, so `exit.rs` is `all` until QPLAN §6 Q16. **Unseen check:** X1d (append value) and H1d (power of a sum) share recursion and a `calc`, on different statements; X2d combines a `forall` statement with a library lemma used nowhere else in Q04; X1v shares the `nonlinear_arith` technique with H5v but is a `calc!` chain over a concrete two-limb bound (QPLAN §5.1 records it).

### 2.5 Agent files (retriever race)

Appendix A.7. Dafny goals and the one call each (unchanged): `ScaleStrict` (`Mul.LemmaMulStrictInequality(x, y, z)`), `HighLimbOfShift` (`DivMod.LemmaFundamentalDivModConverse(a * c + b, c, a, b)`), `ProductMod` (`DivMod.LemmaMulModNoop(x, y, m)`). Verus (revised): `lemma_pow_of_pow` (`lemma_pow_multiplies(BASE as int, n, 2)`), `lemma_low_limb_of_power` (`lemma_pow_mod_noop(x, e, BASE as int)`), `lemma_pow_mod_base` (`lemma_pow_adds(BASE, n - 1, 1)`, `lemma_pow1(BASE)`, `lemma_mod_multiples_basic(pow(BASE, n - 1), BASE)`).

- **E2.** The plan's `lemma_pow_split` and `lemma_pow_shift_down` verify under E2 (the light arithmetic groups include `group_pow_properties`, which broadcasts `lemma_pow_adds` and `lemma_pow1`), so they were not admissible and are replaced. `lemma_pow_multiplies` and `lemma_pow_mod_noop` are in no light group; both new goals fail every mode. Two division goals were tried and rejected: `nonlinear_arith` closes them.
- **Disjointness.** Two earlier goals were dropped because they overlapped Q04's exit X2d (`PowersOfBaseGrow`, and a non-strict `PowNondecreasing` whose library name sits next to X2d's), and the Verus `lemma_pow_grows` for the same reason; two more because their empty bodies verify (`LowLimbOfShift`, `PowStep`); `lemma_quotient` because NL closed it. `ScaleStrict`'s lemma is one of H3d's four calls (not a whole answer). No goal uses a `mod_multiples_vanish` lemma (Q06.X2).
- **Soft spots** a contractor tends to hit: an invented lemma name (`LemmaMulStrictlyIncreases`, `lemma_pow_positive_auto`), a non-library `assert … by` step, an extra helper lemma, `// found-by: memory` on every line. The `COMPARISON` block should catch each.
- **Audit pins** `expected/Q04_AgentRetriever.audit` and `expected/q04_proof_craft_agent.audit` are empty (no attribute, no assumption in a solved file).

### 2.6 The mismatch lab

**Correction.** The plan lane wrote that the guard refuses the first two Dafny runs in a Claude session. It does not: `spoiler-guard.sh` (rule 2g, `verifier_flags`) allows `--solver-path` naming either bundled Z3 (`z3-4.12.1` or `z3-4.14.1`) and refuses any other path, and it refuses `VERUS_Z3_PATH=`; it does not mention `RUSTUP_TOOLCHAIN`. `scripts/vcheck` refuses solver pass-through by design, so this lane ran the plain binaries through `dvl.common.run_capped` (8 GB cap), on a one-lemma file (`lab/one.dfy`) and a one-function file (`lab/one.rs`):

| run | exit | output |
|---|---|---|
| `dafny verify one.dfy` (the bundled default Z3) | 0 | `Dafny program verifier finished with 1 verified, 0 errors` |
| `dafny verify --solver-path …/z3/bin/z3-4.14.1 one.dfy` | 0 | the same line, nothing else |
| `verus one.rs --crate-type=lib`, `RUSTUP_TOOLCHAIN=1.98.1-x86_64-unknown-linux-gnu` | 0 | `verification results:: 1 verified, 0 errors` |
| `verus one.rs --crate-type=lib`, `RUSTUP_TOOLCHAIN=stable` (the host default, rustc 1.92.0) | 0 | the same line |

Recorded elsewhere: `VERSIONS.md` §1 rows "Bundled Z3 binaries", "Z3 that Dafny uses by default", "Dafny and a `z3` on PATH" (no Z3 at all: exit 4, "Z3 is not found"), "`verus --version`" (the `Toolchain:` line and its parenthetical), "Z3 version check" (`VERUS_Z3_PATH=<z3-4.14.1>`: panic, exit 134, "The verifier expects z3 version "4.16.0", found version "4.14.1""), "Rust toolchain required/installed" (1.98.1 vs the user default 1.92.0). **Not captured:** `--solver-path` to a missing path (the guard refuses it here); the chapter lane captures it in a plain terminal and quotes it as a recorded run (QPLAN §6 Q17). The `RUSTUP_TOOLCHAIN=stable` run is worth the chapter's attention: it exits 0, so the lab's lesson there is what the `Toolchain:` line reports, not a failure.

### 2.7 Leak checks (Q04)

- No Q04 learner-visible text names `LemmaMulStrictInequality`, `LemmaPowStrictlyIncreases`, `LemmaPowAdds`, `lemma_mul_strict_inequality`, `lemma_mul_is_associative` or the bounds-group name in a hole's block beyond what the item states (H4v's statement names "L3's bounds group", which is the item's own method clause).
- Q04.X1d (Dafny) and Q06.H3v (Verus) share a statement; no Q06 file holds X1d's proof (Q06's Dafny files hold no append lemma).
- P1dv's and P6v's scenarios are quoted commented in the prediction blocks; no live code in Q04 files splits a `u128` by `as u64` / `>> 64`. P7v's scenario (`at_least_low_limb`) is no item's statement.

### 2.8 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §9.2's exit table now names each Q04 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §9.2's exit table, as it stood:

**Exit (closed book; 4 items; ≥ 3/4 with ≥ 1/2 in each language).** Do not read this table before you sit Q04's exit (§8 banner).

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q04.X1d | S4 | calc, lemma-recursion | `lemma ToNatAppend(a: seq<nat>, b: seq<nat>)`; `ensures ToNat(a + b) == ToNat(a) + Pow(\|a\|) * ToNat(b)` | prove it by recursion on `a` (`decreases \|a\|` ships), with a `calc` chain in the recursive case | statement-shipped, bodyless lemma · the exit file's options |
| Q04.X2d | S5 | forall, library-call | `lemma PowsBelow(n: nat)`; `ensures forall k \| 0 <= k < n :: Pow(k) < Pow(n)` | prove it with one `forall` statement and the standard library (L3's bridge is open to you) | statement-shipped, bodyless lemma · the exit file's options (manual lemma induction) |
| Q04.X1v | S5 | calc, nonlinear-arith | `pub proof fn lemma_limb_square(x: u64)`; `(x as nat) * (x as nat) < weight(2)` | prove it with a `calc!` chain one of whose steps is closed by `nonlinear_arith` | statement-shipped, `proof_note` assume · none |
| Q04.X2v | S5 | broadcast-use | `pub fn fits_one_limb(a: &BigNat) -> (r: bool)`; `r == (a.to_nat() < BASE)` | implement it (requires `a.wf()`), with no loop | statement-shipped, `external_body` hole · none |

Other QPLAN lines that described a Q04 exit statement, as they stood (QPLAN now points here):

- §5.1, the "exits unseen" row:

```text
| exits unseen | no exit item shares its statement or its proof's structure with an H, T or W item of its own module | yes (X1v shares the `nonlinear_arith` technique with H5v, on another statement and shape) | yes | yes |
```

- §8.6, two rows of the table:

```text
| Q04.H5v, X1v | product bounds | no | none |
| Q04.X1d, X2d, X2v | the value of an append, the order of powers, a one-limb test | no | none |
```

- §8.7 F7:

```text
- **F7.** Q04, Q05 and Q06 are one tier: no module's files hold another's answers, and no Q04–Q06 given code (agent files included) answers a Q04–Q06 item. Shared techniques are intended (Q04's shifted-bound proof and Q06's budget items; Q04's `cmp` scan and Q05's `CmpFast` scan in the other language). One statement is shared across languages on purpose: the value of an append is Q04's Dafny exit item X1d and Q06's Verus budget item H3v; no Q06 file holds X1d's proof, and Q06.H3v is about the budget, not the induction.
```

### 2.9 As built (DV3a Q04 lane, 2026-10-05)

Q04's code is built: `Solutions/plans/Q04-code-notes.md` records every prediction answer as captured on the real scenarios (all nine equal §2.1's), the card demos and their outcomes, the gate results and the deviations from §2.2–§2.5 (C1v's failure demo, the two-step C1 chains, C5v's named calls, C9dv's demos, two extra `after:` lines, the check unit's dropped `Std` import, the exit headers). The references of §2.2 and Appendix A.3–A.7 are unchanged in code.

## 3. Q05

### 3.1 Prediction answers

| item | answer | evidence |
|---|---|---|
| P1dv | `D:fail V:ok` | `d/q05/p1dv_d.dfy`: "insufficient reads clause to read field" (stage verify, so `fail`); `p1dv_v.rs`: verified (a spec fn reads `self` freely) |
| P2dv | `D:ok V:fail` | **re-posed** (revise lane). Dafny half unchanged: `d/q05/p2dv_d2.dfy` (`G` with no `decreases`) verified, 23 tasks (Dafny's default `decreases m, n`). Verus half now carries `decreases m`: `p2dv_v2.rs`, `vcheck --json`: verdict `failed`, stage `verify`, exit 1, "could not prove termination" at the recursive call. The old Verus half (no clause, a resolve error) repeated Q01.P7dv's answer and message |
| P3dv | `D:no V:8` | `x/py3/p3dv_d-py/`: the generated class has `x` and no `Shadow`; `p3dv_v.rs` under `vcheck --test`: `size_of::<Tagged>() == 8` passed. The scenario now names a scratch directory (Δ32: the build writes `<stem>-py/` beside the source) |
| P4d | `FAILS b` | **re-probed** with `Push` declared by its contract only (`d/q05/p4d_bodyless.dfy`, Appendix B.6): `vcheck` reached verify, 11 verified, 1 hole (`bodyless-method P4.LimbStack.Push`), 4 errors, all at line 50, the `assert` of [b] (one per conjunct of `Valid()`). The old specimen held H1d's whole answer |
| P5v | `FAILS b` | **re-probed** with `maybe_push` declared `#[verifier::external_body]` over `unimplemented!()` on a renamed type `Bounded { items, limit }` with `Rejected` (`p5v.rs`, Appendix B.6): `vcheck --json`: verdict `failed`, stage `verify`, 1 hole (`external_body Bounded::maybe_push`), 1 error at line 46, the `assert` of [b] ("assertion failed"). The old specimen's body was H2v's answer |
| P6d | `FAILS d` | `d/q05/p6d.dfy` (Appendix B.4): the condition without the frame conjunct fails |
| P8d | `3` | `dafny/checks/Q05_checks.dfy`, `vcheck --test`: PASSED with `== 3` |
| P9dv | `b` | paper. Callee `method Bump(a: array<nat>, i: nat) requires i < a.Length modifies a ensures a[i] == old(a[i]) + 1 ensures forall j | 0 <= j < a.Length && j != i :: a[j] == old(a[j])`; caller: `requires a.Length == 2`, `Bump(a, 0); assert a[0] >= 1 && a[1] == old(a[1]);`. Options for the block: a) `0 < a.Length`; **b)** `0 < a.Length && forall a1 :: (a1[0] == a[0] + 1 && forall j | 0 <= j < 2 && j != 0 :: a1[j] == a[j]) ==> (a1[0] >= 1 && a1[1] == a[1])`; c) `0 < a.Length ==> a[0] + 1 >= 1 && a[1] == a[1]` (inlines the callee's body); d) `forall a1 :: a1[0] == a[0] + 1 ==> a1[0] >= 1 && a1[1] == a[1]` (drops the precondition and the frame) |

**P7v is removed.** It asked P6d's four logic-only conditions again over `Seq<u64>` with the same answer (`FAILS d`), so it gave no new first try; P6d and the `dv` item P9dv carry S8.

**Test-out answers.** T1d: `function Odometer(lo: nat, hi: nat): nat decreases hi, lo { if lo > 0 then 1 + Odometer(lo - 1, hi) else if hi > 0 then 1 + Odometer(9, hi - 1) else 0 }`; without the `decreases` Dafny's default order (`lo, hi`) is rejected (`d/q05/t1d_nodec.dfy`), with it `Odometer(2, 1) == 12` verifies (`t1d.dfy`). T1v: the same `spec fn` with `decreases hi, lo`; the `compute_only` check verifies (`t1v.rs`). With the prediction block first (QPLAN §8.0), T1 no longer comes before P2dv.

### 3.2 Holes and exits

References: Appendix A.8 (std file, with the shipped forms of H1d, H4d, H5d), A.9 (exit), A.10 (`lib.rs`), A.11 (`exit.rs`). Notes:

- **H1d `Push`** (now an annotation hole): the code is given; the learner region is the copy loop's `modifies b` and its two invariants `0 <= i <= n <= a.Length < b.Length` and `b[..i] == a[..i]` (3 lines). The loop frame is needed: without `modifies b` the reference fails (`PushRefNoFrame`, four errors at the postcondition), since the loop then may modify every object of `Repr`, and `a`'s contents are lost.
- **H2d `Pop`**: learner region = `modifies this` and `ensures Valid() && Repr == old(Repr)`. Without `Repr == old(Repr)` the shipped `PopCheck` fails (probed). Other frame clauses that let `PopCheck` verify are equally correct; only the reference form was probed. Region markers in the twin. The shipped form (`assume false;` first, no `modifies`) verifies with 1 hole (`freeze/ship.dfy`); `specfreeze --against` the shipped file reports `freeze-changed` on the twin's `Pop` (QPLAN §6 Q22).
- **H3d `CmpFast`**: pre-loop `assert Drop(a, i) == [] && Drop(b, i) == []` (with `i := max(|a|, |b|)`), invariants `0 <= i <= max` and `r == Cmp(Drop(a, i), Drop(b, i))`, `DropStep(a, i - 1)`, `DropStep(b, i - 1)` in the body, and after the loop `assert Drop(a, 0) == a && Drop(b, 0) == b` (≈ 8 learner lines).
- **H4d `CountOnes`** (now an annotation hole with the measure missing): the code is given, including the body's `assert s[i..][1..] == s[i + 1..]`; the learner region is `invariant 0 <= i <= |s|`, `invariant c + BitCount(x) + Ones(s[i..]) == Ones(s)` and `decreases |s| - i, x` (3 lines). The shipped form (`assume false;` first, no loop annotations) verifies with 1 hole.
- **H5d `ParseDecimal`** (now a code hole with given annotations): the loop header with its three invariants and the final `assert s[..|s|] == s; return Success(v);` are given; the learner writes `if |s| == 0 { return Failure("empty"); }` and the body `var d :- Digit(s[i]); assert s[..i + 1][..i] == s[..i]; v := v * 10 + d; i := i + 1;` (≈ 6 lines). The shipped form (empty loop body, `assume false;` first) verifies with 1 hole.
- **H1v `shift_up`**: when `a.limbs.len() > 0`, `a.limbs.insert(0, 0)` and `assert(a@.drop_first() =~= old(a)@)`; the zero `BigNat` (`[]`, canonical) is left alone, since `[0]` is not canonical (6 lines).
- **H2v `try_push`** (6), **H4v `count_ones`** (the lexicographic loop with `decreases v.len() - i, x`, 26 lines with code), **H5v `parse_decimal`** (25 lines: the overflow clause needs the witness prefix `k`).
- **Why H4v and H5v stay exec holes.** The Verus annotation form cannot ship here (probes `q05probe.rs`, Appendix B.9): a loop without a `decreases` is a resolve error ("loop must have a decreases clause"); with a partial `decreases v.len() - i` and a labelled `assume(false)` before the loop, Verus still checks the loop body from the (missing) invariant and reports an overflow at `c + x % 2` and "decreases not satisfied at end of loop"; an empty `parse_decimal` loop body fails its `decreases` the same way. QPLAN §8.0 states the shape rule; §10.5 gives each 10 minutes and marks them for the first calibration run.
- **X1d `CountFull`**: a reverse loop with `invariant c == CountFull(s[i..])` (`d/q05/x1d_ref.dfy`), 16 lines. **X2d `ParseTwo`**: `var x :- ParseField(s[..k]); var y :- ParseField(s[k..]); r := Success((x, y));` (3). **X1v `transfer`** (new, Appendix A.11): `if k <= from.bal && k <= to.cap - to.bal { from.bal = from.bal - k; to.bal = to.bal + k; Ok(()) } else { Err(Short) }` (8 lines; twin `// triv: { Err(Short) }`). **X2v `parse_pair`**: `let x = parse_digit(a)?; let y = parse_digit(b)?; Ok((x, y))` (3).
- **Unseen check.** X1v replaces `Meter::tick`, which was H2v's conditional-push shape on a counter. `transfer` takes two `&mut` parameters (not `self`), has two failure conditions and must leave both unchanged on `Err`; it shares no code with H1v, H2v or W1v (`Counter::reset`). X1d writes a whole by-method body (H3d annotates one); X2d's two `:-` steps over a given field parser and X2v's two `?` steps are straight-line, where H5d/H5v loop.

### 3.3 Cards

- **C1d `write:dynamic-frames`** failure demo: a function reading a field with no `reads` → settles P1dv's D half: `// after: Q05.P1dv`; a second failure (no disjointness) would settle P4d — keep it out, or mark `// after: Q05.P4d` too. The success must not grow an array (H1d) or pop (H2d).
- **C2d `write:by-method`**: success = a `by method` body for a **counter recursion over a `nat`** (for example the sum `0 + 1 + … + n` computed by an upward loop), never a fold over a sequence's suffix (X1d's shape `c == F(s[i..])`) and never over limbs; failure = the loop without its invariant. No prediction.
- **C3d / C3v `write:error-propagation`**: `:-` / `?` successes on a one-step helper; failure = a postcondition about the success value that the early return breaks. No loop over digits (H5d/H5v), and no two-field parse (X2d/X2v). No prediction.
- **C4d / C4v `write:lexicographic-decreases`**: failure demos = a recursion whose default (Dafny) or wrong single (Verus) measure is rejected → settle P2dv: both `// after: Q05.P2dv`. Neither demo is an odometer (T1) or a bit count (H4).
- **C5v `write:mut-ref`**: failure = a missing `final(self)` clause on an `Err` path → settles P5v [b]: `// after: Q05.P5v`. Not a stack push (H2v) and not a two-account move (X1v).
- **C6v `write:result`**: success/failure on a `Result` postcondition. No prediction.
- **C7dv `diverge:q05-c7`** (erasure): Dafny ghost fields absent from compiled code; Verus `Ghost<T>` zero-sized → settles P3dv: `// after: Q05.P3dv` on both demos, sealed sidecars.
- **C8dv `diverge:q05-c8`** (`:-` vs `?`): Dafny's failure-compatible protocol (`IsFailure`, `PropagateFailure`, `Extract`) vs Rust's `?` on `Result` (and the `From` conversion). No prediction.

### 3.4 Agent files (infra debugger): planted failures and receipts

The review found that the plan's planted failures (an `include`, a `#[path]` module, an import of L4) are all isolation-group (I1) errors of `check_course_map.py`, which scans every agent file, so the shipped course would fail CI. The revised failures are no I1 violation (§0.4 ran the planted stubs through every group) and are diagnosed from the receipts alone. Probed (Appendix A.12, `vcheck --json` and `vaudit` on the planted file, then on each repair step):

| file | planted | receipt (probed) | repair |
|---|---|---|---|
| `Q05_AgentInfra.dfy` | the `import opened QG_L3_BigNat` line is missing (the file imports L1, L2 and `Std.Wrappers`; the given `Larger` calls L3's `Cmp` once) | `vcheck --json` (exit 1): verdict `failed`, stage `resolve`, the tool's `exit_code` 2, one diagnostic at line 10: "unresolved identifier: Cmp" | add `import opened QG_L3_BigNat` (the chain in `MODULES.toml` is L1–L3) |
| | `module {:options "--function-syntax:4"} Q05_AgentInfra` (an accepted per-file option, Δ30) | in the planted state `vaudit` prints three findings, exit 1: two `audit-error` lines (the audit did not run to completion, exit 2; no summary line, W-D14) and `options-attribute` at line 1 ("verifier options live only in the unit's project file, never in a source file (spec §3.1 rule 6)"); after the import repair, `vcheck` verifies (32) and `vaudit` reports only `options-attribute` | delete the attribute; then `vcheck --gate` 32 verified, `vaudit` 0 findings |
| `agent.rs` | `use qg_bignat_l2::*;` where the file needs L3 (the given `one_more` calls L3's `add_limb`) | `vcheck --json` (exit 1): verdict `failed`, stage `resolve`, the tool's `exit_code` 1, one diagnostic: E0425 "cannot find function `add_limb` in this scope" (line 15) | `use qg_bignat_l3::*;` |
| | the given helper `limb_count` sits after the closing `} // verus!` | in the planted state `vaudit` prints `audit-incomplete` (the `--no-cheating` run stopped at resolve) and `outside-verus` at line 21 ("code outside verus! is never verified (V9, Δ9)"), exit 1; after the import repair, `vcheck` verifies (1) and `vaudit` reports only `outside-verus` | move the closing `} // verus!` below the helper; then `vcheck --gate` 2 verified, `vaudit` 0 findings |

- **Given code.** Dafny: `Larger(a, b)` (`r := if Cmp(a, b) < 0 then b else a;`, `ensures r == a || r == b`) and `Width(a)`; Verus: `one_more(a)` (`add_limb(a, 1)`) and `limb_count(a)`. None answers a Q04–Q06 item, and each failure gives one diagnostic. **Rule for the module lane:** any further given code in these files answers no item of Q01–Q06 (QPLAN §8.7 F7); the plan's `lemma_weight_one` was Q06.H1v's whole answer and `CmpSelf` a fragment of Q04.H4d's proof, so both are gone.
- **The acceptance's diff line** ("only lines outside every declaration change") admits both repairs in each file (an import line, the module header's attribute, the `verus!` boundary) and refuses edits of the given code.
- **Soft spots:** a contractor fixes the resolve error and stops at a green gate with the audit finding still there (the acceptance's `vaudit --compare` line catches it); it may "fix" `outside-verus` by deleting the helper (the diff line catches it); it may try to add a dependency or a `{:options}` line to `Cargo.toml` or `dfyconfig.toml` (guard 2g refusal).
- **QPLAN** names no failure: §10.4 says only "2 planted wiring failures, diagnosed from receipts".

### 3.5 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §10.2's exit table now names each Q05 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §10.2's exit table, as it stood:

**Exit (closed book; 4 items; ≥ 3/4 with ≥ 1/2 in each language).** Do not read this table before you sit Q05's exit (§8 banner).

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q05.X1d | S7 | by-method | `function CountFull(s: seq<nat>): nat`; `if \|s\| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])` | write the `by method` body: a loop that counts the limbs equal to `BASE - 1` | statement-shipped, exec hole in the by-method body |
| Q05.X2d | S6 | error-propagation | `method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)`; `ensures r.Success? <==> (\|s[..k]\| > 0 && AllDigits(s[..k]) && \|s[k..]\| > 0 && AllDigits(s[k..]))` | implement it (requires `k <= \|s\|`) with two `:-` steps over the given `ParseField` | statement-shipped, exec hole |
| Q05.X1v | S6 | mut-ref, result | `pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)`; `r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap)` | implement it on the given `Account { bal: u64, cap: u64 }` (the block's other `ensures`: both capacities unchanged, both balances within their capacities, `k` moved on `Ok`, nothing changed on `Err`) | statement-shipped, `external_body` hole |
| Q05.X2v | S6 | error-propagation | `pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)`; `r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0]))` | implement it with two `?` steps over the given `parse_digit` | statement-shipped, `external_body` hole |

Other QPLAN lines that described a Q05 exit statement, as they stood (QPLAN now points here):

- §10.1, the exit row of the files table:

```text
| exit | `dafny/Q/Q05_Frames/exit/Q05_Exit.dfy` (`module Q05_Exit`; imports L1, `Std.Wrappers`; holds the given `AllDigits` and `ParseField`, whose postcondition states exactly when it succeeds): 2 blocks, **2 shipped holes** (X1d, X2d). `verus/q/q05_frames/src/exit.rs` (holds the given `Account`, `Short`, `ParseError`, `is_digit` and `parse_digit` above the blocks): 2 blocks, **2 shipped holes** (X1v, X2v) | green |
```

### 3.6 As built (DV3a Q05 lane, 2026-10-05)

Q05's code is built: `Solutions/plans/Q05-code-notes.md` records the prediction answers as re-captured on the real scenarios, the shipped forms and gate results of every hole (the region gates included), the cards and demos, the agent files' receipts as captured, and the deviations from §3.2–§3.4 and Appendix A.8–A.12 (the Dafny file's card order, the P4d and P5v twins' reference bodies, the C4 and C5v demo designs, the commented checks, the receipt line numbers). DELTAS Δ139 and QPLAN §13 record the deviations without answers.

## 4. Q06

### 4.1 Prediction answers

| item | answer | evidence |
|---|---|---|
| P1dv | `D:0 V:0 true` | **re-posed** (revise lane): the Dafny half now runs `dafny test --no-verify --target py` (the old half, `dafny verify --no-verify`, only tested that the option is rejected). Captured through `run_capped` on `lab/p1dv.dfy` (a lemma with a false `ensures` and one passing `@Test`): exit 0, "Dafny program verifier did not attempt verification", "P1.Passes: PASSED" (matches `VERSIONS.md` G7). Without `--target py` the default C# target needs `dotnet` (absent: exit 3), hence the scenario's flag. Verus `verus p1dv.rs --crate-type=lib --no-verify --output-json`: exit 0, `success: true`, `verified: 0` (V18). `dafny verify --no-verify` still exits 1 ("not a recognized option") |
| P2dv | `D:1 inconclusive V:1 inconclusive` | `d/q06/p2_oor.dfy` (the naive `TwoShifts`): `vcheck --json` exit 1, `"verdict": "inconclusive"`, "Verification out of resource"; Verus: an out-of-resource proof fn, exit 1, `inconclusive`, "Resource limit (rlimit) exceeded". Plain failures give `failed` (`p2_fail.json`). The JSON's own `exit_code` field is the tool's (Dafny 4 for a failure), which is why the prompt says "of `scripts/vcheck` itself". The module lane captures the Verus half on H3v's quoted attempt (§4.2), which this lane saw out of resource |
| P3d | `FAILS b` | `d/q06/p3_trig.dfy` (Appendix B.5): [b] (`BASE * BASE` mentions no `Pow` term) fails; [a], [c], [d] hold |
| P4v | `FAILS b` | the Verus twin over `weight(k)` triggers: [b] fails even with `lemma_weight_zero()`/`lemma_weight_succ(0)` in scope (probe not retained) **As built (DV3a Q06 lane): `FAILS b c`**, captured on the built specimen and confirmed by `pins.py --ref`; why the plan's answer changed is in `Solutions/plans/Q06-code-notes.md` §4 |
| P5dv | `D:fail V:fail` | `d/q06/p5_scope.dfy`: `AfterBy` fails, `InsideBy` and `TopLevel` verify; the Verus twin `after_by` fails |
| P6dv | `a c` | `d/q06/p6_attr.dfy`: `vaudit` reports `resource-attribute` for `{:rlimit 1000}`; Verus `#[verifier::rlimit(1)]` not reported (at most the pin, 2), `#[verifier::rlimit(4)]` reported as `rlimit-inflation` |
| P7py | `c` | Wilson 95 % for 14/20: (0.4810, 0.8545), half-width 0.1867 (§4.6's sketch) |
| P8dv | `D:no V:no` | `vaudit` on the Q06 std file: 0 findings (Δ98: the 81 standard-library rows are excluded); `vcheck` and `vaudit` on `exit.rs` (uses `vstd::arithmetic`): verified, 0 findings (vstd's own trusted sites are not reported) |
| P9py | `c` | **re-posed**: n = 10, c = 3, k = 5: `1 - C(7, 5) / C(10, 5) = 1 - 21/252 = 0.9167`; the naive `1 - 0.7^5 = 0.8319` is option b, so the options a) 0.30 b) 0.83 c) 0.92 d) 1.00 separate the unbiased estimator from the naive one (the old k = 3 put both on one option) |

### 4.2 Holes and exits

References: Appendix A.13 (std), A.14 (exit), A.15 (`lib.rs`, the suite included), A.16 (`exit.rs`), A.20 (the budget attempts).

- **T1d** `assert Head(Drop(s, 1)) < 100;` (1 line). **T1v** `assert(limb_at(s, 1) < 100);` (1). With the prediction block first, T1 no longer comes before P3d/P4v.
- **H1d** `assert Pow(1) == BASE;` (1). **H1v** `lemma_weight_zero(); lemma_weight_succ(0); assert(weight(1) == BASE);` (3).
- **H2d** `reveal Pack(); ToNatCons(lo, [hi]); ToNatSingleton(hi); assert [lo] + [hi] == [lo, hi];` (4). **H2v** `reveal(pack);` and four asserts, among them `seq_to_nat(Seq::empty()) == 0` and `seq_to_nat(seq![hi]) == hi` (6).
- **H3d `TwoShifts`** (budget item). Reference: bridges, `Power.LemmaPowAdds(BASE, n, n)`, `Mul.LemmaMulUpperBound(x, p - 1, y, p - 1)`, `assert (p - 1) * (p - 1) < p * p;` (6 lines; 79,928 resource units). **Quoted attempt:** the bridges, `Power.LemmaPowAdds(BASE, n, n)` and `Power.LemmaPowPositive(BASE, n)` (Appendix A.20). At the pin it ends out of resource (5,007,842 units, 1.1 s); with `{:resource_limit 50000000}` it ran into Dafny's per-run time limit after 34 s at 24,619,794 units, still inconclusive. **No candidate attempt verifies at 10×** (the review asked for one): adding `assert x * y < Pow(n) * Pow(n)`, or the nonlinear hints `x * y <= x * (p - 1)`, `x * (p - 1) <= (p - 1) * (p - 1)`, `(p - 1) * (p - 1) < p * p` (V3), or `x * y < p * y || y == 0` with `p * y <= p * p` (V4), or `x * y <= (p - 1) * (p - 1)` (V5), each ends out of resource at 5M **and** at 50M (each 50M run burns the budget in 1–3 s): with nonlinear arithmetic on, the solver does not find the product bound without a library fact, whatever the budget. The reference minus its final assertion verifies (127,211 units), so that assertion is not needed and is dropped from the twin if the module lane prefers. QPLAN §8.0 therefore describes the attempt as one that "does not verify at the pinned limit" and the answer is the attempt with a library call **added** (no answer is the attempt with lines deleted).
- **H3v `lemma_seq_to_nat_append`** (budget item). Reference: structured recursion (11 lines; `lemma_mul_is_distributive_add` is not needed, `h3_ref_nodist` verifies without it). **Quoted attempt (replaced):** a quantified weight step `assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by { lemma_weight_succ(k); }` (a self-feeding trigger: each instance makes the next `weight` term) and a bare recursion (`h3_attempt`, Appendix A.20): "Resource limit (rlimit) exceeded" at `--rlimit 2` and again under `#[verifier::rlimit(20)]`. The answer deletes the quantified step and adds the extensionality assertion, `lemma_weight_succ(k)` and `lemma_mul_is_associative(…)`, so it is not the attempt minus lines. **Why the plan's attempt was dropped:** its "broadcast flood" was the reference plus `broadcast use` lines, so deleting them gave the answer; and in this lane's probes the reference plus `vstd::seq_lib::group_seq_properties`, `vstd::seq::group_seq_axioms` and `group_bignat_bounds` **verified** at `--rlimit 2` (`h3_flood_full`), while the flood without the extensionality assertion failed outright at 2 and at 20 (`app_flood`, `app_flood_base`).
- **H4d `CheckSplit`** (two-sided): a loop that returns `false` at the first mismatch, with invariant `forall j | 0 <= j < k :: f(samples[j].0, samples[j].1) == RefSplit(samples[j].0, samples[j].1)` and `decreases |samples| - k` (12); `ok := false` fails the `<==>` postcondition (probed). Suite over the boundary samples `(0, 0)`, `(1, BASE - 1)`, `(BASE - 1, 1)`, `(BASE - 1, BASE - 1)`, `(BASE / 2, BASE / 2)`: `AddCarryA` passes, `AddCarryB` (planted: `<=` for `<` at the carry boundary) is rejected; `vcheck --test` on the unit: 2 passed. **H4v `check_split_results`** (two-sided `ok == (forall …)`): the same loop over `got`, calling the given `split_matches` (one sample in `u128` arithmetic; given above the block to shrink the hole), 13 lines; the default TRIV `false` fails; suite 2 passed. No `// triv:` override.
- **X1d `FirstDisagreement`** (new): the same loop shape returning the index `k` of the first disagreement of `f` and `g`, or `-1` (13); a differential check of two candidates, where H4d checks one candidate against a reference. **X1v `first_disagreement`** (new): over two `Vec<bool>` result vectors, returning `Some(k)` or `None` (14); twin `// triv: { None }` (fails).
- **X2d `LowOfShift`** (new; opaque `Low(x, m) = x % m`, `requires m > 0`): `reveal Low(); DivMod.LemmaModMultiplesVanish(y, x, m);` (2; 7,578 units). **Quoted attempt:** a transparent copy `LowT` with an empty-bodied lemma: out of resource at 5M and at 50M (`TransparentEmpty`, `TransparentEmptyHigh`); `reveal Low();` alone behaves the same (`RevealOnly`, `RevealOnlyHigh`). The answer adds a library call to the revealed version. A rejected candidate: the opaque quotient `High(x, n) = x / Pow(n)` with `x < Pow(n + 1) ==> High(x, n) < BASE` verified with `reveal` alone (13,188 units), so it was no budget item.
- **X2v `lemma_low_of_shift`** (new; opaque `low(x, m) = x % m`): `reveal(low); lemma_mod_multiples_vanish(y as int, x as int, m as int);` (2). **Quoted attempt:** `reveal(low);` and a periodicity step `assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by { reveal(low); lemma_mod_add_multiples_vanish(t as int, m as int); }` (a self-feeding trigger): out of resource at `--rlimit 2` and under `#[verifier::rlimit(20)]`. The attempt's helper uses a different lemma (`lemma_mod_add_multiples_vanish`) from the answer's. A transparent copy fails outright in Verus (no out-of-resource), so the Verus attempt differs from the Dafny one; an opaque quotient `high` was rejected because `nonlinear_arith` with its `requires` proves it at the pin.
- **Unseen check.** X1 (a witness-returning differential checker) versus H4 (a boolean check against a reference) and the C4 card (a unary property); X2 (a remainder of a shifted value, opaque, one division-modulo lemma) versus H3 (a product bound or an append value) and H2 (pack/unpack). The plan's X2v (`lemma_split_value`) was H3v re-indexed, and X2d (`AppendBound`) repeated H3d's `LemmaPowAdds` plus a multiplication inequality; both are gone.

### 4.3 Cards

- **C1d / C1v `write:trigger`**: failure demos = a goal phrased without the trigger term → settle P3d / P4v: `// after: Q06.P3d` (Dafny), `// after: Q06.P4v` (Verus). Not `Head(Drop(s, k))` or `limb_at` (T1), not the prefix bounds of H1.
- **C2d / C2v `write:opaque-reveal`**: failure = a reveal confined to an `assert … by` and used afterwards → settles P5dv: both `// after: Q06.P5dv`. Not `Pack` (H2) and not a remainder (X2).
- **C3d / C3v `write:rlimit`**: failure = an out-of-resource proof → shows the verdict word and exit code → settles P2dv: both `// after: Q06.P2dv`. The demo's statement is none of `TwoShifts`, the append value or the remainder of a shifted value, and the demo shows no self-feeding trigger (H3v's and X2v's attempts). The card says nothing about attribute audits (P6dv).
- **C4d / C4v `write:property-test`**: success = a bounded checker of a **unary** property of sampled outputs (for example "every low limb is below the bound the candidate claims"), two-sided, and its suite; failure = the same checker with a one-sided `ok ==>` postcondition, which a constant `false` satisfies. Never two-function agreement (H4, X1), never a witness index (X1). No prediction.
- **C5dv `diverge:q06-c5`** (doors and verdicts): direct `dafny`/`verus` exit codes vs `scripts/vcheck`'s verdict words, `--no-verify` → `// after: Q06.P1dv` and `// after: Q06.P2dv`, sealed.
- **C6dv `diverge:q06-c6`** (trusted bases): what `vaudit` reports in each language (attributes, the libraries) → `// after: Q06.P6dv` and `// after: Q06.P8dv`, sealed.

### 4.4 Python items

Reference (sketch, §4.6): H5py counts `diagnostics` entries with `severity == "error"`, takes `len(doc["holes"])`, and copies `lang`, `verdict`, `verified_count`. H6py keeps one first-attempt record per task for the arm and calls `fvh.stats.wilson_interval`; for an arm with no records it raises `ValueError` (QPLAN §11.8; the sketch predates this and divides by zero). H7py groups by task and averages `fvh.stats.pass_at_k(n, c, k)`; `ValueError` for an empty arm. TRIV bodies for the Python TRIV mode (QPLAN §11.8): H5py `return RunRecord(task_id, arm, attempt, "", "verified", 0, 0, 0)`; H6py `return (0, 0, (0.0, 1.0))`; H7py `return 0.0`. The acceptance tests must reject each (a failed document must map to `failed`; a non-empty record set must give `n > 0`, and an empty arm must raise; a solved task must give a positive pass@k). **Leak constraints:** the frozen tests and the paper problems use neither P7py's input (14 of 20) nor P9py's (n = 10, c = 3, k = 5), and no test helper re-implements H5py–H7py (tests compare with constants and with `fvh.stats` itself).

**`EVAL.md` v0** (what the rubric should look for): claim ("my first-try prediction rate on Q01–Q06"), metric (first-try pass, `predict` records only; other kinds excluded and counted, through `fvh.records.calib_records`), estimator (proportion with a Wilson 95 % interval via H6py's function or `fvh.stats` directly), n and exclusions, cost (minutes from the gradebook), and a disclosure line (the predictions were the learner's; Claude was the tutor and grader of the paper parts). **`TRUST.md` v0**: Dafny 4.11.0 front end and Boogie, Z3 4.12.1 (the bundled default), the standard library (its `{:axiom}`s are not reported by `vaudit`, Δ98; some lemmas carry their own `@ResourceLimit`, for example `LemmaFundamentalDivModConverse`), `scripts/vcheck`/`vaudit` and the generated `dfyconfig.toml`s, L1–L3; Verus 0.2026.09.27, rustc 1.98.1, Z3 4.16.0, `vstd` (its `external_body` and `assume_specification` sites), `--no-cheating`, the course wrappers, L1–L3. For each, one line on what would make a green run wrong (a lying solver on PATH, G22; an `external_body` in `vstd` with a wrong spec; a wrapper bug).

### 4.5 Agent file (audited prover, Dafny only)

Top lemma `CanonicalUnique`. **The reference skeleton** (Appendix A.19, from DV0's `Solutions/spikes/dafny/QG_L3_BigNat.dfy`): three leaves, `PowMono` (`Pow(m) <= Pow(n)` for `m <= n`: two bridges and `Power.LemmaPowIncreases`), `ToNatLowerBound` (a canonical non-empty value is at least `Pow(|s| - 1)`: recursion on `s[1..]`), `CanonicalLengthOrder` (a shorter canonical numeral has a smaller value: `ToNatBound`, `ToNatLowerBound`, `PowMono`), and the top lemma's proof (length cases by `CanonicalLengthOrder`, then `ValidTail`, two last-limb asserts, the recursive call and two concatenation asserts; 15 lines). Built and gated by this lane: the twin passes `--gate` (35 verified); with the three leaves bodyless the file is green with 3 holes; as shipped (top lemma bodyless, empty `SKELETON`) it is green with 1 hole; each leaf's empty body is lever-needed (maxauto verifies, every seed fails under the file's manual induction) and the top lemma's empty body fails every run.

- **Why no Verus rung.** The Verus decomposition's natural leaves are not holes: `leaf_same_length` (equal values of canonical numerals have equal lengths) verifies under EC (the course group), `leaf_tail_wf` (the tail of a canonical numeral is canonical) and `leaf_head_tail` (equal values give equal low limbs and equal tail values) verify under E0 (`leaves.rs`, Appendix A.21). A Verus agent file would have no admissible leaf, and one 15-minute line cannot hold two skeletons.
- **The decomposition's shape** (what QPLAN §11.4 lets the file's `SKELETON` comment say): a lower bound on a canonical numeral's value, an order between lengths, a monotonicity fact about `Pow`. It names no lemma and no proof step.
- **Budget.** 15 minutes: skeleton 8 (three leaf statements and a 15-line top proof, given the shape), contract run and audit 7. Timed first in the calibration run.
- **Soft spots:** a contractor strengthening a leaf's `requires` until it is vacuous (the usefulness check catches it), changing a leaf statement (`specfreeze --against` catches it), adding a sixth lemma, or proving a leaf by an `{:induction}` attribute (the gate would call it lever-needed; the audit shows the attribute).

### 4.6 The Python sketch (`/tmp/dvl0-dv3a-plan/py/sketch/`)

A standard-library-only sketch of `fvh.stats.pass_at_k`, `wilson_interval`, `fvh.records.RunRecord`, `fvh.holes.count_holes` (AST) and the Q06 reference (Appendix A.18). Its check printed: `wilson 14/20: 0.481 0.8545 half-width 0.1867`; `pass@3 n=10 c=3: 0.7083`; the reference has 0 holes, a copy with the three bodies replaced by `raise NotImplementedError("<id>")` has 3, and a string holding that text inside a function is not a hole. The revise lane recomputed P9py's new value with `math.comb` (0.9167; naive 0.8319). DV4 owns the real core (QPLAN §11.8); the sketch is evidence that the specified API and hole form are buildable with the standard library alone. It does not yet implement the empty-arm `ValueError` or `calib_records`.

### 4.7 Exit statements and prompts (moved from QPLAN by Δ133)

*Moved verbatim on 2026-10-05 by the DV3a records lane (QPLAN §6 Q25, DELTAS Δ133). QPLAN §11.2's exit table now names each Q06 exit item only by its id, form, strand, language, file and minutes; this section holds the rest, as it stood in QPLAN. Edit an exit statement here, never in QPLAN, and keep the exit file, its twin and this section in step. The answers and references are in the module's exit section above.*

QPLAN §11.2's exit table, as it stood:

**Exit (closed book; 4 items; ≥ 3/4 with ≥ 1/2 in each language).** Do not read this table before you sit Q06's exit (§8 banner).

| id | strand | pair | uses | need | prompt | shipped |
|---|---|---|---|---|---|---|
| Q06.X1d | S12 | Q06.X1v | property-test | `method FirstDisagreement(f: nat -> int, g: nat -> int, samples: seq<nat>) returns (r: int)`; its three `ensures` (`-1 <= r < \|samples\|`; `r == -1` exactly when `f` and `g` agree on every sample; `r >= 0 ==>` they disagree at `samples[r]`) | write the checker that compares two candidates on the samples | statement-shipped, exec hole |
| Q06.X2d | S11 | Q06.X2v | opaque-reveal, rlimit | `lemma LowOfShift(x: nat, y: nat, m: nat)`; `ensures Low(x + m * y, m) == Low(x, m)` | prove it (requires `m > 0`; `opaque function Low(x, m) = x % m` is given above the block, which quotes, commented, an attempt that does not verify at the pinned limit) at the pinned limit, with no resource attribute | statement-shipped, bodyless lemma · the opacity of `Low` |
| Q06.X1v | S12 | Q06.X1d | property-test | `pub fn first_disagreement(xs: &Vec<bool>, ys: &Vec<bool>) -> (r: Option<usize>)`; its two `ensures` (`r is None` exactly when the two result vectors agree everywhere; `r is Some ==>` they disagree at the returned index) | write the checker (requires `xs.len() == ys.len()`) | statement-shipped, `external_body` hole |
| Q06.X2v | S11 | Q06.X2d | opaque-reveal, rlimit | `pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)`; `low(x + m * y, m) == low(x, m)` | prove it (requires `0 < m`; `#[verifier::opaque] spec fn low(x, m) = x % m` is given above the block, which quotes, commented, an attempt that does not verify at the pinned limit) at the pinned limit, with no resource attribute | statement-shipped, `proof_note` assume · the opacity of `low` |

Other QPLAN lines that described a Q06 exit statement, as they stood (QPLAN now points here):

- §8.0, the property-test row:

```text
| **Property-test item** (Q06.H4d/H4v, X1d/X1v) | an exec hole: a bounded checker whose postcondition is **two-sided** (`ok` holds exactly when every sample has the property; an exit's checker also returns a witness index), so no constant body verifies. Below it, outside the verified code (Verus: a `#[cfg(test)]` module after `verus!`; Dafny: `@Test` methods), a commented suite under `Uncomment as you go:` runs the checker on a correct candidate (it must pass) and on a planted one (it must reject it). Done adds `scripts/vcheck --test` on the unit (§6 Q20) |
```

- §11.1, the exit row of the files table:

```text
| exit | `dafny/Q/Q06_Machine/exit/Q06_Exit.dfy` (`module Q06_Exit`; imports L1–L3, `Std.Arithmetic.DivMod`): 2 blocks, **2 shipped holes** (X1d, X2d). `verus/q/q06_machine/src/exit.rs`: 2 blocks, **2 shipped holes** (X1v, X2v); each opaque definition an exit item uses sits above its block | green |
```

### 4.8 As built (DV3a Q06 lane, 2026-10-05)

Q06's code is built: `Solutions/plans/Q06-code-notes.md` records the verdict answers as captured (P4v's differs from §4.1's plan; the row above is marked), the hole references and gates, the learner-flow simulation and the deviations from §4.2–§4.5 and Appendix A.13–A.19 (given definitions above their hole's marker, the X1 suites, the C3, C4 and C6dv demos, the agent twin's leaves). Where Appendix A.13–A.16 and the twins differ, the twins are authoritative. The Python core and the twin `Solutions/harness/q/fvh_q/q06_stats.py` are the fvh lane's (DELTAS Δ136).

## 5. Minutes and calibration notes

The itemized minutes are the design's (§7.5) line by line. Hole minutes are itemized per item inside each holes line (QPLAN §9.6, §10.5, §11.5): Q04 54 (H1v 8, the rest 5–6), Q05 54 (H1d and H4d 4 as annotation holes, H4v and H5v 10 as the two exec holes the Verus shape rule keeps whole), Q06 36 for six verifier holes plus the two property-test holes inside the 15-minute property line and the three Python holes inside the 30-minute statistics line. Per language over the tier: Dafny 13 holes, 70 minutes; Verus 13 holes, 86 minutes (45 / 55). The first calibration run (Δ128's harness, once run) times, in this order: Q05.H4v, Q05.H5v, Q04.H1v, Q06.H3v, Q06.H4v, Q05.H3d and the Q06 agent skeleton. If a Verus exec hole runs over, the lane moves minutes inside the holes line (from the Dafny annotation holes), never from another line.

## 6. What the module lanes must not do

- Change a statement, an answer form or a label order without updating this file and re-running the gate.
- Put a `decreases`-less recursive function in any Q04 file (Q05.P2dv), a reveal-scope demo before Q06's prediction block (P5dv), or a `u128`-split in live Q04 code (P1dv).
- Ship a planted failure (any agent file) that `check_course_map.py` flags: run every group on the shipped agent files, not only on the repaired ones.
- Put an answer of any Q01–Q06 item into given code, a specimen or a card demo: in particular no `Push` body in P4d, no `maybe_push`/`try_push` body in P5v, no agent given code from §3.4's history, and the card constraints of §2.3, §3.3 and §4.3.
- Quote a budget attempt from which deleting lines yields the answer, or let a budget item's twin carry a resource attribute.
- Ship a Verus annotation hole whose loop body, or a `return` inside its loop, needs the learner's invariant (QPLAN §8.0's shape rule; Q04.H4v's plan shape was red).
- Give a property-test checker a one-sided (`ok ==>`) postcondition, or a `// triv: { true }` body.
- Use `LittleEndianNat` anywhere (Δ35), a `Std` import in Q04's core file, or a `vstd::arithmetic` import in Q04's `lib.rs`.
- Write L3 before the orchestrator decides QPLAN §6 Q15, or arm Q05 before §6 Q22 and Q06 before §6 Q19 and Q21. *Decided (Δ130, Δ134, Δ135):* Q15 is decided, so L3 may be written; Q19, Q21 and Q22 are built in DV3a, and the arming conditions stand until each build is recorded.

## 7. Review findings: disposition

The review (2026-10-05) raised 3 blockers, 14 majors and 6 minors (its verdict line counts 15 majors; its list holds 14). Each is listed with what the revise lane did; "applied" means the fix is in QPLAN §5.1, §6 and §8–§11 and in this file.

| # | finding | disposition |
|---|---|---|
| B1 | Q05's planted wiring failures are I1 isolation errors, so CI fails | **applied, route (b):** new failures (a missing L3 import, a lower layer's crate; an `{:options}` attribute, a helper outside `verus!`), probed as a two-failure state and step by step (§3.4), and the planted stubs pass every checker group (§0.4). Route (a), a `// planted:` exemption in the isolation group, is **rejected**: it needs a tools change, and the marker would sit in the file the contractor diagnoses, pointing at the planted lines (Δ118's open item is the same hint risk) |
| B2 | P4d and P5v specimens hold H1d's and H2v's answers | **applied:** `Push` contract-only, `maybe_push` `external_body` on a renamed type; both re-probed (`FAILS b`); constraint in §6 |
| B3 | property-test items accept a constant body; `firsttry` runs no test | **applied:** two-sided checkers (X1 also returns a witness), default TRIV fails, `{ true }` bodies dropped; QPLAN §6 Q20 kept, now low |
| M1 | P7v's text hints at the answer; the answer was never captured | **applied:** the run-safety sentence is gone (`vcheck` caps memory); the scenario is re-posed and captured (`V:ok`, §2.1); the old answer rested on a different scenario |
| M2 | T items settle predictions; P2dv's Verus half repeats Q01.P7dv | **applied:** the moderate tier puts the prediction block before T (QPLAN §8.0, §6 Q23 for enforcement); P2dv's Verus half re-posed and captured |
| M3 | L3 trips Q02/Q03 leak patterns; §1.1 rule 3 | **escalated:** QPLAN §6 Q15 proposes the DELTAS text (blocks L3); this lane does not write DELTAS; *decided* by the orchestrator (Δ130) |
| M4 | renumbering broke references | **applied:** QPLAN §1–§7 are byte-identical to HEAD except the status line and §5's heading; the new material is §5.1, §6 Q13–Q25 and §8–§11; the old Q21 is dropped |
| M5 | rlimit items unenforced; quoted proofs misdescribed | **applied in part, adapted in part:** QPLAN §6 Q21 (the lint at the exit and in the strict report); H3v's attempt replaced (no answer is an attempt minus lines); every attempt re-probed at 10×. **Adapted:** no Dafny attempt verifies at 10× (§4.2: five variants out of resource at 50M), so instead of keeping only 10×-verifying attempts the plan now describes each quoted attempt truthfully (it does not verify at the pinned limit), and the card teaches that an out-of-resource verdict says nothing about "almost" |
| M6 | Q05.H2d conflicts with the statement freeze | **applied:** QPLAN §6 Q22 (`open_frames`), probed with `specfreeze --against` |
| M7 | Q05 agent given code answers Q06.H1v; the plan's Q05 agent section names the failures | **applied:** new given code (§3.4), QPLAN §10.4 names no failure |
| M8 | card-demo leak constraints have gaps | **applied:** §2.3, §3.3, §4.3 |
| M9 | exits not unseen (Q06.X1, X2; Q05.X1v) | **applied:** Q06.X1d/X1v (differential, witness), X2d/X2v (opaque remainder), Q05.X1v (`transfer`); every exit checked against its module's H, T and W items (QPLAN §5.1) |
| M10 | strand markers break the usage rule | **applied:** H1v, H4v, H5v, X1v to S5 (and H1d to S4, which the review did not list but which used lemma recursion from S3) |
| M11 | Verus library staging | **applied:** `lib.rs` / `library.rs` split, verified (§2.2) |
| M12 | E2 not run on the Verus pow goals | **applied:** E2 closes two goals; both replaced; E2 run on every Verus proof hole of Q04–Q06 (all fail) |
| M13 | holes too large for 6 minutes | **applied in part:** Q05.H1d, H4d, H5d shrink to 3–6 lines (new hole forms), Q06.H4v gets a given helper; **not possible** for Q05.H4v and H5v (the Verus shape rule, probed), which get 10 minutes each inside the holes line; Q04.H1v keeps its size (a `calc!` chain over five relations) at 8 minutes; all are first in the calibration order |
| M14 | rung 6 unbuilt; budget unrealistic | **applied:** the Dafny twin is built and gated, the skeleton is committed before `/contract`, the decomposition's shape is given; the Verus rung is dropped (its leaves fall to automation, probed) |
| m1 | card-level hand before automation; H4v's form undeclared | **applied:** C5v/C6v content (§2.3); QPLAN §8.0 rows for H4v's form and the shape rule |
| m2 | X1v prompt; X2d's lever | **applied** |
| m3 | P9py does not discriminate; P7v repeats P6d | **applied:** P9py at k = 5; P7v removed (folded into P6d and P9dv) |
| m4 | `fvh` spec gaps | **applied:** empty arms raise, `calib_records`, `.gitignore`, `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, leak constraints (QPLAN §11.8) |
| m5 | F6 vs Q16 H2; `FromNatCanonical`; exit tables; §2.6; audit rows | **applied:** QPLAN §6 Q14, §8.5, the §8 banner and §6 Q25, §2.6 here (runs captured), §6 Q24 |
| m6 | rates off-spec; P3dv's build directory; P1dv tests an option; TRUST.md strand | **applied:** QPLAN §8.0's rates row (the deviations recorded), P3dv's scratch directory, P1dv re-posed and captured, the D4 nominal comment |
| new | Q04.H4v's plan shape ships red | **found and fixed** by this lane (§2.2) |
| new | Verus annotation holes need the loop body to verify under the shipped invariant | **found;** QPLAN §8.0's shape rule |

## 8. DV3a integration (2026-10-05): the leak scan's author-only detail

The integration lane's leak scan (DELTAS Δ140) compared every learner-visible text file of the worktree (797 files: everything outside `Solutions/`, `.git`, `.toolchain`, `build/`, `target/`, the caches, `tests/instructor/leak_patterns/`, `tests/instructor/fixtures/` and `paper/solutions/`) with the answer regions of the 62 Q01–Q06 twins (30 of them Q04–Q06's, the Python twin and the obligation specimens included) (twin lines a line diff leaves unmatched against the learner counterpart, comments stripped: 623 answer lines of at least 12 code characters and 6892 seven-token shingles), every reference slot value of Q04–Q06, and the code spans, fenced code and eight-word runs of this file's answer sections (§2.1–§2.6, §2.8, §3.1–§3.5, §4.1–§4.7) and of the three code notes. Given layers above a twin's module were exempt (Δ130): L3 for Q01–Q03 twins, L2 for Q01's. Every hit was reviewed. Scripts and reports: `/tmp/dvl0-dv3a-integ/leak/` (lane scratch, not archived).

No hole, exit, test-out or agent answer of Q04–Q06, and no verdict, obligation or value answer, appears in a learner-visible file. The hits are statements and commented checks the files ship (and QPLAN quotes), given code and WRITE-card examples that the holes use by design, generic loop, recursion and `calc` scaffolding, test-fixture idioms, and verdict-form strings that are Q01–Q03's own answers in their chapters and banks. The exempt hits in L3 are its re-supplied Q02–Q03 hole proofs; L3 holds the whole answer of no Q01–Q03 exit item (its one-zero `ToNatDropLastZero` is a step toward Q02.X3d, and L3 is not on Q02's spine).

Accepted exposures, all low, each guarded by the order of work or the *Predictions first* norm:
- **Q06.P6dv** can be read off DV1b's lint fixtures (`tests/wrappers/fixtures/dafny/lint/learner.dfy` and `tests/wrappers/fixtures/verus/lint/learner.rs` mark which resource attributes the lint flags) and off the lint rules in `scripts/dvl/`. Pre-existing (the tools lane's report).
- **Q05.H5d and Q05.H5v:** the exit files' given parsers open with the same empty-input line as the holes' answers; **Q05.X1d's** answer reuses the slice assertion that H4d's given code shows. The exit files stay closed until the exit, which comes after the holes (the Q05 lane's report).
- **Q05.H4v** (an exec hole) asks for the loop whose code Q05.H4d (an annotation hole) ships; the measure and the invariants, which the pair tests, are given in neither. This follows QPLAN §10.2's hole forms.
- **Q04.X1d's** empty case and tail equality are the sequence-append idiom of DV1b's freeze fixture `tests/wrappers/fixtures/dafny/freeze/good.dfy` (`RevAppend`); the chain over `Pow` is not there. Pre-existing and generic.
- **Q06.H4d/H4v and X1d/X1v** share their loop scaffolding with card C4's given checker (a WRITE card, by design).
- The in-file `EXPECT` lines of WRITE demos that carry `after:` lines stay readable (Δ120, Δ122): Q04's C1 demos (P3dv), C5v (P9v) and C6v (P6v); Q05's C1d, C4d, C4v and C5v; Q06's C1–C3 demos (C3's bear on P2dv).

Fixed by the integration lane: the synthetic Q04 of `scripts/test_course_map.py` filled its `P1dv` slot, in one case, with a value equal to the real Q04.P1dv's answer (a DV1a fixture that predates the answer); the value is now one that answers nothing.

## Appendix A. Candidate files (scratch, as verified)

Each block is the file as it stood when last verified; paths are the planned ones under the lane's `root/` (the plan lane's `/tmp/dvl0-dv3a-plan/root/` for unchanged blocks, the revise lane's `/tmp/dvl0-dv3a-revise/root/` otherwise). Item markers in these candidates are informal (some carry trailing notes); the module lanes write the real markers.

### A.1 L3, Dafny
`root/dafny/given/Q/QG_L3_BigNat.dfy`

```dafny
/*!
# QG_L3_BigNat — the BigNat spine, layer L3 (PROVIDED, complete)

Candidate (DV3a plan lane, scratch). Re-supplied intro-tier lemmas, the
moderate-tier definition Cmp, and the std-tier helper PowIsStdPow.
*/
module QG_L3_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import Power = Std.Arithmetic.Power

  // Re-supplied intro-tier targets (Q02-Q03)

  lemma ToNatDropLastZero(s: seq<nat>)
    requires |s| > 0 && s[|s| - 1] == 0
    ensures ToNat(s[..|s| - 1]) == ToNat(s)
  {
    var p := s[..|s| - 1];
    assert s == p + [0];
    ToNatAppendZero(p);
  }

  lemma NormalizeToNat(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      ToNatDropLastZero(s);
      NormalizeToNat(s[..|s| - 1]);
    }
  }

  lemma NormalizeCanonical(s: seq<nat>)
    requires Valid(s)
    ensures Canonical(Normalize(s))
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeCanonical(s[..|s| - 1]);
    }
  }

  lemma FromNatCorrect(n: nat)
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
    decreases n
  {
    if n > 0 {
      FromNatCorrect(n / BASE);
      ToNatCons(n % BASE, FromNat(n / BASE));
      ValidCons(n % BASE, FromNat(n / BASE));
    }
  }

  lemma AddLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(AddLimb(s, d)) && ToNat(AddLimb(s, d)) == ToNat(s) + d
    decreases |s|
  {
    if |s| == 0 {
      ToNatSingleton(d);
    } else if s[0] + d < BASE {
      ValidTail(s);
      ToNatCons(s[0] + d, s[1..]);
      ValidCons(s[0] + d, s[1..]);
    } else {
      ValidTail(s);
      AddLimbCorrect(s[1..], 1);
      ToNatCons(s[0] + d - BASE, AddLimb(s[1..], 1));
      ValidCons(s[0] + d - BASE, AddLimb(s[1..], 1));
    }
  }

  // The moderate-tier definition: three-way comparison by the most
  // significant differing limb; a missing limb reads as 0.
  function Cmp(a: seq<nat>, b: seq<nat>): int
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then 0
    else
      var c := Cmp(Tail(a), Tail(b));
      if c != 0 then c
      else if Head(a) < Head(b) then -1
      else if Head(a) > Head(b) then 1
      else 0
  }

  // The std-tier helper: L1's Pow is the standard library's power at BASE.
  lemma PowIsStdPow(n: nat)
    ensures Pow(n) == Power.Pow(BASE, n)
    decreases n
  {
    if n > 0 {
      PowIsStdPow(n - 1);
    }
  }
}
```

### A.2 L3, Verus
`root/verus/given/qg_bignat_l3/Cargo.toml`

```toml
[package]
name = "qg_bignat_l3"
version = "0.1.0"
edition = "2021"
publish = false
build = false

[lib]
path = "src/lib.rs"

[dependencies]
vstd = "=0.0.0-2026-09-20-0158"
qg_bignat_l1 = { path = "../qg_bignat_l1" }
qg_bignat_l2 = { path = "../qg_bignat_l2" }

[package.metadata.verus]
verify = true
```
`root/verus/given/qg_bignat_l3/src/lib.rs`

```rust
//! qg_bignat_l3 candidate (DV3a plan lane, scratch).
#![allow(unused_imports)]
use vstd::prelude::*;
pub use qg_bignat_l2::*;

verus! {

// ---- re-supplied intro-tier targets (Q02-Q03) ----

pub proof fn lemma_seq_to_nat_drop_last_zero(s: Seq<u64>)
    requires
        s.len() > 0,
        s.last() == 0,
    ensures
        seq_to_nat(s.drop_last()) == seq_to_nat(s),
{
    assert(s.drop_last().push(0) =~= s);
    lemma_seq_to_nat_push_zero(s.drop_last());
}

pub fn from_u64(x: u64) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    let mut v: Vec<u64> = Vec::new();
    if x != 0 {
        v.push(x);
        proof {
            assert(v@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(v@.drop_first()) == 0);
        }
    }
    BigNat { limbs: v }
}

pub fn add_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = x;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![x as nat];
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == x,
            c[i as int] == carry,
            i > 0 ==> carry <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + c[j] == #[trigger] res@[j] + BASE * c[j + 1],
        decreases n - i,
    {
        let li = a.limbs[i];
        if li <= u64::MAX - carry {
            res.push(li + carry);
            carry = 0;
        } else {
            res.push(li - (u64::MAX - carry) - 1);
            carry = 1;
        }
        i = i + 1;
        proof {
            c = c.push(carry as nat);
        }
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
        }
    }
    proof {
        lemma_add_limb_lift(a@, res@, c);
    }
    BigNat { limbs: res }
}

// ---- the moderate-tier power and its bounds group ----

#[verifier::opaque]
pub open spec fn weight(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        BASE * weight((n - 1) as nat)
    }
}

pub proof fn lemma_weight_zero()
    ensures
        weight(0) == 1,
{
    reveal(weight);
}

pub proof fn lemma_weight_succ(n: nat)
    ensures
        weight(n + 1) == BASE * weight(n),
{
    reveal(weight);
}

pub broadcast proof fn lemma_weight_mono(m: nat, n: nat)
    requires
        m <= n,
    ensures
        #[trigger] weight(m) <= #[trigger] weight(n),
    decreases n,
{
    reveal(weight);
    if m < n {
        lemma_weight_mono(m, (n - 1) as nat);
    }
}

pub broadcast proof fn lemma_seq_to_nat_upper(s: Seq<u64>)
    ensures
        #[trigger] seq_to_nat(s) < weight(s.len()),
    decreases s.len(),
{
    reveal(weight);
    if s.len() > 0 {
        lemma_seq_to_nat_upper(s.drop_first());
    }
}

pub broadcast proof fn lemma_seq_to_nat_lower(s: Seq<u64>)
    requires
        seq_wf(s),
        s.len() > 0,
    ensures
        weight((s.len() - 1) as nat) <= #[trigger] seq_to_nat(s),
    decreases s.len(),
{
    reveal(weight);
    if s.len() > 1 {
        assert(s.drop_first().last() == s.last());
        lemma_seq_to_nat_lower(s.drop_first());
    }
}

pub broadcast group group_bignat_bounds {
    lemma_weight_mono,
    lemma_seq_to_nat_upper,
    lemma_seq_to_nat_lower,
}

/// Same length, equal above index `i`, smaller at `i`: smaller value.
pub proof fn lemma_lt_at(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        a.len() == b.len(),
        0 <= i < a.len(),
        a[i] < b[i],
        forall|j: int| i < j < a.len() ==> a[j] == b[j],
    ensures
        seq_to_nat(a) < seq_to_nat(b),
    decreases i,
{
    if i == 0 {
        assert(a.drop_first() =~= b.drop_first());
    } else {
        lemma_lt_at(a.drop_first(), b.drop_first(), i - 1);
    }
}

} // verus!
```

### A.3 Q04 core file (T1d, H1d, H2d, X1d filled)
Unchanged code; the real markers give H1d strand S4 (QPLAN §9.2).

`root/dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy`

```dafny
module Q04_ProofCraft {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q04.T1d S4
  lemma ZeroValueZeroLimbs(s: seq<nat>)
    requires ToNat(s) == 0
    ensures forall i | 0 <= i < |s| :: s[i] == 0
    decreases |s|
  {
    if |s| > 0 {
      ZeroValueZeroLimbs(s[1..]);
      forall i | 0 <= i < |s|
        ensures s[i] == 0
      {
        if i > 0 {
          assert s[i] == s[1..][i - 1];
        }
      }
    }
  }

  // item: Q04.H1d S3
  lemma PowAdd(m: nat, n: nat)
    ensures Pow(m + n) == Pow(m) * Pow(n)
    decreases m
  {
    if m > 0 {
      calc {
        Pow(m + n);
      ==
        BASE * Pow(m - 1 + n);
      == { PowAdd(m - 1, n); }
        BASE * (Pow(m - 1) * Pow(n));
      ==
        (BASE * Pow(m - 1)) * Pow(n);
      ==
        Pow(m) * Pow(n);
      }
    }
  }

  // item: Q04.H2d S2
  lemma PrefixBounds(s: seq<nat>)
    requires Valid(s)
    ensures forall k | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
  {
    forall k | 0 <= k <= |s|
      ensures ToNat(s[..k]) < Pow(k)
    {
      ToNatBound(s[..k]);
    }
  }

  // item: Q04.X1d S3
  lemma ToNatAppend(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
    } else {
      calc {
        ToNat(a + b);
      == { assert (a + b)[1..] == a[1..] + b; }
        a[0] + BASE * ToNat(a[1..] + b);
      == { ToNatAppend(a[1..], b); }
        a[0] + BASE * (ToNat(a[1..]) + Pow(|a| - 1) * ToNat(b));
      ==
        ToNat(a) + Pow(|a|) * ToNat(b);
      }
    }
  }
}
```

### A.4 Q04 library file (H3d, H4d, X2d filled)
`root/dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy`

```dafny
module Q04_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  // item: Q04.H4d S4
  lemma CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  {
    if |a| != 0 || |b| != 0 {
      ValidTail(a);
      ValidTail(b);
      CmpCorrect(Tail(a), Tail(b));
      ToNatHeadTail(a);
      ToNatHeadTail(b);
    }
  }

  // item: Q04.H3d S5
  lemma ShiftBound(x: nat, n: nat, m: nat)
    requires x < Pow(n)
    ensures x * Pow(m) < Pow(n + m)
  {
    PowIsStdPow(n);
    PowIsStdPow(m);
    PowIsStdPow(n + m);
    Power.LemmaPowAdds(BASE, n, m);
    Power.LemmaPowPositive(BASE, m);
    Mul.LemmaMulStrictInequality(x, Pow(n), Pow(m));
  }

  // item: Q04.X2d S5
  lemma PowsBelow(n: nat)
    ensures forall k | 0 <= k < n :: Pow(k) < Pow(n)
  {
    forall k | 0 <= k < n
      ensures Pow(k) < Pow(n)
    {
      PowIsStdPow(k);
      PowIsStdPow(n);
      Power.LemmaPowStrictlyIncreases(BASE, k, n);
    }
  }
}
```

### A.5 Q04 and Q05 check units
`root/dafny/checks/Q04_checks.dfy`

```dafny
module Q04_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Std.Wrappers

  @Test
  method P2() {
    expect Cmp([5, 1], [7, 0, 0]) == 1;
  }
}
```
`root/dafny/checks/Q05_checks.dfy`

```dafny
module Q05_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Std.Wrappers

  @Test
  method P2() {
    expect |AddLimb([18446744073709551615, 18446744073709551615], 1)| == 3;
  }
}
```

### A.6 Q04 Verus crate: `lib.rs`, `library.rs`, `exit.rs` (every Verus item filled)
The crate root declares `mod library;`. The H4v shipped form follows the twin (Appendix B.8 holds the plan's red shape).

`root/verus/q/q04_proof_craft/src/lib.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use qg_bignat_l3::*;

mod library;

verus! {

// item: Q04.T1v S4
pub proof fn lemma_zero_value_zero_limbs(s: Seq<u64>)
    requires
        seq_to_nat(s) == 0,
    ensures
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_zero_value_zero_limbs(s.drop_first());
        assert forall|i: int| 0 <= i < s.len() implies s[i] == 0 by {
            if i > 0 {
                assert(s[i] == s.drop_first()[i - 1]);
            }
        }
    }
}

// item: Q04.H2v S2
pub proof fn lemma_first_difference(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
    ensures
        forall|i: int|
            0 <= i < a.len() && #[trigger] a[i] < b[i] && (forall|j: int| i < j < a.len() ==> a[j] == b[j])
                ==> seq_to_nat(a) < seq_to_nat(b),
{
    assert forall|i: int|
        0 <= i < a.len() && #[trigger] a[i] < b[i] && (forall|j: int| i < j < a.len() ==> a[j] == b[j])
        implies seq_to_nat(a) < seq_to_nat(b) by {
        lemma_lt_at(a, b, i);
    }
}

// item: Q04.W1v S3
pub proof fn lemma_weight_succ_comm(n: nat)
    ensures
        weight(n + 1) == weight(n) * BASE,
{
    calc! {
        (==)
        weight(n + 1); { lemma_weight_succ(n); }
        BASE * weight(n);
        (==) { }
        weight(n) * BASE;
    }
}

} // verus!
```

`root/verus/q/q04_proof_craft/src/library.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::calc;
use qg_bignat_l3::*;
use core::cmp::Ordering;

verus! {

// item: Q04.H1v S5
pub proof fn lemma_weight_add(m: nat, n: nat)
    ensures
        weight(m + n) == weight(m) * weight(n),
    decreases m,
{
    if m == 0 {
        lemma_weight_zero();
        assert(m + n == n);
    } else {
        let k = (m - 1) as nat;
        lemma_weight_add(k, n);
        lemma_weight_succ(k + n);
        lemma_weight_succ(k);
        calc! {
            (==)
            weight(m + n); { assert(m + n == (k + n) + 1); }
            BASE * weight(k + n);
            (==) { }
            BASE * (weight(k) * weight(n));
            (==) { lemma_mul_is_associative(BASE as int, weight(k) as int, weight(n) as int); }
            (BASE * weight(k)) * weight(n);
            (==) { }
            weight(m) * weight(n);
        }
    }
}

// item: Q04.H3v S5
pub proof fn lemma_shift_bound(x: nat, n: nat, m: nat)
    requires
        x < weight(n),
    ensures
        x * weight(m) < weight(n + m),
{
    lemma_weight_add(n, m);
    lemma_weight_zero();
    lemma_weight_mono(0, m);
    lemma_mul_strict_inequality(x as int, weight(n) as int, weight(m) as int);
}

// item: Q04.H4v S5
pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    broadcast use group_bignat_bounds;

    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
            forall|j: int| i <= j < n ==> a@[j] == b@[j],
        decreases i,
    {
        i = i - 1;
    }
    if i == 0 {
        proof {
            assert(a@ =~= b@);
        }
        Ordering::Equal
    } else if a.limbs[i - 1] < b.limbs[i - 1] {
        proof {
            lemma_lt_at(a@, b@, (i - 1) as int);
        }
        Ordering::Less
    } else {
        proof {
            lemma_lt_at(b@, a@, (i - 1) as int);
        }
        Ordering::Greater
    }
}

// item: Q04.H5v S5
pub proof fn lemma_value_times_limb(x: nat, d: nat, n: nat)
    requires
        x < weight(n),
        d < BASE,
    ensures
        x * d < weight(n + 1),
{
    lemma_weight_succ(n);
    let w = weight(n);
    assert(x * d < w * BASE) by (nonlinear_arith)
        requires
            x < w,
            d < BASE,
    ;
}

} // verus!
```

`root/verus/q/q04_proof_craft/src/exit.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use qg_bignat_l3::*;

verus! {

// item: Q04.X1v S5
pub proof fn lemma_limb_square(x: u64)
    ensures
        (x as nat) * (x as nat) < weight(2),
{
    lemma_weight_zero();
    lemma_weight_succ(0);
    lemma_weight_succ(1);
    calc! {
        (<)
        (x as nat) * (x as nat); { assert((x as nat) * (x as nat) < BASE * BASE) by (nonlinear_arith) requires (x as nat) < BASE; }
        BASE * BASE;
        (==) { }
        BASE * weight(1);
        (==) { }
        weight(2);
    }
}

// item: Q04.X2v S5
pub fn fits_one_limb(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() < BASE),
{
    broadcast use group_bignat_bounds;

    proof {
        lemma_weight_zero();
        lemma_weight_succ(0);
    }
    a.limbs.len() <= 1
}

} // verus!
```

The shipped form of H4v (gated: every mode fails), as `h4v_ship2.rs`:

`root/verus/q/q04_proof_craft/src/h4v_ship2.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
use core::cmp::Ordering;

verus! {

pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    #[verifier::proof_note("Q04.H4v")]
    assume(false);
    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
        decreases i,
    {
        i = i - 1;
    }
    if i == 0 {
        proof {
            assert(a@ =~= b@);
        }
        Ordering::Equal
    } else if a.limbs[i - 1] < b.limbs[i - 1] {
        proof {
            lemma_lt_at(a@, b@, (i - 1) as int);
        }
        Ordering::Less
    } else {
        proof {
            lemma_lt_at(b@, a@, (i - 1) as int);
        }
        Ordering::Greater
    }
}

} // verus!
```

### A.7 Q04 agent files (solved)
`root/dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` (unchanged)

```dafny
module {:disableNonlinearArithmetic} Q04_AgentRetriever {
  import opened QG_L1_BigNat
  import opened QG_L3_BigNat
  import Mul = Std.Arithmetic.Mul
  import DivMod = Std.Arithmetic.DivMod
  import Power = Std.Arithmetic.Power

  lemma ScaleStrict(x: nat, y: nat, z: nat)
    requires x < y && z > 0
    ensures x * z < y * z
  {
    Mul.LemmaMulStrictInequality(x, y, z);
  }

  lemma HighLimbOfShift(a: nat, b: nat, c: nat)
    requires b < c
    ensures (a * c + b) / c == a
  {
    DivMod.LemmaFundamentalDivModConverse(a * c + b, c, a, b);
  }

  lemma ProductMod(x: nat, y: nat, m: nat)
    requires m > 0
    ensures (x % m) * (y % m) % m == x * y % m
  {
    DivMod.LemmaMulModNoop(x, y, m);
  }
}
```

The Verus agent file with the replaced goals (`--gate`: 3 verified):

`root/verus/q/q04_proof_craft/src/agent.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::power::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;
verus! {
pub proof fn lemma_pow_of_pow(n: nat)
    ensures
        pow(pow(BASE as int, n), 2) == pow(BASE as int, 2 * n),
{
    lemma_pow_multiplies(BASE as int, n, 2);
}
pub proof fn lemma_low_limb_of_power(x: int, e: nat)
    ensures
        pow(x % (BASE as int), e) % (BASE as int) == pow(x, e) % (BASE as int),
{
    lemma_pow_mod_noop(x, e, BASE as int);
}
pub proof fn lemma_pow_mod_base(n: nat)
    requires
        n > 0,
    ensures
        pow(BASE as int, n) % (BASE as int) == 0,
{
    lemma_pow_adds(BASE as int, (n - 1) as nat, 1);
    lemma_pow1(BASE as int);
    lemma_mod_multiples_basic(pow(BASE as int, (n - 1) as nat), BASE as int);
}
} // verus!
```

### A.8 Q05 std file (the twin, and the shipped forms of H1d, H4d, H5d and H2d)
`root/dafny/Q/Q05_Frames/std/Q05_Frames.dfy`

```dafny
module Q05_Frames {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened Std.Wrappers

  // ---------------------------------------------------------------------------
  // Given: a growable stack of limbs, with dynamic frames
  // ---------------------------------------------------------------------------
  class LimbStack {
    var a: array<nat>
    var n: nat
    ghost var Contents: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && Contents == a[..n]
    }

    constructor (cap: nat)
      requires cap > 0
      ensures Valid() && fresh(Repr) && Contents == []
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    // W1d-style: a read-only query
    function Size(): nat
      reads this, Repr
      requires Valid()
      ensures Size() == |Contents|
    {
      n
    }

    // item: Q05.H1d S6  (exec hole in the shipped file)
    method Push(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          invariant 0 <= i <= n <= a.Length < b.Length
          invariant b[..i] == a[..i]
          modifies b
        {
          b[i] := a[i];
          i := i + 1;
        }
        a := b;
        Repr := Repr + {b};
      }
      a[n] := x;
      n := n + 1;
      Contents := Contents + [x];
    }

    // item: Q05.H2d S6  (annotation hole: modifies + frame ensures)
    method Pop() returns (x: nat)
      requires Valid() && |Contents| > 0
      modifies this
      ensures Valid() && Repr == old(Repr)
      ensures x == old(Contents)[|old(Contents)| - 1] && Contents == old(Contents)[..|old(Contents)| - 1]
    {
      n := n - 1;
      x := a[n];
      Contents := Contents[..n];
    }
  }

  method PopCheck(s: LimbStack, t: LimbStack)
    requires s.Valid() && t.Valid() && s.Repr !! t.Repr && |s.Contents| > 0
    modifies s.Repr
  {
    var tc := t.Contents;
    var x := s.Pop();
    assert t.Valid() && t.Contents == tc && s.Repr !! t.Repr;
  }

  // ---------------------------------------------------------------------------
  // item: Q05.H3d S7  (annotation hole in a by-method body)
  // ---------------------------------------------------------------------------
  function CmpFast(a: seq<nat>, b: seq<nat>): int
  {
    Cmp(a, b)
  } by method {
    var i := if |a| < |b| then |b| else |a|;
    var r := 0;
    assert Drop(a, i) == [] && Drop(b, i) == [];
    while i > 0
      invariant 0 <= i <= (if |a| < |b| then |b| else |a|)
      invariant r == Cmp(Drop(a, i), Drop(b, i))
      decreases i
    {
      i := i - 1;
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      DropStep(a, i);
      DropStep(b, i);
      if r == 0 {
        r := if x < y then -1 else if x > y then 1 else 0;
      }
    }
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    return r;
  }

  // ---------------------------------------------------------------------------
  // Given: bit counts
  // ---------------------------------------------------------------------------
  function BitCount(x: nat): nat
    decreases x
  {
    if x == 0 then 0 else x % 2 + BitCount(x / 2)
  }

  function Ones(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else BitCount(s[0]) + Ones(s[1..])
  }

  // item: Q05.H4d S7  (exec hole: one loop, lexicographic decreases)
  method CountOnes(s: seq<nat>) returns (c: nat)
    ensures c == Ones(s)
  {
    var i := 0;
    var x := 0;
    c := 0;
    while x > 0 || i < |s|
      invariant 0 <= i <= |s|
      invariant c + BitCount(x) + Ones(s[i..]) == Ones(s)
      decreases |s| - i, x
    {
      if x > 0 {
        c := c + x % 2;
        x := x / 2;
      } else {
        assert s[i..][1..] == s[i + 1..];
        x := s[i];
        i := i + 1;
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Given: decimal digits
  // ---------------------------------------------------------------------------
  predicate AllDigits(s: string)
  {
    forall i | 0 <= i < |s| :: '0' <= s[i] <= '9'
  }

  function DecValue(s: string): nat
    requires AllDigits(s)
    decreases |s|
  {
    if |s| == 0 then 0 else DecValue(s[..|s| - 1]) * 10 + (s[|s| - 1] as nat - '0' as nat)
  }

  function Digit(c: char): Result<nat, string>
  {
    if '0' <= c <= '9' then Success(c as nat - '0' as nat) else Failure("not a digit")
  }

  // item: Q05.H5d S6  (exec hole: one loop, `:-` on Digit)
  method ParseDecimal(s: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|s| > 0 && AllDigits(s))
    ensures r.Success? ==> AllDigits(s) && r.value == DecValue(s)
  {
    if |s| == 0 {
      return Failure("empty");
    }
    var v := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant AllDigits(s[..i])
      invariant v == DecValue(s[..i])
    {
      var d :- Digit(s[i]);
      assert s[..i + 1][..i] == s[..i];
      v := v * 10 + d;
      i := i + 1;
    }
    assert s[..|s|] == s;
    return Success(v);
  }
}
```

The shipped forms (`probe/q05_shipped.dfy`: each green with one `assume` hole; `PushRefNoFrame` shows that the loop frame is needed):

`probe/q05_shipped.dfy`

```dafny
module Q05_Probe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened Std.Wrappers

  class LimbStack {
    var a: array<nat>
    var n: nat
    ghost var Contents: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && Contents == a[..n]
    }

    constructor (cap: nat)
      requires cap > 0
      ensures Valid() && fresh(Repr) && Contents == []
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    method PushShipped(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      assume false;
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          decreases n - i
        {
          b[i] := a[i];
          i := i + 1;
        }
        a := b;
        Repr := Repr + {b};
      }
      a[n] := x;
      n := n + 1;
      Contents := Contents + [x];
    }

    method PushRefNoFrame(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          invariant 0 <= i <= n <= a.Length < b.Length
          invariant b[..i] == a[..i]
          decreases n - i
        {
          b[i] := a[i];
          i := i + 1;
        }
        a := b;
        Repr := Repr + {b};
      }
      a[n] := x;
      n := n + 1;
      Contents := Contents + [x];
    }

    method PushRef(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          invariant 0 <= i <= n <= a.Length < b.Length
          invariant b[..i] == a[..i]
          modifies b
          decreases n - i
        {
          b[i] := a[i];
          i := i + 1;
        }
        a := b;
        Repr := Repr + {b};
      }
      a[n] := x;
      n := n + 1;
      Contents := Contents + [x];
    }
  }

  function BitCount(x: nat): nat
    decreases x
  {
    if x == 0 then 0 else x % 2 + BitCount(x / 2)
  }

  function Ones(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else BitCount(s[0]) + Ones(s[1..])
  }

  method CountOnesShipped(s: seq<nat>) returns (c: nat)
    ensures c == Ones(s)
  {
    assume false;
    var i := 0;
    var x := 0;
    c := 0;
    while x > 0 || i < |s|
    {
      if x > 0 {
        c := c + x % 2;
        x := x / 2;
      } else {
        assert s[i..][1..] == s[i + 1..];
        x := s[i];
        i := i + 1;
      }
    }
  }

  predicate AllDigits(s: string)
  {
    forall i | 0 <= i < |s| :: '0' <= s[i] <= '9'
  }

  function DecValue(s: string): nat
    requires AllDigits(s)
    decreases |s|
  {
    if |s| == 0 then 0 else DecValue(s[..|s| - 1]) * 10 + (s[|s| - 1] as nat - '0' as nat)
  }

  function Digit(c: char): Result<nat, string>
  {
    if '0' <= c <= '9' then Success(c as nat - '0' as nat) else Failure("not a digit")
  }

  method ParseDecimalShipped(s: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|s| > 0 && AllDigits(s))
    ensures r.Success? ==> AllDigits(s) && r.value == DecValue(s)
  {
    assume false;
    var v := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant AllDigits(s[..i])
      invariant v == DecValue(s[..i])
    {
    }
    assert s[..|s|] == s;
    return Success(v);
  }

  method ParseDecimalRef(s: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|s| > 0 && AllDigits(s))
    ensures r.Success? ==> AllDigits(s) && r.value == DecValue(s)
  {
    if |s| == 0 {
      return Failure("empty");
    }
    var v := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant AllDigits(s[..i])
      invariant v == DecValue(s[..i])
    {
      var d :- Digit(s[i]);
      assert s[..i + 1][..i] == s[..i];
      v := v * 10 + d;
      i := i + 1;
    }
    assert s[..|s|] == s;
    return Success(v);
  }
}
```

The shipped `Pop` of H2d (`freeze/ship.dfy`, excerpt; green with one hole):

`freeze/ship.dfy`

```dafny
    method Pop() returns (x: nat)
      requires Valid() && |Contents| > 0
      ensures x == old(Contents)[|old(Contents)| - 1] && Contents == old(Contents)[..|old(Contents)| - 1]
    {
      assume false;
      n := n - 1;
      x := a[n];
      Contents := Contents[..n];
    }
  }
```

### A.9 Q05 Dafny exit file
`root/dafny/Q/Q05_Frames/exit/Q05_Exit.dfy`

```dafny
module Q05_Exit {
  import opened QG_L1_BigNat
  import opened Std.Wrappers

  // item: Q05.X1d S7
  function CountFull(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])
  } by method {
    var c := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s|
      invariant c == CountFull(s[i..])
    {
      i := i - 1;
      assert s[i..][1..] == s[i + 1..];
      if s[i] == BASE - 1 {
        c := c + 1;
      }
    }
    assert s[0..] == s;
    return c;
  }

  // given for X2d
  predicate AllDigits(s: string)
  {
    forall i | 0 <= i < |s| :: '0' <= s[i] <= '9'
  }

  method ParseField(t: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|t| > 0 && AllDigits(t))
  {
    if |t| == 0 {
      return Failure("empty");
    }
    var v: nat := 0;
    var i := 0;
    while i < |t|
      invariant 0 <= i <= |t|
      invariant AllDigits(t[..i])
    {
      if !('0' <= t[i] <= '9') {
        return Failure("not a digit");
      }
      v := v * 10 + (t[i] as nat - '0' as nat);
      i := i + 1;
    }
    assert t[..|t|] == t;
    return Success(v);
  }

  // item: Q05.X2d S6
  method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)
    requires k <= |s|
    ensures r.Success? <==> (|s[..k]| > 0 && AllDigits(s[..k]) && |s[k..]| > 0 && AllDigits(s[k..]))
  {
    var a :- ParseField(s[..k]);
    var b :- ParseField(s[k..]);
    return Success((a, b));
  }
}
```
`d/q05/x1d_ref.dfy`

```dafny
module X1R {
  const BASE: nat := 18446744073709551616
  function CountFull(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])
  } by method {
    var c := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s|
      invariant c == CountFull(s[i..])
    {
      i := i - 1;
      assert s[i..][1..] == s[i + 1..];
      if s[i] == BASE - 1 {
        c := c + 1;
      }
    }
    assert s[0..] == s;
    return c;
  }
}
```

### A.10 Q05 Verus crate
`root/verus/q/q05_frames/src/lib.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

// ---- given: a bounded stack the module owns ----
pub struct Full;

pub struct LimbStack {
    pub v: Vec<u64>,
    pub cap: usize,
}

impl View for LimbStack {
    type V = Seq<u64>;

    open spec fn view(&self) -> Seq<u64> {
        self.v@
    }
}

impl LimbStack {
    pub open spec fn inv(&self) -> bool {
        self.v@.len() <= self.cap
    }

    pub fn new(cap: usize) -> (r: Self)
        ensures
            r.inv(),
            r@ == Seq::<u64>::empty(),
            r.cap == cap,
    {
        LimbStack { v: Vec::new(), cap }
    }

    // item: Q05.H2v S6
    pub fn try_push(&mut self, x: u64) -> (r: Result<(), Full>)
        requires
            old(self).inv(),
        ensures
            final(self).inv(),
            final(self).cap == old(self).cap,
            r is Ok <==> old(self)@.len() < old(self).cap,
            r is Ok ==> final(self)@ == old(self)@.push(x),
            r is Err ==> final(self)@ == old(self)@,
    {
        if self.v.len() < self.cap {
            self.v.push(x);
            Ok(())
        } else {
            Err(Full)
        }
    }
}

// item: Q05.H1v S6
pub fn shift_up(a: &mut BigNat)
    requires
        old(a).wf(),
    ensures
        final(a).wf(),
        final(a).to_nat() == BASE * old(a).to_nat(),
{
    if a.limbs.len() > 0 {
        a.limbs.insert(0, 0);
        proof {
            assert(a@.drop_first() =~= old(a)@);
        }
    }
}

// ---- given: bit counts ----
pub open spec fn bit_count(x: nat) -> nat
    decreases x,
{
    if x == 0 {
        0
    } else {
        x % 2 + bit_count(x / 2)
    }
}

pub open spec fn ones(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        bit_count(s[0] as nat) + ones(s.drop_first())
    }
}

// item: Q05.H4v S7
pub fn count_ones(v: &Vec<u64>) -> (c: u64)
    requires
        ones(v@) <= u64::MAX,
    ensures
        c == ones(v@),
{
    let mut i: usize = 0;
    let mut x: u64 = 0;
    let mut c: u64 = 0;
    proof {
        assert(v@.subrange(0, v.len() as int) =~= v@);
    }
    while x > 0 || i < v.len()
        invariant
            i <= v.len(),
            c + bit_count(x as nat) + ones(v@.subrange(i as int, v.len() as int)) == ones(v@),
            ones(v@) <= u64::MAX,
        decreases v.len() - i, x,
    {
        if x > 0 {
            c = c + x % 2;
            x = x / 2;
        } else {
            proof {
                assert(v@.subrange(i as int, v.len() as int).drop_first()
                    =~= v@.subrange(i + 1, v.len() as int));
            }
            x = v[i];
            i = i + 1;
        }
    }
    c
}

// ---- given: decimal digits ----
pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

pub open spec fn all_digits(s: Seq<u8>) -> bool {
    forall|i: int| 0 <= i < s.len() ==> is_digit(#[trigger] s[i])
}

pub open spec fn dec_value(s: Seq<u8>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        dec_value(s.drop_last()) * 10 + (s.last() - 48) as nat
    }
}

pub fn digit(c: u8) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> is_digit(c),
        r is Ok ==> r->Ok_0 == c - 48,
        r is Err ==> r->Err_0 == ParseError::NotDigit,
{
    if 48 <= c && c <= 57 {
        Ok((c - 48) as u64)
    } else {
        Err(ParseError::NotDigit)
    }
}

pub fn mul10_add(acc: u64, d: u64) -> (r: Result<u64, ParseError>)
    requires
        d < 10,
    ensures
        r is Ok <==> acc * 10 + d <= u64::MAX,
        r is Ok ==> r->Ok_0 == acc * 10 + d,
        r is Err ==> r->Err_0 == ParseError::Overflow,
{
    if acc <= (u64::MAX - d) / 10 {
        Ok(acc * 10 + d)
    } else {
        Err(ParseError::Overflow)
    }
}

// item: Q05.H5v S6
pub fn parse_decimal(s: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok ==> s@.len() > 0 && all_digits(s@) && r->Ok_0 == dec_value(s@),
        (r is Err && r->Err_0 == ParseError::Empty) <==> s@.len() == 0,
        r is Err && r->Err_0 == ParseError::NotDigit ==> !all_digits(s@),
        r is Err && r->Err_0 == ParseError::Overflow ==> exists|k: int|
            0 < k <= s@.len() && all_digits(s@.subrange(0, k)) && #[trigger] dec_value(s@.subrange(0, k)) > u64::MAX,
{
    if s.len() == 0 {
        return Err(ParseError::Empty);
    }
    let mut v: u64 = 0;
    let mut i: usize = 0;
    while i < s.len()
        invariant
            0 < s@.len(),
            i <= s@.len(),
            all_digits(s@.subrange(0, i as int)),
            v == dec_value(s@.subrange(0, i as int)),
        decreases s.len() - i,
    {
        let d = digit(s[i])?;
        proof {
            assert(s@.subrange(0, i + 1).drop_last() =~= s@.subrange(0, i as int));
            assert(dec_value(s@.subrange(0, i + 1)) == v * 10 + d);
        }
        v = mul10_add(v, d)?;
        i = i + 1;
    }
    proof {
        assert(s@.subrange(0, s@.len() as int) =~= s@);
    }
    Ok(v)
}

} // verus!
```
`root/verus/q/q05_frames/src/t1v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
verus! {
pub open spec fn odometer(lo: nat, hi: nat) -> nat
    decreases hi, lo,
{
    if lo > 0 {
        1 + odometer((lo - 1) as nat, hi)
    } else if hi > 0 {
        1 + odometer(9, (hi - 1) as nat)
    } else {
        0
    }
}
pub proof fn odometer_check() {
    assert(odometer(2, 1) == 12) by (compute_only);
}
} // verus!
```
`d/q05/t1d.dfy`

```dafny
module T1 {
  function Odometer(lo: nat, hi: nat): nat
    decreases hi, lo
  {
    if lo > 0 then 1 + Odometer(lo - 1, hi)
    else if hi > 0 then 1 + Odometer(9, hi - 1)
    else 0
  }
  lemma OdometerCheck()
    ensures Odometer(2, 1) == 12
  {
  }
}
```

### A.11 Q05 Verus exit file (with `transfer`)
`root/verus/q/q05_frames/src/exit.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

pub struct Short;

pub struct Account {
    pub bal: u64,
    pub cap: u64,
}

// item: Q05.X1v S6
pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
    requires
        old(from).bal <= old(from).cap,
        old(to).bal <= old(to).cap,
    ensures
        final(from).cap == old(from).cap,
        final(to).cap == old(to).cap,
        final(from).bal <= final(from).cap,
        final(to).bal <= final(to).cap,
        r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap),
        r is Ok ==> final(from).bal == old(from).bal - k && final(to).bal == old(to).bal + k,
        r is Err ==> final(from).bal == old(from).bal && final(to).bal == old(to).bal,
{
    if k <= from.bal && k <= to.cap - to.bal {
        from.bal = from.bal - k;
        to.bal = to.bal + k;
        Ok(())
    } else {
        Err(Short)
    }
}

pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

pub fn parse_digit(t: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> (t@.len() == 1 && is_digit(t@[0])),
        r is Ok ==> r->Ok_0 == t@[0] - 48,
{
    if t.len() != 1 {
        return Err(ParseError::Empty);
    }
    if t[0] < 48 || t[0] > 57 {
        return Err(ParseError::NotDigit);
    }
    Ok((t[0] - 48) as u64)
}

// item: Q05.X2v S6
pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)
    ensures
        r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0])),
{
    let x = parse_digit(a)?;
    let y = parse_digit(b)?;
    Ok((x, y))
}

} // verus!
```

### A.12 Q05 agent files: planted and repaired
Receipts for each state are in §3.4.

`agent/planted.dfy (as shipped)`

```dafny
module {:options "--function-syntax:4"} Q05_AgentInfra {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import Std.Wrappers

  // Given: the larger of two numerals, chosen by the layer's comparison.
  method Larger(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    ensures r == a || r == b
  {
    r := if Cmp(a, b) < 0 then b else a;
  }

  // Given: a numeral's limb count.
  function Width(a: seq<nat>): nat
  {
    |a|
  }
}
```

`agent/repaired.dfy (the twin)`

```dafny
module Q05_AgentInfra {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Std.Wrappers

  // Given: the larger of two numerals, chosen by the layer's comparison.
  method Larger(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    ensures r == a || r == b
  {
    r := if Cmp(a, b) < 0 then b else a;
  }

  // Given: a numeral's limb count.
  function Width(a: seq<nat>): nat
  {
    |a|
  }
}
```

`agent/planted.rs (as shipped)`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

/// Given: one more than a numeral.
pub fn one_more(a: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + 1,
{
    add_limb(a, 1)
}

} // verus!

/// Given: the number of limbs of a numeral.
pub fn limb_count(a: &BigNat) -> usize {
    a.limbs.len()
}
```

`agent/repaired.rs (the twin)`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

/// Given: one more than a numeral.
pub fn one_more(a: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + 1,
{
    add_limb(a, 1)
}

/// Given: the number of limbs of a numeral.
pub fn limb_count(a: &BigNat) -> usize {
    a.limbs.len()
}

} // verus!
```

### A.13 Q06 std file (the twin; the property suite live)
`root/dafny/Q/Q06_Machine/std/Q06_Machine.dfy`

```dafny
module Q06_Machine {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  // item: Q06.T1d S11
  lemma SecondLimb(s: seq<nat>)
    requires |s| > 1
    requires forall k {:trigger Head(Drop(s, k))} | 0 <= k < |s| :: Head(Drop(s, k)) < 100
    ensures s[1] < 100
  {
    assert Head(Drop(s, 1)) < 100;
  }

  // item: Q06.H1d S11
  lemma FirstPrefix(s: seq<nat>)
    requires |s| >= 1
    requires forall k {:trigger Pow(k)} | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
    ensures ToNat(s[..1]) < BASE
  {
    assert Pow(1) == BASE;
  }

  // item: Q06.H2d S11
  opaque function Pack(lo: nat, hi: nat): nat
  {
    lo + BASE * hi
  }

  lemma PackToNat(lo: nat, hi: nat)
    ensures Pack(lo, hi) == ToNat([lo, hi])
  {
    reveal Pack();
    ToNatCons(lo, [hi]);
    ToNatSingleton(hi);
    assert [lo] + [hi] == [lo, hi];
  }

  // item: Q06.H3d S11
  lemma TwoShifts(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Mul.LemmaMulUpperBound(x, p - 1, y, p - 1);
    assert (p - 1) * (p - 1) < p * p;
  }

  // item: Q06.H4d S12 (given helpers, the hole, the suite)
  function RefSplit(a: nat, b: nat): (nat, nat)
  {
    ((a + b) % BASE, (a + b) / BASE)
  }

  method CheckSplit(f: (nat, nat) -> (nat, nat), samples: seq<(nat, nat)>) returns (ok: bool)
    ensures ok <==> forall k | 0 <= k < |samples| :: f(samples[k].0, samples[k].1) == RefSplit(samples[k].0, samples[k].1)
  {
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant forall j | 0 <= j < k :: f(samples[j].0, samples[j].1) == RefSplit(samples[j].0, samples[j].1)
      decreases |samples| - k
    {
      if f(samples[k].0, samples[k].1) != RefSplit(samples[k].0, samples[k].1) {
        return false;
      }
      k := k + 1;
    }
    return true;
  }

  function Boundary(): seq<(nat, nat)>
  {
    [(0, 0), (1, BASE - 1), (BASE - 1, 1), (BASE - 1, BASE - 1), (BASE / 2, BASE / 2)]
  }

  function AddCarryA(a: nat, b: nat): (nat, nat)
  {
    if a + b < BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  function AddCarryB(a: nat, b: nat): (nat, nat)
  {
    if a + b <= BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  @Test
  method GoodPasses() {
    var ok := CheckSplit(AddCarryA, Boundary());
    expect ok;
  }

  @Test
  method PlantedRejected() {
    var ok := CheckSplit(AddCarryB, Boundary());
    expect !ok;
  }

}
```

### A.14 Q06 Dafny exit file
`root/dafny/Q/Q06_Machine/exit/Q06_Exit.dfy`

```dafny
module Q06_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import DivMod = Std.Arithmetic.DivMod

  // item: Q06.X1d S12
  method FirstDisagreement(f: nat -> int, g: nat -> int, samples: seq<nat>) returns (r: int)
    ensures -1 <= r < |samples|
    ensures r == -1 <==> forall k | 0 <= k < |samples| :: f(samples[k]) == g(samples[k])
    ensures r >= 0 ==> f(samples[r]) != g(samples[r])
  {
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant forall j | 0 <= j < k :: f(samples[j]) == g(samples[j])
      decreases |samples| - k
    {
      if f(samples[k]) != g(samples[k]) {
        return k;
      }
      k := k + 1;
    }
    return -1;
  }

  // given above X2d
  opaque function Low(x: nat, m: nat): nat
    requires m > 0
  {
    x % m
  }

  // item: Q06.X2d S11
  // An attempt, over a transparent copy of Low (it does not verify at the pinned limit):
  //   function LowT(x: nat, m: nat): nat requires m > 0 { x % m }
  //   lemma LowOfShiftT(x: nat, y: nat, m: nat) requires m > 0 ensures LowT(x + m * y, m) == LowT(x, m) {}
  lemma LowOfShift(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Low(x + m * y, m) == Low(x, m)
  {
    reveal Low();
    DivMod.LemmaModMultiplesVanish(y, x, m);
  }
}
```

### A.15 Q06 Verus crate (the twin; the property suite live)
`root/verus/q/q06_machine/src/lib.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l3::*;

verus! {

// item: Q06.T1v S11
pub proof fn lemma_second_limb(s: Seq<u64>)
    requires
        s.len() > 1,
        forall|k: int| 0 <= k < s.len() ==> #[trigger] limb_at(s, k) < 100,
    ensures
        s[1] < 100,
{
    assert(limb_at(s, 1) < 100);
}

// item: Q06.H1v S11
pub proof fn lemma_first_prefix(s: Seq<u64>)
    requires
        s.len() >= 1,
        forall|k: nat| k <= s.len() ==> seq_to_nat(s.subrange(0, k as int)) < #[trigger] weight(k),
    ensures
        seq_to_nat(s.subrange(0, 1)) < BASE,
{
    lemma_weight_zero();
    lemma_weight_succ(0);
    assert(weight(1) == BASE);
}

// item: Q06.H2v S11
#[verifier::opaque]
pub open spec fn pack(lo: u64, hi: u64) -> nat {
    lo as nat + BASE * hi as nat
}

pub proof fn lemma_pack_to_nat(lo: u64, hi: u64)
    ensures
        pack(lo, hi) == seq_to_nat(seq![lo, hi]),
{
    reveal(pack);
    let s = seq![lo, hi];
    assert(s.drop_first() =~= seq![hi]);
    assert(seq![hi].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(Seq::<u64>::empty()) == 0);
    assert(seq_to_nat(seq![hi]) == hi as nat);
}

// item: Q06.H3v S11
pub proof fn lemma_seq_to_nat_append(a: Seq<u64>, b: Seq<u64>)
    ensures
        seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        lemma_seq_to_nat_append(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(a.drop_first()) as int, (weight(k) * seq_to_nat(b)) as int);
    } else {
        lemma_weight_zero();
        assert(a + b =~= b);
    }
}

// item: Q06.H4v S12 (the given helper above the hole)
/// Given: one sample's check, in u128 arithmetic.
pub fn split_matches(a: u64, b: u64, lo: u64, hi: u64) -> (r: bool)
    ensures
        r == (lo as nat + hi as nat * BASE == a as nat + b as nat),
{
    lo as u128 + (hi as u128) * 0x1_0000_0000_0000_0000u128 == a as u128 + b as u128
}

pub fn check_split_results(samples: &Vec<(u64, u64)>, got: &Vec<(u64, u64)>) -> (ok: bool)
    requires
        got.len() == samples.len(),
    ensures
        ok == (forall|k: int| 0 <= k < samples.len() ==>
            (#[trigger] got@[k]).0 as nat + got@[k].1 as nat * BASE == samples@[k].0 as nat + samples@[k].1 as nat),
{
    let mut k: usize = 0;
    while k < samples.len()
        invariant
            k <= samples.len(),
            got.len() == samples.len(),
            forall|j: int| 0 <= j < k ==>
                (#[trigger] got@[j]).0 as nat + got@[j].1 as nat * BASE == samples@[j].0 as nat + samples@[j].1 as nat,
        decreases samples.len() - k,
    {
        if !split_matches(samples[k].0, samples[k].1, got[k].0, got[k].1) {
            return false;
        }
        k = k + 1;
    }
    true
}


pub fn add_carry_a(a: u64, b: u64) -> (u64, u64) {
    let s = a.wrapping_add(b);
    (s, if s < a { 1 } else { 0 })
}

pub fn add_carry_b(a: u64, b: u64) -> (u64, u64) {
    let s = a.wrapping_add(b);
    (s, if s <= a { 1 } else { 0 })
}

} // verus!

#[cfg(test)]
mod props {
    use super::*;
    fn boundary() -> Vec<(u64, u64)> {
        vec![(0, 0), (1, u64::MAX), (u64::MAX, 1), (u64::MAX, u64::MAX), (1u64 << 63, 1u64 << 63)]
    }
    fn run(f: fn(u64, u64) -> (u64, u64)) -> bool {
        let s = boundary();
        let got: Vec<(u64, u64)> = s.iter().map(|&(a, b)| f(a, b)).collect();
        check_split_results(&s, &got)
    }
    #[test]
    fn good_passes() { assert!(run(add_carry_a)); }
    #[test]
    fn planted_rejected() { assert!(!run(add_carry_b)); }
}
```

### A.16 Q06 Verus exit file
`root/verus/q/q06_machine/src/exit.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;

verus! {

// item: Q06.X1v S12
pub fn first_disagreement(xs: &Vec<bool>, ys: &Vec<bool>) -> (r: Option<usize>)
    requires
        xs.len() == ys.len(),
    ensures
        r is None <==> (forall|k: int| 0 <= k < xs.len() ==> #[trigger] xs@[k] == ys@[k]),
        r is Some ==> r->Some_0 < xs.len() && xs@[r->Some_0 as int] != ys@[r->Some_0 as int],
{
    let mut k: usize = 0;
    while k < xs.len()
        invariant
            k <= xs.len(),
            xs.len() == ys.len(),
            forall|j: int| 0 <= j < k ==> #[trigger] xs@[j] == ys@[j],
        decreases xs.len() - k,
    {
        if xs[k] != ys[k] {
            return Some(k);
        }
        k = k + 1;
    }
    None
}


// given above X2v
#[verifier::opaque]
pub open spec fn low(x: nat, m: nat) -> nat
    recommends m > 0,
{
    x % m
}

// item: Q06.X2v S11
// An attempt (it does not verify at the pinned limit):
//     reveal(low);
//     assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by {
//         reveal(low);
//         lemma_mod_add_multiples_vanish(t as int, m as int);
//     }
pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    lemma_mod_multiples_vanish(y as int, x as int, m as int);
}


} // verus!
```

### A.17 Q06 property-suite probes
Merged into A.13 and A.15: both twins carry their suites live (`vcheck --test`: 2 passed in each language).

### A.18 Python sketch (fvh core subset and the Q06 reference)
`py/sketch/fvh/stats.py`

```python
"""Sketch of fvh.stats (DV3a plan lane): the two functions Q06 composes."""
from math import comb, sqrt
from statistics import NormalDist


def pass_at_k(n: int, c: int, k: int) -> float:
    if not (0 <= c <= n) or not (1 <= k <= n):
        raise ValueError("need 0 <= c <= n and 1 <= k <= n")
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n < 1 or not (0 <= successes <= n) or not (0 < confidence < 1):
        raise ValueError("need n >= 1, 0 <= successes <= n, 0 < confidence < 1")
    z = NormalDist().inv_cdf(1 - (1 - confidence) / 2)
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))
```
`py/sketch/fvh/records.py`

```python
"""Sketch of fvh.records (DV3a plan lane)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RunRecord:
    task_id: str
    arm: str
    attempt: int
    lang: str
    verdict: str
    holes: int
    errors: int
    verified_count: int

    @property
    def success(self) -> bool:
        return self.verdict == "verified" and self.holes == 0


def first_attempts(records):
    return [r for r in records if r.attempt == 1]
```
`py/sketch/fvh/holes.py`

```python
"""Sketch of fvh.holes (DV3a plan lane): AST-counted Python holes."""
import ast
import re
import sys

MARK = re.compile(r"^\s*#\s*item:\s*(\S+)")


def _is_hole(fn, item):
    body = fn.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], ast.Raise):
        return False
    exc = body[0].exc
    return (isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name)
            and exc.func.id == "NotImplementedError" and len(exc.args) == 1
            and isinstance(exc.args[0], ast.Constant) and exc.args[0].value == item)


def count_holes(source: str):
    lines = source.split("\n")
    marks = {}
    cur = None
    for i, line in enumerate(lines, 1):
        m = MARK.match(line)
        if m:
            cur = m.group(1)
        marks[i] = cur
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            item = marks.get(node.lineno)
            if item and _is_hole(node, item):
                out.append((item, node.name, node.lineno))
    return sorted(out, key=lambda h: h[2])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f"{f}: {len(count_holes(open(f).read()))} hole(s)")
```
`py/sketch/q/fvh_q/q06_stats.py`

```python
"""Reference sketch of harness/q/fvh_q/q06_stats.py (author-only)."""
from collections import defaultdict
from typing import Sequence

from fvh import stats
from fvh.records import RunRecord


# item: Q06.H5py S9
def record_from_vcheck(doc: dict, task_id: str, arm: str, attempt: int) -> RunRecord:
    """One run record from one `scripts/vcheck --json` document."""
    errors = sum(1 for d in doc.get("diagnostics", []) if d.get("severity") == "error")
    return RunRecord(task_id, arm, attempt, doc["lang"], doc["verdict"], len(doc.get("holes", [])),
                     errors, doc.get("verified_count", 0))


# item: Q06.H6py S13
def pass_rate_ci(records: Sequence[RunRecord], arm: str, confidence: float = 0.95):
    """First-attempt successes, the number of tasks, and the Wilson interval."""
    first = {}
    for r in records:
        if r.arm == arm and r.attempt == 1:
            first[r.task_id] = r
    n = len(first)
    s = sum(1 for r in first.values() if r.success)
    return s, n, stats.wilson_interval(s, n, confidence)


# item: Q06.H7py S13
def pass_at_k_by_task(records: Sequence[RunRecord], arm: str, k: int) -> float:
    """The mean over tasks of the unbiased pass@k."""
    by_task = defaultdict(list)
    for r in records:
        if r.arm == arm:
            by_task[r.task_id].append(r)
    vals = [stats.pass_at_k(len(rs), sum(1 for r in rs if r.success), k) for rs in by_task.values()]
    return sum(vals) / len(vals)
```
`py/sketch/check.py`

```python
import sys
sys.path[:0] = [".", "q"]
from fvh import stats, holes
from fvh.records import RunRecord
from fvh_q import q06_stats as q
lo, hi = stats.wilson_interval(14, 20)
print("wilson 14/20:", round(lo, 4), round(hi, 4), "half-width", round((hi - lo) / 2, 4))
print("pass@3 n=10 c=3:", round(stats.pass_at_k(10, 3, 3), 4))
doc_ok = {"lang": "dafny", "verdict": "verified", "holes": [], "diagnostics": [], "verified_count": 31}
doc_bad = {"lang": "verus", "verdict": "failed", "holes": [], "verified_count": 2,
           "diagnostics": [{"severity": "error"}, {"severity": "warning"}]}
r1 = q.record_from_vcheck(doc_ok, "t1", "A", 1); r2 = q.record_from_vcheck(doc_bad, "t2", "A", 1)
r3 = q.record_from_vcheck(doc_ok, "t2", "A", 2)
print(r1.success, r2.success, r2.errors)
print(q.pass_rate_ci([r1, r2, r3], "A"))
print(q.pass_at_k_by_task([r1, r2, r3], "A", 1))
src = open("q/fvh_q/q06_stats.py").read()
print("holes in reference:", len(holes.count_holes(src)))
holed = src.replace('    """One run record from one `scripts/vcheck --json` document."""\n    errors', '    """x"""\n    raise NotImplementedError("Q06.H5py")\n    errors')
import re
holed = re.sub(r'(# item: (Q06\.H\dpy) S\d+\ndef [^\n]*\n    """[^"]*"""\n)(?:    .*\n|\n(?=    ))*', lambda m: m.group(1) + f'    raise NotImplementedError("{m.group(2)}")\n\n\n', src)
print("holes in holed copy:", len(holes.count_holes(holed)))
print("string 'raise NotImplementedError' in a comment is not a hole:", len(holes.count_holes('# item: Q06.H5py S9\ndef f():\n    x = "raise NotImplementedError(\'Q06.H5py\')"\n    return x\n')))
```

### A.19 Q06 agent twin (Dafny)
Shipped form: the same file with an empty `SKELETON` section and `CanonicalUnique` bodyless (green, 1 hole); the reference skeleton: the three leaves bodyless (green, 3 holes).

`probe/agent6_twin.dfy`

```dafny
module Q06_AgentProver {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power

  // SKELETON (the learner's leaves; the reference fills them)
  lemma PowMono(m: nat, n: nat)
    requires m <= n
    ensures Pow(m) <= Pow(n)
  {
    PowIsStdPow(m);
    PowIsStdPow(n);
    Power.LemmaPowIncreases(BASE, m, n);
  }

  lemma ToNatLowerBound(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
    decreases |s|
  {
    if |s| > 1 {
      assert s[1..][|s[1..]| - 1] == s[|s| - 1];
      ValidTail(s);
      ToNatLowerBound(s[1..]);
    }
  }

  lemma CanonicalLengthOrder(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && |a| < |b|
    ensures ToNat(a) < ToNat(b)
  {
    ToNatBound(a);
    ToNatLowerBound(b);
    PowMono(|a|, |b| - 1);
  }

  // The frozen top lemma
  lemma CanonicalUnique(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && ToNat(a) == ToNat(b)
    ensures a == b
    decreases |a|
  {
    if |a| < |b| {
      CanonicalLengthOrder(a, b);
    } else if |b| < |a| {
      CanonicalLengthOrder(b, a);
    } else if |a| > 0 {
      ValidTail(a);
      ValidTail(b);
      if |a| > 1 {
        assert a[1..][|a| - 2] == a[|a| - 1];
        assert b[1..][|b| - 2] == b[|b| - 1];
      }
      CanonicalUnique(a[1..], b[1..]);
      assert a == [a[0]] + a[1..];
      assert b == [b[0]] + b[1..];
    }
  }
}
```

### A.20 Budget attempts (Q06.H3d, H3v, X2d, X2v)
Dafny, run with `vcheck --module Q06 <probe>` (the module's chain and unit options); resource counts from the run's `tasks.csv`.

`probe/rl_d1.dfy`

```dafny
module Q06_RlProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul
  import DivMod = Std.Arithmetic.DivMod

  lemma TwoShiftsNaive(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Power.LemmaPowPositive(BASE, n);
  }

  lemma {:resource_limit 50000000} TwoShiftsNaiveHigh(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Power.LemmaPowPositive(BASE, n);
  }

  lemma {:resource_limit 50000000} TwoShiftsNaiveHigh2(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Power.LemmaPowPositive(BASE, n);
    assert x * y < Pow(n) * Pow(n);
  }

  lemma TwoShiftsRef(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Mul.LemmaMulUpperBound(x, p - 1, y, p - 1);
    assert (p - 1) * (p - 1) < p * p;
  }
}
```

`probe/rl_d3.dfy`

```dafny
module Q06_RlProbe3 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  lemma V3(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y <= x * (p - 1);
    assert x * (p - 1) <= (p - 1) * (p - 1);
    assert (p - 1) * (p - 1) < p * p;
  }

  lemma {:resource_limit 50000000} V3High(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y <= x * (p - 1);
    assert x * (p - 1) <= (p - 1) * (p - 1);
    assert (p - 1) * (p - 1) < p * p;
  }

  lemma V4(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y < p * y || y == 0;
    assert p * y <= p * p;
  }

  lemma {:resource_limit 50000000} V4High(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y < p * y || y == 0;
    assert p * y <= p * p;
  }

  lemma V5(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y <= (p - 1) * (p - 1);
  }

  lemma {:resource_limit 50000000} V5High(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    assert x * y <= (p - 1) * (p - 1);
  }

  lemma {:induction a} AppA(a: seq<nat>, b: seq<nat>)
    
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
  {
  }

  lemma {:resource_limit 50000000} {:induction a} AppAHigh(a: seq<nat>, b: seq<nat>)
    
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
  {
  }

  lemma {:induction k} ShiftK(k: nat, s: seq<nat>)
    
    ensures ToNat(seq(k, i => 0) + s) == Pow(k) * ToNat(s)
  {
  }

  lemma {:resource_limit 50000000} {:induction k} ShiftKHigh(k: nat, s: seq<nat>)
    
    ensures ToNat(seq(k, i => 0) + s) == Pow(k) * ToNat(s)
  {
  }

  lemma {:induction s} LowerB(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
  {
  }

  lemma {:resource_limit 50000000} {:induction s} LowerBHigh(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
  {
  }
}
```

`probe/rl_d5.dfy`

```dafny
module Q06_RlProbe5 {
  import opened QG_L1_BigNat
  import DivMod = Std.Arithmetic.DivMod

  function RemT(x: nat, m: nat): nat
    requires m > 0
  {
    x % m
  }

  opaque function Rem(x: nat, m: nat): nat
    requires m > 0
  {
    x % m
  }

  lemma TransparentEmpty(x: nat, y: nat, m: nat)
    requires m > 0
    ensures RemT(x + m * y, m) == RemT(x, m)
  {
  }

  lemma {:resource_limit 50000000} TransparentEmptyHigh(x: nat, y: nat, m: nat)
    requires m > 0
    ensures RemT(x + m * y, m) == RemT(x, m)
  {
  }

  lemma RevealOnly(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Rem(x + m * y, m) == Rem(x, m)
  {
    reveal Rem();
  }

  lemma {:resource_limit 50000000} RevealOnlyHigh(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Rem(x + m * y, m) == Rem(x, m)
  {
    reveal Rem();
  }

  lemma Ref(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Rem(x + m * y, m) == Rem(x, m)
  {
    reveal Rem();
    DivMod.LemmaModMultiplesVanish(y, x, m);
  }

  lemma Empty(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Rem(x + m * y, m) == Rem(x, m)
  {
  }
}
```

Verus (the chosen H3v attempt and the rejected flood variants; the chosen X2v attempt is in A.16's comment):

`root/verus/q/q06_machine/src/rlv5.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;

verus! {

pub proof fn h3_attempt(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
        lemma_weight_succ(k);
    }
    if a.len() > 0 {
        h3_attempt(a.drop_first(), b);
    } else {
        lemma_weight_zero();
    }
}

#[verifier::rlimit(20)]
pub proof fn h3_attempt_high(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
        lemma_weight_succ(k);
    }
    if a.len() > 0 {
        h3_attempt_high(a.drop_first(), b);
    } else {
        lemma_weight_zero();
    }
}

#[verifier::opaque]
pub open spec fn high(x: nat, m: nat) -> nat
    recommends m > 0,
{
    x / m
}

pub proof fn x2_loop(x: nat, y: nat, m: nat)
    requires 0 < m, x < m,
    ensures high(x + m * y, m) == y,
{
    assert forall|t: nat| #[trigger] high(t, m) + 1 == high(t + m, m) by {
        reveal(high);
        assert(((t + m) as int) / (m as int) == (t as int) / (m as int) + 1) by (nonlinear_arith)
            requires 0 < m;
    }
}

#[verifier::rlimit(20)]
pub proof fn x2_loop_high(x: nat, y: nat, m: nat)
    requires 0 < m, x < m,
    ensures high(x + m * y, m) == y,
{
    assert forall|t: nat| #[trigger] high(t, m) + 1 == high(t + m, m) by {
        reveal(high);
        assert(((t + m) as int) / (m as int) == (t as int) / (m as int) + 1) by (nonlinear_arith)
            requires 0 < m;
    }
}

pub proof fn x2_ref(x: nat, y: nat, m: nat)
    requires 0 < m, x < m,
    ensures high(x + m * y, m) == y,
{
    reveal(high);
    lemma_div_multiples_vanish_fancy(y as int, x as int, m as int);
}

} // verus!
```

`root/verus/q/q06_machine/src/rlv2.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l3::*;

verus! {

pub proof fn app_flood_base(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    broadcast use vstd::seq_lib::group_seq_properties, vstd::seq::group_seq_lemmas_expensive;
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        app_flood_base(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(a.drop_first()) as int, (weight(k) * seq_to_nat(b)) as int);
    } else {
        lemma_weight_zero();
    }
}

#[verifier::rlimit(20)]
pub proof fn app_flood_base_high(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    broadcast use vstd::seq_lib::group_seq_properties, vstd::seq::group_seq_lemmas_expensive;
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        app_flood_base_high(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(a.drop_first()) as int, (weight(k) * seq_to_nat(b)) as int);
    } else {
        lemma_weight_zero();
    }
}

pub proof fn app_flood_full(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    broadcast use vstd::seq_lib::group_seq_properties, vstd::seq::group_seq_lemmas_expensive;
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        app_flood_full(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(a.drop_first()) as int, (weight(k) * seq_to_nat(b)) as int);
    } else {
        lemma_weight_zero();
        assert(a + b =~= b);
    }
}

#[verifier::rlimit(20)]
pub proof fn app_flood_full_high(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    broadcast use vstd::seq_lib::group_seq_properties, vstd::seq::group_seq_lemmas_expensive;
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        app_flood_full_high(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(a.drop_first()) as int, (weight(k) * seq_to_nat(b)) as int);
    } else {
        lemma_weight_zero();
        assert(a + b =~= b);
    }
}

} // verus!
```

`root/verus/q/q06_machine/src/rlv7.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;

verus! {

#[verifier::opaque]
pub open spec fn low(x: nat, m: nat) -> nat
    recommends m > 0,
{
    x % m
}

pub open spec fn low_t(x: nat, m: nat) -> nat
    recommends m > 0,
{
    x % m
}

pub proof fn x2_ref(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    lemma_mod_multiples_vanish(y as int, x as int, m as int);
}

pub proof fn x2_empty(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
}

pub proof fn x2_transparent(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low_t(x + m * y, m) == low_t(x, m),
{
}

pub proof fn x2_period(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by {
        reveal(low);
        lemma_mod_multiples_vanish(1, t as int, m as int);
    }
}

#[verifier::rlimit(20)]
pub proof fn x2_period_high(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by {
        reveal(low);
        lemma_mod_multiples_vanish(1, t as int, m as int);
    }
}

pub proof fn x2_period_int(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    assert forall|t: int| #[trigger] (t % (m as int)) == (t + m) % (m as int) by {
        lemma_mod_multiples_vanish(1, t, m as int);
    }
}

#[verifier::rlimit(20)]
pub proof fn x2_period_int_high(x: nat, y: nat, m: nat)
    requires 0 < m,
    ensures low(x + m * y, m) == low(x, m),
{
    reveal(low);
    assert forall|t: int| #[trigger] (t % (m as int)) == (t + m) % (m as int) by {
        lemma_mod_multiples_vanish(1, t, m as int);
    }
}

} // verus!
```

### A.21 Verus leaves of `CanonicalUnique` (why Q06's rung is Dafny only)
`root/verus/q/q06_machine/src/leaves.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
verus! {
pub proof fn leaf_same_length(a: Seq<u64>, b: Seq<u64>)
    requires seq_wf(a), seq_wf(b), seq_to_nat(a) == seq_to_nat(b),
    ensures a.len() == b.len(),
{
    broadcast use group_bignat_bounds;
}
pub proof fn leaf_tail_wf(s: Seq<u64>)
    requires seq_wf(s), s.len() > 0,
    ensures seq_wf(s.drop_first()),
{
    if s.len() > 1 {
        assert(s.drop_first().last() == s.last());
    }
}
pub proof fn leaf_head_tail(a: Seq<u64>, b: Seq<u64>)
    requires a.len() > 0, b.len() > 0, seq_to_nat(a) == seq_to_nat(b),
    ensures a[0] == b[0], seq_to_nat(a.drop_first()) == seq_to_nat(b.drop_first()),
{
}
} // verus!
```

## Appendix B. Prediction and shape probes (scratch)

The specimens' labels follow line order, as in the plan; the module lanes rebuild the specimens with the shipped header, `// SLOT: FAILS ???` and the item marker, and re-capture each answer.

### B.1 Q04.P4d specimen probe
`d/p/p4d_spec.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P4 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  lemma CalcSteps(s: seq<nat>)
    requires |s| > 0
  {
    calc {
      ToNat(s + [0]);
    ==
      ToNat(s);  // [a]
    ==
      Head(s) + BASE * ToNat(Tail(s));  // [b]
    ==
      s[0] * BASE + ToNat(s[1..]);  // [c]
    <=
      s[0] * BASE + ToNat(s[1..]) + BASE;  // [d]
    }
  }
}
```

### B.2 Q04.P5d specimen probe (lemmas A, B, C, G are the specimen's [a]–[d])
`d/p/p6d.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P6 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  lemma A(n: nat)
    ensures Pow(n) >= 1
  {
  }
  lemma B(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
  {
  }
  lemma C(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(s) < Pow(|s|)
  {
  }
  lemma D(n: nat)
    ensures ToNat(seq(n, i => 0)) == 0
  {
  }
  lemma E(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
  {
  }
  lemma F(n: nat)
    ensures |FromNat(n)| <= n
  {
  }
  lemma G(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures |AddLimb(s, d)| <= |s| + 1
  {
  }
  lemma H(s: seq<nat>)
    ensures |Normalize(s)| <= |s|
  {
  }
}
```

### B.3 Q04.P9v specimen probe
`root/verus/q/q04_proof_craft/src/p9v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
verus! {
pub proof fn a_with_group()
    ensures weight(3) <= weight(5),  // [a]
{
    broadcast use group_bignat_bounds;
}
pub proof fn b_without_group()
    ensures weight(3) <= weight(5),  // [b]
{
}
pub proof fn c_canonical(s: Seq<u64>)
    requires seq_wf(s), s.len() == 3,
    ensures weight(2) <= seq_to_nat(s),  // [c]
{
    broadcast use group_bignat_bounds;
}
pub proof fn d_next(s: Seq<u64>)
    ensures seq_to_nat(s) < weight(s.len() + 1),  // [d]
{
    broadcast use group_bignat_bounds;
}
} // verus!
```

### B.4 Q05.P6d specimen probe
`d/q05/p6d.dfy`

```dafny
module P6 {
  // Bump(a, i): requires i < |a|; ensures a'[i] == a[i] + 1 and every other limb unchanged.
  // Four candidate verification conditions for the caller `Bump(a, 0); assert a[0] >= 1 && a[1] == old(a[1]);`
  lemma CallPre(s0: seq<nat>)
    requires |s0| > 1
    ensures 0 < |s0|  // [a]
  {
  }
  lemma FirstLimb(s0: seq<nat>, s1: seq<nat>)
    requires |s1| == |s0| > 1
    requires s1[0] == s0[0] + 1
    requires forall j | 0 <= j < |s0| && j != 0 :: s1[j] == s0[j]
    ensures s1[0] >= 1  // [b]
  {
  }
  lemma OtherLimb(s0: seq<nat>, s1: seq<nat>)
    requires |s1| == |s0| > 1
    requires s1[0] == s0[0] + 1
    requires forall j | 0 <= j < |s0| && j != 0 :: s1[j] == s0[j]
    ensures s1[1] == s0[1]  // [c]
  {
  }
  lemma OtherLimbNoFrame(s0: seq<nat>, s1: seq<nat>)
    requires |s1| == |s0| > 1
    requires s1[0] == s0[0] + 1
    ensures s1[1] == s0[1]  // [d]
  {
  }
}
```

### B.5 Q06.P3d specimen probe
`d/q06/p3_trig.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P3 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  lemma A(s: seq<nat>, k: nat)
    requires forall i {:trigger Pow(i)} | 0 <= i <= |s| :: ToNat(s[..i]) < Pow(i)
    requires k <= |s|
    ensures ToNat(s[..k]) < Pow(k)  // [a]
  {
  }
  lemma B(s: seq<nat>)
    requires forall i {:trigger Pow(i)} | 0 <= i <= |s| :: ToNat(s[..i]) < Pow(i)
    requires |s| >= 2
    ensures ToNat(s[..2]) < BASE * BASE  // [b]
  {
  }
  lemma C(s: seq<nat>)
    requires forall i {:trigger s[..i]} | 0 <= i <= |s| :: ToNat(s[..i]) < Pow(i)
    requires |s| >= 2
    ensures ToNat(s[..2]) < BASE * BASE  // [c]
  {
  }
  lemma D(s: seq<nat>)
    requires forall i {:trigger Pow(i)} | 0 <= i <= |s| :: ToNat(s[..i]) < Pow(i)
    requires |s| >= 2
    ensures ToNat(s[..2]) < Pow(2)  // [d]
  {
  }
}
```

### B.6 Q05.P4d and P5v specimen probes (contract-only)
`d/q05/p4d_bodyless.dfy`

```dafny
module P4 {
  class LimbStack {
    var a: array<nat>
    var n: nat
    ghost var Contents: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && Contents == a[..n]
    }

    constructor (cap: nat)
      requires cap > 0
      ensures Valid() && fresh(Repr) && Contents == []
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    function Size(): nat
      reads this, Repr
      requires Valid()
      ensures Size() == |Contents|
    {
      n
    }

    method Push(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
  }

  method WithDisjoint(s: LimbStack, t: LimbStack, x: nat)
    requires s.Valid() && t.Valid() && s.Repr !! t.Repr
    modifies s.Repr
  {
    s.Push(x);
    assert t.Valid();  // [a]
  }
  method WithoutDisjoint(s: LimbStack, t: LimbStack, x: nat)
    requires s.Valid() && t.Valid()
    modifies s.Repr
  {
    s.Push(x);
    assert t.Valid();  // [b]
  }
  method StillDisjoint(s: LimbStack, t: LimbStack, x: nat)
    requires s.Valid() && t.Valid() && s.Repr !! t.Repr
    modifies s.Repr
  {
    s.Push(x);
    assert s.Repr !! t.Repr;  // [c]
  }
  method SameStackTwice(s: LimbStack, x: nat, y: nat)
    requires s.Valid()
    modifies s.Repr
  {
    s.Push(x);
    s.Push(y);
    assert s.Contents == old(s.Contents) + [x, y];  // [d]
  }
}
```

`root/verus/q/q05_frames/src/p5v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
verus! {
pub struct Rejected;
pub struct Bounded {
    pub items: Vec<u64>,
    pub limit: usize,
}
impl View for Bounded {
    type V = Seq<u64>;
    open spec fn view(&self) -> Seq<u64> {
        self.items@
    }
}
impl Bounded {
    pub open spec fn inv(&self) -> bool {
        self.items@.len() <= self.limit
    }
    pub fn new(limit: usize) -> (r: Self)
        ensures r.inv(), r@ == Seq::<u64>::empty(), r.limit == limit,
    {
        Bounded { items: Vec::new(), limit }
    }
    #[verifier::external_body]
    pub fn maybe_push(&mut self, x: u64) -> (r: Result<(), Rejected>)
        requires old(self).inv(),
        ensures
            final(self).inv(),
            final(self).limit == old(self).limit,
            r is Ok ==> final(self)@ == old(self)@.push(x),
    {
        unimplemented!()
    }
}
pub fn other_unchanged() {
    let mut s = Bounded::new(0);
    let t = Bounded::new(4);
    let _ = s.maybe_push(1);
    assert(t@ == Seq::<u64>::empty());  // [a]
}
pub fn same_unchanged_on_err() {
    let mut s = Bounded::new(4);
    let r = s.maybe_push(1);
    match r {
        Err(_) => {
            assert(s@ == Seq::<u64>::empty());  // [b]
        },
        Ok(_) => {},
    }
}
pub fn limit_unchanged() {
    let mut s = Bounded::new(2);
    let _ = s.maybe_push(1);
    assert(s.limit == 2);  // [c]
}
pub fn length_bounded() {
    let mut s = Bounded::new(2);
    let _ = s.maybe_push(1);
    assert(s@.len() <= 2);  // [d]
}
} // verus!
```

### B.7 Verdict scenario probes
`d/p/p1dv_d.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P1 {
  import opened QG_L1_BigNat
  method SplitSum(a: nat, b: nat) returns (lo: nat, hi: nat)
    requires a < BASE && b < BASE
    ensures lo + hi * BASE == a + b
  {
    var s := a + b;
    lo := s % BASE;
    hi := s / BASE;
  }
}
```

`d/p/p9dv_d.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P9 {
  import opened QG_L1_BigNat
  import opened Std.Arithmetic.Power
  lemma UsePow()
    ensures Pow(1) == BASE
  {
  }
}
```

`root/verus/q/q04_proof_craft/src/p9dv_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::power::*;
use qg_bignat_l3::*;

verus! {
pub open spec fn pow(b: int, e: nat) -> int {
    b + e
}

pub proof fn use_pow()
    ensures pow(2, 3) == 5,
{
}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7_empty.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
    ensures
        (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat,
{

}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7_nl.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
    ensures
        (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat,
{
    assert((x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat) by (nonlinear_arith);
}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7_bv.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
    ensures
        (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat,
{
    assert((x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat) by (bit_vector);
}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7_compute.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
    ensures
        (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat,
{
    assert((x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat) by (compute);
}
} // verus!
```

`d/q05/p1dv_d.dfy`

```dafny
module P1 {
  class Counter {
    var n: nat
    function Size(): nat
    {
      n
    }
  }
}
```

`root/verus/q/q05_frames/src/p1dv_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
verus! {
pub struct Counter {
    pub n: u64,
}
impl Counter {
    pub open spec fn size(&self) -> nat {
        self.n as nat
    }
}
} // verus!
```

`d/q05/p3dv_d.dfy`

```dafny
module P3 {
  class Tagged {
    var x: nat
    ghost var Shadow: seq<nat>
    constructor ()
    {
      x := 0;
      Shadow := [];
    }
  }
  method Main() {
    var t := new Tagged();
    print t.x, "\n";
  }
}
```

`root/verus/q/q05_frames/src/p3dv_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub struct Tagged {
    pub x: u64,
    pub shadow: Ghost<Seq<u64>>,
}
} // verus!

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn size_is_8() {
        assert_eq!(core::mem::size_of::<Tagged>(), 8);
    }
    #[test]
    fn size_is_16() {
        assert_eq!(core::mem::size_of::<Tagged>(), 16);
    }
}
```

`d/q06/p2_oor.dfy`

```dafny
// (inline copies of the L1/L2 layer text omitted)
module P2O {
  import opened QG_L1_BigNat
  import Power = Std.Arithmetic.Power
  lemma PowIsStdPow(n: nat)
    ensures Pow(n) == Power.Pow(BASE, n)
    decreases n
  {
    if n > 0 {
      PowIsStdPow(n - 1);
    }
  }
  lemma TwoShiftsNaive(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Power.LemmaPowPositive(BASE, n);
  }
}
```

`d/q06/p5_scope.dfy`

```dafny
module P5 {
  opaque function F(x: nat): nat { x + 1 }
  lemma InsideBy(x: nat)
    ensures F(x) > x
  {
    assert F(x) == x + 1 by { reveal F(); }
  }
  lemma AfterBy(x: nat)
    ensures F(x) > x
  {
    assert true by { reveal F(); }
  }
  lemma TopLevel(x: nat)
    ensures F(x) > x
  {
    reveal F();
  }
}
```

`d/q06/p6_attr.dfy`

```dafny
module P6A {
  lemma {:rlimit 1000} Low(x: nat)
    ensures x + 0 == x
  {
  }
}
```

`d/q05/p2dv_d2.dfy`

```dafny
module P2b {
  function G(m: nat, n: nat): nat
  {
    if m == 0 then n else if n == 0 then G(m - 1, 7) else G(m, n - 1)
  }
}
```

`root/verus/q/q05_frames/src/p2dv_v2.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
verus! {
pub open spec fn g(m: nat, n: nat) -> nat
    decreases m,
{
    if m == 0 {
        n
    } else if n == 0 {
        g((m - 1) as nat, 7)
    } else {
        g(m, (n - 1) as nat)
    }
}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7v_base3.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
verus! {
pub proof fn at_least_low_limb(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) >= s[0],
{
}
} // verus!
```

`root/verus/q/q04_proof_craft/src/p7v_mul3.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
verus! {
pub proof fn at_least_low_limb(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) >= s[0],
{
    broadcast use vstd::arithmetic::mul::group_mul_properties;
}
} // verus!
```

`lab/p1dv.dfy`

```dafny
module P1 {
  lemma Wrong(x: nat)
    ensures x + 1 == x
  {
  }

  @Test
  method Passes() {
    expect 1 + 1 == 2;
  }
}
```

`lab/p1dv.rs`

```rust
use vstd::prelude::*;
verus! {
proof fn wrong(x: nat)
    ensures x + 1 == x,
{
}
} // verus!
```

### B.8 Q04.H4v: the plan lane's shape, shipped (RED)
`root/verus/q/q04_proof_craft/src/h4v_ship.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;
use core::cmp::Ordering;

verus! {

// item: Q04.H4v S4
pub fn cmp_shipped(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    #[verifier::proof_note("Q04.H4v")]
    assume(false);
    while i > 0
        decreases i,
    {
        i = i - 1;
        if a.limbs[i] < b.limbs[i] {
            proof {
                lemma_lt_at(a@, b@, i as int);
            }
            return Ordering::Less;
        }
        if a.limbs[i] > b.limbs[i] {
            proof {
                lemma_lt_at(b@, a@, i as int);
            }
            return Ordering::Greater;
        }
    }
    proof {
        assert(a@ =~= b@);
    }
    Ordering::Equal
}

} // verus!
```

### B.9 Q05: Verus annotation-form probes, P2dv's old shape, `transfer`
`root/verus/q/q05_frames/src/q05probe.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

pub open spec fn bit_count(x: nat) -> nat
    decreases x,
{
    if x == 0 { 0 } else { x % 2 + bit_count(x / 2) }
}

pub open spec fn ones(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { bit_count(s[0] as nat) + ones(s.drop_first()) }
}

pub fn count_ones_shipped(v: &Vec<u64>) -> (c: u64)
    requires
        ones(v@) <= u64::MAX,
    ensures
        c == ones(v@),
{
    let mut i: usize = 0;
    let mut x: u64 = 0;
    let mut c: u64 = 0;
    proof {
        assert(v@.subrange(0, v.len() as int) =~= v@);
    }
    #[verifier::proof_note("Q05.H4v")]
    assume(false);
    while x > 0 || i < v.len()
        decreases v.len() - i,
    {
        if x > 0 {
            c = c + x % 2;
            x = x / 2;
        } else {
            proof {
                assert(v@.subrange(i as int, v.len() as int).drop_first()
                    =~= v@.subrange(i + 1, v.len() as int));
            }
            x = v[i];
            i = i + 1;
        }
    }
    c
}

pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

pub open spec fn all_digits(s: Seq<u8>) -> bool {
    forall|i: int| 0 <= i < s.len() ==> is_digit(#[trigger] s[i])
}

pub open spec fn dec_value(s: Seq<u8>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { dec_value(s.drop_last()) * 10 + (s.last() - 48) as nat }
}

pub fn digit(c: u8) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> is_digit(c),
        r is Ok ==> r->Ok_0 == c - 48,
        r is Err ==> r->Err_0 == ParseError::NotDigit,
{
    if 48 <= c && c <= 57 { Ok((c - 48) as u64) } else { Err(ParseError::NotDigit) }
}

pub fn mul10_add(acc: u64, d: u64) -> (r: Result<u64, ParseError>)
    requires
        d < 10,
    ensures
        r is Ok <==> acc * 10 + d <= u64::MAX,
        r is Ok ==> r->Ok_0 == acc * 10 + d,
        r is Err ==> r->Err_0 == ParseError::Overflow,
{
    if acc <= (u64::MAX - d) / 10 { Ok(acc * 10 + d) } else { Err(ParseError::Overflow) }
}

pub fn parse_decimal_shipped(s: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok ==> s@.len() > 0 && all_digits(s@) && r->Ok_0 == dec_value(s@),
        (r is Err && r->Err_0 == ParseError::Empty) <==> s@.len() == 0,
        r is Err && r->Err_0 == ParseError::NotDigit ==> !all_digits(s@),
        r is Err && r->Err_0 == ParseError::Overflow ==> exists|k: int|
            0 < k <= s@.len() && all_digits(s@.subrange(0, k)) && #[trigger] dec_value(s@.subrange(0, k)) > u64::MAX,
{
    #[verifier::proof_note("Q05.H5v")]
    assume(false);
    let mut v: u64 = 0;
    let mut i: usize = 0;
    while i < s.len()
        invariant
            0 < s@.len(),
            i <= s@.len(),
            all_digits(s@.subrange(0, i as int)),
            v == dec_value(s@.subrange(0, i as int)),
        decreases s.len() - i,
    {
    }
    proof {
        assert(s@.subrange(0, s@.len() as int) =~= s@);
    }
    Ok(v)
}

pub open spec fn g(m: nat, n: nat) -> nat
    decreases m,
{
    if m == 0 {
        n
    } else if n == 0 {
        g((m - 1) as nat, 7)
    } else {
        g(m, (n - 1) as nat)
    }
}

pub struct Short;

pub struct Account {
    pub bal: u64,
    pub cap: u64,
}

pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
    requires
        old(from).bal <= old(from).cap,
        old(to).bal <= old(to).cap,
    ensures
        final(from).cap == old(from).cap,
        final(to).cap == old(to).cap,
        final(from).bal <= final(from).cap,
        final(to).bal <= final(to).cap,
        r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap),
        r is Ok ==> final(from).bal == old(from).bal - k && final(to).bal == old(to).bal + k,
        r is Err ==> final(from).bal == old(from).bal && final(to).bal == old(to).bal,
{
    if k <= from.bal && k <= to.cap - to.bal {
        from.bal = from.bal - k;
        to.bal = to.bal + k;
        Ok(())
    } else {
        Err(Short)
    }
}

} // verus!
```
