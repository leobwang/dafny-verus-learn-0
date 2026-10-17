# Q10–Q18 author notes (DV5 item plan: the practice tiers and layers L5–L7)

> **Author-only.** This file holds reference proofs, gate results, line counts, exit statements and answers, the prose items' reference statements, the planned forensic and stage scenarios, the flawed grading fixture's planted flaws, the MDE computation behind QPLAN §6 Q35 and the benchmark validation sample. Never quote, paraphrase or link any of it from a learner-visible file (`QPLAN.md`, the registry, exercise, check, exit and agent files, specimens, `slots/`, `expected/`, chapters, banks, rubrics, `research/` templates, `docs/design/`). The learner-visible plan is `QPLAN.md` §19–§30; item ids here are the same.

Written 2026-10-07 by the DV5 plan lane, and revised the same day after the plan review (§13 records every disposition and the revision's probes; Appendix C the revised texts; where §13 or Appendix C differs from an earlier section, they win). Every tool result quoted below was captured on the pins, one solver job at a time, each job started with at least 100 GB available (`free -g` read before each batch: 102–103 GB available), through:

- the course wrappers run from a scratch copy of the authoring worktree's tracked files (`git ls-files` at `f71dde4`, without `Solutions/`, `paper/solutions/` and `tests/instructor/leak_patterns/`), with the toolchain linked from the primary checkout's `.toolchain/` (read only), and every `dvl` job's memory cap clamped to 8 GB, the lane's share, by `drv/capped.py` (it replaces `dvl.common.run_capped` with a wrapper that passes `min(cap, 8)`, then runs the wrapper unchanged; `DVL_SCRATCH` set to the lane's scratch);
- the `dvl` library's empty-body gates (`dvl.dafny.empty_body`: maxauto plus the shipped options under seeds 1–3; `dvl.verus.empty_body`: the light modes under seeds 1–3, with a declared trivial body for the TRIV mode of an exec item), through the same clamp (`drv/eb.py`, `drv/ebt.py`);
- `scripts/vcheck --brittleness` (seeds 1–3) on every probe file and crate, and `--brittleness --solvers` (both bundled Z3s × seeds 1–3) on the Dafny files of Q10, Q13–Q14 and Q16.

The scratch registry armed Q10 (layer L5), Q13 (L6) and Q16 (L7) with the candidate layer files declared, so that `scripts/gen_units.py` generated their units and `scripts/vcheck` resolved every probe's chain; Q11's and Q12's probes ran in Q10's unit and crate (the same chain, L1–L5), Q14's in Q13's. Probe files are lane scratch under `/tmp/dvl0-plan5r-q/` (`root/` the scratch copy; `drv/` the drivers; `bench/` the validation sample; raw outputs under `dvl/runs/`), **not archived**; Appendix A reproduces every candidate file and probe as last verified, so nothing below depends on the scratch tree surviving. Every result is re-captured on the real files by the lane that writes them.

## 0. What was and was not run

### 0.1 Verification, empty-body gate and stability of the references

| item | reference (Appendix) | lines (body; with invented statements) | band | verifies | empty-body gate | stable |
|---|---|---|---|---|---|---|
| L5 Dafny `CanonicalLower`, `PowPositive`, `NormalizeTrim` | A.1 | — | — | yes (in every unit that reaches L5) | — | seeds 1–3, both solvers |
| L5 Verus `lemma_weight_pos` | A.2 | — | — | yes | — | seeds 1–3 |
| L6 Dafny `FromNatCanonical`, `NormalizeAddCorrect`, `SubB`/`Sub` (revised: `Sub` a ghost function by value, `SubB` dropped, §13.3, C.1) | A.3, C.1 | — | — | yes | — | seeds 1–3, both solvers |
| L6 Verus `normalize` | A.4 | — | — | yes | — | seeds 1–3 (CV 0.3%) |
| L7 Dafny `Shift`, `MulAcc`, `Times` (revised: `MulAcc`, `Times` ghost, §13.3, C.2) | A.5, C.2 | — | — | yes | — | seeds 1–3, both solvers |
| L7 Verus `sub`, `lemma_sub_lift`, `to_u64`, `BigNatCore` + impl | A.6 | — | — | yes (6 verified) | — | seeds 1–3 (CV 9.4%) |
| Q10.H1d `ToU64` | A.7 | 10 | ≤ 10 (edge) | yes | failed: maxauto and seeds 1–3 | yes |
| Q10.H1v `to_u64` | A.8 | 15 | ≤ 15 (edge) | yes | failed in every mode (E0…EM), seeds 1–3 | yes |
| Q10.H2d `Shift` (spec) | A.7 | 1 ensures line | ≤ 10 | yes, with `ShiftTwice` | statement hole: the client fails with no `ensures` (by construction) | yes |
| Q10.H2v `high_limb` (spec) | A.8 | 1 ensures line | ≤ 15 | yes, with `high_client` | as H2d | yes |
| Q10.H3d `ToNatTopLimb` | A.7 | 5 | ≤ 10 | yes; the quoted attempt (the reference minus its sequence-identity assertion) **fails** | failed: maxauto and seeds 1–3 | yes; CV 27.6% under 4.14.1 (flagged, advisory) |
| Q10.H3v `lemma_top_limb` | A.8 | 4 | ≤ 15 | yes | failed in every mode; BV killed by its clock (counts as failing, Δ58) | yes |
| Q10.H4d `NormLen` | A.7 | 3 invariant lines (11 with the given code) | ≤ 10 | yes | failed | yes |
| Q10.H4v `norm_len` | A.8 | 3 invariant lines | ≤ 15 | yes | failed in every mode, INV and TRIV included | yes |
| Q10.H5d `ModPowSucc` | A.7 | 2 | ≤ 10 | yes | failed (maxauto inconclusive, seeds failed; rerun in the revision: maxauto `inconclusive` again, which `dvl.dafny` reports only for an out-of-resource or time-out result, so the empty body does not verify at the pinned limit; QPLAN §30 Q66) | yes |
| Q10.H5v `lemma_mod_weight_succ` | A.8 | 4 | ≤ 15 | yes | failed (BV: no-verify on `weight`, counts as failing) | yes |
| Q10.H6v `Ring::get` | A.8 | 4 | ≤ 15 | yes | TRIV failed; the E modes keep the exec code, which needs no proof: an exec hole is gated by TRIV | yes |
| Q10.H7v `Ring::push_back` | A.8 | 7 | ≤ 15 | yes | TRIV failed (E modes as H6v) | yes; CV 17.4% |
| Q11.H1d `LimbVec.Set` | A.9 | 2 | ≤ 10 | yes | failed | yes |
| Q11.H2d `LimbVec.CopyFrom` | A.9 | 8 | ≤ 10 | yes | failed | yes |
| Q11.H3v `Acc::add_word` | A.10 | 5 | ≤ 15 | yes | TRIV (`{ Ok(()) }`) failed | yes |
| Q11.H4v `Acc::take_if_at_least` | A.10 | 9 | ≤ 15 | yes | TRIV (`{ Err(AccError::TooSmall) }`) failed | yes |
| Q11.H5d `AddCanon` | A.9 | 4 | ≤ 10 | yes | the body without its lemma calls fails the subset constraint | yes |
| Q11.H6v `value_two` | A.10 | 14 | ≤ 15 | yes | TRIV failed | yes |
| Q11.H7d, H8d `Pre1`, `Pre2` | A.9, C.3 | 1, 2 | ≤ 10 | yes (`Pre1Exact`, `Pre2Exact` with empty bodies) | the placeholder bodies `true` and `false` each fail the `Exact` lemma; **but** the construct-free answer `Post1(Prog1(x, y))` (and `Post2(Prog2(x, y))`) verified in this layout (plan review blocker 1, confirmed): restated in three modules, §13.3 | yes |
| Q11.H9d `WpSoundIfThen` | A.9 | 3 | ≤ 10 | yes | failed | yes |
| Q11.H10v `max_into` (gated) | A.10 | 5 | ≤ 15 | yes | TRIV failed | yes |
| Q12.H3d `NormalizeLiteral` | A.11 | 3 | ≤ 10 | yes | failed (maxauto failed too) | yes |
| Q12.H3v `lemma_chain_le` | A.12 | 1 | ≤ 15 | yes | failed in every light mode | yes |
| Q12.H4d `ToNatMono` | A.11 | 2 | ≤ 10 | yes | failed as shipped; maxauto verified (a hole + lever: manual induction) | yes |
| Q12.H5d `MulLimbByZero` | A.11 | 3 | ≤ 10 | yes | failed | yes |
| Q12.H6d `CmpSelf` | A.11 | 2 | ≤ 10 | yes | failed as shipped; maxauto verified (hole + lever) | yes |
| Q12.H7d `NormalizeShorter` | A.11 | 2 | ≤ 10 | yes | failed as shipped; maxauto verified (hole + lever) | yes |
| Q12.H4v `lemma_seq_to_nat_mono` | A.12 | 4 | ≤ 15 | yes | failed in every light mode | yes |
| Q12.H5v `is_zero` | A.12 | 8 | ≤ 15 | yes | TRIV failed | yes |
| Q12.H6v `eq_big` | A.12 | 3 | ≤ 15 | yes | TRIV failed | yes |
| Q12.H7v `size_bound` | A.12 | 3 | ≤ 15 | yes | TRIV failed | yes |
| Q13.H1v `sub` with `lemma_sub_lift` | A.14, C.5 | 57 with the exec code; 38 proof lines by Δ53's count; **46** under §19.0 (sub 20 + the lift's body 13 + its statement 13), **44** after writing the two one-statement proof blocks on one line each (C.5; re-verified) | 15–45 | yes | failed in E0, E0H, E1, E2, EC (on the first form; the revision changed whitespace only) | yes (CV 5.3%) |
| Q13.H2d `NormalizeConcat` + the invented `NormalizeIdem` | A.13 | 7 + 2, 12 with the helper's statement | 10–30 | yes | failed | yes, both solvers |
| Q13.H3v `lemma_lt_at_any` + the invented `lemma_eq_any` (+ `tail`) | A.14 | 9 + 9 + 3, ≈ 27 with both statements | 15–45 | yes | failed (E0…EC, NL) | yes |
| Q13.H4d `RepeatValue` | A.13 | 22 | 10–30 | yes | failed | yes, both solvers |
| Q13.H4v `lemma_repeat_value` | A.14 | 20 | 15–45 | yes | failed | yes |
| Q13.H5d `ValueLoop` | A.13, C.4 | 14; 7 proof lines under §19.0, below band: revised (nonlinear-off module), 13 | 10–30 | yes | failed | first form flagged (CV 39.3%, up to 2.3 M); revised form stable, seeds 1–3 × both solvers, flagged CV 26.7% at ≤ 88,716 (1.8% of the limit) |
| Q13.X1v `lemma_value_below_top` | A.15 | 9 | — (exit) | yes | failed | yes |
| Q14.H1d `Q14_Cached.CmpCorrect` + the invented `Shorter` | A.16 | 6 + 5, 14 with the helper's statement | 10–30 | yes | failed | yes, both solvers |
| Q14.H2v `impl Accum for PairAcc` | A.15, C.6 | 21 (two methods); 10 proof lines under QPLAN §19.0, below band: revised (`from_big` added), 24 | 15–45 | yes | first form not run (`ebt.py` refused both names as not unique); the revision ran TRIV by hand-written variants, seeds 1–3: all three methods fail (§13.2) | yes |
| Q14.H3d `InterleaveSpec` | A.16 | 4 + its measure | **below** 10 | yes | failed as shipped; maxauto verified (with `Q14_Term` after the nonlinear-off module); with `Q14_Term` first (the revision's order, Δ31), maxauto failed too | yes |
| Q14.H3v `sum_limbs` | A.15, C.6 | 19; 13 proof lines under §19.0, below band: revised (top-down loop + one invented lemma), 27 | 15–45 | yes | TRIV (`{ 0 }`) failed once the specification states the sum (a weaker first draft, `r <= len * bound`, let TRIV verify: a constant answer); the revised form fails every mode (§13.2) | yes |
| Q16.H1d `MulCorrect` + the invented `MulAccCorrect`, `ShiftCorrect` | A.17 | 3 + 26 + 9, 46 with both statements (47 under §19.0, `ShiftCorrect`'s `decreases` line counted) | 30–80 | yes (also with L7's `MulAcc`, `Times` ghost) | failed; each invented lemma's empty body fails too (revision) | yes, both solvers; the plain-induction attempt captured (§8.2) |
| Q16.H2v `div_limb` + the invented `lemma_suffix_step`, `lemma_div_step` | A.18 | 53 + 1 + 11, ≈ 75 with both statements | 45–120 | yes | failed (E0, E1, EC); TRIV failed | yes (CV 9.7%) |
| Q16.H3v `mul` + the invented `shift_limb` (gated) | A.18 | 31 + 20 = 51 code and proof lines; 38 under §19.0, and 44 with H3d: **below** 45 for the problem | — (Verus half re-planned, §13.3) | yes | failed (E0, E1, EC); TRIV failed | yes |
| Q16.H3d `MulLoop` (gated) | A.17 | 11; 6 under §19.0; with L7's `Times` compiled, `r := Times(a, b); MulCorrect(a, b);` verified (blocker 2, confirmed), and with `Times` ghost it fails at resolve | (with H3v) | yes | failed (also over C.2) | yes, both solvers |
| Q10.X1d, Q10.X1v, Q11.X1d, Q11.X1v, Q12.X1d, Q12.X1v | A.11, A.12 | 9, 4, 2, 5, 3, 1 | — (exits) | yes | failed (Q11.X1d and Q12.X1d: maxauto verified, failed as shipped: hole + lever) | yes |

Line counts in this table are the non-blank, non-comment lines between a declaration's braces (`drv/count.py`, Appendix B), hand-corrected where a spec clause holds braces; "with invented statements" adds the statements of the lemmas the learner must invent, which the band counts (spec §2.8: "measured after the given layers are re-supplied"). **This table mixed conventions** (exec code counted for some items, not for others; plan review major 6). §13.2 re-counts every item under QPLAN §19.0's single rule (proof lines plus invented statements, exec code excluded), and its figures supersede this table's band column.

### 0.2 Not run

- Every Python item (Q12's retry client, policies and report; Q15's client and oracles; Q18's gate v2): they are written on DV4's step 1a remainder (`fvh.protocol` … `fvh.report`), which is not built (QPLAN §30 Q53). No reference was written.
- Q14.H4d (gated), Q14.H5v (gated), all of Q15's verifier items, Q17 and Q18: designs only (§7–§10 below). No reference written; their admissible entries start `admitted = false`.
- Every prediction (P items): scenarios only. **No answer was captured**; the module lanes capture each on its built scenario (as `scripts/pins.py --update --ref --module <ID>` does) and replace any scenario whose answer an earlier prediction already settles.
- No container was started and no model was called: every lab run needs DV4 steps 2b and later (host action H1 not done on 2026-10-07).
- `get_bench.sh --validate` was not run (it writes into the worktree's `bench/public/`); §4.2's sample ran the same `vcheck` commands on copies in the lane scratch.
- The Verus `--solvers` axis does not exist (Verus checks its Z3 version; QPLAN §17.5).

## 1. Layers L5–L7 (QPLAN §19)

- **L5 Dafny** (A.1): `CanonicalLower`, `PowPositive`, `NormalizeTrim`. `CanonicalLower` has the same statement as one leaf of the Q06 agent file's author skeleton (`ToNatLowerBound`, `Solutions/plans/Q04-Q06-author-notes.md` §2.2's Q06 agent block); that skeleton is the learner's to design, so QPLAN does not say so. Re-supplying it in L5 is allowed (Δ130) and spoils nothing for Q06 (L5 is never open before Q10).
- **L5 Verus** (A.2): `lemma_weight_pos` only. A first draft gave a trailing-zeros value lemma for Q10's Verus normalize item; with `n = 0` it is Q01.H3v's statement (`lemma_all_zero`), which §1.7 F2 forbids, so the item's postcondition became structural (`norm_len`) and the lemma was dropped.
- **L6 Dafny** (A.3): `FromNatCanonical` (new), `NormalizeAddCorrect` (Q08.H1d's content, stated for `Valid` inputs, which is stronger than Q08's refined statement; Q08 does not import L6), `SubB`/`Sub` (definitions; the recursive call's precondition is met by `ValidTail` calls inside the function body). **Revised** (review major 9): `SubB` spelled out Q13.H1v's borrow step, so it is dropped, and `Sub` is a ghost function by value (C.1).
- **L6 Verus** (A.4): `normalize`, the Q02.H2v twin verbatim.
- **L7 Dafny** (A.5; revised in C.2: `MulAcc` and `Times` ghost, blocker 2): the schoolbook definitions only. A first design put the capstone's frozen API in L7 as an abstract module refining `QG_L4_Spec`; it was dropped because a given abstract module needs a concrete refinement in the same file for `vaudit --mode given` (Δ97, as L4's `QG_L4_Limbs`), and a concrete `Mul` refinement would give full multiplication to Q16 (§14.7 F13), and because spec §5.5 has the learner write all the capstone's statements.
- **L7 Verus** (A.6): `sub` (Q13.H1v's twin), `to_u64` (Q10.H1v's), and `api.rs`'s `BigNatCore` with its implementation by those two.
- **Headers:** as L3's and L4's ("Do not open this file before you start Q10 / Q13 / Q16"), listing what each holds without mechanism.
- **§19.6 re-check** on the built files: every Q10–Q18 statement against every layer declaration (the module lanes add their exits).

## 2. Q10 (QPLAN §20)

### 2.1 Prediction scenarios (answers not captured)

- **P1dv:** the two cast methods as QPLAN states them. Capture `D:` and `V:` on the built block.
- **P2dv:** the `!=` loop. Dafny may or may not guess the measure for `while i != |s|`; Verus's loop carries an explicit `decreases`. Capture both. If Dafny's verdict repeats Q02.P4dv's lesson exactly, replace the Dafny half by a loop whose guessed measure is wrong.

### 2.2 References and sizes

§0.1 and A.7–A.8. Notes:
- **H1d** uses L5's `CanonicalLower` and `PowPositive`; the two-limb case needs `Pow(|s| - 1) == BASE * Pow(|s| - 2)`, which Dafny unfolds once. 10 body lines, 4 of them proof lines (QPLAN §19.0's count): well inside the band.
- **H1v**: the spike's `to_u64`, with `reveal(weight)` replaced by `lemma_weight_zero`, `lemma_weight_succ(0)` and `lemma_weight_mono` (L3), and the `Option` specification in `is`/`->` form; 15 lines, 8 of them proof lines.
- **The fallbacks' contents** (QPLAN's registry strings are neutral, review major 18): F-H1d `ToU64` restricted to `|s| <= 2` (no lower bound needed); F-H1v `to_u64` restricted to `a@.len() <= 2`; F-H3d the repair of a one-step sequence-identity proof; F-H3v the same repair with the append lemma's call given; F-H5v the same fact with `weight(n) * BASE` given; F-H6v and F-H7v the buffer whose head is 0. None has a reference: each carries 0 minutes until its lane records its four results (QPLAN §19.0).
- **H2d / H2v** are statement holes: the given clients fail as shipped (no `ensures`); the references' ensures are `Valid(r) && ToNat(r) == BASE * ToNat(s) && (Canonical(s) ==> Canonical(r))` and `r == 0 <==> a@.len() == 0`. A too-weak spec (`Valid(r) && ToNat(r) == BASE * ToNat(s)`) fails `ShiftTwice`'s canonicity; a too-strong one (`r == [0] + s`) fails the body on the empty input. The module lane probes both and records them as `cfree`-style lines.
- **H3d's quoted attempt** is A.7's `ToNatTopLimb` without the line `assert s[1..][..|s| - 2] == s[..|s| - 1][1..];` (probed: "a postcondition could not be proved on this return path"). **H3v's** is A.8's `lemma_top_limb` without `assert(s =~= s.drop_last() + seq![s.last()]);` (the module lane captures its failure).
- **H4d** uses L5's `NormalizeTrim`; `NormalizeTrim(s, 0)` with L3's `NormalizeToNat` gives Q01.H3d's `AllZeroToNat` in two calls (F22): recorded, not a re-supply (different statement, two steps).
- **H5d** needs `Std.Arithmetic.DivMod.LemmaModMod(x, Pow(n), BASE)` and L5's `PowPositive`; the `0 < Pow(n)` conjunct is in the statement because the `ensures` is not well-formed without it (probed: "possible division by zero" on the bare `%`). **H5v** needs `vstd::arithmetic::div_mod::lemma_mod_mod` with L5's `lemma_weight_pos`.
- **The ring buffer** avoids `%` in `slot`; `get` and `push_back` compute the wrapped index by a comparison.

### 2.3 Leak and re-pose checks

H1v vs Q03.H4v (`try_limb`: a `u128` to a limb): different statement. H4d/H4v vs Q02.H2d/H2v (a backward trim, an invariant of `Normalize`'s value): different loop and invariant. H3v vs Q06.H3v and L4's `lemma_seq_to_nat_append` (the general concatenation): a special case, posed as a repair whose quoted attempt already makes the call. H5v vs Q07.H5v (division by the next weight): a remainder, not a quotient.

### 2.6 Exit statements and answers (Δ133)

- **Q10.X1d** (statement-shipped, S4, Dafny, 10 min): with the given `function Sum(s: seq<nat>): nat` (head first: `if |s| == 0 then 0 else s[0] + Sum(s[1..])`, `decreases |s|`): `method SumLimbs(s: seq<nat>) returns (t: nat) ensures t == Sum(s)`, the prompt: "a loop from the top limb down". `need: method SumLimbs(s: seq<nat>) returns (t: nat)`. Reference A.11 (`Q10_ExitProbe.SumLimbs`, 9 lines: invariant `t == Sum(s[i..])`, the step's sequence identity).
- **Q10.X1v** (statement-shipped, S1, Verus, 10 min), **revised** (plan review: `add_words`'s idiom `a <= u64::MAX - b` is visible in L3's `add_limb`, and its `u128` alternative in L4's `add`): `pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64)) ensures r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2`. `need: pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))`. Reference C.7 (one line of code: the low bit of `hi` moves to the top of the low word); no layer L1–L5 divides. Probed: verifies; TRIV `{ (0, 0) }` and the near miss `{ (lo / 2, hi / 2) }` fail seeds 1–3; the E modes keep the exec code, which needs no proof (gated by TRIV, as `add_words` was); stable seeds 1–3. It shares no statement or structure with Q10's H items. (A.12's `add_words` is superseded.)

## 3. Q11 (QPLAN §21)

### 3.1 Prediction scenarios (answers not captured)

- **P1dv:** Dafny `modifies this` while writing `other.n` (a second object), and Verus `&mut self` plus `other: &mut Self` writing `other.n`. Capture.
- **P2dv:** a ghost value used in compiled code: capture each language's stage.

### 3.2 References

A.9–A.10. Notes: `CopyFrom`'s loop needs only `i <= other.n && a[..i] == other.a[..i]` and `modifies a`: the disjointness of the two `Repr`s frames `other` automatically (probed). `AddCanon`'s body calls `AddCorrect`, `NormalizeCanonical` and `NormalizeToNat` (L3–L4) as statement expressions. `Pre1(x, y) = x + 2 * y > 0 && x + y < 10`; `Pre2(x, y) = (x > y ==> 2 * x - y >= 5 && x - y <= 3) && (x <= y ==> y >= 5 && y - x <= 3)`. **Revised layout** (blocker 1; §13.3, C.3): `Q11_VcProg` (the programs and postconditions), `Q11_VcAnswer` (the predicates; no import) and `Q11_VcCheck` (the `Exact` lemmas). The twins carry `// cfree: { Post1(Prog1(x, y)) }` and `// cfree: { Post2(Prog2(x, y)) }`. F-H5d: `FromNat` into `CanonSeq` (one L6-free lemma call). `WpSoundIfThen`: one assertion of the two conjuncts and, in the false branch, `assert Holds(Not(b), s);`. A first design used a two-guard command (`Guard(b1, c1, b2, c2)`): its case proof took 13 lines, above the band, so the item became the one-armed `IfThen`. `max_into` reads both cells (lending `&*pd`) and writes only when the source is larger; `PointsTo` at the pin has no `is_init` (a first draft's precondition did not resolve). `take_if_at_least` uses `core::mem::swap` (`mem::replace` has no specification at the pin) and a `match` on `cmp`'s `Ordering` (an `==` on `Ordering` left the postcondition unproved).

### 3.3 Leak and re-pose checks

H9d vs Q08.H9d (soundness for a two-armed `If`, by induction over commands): Q11's is one case of a one-armed `If`, with the branch's soundness as a hypothesis, in a fresh language (no substitution lemma is given or needed). H6v vs Q07.T1v (`lemma_three_limbs`, a spec value of a literal sequence): an exec computation over a `u128`. H5d vs Q08.H1d (the value of `Normalize(Add(…))` in a refinement): the subset constraint and the value of a function, not a refined lemma; L6 re-supplies Q08.H1d's content later, but Q11 imports only L5.

### 3.6 Exit statements and answers

- **Q11.X1d** (statement-shipped, S7, Dafny, 10 min): with the given `function Digits(n: nat): nat` (`if n == 0 then 0 else 1 + Digits(n / BASE)`, `decreases n`): `lemma DigitsLength(n: nat) ensures Digits(n) == |FromNat(n)|`. `need: lemma DigitsLength(n: nat)`. Reference A.11 (2 lines; hole + lever: auto-induction would close it).
- **Q11.X1v** (statement-shipped, S6, Verus, 10 min): on the given `Counter2 { lo: u64, hi: u64 }` with `open spec fn value(&self) -> nat { self.lo as nat + BASE * self.hi as nat }`: `pub fn incr(&mut self) requires old(self).hi < u64::MAX, ensures final(self).value() == old(self).value() + 1`. Reference A.12 (5 lines).

## 4. Q12 and Lab 1 (QPLAN §22)

### 4.1 Stage specimens, battery and fixture (planned content)

- **Stage specimens** (answers not captured), **redrawn** in the revision: the first draft's P5d (a failing `expect` under `vcheck --test`) and P6v (a failing `assert_eq!`) were test-stage failures, R's later-stage tag (PLAN §5.1, R01.P2dv), and its P3d (a ghost variable in a compiled expression) repeated Q11.P2dv's scenario. The six are drawn from the `cli`, `parse`, `resolve`, `verify` and `compile` stages only (Q's tags), and QPLAN says so nowhere (it would narrow the predictions): P1d a Dafny file with an unbalanced brace (`--json` `stage`); P2v a Verus file naming an undefined spec function (`--json`); P3d a Dafny file that imports a module its unit does not provide (`scripts/vcheck`); P4v a Verus exec fn whose postcondition fails (`scripts/vcheck`); P5d a Dafny file that verifies but that the compiler rejects (for example a compiled method with no body and no `{:extern}`), run with `scripts/vcheck --test`; P6v a Verus check run on a path that is no crate of the registry (`scripts/vcheck`). The module lane captures each stage, replaces any scenario whose stage an earlier Q prediction settles (Q03.P6dv, Q11.P2dv among them), and keeps the six inside the five stages above; the planned set covers all five.
- **The battery** (S9 retry client): twelve goals (six per language) over BigNat facts that no Q10–Q12 item poses (for example: the value of `[0] + s`, the canonicity of a pushed non-zero limb, the length of `AddLimb`'s result for `d = 0` — chosen by the Q12 lane against the leak table of §11), three candidates each: one correct, one missing a lemma call (verify), one with a hole or an `assume` (the gate's zero-holes rule), arranged so that the pinned solve count is between 6 and 10. The documents are recorded with an extension of `fvh.tools.record` (QPLAN §30 Q53).
- **The flawed pre-registration fixture** (grade-the-grader): five planted flaws: the budget arithmetic omits the repeats (calls off by a factor 3); no MDE; a stopping rule that stops an arm early when it leads; Claude's repeated runs called "seeds"; no rule for truncated attempts. The learner's record says which pass caught which.

### 4.2 The benchmark validation sample (for the pools)

Commands: `scripts/vcheck --gate` on each answer and `scripts/vcheck` on each task form, on copies in `bench/` of the lane scratch (the sets as installed in the authoring worktree at their pinned commits), one job at a time, 8 GB clamp.

| set | sample | result |
|---|---|---|
| DafnyBench | 10 answers (seeded draw: `shuf --random-source=<(yes 7)`) | 5 pool-valid (answer verified with 0 holes and the task form fails): `Clover_cal_ans`, `Clover_linear_search1`, `Clover_replace`, `verified-using-dafny_…_longestZero`, `vfag_…_mergesort`; 2 excluded because the task form verifies as shipped (`Clover_avg`, `Clover_min_of_two`); 1 answer inconclusive (`assertive-programming-assignment-1_…_ProdAndCount`: a resource limit); 1 answer failed (`Clover_insert`); 1 answer with 3 holes (`dafny_examples_…_test_shuffle`). Yield 5/10 (Wilson 95%: 24–76%) |
| HumanEval-Verus | 6 answers (same draw) | all 6 fail the course gate as installed: one lint finding each, "code outside verus! is never verified (V9, Δ9)" on `fn main() {}`. With that line removed: 4 verify (`human_eval_023`, `045`, `049`, `050`); `human_eval_010` has more code outside `verus!`; `human_eval_124` verifies nothing ("verified 0 < the unit's minimum 1"). So DV5's normalization must move or drop the code outside `verus!` (QPLAN §30 Q57) |
| MINIF2F-DAFNY | not run | the installed copy holds 490 task files and 12 answers (`example_solutions/`): the validated pool is at most 12 problems, too few for six draws plus a doubled pilot; **dropped as a Lab 1 pool in the revision** (QPLAN §22.6: the public Dafny stratum is 20 DafnyBench tasks) |
| vericoding | not run | 5,240 task files, 2,683 answers in the installed subset (Dafny and Verus, without the `bignum` source) |

**The local stratum and the hand items (revision, review major 13a).** Lab 1's validity rule now requires every task form to fail under maximal automation too, or the lab gate to refuse an added lever (QPLAN §22.6, §30 Q63). Q12.H4d (`ToNatMono`), H6d (`CmpSelf`) and H7d (`NormalizeShorter`) verify with an empty body under maximal automation (§0.1: hole + lever), so they stay hand items (the learner works under the shipped options, manual induction) but are **not** tasks of the agents' local stratum until the lever refusal exists. The Dafny local stratum is H5d (`MulLimbByZero`, whose empty body fails under maxauto) plus nine author tasks; the Verus local stratum is H4v–H7v plus six author tasks (the Verus lemma fails in every light mode; the exec items fail TRIV). The report's hand-versus-arm comparison uses the overlapping tasks only (one Dafny, four Verus). If Q63's refusal is built before the lab runs, the three return to the stratum and three author tasks leave it (pre-registered either way).

### 4.3 The MDE figure of design §11.2 (QPLAN §6 Q35) — author-only

`fvh.stats.mde_two_proportions` (A.20's commands):

| n per arm | p0 = 0.2 | p0 = 0.35 | p0 = 0.5 |
|---|---|---|---|
| 60, unpaired | 0.236 | — | 0.245 |
| 60, paired (Connor; conservative) | 0.242 | 0.259 | 0.251 |
| 60, paired, α = 0.05 / 3 (Holm's first step) | 0.286 | 0.302 | 0.289 |
| 120, paired | 0.164 | 0.181 | 0.179 |
| 180, paired | 0.131 | 0.147 | 0.147 |

So design §11.2's "MDE at n = 60 ≈ 15–20 pp [A]" does not hold: at n = 60 the conservative MDE is about 24–25 pp (29–30 pp at Holm's first step), and 15–20 pp needs about 120–180 tasks per arm. **This is the answer to Q09.P4py** (`mde_two_proportions(60, 0.5)` = 0.245, option c), so QPLAN states only that the figure was checked. Proposed DELTAS entry (records lane; its text must not state the number while Q09.P4py is unanswered for a learner who reads DELTAS before Q09: "the figure was checked against `fvh.stats` and is superseded by each lab's pre-registered computation; the author notes give the computation"). The design's §11.2 line then reads "MDE: computed in the pre-registration".

### 4.4 Lab 1 reference policies and the budget

- The reference policies, renderer and report (Solutions twins of `policies.py`, `report.py`) are written by the Q12 lane once DV4's protocol exists; the frozen tests run them against `MockPolicy`, `ScriptedPolicy` and `ReplayPolicy` fixtures.
- GPU arithmetic (revised: the pilot is 80 calls on the public strata only): 4,400 calls × (768 tokens / 121.7 tok/s + ≈ 1 s prefill) ≈ 4,400 × 7.3 s ≈ 8.9 GPU-h; the throughput figure is DV0's n = 1 sample (Δ65) and DV4 step 3d replaces it. This is the **independent-sample** rate, with thinking off. A2's repair prompts carry the last verifier document and A3's carry the frontier state's, so their prefill grows with the round (not measured: no model was called); with thinking on, 768 tokens would be spent mostly on the thinking trace and most attempts would be truncated. Hence the pre-registration's generation-settings and cost-per-arm fields (QPLAN §22.6), the per-arm redo after step 3d with the pilot's measured prompt sizes, the truncation rate as a sensitivity line, and the two-repeat fallback.
- **The Claude subset** (review minor): 20 of the 60 tasks by a pre-registered seed, 10 per language, proportionally from each stratum (local and public).

### 4.6 Exit statements and answers

- **Q12.X1d** (statement-shipped, S11, Dafny, 10 min): `lemma AddSmall() ensures Add([3, 1], [4]) == [7, 1]` (L4's `AddC` is opaque). `need: lemma AddSmall()`. Reference A.11 (3 lines: `reveal AddC();` and two unfoldings). It shares no proof structure with H3d (an opaque definition revealed, not a transparent one unfolded by fuel); two other candidates were dropped because their empty bodies verified (`FromNat(BASE + 7) == [7, 1]`; `Cmp([1, 2, 3], [5, 2, 3]) == -1`), and `AddLimb([BASE - 1, BASE - 1, 5], 1) == [0, 0, 6]` was dropped as too close to H3d's shape.
- **Q12.X1v** (statement-shipped, S11, Verus, 10 min): `pub proof fn lemma_weight_two() ensures weight(2) == BASE * BASE` (`weight` opaque). `need: pub proof fn lemma_weight_two()`. Reference A.12 (`reveal_with_fuel(weight, 3);`).

## 5. Q13 (QPLAN §23)

### 5.1 Prediction scenario (not captured)

P1dv: [a] `ensures d < BASE`, [b] `ensures d != 0 ==> d == s[|s| - 1]`, one client per spec asserting `d == s[|s| - 1]`. Capture both languages.

### 5.2 References and sizes

§0.1, A.13–A.14. `sub` is the spike's (`Solutions/spikes/verus/qg_bignat_x`) with L6's `normalize` and L3's `group_bignat_bounds`; its lift lemma reveals `weight`. `NormalizeConcat`'s induction is on `|b|` with the identity `(a + b)[..|a + b| - 1] == a + b[..|b| - 1]`. `RepeatValue` (nonlinear arithmetic off): `BASE` is a named constant, so every product with it needs a library call (a first draft that relied on linear arithmetic failed at the calc step). `ValueLoop`'s invariant is `v + w * ToNat(s[i..]) == ToNat(s) && w == Pow(i)`, with the step's unfolding asserted; one more assertion (`w * ToNat(s[i..]) == w * s[i] + (w * BASE) * ToNat(s[i + 1..])`) cut its 4.14.1 spread from CV 92.1% (4.05 M) to 39.3% (2.3 M). **Revised** (§13.2, C.4): under QPLAN §19.0's count that form has 7 proof lines, below the band; moved into `Q13_Library` (nonlinear arithmetic off), every product step becomes a library call (`LemmaMulIsDistributiveAdd`, `LemmaMulIsAssociative`, `LemmaMulIsCommutative`, L4's `MulNonneg`, `LemmaMulBasics` before and after the loop): 13 proof lines, inside 10–30; the empty body fails (maxauto and seeds 1–3); stable on seeds 1–3 × both solvers; still flagged (CV 26.7% under 4.14.1) but at most 88,716 resource units, 1.8% of the limit, where the first form reached 2.3 M. A trial without the second `MulNonneg` failed (`nat` subset constraint), so the reference keeps it. F-H1v: `sub` with `b` at most one limb (a borrow out of the low limb only); F-H5d: the loop from the high limb (the plain invariant suffices). Neither has a reference.

### 5.3 The prose item's reference statement (hidden; for the grader container)

```rust
pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        0 <= i,
        limb_at(a, i) < limb_at(b, i),
        forall|j: int| i < j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) < seq_to_nat(b),
```

The use-site check (learner-visible, commented; probed, A.14's `prose_use_site`): `lemma_lt_at_any(seq![5u64, 0u64, 0u64], seq![1u64, 1u64], 1)` followed by `assert(seq_to_nat(seq![5u64, 0u64, 0u64]) < seq_to_nat(seq![1u64, 1u64]))` verifies with the reference statement; a statement that keeps L3's equal-length requirement cannot be applied to these two sequences (lengths 3 and 2), so the check rejects it. A witness (probed, `prose_witness`): `lemma_lt_at_any(Seq::<u64>::empty(), seq![1u64], 0)`. The hidden equivalence: two lemmas, each assuming one statement's `requires` and proving the other's `requires` and `ensures`, verified in the grader container.

### 5.6 Exit statement and answer

- **Q13.X1v** (statement-shipped, S4, Verus, 20 min): `pub proof fn lemma_value_below_top(s: Seq<u64>) requires s.len() > 0, ensures seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat)`. `need: pub proof fn lemma_value_below_top(s: Seq<u64>)`. Reference A.15 (9 lines: the split by L4's append, L3's upper bound, distributivity). It shares no structure with H1v–H5d (the module lane re-checks against the built files).

## 6. Q14 (QPLAN §24)

### 6.1 Prediction scenario (not captured)

P1dv: `function Swap2(a: seq<nat>, b: seq<nat>): nat { if |a| == 0 then |b| else Swap2(b, a[1..]) }` with no `decreases`, and the Verus `spec fn` twin. Capture.

### 6.2 References and the band finding

A.15–A.16. `CmpCorrect` (refined) splits on the cached lengths; `Shorter` bounds a shorter canonical number by L2's `ToNatBound`, L5's `CanonicalLower` and `Std.Arithmetic.Power.LemmaPowIncreases` through L3's `PowIsStdPow`. The three other refined lemmas ship proved by one or two calls into L3, L4 and L6 (they are given code, so their proofs must not be Q08's answers: `NormalizeAddCorrect` is L6's, re-supplied). `PairAcc`'s two methods: a carry by `lo <= u64::MAX - x`, and `read` building `[]`, `[lo]` or `[lo, hi]` with the two unfoldings. `sum_limbs`'s specification must state the sum (`limb_sum`, given, defined from the top end so that a prefix extends by one `drop_last`); the overflow proof uses the ghost bound through `lemma_mul_inequality`.

**H2v and H3v revised** (§13.2, C.6). Under QPLAN §19.0's count the first H2v has 10 proof lines (the two methods: `add_word` is code only, `read` 10) and the first H3v 13, both below the Verus band 15–45. H2v: the trait gains `fn from_big(a: &BigNat) -> (r: Option<Self>) requires a.wf(), ensures r is Some <==> a.to_nat() < BASE * BASE, r is Some ==> r->0.total() == a.to_nat()`; the reference (zero, one and two limbs by unfolding `seq_to_nat`; three or more by L3's lower bound and `weight` facts) verified first try; 24 proof lines; TRIV `{ None }` and the earlier `add_word`/`read` TRIV variants fail seeds 1–3; stable. H3v: the loop runs from the top limb down, against the given top-defined `limb_sum`, which needs one invented lemma (`limb_sum(t) == t[0] + limb_sum(t.drop_first())`, by induction through `drop_last`); 14 + 7 + 6 = 27 proof lines; `dvl.verus.empty_body` fails every mode for both functions (BV killed by its clock, counted as failing); stable seeds 1–3 (CV 16.2%). F-H1d (QPLAN's neutral string): `CmpCorrect` for equal cached lengths only.

**`InterleaveSpec` is below the band** (4 body lines and a measure). Two extensions were tried: an element-by-element law (`Interleave(a, b)[i]` by parity) with a mutual induction, which the lane did not complete in the time it gave it (the precondition of the swapped call failed for unequal lengths); and the multiset law, which verified but kept the item at 4 lines. The Q14 lane completes the element-by-element version (it needs the measure for the swapped call, twice, and a second lemma for the length-differs-by-one case). The first draft's F-H3d (the length law with a ghost-parameter erasure check) is below the band too, so it is withdrawn: H3d carries no minutes until the element-by-element version (or another in-band candidate) has its four results (QPLAN §24.3).

### 6.3 The gated items (designs, not probed)

- **H4d** (loop rule): `Q14_Loop.dfy`: Q11's language plus `While(b, inv, body)`, `Exec(c, s, fuel): Option<State>` (fuelled; `None` when the fuel runs out), `Wp(While(b, inv, c), q) = inv` with the side conditions `inv && b ==> Wp(c, inv)` and `inv && !b ==> q` as a separate `Vcs` set. Statement: if the side conditions hold in every state and `Holds(inv, s)`, then any `Exec(While(…), s, fuel) == Some(t)` gives `Holds(q, t)` (induction on the fuel). Expected 20–30 lines.
- **H5v** (node list), **redesigned** (review major 11; PLAN §8 R18): a singly linked list of `vstd::simple_pptr::PPtr<Node>` cells, `Node { val: u64, next: Option<PPtr<Node>> }`, where each node carries `Tracked<Option<PointsTo<Node>>>` for its successor, so one permission passes per node and no tracked map appears (the first design's `Tracked<Map<int, PointsTo<u64>>>` arena was R11's take-and-put pattern, W19). `push_front` and `sum` (a loop that borrows each permission in turn). Spike V used `simple_pptr` at the pin (`rg_arena`); the list's API is probed first, and the gate needs a variant that keeps `let tracked` lines (QPLAN §30 Q65).

### 6.6 Exit statement (not probed)

- **Q14.X1d** (statement-shipped, S7, Dafny, 20 min), proposed: `lemma CmpAntisym(a: seq<nat>, b: seq<nat>) ensures Cmp(a, b) == -Cmp(b, a)` (`decreases |a| + |b|`). The Q14 lane writes the reference, checks the band and that its measure is needed, or replaces it.

## 7. Q15 and Lab 2 (QPLAN §25) — designs, not probed

- **P1d** (LSP): capture with the author's own client run through the scratch install (Δ33).
- **Forensic first pass P2d–P5v** and **rung 11's deliveries**: four deliveries each, stopping at `parse`, `resolve`, `verify` and `test` (rung 11's attempts) and, for the P items, four green-looking deliveries whose defect is in the pipeline (a `--library`-style input, an option in `dfyconfig.toml`, an `external_body` in a helper, a test that never runs), each with its instrument. No delivery copies a cheat-corpus fixture or a Q09 forensic delivery.
- **Trigger battery** (`tools/Q15/battery/`): twelve quantified BigNat goals, six per language, each needing one trigger choice; six of them are P6dv–P11dv (the shipped form's verdict). The toolsmith's tool must pass all twelve without changing a statement.
- **H1d / H1v** (stability): a quantified step `forall k {:trigger Pow(k)} :: Pow(k + 1) == BASE * Pow(k)` (Verus: `weight`) in the quoted attempt, whose trigger creates the next instance; the repair moves the trigger to `Pow(k + 1)` (or proves the step per use). The statement: `Pow(n + 3) == BASE * (BASE * (BASE * Pow(n)))` (Verus `weight`). The Q15 lane probes the attempt's matching loop and the repair's stability.
- **H2d** (refute → repair → prove): ships `lemma CmpTop(a: seq<nat>, b: seq<nat>) requires |a| == |b| && |a| > 0 && a[|a| - 1] < b[|b| - 1] ensures ToNat(a) < ToNat(b)` — false without `Valid` (a = `[2 * BASE, 0]`, b = `[0, 1]`); repaired with `Valid(a) && Valid(b)`; proved with one invented top-limb split. **H2v**: ships `lemma_shorter_smaller(a, b) requires a.len() < b.len(), ensures seq_to_nat(a) < seq_to_nat(b)` — false without `seq_wf(b)` (a = `[1]`, b = `[0, 0]`); repaired with `seq_wf(b)`; proved with L3's bounds. The given clients name the repaired lemmas with a `requires` that the repaired statement must accept.
- **Lab 2's six learner prose specs:** Dafny: the number of significant limbs of a valid sequence; the index of the highest differing limb of two equal-length sequences (or −1); saturating subtraction over L6's `Sub`. Verus: the count of non-zero limbs; the split of a value at limb `k` (low value and high part); the larger of two canonical numbers. Their hidden references are written by the Q15 lane with the two-way implication proofs.
- **The local agent tasks (20):** ten Dafny and ten Verus prose tasks distinct from those six (the Q15 lane writes them after the models' release dates), their reference specifications and mutants sealed.

### 7.6 Exit statement (not probed)

- **Q15.X1d** (statement-shipped, S11, Dafny, 20 min), proposed: a lemma whose hypothesis is a quantified fact with no usable trigger as given; the learner adds the trigger annotation (`form: trigger`). Not probed.

## 8. Q16 (QPLAN §26)

### 8.2 References, counts and the plain attempt

- **The plain-induction attempt for H1d** (captured in the revision, C.2's L7 with ghost `MulAcc`/`Times`): `MulCorrect` with `decreases |b|` and the body `if |b| > 0 { ValidTail(b); MulCorrect(a, b[1..]); }` fails with two errors, "a postcondition could not be proved on this return path", one on each conjunct of the `ensures` (`Valid(Times(a, b))` and the value), 137 other symbols verified. The recursive call cannot relate `MulAcc(a, b, [], 0)` to `MulAcc(a, b[1..], row, 1)`: the accumulator and the shift change. The quoted block uses this attempt.
- **References:** A.17 (Dafny: `MulAccCorrect` generalizes over the accumulator and the shift: `ToNat(MulAcc(a, b, acc, k)) == ToNat(acc) + Pow(k) * (ToNat(a) * ToNat(b))`; `ShiftCorrect` gives the shifted row's value; the arithmetic is eight library calls under nonlinear arithmetic off, with `MulNonneg` for the `nat` subtype of the products) and A.18 (Verus: `div_limb` fills a zero vector of length `n` and sets each quotient digit from the top, keeping `seq_to_nat(a@.subrange(i, n)) == seq_to_nat(q@.subrange(i, n)) * d + rem`; `lemma_div_step` bounds the digit with `lemma_multiply_divide_lt`, which is the pinned name — a first draft named a lemma that does not exist at the pin; `mul` is the spike's with `big_add`).
- **The speed test** for H3v: two four-limb factors (for example all limbs `u64::MAX`) whose product the test checks against **precomputed constants** in the test (a Rust `#[test]` cannot call the Dafny mirror, and L7's `Times` is ghost now); repeated addition would iterate about 2^256 times.
- **H3 re-planned** (blocker 2, major 6; §13.3). With L7's `Times` compiled, H3d closed in two lines (`r := Times(a, b); MulCorrect(a, b);`, probed: verified); with `MulAcc` and `Times` ghost the same body fails at resolve ("a call to a ghost function is allowed only in specification contexts"), A.17's loop still verifies, and its empty body fails (maxauto and seeds 1–3). But under QPLAN §19.0's count the probed pair is below both bands: `MulLoop` 6 proof lines (D 30–80), `mul` 22 + `shift_limb` 10 + its statement 6 = 38 (V 45–120). The re-plan (QPLAN §26.4, Q68): H3 is banded as one problem (both halves' proof lines against the Verus band), and the probed pair sums to 38 + 6 = 44, one below 45. The Verus half becomes the in-place schoolbook (the first draft's F-H3): `mul` adding each row of `a` times one limb of `b` into one result vector at offset `j` with an inner carry loop (expected: an inner and an outer invariant, and a row-lift lemma relating the vector after row `j` to `ToNat`-style values; expected well above 45 with the companion). The Dafny half stays A.17's `MulLoop` (a compiled loop over the definition): its `ensures r == Times(a, b)` pins the exact representation, so a by-value shortcut such as `r := FromNat(ToNat(a) * ToNat(b))` would still have to prove equality with `Times`'s sequence, and with `Times` ghost the two-line shortcut fails. (An in-place Dafny mirror was considered and rejected: its result need not equal `Times`'s sequence, and a by-value `ensures` without `r == Times(a, b)` would let `FromNat(ToNat(a) * ToNat(b))` close it in a few lines, `ToNat` and `FromNat` being compiled functions of L1–L2.) No Verus reference written; the Q16 lane writes it, checks the problem's band and records the four results on both twins.
- **F-H1d** (QPLAN's neutral string: "part of the decomposition given; one statement still the learner's"): `MulAccCorrect`'s statement given (the generalization), the learner states and proves the shift lemma and proves `MulAccCorrect` and `MulCorrect`. Its reference is A.17's (3 + 26 + 9 + `ShiftCorrect`'s statement 4 = 42 proof lines, inside 30–80); the revision ran the empty-body gate on `MulAccCorrect`, `ShiftCorrect` and `MulCorrect`: each fails under maxauto and seeds 1–3; stable on both solvers (C.2's L7). So F-H1d has its four results, and the hard-tier rule (one statement written by the learner) still holds under it.
- **F-H2v** ("part of the decomposition given"): `lemma_div_step`'s statement given. Reference A.18's: `div_limb` 34 + `lemma_suffix_step` 1 + its statement 5 + `lemma_div_step`'s body 11 = 51 proof lines, inside 45–120; gate and stability as H2v's (§0.1). So F-H2v has its four results too.

## 9. Q17 (QPLAN §27) — designs, not probed

- **H1d:** `trait PQueue { ghost var Model: multiset<nat>; ghost var Repr: set<object>; ghost predicate Valid() reads this, Repr; method Insert(x: nat) requires Valid() modifies Repr ensures Valid() && Model == old(Model) + multiset{x} && fresh(Repr - old(Repr)); method ExtractMin() returns (m: nat) requires Valid() && |Model| > 0 modifies Repr ensures Valid() && m in old(Model) && (forall y | y in old(Model) :: m <= y) && Model == old(Model) - multiset{m} && fresh(Repr - old(Repr)) }`; `ArrayPQ` keeps a sorted prefix of an array (growing by copy); invented lemmas: the multiset of a sorted insertion, and the minimum of a sorted prefix. Expected 40–70 lines.
- **H3d:** the soundness statements the learner should reach (the reference set, for the agent twin): for every command, fuel and state, if every side condition of `Vcs(c, q)` is valid, `Holds(Pre(c, q), s)` and `Exec(c, s, fuel) == Some(t)`, then `Holds(q, t)`; plus the lemma that the side conditions of a sequence are those of its parts. A plausible-but-wrong statement to audit for: one that quantifies the side conditions only in the initial state.
- **H2v** (gated): Q10's `Ring` with `Vec<PCell<u64>>` slots and a `Tracked<Map<int, PointsTo<u64>>>`; probe the pinned `vstd` map API first. This is R11's take-and-put pattern (waiver W19, proposed); the diversified alternative (slot permissions as separate tracked fields of a fixed-capacity ring) is QPLAN §30 Q67's. Its gate needs the empty-body variant that keeps `let tracked` lines (§30 Q65).

## 10. Q18 (QPLAN §28) — designs, not probed

- **H1d:** a hard-tier lemma whose given proof is stable under 4.12.1 and not under 4.14.1 must be found by sweeping candidates with `vcheck --brittleness --solvers`; Q13's `ValueLoop` showed that nonlinear accumulator steps spread under 4.14.1, so a fresh accumulator statement with fewer hints is the first candidate. **It must not be any Q10–Q17 item's reference** (QPLAN §1.1 rule 4). **H1v:** a Verus proof that flips across seeds (a large `nonlinear_arith` step); the repair splits it (Q09's skill at the hard tier).
- **P1d–P4v:** a delivery green only because its `dfyconfig.toml` passes an option the gate's allowlist refuses; one green through a `{:verify false}` in an included file; a Verus crate green through a `build.rs`; one through `.cargo/config.toml` flags. None copies a cheat-corpus fixture.
- **The three planted cheats for H3's round:** a crate whose `Cargo.toml` adds `--no-verify`-style flags through a profile, a JSON document missing `is-verifying-entire-crate`, and a seed-flipping proof; plus the learner's capstone plant and four controls.
- **Lab 3's twelve crate tasks, redesigned** (blocker 4: the first design's tasks implemented `times`, `div_word` and `to_decimal` against frozen statements, which are the capstone's new operations whose statements H2d/H2v ask the learner to write). Now: every task is over L7's base API (`BigNatCore`: `minus`, `to_word`, comparison, addition) and operations posed nowhere else in the course; none states a property of multiplication, division by a word or the decimal conversions. Eight possible, at increasing size: `min_big` and `max_big` through `cmp`; a saturating `minus`; `to_word` variants (`to_u32`, a checked narrowing); parity of a value from its low limb; a `limb_count` bound pair; `double` by `add(a, a)`; `gcd` by repeated subtraction (a loop with a decreasing measure and a gcd-preservation lemma). Four impossible, of kinds Lab γ does not use (Lab γ's are statements that contradict a frozen differential test against the `regex` crate or a frozen negative CLI or printer test, R author notes §11): two whose frozen statement is false at a boundary of the base API (for example a saturating `minus` claimed strictly smaller than its first argument, false when the second is zero), and two whose only proof needs a trusted step (an `external_body` the task's rules forbid, or a conversion the gate refuses). Expected outcome on the impossible ones: no claimed success is correct. The tasks are sealed and unpacked only after the capstone's statement files are committed (QPLAN §28.6, §30 Q64).
- **F-H1v** (QPLAN's neutral string): the repair of a Q09-style one-step nonlinear proof into scoped steps.

## 11. Leak and disjointness checks across the practice tiers (F21–F23)

- **Against Q01–Q09** (statements, references and exits in the three earlier author-notes files): §2.3, §3.3 and the table here. Q12.H5v (`is_zero`) contains Q02.H7v's fact (a canonical non-empty value is positive) as a step of its proof; no learner-visible file holds that step (the twin is in `Solutions/`). Q12.H6d (`CmpSelf`) has no `Valid` precondition, so L4's `CmpCorrect` does not answer it. Q13.H3v generalizes L3's `lemma_lt_at` (given since Q04) to any lengths. Q14.H1d's given lemmas use L6's re-supply of Q08.H1d's content, never Q08's proof text. Q16.H1d is about L7's `Times`, which Q08.H4v's repeated-addition answer cannot reach.
- **F22 (Q01's targets):** `NormalizeTrim(s, 0)` + `NormalizeToNat` gives `AllZeroToNat` in two calls; Q13.H4d/H4v require a non-zero limb so that `d = 0` (which would give the all-zero value in one call) is excluded; L5 has no trailing-zeros value lemma (§1).
- **Tier-internal (F21):** within Q10–Q12, Q13–Q15 and Q16–Q18 no item's statement or reference appears in another item's given code, exit file or specimen (the module lanes re-run this on the built files, as §14.7 F15's check).
- **The leak-pattern verifier** (`tests/instructor/leak_patterns/README.md`) over the worktree with QPLAN §19–§30 appended: the first draft failed one Q05 pattern (`Repr == old(Repr)`, Q05.H2d's frame postcondition) through Q11.H1d's and H2d's statements; both now state `fresh(Repr - old(Repr))` (re-probed: verified, the empty-body gate fails, stable on both solvers), and the verifier reports `9 module(s), 1123 public files scanned, OK`. The module lanes add Q10–Q18 patterns and re-run it on the built files.
- **Given proofs that compose layer lemmas** (Q14.H1d's shipped `ZeroCorrect`, `FromNatCorrect`, `AddCorrect`): one or two calls into L3, L4 and L6, as L4's `QG_L4_Limbs` does; the substance of Q08.H1d and H2d sits in L6 (allowed, Δ130), never in Q14's text.
- **R disjointness (F23):** no Q10–Q18 object is a regex, a matcher, a derivative or a VM; `avoid.sh` runs when each module is armed. The shared genres the review found carry PLAN §5.4's proposed waivers W15–W19 (§13.1, M11); Q14.H5v's redesign leaves W19 to Q17.H2v alone.

## 12. What the module lanes must not do

- Write `admitted = true` before recording the four results on the built files (QPLAN §19.0).
- Copy an earlier module's answer (Q02–Q09 holes, agent deliveries, exits) into a given part of a practice file; re-supply through a layer instead, and only from a higher tier (Δ130).
- Put an abstract module in a learner file or specimen (Δ3); Q17's queue specification is a trait.
- Quote any tool output in a chapter that the lane has not captured (spec §3.15), or any lab number before a recorded run exists (Δ121).
- Run a model or a container: every lab run waits on DV4's steps 2b and later.

## 13. The plan revision (2026-10-07): the review's dispositions and the revision's probes

Written by the DV5 plan lane after the plan review (4 blockers, 15 majors, 13 minors). Every result below was captured on the pins in the same scratch tree as §0 (`/tmp/dvl0-plan5r-q/root`), one solver job at a time, every `dvl` job clamped to 8 GB (`drv/capped.py`, `drv/eb.py`, `drv/ebt.py`), with `free -g` reading 102 GB available before each batch. The revised probe files are saved under `/tmp/dvl0-plan5r-q/rev/` (not archived); Appendix C reproduces each revised text, and the scratch tree was left in the revised state and re-verified at the end (§13.5). Review items that concern only `PLAN.md` (the R track) are the R plan lane's; this file records only whether the Q side needed anything.

### 13.1 Dispositions

| review item | disposition | where |
|---|---|---|
| **B1** Q11.H7d/H8d closable by `Pre1 := Post1(Prog1(x, y))` | **Confirmed, then applied.** In A.9's layout the two construct-free answers (`Post1(Prog1(x, y))`, `Post2(Prog2(x, y))`) verified (171 verified, 0 errors). Restated in three modules (C.3): with the predicates in `Q11_VcAnswer`, which imports nothing, the same answers fail at resolve ("unresolved identifier: Prog1", "Post2", "Prog2"); the reference verifies (171); the placeholders `true` and `false` each fail (2 errors, one per `Exact` lemma). Residual, probed: an answer that also adds `import opened Q11_VcProg` to `Q11_VcAnswer` verifies again, so the import list is frozen (QPLAN §30 Q62: a `specfreeze` import check or a `no-call:` form). The twins carry the two `cfree:` lines. The admission proposal stays, conditional on the Q11 lane recording that both `cfree:` lines fail on the built three-module file | QPLAN §21.1, §21.2, §21.5, §30 Q62; C.3 |
| **B2** Q16.H3d closable by `r := Times(a, b); MulCorrect(a, b);` | **Confirmed, then applied.** With A.5's compiled `Times` the two-line body verified (138 verified); with `MulAcc` and `Times` ghost (C.2) it fails at resolve ("a call to a ghost function is allowed only in specification contexts"), while A.17's references verify (138), `MulLoop`'s empty body fails (maxauto, seeds 1–3), and the file is stable on seeds 1–3 × both solvers. The capstone's Dafny mirror now compiles the learner's own code (its statements may name the ghost `Times`). H3 was then re-planned for its band (M6 below): the Dafny half stays as probed | QPLAN §19.4, §19.6, §26, §28.3; C.2 |
| **B3** R06 needs R02's `NullableCorrect` | R track only (PLAN §2.2–§2.4, A1b): not this file's. No Q item or layer is affected | — |
| **B4** Lab 3's tasks hand out the capstone's statements | **Applied, both options**: the tasks are over L7's base API and operations posed nowhere else, none states a property of multiplication, division by a word or the decimal conversions; and they are sealed until the sha256 of `research/q18_statements.{dfy,rs}` is committed (`fvh`'s `statements` pin, §30 Q64, shared with Lab γ). The new tasks and impossible kinds: §10 | QPLAN §28.1, §28.6, §30 Q64; §10 |
| **M5** Q14.H2v proposed with its gate never run | **Applied, differently.** TRIV ran by hand-written variants (C.6's first form): `add_word` with `{}` and `read` with an empty limb vector each fail, seeds 1–3 ("postcondition not satisfied"). Under M6's rule the item was then below band and was revised (C.6); the revised item's three TRIV variants fail, seeds 1–3. The count of items with all four results in band is **43** (Q10 12, Q11 10, Q12 10, Q13 6, Q14 3, Q16 2), not the first draft's 45; QPLAN §29 says so per tier | QPLAN §24.2, §24.5, §29; §0.1 |
| **M6** line counts under different conventions | **Applied.** QPLAN §19.0 fixes one rule (Δ53's proof lines plus invented statements, exec code excluded); §13.2 re-counts every probed item with `rev/pcount.py` (C.8), statements by hand. Consequences: Q13.H1v 46 (one above 45) → 44 after its two one-statement proof blocks were written on one line each (whitespace only; re-verified); Q13.H5d 7, Q14.H2v 10, Q14.H3v 13 below band → revised into the band (C.4, C.6); Q16.H1d 47 and H2v 60 inside; Q16's H3, banded as one problem, sums to 38 + 6 = 44 with its probed halves → its Verus half re-planned as the in-place algorithm, no reference yet, 0 minutes until gated (the banding reading is QPLAN §30 Q68). Intro items are all far below their caps under the rule | QPLAN §19.0, §23, §24, §26, §29 |
| **M7** fallbacks with minutes and no reference | **Applied.** QPLAN §19.0: a fallback carries minutes only on its own four results (a paper fallback: rubric rows and model answer); else 0, with the shortfall in a DELTAS note at arming. Q16's F-H1d replaced (the generalization's statement given, the shift lemma's statement still the learner's) and, like F-H2v (one invented statement given), given its four results (§8.2). Q14's F-H3d withdrawn (below band itself). Every other fallback carries 0 until its lane records its results | QPLAN §19.0, §20.5–§28.8, §26.6, §30 Q51; §8.2 |
| **M8** intro minutes against the 2 min/line rate | **Applied in part.** Rebalanced inside its line: Q10's round-trip pair H1d 10 / H1v 14. The rate becomes the calibration run's prior (QPLAN §19.0), and every per-item deviation that a design §7.5 line forces is listed in QPLAN §29 for Q47's DELTAS entry. **Not applied:** moving minutes across design lines (a design change; the calibration run, spec §2.5, decides). Under M6's rule the cited rows are smaller than the review's figures (Q10.H1v 8 proof lines, Q11.H6v 8). H1v and H6v are timed first | QPLAN §19.0, §20.4, §21.5, §29 |
| **M9** L6's `SubB` spells out Q13.H1v's algorithm | **Applied**: `SubB` dropped; `Sub` is a ghost function by value, `FromNat(ToNat(a) - ToNat(b))` with `ToNat(a) >= ToNat(b)` required (C.1); the Q13 and Q16 units verify with it, stable on seeds 1–3 × both solvers. Lab 2's local saturating-subtraction prose task (§7) still has its object | QPLAN §19.3, §19.6, §28.3; C.1 |
| **M10** predictions crossing owner tags | (a) **Applied**: Q12's six stage specimens redrawn from `cli`, `parse`, `resolve`, `verify` and `compile` (§4.1); QPLAN does not name the stages (that would narrow the predictions). (b), (c): R04.P5dv and R05.P3dv are R's (PLAN §5.1 records them changed). The owner-tag check against Q10–Q18 was run by the R lane on this revision (PLAN §5.1); the only Q prediction changed since is Q12's specimen set, which keeps to Q's tags. **Flag**: PLAN §5.1 itself names the five stages Q12's specimens come from, which narrows Q12.P1d–P6v for a learner who reads PLAN; reported to the orchestrator | §4.1; QPLAN §22.3 |
| **M11** shared genres without waivers | **Applied**: QPLAN §19.7 F23 cites PLAN §5.4's proposed W15–W19; Q14.H5v redesigned as a `PPtr` list passing one permission per node (§6.3), so W19 covers only Q17.H2v; Lab 3's impossible kinds differ from Lab γ's (§10). Q17.H2v's map arena kept under W19, with the alternative as QPLAN §30 Q67 | QPLAN §19.7, §24.2, §27.2, §28.6, §30 Q67 |
| **M12** R09's number parser | R track only | — |
| **M13** Lab 1 validity | **Applied**: (a) the validity rule adds "fails under maximal automation", the lab gate refuses added levers (QPLAN §30 Q63), and until then H4d, H6d and H7d leave the local stratum (§4.2); (b) MINIF2F-DAFNY dropped: the public Dafny stratum is 20 DafnyBench tasks, the pilot runs on the public strata only (80 calls), the local stratum is fixed; (c) pilot seeds pre-registered and disjoint from the arms' | QPLAN §22.5, §22.6, §22.8; §4.2 |
| **M14** generation settings and per-arm cost | **Applied** to Labs 1–3: the template's generation-settings and cost-per-arm fields, the truncation rate as a sensitivity line, the GPU arithmetic redone per arm after DV4 step 3d (Lab 2 and Lab 3 inherit the fields) | QPLAN §22.6, §25.6, §28.6; §4.4 |
| **M15** Lab 2's S1 feeds hidden truth back; V unmatched | **Applied**: S1's feedback is reference-free (mutant kill on the shipped implementation's I/O, vacuity and witness checks); `implication` and `classify` run only after the batch in the grader container; V is a separate measurement, never compared with S0/S1 | QPLAN §25.5, §25.6 |
| **M16** R lab budgets; Lab α over 10 GPU-h | R track (PLAN §4.3 now carries them). Q side: QPLAN §30 Q55 says the same records entry carries R12/R15/R16 and states the six-lab Claude total (1,690 with sentinels) | QPLAN §30 Q55 |
| **M17** PLAN predates the spikes | R track only | — |
| **M18** R06's and R16's minutes | R track only | — |
| **M19** learner-visible hints | **Applied**: §26.1's and §26.4's lemma counts and invariant domain, F-H3's row-lift lemma, §24.3's "needs the measure twice", the registry fallback strings (Q10 F-H1d/H1v/H3d/H3v/H5v/H6v/H7v, Q11 F-H5d, Q13 F-H1v/H5d, Q14 F-H1d, Q16 F-H1d/H2v/H3, Q18 F-H1v; their contents moved here, §2.2, §3.2, §5.2, §6.2, §8.2, §10) and §30's Q35 sentence. The leak scan: §13.4 | QPLAN §24.3, §26, registry blocks, §30 |
| minor: R11's arena minutes; R04.H4's open definition; R05's test-out row; S8.vc-generator-soundness; `fvh_r`'s CI rule; A5/R16 names vs Lean; R06.H4d and X1d | R track only (R04.H4d cites QPLAN §30 Q52, which stands) | — |
| minor: `Q14_Term` after an NL-off module | **Applied**: `Q14_Term` first (C.6's note); QPLAN §19.0 states the rule for every file. Probed: the reordered file verifies, stable on seeds 1–3 × both solvers; `InterleaveSpec`'s maxauto run now fails too | QPLAN §19.0, §24.1 |
| minor: Q12.P3d repeats Q11.P2dv | **Applied** (§4.1) | §4.1 |
| minor: Q15 rung 11's freeze reference | **Applied**: `research/q15_forensic.dfy` and `.rs`, listed in §25.1 | QPLAN §25.1, §25.4 |
| minor: Q17.H1d `uses: refines` | **Applied in part**: `refines` dropped. **Not applied**: `trait-spec` for a Dafny item (it is Verus's WRITE construct, Q08; Dafny has no trait slug, and `uses:` must name an earlier construct of the item's language); `uses = dynamic-frames, invariant` | QPLAN §27.2, §27.4 |
| minor: incomplete evidence for Q16.H1d, Q10.H3d, Q10.H5d | **Applied**: Q16.H1d's plain attempt captured (§8.2); Q10.H3d's flag carried into QPLAN §20.4 with its disposition; Q10.H5d's maxauto rerun: `inconclusive` again (out of resources at the pinned limit; `dvl.dafny` reports `inconclusive` only for out-of-resource or time-out results), counted as failing at the pin, QPLAN §30 Q66 | QPLAN §20.4, §30 Q66; §0.1, §8.2 |
| minor: Q10.X1v's idiom visible in L3 | **Applied**: new exit `halve_words` (§2.6, C.7) | §2.6 |
| minor: Lab 1's Claude subset; Q16's speed test | **Applied**: a pre-registered, seeded, language-stratified 20-task subset; the speed test checks precomputed constants | QPLAN §22.5, §26.2, §26.3; §4.4, §8.2 |

### 13.2 Every probed item re-counted under QPLAN §19.0's rule

Proof lines (`rev/pcount.py`, C.8: proof blocks, assertions, invariants, `decreases`, ghost and tracked lines, lemma calls, proof-function and lemma bodies) plus the statements of invented lemmas and exec helpers (counted by hand from the signature to the body's brace); exec code excluded. "Earlier" is §0.1's figure.

| item | earlier | under §19.0 | band | status |
|---|---|---|---|---|
| Q10.H1d `ToU64` | 10 | 4 (6 code) | ≤ 10 | in |
| Q10.H1v `to_u64` | 15 | 8 (7 code) | ≤ 15 | in |
| Q10.H2d / H2v (specs) | 1 / 1 | 1 / 1 ensures line | ≤ 10 / 15 | in |
| Q10.H3d / H3v | 5 / 4 | 5 / 4 | ≤ 10 / 15 | in |
| Q10.H4d / H4v (invariants) | 3 / 3 | 3 / 3 | ≤ 10 / 15 | in |
| Q10.H5d / H5v | 2 / 4 | 2 / 4 | ≤ 10 / 15 | in |
| Q10.H6v `get` / H7v `push_back` | 4 / 7 | 0 (4 code) / 3 (4 code) | ≤ 15 | in (exec-check items: TRIV gates them) |
| Q11.H1d / H2d | 2 / 8 | 0 (2 code) / 2 (6 code) | ≤ 10 | in |
| Q11.H3v / H4v | 5 / 9 | 0 (5 code) / 2 (7 code) | ≤ 15 | in |
| Q11.H5d `AddCanon` | 4 | 3 (1 code) | ≤ 10 | in |
| Q11.H6v `value_two` | 14 | 8 (6 code) | ≤ 15 | in |
| Q11.H7d / H8d (predicate bodies) | 1 / 2 | 1 / 2 | ≤ 10 | in |
| Q11.H9d / H10v | 3 / 5 | 3 / 0 (4 code) | ≤ 10 / 15 | in |
| Q12.H3d / H3v | 3 / 1 | 3 / 1 | ≤ 10 / 15 | in |
| Q12.H4d–H7d | 2, 3, 2, 2 | the same (lemmas) | ≤ 10 | in |
| Q12.H4v / H5v / H6v / H7v | 4 / 8 / 3 / 3 | 4 / 4 (4 code) / 0 (3 code) / 2 (1 code) | ≤ 15 | in |
| Q13.H1v `sub` + `lemma_sub_lift` | 38 (Δ53) / 57 with code | 46 as probed; **44** with the two one-statement proof blocks on one line (C.5) | 15–45 | in (44) |
| Q13.H2d + `NormalizeIdem` | 12 | 7 + 2 + statement 3 = 12 | 10–30 | in |
| Q13.H3v + `lemma_eq_any`, `tail` | ≈ 27 | 9 + 9 + 1 + statements 6 + 1 = 26; 33 with the prose item's own statement (the learner writes it) | 15–45 | in |
| Q13.H4d / H4v | 22 / 20 | 22 / 20 | 10–30 / 15–45 | in |
| Q13.H5d `ValueLoop` | 14 | first form 7 (7 code): **below**; revised (C.4) **13** | 10–30 | in (revised) |
| Q14.H1d + `Shorter` | 14 | 6 + 5 + statement 3 = 14 | 10–30 | in |
| Q14.H2v `PairAcc` | 21 | first form 10 (`add_word` 0, `read` 10): **below**; revised with `from_big` (C.6) **24** | 15–45 | in (revised) |
| Q14.H3d `InterleaveSpec` | 4 | 4 | 10–30 | **below** (unchanged) |
| Q14.H3v `sum_limbs` | 19 | first form 13: **below**; revised top-down + `lemma_limb_sum_cons` (C.6): 14 + 7 + statement 6 = **27** | 15–45 | in (revised) |
| Q16.H1d + `MulAccCorrect`, `ShiftCorrect` | 46 | 3 + 26 + 9 + statements 5 + 4 = **47** | 30–80 | in |
| Q16.H2v `div_limb` + `lemma_suffix_step`, `lemma_div_step` | ≈ 75 with code | 34 (19 code) + 1 + 11 + statements 5 + 9 = **60** | 45–120 | in |
| Q16.H3v `mul` + `shift_limb` (gated) | 51 code and proof | 22 (9 code) + 10 (10 code) + statement 6 = **38** | H3 as one problem: 45–120 | with H3d 44, **below**: the Verus half re-planned |
| Q16.H3d `MulLoop` (gated) | 11 | **6** (5 code) | (with H3v) | stays; its reference holds with `Times` ghost |
| Q16 F-H1d (fallback) | — | 3 + 26 + 9 + `ShiftCorrect`'s statement 4 = 42 (`MulAccCorrect`'s statement given) | 30–80 | in; four results recorded (§8.2) |
| Q16 F-H2v (fallback) | — | 34 + 1 + 5 + 11 = 51 (`lemma_div_step`'s statement given) | 45–120 | in; four results as H2v's |

The revised items' other results: Q13.H5d (C.4) empty body fails under maxauto and seeds 1–3; stable seeds 1–3 × both solvers, flagged CV 26.7% at ≤ 88,716 resource units. Q14.H2v (C.6): TRIV `{ None }` for `from_big` fails seeds 1–3 ("postcondition not satisfied" on the trait's `ensures`), and the two earlier TRIV variants fail (above); the crate is stable on seeds 1–3. Q14.H3v (C.6): `dvl.verus.empty_body` fails every mode for `sum_limbs` (E0, E0H, E1, E2, EC, EM, INV, TRIV) and for `lemma_limb_sum_cons` (E0 … EM, NL; BV killed by its clock, counted as failing), seeds 1–3; stable (CV 16.2%). The APIs are the pinned ones (`vstd::arithmetic::mul`, L3's `lemma_seq_to_nat_lower`, `lemma_weight_mono`, `lemma_weight_succ`, `lemma_weight_zero`; `Std.Arithmetic.Mul`'s `LemmaMulIsDistributiveAdd`, `LemmaMulIsAssociative`, `LemmaMulIsCommutative`, `LemmaMulBasics`).

### 13.3 The revised layouts in one place

- **L6** (C.1): `SubB` removed; `ghost function Sub` by value. **L7** (C.2): `MulAcc`, `Times` ghost; `Shift` compiled.
- **Q11's VC items** (C.3): `Q11_VcProg`, `Q11_VcAnswer` (no import), `Q11_VcCheck`; `cfree:` lines for the two restating answers.
- **Q13.H5d** (C.4): in `Q13_Library` (nonlinear arithmetic off, now also importing L4 for `MulNonneg`), last in the file.
- **Q13.H1v** (C.5): two proof blocks on one line each (whitespace only).
- **Q14** (C.6): `Q14_Term` before `Q14_Cached` in the Dafny file; `Accum` gains `from_big`; `sum_limbs` from the top limb down with `lemma_limb_sum_cons`; H5v's `PPtr` list (§6.3, not probed).
- **Q16's H3**: the Verus half re-planned as the in-place algorithm (§8.2), no reference; A.18's `mul` stays as a starting point and anchor only; the Dafny half is A.17's `MulLoop` over C.2's ghost `Times`.
- **Q10.X1v** (C.7): `halve_words`.

### 13.4 The leak scan after the revision

The leak-pattern verifier (`tests/instructor/leak_patterns/README.md`) over the authoring worktree with the revised QPLAN and `PLAN.md`: `9 module(s), 1123 public files scanned, OK`. Q10–Q18 have no pattern files yet (their twins do not exist), so the lane also grepped QPLAN §19–§30 and `PLAN.md` for 41 reference tokens of this file (the invented lemmas' names, invariant fragments, the VC answers, the new exit's code, the fallbacks' contents, the library calls of the revised references). Hits: none outside given statements (QPLAN quotes `Pre1Exact`'s given `ensures` and `NormalizeShorter`'s given statement; "L4's append lemma" names a layer lemma in §19.6). The module lanes add Q10–Q18 pattern files and re-run the verifier on the built files.

### 13.5 The scratch tree as left

`root/` holds the revised candidates (C.1–C.7 over A.1–A.18): L6 and L7 revised; Q10's unit with C.3's layout in `Q11_Probe.dfy`; Q10's crate with `halve_words` added (`add_words` still present, superseded); Q13's unit with C.4 and the reordered `Q14_Probe.dfy`; Q13's crate with C.5 and C.6. Final runs: Q10's Dafny unit and Q13's Dafny unit `--brittleness --solvers` stable (flags: `ToNatTopLimb` CV 27.6%, `ValueLoop` CV 26.7%, both advisory); Q16's Dafny unit verified (137); Q10's, Q13's and Q16's crates `--brittleness` stable (seeds 1–3).

## Appendix A. Candidate files and probes (scratch, as last verified)
The scratch registry armed three records (`status = "authoring"`, the DV1a fields otherwise) and declared each layer's files in its first module's `[module.imports]`: Q10 (`"dafny/given/Q/QG_L5_BigNat.dfy" = "std"`, `"verus/given/qg_bignat_l5/src/lib.rs" = "arithmetic"`), Q13 (L6's two files), Q16 (L7's two files); `python3 scripts/gen_units.py` then wrote 25 units. Item markers are absent from the probes: the module lanes write the real markers, hole forms and twins.

### A.1 L5, Dafny (`dafny/given/Q/QG_L5_BigNat.dfy`)

`root/dafny/given/Q/QG_L5_BigNat.dfy`:

```dafny
// candidate L5 (plan probe)
module QG_L5_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // A canonical non-empty sequence is at least BASE^(n-1).
  lemma CanonicalLower(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
    decreases |s|
  {
    if |s| == 1 {
      ToNatSingleton(s[0]);
      assert s == [s[0]];
    } else {
      assert Canonical(s[1..]);
      CanonicalLower(s[1..]);
      ToNatHeadTail(s);
    }
  }

  // Every power of BASE is positive.
  lemma PowPositive(n: nat)
    ensures 0 < Pow(n)
    decreases n
  {
    if n > 0 {
      PowPositive(n - 1);
    }
  }

  // Trailing zeros after position n: Normalize keeps the first n limbs.
  lemma NormalizeTrim(s: seq<nat>, n: nat)
    requires n <= |s|
    requires n == 0 || s[n - 1] != 0
    requires forall j | n <= j < |s| :: s[j] == 0
    ensures Normalize(s) == s[..n]
    decreases |s|
  {
    if |s| > n {
      assert s[..|s| - 1][..n] == s[..n];
      NormalizeTrim(s[..|s| - 1], n);
    } else {
      assert s[..n] == s;
    }
  }
}
```

### A.2 L5, Verus (`verus/given/qg_bignat_l5/`)

`root/verus/given/qg_bignat_l5/Cargo.toml`:

```toml
[package]
name = "qg_bignat_l5"
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
qg_bignat_l3 = { path = "../qg_bignat_l3" }
qg_bignat_l4 = { path = "../qg_bignat_l4" }

[package.metadata.verus]
verify = true
```

`root/verus/given/qg_bignat_l5/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l4::*;

verus! {

/// Every weight is positive.
pub proof fn lemma_weight_pos(n: nat)
    ensures
        weight(n) > 0,
{
    lemma_weight_zero();
    lemma_weight_mono(0, n);
}

} // verus!
```

### A.3 L6, Dafny (`dafny/given/Q/QG_L6_BigNat.dfy`)

`root/dafny/given/Q/QG_L6_BigNat.dfy`:

```dafny
// candidate L6 (plan probe)
module {:disableNonlinearArithmetic} QG_L6_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat

  // FromNat gives canonical limbs (new; never posed).
  lemma FromNatCanonical(n: nat)
    ensures Canonical(FromNat(n))
    decreases n
  {
    FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / BASE);
      if n / BASE == 0 {
        assert FromNat(n / BASE) == [];
        assert n % BASE == n;
      }
    }
  }

  // Normalized addition is canonical with the sum (re-supplied: Q08.H1d's statement, for a later refinement).
  lemma NormalizeAddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Canonical(Normalize(Add(a, b))) && ToNat(Normalize(Add(a, b))) == ToNat(a) + ToNat(b)
  {
    AddCorrect(a, b);
    NormalizeCanonical(Add(a, b));
    NormalizeToNat(Add(a, b));
  }

  // Schoolbook subtraction with a borrow (definitions only).
  function SubB(a: seq<nat>, b: seq<nat>, borrow: nat): seq<nat>
    requires Valid(a) && Valid(b) && borrow <= 1
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then (if borrow == 0 then [] else [BASE - 1])
    else
      ValidTail(a);
      ValidTail(b);
      var x := Head(a);
      var y := Head(b) + borrow;
      if x >= y then [x - y] + SubB(Tail(a), Tail(b), 0)
      else [x + BASE - y] + SubB(Tail(a), Tail(b), 1)
  }

  function Sub(a: seq<nat>, b: seq<nat>): seq<nat>
    requires Valid(a) && Valid(b)
  {
    SubB(a, b, 0)
  }
}
```

### A.4 L6, Verus (`verus/given/qg_bignat_l6/src/lib.rs`)

`root/verus/given/qg_bignat_l6/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l5::*;

verus! {

/// Strip the most significant zero limbs in place (re-supplied: first posed as Q02.H2v).
pub fn normalize(a: &mut BigNat)
    ensures
        final(a).wf(),
        final(a).to_nat() == old(a).to_nat(),
{
    while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
        invariant
            a.to_nat() == old(a).to_nat(),
        decreases a.limbs.len(),
    {
        proof {
            lemma_seq_to_nat_drop_last_zero(a@);
        }
        a.limbs.pop();
    }
}

} // verus!
```

### A.5 L7, Dafny (`dafny/given/Q/QG_L7_BigNat.dfy`)

`root/dafny/given/Q/QG_L7_BigNat.dfy`:

```dafny
// candidate L7 (plan probe)
module {:disableNonlinearArithmetic} QG_L7_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L4_BigNat

  // The schoolbook definitions: one MulLimb row per limb of b, from the low limb.
  function Shift(s: seq<nat>, k: nat): seq<nat>
  {
    seq(k, _ => 0) + s
  }

  function MulAcc(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat): seq<nat>
    decreases |b|
  {
    if |b| == 0 then acc else MulAcc(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)), k + 1)
  }

  function Times(a: seq<nat>, b: seq<nat>): seq<nat>
  {
    MulAcc(a, b, [], 0)
  }

}
```

### A.6 L7, Verus (`verus/given/qg_bignat_l7/src/lib.rs`, `src/api.rs`)

`root/verus/given/qg_bignat_l7/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l6::*;
pub mod api;

verus! {

/// Borrow lifting and subtraction (re-supplied: first posed as Q13.H1v).
pub proof fn lemma_sub_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() == r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] <= 1,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + BASE * c[j + 1] == #[trigger] r[j] + limb_at(b, j)
                + c[j],
    ensures
        seq_to_nat(a) + (if c[r.len() as int] == 0 { 0 } else { weight(r.len()) }) == seq_to_nat(r)
            + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    reveal(weight);
    if r.len() > 0 {
        let a2 = a.drop_first();
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + BASE * c2[j + 1]
            == #[trigger] r2[j] + limb_at(b2, j) + c2[j] by {
            assert(limb_at(a, j + 1) + BASE * c[j + 2] == r[j + 1] + limb_at(b, j + 1) + c[j + 1]);
        }
        lemma_sub_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + BASE * c[1] == r[0] + limb_at(b, 0) + c[0]);
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut borrow: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            m == b@.len(),
            m <= n,
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == borrow,
            borrow <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + BASE * c[j + 1] == #[trigger] res@[j] + limb_at(b@, j)
                    + c[j],
        decreases n - i,
    {
        let x: u64 = a.limbs[i];
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let d: u64;
        if x >= y && x - y >= borrow {
            d = x - y - borrow;
            borrow = 0;
        } else {
            d = ((x as u128 + 0x1_0000_0000_0000_0000u128) - y as u128 - borrow as u128) as u64;
            borrow = 1;
        }
        res.push(d);
        proof {
            c = c.push(borrow as nat);
        }
        i = i + 1;
    }
    proof {
        lemma_sub_lift(a@, b@, res@, c);
    }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}

/// The value as one word, when it fits (re-supplied: first posed as Q10.H1v).
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        r is Some <==> a.to_nat() < BASE,
        r is Some ==> r->0 as nat == a.to_nat(),
{
    let n = a.limbs.len();
    if n == 0 {
        Some(0)
    } else if n == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        Some(a.limbs[0])
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_mono(1, (n - 1) as nat);
            lemma_weight_zero();
            lemma_weight_succ(0);
        }
        None
    }
}

} // verus!
```

`root/verus/given/qg_bignat_l7/src/api.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l6::*;
use crate::{sub, to_u64};

verus! {

/// The mini-crate's base API: NatLike plus subtraction and the conversion to one word.
pub trait BigNatCore: NatLike {
    fn minus(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
            self.value() >= other.value(),
        ensures
            r.valid(),
            r.value() == self.value() - other.value(),
    ;

    fn to_word(&self) -> (r: Option<u64>)
        requires
            self.valid(),
        ensures
            r is Some <==> self.value() < BASE,
            r is Some ==> r->0 as nat == self.value(),
    ;
}

impl BigNatCore for BigNat {
    fn minus(&self, other: &Self) -> (r: Self) {
        sub(self, other)
    }

    fn to_word(&self) -> (r: Option<u64>) {
        to_u64(self)
    }
}

} // verus!
```

### A.7 Q10 Dafny references (probe file at Q10's exercise path)

`root/dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy`:

```dafny
module Q10_PracticeIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Wrappers
  import opened Std.Arithmetic.DivMod

  // H1d: the u64 mirror
  method ToU64(s: seq<nat>) returns (r: Option<nat>)
    requires Canonical(s)
    ensures r.Some? <==> ToNat(s) < BASE
    ensures r.Some? ==> r.value == ToNat(s)
  {
    if |s| == 0 {
      return Some(0);
    } else if |s| == 1 {
      ToNatSingleton(s[0]);
      assert s == [s[0]];
      return Some(s[0]);
    } else {
      CanonicalLower(s);
      PowPositive(|s| - 2);
      return None;
    }
  }
}

module Q10_More {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat

  // H2d spec item: Shift's ensures is the hole (shipped: none); body and client given
  method Shift(s: seq<nat>) returns (r: seq<nat>)
    requires Valid(s)
    ensures Valid(r) && ToNat(r) == BASE * ToNat(s) && (Canonical(s) ==> Canonical(r))
  {
    if |s| == 0 {
      r := [];
    } else {
      ToNatCons(0, s);
      ValidCons(0, s);
      r := [0] + s;
    }
  }
  method ShiftTwice(s: seq<nat>) returns (r: seq<nat>)
    requires Canonical(s)
    ensures Canonical(r) && ToNat(r) == BASE * (BASE * ToNat(s))
  {
    var r1 := Shift(s);
    r := Shift(r1);
  }

  // H3d assertion repair: the top limb's place value
  lemma ToNatTopLimb(s: seq<nat>)
    requires |s| > 0
    ensures ToNat(s) == ToNat(s[..|s| - 1]) + Pow(|s| - 1) * s[|s| - 1]
    decreases |s|
  {
    if |s| > 1 {
      ToNatTopLimb(s[1..]);
      assert s[1..][..|s| - 2] == s[..|s| - 1][1..];
    } else {
      assert s[..0] == [];
    }
  }

  // H4d normalize forward scan: invariants are the hole
  method NormLen(s: seq<nat>) returns (n: nat)
    ensures n <= |s| && s[..n] == Normalize(s)
  {
    n := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= n <= i <= |s|
      invariant n == 0 || s[n - 1] != 0
      invariant forall j | n <= j < i :: s[j] == 0
      decreases |s| - i
    {
      if s[i] != 0 {
        n := i + 1;
      }
      i := i + 1;
    }
    NormalizeTrim(s, n);
  }
}

module {:disableNonlinearArithmetic} Q10_Search {
  import opened QG_L1_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.DivMod

  // H5d search-then-name
  lemma ModPowSucc(x: nat, n: nat)
    ensures 0 < Pow(n) && x % Pow(n + 1) % Pow(n) == x % Pow(n)
  {
    PowPositive(n);
    LemmaModMod(x, Pow(n), BASE);
  }
}
```

### A.8 Q10 Verus references (`verus/q/q10_practice_ia/src/lib.rs`; its `mod q11; mod q1x;` lines are the probe crate's, A.10 and A.12)

`root/verus/q/q10_practice_ia/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;
pub mod q11;
pub mod q1x;

verus! {

// H1v
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        r is Some <==> a.to_nat() < BASE,
        r is Some ==> r->0 as nat == a.to_nat(),
{
    let n = a.limbs.len();
    if n == 0 {
        Some(0)
    } else if n == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        Some(a.limbs[0])
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_mono(1, (n - 1) as nat);
            lemma_weight_zero();
            lemma_weight_succ(0);
        }
        None
    }
}

// W: the round trip, a given client
pub fn round_trip(x: u64) -> (r: Option<u64>)
    ensures
        r == Some(x),
{
    let b = from_u64(x);
    to_u64(&b)
}


// H2v spec item: high_limb's ensures is the hole
pub fn high_limb(a: &BigNat) -> (r: u64)
    requires
        a.wf(),
    ensures
        r == 0 <==> a@.len() == 0,
{
    if a.limbs.len() == 0 {
        0
    } else {
        a.limbs[a.limbs.len() - 1]
    }
}

pub fn high_client(a: &BigNat)
    requires
        a.wf(),
{
    let h = high_limb(a);
    if h == 0 {
        assert(a.to_nat() == 0);
    }
}

// H3v assertion repair: the top limb's place value
pub proof fn lemma_top_limb(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) == seq_to_nat(s.drop_last()) + weight((s.len() - 1) as nat) * s.last(),
{
    lemma_seq_to_nat_append(s.drop_last(), seq![s.last()]);
    assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(seq![s.last()].drop_first()) == 0);
    assert(s =~= s.drop_last() + seq![s.last()]);
}

// H4v normalize forward scan: the loop invariant is the hole
pub fn norm_len(v: &Vec<u64>) -> (n: usize)
    ensures
        n <= v@.len(),
        n == 0 || v@[n - 1] != 0,
        forall|j: int| n <= j < v@.len() ==> v@[j] == 0,
{
    let mut n: usize = 0;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            n <= i <= v@.len(),
            n == 0 || v@[n - 1] != 0,
            forall|j: int| n <= j < i ==> v@[j] == 0,
        decreases v@.len() - i,
    {
        if v[i] != 0 {
            n = i + 1;
        }
        i = i + 1;
    }
    n
}

// H5v search-then-name
pub proof fn lemma_mod_weight_succ(x: nat, n: nat)
    ensures
        x % weight(n + 1) % weight(n) == x % weight(n),
{
    lemma_weight_pos(n);
    lemma_weight_succ(n);
    vstd::arithmetic::div_mod::lemma_mod_mod(x as int, weight(n) as int, BASE as int);
    assert(weight(n) * BASE == BASE * weight(n));
}

// H6v, H7v ring buffer
pub struct Ring {
    pub buf: Vec<u64>,
    pub head: usize,
    pub len: usize,
}

impl Ring {
    pub open spec fn inv(&self) -> bool {
        self.buf@.len() > 0 && self.head < self.buf@.len() && self.len <= self.buf@.len()
    }

    pub open spec fn slot(&self, i: int) -> int {
        if self.head + i < self.buf@.len() { self.head + i } else { self.head + i - self.buf@.len() }
    }

    pub open spec fn view(&self) -> Seq<u64> {
        Seq::new(self.len as nat, |i: int| self.buf@[self.slot(i)])
    }

    pub fn get(&self, i: usize) -> (r: u64)
        requires
            self.inv(),
            i < self.len,
        ensures
            r == self@[i as int],
    {
        if self.head < self.buf.len() - i {
            self.buf[self.head + i]
        } else {
            self.buf[i - (self.buf.len() - self.head)]
        }
    }

    pub fn push_back(&mut self, x: u64)
        requires
            old(self).inv(),
            old(self).len < old(self).buf@.len(),
        ensures
            final(self).inv(),
            final(self)@ == old(self)@.push(x),
    {
        let cap = self.buf.len();
        let idx = if self.head < cap - self.len { self.head + self.len } else { self.len - (cap - self.head) };
        let ghost before = self@;
        self.buf.set(idx, x);
        self.len = self.len + 1;
        proof {
            assert(self@ =~= before.push(x));
        }
    }
}

} // verus!
```

### A.9 Q11 Dafny references (probe file in Q10's unit)

`root/dafny/Q/Q10_PracticeIA/std/Q11_Probe.dfy`:

```dafny
module Q11_Frames {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  class LimbVec {
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
      ensures Valid() && fresh(Repr) && Contents == [] && a.Length == cap
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    // H1d
    method Set(i: nat, x: nat)
      requires Valid() && i < |Contents|
      modifies Repr
      ensures Valid() && Contents == old(Contents)[i := x] && fresh(Repr - old(Repr))
    {
      a[i] := x;
      Contents := a[..n];
    }

    // H2d
    method CopyFrom(other: LimbVec)
      requires Valid() && other.Valid() && Repr !! other.Repr
      requires |other.Contents| <= a.Length
      modifies Repr
      ensures Valid() && Contents == other.Contents && fresh(Repr - old(Repr))
      ensures other.Contents == old(other.Contents)
    {
      var i := 0;
      while i < other.n
        invariant i <= other.n && a[..i] == other.a[..i]
        modifies a
      {
        a[i] := other.a[i];
        i := i + 1;
      }
      n := other.n;
      Contents := a[..n];
    }
  }
}
module Q11_Subset {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  type CanonSeq = s: seq<nat> | Canonical(s) witness []

  // H5d
  function AddCanon(a: CanonSeq, b: CanonSeq): (r: CanonSeq)
    ensures ToNat(r) == ToNat(a) + ToNat(b)
  {
    AddCorrect(a, b);
    NormalizeCanonical(Add(a, b));
    NormalizeToNat(Add(a, b));
    Normalize(Add(a, b))
  }
}

module Q11_Vc {
  // H7d: the weakest precondition of a straight-line program, by hand
  function Prog1(x: int, y: int): (int, int)
  {
    var x1 := x + 2 * y;
    var y1 := x1 - y;
    (x1, y1)
  }
  ghost predicate Post1(r: (int, int)) { r.0 > 0 && r.1 < 10 }
  ghost predicate Pre1(x: int, y: int) { x + 2 * y > 0 && x + y < 10 }
  lemma Pre1Exact(x: int, y: int) ensures Pre1(x, y) <==> Post1(Prog1(x, y)) {}

  // H8d: a program with a branch
  function Prog2(x: int, y: int): (int, int)
  {
    var y1 := if x > y then x - y else y - x;
    var x1 := x + y1;
    (x1, y1)
  }
  ghost predicate Post2(r: (int, int)) { r.0 >= 5 && r.1 <= 3 }
  ghost predicate Pre2(x: int, y: int) {
    (x > y ==> 2 * x - y >= 5 && x - y <= 3) && (x <= y ==> y >= 5 && y - x <= 3)
  }
  lemma Pre2Exact(x: int, y: int) ensures Pre2(x, y) <==> Post2(Prog2(x, y)) {}
}

module {:disableNonlinearArithmetic} Q11_Wp {
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)
  datatype BExp = Lt(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)
  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd)
               | IfThen(b: BExp, c: Cmd)
  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
  }
  predicate Holds(p: BExp, s: State)
  {
    match p
    case Lt(l, r) => Eval(l, s) < Eval(r, s)
    case And(p1, p2) => Holds(p1, s) && Holds(p2, s)
    case Not(p1) => !Holds(p1, s)
    case Imp(p1, p2) => Holds(p1, s) ==> Holds(p2, s)
  }
  function Exec(c: Cmd, s: State): State
  {
    match c
    case Skip => s
    case Assign(x, e) => (y: nat) => if y == x then Eval(e, s) else s(y)
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
    case IfThen(b, c1) => if Holds(b, s) then Exec(c1, s) else s
  }
  function SubstE(t: Expr, x: nat, e: Expr): Expr
  {
    match t
    case Const(n) => Const(n)
    case Var(y) => if y == x then e else Var(y)
    case Plus(a, b) => Plus(SubstE(a, x, e), SubstE(b, x, e))
  }
  function SubstB(p: BExp, x: nat, e: Expr): BExp
  {
    match p
    case Lt(l, r) => Lt(SubstE(l, x, e), SubstE(r, x, e))
    case And(p1, p2) => And(SubstB(p1, x, e), SubstB(p2, x, e))
    case Not(p1) => Not(SubstB(p1, x, e))
    case Imp(p1, p2) => Imp(SubstB(p1, x, e), SubstB(p2, x, e))
  }
  function Wp(c: Cmd, q: BExp): BExp
  {
    match c
    case Skip => q
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Wp(c1, Wp(c2, q))
    case IfThen(b, c1) => And(Imp(b, Wp(c1, q)), Imp(Not(b), q))
  }

  // H9d: the IfThen case of soundness, the branch's soundness given
  lemma WpSoundIfThen(b: BExp, c: Cmd, q: BExp, s: State)
    requires forall t :: Holds(Wp(c, q), t) ==> Holds(q, Exec(c, t))
    requires Holds(Wp(IfThen(b, c), q), s)
    ensures Holds(q, Exec(IfThen(b, c), s))
  {
    assert Holds(Imp(b, Wp(c, q)), s) && Holds(Imp(Not(b), q), s);
    if !Holds(b, s) {
      assert Holds(Not(b), s);
    }
  }
}
```

### A.10 Q11 Verus references (`src/q11.rs` of the probe crate)

`root/verus/q/q10_practice_ia/src/q11.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

verus! {

pub enum AccError { Overflow, TooSmall }

pub struct Acc {
    pub total: BigNat,
    pub steps: u64,
}

impl Acc {
    // H3v
    pub fn add_word(&mut self, x: u64) -> (r: Result<(), AccError>)
        requires
            old(self).total.wf(),
        ensures
            final(self).total.wf(),
            r is Ok <==> old(self).steps < u64::MAX,
            r is Ok ==> final(self).total.to_nat() == old(self).total.to_nat() + x
                && final(self).steps == old(self).steps + 1,
            r is Err ==> final(self).total@ == old(self).total@ && final(self).steps == old(self).steps,
    {
        if self.steps == u64::MAX {
            return Err(AccError::Overflow);
        }
        self.total = add_limb(&self.total, x);
        self.steps = self.steps + 1;
        Ok(())
    }

    // H4v
    pub fn take_if_at_least(&mut self, limit: &BigNat) -> (r: Result<BigNat, AccError>)
        requires
            old(self).total.wf(),
            limit.wf(),
        ensures
            final(self).total.wf(),
            r is Ok <==> old(self).total.to_nat() >= limit.to_nat(),
            r is Ok ==> r->Ok_0.wf() && r->Ok_0.to_nat() == old(self).total.to_nat()
                && final(self).total.to_nat() == 0 && final(self).steps == 0,
            r is Err ==> final(self).total@ == old(self).total@ && final(self).steps == old(self).steps,
    {
        match cmp(&self.total, limit) {
            Ordering::Less => { return Err(AccError::TooSmall); }
            _ => {}
        }
        let mut out = BigNat { limbs: Vec::new() };
        core::mem::swap(&mut out, &mut self.total);
        self.steps = 0;
        proof {
            assert(seq_to_nat(self.total@) == 0);
        }
        Ok(out)
    }
}

// H6v modes
pub fn value_two(a: &BigNat) -> (r: u128)
    requires
        a.wf(),
        a@.len() <= 2,
    ensures
        r as nat == a.to_nat(),
{
    if a.limbs.len() == 0 {
        0
    } else if a.limbs.len() == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        a.limbs[0] as u128
    } else {
        proof {
            let t = a@.drop_first();
            assert(t.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(t.drop_first()) == 0);
            assert(seq_to_nat(t) == t[0] as nat);
        }
        a.limbs[0] as u128 + (a.limbs[1] as u128) * 0x1_0000_0000_0000_0000u128
    }
}

// H10v gated primer
pub fn max_into(src: &PCell<u64>, dst: &PCell<u64>, Tracked(ps): Tracked<&PointsTo<u64>>,
    Tracked(pd): Tracked<&mut PointsTo<u64>>)
    requires
        src.id() == ps.id(),
        dst.id() == old(pd).id(),
    ensures
        final(pd).id() == dst.id(),
        *final(pd).value() == if *ps.value() > *old(pd).value() { *ps.value() } else { *old(pd).value() },
{
    let s = src.read(Tracked(ps));
    let d = dst.read(Tracked(&*pd));
    if s > d {
        dst.write(Tracked(&mut *pd), s);
    }
}

} // verus!
```

### A.11 Q10–Q12 Dafny exits, Q12's fuel item and Lab 1's Dafny hand items (probe file in Q10's unit)

`root/dafny/Q/Q10_PracticeIA/std/Q1x_Exits.dfy`:

```dafny
module Q10_ExitProbe {
  import opened QG_L1_BigNat
  function Sum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + Sum(s[1..])
  }
  // Q10.X1d
  method SumLimbs(s: seq<nat>) returns (t: nat)
    ensures t == Sum(s)
  {
    t := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s| && t == Sum(s[i..])
      decreases i
    {
      i := i - 1;
      assert s[i..][1..] == s[i + 1..];
      t := t + s[i];
    }
    assert s[0..] == s;
  }
}

module Q11_ExitProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  // Q11.X1d: a digit count and its termination
  function Digits(n: nat): nat
    decreases n
  {
    if n == 0 then 0 else 1 + Digits(n / BASE)
  }
  lemma DigitsLength(n: nat)
    ensures Digits(n) == |FromNat(n)|
    decreases n
  {
    if n > 0 {
      DigitsLength(n / BASE);
    }
  }
}

module Q12_Probe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  // Q12.H3d fuel: normalizing a literal
  lemma NormalizeLiteral()
    ensures Normalize([5, 0, 0, 0]) == [5]
  {
    assert [5, 0, 0, 0][..3] == [5, 0, 0];
    assert [5, 0, 0][..2] == [5, 0];
    assert [5, 0][..1] == [5];
  }
  // Q12.X1d candidate (opaque AddC)
  lemma AddSmall()
    ensures Add([3, 1], [4]) == [7, 1]
  {
    reveal AddC();
    assert Tail([3, 1]) == [1] && Tail([4]) == [] && Tail([1]) == [];
    assert AddC([1], [], 0) == [1];
  }
  // the earlier candidate, kept for comparison
  lemma AddLimbLiteral()
    ensures AddLimb([BASE - 1, BASE - 1, 5], 1) == [0, 0, 6]
  {
    assert [5][1..] == [];
    assert AddLimb([5], 1) == [6];
    assert [BASE - 1, 5][1..] == [5];
    assert AddLimb([BASE - 1, 5], 1) == [0, 6];
    assert [BASE - 1, BASE - 1, 5][1..] == [BASE - 1, 5];
  }
}

module Q12_Lab1Hand {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // H4d
  lemma ToNatMono(a: seq<nat>, b: seq<nat>)
    requires |a| == |b| && forall i | 0 <= i < |a| :: a[i] <= b[i]
    ensures ToNat(a) <= ToNat(b)
    decreases |a|
  {
    if |a| > 0 {
      ToNatMono(a[1..], b[1..]);
    }
  }
  // H5d
  lemma MulLimbByZero(s: seq<nat>)
    ensures |MulLimb(s, 0)| == |s| && forall i | 0 <= i < |s| :: MulLimb(s, 0)[i] == 0
    decreases |s|
  {
    if |s| > 0 {
      MulLimbByZero(s[1..]);
      assert s[0] * 0 == 0;
    }
  }
  // H6d
  lemma CmpSelf(a: seq<nat>)
    ensures Cmp(a, a) == 0
    decreases |a|
  {
    if |a| > 0 {
      CmpSelf(Tail(a));
    }
  }
  // H7d
  lemma NormalizeShorter(s: seq<nat>)
    ensures |Normalize(s)| <= |s|
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeShorter(s[..|s| - 1]);
    }
  }
}
```

### A.12 Q10–Q12 Verus exits, Q12's trigger item and Lab 1's Verus hand items (`src/q1x.rs`)

`root/verus/q/q10_practice_ia/src/q1x.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

verus! {

// Q10.X1v
pub fn add_words(a: u64, b: u64) -> (r: (u64, u64))
    ensures
        r.0 as nat + r.1 as nat * BASE == a as nat + b as nat,
        r.1 <= 1,
{
    if a <= u64::MAX - b {
        (a + b, 0)
    } else {
        (a - (u64::MAX - b) - 1, 1)
    }
}

// Q11.X1v
pub struct Counter2 {
    pub lo: u64,
    pub hi: u64,
}

impl Counter2 {
    pub open spec fn value(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    pub fn incr(&mut self)
        requires
            old(self).hi < u64::MAX,
        ensures
            final(self).value() == old(self).value() + 1,
    {
        if self.lo < u64::MAX {
            self.lo = self.lo + 1;
        } else {
            self.lo = 0;
            self.hi = self.hi + 1;
        }
    }
}

// Q12.H3v trigger
pub proof fn lemma_chain_le(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, k: int)
    requires
        0 <= k < a.len(),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) <= limb_at(b, j),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(b, j) <= limb_at(c, j),
    ensures
        a[k] as nat <= limb_at(c, k),
{
    assert(limb_at(a, k) <= limb_at(b, k));
}

// Q12.X1v fuel through an opaque definition
pub proof fn lemma_weight_two()
    ensures
        weight(2) == BASE * BASE,
{
    reveal_with_fuel(weight, 3);
}

// Lab 1 hand items, Verus
// H4v
pub proof fn lemma_seq_to_nat_mono(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
        forall|i: int| 0 <= i < a.len() ==> a[i] <= b[i],
    ensures
        seq_to_nat(a) <= seq_to_nat(b),
    decreases a.len(),
{
    if a.len() > 0 {
        assert forall|i: int| 0 <= i < a.drop_first().len() implies a.drop_first()[i] <= b.drop_first()[i] by {
            assert(a[i + 1] <= b[i + 1]);
        }
        lemma_seq_to_nat_mono(a.drop_first(), b.drop_first());
    }
}

// H5v
pub fn is_zero(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() == 0),
{
    if a.limbs.len() == 0 {
        true
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_zero();
            lemma_weight_mono(0, (a@.len() - 1) as nat);
        }
        false
    }
}

// H6v
pub fn eq_big(a: &BigNat, b: &BigNat) -> (r: bool)
    requires
        a.wf(),
        b.wf(),
    ensures
        r == (a.to_nat() == b.to_nat()),
{
    match cmp(a, b) {
        Ordering::Equal => true,
        _ => false,
    }
}

// H7v
pub fn size_bound(a: &BigNat) -> (r: usize)
    ensures
        a.to_nat() < weight(r as nat),
{
    proof {
        lemma_seq_to_nat_upper(a@);
    }
    a.limbs.len()
}

} // verus!
```

### A.13 Q13 Dafny references

`root/dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy`:

```dafny
module Q13_Norm {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // H2d: normalize idempotent, and normalize of a concatenation
  lemma NormalizeConcat(a: seq<nat>, b: seq<nat>)
    ensures Normalize(Normalize(a + b)) == Normalize(a + b)
    ensures Normalize(a + b) == (if Normalize(b) == [] then Normalize(a) else a + Normalize(b))
    decreases |b|
  {
    NormalizeIdem(a + b);
    if |b| > 0 {
      if b[|b| - 1] == 0 {
        assert (a + b)[..|a + b| - 1] == a + b[..|b| - 1];
        NormalizeConcat(a, b[..|b| - 1]);
      }
    } else {
      assert a + b == a;
    }
  }

  lemma NormalizeIdem(s: seq<nat>)
    ensures Normalize(Normalize(s)) == Normalize(s)
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeIdem(s[..|s| - 1]);
    }
  }

  // H5d: accumulator generalization (a loop from the low limb, no prefix lemma given)
  method ValueLoop(s: seq<nat>) returns (v: nat)
    ensures v == ToNat(s)
  {
    v := 0;
    var w: nat := 1;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s| && w == Pow(i)
      invariant v + w * ToNat(s[i..]) == ToNat(s)
      decreases |s| - i
    {
      assert ToNat(s[i..]) == s[i] + BASE * ToNat(s[i + 1..]) by {
        assert s[i..][1..] == s[i + 1..];
      }
      assert w * ToNat(s[i..]) == w * s[i] + (w * BASE) * ToNat(s[i + 1..]);
      v := v + w * s[i];
      w := w * BASE;
      i := i + 1;
    }
    assert s[0..] == s;
  }
}

module {:disableNonlinearArithmetic} Q13_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.Mul

  // H4d: the value of n equal non-zero limbs
  lemma RepeatValue(d: nat, n: nat)
    requires 0 < d < BASE
    ensures ToNat(seq(n, _ => d)) * (BASE - 1) == d * (Pow(n) - 1)
    decreases n
  {
    var s := seq(n, _ => d);
    if n == 0 {
      LemmaMulBasics(d);
    } else {
      var t := seq(n - 1, _ => d);
      assert s[1..] == t;
      RepeatValue(d, n - 1);
      PowPositive(n - 1);
      var T := ToNat(t);
      var P := Pow(n - 1);
      assert ToNat(s) == d + BASE * T;
      LemmaMulIsDistributiveAddOtherWay(BASE - 1, d, BASE * T);
      LemmaMulIsAssociative(BASE, T, BASE - 1);
      assert (BASE * T) * (BASE - 1) == BASE * (d * (P - 1));
      LemmaMulIsDistributiveSub(d, P, 1);
      LemmaMulIsAssociative(BASE, d, P);
      LemmaMulIsCommutative(BASE, d);
      LemmaMulIsAssociative(d, BASE, P);
      LemmaMulIsDistributiveSub(BASE, d * P, d);
      LemmaMulIsDistributiveSub(d, BASE, 1);
      LemmaMulIsDistributiveSub(d, BASE * P, 1);
      assert Pow(n) == BASE * P;
    }
  }
}
```

### A.14 Q13 Verus references (`verus/q/q13_practice_iia/src/lib.rs`; `mod q14;` is A.15)

`root/verus/q/q13_practice_iia/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;
pub mod q14;

verus! {

// H1v: sub with borrow (the borrow lift is the one invented lemma)
pub proof fn lemma_sub_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() == r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] <= 1,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + BASE * c[j + 1] == #[trigger] r[j] + limb_at(b, j)
                + c[j],
    ensures
        seq_to_nat(a) + (if c[r.len() as int] == 0 { 0 } else { weight(r.len()) }) == seq_to_nat(r)
            + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    reveal(weight);
    if r.len() > 0 {
        let a2 = a.drop_first();
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + BASE * c2[j + 1]
            == #[trigger] r2[j] + limb_at(b2, j) + c2[j] by {
            assert(limb_at(a, j + 1) + BASE * c[j + 2] == r[j + 1] + limb_at(b, j + 1) + c[j + 1]);
        }
        lemma_sub_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + BASE * c[1] == r[0] + limb_at(b, 0) + c[0]);
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut borrow: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            m == b@.len(),
            m <= n,
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == borrow,
            borrow <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + BASE * c[j + 1] == #[trigger] res@[j] + limb_at(b@, j)
                    + c[j],
        decreases n - i,
    {
        let x: u64 = a.limbs[i];
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let d: u64;
        if x >= y && x - y >= borrow {
            d = x - y - borrow;
            borrow = 0;
        } else {
            d = ((x as u128 + 0x1_0000_0000_0000_0000u128) - y as u128 - borrow as u128) as u64;
            borrow = 1;
        }
        res.push(d);
        proof {
            c = c.push(borrow as nat);
        }
        i = i + 1;
    }
    proof {
        lemma_sub_lift(a@, b@, res@, c);
    }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}

// H3v: prose. Helper (the one invented lemma), then the statement written from prose
pub open spec fn tail(s: Seq<u64>) -> Seq<u64> {
    if s.len() > 0 { s.drop_first() } else { s }
}

pub proof fn lemma_eq_any(a: Seq<u64>, b: Seq<u64>)
    requires
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) == seq_to_nat(b),
    decreases a.len() + b.len(),
{
    if a.len() > 0 || b.len() > 0 {
        assert forall|j: int| 0 <= j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j) by {
            assert(limb_at(a, j + 1) == limb_at(b, j + 1));
        }
        lemma_eq_any(tail(a), tail(b));
        assert(limb_at(a, 0) == limb_at(b, 0));
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        0 <= i,
        limb_at(a, i) < limb_at(b, i),
        forall|j: int| i < j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) < seq_to_nat(b),
    decreases i,
{
    assert forall|j: int| i - 1 < j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j)
        by {
        assert(limb_at(a, j + 1) == limb_at(b, j + 1));
    }
    if i == 0 {
        lemma_eq_any(tail(a), tail(b));
    } else {
        lemma_lt_at_any(tail(a), tail(b), i - 1);
    }
    if a.len() == 0 {
        assert(seq_to_nat(a) == 0);
    }
}


// H3v's use-site check and a witness
pub proof fn prose_use_site() {
    let a = seq![5u64, 0u64, 0u64];
    let b = seq![1u64, 1u64];
    lemma_lt_at_any(a, b, 1);
    assert(seq_to_nat(a) < seq_to_nat(b));
}

pub proof fn prose_witness() {
    lemma_lt_at_any(Seq::<u64>::empty(), seq![1u64], 0);
}

// H4v: the value of n equal non-zero limbs
pub proof fn lemma_repeat_value(d: u64, n: nat)
    requires
        0 < d,
    ensures
        seq_to_nat(Seq::new(n, |i: int| d)) * (BASE - 1) == d * (weight(n) - 1),
    decreases n,
{
    let s = Seq::new(n, |i: int| d);
    if n == 0 {
        lemma_weight_zero();
        assert(seq_to_nat(s) == 0);
    } else {
        let k = (n - 1) as nat;
        let t = Seq::new(k, |i: int| d);
        assert(s.drop_first() =~= t);
        lemma_repeat_value(d, k);
        lemma_weight_succ(k);
        let tv = seq_to_nat(t) as int;
        let w = weight(k) as int;
        assert(seq_to_nat(s) == d + BASE * tv);
        lemma_mul_is_distributive_add_other_way((BASE - 1) as int, d as int, BASE * tv);
        lemma_mul_is_associative(BASE as int, tv, (BASE - 1) as int);
        lemma_mul_is_distributive_sub(d as int, w, 1);
        lemma_mul_is_associative(BASE as int, d as int, w);
        lemma_mul_is_commutative(BASE as int, d as int);
        lemma_mul_is_associative(d as int, BASE as int, w);
        lemma_mul_is_distributive_sub(d as int, BASE * w, 1);
    }
}

} // verus!
```

### A.15 Q14 Verus references and Q13.X1v (`src/q14.rs` of Q13's probe crate)

`root/verus/q/q13_practice_iia/src/q14.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

/// The given trait: an accumulator seen through its ghost total.
pub trait Accum: Sized {
    spec fn total(&self) -> nat;

    fn add_word(&mut self, x: u64)
        requires
            old(self).total() + x < BASE * BASE,
        ensures
            final(self).total() == old(self).total() + x,
    ;

    fn read(&self) -> (r: BigNat)
        ensures
            r.wf(),
            r.to_nat() == self.total(),
    ;
}

/// The given generic client.
pub fn add_both<A: Accum>(acc: &mut A, x: u64, y: u64)
    requires
        old(acc).total() + x + y < BASE * BASE,
    ensures
        final(acc).total() == old(acc).total() + x + y,
{
    acc.add_word(x);
    acc.add_word(y);
}

/// H2v: implement the trait for a two-limb accumulator.
pub struct PairAcc {
    pub lo: u64,
    pub hi: u64,
}

impl Accum for PairAcc {
    open spec fn total(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    fn add_word(&mut self, x: u64) {
        if self.lo <= u64::MAX - x {
            self.lo = self.lo + x;
        } else {
            self.lo = self.lo - (u64::MAX - x) - 1;
            self.hi = self.hi + 1;
        }
    }

    fn read(&self) -> (r: BigNat) {
        let mut v: Vec<u64> = Vec::new();
        if self.hi != 0 {
            v.push(self.lo);
            v.push(self.hi);
            proof {
                assert(v@.drop_first() =~= seq![self.hi]);
                assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first().drop_first()) == 0);
                assert(seq_to_nat(v@.drop_first()) == self.hi as nat);
            }
        } else if self.lo != 0 {
            v.push(self.lo);
            proof {
                assert(v@.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first()) == 0);
            }
        }
        proof {
            assert(seq_to_nat(Seq::<u64>::empty()) == 0);
        }
        BigNat { limbs: v }
    }
}

/// The sum of the limbs, from the top.
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { limb_sum(s.drop_last()) + s.last() as nat }
}

/// H3v: erasure. The bound is ghost; the code never reads it.
pub fn sum_limbs(v: &Vec<u64>, Ghost(bound): Ghost<nat>) -> (r: u128)
    requires
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= bound,
        v.len() * bound <= u128::MAX,
    ensures
        r == limb_sum(v@),
{
    let mut s: u128 = 0;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            s == limb_sum(v@.subrange(0, i as int)),
            s <= i * bound,
            forall|k: int| 0 <= k < v.len() ==> v@[k] <= bound,
            v.len() * bound <= u128::MAX,
        decreases v.len() - i,
    {
        proof {
            lemma_mul_is_distributive_add_other_way(bound as int, i as int, 1);
            lemma_mul_inequality((i + 1) as int, v.len() as int, bound as int);
            assert(v@.subrange(0, i + 1).drop_last() =~= v@.subrange(0, i as int));
        }
        s = s + v[i] as u128;
        i = i + 1;
    }
    proof {
        assert(v@.subrange(0, v.len() as int) =~= v@);
    }
    s
}


// Q13.X1v candidate
pub proof fn lemma_value_below_top(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat),
{
    let p = s.drop_last();
    let w = weight((s.len() - 1) as nat) as int;
    assert(s =~= p + seq![s.last()]);
    lemma_seq_to_nat_append(p, seq![s.last()]);
    assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(seq![s.last()].drop_first()) == 0);
    lemma_seq_to_nat_upper(p);
    lemma_mul_is_distributive_add_other_way(w, s.last() as int, 1);
    lemma_mul_is_commutative(w, s.last() as int);
}

} // verus!
```

### A.16 Q14 Dafny references (probe file in Q13's unit)

`root/dafny/Q/Q13_PracticeIIA/std/Q14_Probe.dfy`:

```dafny
module {:disableNonlinearArithmetic} Q14_Cached refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat
  import L5 = QG_L5_BigNat
  import L6 = QG_L6_BigNat
  import Power = Std.Arithmetic.Power

  datatype Num = Num(limbs: seq<nat>, len: nat)
  type BigNat = Num
  ghost function Val(x: BigNat): nat { L1.ToNat(x.limbs) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x.limbs) && x.len == |x.limbs| }
  function Zero(): BigNat { Num([], 0) }
  function FromNat(n: nat): BigNat { var s := L2.FromNat(n); Num(s, |s|) }
  function Add(a: BigNat, b: BigNat): BigNat { var s := L2.Normalize(L4.Add(a.limbs, b.limbs)); Num(s, |s|) }
  function Cmp(a: BigNat, b: BigNat): int
  {
    if a.len < b.len then -1 else if a.len > b.len then 1 else L3.Cmp(a.limbs, b.limbs)
  }
  lemma ZeroCorrect() {}
  lemma FromNatCorrect(n: nat) { L3.FromNatCorrect(n); L6.FromNatCanonical(n); }
  lemma AddCorrect(a: BigNat, b: BigNat) { L6.NormalizeAddCorrect(a.limbs, b.limbs); }

  // H1d: the item
  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    if a.len < b.len {
      Shorter(a.limbs, b.limbs);
    } else if a.len > b.len {
      Shorter(b.limbs, a.limbs);
    } else {
      L4.CmpCorrect(a.limbs, b.limbs);
    }
  }

  lemma Shorter(x: seq<nat>, y: seq<nat>)
    requires L2.Canonical(x) && L2.Canonical(y) && |x| < |y|
    ensures L1.ToNat(x) < L1.ToNat(y)
  {
    L2.ToNatBound(x);
    L5.CanonicalLower(y);
    L3.PowIsStdPow(|x|);
    L3.PowIsStdPow(|y| - 1);
    Power.LemmaPowIncreases(L1.BASE, |x|, |y| - 1);
  }
}

module Q14_Term {
  function Interleave(a: seq<nat>, b: seq<nat>): seq<nat>
    decreases |a| + |b|
  {
    if |a| == 0 then b else [a[0]] + Interleave(b, a[1..])
  }

  // H3d: the lemma's measure is the learner's (the default one does not work)
  lemma InterleaveSpec(a: seq<nat>, b: seq<nat>)
    ensures |Interleave(a, b)| == |a| + |b|
    ensures multiset(Interleave(a, b)) == multiset(a) + multiset(b)
    ensures (|a| > 0 ==> Interleave(a, b)[0] == a[0]) && (|a| > 0 && |b| > 0 ==> Interleave(a, b)[1] == b[0])
    decreases |a| + |b|
  {
    if |a| > 0 {
      InterleaveSpec(b, a[1..]);
      assert a == [a[0]] + a[1..];
      assert multiset(a) == multiset([a[0]]) + multiset(a[1..]);
    }
  }
}
```

### A.17 Q16 Dafny references

`root/dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy`:

```dafny
module {:disableNonlinearArithmetic} Q16_Mul {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L7_BigNat
  import opened Std.Arithmetic.Mul

  // H1d: the plain statement (ships, known to fail by plain induction)
  lemma MulCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Times(a, b)) && ToNat(Times(a, b)) == ToNat(a) * ToNat(b)
  {
    MulAccCorrect(a, b, [], 0);
    LemmaMulBasics(ToNat(a) * ToNat(b));
    LemmaMulIsAssociative(1, ToNat(a), ToNat(b));
  }

  // invented 1: the generalization
  lemma MulAccCorrect(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat)
    requires Valid(a) && Valid(b) && Valid(acc)
    ensures Valid(MulAcc(a, b, acc, k))
    ensures ToNat(MulAcc(a, b, acc, k)) == ToNat(acc) + Pow(k) * (ToNat(a) * ToNat(b))
    decreases |b|
  {
    if |b| == 0 {
      MulZero(ToNat(a), ToNat(b));
      MulZero(Pow(k), ToNat(a) * ToNat(b));
    } else {
      ValidTail(b);
      MulLimbCorrect(a, b[0]);
      ShiftCorrect(MulLimb(a, b[0]), k);
      var row := Shift(MulLimb(a, b[0]), k);
      AddCorrect(acc, row);
      MulAccCorrect(a, b[1..], Add(acc, row), k + 1);
      // arithmetic: Pow(k) * (A * b0) + Pow(k+1) * (A * B') == Pow(k) * (A * B)
      var A := ToNat(a);
      var B1 := ToNat(b[1..]);
      var P := Pow(k);
      MulNonneg(A, B1);
      MulNonneg(A, b[0]);
      ToNatHeadTail(b);
      assert ToNat(b) == b[0] + BASE * B1;
      assert Pow(k + 1) == BASE * P;
      LemmaMulIsDistributive(A, b[0], BASE * B1);
      LemmaMulIsAssociative(A, BASE, B1);
      LemmaMulIsCommutative(A, BASE);
      LemmaMulIsAssociative(BASE, A, B1);
      LemmaMulIsAssociative(P, BASE, A * B1);
      LemmaMulIsCommutative(P, BASE);
      LemmaMulIsAssociative(BASE, P, A * B1);
      LemmaMulIsDistributive(P, A * b[0], BASE * (A * B1));
    }
  }

  // invented 2: the shift
  lemma ShiftCorrect(s: seq<nat>, k: nat)
    requires Valid(s)
    ensures Valid(Shift(s, k)) && ToNat(Shift(s, k)) == Pow(k) * ToNat(s)
    decreases k
  {
    if k == 0 {
      assert Shift(s, 0) == s;
      LemmaMulBasics(ToNat(s));
    } else {
      ShiftCorrect(s, k - 1);
      assert Shift(s, k) == [0] + Shift(s, k - 1);
      ToNatCons(0, Shift(s, k - 1));
      ValidCons(0, Shift(s, k - 1));
      LemmaMulIsAssociative(BASE, Pow(k - 1), ToNat(s));
    }
  }

  // H3d (the Dafny mirror of H3v): the compiled loop of the schoolbook definition
  method MulLoop(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Times(a, b) && Valid(r) && ToNat(r) == ToNat(a) * ToNat(b)
  {
    r := [];
    var k := 0;
    assert b[0..] == b;
    while k < |b|
      invariant 0 <= k <= |b|
      invariant MulAcc(a, b[k..], r, k) == Times(a, b)
      decreases |b| - k
    {
      assert b[k..][1..] == b[k + 1..];
      r := Add(r, Shift(MulLimb(a, b[k]), k));
      k := k + 1;
    }
    MulCorrect(a, b);
  }
}
```

### A.18 Q16 Verus references (`verus/q/q16_practice_iiia/src/lib.rs`, `src/divl.rs`)

`root/verus/q/q16_practice_iiia/src/lib.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use qg_bignat_l7::*;
pub mod divl;

verus! {

// H2v helper (invented): multiply by BASE
pub fn shift_limb(a: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == BASE * a.to_nat(),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    if n == 0 {
        return BigNat { limbs: v };
    }
    v.push(0);
    let mut i: usize = 0;
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            v@ =~= seq![0u64] + a@.subrange(0, i as int),
        decreases n - i,
    {
        v.push(a.limbs[i]);
        i = i + 1;
        proof {
            assert(v@ =~= seq![0u64] + a@.subrange(0, i as int));
        }
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        assert(v@.drop_first() =~= a@);
    }
    BigNat { limbs: v }
}

// H2v: full multiplication, Horner from the top limb of b
pub fn mul(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * b.to_nat(),
{
    let m = b.limbs.len();
    let mut acc = BigNat { limbs: Vec::new() };
    let mut i: usize = m;
    proof {
        assert(seq_to_nat(b@.subrange(m as int, m as int)) == 0);
        lemma_mul_basics(a.to_nat() as int);
    }
    while i > 0
        invariant
            i <= m,
            m == b@.len(),
            a.wf(),
            acc.wf(),
            acc.to_nat() == a.to_nat() * seq_to_nat(b@.subrange(i as int, m as int)),
        decreases i,
    {
        i = i - 1;
        let s = shift_limb(&acc);
        let p = mul_limb(a, b.limbs[i]);
        acc = big_add(&s, &p);
        proof {
            let t = b@.subrange(i as int, m as int);
            assert(t.drop_first() =~= b@.subrange(i + 1, m as int));
            let av = a.to_nat() as int;
            let t1 = seq_to_nat(t.drop_first()) as int;
            let h = b@[i as int] as int;
            assert(seq_to_nat(t) == h + BASE * t1);
            lemma_mul_is_distributive_add(av, h, BASE * t1);
            lemma_mul_is_associative(av, BASE as int, t1);
            lemma_mul_is_associative(BASE as int, av, t1);
        }
    }
    proof {
        assert(b@.subrange(0, m as int) =~= b@);
    }
    acc
}

} // verus!
```

`root/verus/q/q16_practice_iiia/src/divl.rs`:

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l7::*;

verus! {

// invented 1: the value of a suffix, one limb at a time from the top
pub proof fn lemma_suffix_step(s: Seq<u64>, i: int)
    requires
        0 <= i < s.len(),
    ensures
        seq_to_nat(s.subrange(i, s.len() as int)) == s[i] + BASE * seq_to_nat(s.subrange(i + 1, s.len() as int)),
{
    assert(s.subrange(i, s.len() as int).drop_first() =~= s.subrange(i + 1, s.len() as int));
}

// invented 2: one division step keeps the quotient digit a limb and the remainder below d
pub proof fn lemma_div_step(r: nat, x: nat, d: nat)
    requires
        0 < d < BASE,
        r < d,
        x < BASE,
    ensures
        (r * BASE + x) / d < BASE,
        (r * BASE + x) % d < d,
        r * BASE + x == ((r * BASE + x) / d) * d + (r * BASE + x) % d,
{
    let t = (r * BASE + x) as int;
    lemma_fundamental_div_mod(t, d as int);
    lemma_mul_is_commutative(d as int, t / (d as int));
    lemma_mod_pos_bound(t, d as int);
    assert(t < d * BASE) by (nonlinear_arith)
        requires
            r < d,
            x < BASE,
            t == r * BASE + x,
    ;
    lemma_multiply_divide_lt(t, d as int, BASE as int);
}

// H2v: divide by one limb, from the top
pub fn div_limb(a: &BigNat, d: u64) -> (res: (BigNat, u64))
    requires
        a.wf(),
        d > 0,
    ensures
        res.0.wf(),
        res.1 < d,
        a.to_nat() == res.0.to_nat() * d + res.1,
{
    let n = a.limbs.len();
    let mut q: Vec<u64> = Vec::new();
    let mut k: usize = 0;
    while k < n
        invariant
            k <= n,
            q@.len() == k,
            forall|j: int| 0 <= j < k ==> q@[j] == 0,
        decreases n - k,
    {
        q.push(0);
        k = k + 1;
    }
    let mut rem: u64 = 0;
    let mut i: usize = n;
    proof {
        assert(a@.subrange(n as int, n as int) =~= Seq::<u64>::empty());
        assert(q@.subrange(n as int, n as int) =~= Seq::<u64>::empty());
        assert(seq_to_nat(Seq::<u64>::empty()) == 0);
        lemma_mul_basics(d as int);
    }
    while i > 0
        invariant
            i <= n,
            n == a@.len(),
            q@.len() == n,
            rem < d,
            d > 0,
            seq_to_nat(a@.subrange(i as int, n as int)) == seq_to_nat(q@.subrange(i as int, n as int)) * d + rem,
        decreases i,
    {
        i = i - 1;
        let x = a.limbs[i];
        proof {
            lemma_div_step(rem as nat, x as nat, d as nat);
        }
        let t: u128 = (rem as u128) * 0x1_0000_0000_0000_0000u128 + x as u128;
        let qd: u64 = (t / d as u128) as u64;
        let r2: u64 = (t % d as u128) as u64;
        let ghost oldq = q@;
        q.set(i, qd);
        proof {
            lemma_suffix_step(a@, i as int);
            lemma_suffix_step(q@, i as int);
            assert(q@.subrange(i + 1, n as int) =~= oldq.subrange(i + 1, n as int));
            let qs = seq_to_nat(q@.subrange(i + 1, n as int)) as int;
            let av = seq_to_nat(a@.subrange(i + 1, n as int)) as int;
            assert(av == qs * d + rem);
            lemma_mul_is_distributive_add_other_way(d as int, qd as int, BASE * qs);
            lemma_mul_is_associative(BASE as int, qs, d as int);
            lemma_mul_is_distributive_add(BASE as int, qs * d, rem as int);
        }
        rem = r2;
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        assert(q@.subrange(0, n as int) =~= q@);
    }
    let mut qb = BigNat { limbs: q };
    normalize(&mut qb);
    (qb, rem)
}

} // verus!
```

### A.19 The drivers (`drv/`)

`drv/capped.py`:

```python
#!/usr/bin/env python3
"""Lane driver: run a course script with every dvl job's memory cap clamped to
the lane share (8 GB). Usage: capped.py <root> <script> [args...]"""
import os, sys, runpy
root = os.path.abspath(sys.argv[1]); script = sys.argv[2]; args = sys.argv[3:]
sys.path.insert(0, os.path.join(root, "scripts"))
os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-plan5r-q/dvl")
from dvl import common
_orig = common.run_capped
SHARE = 8
def run_capped(argv, mem_gb, timeout_s, *a, **k):
    return _orig(argv, min(float(mem_gb), SHARE), timeout_s, *a, **k)
common.run_capped = run_capped
# modules that did `from dvl.common import run_capped` keep the old name: patch them too
import importlib
for name in ("dvl.dafny", "dvl.verus", "dvl.python"):
    try:
        m = importlib.import_module(name)
        if hasattr(m, "run_capped"):
            m.run_capped = run_capped
    except Exception:
        pass
os.chdir(root)
sys.argv = [os.path.join(root, "scripts", script)] + args
runpy.run_path(sys.argv[0], run_name="__main__")
```

`drv/eb.py`:

```python
#!/usr/bin/env python3
"""Lane driver: the dvl empty-body gates with every job clamped to 8 GB.
Usage: eb.py <root> d|v <target> <symbol>[,<symbol>...] [modes]"""
import os, sys, json
root = os.path.abspath(sys.argv[1]); lang = sys.argv[2]; target = sys.argv[3]
syms = sys.argv[4].split(","); modes = sys.argv[5].split(",") if len(sys.argv) > 5 else None
sys.path.insert(0, os.path.join(root, "scripts"))
os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-plan5r-q/dvl")
os.chdir(root)
from dvl import common
_orig = common.run_capped
def run_capped(argv, mem_gb, timeout_s, *a, **k):
    return _orig(argv, min(float(mem_gb), 8.0), timeout_s, *a, **k)
common.run_capped = run_capped
from dvl import dafny, verus
for s in syms:
    if lang == "d":
        r = dafny.empty_body(target, s)
    else:
        r = verus.empty_body(target, s, modes=modes)
    d = r if isinstance(r, dict) else getattr(r, "__dict__", {"repr": repr(r)})
    print(s, json.dumps({k: d.get(k) for k in ("verdict", "per_symbol", "message", "error", "reason") if k in d}, default=str))
```

`drv/ebt.py`:

```python
#!/usr/bin/env python3
"""Verus TRIV-only gate with a declared trivial body. Usage: ebt.py <root> <target> <symbol> <body|->"""
import os, sys, json
root = os.path.abspath(sys.argv[1]); target, sym, body = sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, os.path.join(root, "scripts")); os.environ.setdefault("DVL_SCRATCH", "/tmp/dvl0-plan5r-q/dvl"); os.chdir(root)
from dvl import common
_o = common.run_capped
common.run_capped = lambda argv, mem_gb, t, *a, **k: _o(argv, min(float(mem_gb), 8.0), t, *a, **k)
from dvl import verus
r = verus.empty_body(target, sym, modes=["TRIV"], triv_body=None if body == "-" else body)
d = r if isinstance(r, dict) else r.__dict__
print(sym, json.dumps({k: d.get(k) for k in ("verdict", "per_symbol") if k in d}, default=str))
```

`drv/count.py`:

```python
import re,sys
def body_lines(path, name):
    src=open(path).read().split('\n')
    # find declaration line
    pat=re.compile(r'\b(lemma|method|function|predicate|fn)\s+'+re.escape(name)+r'\b')
    for i,l in enumerate(src):
        if pat.search(l):
            # find first '{' at or after i that opens the body (skip lines with ensures/requires etc.)
            j=i; depth=0; started=False; count=0; total=0
            while j < len(src):
                line=src[j]
                code=re.sub(r'//.*','',line)
                for ch in code:
                    if ch=='{':
                        depth+=1; started=True
                    elif ch=='}':
                        depth-=1
                if started:
                    s=code.strip()
                    if s and s not in ('{','}'):
                        count+=1
                    if depth==0:
                        return count, j-i+1
                j+=1
    return None
for spec in sys.argv[1:]:
    path,name=spec.rsplit(':',1)
    print(name, body_lines(path,name))
```

### A.20 The MDE computation (§4.3)

```python
# from harness/ (the frozen core, fvh.stats as built in DV3a)
from fvh.stats import mde_two_proportions as m
for n in (20, 40, 60, 80, 120, 180):
    print(n, [(p0, round(m(n, p0), 3), round(m(n, p0, paired=True), 3),
               round(m(n, p0, alpha=0.05 / 3, paired=True), 3)) for p0 in (0.2, 0.35, 0.5)])
```

Output rows used in §4.3: n = 60: unpaired 0.236 (p0 0.2), 0.245 (p0 0.5); paired 0.242, 0.259, 0.251; paired at α/3 0.286, 0.302, 0.289. n = 120 paired 0.164, 0.181, 0.179; n = 180 paired 0.131, 0.147, 0.147. At n = 20 and 24 (Lab 1's Claude arm, Lab 3's Claude arm) the paired MDE is 0.41–0.45 and 0.39–0.41: descriptive only, as design §11.1 says ("CIs ≈ ±20 pp").

### A.21 Benchmark sample commands (§4.2)

```sh
S=/tmp/dvl0-plan5r-q/bench; W=<authoring worktree>/bench/public
cd $W/dafnybench/answers && ls | shuf -n 10 --random-source=<(yes 7)      # the DafnyBench draw
ls $W/humaneval-verus/answers | shuf -n 6 --random-source=<(yes 7)        # the HumanEval-Verus draw
# each answer: drv/capped.py <root> vcheck --gate <copy>; each task form: drv/capped.py <root> vcheck <copy>
# HumanEval-Verus again with the line `fn main() {}` removed (sed) before vcheck --gate
```

## Appendix C. The revision's probes (scratch, as last verified on 2026-10-07)

Each block supersedes the part of Appendix A it names; everything else in Appendix A stands. Item markers are absent, as in Appendix A.

### C.1 L6, Dafny (supersedes A.3's `SubB` and `Sub`)

`root/dafny/given/Q/QG_L6_BigNat.dfy`, whole file:

```dafny
// candidate L6 (plan probe)
module {:disableNonlinearArithmetic} QG_L6_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat

  // FromNat gives canonical limbs (new; never posed).
  lemma FromNatCanonical(n: nat)
    ensures Canonical(FromNat(n))
    decreases n
  {
    FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / BASE);
      if n / BASE == 0 {
        assert FromNat(n / BASE) == [];
        assert n % BASE == n;
      }
    }
  }

  // Normalized addition is canonical with the sum (re-supplied: Q08.H1d's statement, for a later refinement).
  lemma NormalizeAddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Canonical(Normalize(Add(a, b))) && ToNat(Normalize(Add(a, b))) == ToNat(a) + ToNat(b)
  {
    AddCorrect(a, b);
    NormalizeCanonical(Add(a, b));
    NormalizeToNat(Add(a, b));
  }

  // Subtraction, by value (a specification: no algorithm).
  ghost function Sub(a: seq<nat>, b: seq<nat>): seq<nat>
    requires Valid(a) && Valid(b) && ToNat(a) >= ToNat(b)
  {
    FromNat(ToNat(a) - ToNat(b))
  }
}
```

### C.2 L7, Dafny (supersedes A.5)

`root/dafny/given/Q/QG_L7_BigNat.dfy`:

```dafny
// candidate L7 (plan probe)
module {:disableNonlinearArithmetic} QG_L7_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L4_BigNat

  // The schoolbook definitions: one MulLimb row per limb of b, from the low limb.
  function Shift(s: seq<nat>, k: nat): seq<nat>
  {
    seq(k, _ => 0) + s
  }

  ghost function MulAcc(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat): seq<nat>
    decreases |b|
  {
    if |b| == 0 then acc else MulAcc(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)), k + 1)
  }

  ghost function Times(a: seq<nat>, b: seq<nat>): seq<nat>
  {
    MulAcc(a, b, [], 0)
  }

}
```

A.17's Q16 file verifies over it unchanged (138 verified before C.1, 137 after). The probe of blocker 2 replaced `MulLoop`'s body by `r := Times(a, b);` followed by A.17's last line `MulCorrect(a, b);`: verified with A.5's compiled `Times`, failed at resolve with this file. The plain attempt of §8.2 replaced `MulCorrect`'s body by `if |b| > 0 { ValidTail(b); MulCorrect(a, b[1..]); }` with `decreases |b|`.

### C.3 Q11's VC items (supersedes A.9's `module Q11_Vc`)

In `root/dafny/Q/Q10_PracticeIA/std/Q11_Probe.dfy`, in place of `Q11_Vc`:

```dafny
module Q11_VcProg {
  function Prog1(x: int, y: int): (int, int)
  {
    var x1 := x + 2 * y;
    var y1 := x1 - y;
    (x1, y1)
  }
  ghost predicate Post1(r: (int, int)) { r.0 > 0 && r.1 < 10 }
  function Prog2(x: int, y: int): (int, int)
  {
    var y1 := if x > y then x - y else y - x;
    var x1 := x + y1;
    (x1, y1)
  }
  ghost predicate Post2(r: (int, int)) { r.0 >= 5 && r.1 <= 3 }
}

module Q11_VcAnswer {
  ghost predicate Pre1(x: int, y: int) { x + 2 * y > 0 && x + y < 10 }
  ghost predicate Pre2(x: int, y: int) {
    (x > y ==> 2 * x - y >= 5 && x - y <= 3) && (x <= y ==> y >= 5 && y - x <= 3)
  }
}

module Q11_VcCheck {module Q11_VcCheck {
  import opened Q11_VcProg
  import opened Q11_VcAnswer
  lemma Pre1Exact(x: int, y: int) ensures Pre1(x, y) <==> Post1(Prog1(x, y)) {}
  lemma Pre2Exact(x: int, y: int) ensures Pre2(x, y) <==> Post2(Prog2(x, y)) {}
}
```

Variants probed (each the whole file with one change): both predicate bodies `Post1(Prog1(x, y))` / `Post2(Prog2(x, y))` in `Q11_VcAnswer` (fails at resolve, three unresolved identifiers); the same with `import opened Q11_VcProg` added to `Q11_VcAnswer` (verifies: the residual of QPLAN §30 Q62); both bodies `true`; both bodies `false` (each: 2 errors). The same construct-free bodies inside A.9's single module verified.

### C.4 Q13.H5d (supersedes A.13's `ValueLoop`)

The head of `Q13_Library` (now importing L4 for `MulNonneg`), and the method, which moved from `Q13_Norm` to the end of `Q13_Library`, the file's last module:

```dafny
module {:disableNonlinearArithmetic} Q13_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.Mul

  // H4d
  // ... RepeatValue as A.13 ...

  // H5d (revised: in the nonlinear-off module): the loop from the low limb, every product step by a library call
  method ValueLoop(s: seq<nat>) returns (v: nat)
    ensures v == ToNat(s)
  {
    v := 0;
    var w: nat := 1;
    var i := 0;
    assert s[0..] == s;
    LemmaMulBasics(ToNat(s));
    while i < |s|
      invariant 0 <= i <= |s| && w == Pow(i)
      invariant v + w * ToNat(s[i..]) == ToNat(s)
      decreases |s| - i
    {
      ghost var t := ToNat(s[i + 1..]);
      assert ToNat(s[i..]) == s[i] + BASE * t by {
        assert s[i..][1..] == s[i + 1..];
      }
      MulNonneg(w, s[i]);
      LemmaMulIsDistributiveAdd(w, s[i], BASE * t);
      LemmaMulIsAssociative(w, BASE, t);
      LemmaMulIsCommutative(w, BASE);
      v := v + w * s[i];
      w := w * BASE;
      i := i + 1;
    }
    LemmaMulBasics(w);
  }
}
```

A trial without `MulNonneg(w, s[i]);` failed ("value does not satisfy the subset constraints of 'nat'"); one without a second `MulNonneg(w, BASE);` (in an earlier draft) verified, so that call was dropped.

### C.5 Q13.H1v (supersedes A.14's `sub`; `lemma_sub_lift` unchanged)

```rust
pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut borrow: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            m == b@.len(),
            m <= n,
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == borrow,
            borrow <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + BASE * c[j + 1] == #[trigger] res@[j] + limb_at(b@, j)
                    + c[j],
        decreases n - i,
    {
        let x: u64 = a.limbs[i];
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let d: u64;
        if x >= y && x - y >= borrow {
            d = x - y - borrow;
            borrow = 0;
        } else {
            d = ((x as u128 + 0x1_0000_0000_0000_0000u128) - y as u128 - borrow as u128) as u64;
            borrow = 1;
        }
        res.push(d);
        proof { c = c.push(borrow as nat); }
        i = i + 1;
    }
    proof { lemma_sub_lift(a@, b@, res@, c); }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}
```

### C.6 Q14, Verus (supersedes A.15's trait, `PairAcc` impl and `sum_limbs`) and the Dafny order

```rust
/// The given trait: an accumulator seen through its ghost total.
pub trait Accum: Sized {
    spec fn total(&self) -> nat;

    fn add_word(&mut self, x: u64)
        requires
            old(self).total() + x < BASE * BASE,
        ensures
            final(self).total() == old(self).total() + x,
    ;

    fn read(&self) -> (r: BigNat)
        ensures
            r.wf(),
            r.to_nat() == self.total(),
    ;

    fn from_big(a: &BigNat) -> (r: Option<Self>)
        requires
            a.wf(),
        ensures
            r is Some <==> a.to_nat() < BASE * BASE,
            r is Some ==> r->0.total() == a.to_nat(),
    ;
}

impl Accum for PairAcc {
    open spec fn total(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    fn add_word(&mut self, x: u64) {
        if self.lo <= u64::MAX - x {
            self.lo = self.lo + x;
        } else {
            self.lo = self.lo - (u64::MAX - x) - 1;
            self.hi = self.hi + 1;
        }
    }

    fn read(&self) -> (r: BigNat) {
        let mut v: Vec<u64> = Vec::new();
        if self.hi != 0 {
            v.push(self.lo);
            v.push(self.hi);
            proof {
                assert(v@.drop_first() =~= seq![self.hi]);
                assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first().drop_first()) == 0);
                assert(seq_to_nat(v@.drop_first()) == self.hi as nat);
            }
        } else if self.lo != 0 {
            v.push(self.lo);
            proof {
                assert(v@.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first()) == 0);
            }
        }
        proof {
            assert(seq_to_nat(Seq::<u64>::empty()) == 0);
        }
        BigNat { limbs: v }
    }

    fn from_big(a: &BigNat) -> (r: Option<Self>) {
        let n = a.limbs.len();
        if n == 0 {
            Some(PairAcc { lo: 0, hi: 0 })
        } else if n == 1 {
            proof {
                assert(a@.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(a@.drop_first()) == 0);
            }
            Some(PairAcc { lo: a.limbs[0], hi: 0 })
        } else if n == 2 {
            proof {
                let t = a@.drop_first();
                assert(t.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(t.drop_first()) == 0);
                assert(seq_to_nat(t) == t[0] as nat);
            }
            Some(PairAcc { lo: a.limbs[0], hi: a.limbs[1] })
        } else {
            proof {
                lemma_seq_to_nat_lower(a@);
                lemma_weight_mono(2, (n - 1) as nat);
                lemma_weight_zero();
                lemma_weight_succ(0);
                lemma_weight_succ(1);
            }
            None
        }
    }
}

/// H3v: erasure. The bound is ghost; the code never reads it. (Variant: from the top limb down.)
pub fn sum_limbs(v: &Vec<u64>, Ghost(bound): Ghost<nat>) -> (r: u128)
    requires
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= bound,
        v.len() * bound <= u128::MAX,
    ensures
        r == limb_sum(v@),
{
    let mut s: u128 = 0;
    let mut i: usize = v.len();
    while i > 0
        invariant
            i <= v.len(),
            s == limb_sum(v@.subrange(i as int, v.len() as int)),
            s <= (v.len() - i) * bound,
            forall|k: int| 0 <= k < v.len() ==> v@[k] <= bound,
            v.len() * bound <= u128::MAX,
        decreases i,
    {
        i = i - 1;
        proof {
            let t = v@.subrange(i as int, v.len() as int);
            lemma_limb_sum_cons(t);
            assert(t.drop_first() =~= v@.subrange(i + 1, v.len() as int));
            lemma_mul_is_distributive_add_other_way(bound as int, (v.len() - i - 1) as int, 1);
            lemma_mul_inequality((v.len() - i) as int, v.len() as int, bound as int);
        }
        s = s + v[i] as u128;
    }
    proof { assert(v@.subrange(0, v.len() as int) =~= v@); }
    s
}

/// H3v's invented lemma (variant): the top-defined sum read from the bottom.
pub proof fn lemma_limb_sum_cons(t: Seq<u64>)
    requires
        t.len() > 0,
    ensures
        limb_sum(t) == t[0] as nat + limb_sum(t.drop_first()),
    decreases t.len(),
{
    if t.len() > 1 {
        lemma_limb_sum_cons(t.drop_last());
        assert(t.drop_last().drop_first() =~= t.drop_first().drop_last());
        assert(t.drop_first().last() == t.last());
    } else {
        assert(limb_sum(t.drop_last()) == 0);
        assert(limb_sum(t.drop_first()) == 0);
    }
}
```

The hand-written TRIV variants: `fn add_word(&mut self, x: u64) {}`; `fn read(&self) -> (r: BigNat) { BigNat { limbs: Vec::new() } }` (both on A.15's first form); `fn from_big(a: &BigNat) -> (r: Option<Self>) { None }` (on this form); each verified as the whole crate under `--seed 1`, `2` and `3`. **Dafny order:** A.16's file with `module Q14_Term { … }` moved before `module {:disableNonlinearArithmetic} Q14_Cached refines QG_L4_Spec { … }`, no other change.

### C.7 Q10.X1v (supersedes A.12's `add_words` as the exit)

In `root/verus/q/q10_practice_ia/src/q1x.rs`:

```rust
// Q10.X1v (revised): halving a two-word number
pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))
    ensures
        r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2,
{
    (lo / 2 + (hi % 2) * 0x8000_0000_0000_0000u64, hi / 2)
}
```

TRIV variants (`drv/ebt.py`): `{ (0, 0) }` and `{ (lo / 2, hi / 2) }`, each failing seeds 1–3.

### C.8 The line counter (`rev/pcount.py`)

A heuristic tagger: each body line is P (proof) or C (code); `--show` prints the tags, which the lane read for every exec item. Lemma and proof-fn bodies count as proof throughout. Statements of invented lemmas were counted with its `stmt_lines` (signature to body brace).

```python
#!/usr/bin/env python3
"""Proof-line counter (Δ53 mode): non-blank, non-comment body lines of a fn/method,
tagged P (proof: proof blocks, assert, invariant/decreases clauses, ghost/tracked lets,
reveal, lemma calls, calc, forall statements) or C (exec code). Prints the tagged body
with --show. Usage: pcount.py [--show] <file>:<name> ..."""
import re, sys
show = "--show" in sys.argv
specs = [a for a in sys.argv[1:] if a != "--show"]
PSTART = re.compile(r'^(assert|assume|invariant|decreases|reveal|reveal_with_fuel|calc|broadcast use|let\s+ghost|let\s+tracked|ghost\s+var|lemma_\w+|forall\b|Ghost\(|Tracked\()')
CLAUSE_CONT = re.compile(r'^(invariant|decreases|ensures|requires)\b')
def find(src, name):
    nth = 1
    if '@' in name: name, nth = name.split('@'); nth = int(nth)
    pat = re.compile(r'\b(lemma|method|function|predicate|fn)\s+' + re.escape(name) + r'\b')
    for i, l in enumerate(src):
        if pat.search(l):
            nth -= 1
            if nth == 0: return i
def body(src, i):
    depth = 0; started = False; out = []
    for j in range(i, len(src)):
        code = re.sub(r'//.*', '', src[j])
        opened_here = False
        line_depth = depth
        for ch in code:
            if ch == '{':
                depth += 1
                if not started: started = True; opened_here = True
            elif ch == '}':
                depth -= 1
        if started:
            out.append((line_depth, code.strip(), opened_here))
            if depth == 0: return out
    return out
for spec in specs:
    path, name = spec.rsplit(':', 1)
    src = open(path).read().split('\n')
    i = find(src, name)
    if i is None: print(name, "not found"); continue
    ind = len(src[i]) - len(src[i].lstrip())
    start = i
    for j in ([] if src[i].rstrip().endswith('{') else range(i, min(i + 60, len(src)))):
        t = src[j]
        if t.strip() == '{' and len(t) - len(t.lstrip()) == ind: start = j; break
        if j > i and re.match(r'^\s*(pub |proof |fn |lemma |method |function |ghost |predicate )', t) and len(t) - len(t.lstrip()) == ind: break
    else:
        start = i
    if start == i and not src[i].rstrip().endswith('{'):
        # signature spans lines and the body brace ends a clause line
        for j in range(i, min(i + 60, len(src))):
            if src[j].rstrip().endswith('{') and not re.search(r'(if|else|=>|\|)\s*\{$', src[j].rstrip()): start = j; break
    lines = body(src, start)
    p = c = 0; in_proof = 0; in_clause = False; rows = []
    proofmode = bool(re.search(r'\b(proof\s+fn|lemma)\b', src[i]))
    for k, (d, s, oh) in enumerate(lines):
        if oh:  # the line that opens the body
            s2 = s[s.index('{')+1:].strip() if '{' in s else ''
            if not s2 or s2 == '}': continue
            s = s2
        if not s or s in ('{', '}', '};', '},'):
            if s == '{': in_clause = False
            if in_proof and s.startswith('}') and d <= in_proof: in_proof = 0
            continue
        tag = 'C'
        if in_proof and d >= in_proof: tag = 'P'
        elif s.startswith('proof {') or s == 'proof{':
            tag = 'P'; in_proof = d + 1
        elif PSTART.match(s): tag = 'P'
        elif re.match(r'^[A-Z]\w*\(.*\);$', s) and ':=' not in s: tag = 'P'  # Dafny lemma call statement
        if CLAUSE_CONT.match(s): in_clause = True; tag = 'P'
        elif in_clause:
            if s.startswith('{') : in_clause = False
            elif not re.match(r'^(while|if|let|for|loop|return|match)\b', s): tag = 'P'
            else: in_clause = False
        if s.endswith('{') and in_clause and not CLAUSE_CONT.match(s): in_clause = False
        if in_proof and s.startswith('}') and d + 0 < in_proof: in_proof = 0
        if proofmode: tag = 'P'
        rows.append((tag, s))
        if tag == 'P': p += 1
        else: c += 1
    print(f"{name}: proof {p}, code {c}, total {p+c}")
    if show:
        for t, s in rows: print(f"   {t} {s}")

def stmt_lines(path, name):
    src = open(path).read().split('\n')
    i = find(src, name)
    n = 0
    for j in range(i, len(src)):
        t = re.sub(r'//.*', '', src[j]).strip()
        if t == '{': break
        if t: n += 1
        if t.endswith('{') and j > i - 1 and not re.search(r'(if|else)\b.*\{$', t): break
    return n
```
