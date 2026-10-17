# Q16 code notes (DV5c Q16 lane, as built)

> **Author-only.** Gate results, the four admission results per item, the probes behind
> them, the plain attempt, the construct-free answers and their forms, and the deviations
> of Q16's code and kit from the plan. Never quote, paraphrase or link any of it from a
> learner-visible file. The plan is `QPLAN.md` §19 and §26 and
> `Solutions/plans/Q10-Q18-author-notes.md` §8.2, §13.2, Appendix A.17, A.18 and C.2;
> layer L7 as built is `Solutions/plans/L7-notes.md`. This file records what was built
> (authoring worktree at 5e5d3ee plus the round's uncommitted work, 2026-10-11) and where
> it differs.

Every result below was captured on the pins (Dafny 4.11.0, Verus 0.2026.09.27.3cf1832)
through the course wrappers (`scripts/vcheck`, `scripts/vaudit`, `scripts/specfreeze`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/pcount.py`), one solver job at a time,
under the wrappers' caps (Dafny 8 GB, Verus 16 GB) and inside `systemd-run --user --scope
-p MemoryMax=16G -p MemorySwapMax=0` (the lane's share). `free -g` showed 97–99 GB
available before every batch (31 GB needed); no job was killed.
`DVL_SCRATCH=/tmp/dvl0-dv5c-q16/scratch`. Logs and probes are archived under
`~/.cache/dafny-verus-learn-0/author-probes/dv5c/q16/` (`empty-body-1.txt`,
`final-1.txt`, `brit-d.txt`, `brit-v.txt`, `brit-v.json`, `brit-v2.json`, `probe/`,
`rubric/`, `bank/`, `fix/`, `twin-test.txt`).

## 1. Files

| file | shipped state | twin |
|---|---|---|
| `dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy` (one module, `module {:disableNonlinearArithmetic} Q16_PracticeIIIA`, L1–L7 and `Std.Arithmetic.Mul` opened; a file-wide `HELPERS` area; H1d, then H3d) | verified, 2 holes (H1d a bodyless lemma; H3d an exec `assume false;`), 134 verified | 141 verified (with two reference-only declarations that only support H3d's `cfree:` line, §4) |
| `verus/q/q16_practice_iiia/src/lib.rs` (L1–L7 through `use qg_bignat_l7::*;`, `vstd::arithmetic::{mul, div_mod}`; a file-wide `HELPERS` area; H2v, H3v; the speed test commented after `verus!`) | verified, 2 holes (H2v, H3v: `external_body` + `unimplemented!()`) | 15 verified; the speed test live: `vcheck --test` 2 passed |
| `dafny/Q/Q16_PracticeIIIA/std/dfyconfig.toml`, `verus/q/q16_practice_iiia/Cargo.toml`, `verus/Cargo.toml` | generated (`gen_units.py`: 35 units; the workspace gains `given/qg_bignat_l7` and the Q16 crate) | `Solutions/verus/q/q16_practice_iiia/Cargo.toml` (hand-written, as Q13's) and a member line in `Solutions/verus/Cargo.toml` |
| `expected/Q16.counts` (Dafny unit 141 / floor 2, crate 15 / floor 2; 2 files, 2 + 2 holes), `expected/Q16.freeze` (8 statements in 2 files; the module's nonlinear attribute as a frozen lever), `expected/Q16.chapter.toml` (3 pins) | author-written | — |

No exit file, no prediction, no slot file, no specimen, no agent file (QPLAN §19.0, §26).
`expected/Q16.pins` does not exist (no verdict slot); `pins.py --ref --module Q16` says
"nothing to check" and exits 1 for that module alone, as designed for an empty set; the CI
step runs `--ref` over every module and is not affected.

## 2. The plain attempt (H1d), captured on the built files

`MulCorrect` with `decreases |b|` and the body `if |b| > 0 { ValidTail(b); MulCorrect(a,
b[1..]); }` in a probe module of Q16's context (`probe/plain_h1d.dfy`): **failed — 140
verified, 0 holes, 2 errors**, "a postcondition could not be proved on this return path",
one per conjunct of the `ensures`. The chapter's pinned fence `plain-h1d` is the same
attempt in a smaller module (`Plain`, L1, L2, L4, L7 opened): failed, 133 verified, 2
errors. The hard tier's "plain statement ships and is known to fail" holds.

Other H3d probes (`probe/`): `r := Times(a, b); MulCorrect(a, b);` fails at resolve ("a call
to a ghost function is allowed only in specification contexts"); the by-value body
`r := FromNat(ToNat(a) * ToNat(b)); MulCorrect(a, b);` fails (the postcondition `r ==
Times(a, b)`, and a `nat` subset constraint); a compiled recursion copying `MulAcc`'s body
plus a one-call induction lemma (`probe/h3d_rec.dfy`) **verifies** (141): it is the twin's
`cfree:` line, killed by `form: loop-dir:up` (§4).

## 3. References, counts and stability

Counts are QPLAN §19.0's rule with the user's layout rule D1 (`scripts/pcount.py`); the
hard band is D 30–80 / V 45–120, H3 banded as one problem against the Verus band (Δ178);
2–4 invented lemmas or one invariant per problem.

| item | reference | proof lines (D1) | without D1 | band | invented |
|---|---|---|---|---|---|
| H1d `MulCorrect` | A.17 (C.2's ghost `Times`) | 3 + `MulAccCorrect` 26 + `ShiftCorrect` 9 + statements 5 + 4 = **47** | 47 | 30–80 | `MulAccCorrect`, `ShiftCorrect` |
| H2v `div_limb` | A.18's `divl.rs`, moved into `lib.rs` (the first loop's unused `forall` invariant dropped) | 32 + `lemma_suffix_step` 1 + statement 7 + `lemma_div_step` 11 + statement 9 = **60** | 61 | 45–120 | `lemma_suffix_step`, `lemma_div_step` |
| H3v `mul` | **new** (the in-place schoolbook; no plan reference existed) | 66 + `lemma_push_value` 4 + statement 3 + `lemma_set_limb` 16 + statement 7 = **96** | 99 | (with H3d) | `lemma_push_value`, `lemma_set_limb` |
| H3d `MulLoop` | A.17 | **6** | 6 | — | none |
| H3 (one problem) | — | 96 + 6 = **102** | 105 | 45–120 | — |

`pcount` gives `mul` 66 directly since the DV5c fix round (its clause state now ends with
the `assert(…) by (nonlinear_arith) requires …;` statement and with the proof block, so
`res.push(carry);` and `j = j + 1;` are code; before the fix it said 68 and this note
subtracted 2 by hand).
Statement lines are `pcount --stmt`'s (formatted Verus clauses run over several lines,
so `lemma_suffix_step`'s statement is 7 here where §13.2 of the author notes counted 5).

**H3v's reference (new).** `mul` fills a vector with `|a|` zeros (value 0 by L1's
`lemma_seq_to_nat_push_zero`), then for each limb `b_j` runs one inner pass over `a`:
the 128-bit sum `a_i * b_j + res[j + i] + carry` (bounded by `lemma_mul_upper_bound`)
gives the limb written at `j + i` and the next carry; after the pass the carry is pushed
on top. Invariants: outer `res@.len() == n + j`, `seq_to_nat(res@) == a.to_nat() *
seq_to_nat(b@.subrange(0, j))`; inner (with `v0` the value at the row's start)
`seq_to_nat(res@) + weight(j + i) * carry == v0 + weight(j) * (seq_to_nat(a@.subrange(0,
i)) * b_j)`, plus the outer facts restated (Verus loop isolation). Helpers: the value of
a push (`lemma_push_value`, from L4's `lemma_seq_to_nat_append`) and the value of a write
at a position (`lemma_set_limb`, induction on the position). The inner step's identity
is ten named `vstd::arithmetic::mul` calls (a first version used one scoped
`nonlinear_arith` step: verified, but flagged at CV 31.2% with up to 1,546,097 resource
units on seed variation, `brit-v.json`; the named calls bring `mul` to CV 5.8%,
`brit-v2.json`); the row end keeps one scoped `nonlinear_arith` step with its `// did:`
receipt. L6's `normalize` makes the result canonical. The twin's speed test (two
four-limb factors against precomputed constants: all limbs `u64::MAX` squared, and a
mixed pair; the constants computed with Python's integers) passes: `vcheck --test` on the
crate with the twin laid over the learner file in place (restored byte-identical after,
`cmp`): `2 passed, 0 failed` (`twin-test.txt`).

**Stability** (`vcheck --ref --brittleness`, Dafny with `--solvers`), final files
(`final-1.txt`):
- Dafny twin: 4.12.1 and 4.14.1 × seeds 1–3 all verified, `stable`; 130 symbols, widest spread 28,782–39,413 (CV 13.9%, solver 4.14.1; the tool names it only as a declaration outside the target's files, the same L1 figure the L7 lane recorded); nothing flagged.
- Verus twin: seeds 1–3 verified, `stable`; 8 symbols, widest spread 89,803–124,519 (CV 16.0%, `lemma_set_limb`: by its counts then; since DV5d the sweep names its location, `src/lib.rs:69`); nothing flagged. `mul` 558,892–641,698 (CV 5.8%), `div_limb` 414,839–452,552 (CV 3.8%), every count at most 11% of the limit.

**APIs** (all at the pins; the twins verify): L1–L7 (L1's `lemma_seq_to_nat_push_zero`,
`ToNat`, `Valid`, `Pow`; L2's `ValidTail`, `ValidCons`, `ToNatCons`, `ToNatHeadTail`; L3's
`weight`, `lemma_weight_succ`, `lemma_weight_zero`; L4's `Add`, `AddCorrect`, `MulLimb`,
`MulLimbCorrect`, `MulNonneg`, `MulZero`, `lemma_weight_add`, `lemma_seq_to_nat_append`;
L6's `normalize`; L7's `Shift`, `MulAcc`, `Times`); `Std.Arithmetic.Mul`'s
`LemmaMulBasics`, `LemmaMulIsAssociative`, `LemmaMulIsCommutative`,
`LemmaMulIsDistributive`; `vstd::arithmetic::mul`'s `lemma_mul_basics`,
`lemma_mul_is_associative`, `lemma_mul_is_commutative`, `lemma_mul_is_distributive_add`,
`lemma_mul_is_distributive_add_other_way`, `lemma_mul_upper_bound`;
`vstd::arithmetic::div_mod`'s `lemma_fundamental_div_mod`, `lemma_mod_pos_bound`,
`lemma_multiply_divide_lt`; `Vec::new`, `push`, `set`, `len`, indexing; `Seq::subrange`,
`push`, `update`, `drop_first`.

## 4. The empty-body gate, the forms and the construct-free answers

`scripts/firsttry.sh Q16 --empty-body` (16 GB scope): run 1 (`empty-body-1.txt`) **4/4**,
68 s; the final run on the final files (`final-1.txt`): **4/4**, exit 0. Per item:

| item | result |
|---|---|
| H1d | ✓ maxauto and seeds 1–3 fail |
| H3d | ✓ maxauto and seeds 1–3 fail; ✓ the twin meets `loop-dir:up`; ✓ its `cfree:` answer fails its forms ("no loop in the block's answer region") |
| H2v | ✓ every light mode fails, TRIV (`{ (BigNat { limbs: Vec::new() }, 0) }`) included; ✓ the twin meets `loop-dir:i:down`; ✓ its `cfree:` answer fails its forms ("no loop on `i`") |
| H3v | ✓ every light mode fails, TRIV (`{ BigNat { limbs: Vec::new() } }`) included; ✓ the twin meets `no-call:big_add, no-call:plus`; ✓ its `cfree:` answer fails its forms ("a call of `big_add`") |

**Construct-free answers** (`// cfree:` in the twins; each verifies as a probe, so each
is a real shortcut, and each fails a form, Δ173):
- **H2v: division by repeated subtraction.** `r` starts as `a` (through `big_add(a,
  zero)`), `q` at zero; while `cmp(r, d) != Less`: `r = big_sub(r, d)`, `q = add_limb(q,
  1)`, one distributivity call; then `to_u64(r)`. About 10 lines, below the band, and
  it never reads a limb. Probe `probe/h2v_cfree.rs`: **verified** (15). Its loop's guard
  has no counter (`ge` is assigned by a comparison), so `form: loop-dir:i:down` refuses
  it. The prompt names the counter `i` and the direction.
- **H3v: rows by whole-number addition (Horner from the top limb, the plan's first
  draft, A.18's `mul`).** Shift by multiplying by `2^32` twice through `mul_limb`, the
  row by `mul_limb`, then `big_add`. Probe `probe/h3v_cfree.rs`: **verified**. It is
  fast (the speed test cannot see it), so `form: no-call:big_add, no-call:plus` (built
  this round, §6) refuses it; the prompt says the rule. Repeated addition (`a` added `b`
  times) also calls `big_add`, and the speed test would not finish on it.
- **H3d: a compiled recursion copying `MulAcc`'s body**, with a one-call induction lemma
  equating it to `MulAcc`. Probe `probe/h3d_rec.dfy`: **verified** (141). It avoids the
  invariant the item exercises, so `form: loop-dir:up` refuses it (the region holds no
  loop). The twin carries the two supporting declarations (`MulRec`, `MulRecIsMulAcc`),
  marked `reference-only`, so the gate can run the `cfree:` body in place.
- **H1d:** no shortcut known. Deleting the module's nonlinear attribute is refused by the
  lever freeze (`specfreeze --check` and `firsttry --report --strict` report
  `freeze-lever-removed` / `lever:`; `expected/Q16.freeze` records the lever).

**Residual, for a reader (rubric C4, C5; narrowed by the DV5c fix round):** a helper copied
from L4's `big_add` under another name is refused by `no-adder` (its `ensures` states a
whole-number sum) and is the twin's `cfree-decl:` answer; a reversed index or a loop that
only counts is refused by the extended `loop-dir` and is a twin `cfree:` answer (H2v's padded
answer, H3d's two). What still passes a form: a whole-number addition inlined in `mul` or a
helper whose sum is stated another way, and an index computed through a helper or read from
another sequence. Both are rubric findings at grade 1; the forms are tripwires for these,
never proofs that the construct is used.

## 5. Admission: the four results, item by item (QPLAN §19.0, Δ173, Δ178)

(1) reference complete and in band (§3); (2) empty-body gate fails, every known shortcut
fails (§4); (3) twin stable, seeds 1–3, Dafny both bundled solvers (§3); (4) only pinned
APIs (§3).

| item | (1) | (2) | (3) | (4) | registry |
|---|---|---|---|---|---|
| H1d | ✓ 47 (30–80), two invented lemmas | ✓ | ✓ | ✓ | **true, 45** |
| H2v | ✓ 60 (45–120), two invented lemmas | ✓ (TRIV; `cfree:` killed by `loop-dir:i:down`) | ✓ | ✓ | **true, 50** |
| H3v (gated, with H3d) | ✓ the pair 102 (45–120), two invented lemmas | ✓ (TRIV; `cfree:` killed by `no-call:`); the speed test passes on the twin | ✓ | ✓ | **true, 35** |
| H3d (gated, with H3v) | ✓ (in the pair) | ✓ (`cfree:` killed by `loop-dir:up`) | ✓ | ✓ | **true, 20** |

Hole minutes admitted: 150 of the module's 225 (H1 45, H2 50, H3 55), every H line whole;
the rest is brief 10, blueprint 30, `/review-code` 15, paper 15, ledger 5. No shortfall
note is needed. The fallbacks F-H1d and F-H2v keep their four results from author notes
§8.2 (not re-run on the built files: no item falls back to them); F-H3 has none and
carries 0 (it is not needed: H3 is admitted).

## 6. The tool change: `no-call:` for Verus

`scripts/dvl/forms.py`: `FORMS["no-call"]` is now `"dv"`; new `v_no_call(src, block,
blocks, name)` fails when a fn of the block, or a helper of the same file outside every
H, X and T block that they call (transitively, by name: `_v_reach`, the scope of
`no-nl` and `bv-exec`), calls `name` (an identifier before `(`, a method call
included); `check_static` dispatches by language; the vocabulary docstring describes the
Verus reading. Tests (`tests/wrappers/test_forms_static.py`): `test_vocabulary` now
expects no language problem for a Verus `no-call:` (and still one for `formula:`); new
`test_no_call_verus` (a call through a helper, a direct call, a method call, and a clean
block). `python3 -B -m unittest discover -s tests/wrappers -p 'test_forms_static.py'`:
55 OK. No other form or tool changed; no earlier module carries a Verus `no-call:` line,
so no earlier gate result moves.

## 7. Other checks run (final files)

All on the final files (`final-2.txt`, `final-3.txt`):
`vcheck Q16` (both units verified, 4 holes; the chapter's `units` fence captured);
`vaudit` one finding per hole (Dafny unit 2, crate 2) and `vaudit --ref` 0 on both twins;
`vcheck --ref --gate` on the twins (141, 15; 0 holes); `vcheck --ref --pin-counts Q16`
(re-run after the inner step's rewrite moved the crate's count from 16 to 15: a scoped
`nonlinear_arith` assertion is a verified task of its own); `vcheck --shipped Q16` 0
problems; `specfreeze --pin`, then `--check Q16` 0 findings; `reference_lint.py --module
Q16` 0 findings; `firsttry Q16 --lint-hollow` OK (2 files); `--report` (0 slots, 38
commented checks, 0 forms not met, 0 missing receipts); `pins.py --ci --module Q16` 7
pins, 0 problems (`--ref --module Q16`: nothing to check, §1); `pins.py --chapter Q16` 3
pins, 0 problems; `chapter_lint Q16` 0 problems (2,587 words, 4 diagrams, 3 pinned
fences); `gen_units.py --check` (35 units); `check_course_map.py` OK (49 modules, 17
authoring) and `--only vocab` OK (no new concept row); `avoid.sh` OK (0 hits);
`update_rubric_pins.sh` (Q16's four pins written and current; the 6 pending pins the
check reports are Q17's rubric, another lane's); `make -C paper paper` (34 documents)
and `paper-solutions` (17) green; the two fixtures compiled with latexmk in a scratch
copy; the leak verifier over all 16 modules OK (1,552 public files); the static wrapper
suites (`test_{dafny,forms,pcount,practice_tools,tools,verus}_static.py`: 57, 55, 7, 32,
112 with 1 skipped, 49: OK). `scripts/test_course_map.py`: 366 passed, 6 failed, every
failure from other lanes' in-progress registry records (Q18's planned record declares
imports, among them a harness gate file, which the fixture's armed cases and the Q gate
cases do not expect); arming Q16 cleared the two import-tier failures the L7 lane
reported.

A line-level answer check: every twin line of at least 16 characters that the learner
file lacks was searched (whitespace-normalized) in the chapter, bank, rubric, problems,
answers, learner files, QPLAN, the chapter pins and the registry: the only hits are the
commented checks and the speed test (shipped by design) and the generic `requires
Valid(s)` in QPLAN.

## 8. The chapter and the kit

- **Chapter** `docs/Q16_PracticeIIIA.md`: about 2,600 words, 4 diagrams, 3 pinned fences
  (`ghost-call`, `plain-h1d`, `units`); no predict box (Q16 has no P item); no exit
  section (no exit file; chapter_lint requires one only when `exits` is non-empty); the
  hard tier's no-hint rule stated (§8 "The hint dial"). Hints removed in review of my own
  draft, after QPLAN's plan review (M19) removed the same kind from QPLAN: the
  invariants' domains, the H2v lemmas' subjects and the row-lift lemma's subject.
- **Written pair** `paper/Q16_problems.tex` / `paper/Q16_answers.tex`: B1 the blueprint
  (`[informal-proof-first]`, 30 minutes, ≥ 3 on every dimension before formal work;
  parts (a)–(e) per problem), B2 card 01.13 (`cheatsheets.md` lines 458–481, sha256
  `e4dafe60c3a94bf011321b2f331db4fc667b6ee3fbafdfc9b0f518e3aa104c08`, the heading through
  the *Why it matters* paragraph). `paper/solutions/Q16_solutions.tex`: the reference
  blueprint (the twins') and the card fields with their lines.
- **Rubric** `paper/rubrics/Q16_rubric.md` at `library-pr`: Probes A (a Dafny claim
  about `MulAcc`, negated at an empty `b`), B (a Verus claim, negated at a literal state),
  C (card pin), D (dead line), E (stability), F (speed test); B1's five dimensions with
  predicates; Gate A1–A7; focus C1–C8. Probe A and B as shipped and with a true claim:
  captured (`rubric/`): A verifies with the placeholder and fails with the true value;
  likewise B. Ghost `MulAcc` cannot be evaluated by a compiled test (`vcheck --test`
  takes no module context, so a test file cannot import the layers: probed, resolve
  error), and literal evaluation of `MulAcc` on a non-empty `b` does not verify (the
  opaque `AddC` and fuel; probed with both a false and a true right side): so the
  rubric's refutations are verified negations at instances that unfold in one step.
- **Bank** `.claude/skills/instructor/banks/Q16.md`: K1–K8 (S1 K2, K5; S2 K3, K4; S3 K7;
  S4 K1, K8; S5 K6), 4 predicts, 7 backward edges to 7 different modules, every probe
  output real (`runbank.py`, `assemble.py`; `bank/all.json`), three parallel problems
  with references verified and stable on seeds 1–3 (`bank/ref/`). Toy names checked
  disjoint (grep over the course's code trees) and `avoid.sh` clean after `Bin` was
  renamed `Binary` (a curated Lean name). The hard tier's viva draws are Q18's to table.
- **Fixtures**: `tests/instructor/fixtures/Q16_flawed_answers.tex` (one planted flaw: H1's
  generalization multiplies the accumulator by `Pow(k)` too; Probe A refutes it,
  verified, captured; the reference generalization at the same instance is not refuted)
  and `Q16_gold_answers.tex` (correct, paraphrased lemma names); both compile.
- **Leak patterns** `tests/instructor/leak_patterns/Q16.txt`: 8 (H1d twice, H3d, H2v
  twice, H3v three times) and the README row; the verifier over all 16 modules OK.

## 9. Deviations from the plan

1. **H3v's reference is new** (QPLAN §26.4: "no reference yet"); its shape is §3's.
   The plan expected "an inner and an outer invariant, and a row-lift lemma": as built,
   two invariants and two helpers (a push and a write), 96 proof lines.
2. **A Verus `no-call:` form** was built (§6) to close H3v's known shortcut; the prompt
   names `big_add` and `NatLike::plus`. QPLAN §26.3's H3v form column said only
   "`external_body` + `unimplemented!()` + commented suite".
3. **Form lines on H2v and H3d** (`loop-dir:i:down`, `loop-dir:up`), each closing a
   construct-free answer that verifies (§4); the prompts name the direction (and H2v's
   counter `i`). QPLAN §26.3's prompts said "from the top limb down" and "a compiled
   loop"; the counter name is new.
4. **One file per language, one `HELPERS` area per file.** A.18's `divl.rs` is merged
   into `lib.rs` (QPLAN §26.2 lists only `lib.rs`).
5. **The Verus crate imports `vstd::arithmetic::div_mod`** beside `mul` (H2v needs it);
   QPLAN §26.2's tier is unchanged (`arithmetic`).
6. **L7's subtraction is `big_sub`** (the L7 lane's rename); Q16 does not call it except
   in H2v's `cfree:` line.
7. **The prompts' closing questions** are neutral ("Which equation between values holds
   at every step?", "What must the invariant say for its last instance to give the
   `ensures`?") rather than the plan's invariant-domain hints (M19).
8. **The twin carries two reference-only declarations** (`MulRec`, `MulRecIsMulAcc`) that
   exist only so the empty-body gate can run H3d's `cfree:` body; two of the Dafny twin's
   141 verified tasks are theirs.

## 10. DELTAS-ready text (for the records lane)

> ### Δ2xx · Q16 code and kit as built; a Verus `no-call:` form; H1–H3 admitted — adopted (DV5c, 2026-10-11)
> - **Status:** Q16's code, chapter and kit (practice III-A, family A, the hard tier's
>   first module) on Δ195's and Δ198's model, built on layer L7 as the L7 lane left it.
>   Like Δ160–Δ205, it names no answer; the detail is in `Solutions/plans/Q16-code-notes.md`.
> - **Change:**
>   - **Files.** `dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy` (one nonlinear-off
>     module over L1–L7 and `Std.Arithmetic.Mul`), `verus/q/q16_practice_iiia/src/lib.rs`
>     (with H3's speed test commented after `verus!`), their twins, the generated units;
>     no exit file, prediction, slot or specimen. 4 holes (Dafny 2, Verus 2).
>   - **Pins.** `expected/Q16.counts` (Dafny unit 141 / floor 2, crate 15 / floor 2),
>     `expected/Q16.freeze` (8 statements; the module's nonlinear lever frozen),
>     `expected/Q16.chapter.toml` (3 pins).
>   - **References.** H1d and H2v from the author notes' A.17 and A.18; **H3v's in-place
>     schoolbook is new** (two loops, two helpers, 96 proof lines; the pair with H3d 102,
>     inside the Verus band, Δ178). Counts under the layout rule D1: H1d 47, H2v 60.
>   - **Forms.** H2v `loop-dir:i:down` and H3d `loop-dir:up` (each kills a verified
>     construct-free answer: division by repeated subtraction; a compiled recursion in
>     place of the loop); H3v `no-call:big_add, no-call:plus`, which kills the plan's first
>     draft (rows by whole-number addition), fast enough to pass the speed test.
>   - **Tool:** `dvl.forms`'s `no-call:<f>` applies to Verus (`v_no_call`: the block's fns
>     and the same-file helpers they reach, as `no-nl`); `test_forms_static.py` 55 OK.
>   - **Admissions** (`[module.admissible]`): H1d 45, H2v 50, and the gated pair H3v 35 +
>     H3d 20 on the lane's recorded gate (QPLAN §19.0's gated-items rule; Δ178). Hole
>     minutes 150 of 225: every H line whole.
>   - **Chapter and kit.** `docs/Q16_PracticeIIIA.md` (3 pinned fences: the ghost call
>     refused, the plain H1d attempt failing on both conjuncts, the units); the written
>     pair (B1 the blueprint, B2 card 01.13), solutions, rubric at `library-pr` (Probes A–F),
>     bank K1–K8 with three parallel problems, fixtures, 8 leak patterns.
> - **Why:** the Q16 lane's runs (16 GB scope, one job at a time): `firsttry --empty-body`
>   4/4 (twice); the twins gate 141 / 15 with 0 holes; `--brittleness` stable (Dafny on
>   both bundled solvers); the speed test 2 passed on the twin; `vcheck --shipped`,
>   `specfreeze --check`, `reference_lint`, `pins.py --ci`, `--lint-hollow`, `--report`,
>   `gen_units --check`, `check_course_map` (and `--only vocab`), `avoid.sh`,
>   `chapter_lint`, `update_rubric_pins.sh --check`, `make -C paper paper` and
>   `paper-solutions`, and the leak verifier clean.
> - **Touches:** Δ173, Δ178, Δ182, Δ191, Δ195, Δ198; the user's D1 and D4; QPLAN §26
>   (§26.3's H3v form and the prompts' wording are superseded as §9 of the notes says);
>   `MODULES.toml` (Q16); `scripts/dvl/forms.py`; `tests/wrappers/test_forms_static.py`;
>   `verus/Cargo.toml`, `Solutions/verus/Cargo.toml`.
> - **Owner:** this round's Q16 lane.
> - **Open** (owner, severity): the calibration owner (medium): `calibrate.py` covers
>   Q01–Q15 (Q16's tutor holes and budget); the simulations owner (high: before Q16
>   ships): Q16's skill simulations; the Q18 lane (medium): the hard tier's viva draws in
>   `banks/Q18.md` over K1–K8; the records lane (low): QPLAN §26.3–§26.6 text this entry
>   supersedes.

## The DV5c review fix round (2026-10-12)

Reproduced and fixed, with the twin carrying each known shortcut so the empty-body gate runs it:

- **H3v, the copied adder.** L4's `big_add` copied as `my_add` (a helper under the HELPERS
  line) with the H3v `cfree:` body calling it verified and passed `no-call:`. New form
  `no-adder` (`dvl.forms.v_no_adder`): no exec helper the block reaches states a whole-number
  sum in its `ensures` (`A == B + C` over `.to_nat()` / `seq_to_nat(…)` terms, either way
  round). The learner block and twin carry `// form: no-call:big_add, no-call:plus,
  no-adder`; the twin's second answer is the copied-adder variant, its helper given by
  `// cfree-decl:` lines (new: firsttry puts them below the file's HELPERS line, outside every
  block). An in-place row helper (its `ensures` a sum with a product) passes the form.
- **H2v and H3d, padding.** H2v's repeated-subtraction answer plus a down-counting dummy loop,
  and H3d's `MulRec` answer plus a dummy up loop (or the call moved into a one-pass loop),
  passed `loop-dir`; the extended rule (Q13 notes §13) needs one checked loop to read an
  argument at its counter and assign what the result is computed from. Twin answers: H2v 2,
  H3d 2 and 3.
- `firsttry.sh Q16 --empty-body` (92 s): **4/4**, exit 0; every recorded answer verifies or not
  and fails a form (H3v 1 `no-call:big_add`, 2 `no-adder`; H2v 1–2, H3d 1–3 `loop-dir`). H3v
  keeps 35 and H3d 20.
- **Bank K7** rewritten (a prefix identity over an unweighted fold, `Cairn`), re-captured with
  `runbank.py` (archive `dv5c/fix/bank/`); its fields are unchanged, so `check_draws.py` OK; the
  leak pattern for H3v's `lemma_set_limb` call was retargeted to H2v's suffix-step `ensures`;
  the leak verifier OK.
