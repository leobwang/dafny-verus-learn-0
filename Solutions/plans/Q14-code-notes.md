# Q14 code notes (DV5b, the Q14 module lane)

> **Author-only.** The prediction answer and the evidence it was captured from, the hole gate
> results, the admissibility results (the four results of QPLAN §19.0) of every H item, the
> construct-free and shortcut probes, the H3d band work, and every deviation from the plan.
> Never quote, paraphrase or link any of it from a learner-visible file. The item plan is
> `QPLAN.md` §19 and §24 (learner-visible) and `Solutions/plans/Q10-Q18-author-notes.md` §6,
> §13 and Appendices A.15, A.16 and C.6; this file records what the module lane built and
> re-captured on the real files, 2026-10-11.

Every run went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/specfreeze`, `scripts/reference_lint.py`)
at the course pins (Dafny 4.11.0 with its bundled Z3 4.12.1, and 4.14.1 for the `--solvers`
axis, `--resource-limit 5000000`; Verus and vstd `0.0.0-2026-09-20-0158`, `--rlimit 2`), one
solver job at a time under the `dvl` caps (Dafny 8 GB, Verus 16 GB); both empty-body sweeps
also ran inside a 16 GB `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, the
lane's share. `free -g` read 92–102 GB available before each batch. `DVL_SCRATCH` was
`/tmp/dvl0-dv5b-q14/scratch`. Probes ran from `instructor/scratch/q14/`. The archive is
`~/.cache/dafny-verus-learn-0/author-probes/dv5b/q14/`: `probes/` (every probe and variant
file named below), `runs-raw/` (the three prediction runs), `empty-body-1.txt`,
`empty-body-final.txt`, `forms-gate.txt`, the brittleness outputs (`brittleness-dafny-unit.txt`,
`brit-v2.txt`, `brit-dx.txt`, `brit-rd_*.json`, `brit-vlib_b.json`, `brit-vperm.json`) and the
drivers (`pcount.py`, C.8's counter; `minimize.py`, a greedy line dropper; `brit.sh`).

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q14_PracticeIIB/std/Q14_PracticeIIB.dfy` | verified, 2 holes: H3d (bodyless lemma, one `ensures`), H1d (refined lemma `{ assume false; }`, Δ154); P1dv; modules `Q14_Term` (first) and `{:disableNonlinearArithmetic} Q14_Cached refines QG_L4_Spec` (last, Δ31; C.6's order) | twin |
| `dafny/Q/Q14_PracticeIIB/std/Q14_Loop.dfy` | verified, 1 hole: H4d (bodyless lemma, one `ensures`); W2d; module `{:disableNonlinearArithmetic} Q14_Loop`, no import | twin |
| unit `dafny/Q/Q14_PracticeIIB/std` | learner loop 146 verified, 3 holes | twin 152 verified (`expected/Q14.counts`: 13 symbols, floor 13); `Solutions/dafny/Q/Q14_PracticeIIB/std/dfyconfig.toml` mirrors the generated project |
| `verus/q/q14_practice_iib/src/lib.rs` | verified, 4 holes: H2v's `add_word`, `read`, `from_big`, H3v (`external_body` over `unimplemented!()`); `mod perm;` | twin (`// triv: <method>:` lines on H2v, `// triv: { 0 }` and the `cfree:` loop on H3v) |
| `verus/q/q14_practice_iib/src/perm.rs` | verified, 2 holes: H5v's `push_front`, `sum` (`external_body`) | twin (`// triv: push_front: { }`, `// triv: sum: { 0 }`) |
| crate `verus/q/q14_practice_iib` | 6 holes | twin 18 verified (9 symbols, floor 9); `Solutions/verus/q/q14_practice_iib/Cargo.toml` (`solutions_q14_practice_iib`), a member of `Solutions/verus/Cargo.toml` |
| `dafny/Q/Q14_PracticeIIB/exit/Q14_Exit.dfy` | verified, 1 hole (X1d, bodyless lemma) | twin 132 verified |
| `verus/q/q14_practice_iib/src/exit.rs` | verified, no block, no hole; one given empty proof fn (`no_verus_exit_item`) | twin 1 verified |
| `slots/Q14.slots` (1 line, unfilled) | — | `Solutions/slots/Q14.slots` |
| — | — | `expected/Q14.pins` (1 salted hash), `expected/Q14.counts` (schema 2: 2 units, 6 files), `expected/Q14.freeze` (59 statements in 6 files; `open_bodies = ["Accum::total"]` in lib.rs) |

Header counts as shipped: 9 counted holes in 6 items (Dafny 3; Verus 6), 1 prediction, 1 timed
exit item. No specimen, card, agent or harness file (QPLAN §24 gives Q14 none); `specimens/Q14/`
is not created.

## 2. The prediction answer, captured

| item | answer | evidence (probes `p1.dfy`, `p1b.rs`; raw runs in `runs-raw/`) |
|---|---|---|
| P1dv | `D:fail V:fail` | Dafny `function Swap2` with no `decreases` (the docstring's text, a file of its own): failed (22 verified, 1 error) "cannot prove termination; try supplying a decreases clause" at the recursive call. Verus `pub open spec fn swap2(...) decreases a.len(), b.len(),`: failed (0 verified, 1 error) "could not prove termination" |

**The Verus half deviates from QPLAN §24.2** (which has the Verus `spec fn` with no
`decreases` too). That form was captured first (`p1.rs`): failed, stage resolve, "recursive
function must have a decreases clause" (`D:fail V:err:resolve`), which Q08.P4dv's Verus half
already settles (a recursive spec fn with no measure is refused at resolve). Author notes §0.2
say to replace a scenario an earlier prediction settles, so the Verus half writes out Dafny's
default measure (the two lengths in parameter order) instead: the learner predicts whether that
lexicographic measure decreases at the swapped call. The Dafny half is new (Q05.P2dv's default
measure decreases; this one does not). `pins.py --update --ref --module Q14` wrote the salted
pin; `pins.py --ref --module Q14`: "1 check(s); 0 problem(s)".

## 3. Holes: references, line counts and the empty-body gate

Line counts under QPLAN §19.0's rule (`pcount.py` on the twins; invented statements by its
`stmt_lines`; exec code excluded):

| item | reference | proof lines | band | invented lemmas |
|---|---|---|---|---|
| H1d `CmpCorrect` + `Shorter` | A.16 verbatim | 6 + 5 + statement 3 = **14** | 10–30 | 1 |
| H2v `impl Accum for PairAcc` | C.6 verbatim | `add_word` 0 (2 code), `read` 10 (7 code), `from_big` 14 (9 code) = **24** | 15–45 | 0 |
| H3d `InterleaveSpec` + `InterleaveCount` | new (§4) | 8 + measure 1 + 5 + statement 3 = **17**; the shortest known one-lemma proof 9 + 1 = 10 | 10–30 | 1 |
| H3v `sum_limbs` + `lemma_limb_sum_cons` | C.6, plus two assertions (§6) | 17 (6 code) + 7 + statement 6 = **30** | 15–45 | 1 |
| H4d `WpSoundWhile` | new (§5) | **16**; greedy minimum 12 (`minimize.py`) | 10–30 | 0 |
| H5v `List::push_front`, `List::sum` | new (§5) | `push_front` 3 + 2 (the tracked and ghost field updates, by hand: the counter tags them code) + `sum` 15 (8 code) = **20** | 15–45 | 0 |
| X1d `PushAllConcat` | new (§7) | 3 + measure 1 | — (exit) | 0 |

`systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 scripts/firsttry.sh Q14
--empty-body` on the final files: **7/7 pass**, exit 0 (`empty-body-final.txt`):

| item | result |
|---|---|
| H1d | the empty body fails in every run (maxauto and seeds 1–3); the `cfree:` answer fails verification |
| H3d, H4d, X1d | the empty body fails in every run (maxauto and seeds 1–3) |
| H2v | one gate per hole method (`<PairAcc as Accum>::add_word`, `read`, `from_big`): each fails in every light mode and seed, TRIV with the twin's named bodies (`{ }`, `{ BigNat { limbs: Vec::new() } }`, `{ None }`) |
| H3v | the empty body fails in every mode, TRIV `{ 0 }` included; **the `cfree:` answer verifies and meets every form** ("CONSTRUCT NOT REQUIRED"), reported and not failing the run because the registry records H3v as not admitted (§6) |
| H5v | one gate per hole method (`List::push_front`, `List::sum`): each fails in every light mode and seed, TRIV `{ }` and `{ 0 }` (the E0 family keeps `let tracked` lines, Δ182) |

The per-method gate of H5v needed a tool change (§8): before it, an inherent-impl item was
gated on its first fn only, so `sum` would have gone ungated.

## 4. H3d: the band finding and the extension

The plan's statement (length, multiset and the first two elements) has a 4-line proof (author
notes §6.2). Its named candidate does not extend it: an element-by-element law, written two ways
on this unit's options, is proved by the same four lines.

- `v_nofor.dfy`: the A.16 statement with `forall k :: … Interleave(a, b)[2 * k] == a[k]` and
  the odd-index twin added, and the reference's two `forall` statements removed: verified.
  `minimize.py` then removed every assertion but `a == [a[0]] + a[1..]` (`v3.dfy`: verified).
- `t1.dfy`: the parity form (`i % 2`, `i / 2`) plus the two tail laws, with the same 4-line
  body: verified.

So the lane wrote another in-band candidate, as §6.2 allows: **appending one element to each
side** (`|a| == |b| ==> Interleave(a + [x], b + [y]) == Interleave(a, b) + [x, y]`, and with
`|a| == |b| + 1` the elements' roles exchanged), beside the length and multiset conjuncts; the
"first two elements" conjunct is dropped (it is automatic). The statement gains two parameters,
`x` and `y`. Evidence:

- `t2.dfy`: the minimal 4-line body fails (2 errors, one per appended law); `t5.dfy`: with no
  measure the recursive call fails ("cannot prove termination"), so the learner's measure is
  needed (the default is the parameter tuple).
- `t3.dfy`, `t4.dfy`: one-lemma proofs verify; `t4.dfy` (9 lines + measure = 10, the band's
  edge) is the shortest found.
- **Cost.** The one-lemma proof, stable on both solvers × seeds 1–3, costs 1.18–3.89 M resource
  units (up to 78% of the limit; CV 47.4% under 4.14.1), and one variant (`h3d_v4.dfy`) went
  out of resources under 4.14.1 seed 1. `h3d_nom.dfy` (no multiset conjunct) is cheap, so the
  multiset axioms meeting the appended sequences are the cost. The reference therefore proves
  length and multiset in the one invented lemma (`InterleaveCount`, by the same recursion) and
  the appended laws in the item (`h3d_b.dfy`; `h3d_a.dfy` without the multiset assertion was
  flagged at CV 31.4%): at most 302,092 units, no flag.

The learner may write the one-lemma proof; it verifies at the pin but near the limit. The
chapter lane may want to say so in its brief (§10).

## 5. The gated items (H4d, H5v): designs as built

- **H4d** (`Q14_Loop.dfy`, QPLAN §19.0 *gated*). W2d is Q11's language (`Q11_Wp`) with
  `While(b, inv, body)`, an `Outcome = Stuck | Done(s)` result, a fuelled
  `Exec(c, s, fuel)` (`decreases fuel, c`; a loop iteration spends one unit; `Seq` and `IfThen`
  pass the fuel on), `Wp(While(b, inv, body), q) = inv`, `Vcs(c, q): set<BExp>` collecting
  `Imp(And(inv, b), Wp(body, inv))` and `Imp(And(inv, Not(b)), q)` for every loop and its body,
  and `ghost predicate Valid(p)`. The statement (one `ensures`, `decreases fuel` shipped): the
  body's soundness for `inv` as a hypothesis (as Q11.H9d's), every member of
  `Vcs(While(b, inv, c), q)` valid, `Holds(Wp(While(…), q), s)` ⟹ a `Done` run ends in `q`.
  It is the `While` case only: Q17.H3d's whole-language soundness statement is not stated here
  (author notes §9). Reference 16 lines (the two membership assertions per case, the unfoldings
  of `Imp`/`And`/`Not`, the recursive call from the body's final state).
- **H5v** (`perm.rs`, tier `all`). Given: `Node { val, next: Option<PPtr<Node>>, perm:
  Tracked<Option<PointsTo<Node>>> }` (the permission of `next`), `chain_wf` and `chain_view`
  (recursive on a ghost length), `vals_sum` (front-defined), `List { head, perm, len: Ghost<nat>
  }` with `View` and `wf`, and `List::new`. Holes: `push_front(&mut self, v)` (ensures
  `final(self)@ == seq![v] + old(self)@`) and `sum(&self) -> u64` (requires the sum to fit in a
  `u64`, so no product bound is needed). One permission per node, no map (author notes §6.3; W19
  is not needed on the Q side for Q14, §9). The reference: `push_front` exchanges the list's
  permission for `None` with `vstd::modes::tracked_swap`, puts it into the new node and keeps the
  new node's permission; `sum` walks a tracked shared reference to the current permission,
  borrowing each node with `PPtr::borrow` and re-pointing the reference at the node's own
  permission inside a proof block. Both verified at the first full try (`perm1.rs`).

Both gated items were admitted on the module lane's recorded gate (the four results, §6), as
QPLAN §19.0 and design §7.5 allow; their fallbacks are not needed and have no reference.

## 6. Admissibility: the four results

Stability: `vcheck --ref --brittleness --solvers` on the Dafny twin unit and on the exit twin:
stable in all six rows; `vcheck --ref --brittleness` on the Verus twin crate: stable (seeds
1–3), widest spread CV 6.2%. Per-symbol figures from the twins run as probes in Q14's context
(`rd_main.dfy`, `rd_loop.dfy`, `rd_exit.dfy` with module names suffixed `R`; `vlib_b.rs` with
`mod perm;` removed, `vperm.rs`).

| item | 1. complete, in band | 2. empty-body gate fails | 3. stable | 4. pinned API | entry |
|---|---|---|---|---|---|
| H1d | twin unit 152, 0 holes; 14 lines | yes; `cfree:` killed | `CmpCorrect` 40,644..45,132, `Shorter` 27,335..27,948 (CV ≤ 3.7%, both solvers) | `Std.Arithmetic.Power.LemmaPowIncreases` (Dafny 4.11.0 standard library); L2 `ToNatBound`, L3 `PowIsStdPow`, `FromNatCorrect`, L4 `CmpCorrect`, L5 `CanonicalLower`, L6 `FromNatCanonical`, `NormalizeAddCorrect` | admitted, 35 |
| H2v | crate twin 18, 0 holes; 24 lines | yes, each method, TRIV included | `from_big` 85,636..94,189 (CV 4.5%), `read` 27,821..28,196, `add_word` 37,868..37,935 | L1 `seq_to_nat`, L3 `lemma_seq_to_nat_lower`, `lemma_weight_mono`, `lemma_weight_zero`, `lemma_weight_succ` | admitted, 30 |
| H3d | 17 lines (§4) | yes | `InterleaveSpec` 201,097..302,092 (CV 16.4%), `InterleaveCount` 102,568..229,279 (CV ≤ 16.0%) | — | admitted, 12 |
| H3v | 30 lines (29 under D1, §13) | yes (every mode, TRIV `{ 0 }`); since DV5c its `loop-dir:i:down` form kills the `cfree:` loop (§13) | `sum_limbs` 174,649..180,855 (CV 1.5%), `lemma_limb_sum_cons` 45,021..46,853 | vstd `arithmetic/mul.rs`: `lemma_mul_inequality` (l. 164), `lemma_mul_is_distributive_add_other_way` (l. 280) | **admitted, 13** (DV5c; not admitted before, below) |
| H4d (gated) | 16 lines | yes | `WpSoundWhile` 129,058..144,295 (CV ≤ 1.4%) | — | admitted, 30 |
| H5v (gated) | 20 lines | yes, each method, TRIV included | `List::sum` 100,831..104,576 (CV 1.7%), `List::push_front` 20,930..21,150 | vstd `simple_pptr.rs`: `PPtr` (l. 153), `PointsTo` (l. 162), `pptr` (l. 222), `is_init` (l. 257), `value` (l. 267), `PPtr::new` (l. 397, returns `(PPtr<V>, Tracked<PointsTo<V>>)`), `PPtr::borrow` (l. 530); `modes.rs` `tracked_swap` (l. 9); `std_specs/option.rs` `tracked_borrow` (l. 45); `Tracked::borrow`, `borrow_mut` (verus_builtin) | admitted, 30 |
| X1d (exit) | 3 + measure | yes | `PushAllConcat` 33,432..47,198 (CV ≤ 15.1%) | — | (exit) |

**H3v was not admitted (DV5b; admitted at 13 in DV5c, §13).** Its four results hold, but a shortcut the lane measured passes: the
loop **from the low limb up** (the plan's first form, A.15, 13 proof lines, below the band) meets
the statement with no lemma (`h3v_up.rs`: verified; in the twin as the `cfree:` answer, which the
forms gate reports as "CONSTRUCT NOT REQUIRED"). It skips both the prompt's direction and the
item's `lemma-recursion`. No form rule of `dvl.forms` sees a loop's direction (Δ186, Δ191: no
loop form is built), so under Δ173 the item carries 0 minutes, and its fallback (the bound as a
runtime argument) has no reference and carries 0 too. The termination + erasure line carries 12
of its 25 minutes. The twin's own `sum_limbs` gained two assertions over C.6 (the limb's bound,
and the partial sum below `len * bound`): C.6's form verified stably but flagged (CV 20.6–30.8%
over runs); with them, CV 1.5% (`vlib_a.rs` tried one assertion: CV 28.5%).

Registry (Q14's record, written by this lane): `admitted = true` with QPLAN §24.5's minutes for
H1d (35), H2v (30), H4d (30), H5v (30), and H3d at §24.4's 12; H3v `admitted = false, minutes =
0`. Of design §7.5's 210, the H lines carry 137 of 150; the shortfall is H3v's 13.

## 7. The exit

QPLAN §24's exit X1d (author notes §6.6's proposal, `CmpAntisym` over L3's `Cmp` with `decreases
|a| + |b|`) was replaced: its measure is not needed (`x1.dfy`: the lemma with no `decreases` and
the two-line body verified, 131), so it did not test S7. The replacement, `PushAllConcat(a, b)
ensures PushAll(a, b) == a + b` over a given tail-recursive `PushAll` (`decreases |b|`, given),
ships with no measure: the default (the parameter tuple) fails because the first argument grows
(`x3.dfy`: "cannot prove termination"), and `decreases |b|` with the recursive call and one
sequence identity proves it (`x2.dfy`). `need: lemma PushAllConcat(a: seq<nat>, b: seq<nat>)`.
It shares no declaration or structure with H1–H5 (H3d's recursion swaps its arguments; this one
grows one) and no Q10–Q13 item; `avoid.sh` is clean. The Verus exit file holds no block; the
gate needs one verified function per target (`verified 0 < the unit's minimum 1`), so it ships
one given empty proof fn, in the learner file and the twin alike.

**Fix round (DV5b review, 2026-10-11).** The given `PushAll` printed the answer's measure
(`decreases |b|`) four lines above the hole of a closed-book file. It now takes its arguments
the other way round, `PushAll(b, a)` recurring as `PushAll(b[1..], a + [b[0]])`, and ships no
`decreases`: its default measure (`b, a`) holds (the learner file verifies, 131, 1 hole). The
lemma keeps its parameter order, `PushAllConcat(a, b) ensures PushAll(b, a) == a + b`, so its
default measure (`a, b`) still fails at the recursive call (probe: the twin without its
`decreases |b|`, "cannot prove termination"), and the twin with it passes `--gate` (132).
`specfreeze --pin Q14` re-pinned (0 findings); `vcheck --ref --pin-counts Q14`; `firsttry.sh
Q14 --empty-body` 7/7 (X1d's empty body fails in every run; H3v's recorded shortcut still
reported, not admitted); the exit twin stable under `--brittleness --solvers` (both solvers ×
seeds 1-3, widest CV 16.8%); `vcheck --shipped Q14` 0 problems; chapter pins re-captured (8,
`--ci` 18 pins, 0 problems; the `units` pin moved with the exit's lines).

## 8. Tool change: per-method gates for an inherent impl (`scripts/firsttry.py`)

`impl_hole_methods` gated per method only a block whose first fn is a method of `impl Trait for
Type` (QPLAN §30 Q65(a), built for Q14.H2v). H5v's two holes are methods of an inherent `impl
List`, so only `push_front` would have been gated. The change: a block whose first fn is a method
of an inherent impl is gated per method too **when it holds two or more hole methods** (symbols
`Type::method`); a one-method block keeps its first fn's gate, so no earlier item's gate changes
(a scan of every armed Verus file finds only Q14.H2v and H5v under the per-method path). The
messages that said "trait-impl item" now say "impl item". `tests/wrappers/test_practice_tools_static.py`
`TraitImplItems.test_hole_methods` now expects the two-method inherent block to be gated per
method and adds a one-method block that is not; `test_practice_tools_static` and
`test_forms_static`: 76 tests OK. For the tools owner's review.

## 9. Deviations from the plan (and why)

1. **H3d's statement** (§4): the appended-element laws replace "the first two elements", with two
   new parameters `x`, `y`; the plan's named candidate is automatic on the unit's options.
2. **P1dv's Verus half** (§2): Dafny's default measure written out, since the plan's form is
   settled by Q08.P4dv.
3. **X1d replaced** (§7): the proposed exit's measure was not needed.
4. **H3v not admitted** (§6); the twin adds two assertions to C.6's loop for stability.
5. **The Verus exit file ships one given empty proof fn** (§7), so its gate has a function to
   count.
6. **File order.** The Dafny file holds `Q14_Term` (P1dv, H3d) before `Q14_Cached` (H1d), as
   C.6 and Δ31 require; the header gives the module's working order (H1, H2, H3 Verus then
   Dafny, H4, H5).
7. **H5v's operations** are methods of an inherent `impl List`, gated per method after §8's tool
   change; `sum` returns a `u64` under a precondition that the sum fits.
8. **Checks the plan did not list**: `InterleaveSpecCheck`, `CmpCorrectCheck`, `pair_acc_check`,
   `sum_limbs_check`, `list_check`; commented under `Uncomment as you go:`, live in the twins.
9. **Names the plan left open**: `Outcome`/`Stuck`/`Done`, `Valid`, `WpSoundWhile` (H4d);
   `Node`, `List`, `chain_wf`, `chain_view`, `vals_sum` (H5v); `PushAll`, `PushAllConcat` (X1d);
   the invented `InterleaveCount` (H3d's reference helper).
10. **W19** (Δ177): Q14.H5v uses no tracked map, so the Q side of W19 needs only Q17.H2v.

## 10. Runs (final files)

- `vcheck --module Q14`: Dafny unit 146 verified, 3 holes; crate 6 holes; 9 in all. `vcheck
  --ref`: Dafny twin unit 152, crate twin 18, Dafny exit twin 132, Verus
  exit twin 1, all 0 holes; the learner exit files 131 verified + 1 hole (Dafny) and 1 verified (Verus, gate).
- `vaudit`: one finding per hole (Dafny `audit-bodyless-ghost` ×3 (H3d, H4d, X1d),
  `audit-assume` (H1d); Verus `hole-external-body` ×6); `vaudit --ref` 0 on every twin.
- `vcheck --ref --pin-counts Q14`: Dafny 152 (13 of the contract declarations pinned, floor 13),
  Verus 18 (9 of 12, floor 9), 6 files. `vcheck --shipped Q14`: 6 files, 0 problems.
- `specfreeze --pin Q14`: 59 statements in 6 files; `--check Q14`: 0 findings (the twins'
  added measures accepted, Δ168).
- `pins.py --ci --module Q14`: 10 pins, 0 problems; `--ref`: 1 check, 0 problems.
- `firsttry.sh Q14 --lint-hollow`: OK (6 files). `--report`: 1 unfilled slot, 36 commented
  checks, 0 missing, vacuous, banned or forms not met; the exits not scored yet.
- `reference_lint.py --module Q14`: 0 findings (6 twins).
- `check_course_map.py`: OK (49 modules, 14 authoring); `--items Q14` parses every item.
  `gen_units.py --check`: 29 units and `verus/Cargo.toml` match.
- `avoid.sh`: OK (Q 1650 declarations, 535 sources, 0 hits).
- The leak-pattern verifier: "13 module(s), 1408 public files scanned, 1 problem(s)": the one
  problem is a Q13 pattern hitting Q13's own learner file and chapter (that lane's), no Q14 file;
  Q14 has no pattern file yet (the kits lane's).

## 11. DELTAS-ready notes (for the records lane)

- **Q14 code as built** (on Δ186's model): the files of §1; 9 holes (Dafny 3, Verus 6), one
  verdict prediction, one timed exit item; pins `expected/Q14.counts` (Dafny 152, floor 13;
  Verus 18, floor 9; 6 files), `expected/Q14.freeze` (59 statements in 6 files), `expected/Q14.pins`
  (1 salted). Admissions: H1d 35, H2v 30, H3d 12, H4d 30 and H5v 30 (the two gated items on the
  lane's recorded gate); **H3v not admitted** (0 minutes): a known shortcut (the loop in the
  other direction, which needs no lemma) passes, and no form rule sees a loop's direction; its
  fallback has no reference. The termination + erasure line is 13 minutes short (Δ173).
  Deviations: H3d's statement extended with an appended-element law (the plan's candidate is
  automatic); P1dv's Verus half rewritten (the plan's form repeats Q08.P4dv); the exit replaced
  (its measure was not needed); the Verus exit file holds one given empty proof fn.
- **Fix round (DV5b review, 2026-10-11):** the exit's given `PushAll` takes its arguments as
  `(b, a)` and ships no measure (§7), so the closed-book file no longer prints the lemma's
  measure; H4d's fallback reads "the loop rule on paper (not built; no rubric rows or model
  answer)": B2 is the paper card 06.9, so the earlier "(B2)" pointed at no problem (QPLAN
  §24.3 and §24.4 still name it: the records lane); the chapter's P1dv paragraph no longer
  says Dafny's default measure compares sequences by length, and Q05's `Ack` is described as
  a first component that never goes up.
- **Tools** (for the tools owner's review): `firsttry`'s per-method empty-body gate covers an
  inherent-impl block with two or more hole methods (Q14.H5v).
- **Open** (owner, severity): the orchestrator or tools owner (medium, before Q14 ships): a
  loop-direction form (or an interim `/review-code` rubric line, as QPLAN §30 Q62 did) to close
  H3v's shortcut, after which H3v can be admitted at 13; the kits lane (high): chapter, written
  pair (B2 is F-H4d's paper fallback, not needed now that H4d is admitted), rubric, bank,
  fixtures and leak patterns; the records lane: W19's Q14 half is not needed (Δ177).

## 12. Interfaces for later lanes

- **Kits lane.** Items and the learner-visible statements as shipped (§1, §5); P1dv's scenario
  is the docstring in `Q14_Term` (the Dafny form has no module wrapper; the Verus form is a
  standalone file with `use vstd::prelude::*;`), answer in `Solutions/slots/Q14.slots`. The
  chapter's brief may note that H3d's one-lemma proof verifies but near the resource limit
  (§4), and that H3v's direction is required by the prompt (§6). Card 06.9 (the module's card)
  is the paper's. `review_bar = "design-judgment"`.
- **Q17 lane.** Q14's W2d/H4d gives the fuelled language with `While`, `Vcs` and `Valid`
  (`Q14_Loop.dfy`); Q17.H3d's soundness statements must not be the H4d lemma or its twin
  proof (tier-internal reuse is across tiers here, but the twin stays author-only).
- **Integration lane.** `CLAUDE.md`'s **Armed** line and `README.md`'s status do not yet name Q14
  (not this lane's files); `Solutions/verus/Cargo.toml` has the `q/q14_practice_iib` member.

## 13. DV5c: the user's decisions D1 and D4, admitted (2026-10-12)

One solver job at a time inside a 16 GB `systemd-run` scope (`free -g` 97–98 GB available);
archive `~/.cache/dafny-verus-learn-0/author-probes/dv5c/tools/`. Q13's code notes §11 has
the rules and the tools.

**D1 (a one-statement proof block counts as one line), re-count** with `scripts/pcount.py`:

| item | before | under D1 | band | status |
|---|---|---|---|---|
| H1d `CmpCorrect` + `Shorter` | 14 | 6 + 5 + 3 = 14 | 10–30 | in |
| H2v `add_word`, `read`, `from_big` | 24 | 0 + 9 + 14 = **23** | 15–45 | in |
| H3d `InterleaveSpec` + `InterleaveCount` | 17 | 17 | 10–30 | in |
| H3v `sum_limbs` + `lemma_limb_sum_cons` | 30 | 16 + 7 + 6 = **29** | 15–45 | in |
| H4d `WpSoundWhile` | 16 | 16 | 10–30 | in |
| H5v `push_front`, `sum` | 20 | 4 + 15 = **19** (`push_front`'s tracked and ghost field updates by hand until DV5d; `scripts/pcount.py` counts them since) | 15–45 | in |

(`read`'s and `sum_limbs`'s closing `proof { … }` blocks and `push_front`'s one-statement block
are what moved.)

**D4 (the loop-direction form).** H3v's learner block and twin carry `// form: loop-dir:i:down`
(the prompt names `i` counting from `v.len()` to 0); the twin's docstring now says the form
kills the `cfree:` loop. `scripts/firsttry.sh Q14 --empty-body` (199 s): **7/7**, exit 0; H3v:
"the empty body fails in every run" (TRIV `{ 0 }` included), "the twin meets its forms
(loop-dir:i:down)", "construct-free answer 1 fails its forms: form loop-dir:i:down not met
(the while loop at line 228 steps `i` up, not down)" (`eb-Q14.txt`). Stability: §13.1. H3v's
four results hold; **registry: `Q14.H3v` admitted, 13 minutes**; the H lines carry 150 of 150
(the termination + erasure line is whole).

**§13.1 Stability and the other checks.** `vcheck --ref --brittleness` on the Verus twin
crate: seeds 1–3 verified, `stable`, widest spread CV 6.2% (a declaration outside the crate's
files); `vcheck --ref --gate` on the crate twin 18 verified, 0 holes; `vcheck --shipped Q14` 6
files, 0 problems; `specfreeze --check Q14` 0; `pins.py --ci --module Q14` 18 pins, 0 problems;
`chapter_lint Q14` 0; rubric pins current.

Chapter §2 (the direction paragraph), §4 (a new `--report --strict` row; the gate and reader
rows), the touchpoints line; rubric A5 (the form line), A7 and C5 (the form is the anchor; the
limb the body reads is still the reader's). The units fence was re-captured (H3v's hole moved
from line 151 to 152). `vcheck --gate` on the shipped Dafny unit no longer reports
`pinned-symbol-missing` for `Q14_Term.InterleaveSpec` (the simulation's finding, DV5b).

## 14. The DV5c review fix round (2026-10-12)

The DV5c admission review's variant of the recorded shortcut (`i` stepping down from
`v.len()`, the limb read at `let j: usize = v.len() - i`, the cfree's invariant otherwise)
verified and passed `loop-dir:i:down`. Reproduced; fixed by the extended `loop-dir` (Q13 notes
§13: indices read through one-definition locals, none subtracting the counter; one loop must
read an argument at its counter and assign the result's identifiers). The variant is the
twin's second `cfree:` answer; the learner docstring adds "each limb read at an index that
counts with `i`". `firsttry.sh Q14 --empty-body` (206 s): **7/7**, exit 0; H3v: the twin meets
its form, answer 1 fails it (steps `i` up), answer 2 fails it (index `j + 1` subtracts `i`).
H3v keeps `admitted = true, minutes = 13` (D4). Chapter §2 and §4 rows, rubric A5, A7 and C5
updated (the reader still checks an index the form cannot follow).
