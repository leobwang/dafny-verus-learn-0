# DVR4 — the R-track repair plan (author-side)

*Status: plan, 2026-10-17, written against `authoring` at `932dd47` (R01/R02 shipped on `basic`; R04–R13 authoring candidates; R14 parked incomplete; R03 parked under `Solutions/plans/drafts/R03`; R15–R16 planned). Author-only: it names hole targets, reference shapes and admission controls, so it lives under `Solutions/` and is never learner-visible. It changes no other file; every step below is a proposal until its DELTAS entry. Binding inputs: the user's decisions **D48** (R03's ranges become `u32` code-point pairs; A2 provisional until R03 and R06 pass) and **D49** (Lab α redesign), and the agreed repair order (canonical line + `basic` → this dependency review → restore R08/R12–R14 and pilot Lab α → one exemplar module → systemic passes → accumulated compatibility CI → R15, R16 → R03 per this review). Section 6 lists what needs a user decision; nothing in §§1–5 that depends on a DECISION item is to be built before the user answers it.*

*Evidence conventions. "Verified" means checked on `932dd47` while writing this plan (command or file named). "Reported" means an independent review's finding that this plan relies on but did not re-check; each reported item has a verification step in §5. "[probe]" marks a tool behaviour this plan assumes and the build step must establish natively before relying on it.*

---

## 0. State at `932dd47` (what this plan relies on)

| module | status | layer | admitted items · minutes (`[module.admissible]`) | chapter words (raw) · dafny/rust blocks · mermaid | bank lines · `**Reread**` | review |
|---|---|---|---|---|---|---|
| R01 | shipped | — | **0 rows** (`admissible = {}`) | 6,485 · 1/1 · 4 | 222 · 0 | B |
| R02 | shipped | A1 | **0 rows** | 6,811 · 0/0 · 4 | 263 · 0 | C+ |
| R03 | planned (parked draft) | A1 | 0 | — (draft ≈ 5,929 lint words) | — (draft bank) | — |
| R04 | authoring | A1 | **0 rows** | 7,323 · 1/1 · 3 | 242 · 0 | C+ |
| R05 | authoring | A1 | 10 · 96 | 6,766 · 0/0 · 3 | 242 · 0 | B- |
| R06 | authoring | A1b | 14 · 218 | 6,708 · 0/0 · 3 | 248 · 0 | B- |
| R07 | authoring | A2 | 10 · 72 | 6,795 · 0/0 · 3 | 234 · 0 | C+ |
| R08 | authoring | A2 | 8 · 90 | 5,325 · 0/0 · 3 | 243 · 0 | D+ |
| R09 | authoring | A3 | 12 · 120 | 4,897 · 0/0 · 3 (outputs in an appendix) | 231 · 0 | C+ |
| R10 | authoring | A4 | 8 · 110 | 5,953 · 0/0 · 3 (appendix) | 234 · 0 | C |
| R11 | authoring | A4 | 22 · 252 | 5,912 · 0/0 · 3 (appendix) | 242 · 0 | B- |
| R12 | authoring | A4 | 11 · 300 | 6,202 · 0/0 · 3 | 240 · 0 | C- |
| R13 | authoring | A4 | 8 · 70 | 5,073 · 0/0 · 3 | 220 · 0 | D |
| R14 | authoring (incomplete) | A4 | 6 · 70 | none | none | F |
| R15, R16 | planned | A4, A5 | 0 | — | — | — |

Q bar for comparison (verified, same counters): Q01–Q09 chapters 7,040–8,591 words, **7–22** `dafny`/`rust`/`python` blocks, 3–5 diagrams; banks 563–1,120 lines with 8 `**Reread**` lines each (Q06: 973 lines for 8 questions, ≈ 120 lines per question).

Verified review findings used below: R08's four hand holes are a call to the given matcher, one `if`/`else` over `ClassMember`, one `reveal`, and one `reveal` plus one `DerivCorrect` call (`dafny/R/R08_Abstraction/std/R08_Abstraction.dfy`); R13's holes are `ClampIndexR13`, `SaturatingSumR13`, `RangeFitsR13`, `PairWitnessR13`; R14's committed holes are `PrefixCapR14`, `OddSquareR14`, `ClearLowBitR14` and its battery is over `PrefixMassR14` (`tools/R14/battery.json`); R12's native holes are `RemainingBudgetR12`, `CountAcceptedR12`, `FirstRejectionR12` (flag loops, no regex object); `specimens/R06/P5v.rs.specimen` lines 174–176 carry one direction of R06.H2v's invariant plus the `DerivCorrect` quantifier; R01's bank Draw A (K1, K3, K5, K7, K9, K11) holds no predict (K2 and K6 are both in Draw B); R02.H4v's reference uses `choose` (Solutions `r02_datatypes/src/lib.rs:189`) and the R02 chapter uses "choose" only as an English verb; `verus/given/rg_re_a2/src/char_class.rs` labels `member_from` "(R03.H1v)", `class_insert` "(R03.W2v)", `class_union` "(R03.H3v)" with no "do not open before" header, and A1b's header does not warn that it holds R02's and R05's answers; `fvh.stats.mde_two_proportions(20, 0.5, paired=True, alpha=0.05/40)` returns `inf` (and 0.43 at n = 40). Lab α's stratum is 40 forms over 20 "paired-language-original-algorithm" clusters (`bench/local/r/labalpha/STRATUM.toml`: accepted-ledger, first-rejection, sum-prefix-odds, quotient-three, …): no regex object. R14's notes record that the pinned wrapper refuses `--log smt` (`Solutions/plans/DVR3-R14-build-notes.md`), which bounds what `trigscan` can observe.

Reported (to verify in §5 step 5): R09's learner Verus file holds R04 reference lines (a grep for the string `R04` finds none, so the finding is about content, not labels); "11–19 % of twin lines pack several statements from R10 on" (this plan's cruder counter, lines with ≥ 2 `;`, gives 1–10 % for R04–R14 against Q06's 0.1 %); R08, R09 and R13 below PLAN §1.2's 5,000-word floor by the lint counter (raw counts above: 5,325, 4,897, 5,073; R13's own notes give 4,503 lint words); CI on R05–R13 was six focused jobs per module, never one accumulated run.

---

## 1. R03 dependency review (D48)

### 1.1 What depends on the `(char, char)` class representation or the Unicode bridge

Found with `grep -rE 'CRange|CharClass|char_class|class_insert|ClassInsert|ClassValid|InClass|ClassMember|class_member|ClassUnion|class_union|\(char, ?char\)|ISet<char>|ClassLowered|ClassToRe|RangeRe|range_re|class_re|SpanClass|from_u32|ClassMax|CLASS_MAX|0xD800|surrogate|scalar'` over the tree (excluding `.git`, `build`, `target`; the Lean course was not read). Everything not listed is independent of the representation: A1, A1b, A4; R01, R02, R04, R05, R06, R10–R14 sources, specimens, chapters, banks and papers; `bench/local/r/labalpha`.

**Layers.**

| file | what depends | kind |
|---|---|---|
| `dafny/given/R/RG_A2_Deriv.dfy` | `datatype CRange(lo: char, hi: char)`, `type CharClass = seq<CRange>` (transparent), `InRange`, `InClass`, `ClassValid` (sorted, `hi < lo'`, adjacency allowed), `MinC`/`MaxC`, `ClassMember`, `ClassInsert` (+ its `res[k].lo >= …` helper clause), `ClassUnion` | representation |
| `verus/given/rg_re_a2/src/char_class.rs` | private `ranges: Vec<(char, char)>`, `in_range`, `in_ranges`, `sorted_ranges`, `lemma_in_ranges_push/drop`, `cover`, `target`, `lemma_insert_step`, `class_empty`, `copy_class`, `member_from`, `class_member`, `class_insert(lo: char, hi: char)`, `class_union`; view `ISet<char>` | representation; R03 labels without a header |
| `dafny/given/R/RG_A3_Syntax.dfy` | `ClassMax = 0xD800`, `ClassLowered(cc)` (reads `cc[i].lo/hi`), `RangeRe(lo: char, hi: char)` (steps with `(lo as int + 1) as char`), `ClassToRe`, `SClass(cc: CharClass, …)`, `WF`'s `SClass` case, `Lower`'s `SClass` case | representation + the below-surrogate lowering domain |
| `verus/given/rg_re_a3/src/ranges.rs` | `SpanClass { pub ranges: Vec<(char, char)> }`: a public-field copy of A2's insertion construction (Δ261), its own `in_range`/`in_ranges`/`sorted_ranges`/`cover`/`target`/`lemma_insert_step`/`class_empty`/`copy_class`/`class_insert` | duplicate representation |
| `verus/given/rg_re_a3/src/lib.rs` | `CLASS_MAX`, `range_valid(lo: char, hi: char)`, `class_valid(Seq<(char, char)>)`, `range_re` (spec `((lo as u32) + 1) as char`), `class_re`, `SyntaxKind::Class(SpanClass)`, `wf`, `lower`, `simple_class_body` (`(s[q] as u32) < CLASS_MAX`) | representation + domain |

**Modules and items.**

| module | files | items / declarations |
|---|---|---|
| R03 (parked draft) | everything under `Solutions/plans/drafts/R03/` | all 10 holes, 4 predictions, W1/W2, cards C1–C8, agent A1d/A1v; the Unicode bridge: `verus/given/rg_re_a1/src/char_scalar.rs` (`scalar_char` via `vstd::utf8`, `char_prev`, `char_next`; the rejected A1 adapter) and Dafny `CharPrev`/`CharNext` in `R03_AgentApi.dfy` (used by `ClassDiff`); bank K9 ("scalar boundaries"), rubric probe C, chapter §§ on surrogate-gap neighbours |
| R07 | `dafny/R/R07_Libraries/std/R07_Libraries.dfy`, `agent/R07_AgentRetriever.dfy`, `dafny/checks/R07_checks.dfy`, `verus/r/r07_libraries/src/{lib,agent}.rs`, twins in `Solutions/`, `specimens/R07/card-c4dv-v.rs.specimen`, `expected/R07.freeze`, `tests/instructor/leak_patterns/R07.txt`, chapter/bank wording ("inclusive scalar pairs") | H1d/H1v `FilteredSamplePrefix`, H2d/H2v `FilteredAlphabetExact` (statements over `InClass`/the view: unchanged); `ClassLookupFromAPI` (given); A1d/A2d `FlattenClassBatches`, `ContainedClassBatch` (`seq<CharClass>`); A1v/A2v (`Seq<Seq<(char,char)>>`: retyped); the check unit's literal `[CRange('a','c')]` (P1d's subject) |
| R08 | `dafny/R/R08_Abstraction/std/R08_Abstraction.dfy` (`type Pattern = A2.CharClass`), `verus/r/r08_abstraction/src/lib.rs` (`ClassEngine { class: CharClass }`), leak patterns R08.txt | H2d/H2v (class engine). R08 is rebuilt in §2.3 anyway |
| R09 | `dafny/R/R09_Effects/std/R09_Effects.dfy`, `verus/r/r09_effects/src/lib.rs` (tier `all`), twins, `tools/R09/check_frontend.py` (prints raw class vectors), `docs/R09_Effects.md` (below-0xD800 text, captured class vectors), bank R09, `paper/R09_problems.tex`, `tests/instructor/leak_patterns/R09.txt` (lines 9–11, 29–31 quote `ClassInsert(ranges,CRange(c,d))` / `acc.class_insert(c,d)`), `expected/R09.*` | **H2d `ClassItems` / H2v `class_items`** (hole answers change); given helpers `RangeNodesR09`, `ClassNodesR09`, `RangeNodesCorrectR09(lo: char, hi: char)`, `ClassNodesCorrectR09(xs: seq<CRange>)`, `CheckedClassCostR09`, `ClassLowerExecR09`; Verus `class_nodes_r09(Seq<(char,char)>)`, `lemma_class_nodes_r09`, `range_lower_exec_r09`, `class_lower_exec_r09`; **the second Unicode bridge** `scalar_char_r09(n: u32) -> char` (proved against `vstd::utf8`, legal at R09's `all` tier) |
| R10–R14 | none in source; they import A2/A3 transitively | re-gate and re-pin only |
| R15, R16 | not built | design against the new API (§1.4) |

### 1.2 The `u32` design

**Representation and view (both languages).** A range is a pair of `u32` code points `(lo, hi)`, inclusive. Its view is the set of `char`s whose code lies in it; a class's view is the union over its ranges. The only conversion is `char → u32` (Dafny `c as int`, Verus `c as u32`); nothing ever builds a `char` from a number, so no bridge, no neighbour primitive and no `vstd::utf8` import is needed anywhere in R03 or A2. Code points that are not `char`s (the surrogate block `0xD800..=0xDFFF`, everything above `0x10FFFF`) may lie inside a range; they contribute nothing to the view. That is the lesson R03 now teaches with its abstraction square: two different valid representations (`[(0xD7FF, 0xD7FF), (0xE000, 0xE000)]` and `[(0xD7FF, 0xE000)]`) have the same view, so a client can rely only on the view.

**Validity.** `lo <= hi` for every range, and ranges are sorted and **separated**: `rs[i].hi + 1 < rs[j].lo` for `i < j`, computed in `int` in specs (so `hi = u32::MAX` needs no special case in a spec) and as `hi < lo && lo - hi > 1` in exec code (no overflow). Separation makes `ClassInsert` merge adjacent ranges, which the old A2 (`hi < lo'`) did not; the merge needs `hi + 1`, which on `u32` is ordinary guarded arithmetic. No bound at `0x10FFFF` is imposed: imposing one would require the fact `c as u32 <= 0x10FFFF`, which in Verus may sit in `vstd::string`/`utf8` (the draft called `char_is_scalar`), i.e. the tier problem again [probe: whether `vstd` prelude states the `char` range; the design does not need it].

**Dafny.**
```dafny
newtype Cp = x: int | 0 <= x < 0x1_0000_0000      // "u32" (D48); name per avoid.sh, §6 D-A3
datatype CRange = CRange(lo: Cp, hi: Cp)
datatype CharClass = CharClass(ranges: seq<CRange>)   // R03: hidden behind `provides`; A2: see §6 D-A1
function Code(c: char): Cp { c as int as Cp }          // [probe] Dafny proves 0 <= c as int < 2^32
predicate InRange(g: CRange, c: char) { g.lo <= Code(c) <= g.hi }
ghost predicate InClass(cc: CharClass, c: char) { exists i | 0 <= i < |cc.ranges| :: InRange(cc.ranges[i], c) }
predicate ClassValid(cc: CharClass) {
  (forall i | 0 <= i < |cc.ranges| :: cc.ranges[i].lo <= cc.ranges[i].hi) &&
  (forall i, j | 0 <= i < j < |cc.ranges| :: cc.ranges[i].hi as int + 1 < cc.ranges[j].lo as int) }
```

**Verus.**
```rust
pub struct CharClass { ranges: Vec<(u32, u32)> }
pub open spec fn in_range(g: (u32, u32), c: char) -> bool { g.0 <= (c as u32) && (c as u32) <= g.1 }
spec fn in_ranges(rs: Seq<(u32, u32)>, c: char) -> bool { exists|i: int| 0 <= i < rs.len() && in_range(#[trigger] rs[i], c) }
spec fn separated(rs: Seq<(u32, u32)>) -> bool {
    &&& forall|i: int| 0 <= i < rs.len() ==> (#[trigger] rs[i]).0 <= rs[i].1
    &&& forall|i: int, j: int| 0 <= i < j < rs.len() ==> (#[trigger] rs[i]).1 + 1 < (#[trigger] rs[j]).0 }
impl View for CharClass { type V = ISet<char>; closed spec fn view(&self) -> ISet<char> { ISet::new(|c: char| in_ranges(self.ranges@, c)) } }
```
The view type stays `ISet<char>`, so every client that reads only the view (R07's H1v/H2v, R08's class engine, `card-c4dv`) is unchanged. `c as u32` in exec code is prelude-legal (R09's `range_lower_exec_r09` already does `lo as u32`) [probe: A2 stays at the `prelude` tier after the change; `scripts/check_course_map.py` tier group].

**The A2 class API, before and after.**

| declaration | before (A2 today) | after (R03's API, re-supplied by A2 from R07) |
|---|---|---|
| range | D `CRange(lo: char, hi: char)` · V `(char, char)` | D `CRange(lo: Cp, hi: Cp)` · V `(u32, u32)` |
| class | D `type CharClass = seq<CRange>` (transparent) · V private `Vec<(char,char)>` | D `datatype CharClass(ranges)`, hidden or open per §6 D-A1 · V private `Vec<(u32,u32)>` |
| membership spec | `g.lo <= c <= g.hi` | `g.lo <= Code(c) <= g.hi` · `g.0 <= c as u32 <= g.1` |
| validity | sorted, `hi < lo'` | sorted, separated `hi + 1 < lo'`, `lo <= hi` |
| `ClassEmpty` / `class_empty` | unchanged | unchanged |
| `ClassInsert(cc, g)` / `class_insert(&self, lo, hi)` | D `requires ClassValid(cc) && g.lo <= g.hi`; V `lo: char, hi: char`, empty range is a copy | D `requires ClassValid(cc)` only (an empty range is a no-op: total in the range); V `lo: u32, hi: u32`; merges overlapping **and adjacent** ranges |
| `ClassMember` / `class_member` | unchanged signature | unchanged signature (body compares `Code(c)` / `c as u32`) |
| `ClassUnion` / `class_union` | unchanged | unchanged |
| `MinC`/`MaxC` | over `char` | over `Cp` (D only) |
| `ClassRange(lo: char, hi: char)` / `class_range` | absent | added (R03.H2's answer; total; `InClass(r, c) <==> lo <= c <= hi`) |
| `ClassOfString` / `class_of_string` | absent | added (R03.H5's answer) |
| representation accessor | none (A3 copied the code instead) | D `function ClassRanges(cc): seq<CRange>` + `lemma InClassRanges(cc, c)` stating `InClass` through the listing; V `pub fn ranges(&self) -> (r: &Vec<(u32, u32)>) ensures r@ == self.ranges_spec()`, `pub closed spec fn ranges_spec(&self)`, `pub proof fn lemma_view_ranges(&self) ensures self@ == …, self.valid() == separated(self.ranges_spec())` (read-only listing for A3's lowering and size accounting; §6 D-A1) |
| R03 labels in comments | "(R03.H1v)", "(R03.W2v)", "(R03.H3v)" | removed; file header: "Re-supplies R03's API: do not open before `scripts/firsttry.sh R03 --check` and R03's holes are done" |

**A3 after.** Dafny: `ClassLowered(cc) := forall r in ClassRanges(cc) :: r.lo <= r.hi < ClassMax`, `RangeRe(lo: Cp, hi: Cp) requires lo <= hi < ClassMax` builds `Chr(lo as int as char)` (legal because `lo < 0xD800`), `ClassToRe` over `ClassRanges`. Verus: `SpanClass` is deleted and `SyntaxKind::Class(CharClass)` uses A2's class through the accessor (§6 D-A1 option (a)); `range_valid(lo: u32, hi: u32) := lo <= hi < CLASS_MAX`; `range_re` steps `lo + 1` on `u32` and builds `Re::Chr(lo as char)` in spec mode only (as today). The lowering domain stays below `0xD800` (§6 D-A2), so R09's learner-visible semantics do not change. The one remaining `u32 → char` conversion in exec code is R09's lowering (`class_lower_exec_r09`), which keeps its given, proved `scalar_char_r09` at R09's `all` tier: the bridge is no longer on any path before R07, which was the R03 blocker (Δ251).

### 1.3 What R03's items become

| item | before (draft) | after (`u32`) | proof-work change |
|---|---|---|---|
| W1d/W1v mini-API | `SpanBox(lo: char, hi: char)` | unchanged (a span of chars; it never crosses to codes) | none |
| W2d/W2v `ClassInsert` (worked) | merge overlaps; `MinC`/`MaxC` on chars | merge overlaps and adjacency; guarded `hi + 1`; `Cp`/`u32` | given; the adjacency case adds one branch and one `cover` step |
| H1 `ClassMember` / `member_from` | recursion over ranges | same, comparing `Code(c)` | unchanged |
| H2 `ClassRange(lo, hi)` (total, no `requires`) | `if lo <= hi then [CRange(lo, hi)] else []` | same with `Code(lo), Code(hi)`; the `InClass` equivalence needs "`Code` is monotone and injective" [probe: both solvers know it natively; else one given lemma `CodeOrder(c, d)` in R03's file] | one more fact (the char order is the code order) |
| H3 `ClassUnion` over `ClassInsert` | — | unchanged | unchanged |
| H4 client `Union3` | — | unchanged | unchanged |
| H5 `ClassOfString(s)` | inserts `CRange(c, c)` | inserts `CRange(Code(c), Code(c))`; membership needs injectivity of `Code` | as H2 |
| P1d/P2v (strengthened `requires`) | call [b] `ClassInsert(ClassEmpty(), CRange('a','f'))` | `CRange(Code('a'), Code('f'))` | wording of the specimen; the answer (which labels fail) is unchanged |
| P3dv/P4dv (`provides` vs `reveals`) | `ClassSingle(c)` | unchanged | none |
| C8dv divergence | names/contracts/bodies/fields across boundaries | unchanged | none |
| A1d/A1v agent `ClassIntersect`, `ClassDiff` | needed `CharPrev`/`CharNext` (surrogate skip, UTF-8 bridge) | `ClassDiff` splits `[lo, a - 1]`, `[b + 1, hi]` in `u32` under the guards `lo < a`, `b < hi`; no primitive | the adversarial review's boundary probes become `0`, `u32::MAX`, adjacency and "a range that spans the surrogate block" |
| bank K9, rubric probe C | "scalar boundaries and the surrogate gap" | "`u32` boundaries; why a range over the surrogate block is valid and harmless" | rewrite |
| whisper "`char` ranges (→ R09's encoding divergences)" | — | "codes vs chars (→ R09: the lowering, the only place a code becomes a `char`)" | wording |

R03's minutes (300), hole count (10), prediction count (4) and §6.3's item table stand; the draft README's unfinished checks (pins, leak patterns, admission, seeds, study workflow, focused CI) remain to do in §5 step 8.

### 1.4 Impact per module R03–R16

| module | impact | effort |
|---|---|---|
| R03 | rebuild the draft on §1.2–1.3; delete `char_scalar.rs` and `CharPrev`/`CharNext`; regenerate every capture, pin, leak pattern; R03's API reference is the source A2 re-supplies | 2 sessions core + kit (step 8) |
| R04–R06 | none in source. R06 must pass its repaired admission (P5v rewrite, §2.1) before A2's Deriv half loses "provisional" (D48) | — |
| R07 | check unit literal → `ClassRange('a','c')` (A2 re-supplies it) or `ClassInsert(ClassEmpty(), CRange(Code('a'), Code('c')))`; P1d's value is unchanged but its capture and pin refresh; A1v/A2v `Seq<Seq<(char,char)>>` → `Seq<Seq<(u32,u32)>>` (or the views); re-prove H1/H2 references only if they unfold `InRange`; chapter/bank wording; R07 admission rerun (10 rows); `expected/R07.*` | 0.5 session |
| R08 | the current class engine changes trivially, but R08 is rebuilt (§2.3) directly on the new API | in §2.3 |
| R09 | H2d/H2v answers change (`CRange(Code(c), Code(d))`, `acc.class_insert(c as u32, d as u32)`; the `c <= d` check stays on chars); retype the given size/lowering helpers; keep `scalar_char_r09`; `tools/R09/check_frontend.py` prints code pairs, so its 297 frontend and 12 port observations, the chapter's captures and the `sidecars` are re-captured; leak patterns R09.txt regenerated; R09 admission rerun (12 rows) | 1 session |
| R10–R14 | re-gate every unit (the A2/A3 file hashes change), `pins.py --check`, chapter capture diff; no edits expected | 0.5 session (CI time) |
| R15 | Lab β cards over classes use the `u32` API; the escalation ladder's differential oracle (Rust `regex`) compares on `char` strings, unaffected | design only |
| R16 | `rexc`'s class syntax goes through A3; Lab γ's crate tasks "over character classes" are written against the `u32` API; `trust-report` unaffected | design only |
| Lab α | clusters stripped from R07/R09 references are cut from the `u32` references (§3.5) | in §3 |

### 1.5 Re-verification needed

1. **Layers:** A2 and A3 in both languages: `scripts/vcheck --gate`, `scripts/vaudit`, three seeds at the pins; the tier check (A2 Verus still `prelude`, A3 Verus still `prelude`); `scripts/avoid.sh` (new keys `Cp`, `Code`, `ClassRanges`, `ranges_spec`, `separated`); course map and generated units (`scripts/gen_units.py` unit list unchanged).
2. **R03:** full admission of all 10 holes (the four results, §0 of PLAN: reference 3 seeds, `--empty-body`, maximal automation, TRIV for exec items H1, H2, H3, H4, H5), the agent pair (two statements, specfreeze, `vaudit`), five WRITE/recognise cards, four predictions with native referees, study workflow, focused CI (six jobs).
3. **R07, R09:** canonical admission reruns (10 and 12 rows), three seeds on every reference target, the R09 compiled-frontend and port harnesses on the final learner paths, P1d (R07) re-captured.
4. **R07–R14:** every unit gated, `scripts/pins.py --check` 0 problems, every chapter capture re-run and diffed (any byte change re-pinned and re-read), the protected source-leak verifier, `tests/instructor/leak_patterns/*` Rule 1/Rule 2 replay.
5. **One accumulated CI run** over R01–R14 plus layers (§5 step 6), not per-module focused jobs.

---

## 2. Objective-to-exercise map, R01–R16

"Objectives" are PLAN §3's approved record (Why, Core payload, Exercises). "Built" counts hand items in the learner files (`// item:` markers) and `[module.admissible]` minutes. Verdicts: **keep** (items meet the record; only the systemic passes of §4 apply), **revise** (items mostly meet it; named items change), **rebuild** (items replaced).

| module | §3 exercises (approved) | built (hand items; admitted H/T/X minutes) | gap | verdict |
|---|---|---|---|---|
| R01 | `Midpoint` without overflow; a naive mean's precondition; a first recursive lemma over strings; the hole census (test-out); a triage drill | T1d/v census, H1 `Midpoint`, H2 lemma, H3 `MeanOfTwo`; A1 repairer (plan 24 + 10) | registry rows missing (`admissible = {}` although notes record 8/8); Draw A has no live predict; 1+1 source blocks | **keep** + rows + Draw A swap (K2 ↔ K3) |
| R02 | `NullableCorrect`; `NodeCount`/`Backwards`; `Nullable` of a reversed regex; `Cat(Eps, r)`; `IsVoid` | H1–H5 d/v exactly these; T1 `ChrCount`; A1 implementer (plan 60 + 10) | rows missing; chapter has **no** code block; `choose` untaught but needed by H4v; holes lack prompts/hints/checks and precede the cards that teach them; A1b holds H1/H4 answers without a header | **revise** (pedagogy only; the exemplar, §4) |
| R03 | `ClassMember`, total `ClassRange`, `ClassUnion` over `ClassInsert`, API-only client, class from a string | parked draft, all items | the Unicode bridge (Δ251) | **rebuild on `u32`** (§1) |
| R04 | witness proofs (positive, negative, anchoring); prose-to-spec with use-site checks; mutant-kill witness | H1 `WitnessAbb`, H2 `WitnessNotBa`, H3 `WitnessAnchored`, H4 `PrefixMatch`, H5 `MutantKilled`, T1 (plan 70 + 10) | **no admissible rows**; 1+1 source blocks | **keep** + rows |
| R05 | `Cat` associativity both ways; `StarOne`; bisect-and-repair; variance log + 2 Python holes | H1–H4 d/v (`CatAssocLR/RL`, `StarOne`, `StarConcat`), H1py/H2py; 96 min (plan 72 + py 24) | systemic only | **keep** |
| R06 | `DerivCorrect` flagship; matcher invariant; refute → repair → prove on `Star`; checkpoint 2 D + 2 V | H1 flagship, H2 `DerivMatch`, H3 refuted, H4 `StarUnfold`, X1/X2 d/v, T1; 218 min | P5v near-leak of H2v; no source blocks | **keep** + rewrite P5v (a loop over `NodeCount` with a different invariant shape, re-captured) |
| R07 | library-backed rewrites of band-1 sequence/char-set facts over A2's class API; trust audit; pass@k by hand | H1–H3 d (8/11/12), H1–H5 v (6/7/8/5/5), T1; 72 min | small holes; `u32` port (§1.4) | **revise** (port; check each hole's reference size against its band) |
| R08 | the derivative matcher as a `Matcher` refinement; a second refinement over A2's class API; opacity repairs; semantic refinement failure; what a refinement may change | four ≈ 10-line holes (90 min claimed) | objective missing from the hand items (only the agent plant is semantic) | **rebuild** (§2.3) |
| R09 | parser holes over A3's spec (bounds, budget, positions); `Rep`'s lowering and correctness; port + fidelity audit | T1, H1 `Counted`, H2 `ClassItems`, H3 budget, H4 `RepRangeCorrect`, H5 cursor; 120 min | outputs in an appendix; < 5,000 words; R04 lines (reported); `u32` port of H2 | **revise** |
| R10 | `NormRe` invariants; learner-written language-preservation statements; erasure items | H1/H2 packets (subset type, `by method`), H3 `NormalFixedR10`, H4 `NormalizePacketR10`; flagship statements in the agent file; 110 min | appendix outputs; packed twins | **keep** + systemic |
| R11 | `Derivation`, `CheckDeriv` and soundness; the loop's VCs; the arena (V, gated; Vec fallback); checkpoint | 22 rows, 252 min, Vec arena fallback admitted (Δ267) | appendix outputs | **keep** + systemic |
| R12 | hint-site holes in the exercise files (obligations for the loop); extractor and loop Python holes; profiler; Lab α's environment and engine | T1/H1/H2 d/v are flag loops; H1py–H5py (40/40/20/90/60) match the extractor/loop/engine/environment lines | native holes are not hint-site regex forms; Lab α corpus and statistics (§3) | **revise** native holes (§2.4) + Lab α (§3) |
| R13 | stage-attribution items; forensic deliveries diagnosed by ≥ 2 instruments; `TRUST.md` R-v0 | T1 `ClampIndexR13`, H1 `SaturatingSumR13`, H2 `RangeFitsR13`, H3 `PairWitnessR13` (off-topic arithmetic); forensics/stage parts built | holes have no regex or trust content | **rebuild holes** (§2.5); keep forensics |
| R14 | triggers on split existentials (R14's own variants), matching loops over concatenation, fuel on `Matches`, nonlinear/bit-vector where repetition needs it, isolation; 12-assertion battery; `trigscan` | `PrefixCapR14`, `OddSquareR14`, `ClearLowBitR14`; battery over `PrefixMassR14`; no chapter/bank | off-plan; incomplete | **rebuild** (§2.6) |
| R15 | the ladder on `rexc`'s matcher; statement-review items; `spectest`, `roundtrip`; Lab β | — | not started | **build** (§2.7) |
| R16 | frozen statements + statement-only review; emitter soundness/completeness (2 per language); jump threading (gated); the plant; `rexc`; trust-report; Lab γ | — | not started; A5 not reconciled | **build** (§2.8) |

### 2.1 Common admission evidence for every new or changed hole

For each hole the build step records, in the module's author notes and in one `[module.admissible]` row: (1) the reference verifies on seeds 1–3 at the pins (`--resource-limit 5000000` / `--rlimit 2` unless the record names another pinned value); (2) `scripts/firsttry.sh <ID> --empty-body` fails in the shipped configuration (Dafny R03–R16: `manual-lemma-induction = true`); (3) the empty body also fails under maximal automation (Dafny default induction plus every lever the module allows; Verus `E0`/`E0H`/`E1`), or the shipped lever is named in the row; (4) for exec items, a trivial body (`false`, `0`, `[]`, the first input) fails (TRIV). An item without all four carries 0 minutes. "Why not trivial" below is the design argument; the four results are what admits it.

### 2.2 Line budget (all rebuilt items)

Each new hole states its expected reference size in proof lines (PLAN §0's counter). The design targets are 5–15 proof lines for a 10-minute hole and 15–30 for a 15–20-minute hole; a reference under 3 lines is redesigned, not admitted at its minutes.

### 2.3 R08 rebuild — interfaces whose obligations are semantic

**Given (F6, replaces `RG_A2_MatcherStatement.dfy` and `word_matcher.rs`).** An abstract step-matcher whose run loop is verified once in the interface, against obligations each engine must discharge:
```dafny
abstract module RG_A2_StepMatcher {
  type Pattern
  type State
  ghost predicate Lang(p: Pattern, w: seq<char>)       // the engine's frozen semantic binding
  ghost predicate Res(st: State, w: seq<char>)         // what a state still accepts
  function Start(p: Pattern): State
  function Step(st: State, c: char): State
  predicate Final(st: State)
  lemma StartLaw(p: Pattern, w: seq<char>) ensures Res(Start(p), w) <==> Lang(p, w)
  lemma StepLaw(st: State, c: char, w: seq<char>) ensures Res(Step(st, c), w) <==> Res(st, [c] + w)
  lemma FinalLaw(st: State) ensures Final(st) <==> Res(st, [])
  method Run(p: Pattern, w: seq<char>) returns (b: bool) ensures b == Lang(p, w)
  { /* given: the loop, invariant Res(st, w[i..]) <==> Lang(p, w), using the three laws */ }
}
```
Verus: a trait `StepMatcher` with associated `Pattern`/`State` types, spec fns `lang`/`res`/`step_spec`/`final_spec`, exec `step`/`is_final` with `ensures r == step_spec(..)`, proof fns `lemma_start/step/final_law`, and a given generic `fn run<M: StepMatcher>(m: &M, …) -> (b: bool) ensures b == m.lang(..)` [probe: associated types and proof fns in traits on the pinned Verus; fallback: one trait per engine with concrete types, and `run` instantiated per engine]. The given derivative engine (Pattern = State = `Re`, `Step = Deriv`, `Final = Nullable`, laws = one call each to A2/A1b) is the **worked** example W1 (it is too easy to be a hole: that was the old H1).

| item | statement shape | proof work | why not trivial | min (D/V) | admission shows |
|---|---|---|---|---|---|
| **H1d/H1v** alternative-set engine: `PartsLaw` | `function Parts(r: Re): seq<Re>` (given: splits top-level `Alt`, drops `Empty`); `lemma PartsLaw(r, w) ensures (exists i \| 0 <= i < \|Parts(r)\| :: Matches(Parts(r)[i], w)) <==> Matches(r, w)` | structural induction on `r`; in the `Alt` case, moving an index across `Parts(a) + Parts(b)` in both directions; `Empty` case | existential over a concatenated sequence's indices; manual induction on; the solver cannot shift indices across `+` without the learner's witnesses | 15 / 15 | empty fails (shipped and default induction: the index shift is not inferable) [probe]; reference 8–12 lines |
| **H2d/H2v** alternative-set engine: `StepLaw` | State = `seq<Re>`; `Res(st, w) = exists i :: Matches(st[i], w)`; given `Step(st, c) = if st == [] then [] else Parts(Deriv(st[0], c)) + Step(st[1..], c)`; prove the interface's `StepLaw` | induction on `\|st\|`; each element via `PartsLaw` + `DerivCorrect` (A2); existential split over `head + tail` | composes two existentials and a recursive flatten; the interface obligation, not a lemma the learner chose | 15 / 15 | empty fails; reference 10–14 lines |
| **H3d/H3v** class-word engine over A2's class API: `StepLaw` | Pattern = `seq<CharClass>`, `Lang(p, w) = \|w\| == \|p\| && forall i :: InClass(p[i], w[i])`; State = `(alive: bool, rest: seq<CharClass>)`; given `Step` (consume one class via `ClassMember`, else dead); prove `StepLaw` | case split alive/dead/empty; index shift `([c] + w)[i + 1] == w[i]` inside a `forall` (Verus: `assert forall … by` with the right trigger) | quantifier shifting; the dead-state case must be argued, not assumed | 10 / 10 | empty fails in both; reference 6–10 lines |
| **H4d/H4v** opacity repair: `FinalLaw` with an opaque `Res` | the alternative-set engine's `Res` is shipped `opaque` (Verus `#[verifier::opaque]`) to keep `exists`-over-`Matches` out of every context; `Final(st)` = given recursive `AnyNullable(st)`; prove `FinalLaw` | `reveal Res` in exactly this lemma, induction on `\|st\|`, `NullableCorrect` per element | the reveal must be scoped (revealing at module level re-breaks H2's stability, which the chapter shows as a captured `inconclusive`) [probe]; still an induction | 5 / 5 | empty fails; maximal automation still needs the reveal; reference 5–7 lines |

Refinement directions (weaken `requires`, strengthen `ensures`) are taught by the C4dv card and the refinement lab (30 min): the given interface has `requires Valid(p)` on `Run`, the class-word engine defines `Valid` as `true`, the alternative-set engine strengthens `Run`'s `ensures` with a size bound. **Agent (rung 5):** a third engine (deduplicating alternatives by syntactic equality, which also drops `Eps` parts as if they were `Empty`) reaches verification with zero holes and fails `StepLaw` at a real postcondition; the faithful repair changes only the engine; a delivery that edits `Lang` verifies a different task and fails `scripts/specfreeze --against`. Minutes: holes 90 (45 per language), record total 354 unchanged. Chapter diagrams: the refinement square, the direction of obligations, the step-matcher's loop with the three laws as its invariant's pieces.

### 2.4 R12 native holes — hint-site forms over regex lemmas

The native holes become the same kind of object Lab α automates, so the learner fills by hand what the engine fills by search. Each ships the proof skeleton with `R12_HINT_SITES` markers; the learner supplies only expressions or proof calls at the sites (the existing frame checker, `tools/R12/admit_forms.py`, enforces it). None of these lemmas enters Lab α's corpus.

| item | form | statement shape | sites (what the learner must read from the obligation) | why not trivial | min |
|---|---|---|---|---|---|
| T1d/T1v | one site | `lemma CatWitnessR12(a, b, u, v) requires Matches(a, u) && Matches(b, v) ensures Matches(Cat(a, b), u + v)` | the split fact `(u + v)[..\|u\|] == u && (u + v)[\|u\|..] == v` | the obligation names the failing existential; the learner must name the witness | 5 |
| H1d/H1v | two sites | `lemma CopiesAppendR12(r, n, m, u, v) requires Matches(Copies(r, n), u) && Matches(Copies(r, m), v) ensures Matches(Copies(r, n + m), u + v)` (A3's `Copies`), skeleton: induction on `n` | (1) the head/tail split of `u` obtained from the `Cat` existential; (2) the recursive call's arguments | two dependent sites; a wrong IH argument verifies nothing | 10 |
| H2d/H2v | two sites | `lemma UpToMonoR12(r, j, k, w) requires j <= k && Matches(CopiesUpTo(r, j), w) ensures Matches(CopiesUpTo(r, k), w)` | (1) the `Alt` branch fact; (2) the IH call with `j - 1, k - 1` and the split | branch choice must be read from which disjunct the obligation reports | 10 |

Minutes unchanged (T1 10, H 40). The Python holes H1py–H5py stay (they match the record's extractor/loop/engine/environment lines); their acceptance tests gain the new resource-accounting fields (§3.8).

### 2.5 R13 holes — fake greens on `rexc` objects, repaired honestly

Each hole is a delivery that "passes" for a stage- or trust-related reason; the learner attributes it (stage, instrument) and then supplies the honest proof. The stage-attribution and forensics lines (30 + 60 min) are unchanged.

| item | the fake green | the honest task (statement shape) | proof work | why not trivial | min |
|---|---|---|---|---|---|
| T1d/T1v | Dafny: a compiled method calls the ghost `Matches` (fails at **resolve**, but a `--symbol` run on another symbol was green); Verus: an exec fn calls spec `matches` (mode error) | `method AcceptsR13(r, s) returns (b: bool) ensures b == Matches(r, s)` | call A2's `DerivMatch` / `matches_vec` | test-out: attribution is the point; TRIV `false` fails | 5 |
| H1d/H1v | a trusted axiom: `lemma {:axiom} DerivsCatR13(r, u, v)` / an `external_body` proof fn, listed by `vaudit`, ignored by a naive grader | prove `Derivs(r, u + v) == Derivs(Derivs(r, u), v)` (`Derivs` = iterated `Deriv`, given) | induction on `\|u\|`, sequence re-association `[u[0]] + (u[1..] + v) == u + v` | manual induction; the re-association is not found unaided | 10 |
| H2d/H2v | a trusted exec helper: `#[verifier::external_body] fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool) ensures b == forall\|i\| … cc@.contains(s@[i])` (Dafny `{:extern}`-shaped `{:axiom}` method) | the verified loop over A2's `u32` class API | loop invariant over a prefix `forall`; early exit | TRIV fails; the invariant must quantify over the prefix | 10 |
| H3d/H3v | a weakened statement: the delivery proves `Nullable(Derivs(r, u)) ==> Matches(r, u)` where the frozen statement is `<==>`; `specfreeze` flags it, the gate does not | `lemma NullableDerivsR13(r, u) ensures Nullable(Derivs(r, u)) <==> Matches(r, u)` | induction on `\|u\|` with `DerivCorrect` and `NullableCorrect`; both directions | the missing direction needs the same induction run backwards | 10 |

### 2.6 R14 rebuild — triggers, fuel and nonlinear facts on R14's own `Matches` variants

R14 defines `MatchesV` (its own copy of A1's semantics) with deliberately chosen triggers, so no item asks which trigger A1 needs (F5).

| item | statement shape | proof work | why not trivial | min (D/V) |
|---|---|---|---|---|
| **H1d/H1v** trigger on a split existential | `MatchesV`'s `Cat` case is `exists i {:trigger MatchesV(a, s[..i])} :: …` (Verus `#[trigger] matches_v(*a, s.subrange(0, i))`, the trigger shape the spike showed blocks unfolding); prove `lemma CatIntroV(a, b, u, v) requires MatchesV(a, u) && MatchesV(b, v) ensures MatchesV(Cat(a, b), u + v)` | make the trigger term appear: `assert (u + v)[..\|u\|] == u;` then mention `MatchesV(a, (u + v)[..\|u\|])` | the needed instantiation term is absent from the goal; adding facts without the trigger term does not help | 10 / 10 |
| **H2d/H2v** fuel vs induction on an honestly recursive definition | `lemma StarPowV(c, n) ensures MatchesV(Star(Chr(c)), Pow(c, n))` (`Pow(c, n)`: `n` copies, given recursive) | induction on `n`, witness `i = 1`, one unfolding of `Pow` and of `MatchesV`'s `Star` case; the WRITE card shows the concrete `n = 3` instance closed by `{:fuel MatchesV, 4}` / `reveal_with_fuel(matches_v, 4)` and fails at fuel 3 | the general fact is not reachable by fuel; the concrete one is, which is the lesson | 10 / 10 |
| **H3d/H3v** nonlinear: the derivative size bound | `lemma DerivSizeV(r, c) ensures NodeCount(Deriv(r, c)) <= 2 * NodeCount(r) * NodeCount(r)` (A1's `NodeCount`, A2's `Deriv`) | structural induction, six cases; in `Cat`/`Alt`/`Star` a product inequality from the IH (`2a² + b + 2b² + 2 <= 2(1 + a + b)²`); Dafny: assert the expanded square; Verus: `by (nonlinear_arith) requires …` | induction plus nonlinear steps; neither automation does both [probe: default induction fails on the nonlinear step] | 15 / 15 |

**Battery (60).** Twelve assertions, 6 D / 6 V, on `MatchesV` and `u32` code points: two split-trigger witnesses, two matching-loop `forall`s over `Cat(r, Star(r))` (one loops, one is repaired by a trigger choice), two fuel instances, two nonlinear size facts, two bit-vector facts on code points (`(c as u32) & 0xFFFFF800 == 0xD800` iff surrogate-range code, with `by (bit_vector)` / `bv32`), two isolation items (`@IsolateAssertions` / `#[verifier::spinoff_prover]`). **`trigscan` (30)** analyses the wrapper's `--triggers-mode verbose` notes and source spans; with `--log smt` refused, a matching loop is reported as a symbolic potential cycle, never as observed instantiations (§6 D-R14). **CV sweeps (40)**: seeds 1–10 on the battery and H items through `fvh.stats`.

### 2.7 R15 designs (from §3's record)

| item | statement / task | work | min |
|---|---|---|---|
| ladder H1d/H1v (proof rung) | `method ContainsMatchR15(r, s) returns (b: bool) ensures b == exists i, j \| 0 <= i <= j <= \|s\| :: Matches(r, s[i..j])` (unanchored search, the R-owned anchoring theme) | nested loops restarting the derivative at each `i`; invariants over `i` and `j` with `DerivCorrect` | 20 / 20 |
| ladder H2v (property rung) | a deterministic generator test (outside `verus!`) comparing `ContainsMatchR15`'s compiled form with the Rust `regex` crate on anchored `^(?:…)$` and unanchored patterns [verify: dev-dependency allowed by the gate] | the learner writes the oracle wrapper and the anchoring translation | 15 |
| H1py `spectest.soundness`, H2py `spectest.completeness`, H3py `roundtrip` | as PLAN §4.3 (Lab β) | — | 35 / 40 / 65 |
| statement review (30) | six frozen candidate statements for `ContainsMatchR15` (faithful, weak, vacuous, over-strong, anchoring error, empty-string error) classified with witnesses | written, rubric-graded | — |

### 2.8 R16 designs (from §3's record; A5 reconciliation first)

| item | statement shape | work | min |
|---|---|---|---|
| statements (40) | the learner writes `EmitComplete`/`EmitSound` generalized over the continuation: `CodeAt(p, pc, Emit(r, pc)) && Matches(r, u) && AcceptsFrom(p, pc + \|Emit(r, pc)\|, v) ==> AcceptsFrom(p, pc, u + v)`, and its converse with an existential split | frozen after a statement-only review | — |
| H1d/H1v completeness | the frozen `EmitComplete` | induction on `r`; `Star` by inner induction on chunks (non-empty first chunk); A5's layout and one-step lemmas given | 45 / 45 |
| H2d/H2v soundness | the frozen `EmitSound` | induction on fuel with the continuation; `Split` nondeterminism by cases | 45 / 45 |
| H3 jump threading (gated, 70) | `Thread(p)` replaces `IJmp(a)` whose target is `IJmp(b)`; `AcceptsFrom(Thread(p), pc, s) <==> AcceptsFrom(p, pc, s)` | a DVR spike first; fallback: one-hop threading on acyclic chains with its own four results; 0 minutes until then | 70 |

---

## 3. Lab α redesign (D49)

### 3.1 Question and estimand

**Primary question (pre-registered, fixed by the course).** For best-first search at equal node budget, does obligation-localized feedback raise the area under the success-vs-budget curve compared with raw verifier text?

**Estimand.** θ = mean over confirmatory clusters c of `AUC_obl(c) − AUC_raw(c)`, where for one arm `AUC(c) = (1/B) Σ_{b=1..B} S_c(b)`, `S_c(b)` is the fraction of the cluster's runs (tasks × repeats) whose first verified-and-re-judged success came within `b` node calls, and `B = 10`. Per run this equals `max(0, B − T + 1)/B` for a first success at call `T` (0 if none), so `AUC ∈ [0, 1]` and reads as "budget-weighted success". Clusters are weighted equally.

### 3.2 Primary test

Two-sided paired sign-flip permutation test on the cluster differences `d_c` (`fvh.stats.permutation_test(x, y, paired=True, n_permutations=10_000, seed=…)` composes it), α = 0.05, **one** test (no Holm over budget points). The interval is a cluster bootstrap (percentile, 10,000 resamples of clusters) of the mean `d_c`. The claim is scoped: "on these tasks, with this model, these prompts and B = 10", a small-scale replication with model substitution.

### 3.3 Analysis plan (all frozen before the confirmatory run)

- **Budget axis:** node calls, B = 10, read as prefixes of each run (each regime's (width, depth, priority) is budget-independent, as now).
- **Aggregation:** run → cluster-arm AUC (mean over its tasks × repeats) → cluster difference → mean over clusters.
- **Secondary, descriptive only:** the full `S(b)` curves of all four regimes (independent, repair, best-first × {obligation, raw}) with clustered bootstrap bands; crossing points read off the bands, never tested; by-language and by-source (regex vs public) strata; the Claude arm's ten runs.
- **Missing results:** a policy-attributable failure (malformed action, refused edit, a model-call timeout) is a failed node that consumes budget. An apparatus failure (verifier OOM, container error) is re-run once with the same seed; if it persists the run is excluded, the cluster-arm AUC uses the remaining runs, and a cluster with no run left in either primary arm leaves the primary contrast. Reported counts per arm; sensitivity: worst case for the claim (excluded runs scored 0 in the obligation arm and 1 in the raw arm).
- **Resource accounting comparable across formats:** identical `num_ctx`, `num_predict`, temperature, thinking setting and seeds list per arm; the feedback text is capped at the same token budget in both formats (raw text truncated head + tail with a marker; obligation feedback rarely reaches the cap), the truncation rate per arm is reported; tokens in/out, GPU-seconds and wall clock are logged per call; sensitivity: AUC on a cumulative-prompt-token axis with the same ten quantile budget points for both arms.
- **Re-judging:** every success is re-judged in the verification container by `vcheck --gate` (three seeds), `vaudit` and `specfreeze` against the frozen form, as now.
- **Stopping rule:** fixed N; no interim look at the primary contrast; the pilot (§3.6) is excluded from the confirmatory sample.

### 3.4 Power simulation

**Method.** Monte-Carlo over a generative model of one run: the per-call success probability is `p = logistic(b0 + β·arm + u_c + arm·(τ·z_c + η_t) + w_t)`, the first-success call is geometric in `p`, and the run's AUC follows. `u_c ~ N(0, σ_u²)` is the cluster effect, `w_t ~ N(0, 0.5²)` the task-within-cluster effect shared by both arms (the arms run on the same tasks), `τ·z_c` the cluster-level heterogeneity of the effect, and `η_t ~ N(0, 0.5²)` a task-by-arm interaction. ICC is on the latent scale, `σ_u² / (σ_u² + 0.5² + π²/3)`. `b0` is calibrated by bisection so the raw arm's mean AUC is 0.35 or 0.60. Each regex cluster has 2 tasks (D, V) and each public cluster 1; repeats r per arm. For each cell: 1,000 simulated datasets, exact two-sided paired t-test on cluster differences at α = 0.05; the true δ (population mean AUC difference) for each β by 30–40k draws; MDE = the δ at 80 % power by linear interpolation in β. Checks: the sign-flip test and the t-test agree (power 0.940 vs 0.947 at K = 60, 0.70 vs 0.70 at K = 20, 300 datasets); null calibration (β = τ = η = 0): type-I error 0.051 (K = 20) and 0.055 (K = 60) over 2,000 datasets.

**Code.** `~/.cache/dafny-verus-learn-0/author-probes/dvr4-plan/power_sim.py` (grid), `designs.py` (candidate designs), `checks.py` (validation); results `power_results.json`, `design_results.json`; standard library only, seed 20261017, run under `systemd-run --user --scope -p MemoryMax=4G`. Step 3 (§5) commits a cleaned copy as `Solutions/plans/labalpha_power_sim.py` and ports the MDE routine into `fvh.stats` (§3.8).

**Results: MDE in AUC points at 80 % power (m = 2 tasks per cluster, r = 3 repeats, α = 0.05).**

| raw-arm AUC | ICC | τ | K = 20 | 40 | 60 | 80 | 100 | 120 |
|---|---|---|---|---|---|---|---|---|
| 0.35 | 0.05 | 0 | 0.144 | 0.102 | 0.083 | 0.070 | 0.063 | 0.058 |
| 0.35 | 0.05 | 0.5 | 0.161 | 0.108 | 0.089 | 0.077 | 0.070 | 0.063 |
| 0.35 | 0.05 | 1.0 | 0.192 | 0.130 | 0.107 | 0.094 | 0.083 | 0.077 |
| 0.35 | 0.15 | 0 | 0.138 | 0.094 | 0.078 | 0.066 | 0.060 | 0.055 |
| 0.35 | 0.15 | 0.5 | 0.156 | 0.104 | 0.090 | 0.073 | 0.068 | 0.062 |
| 0.35 | 0.15 | 1.0 | 0.187 | 0.131 | 0.102 | 0.088 | 0.077 | 0.071 |
| 0.35 | 0.30 | 0 | 0.131 | 0.088 | 0.074 | 0.062 | 0.055 | 0.051 |
| 0.35 | 0.30 | 0.5 | 0.144 | 0.097 | 0.080 | 0.069 | 0.060 | 0.057 |
| 0.35 | 0.30 | 1.0 | 0.172 | 0.120 | 0.094 | 0.082 | 0.076 | 0.067 |
| 0.60 | 0.05 | 0 | 0.125 | 0.090 | 0.076 | 0.064 | 0.057 | 0.054 |
| 0.60 | 0.05 | 0.5 | 0.143 | 0.101 | 0.081 | 0.074 | 0.065 | 0.058 |
| 0.60 | 0.05 | 1.0 | 0.166 | 0.121 | 0.100 | 0.087 | 0.079 | 0.072 |
| 0.60 | 0.15 | 0 | 0.122 | 0.086 | 0.073 | 0.062 | 0.055 | 0.051 |
| 0.60 | 0.15 | 0.5 | 0.136 | 0.097 | 0.078 | 0.071 | 0.064 | 0.058 |
| 0.60 | 0.15 | 1.0 | 0.159 | 0.116 | 0.098 | 0.083 | 0.076 | 0.070 |
| 0.60 | 0.30 | 0 | 0.116 | 0.078 | 0.070 | 0.060 | 0.051 | 0.048 |
| 0.60 | 0.30 | 0.5 | 0.128 | 0.092 | 0.074 | 0.067 | 0.062 | 0.056 |
| 0.60 | 0.30 | 1.0 | 0.156 | 0.110 | 0.090 | 0.077 | 0.072 | 0.065 |

**Candidate confirmatory designs (raw AUC 0.35 / 0.60, ICC 0.15).**

| design | clusters | Qwen calls, 2 primary arms | MDE τ = 0.5 | MDE τ = 1.0 |
|---|---|---|---|---|
| A: 40 regex × 2 + 20 public × 1, r = 3 | 60 | 6,000 | 0.097 / 0.088 | 0.113 / 0.105 |
| B: 50 × 2 + 30 × 1, r = 2 | 80 | 5,200 | 0.097 / 0.091 | 0.109 / 0.097 |
| **C: 50 × 2 + 30 × 1, r = 3** | **80** | **7,800** | **0.086 / 0.077** | **0.101 / 0.088** |
| D: 60 × 2 + 40 × 1, r = 2 | 100 | 6,400 | 0.089 / 0.080 | 0.099 / 0.090 |
| E: 60 × 2, r = 3 | 60 | 7,200 | 0.088 / 0.078 | 0.107 / 0.097 |

**Reading.** (1) Because both arms run on the same tasks, the cluster and task main effects cancel: ICC barely moves the MDE; **effect heterogeneity (τ, η) and the number of clusters** drive it. (2) The old design (20 clusters, a test per budget point and comparison at α = 0.05/40) has power 0.065 at δ = 0.10 and 0.42 at δ = 0.18 under this model, i.e. an MDE near 0.25 AUC; the frozen binary formula gives `inf`. (3) Single-task (public) clusters carry less information (K = 60 at m = 1: power 0.73 where m = 2 gives 0.95), and a third repeat buys less than more clusters. **Recommendation:** design C (80 confirmatory clusters, MDE ≈ 0.08–0.10 AUC under τ ≤ 1), with D (100 clusters, two repeats) as the fallback if public admission is plentiful and regex admission falls short; D49's floor of 60 gives ≈ 0.10–0.11 (§6 D-L2).

### 3.5 Corpus

**Cluster rule.** One cluster per source lemma family: a lemma and the helpers it calls form one family; its Dafny and Verus forms are the cluster's two tasks; several hint-site forms of one lemma are tasks of the same cluster, never new clusters. Public tasks are single-task clusters. A cluster enters only when every task passes the seven existing admission checks (`baseline-proof-fails`, `max-auto-empty-fails`, `reference-gate`, `reference-three-seeds`, `wrong-hints-fail`, `audit-clean`, `original-model-code-frame`) and the task's import chain contains no layer that already states the lemma (so a task cannot be answered by one call to a given proof).

**Regex sources (candidates before admission; names from the `Solutions/` references at `932dd47`, plus the rebuilt items).**

| source | candidate families |
|---|---|
| R06 | `BackwardsStrAppend`, `BackwardsStrInvolution`, `BackwardsInvolution`, `BackwardsSound`/`BackwardsCorrect`, `DerivBase`, `DerivCorrect` (imports A1/A1b only), `DerivsAppend`, `StarUnfold` (8) |
| R07 | `ObservedAlphabetBound`, `FilteredSamplePrefix`, `FilteredAlphabetExact`, `SampleBatchBound`, `FlattenClassBatches`, `ContainedClassBatch` (6; cut from the `u32` references) |
| R09 | `CopiesSplit`, `CopiesUpToCorrect`, `RepRangeCorrect`, `LiteralAppendR09`, `RepetitionCostGrowsR09`/`…FormulaR09`, `CopiesNodesR09`, `OptionalNodesR09`, `RangeNodesCorrectR09`/`ClassNodesCorrectR09`, `LoweringNodesCorrectR09` (≈ 9) |
| R10 | `NormalFixedR10`, `NormIdempotentR10`, `ReplaceRightR10`, `StarStar`, `MkAltCorrect`, `MkCatCorrect`, `MkStarCorrect` (≈ 6) |
| R11 | `RenameSplitR11`/`RenameTransportR11`, `CertificateLengthR11`, `UniformStepR11`, `CheckSoundR11`, `DirectCompleteR11`, `ResidualStartR11`/`…StepR11`/`…ObserveR11` (≈ 6) |
| R08 (rebuilt) | `PartsLaw`, alternative-set `StepLaw`, class-word `StepLaw`, `FinalLaw` (4) |
| R13 (rebuilt) | `DerivsCatR13`, `NullableDerivsR13`, `class_covers_r13` (3) |
| R14 (rebuilt) | `CatIntroV`, `StarPowV`, `DerivSizeV`, two battery families (≈ 5) |
| A1b (as tasks importing A1 only) | `NullableCorrect`, `CatEpsLeft`/`CatEpsRight`, `CatAssoc`, `StarOne`, `StarConcat` (≈ 5) |

≈ 52 regex families; at an admission rate of 70–80 % [A] that is 36–42 clusters, so design C's 50 needs either more hint-site-eligible families (helpers promoted to their own family when they are not called by another candidate) or design D's balance. R12's own practice lemmas (§2.4) are excluded. A4's `CatCongRight`, `CatCong`, `StarOfEps` verify with empty bodies and fail admission by construction.

**Learner visibility (§6 D-L3).** Tasks cut from R13 and R14 references would show a learner at R12 the proof skeletons of two later modules' holes (PLAN §2.1 rule 3). They are therefore sealed: they live in `Hidden/labs/R12/` and are unsealed only in the grader/verification container; the learner's transcript audit (20 min) samples only clusters from R06–R11, A1b and the public slice; reports show sealed clusters by id and verdict until the learner's R14 first tries are recorded.

**Public slice.** Drawn from the validated pools in `bench/public/POOLS.toml` (DafnyBench 303 tasks, Apache-2.0 at commit `0cd28fe`; HumanEval-Verus 83, MIT; vericoding 2,264, MIT, with an unlicensed upstream `verified-cogen`), by a pre-registered seeded walk with `scripts/dvl/lab2pub.py`'s checks C0–C7 in order (C0 licence per file: MIT/Apache-2.0 provenance recorded, which excludes `jetbrains/verified_cogen` members; C1 form; C2 prose; C3 distinct problem, no HumanEval id shared across languages or with Q15's draws or R12's prior reservation; C4 form resolves; C5 answer gated under seeds 1–3; C6 reference + witness; C7 faithful), followed by materialization into hint-site forms and the seven admission checks. Preference for lemma-shaped tasks (proof obligations over sequences, strings and recursion). **Contamination checks:** treat every public task as possibly seen (2023–2025 public repositories); a perturbation probe per public cluster (identifier renaming and statement-preserving reordering; the cluster is kept but flagged when the probe changes its baseline success); the by-source stratum is reported; the regex clusters are course-authored after the model's release, the public ones are not.

### 3.6 Pilot protocol

Five clusters (three regex, two public), drawn by a pre-registered seed from the admitted pool and **excluded** from the confirmatory sample; all four regimes, three repeats, B = 10 (8 tasks × 4 arms × 3 × 10 = 960 Qwen calls). It checks: ceilings (share of runs solved at call 1 and never solved, per arm; if either primary arm solves > 60 % of runs at call 1 or < 5 % at call 10, the hint-site granularity or B is revised before freezing); instrumentation (every call logged with tokens, feedback bytes, truncation flag, verifier provenance; re-judging reproduces every success; the report reproduces every table from the logs); and the feedback renderer's equal-cap rule. The pilot may raise K or revise the hint-site forms; it may not lower K below the simulation's choice and never touches the estimand or the test. The freeze then commits: estimand, test, B, aggregation, missing-result rule, resource accounting, K, the cluster list and its seed, and the simulation's sha256 into the pre-registration block.

### 3.7 Budget and GPU hours

At PLAN §4.3's working assumption of 7.3 s per Qwen call (`num_predict` 768) [A], to be replaced by DV4 step 3d's throughput probe:

| part | calls | GPU-h at 7.3 s |
|---|---|---|
| pilot (5 clusters = 8 tasks, 4 arms, r = 3) | 960 | 1.9 |
| confirmatory primary arms, design C | 7,800 | 15.8 |
| descriptive regimes (independent, repair) on a seeded 20-cluster subset (12 × 2 + 8 × 1 tasks, r = 3) | 1,920 | 3.9 |
| **Qwen total** | **10,680** | **≈ 21.7** |
| Claude descriptive arm (10 tasks, unchanged) + ≤ 10 sentinels | ≤ 110 | — |

The registry's R12 row is 4,800 Qwen calls and 10 GPU-h (Δ176); the redesign needs a new ceiling (§6 D-L1). Batched serving (vLLM on the 96 GB card) can cut wall-clock GPU time severalfold at the same call count [probe in step 3d]. Verifier load: one single-seed gate per call (≈ 10–30 s), ≈ 60 CPU-h, ≈ 10 h wall at six Verus workers inside the 48 GiB budget; final three-seed re-judging only for successes.

### 3.8 What changes in the harness and the corpus

- `harness/fvh/stats.py` (frozen core, additive; a DELTAS entry and core tests; `mde_two_proportions` unchanged so Q is unaffected): `auc_budget(first_success_calls, budget)`, `cluster_bootstrap_ci(cluster_values, *, n_resamples, confidence, seed)`, `mde_paired_clusters_sim(K_by_size, repeats, base_auc, icc, tau, eta, *, alpha, power, n_sims, seed)` (the §3.4 routine, deterministic).
- `harness/fvh/prereg.py`: new required plan fields `estimand`, `primary_contrast`, `test`, `budget_axis`, `aggregation`, `missing_rule`, `resource_accounting`, `cluster_rule`, `confirmatory_clusters`, `pilot_clusters`, `power_sim_sha256`; refusal when pilot and confirmatory clusters overlap.
- `harness/fvh/report.py`: per-cluster AUC table, the primary test, bootstrap bands, truncation and missing counts, from logs only.
- `harness/r/fvh_r/engine.py` (learner file; its frozen acceptance tests change): a shared `feedback_cap_tokens` applied to both formats in `native_outcome(…, raw_feedback=…)`; per-call accounting fields; regimes unchanged (`R12Independent` (10, 1, fifo), `R12Repair` (1, 10, lifo), `R12BestFirst` (3, 10, best), `R12BestFirstRaw`).
- `tools/R12/plan.py`: plans from the schema-2 stratum (confirmatory, pilot, descriptive subset as three executable plans); `tools/R12/admit_forms.py` run on every new form.
- `bench/local/r/labalpha/`: `STRATUM.toml` schema 2 (`[[cluster]]` with id, source = module/reference/lemma or set/task, tasks, role = pilot|confirmatory|descriptive, admission); the 40 toy forms move to `apparatus-smoke` (kept for CI replay, never data); `UNUSED_PUBLIC.json` is replaced by the admitted public slice with its C0–C7 log; sealed R13/R14-derived tasks under `Hidden/labs/R12/`.
- `MODULES.toml` R12 `budget`, PLAN §4.3/§14, design §11.3 and `docs/R12_Driving.md`'s Lab α section and pre-registration problem (`paper/R12_problems.tex`): rewritten to the frozen primary (the learner registers it and their descriptive analyses; §6 D-L4).

### 3.9 What the lab can and cannot conclude

It can conclude, at the pre-registered level, whether obligation-localized feedback raises best-first's budget-weighted success on this corpus with this model, and it can describe the four regimes' curves with honest bands. It cannot test where curves cross, cannot generalize beyond the corpus, model and prompts, and cannot separate "localization" from "shorter prompt" except through the token-axis sensitivity line.

---

## 4. The exemplar and the R module bar

### 4.1 Which module first: R02 (recommended)

R02 is shipped (its defects are learner-visible now); it is small (342 min) and A1-only, so nothing in §1 or §3 moves under it; it has every recurring artifact (paired D/V holes, R-owned predictions, a rung-2 agent file, written problems, a bench card, a 12-question bank); and its defects cover every systemic category (no source block, an untaught construct, hole order and prompts, a layer that leaks its answers without a header, registry rows). R04 and R05 then copy its patterns directly. Alternatives: R06 (the band-1 resolution with a checkpoint, more representative of hard modules, but 462 min and heavy native sweeps) or R05 (adds the Python pattern). §6 D-E1.

### 4.2 The R module bar (derived from the Q bar and spec §12.1)

| # | criterion | number / form | checked by |
|---|---|---|---|
| 1 | chapter length | 5,000–8,000 words (PLAN §1.2) by `scripts/chapter_lint.py`'s counter | lint |
| 2 | skeleton | spec §2.4.3's headings in order, stable headings, "What the dashboard can and cannot see", "What Rnn planted" table | lint |
| 3 | source in the chapter | ≥ 1 `dafny` and ≥ 1 `rust` block in every numbered section that introduces a construct; ≥ 6 of each per chapter (Q01–Q09: 7–22); each a pinned specimen fence or a twin excerpt that answers no hole | lint (pinned-fence count) + leak verifier |
| 4 | outputs inline | every quoted output immediately after the command or code that produced it, pinned; **no output appendix** | lint + `pins.py` |
| 5 | predicts | each box before its answer; the answer quotes the captured output; ≥ 2 `dv` predictions; slots unfilled | `firsttry --check`, lint |
| 6 | diagrams | exactly the diagrams PLAN §3's record names (3–5), rendered mermaid | lint |
| 7 | hole prompts | every H/T/X item has a doc comment `**Hn.** <task sentence>. <guiding question>` (Q06 form) | `course_items.py` (new check) |
| 8 | hints | **2 hints per hole** (`Hint(1)`, `Hint(2)`), the second naming the given fact or layer lemma, never the answer | course_items check + leak verifier |
| 9 | order | a hole comes after the card or worked example of every construct in its `uses:` | course_items check |
| 10 | checks | each exec hole has a live use-site check (an `assert` in a given client or a compiled test) | twin gate |
| 11 | constructs taught | every construct a reference needs (`choose`, `assert forall … by`, `calc`, triggers) is taught in a card or a chapter block before the hole | review checklist |
| 12 | readable twins | at most one statement per line; no `{ …; … }` one-liners beyond a single-expression body; spaced numerals ("12-question", "3 seeds") | formatter + lint (glued-numeral rule) |
| 13 | bank | 12 questions (8 for R01), Q06 schema: header line (viva, tags, backward edge), toy code in both languages, Target insights, ≥ 2 Misconceptions & counter-moves, Verifier probe with real captured output, answer and follow-up, **Reread** with stable headings; ≈ 80–120 lines per question (≥ 900 lines per bank); mix reconstruct/predict/why/connect/transfer; two disjoint draws **each with ≥ 1 live predict**; 2 parallel problems with *Isolates* and *Diagnostic*; fresh names | bank checker + avoid.sh |
| 14 | leak patterns | 3–8 entries per module, each with its `# source:` line, cut only from H/X/T/A answers, Rule 1 and Rule 2 replayed | `tests/instructor` |
| 15 | admission rows | one `[module.admissible]` row per H/T/X item with the four results; minutes reconcile to the record's total | course map + notes |
| 16 | layer headers | every layer file that re-supplies an answer says which module's first tries it must wait for | review checklist |
| 17 | written pair | compiles; rubric pins filled; calibration fixtures | paper/rubric CI |
| 18 | CI | six focused jobs, then inclusion in the accumulated run (§5 step 6) | CI |

---

## 5. Work order

Every solver job runs under `systemd-run --user --scope -p MemoryMax=<lane> -p MemorySwapMax=0`; total solver RAM ≤ 48 GiB across lanes; ≤ 6 Verus workers in total; one native R lane = 16 GiB with `GATE_WORKERS=1`, `DVL_VERUS_JOBS=3`; at most two native lanes beside one CI lane; scratch under `~/.cache/dafny-verus-learn-0/author-probes/<step>/`. Document-only work (chapters, banks) has no solver budget but advances one module at a time until the exemplar is accepted.

| step | deliverables | gates | effort [A] | lanes |
|---|---|---|---|---|
| 0 | canonical line + `basic` (elsewhere) | `authoring` rebased; Q unaffected | — | — |
| 1 | this plan; user answers to §6 | — | done | docs |
| 2 | **`u32` migration** (if §6 D-A4 (a)): R03 API core references (D/V, `Solutions/` only), A2-class and A3 on `u32` (+ accessor, `SpanClass` removed), R07 and R09 ports, the R09 tool re-capture, DELTAS entry "D48 implemented" | §1.5 items 1, 3, 4; tier check; avoid.sh 0 hits | 3 sessions | 1 native |
| 3 | **restore objectives + pilot**: R08 rebuild (§2.3), R12 native holes (§2.4), R13 holes (§2.5), R14 rebuild (§2.6) — one module at a time, each to admission and focused CI; Lab α corpus admission, `fvh.stats`/`prereg`/`report` changes with core tests, the pilot run (§3.6), freeze | four results per hole; three seeds; `specfreeze`/`vaudit` on agent plants; pilot instrumentation checks; prereg refuses an incomplete freeze | R08 2, R12 1, R13 1.5, R14 2.5, Lab α corpus 3, harness 1.5 sessions; pilot ≈ 1.9 GPU-h | 1–2 native + GPU |
| 4 | **exemplar** (R02 unless §6 D-E1): every §4.2 criterion | the bar's checks; study workflow; focused CI; **user acceptance** | 2 sessions | 1 native |
| 5 | **systemic passes** R01, R04–R14 in order (one module at a time until the exemplar is accepted, then two in parallel): §4.2 criteria; registry rows R01/R04; R01 Draw A predict; R06 P5v; R09 reported R04 lines; layer headers on A1b/A2/A3/A4 | per module: the bar's checks + focused CI + study workflow | ≈ 1.5 sessions per module | ≤ 2 native |
| 6 | **accumulated compatibility CI**: one run over R01–R14, layers A1–A4, Q isolation, avoid.sh, course map, leak verifier, all pins | one green run; failures fixed and the whole run repeated | 0.5 session + CI time | CI lane |
| 7 | **R15, R16**: A5 reconciliation (§2.2 of PLAN), designs §2.7–2.8, Lab β/γ pre-registration designs on the §3 pattern, jump-threading spike | as step 3 | R15 4, R16 6 sessions | 1–2 native |
| 8 | **R03 kit** per §1: chapter, bank, paper, predictions, agent, pins; A2's "provisional" label removed once R03 and R06 pass | §1.5 item 2; focused CI; inclusion in a repeat of step 6 | 3 sessions | 1 native |
| 9 | Lab α confirmatory run (after R12's acceptance and the freeze) | prereg hash committed; grade ≥ 3 on every method dimension | ≈ 20 GPU-h | GPU + 6 Verus workers |

---

## 6. DECISION NEEDED

**D-A1 · How much of R03's information hiding A2 keeps.** (a) A2 re-supplies R03's API exactly (Dafny `provides`-hidden datatype, Verus private field) plus a read-only range accessor for A3 and R09; A3's `SpanClass` copy is deleted. (b) A2 stays transparent (`type CharClass = seq<CRange>`, now `u32`), and A3 keeps `SpanClass` on `(u32, u32)`. (c) Like (a), but A3 keeps its own public copy. *Recommend (a):* one class API across R03–R16, and later modules see the hiding R03 taught. It changes what R07–R09 learners can write: no class literals, only API calls.

**D-A2 · The class lowering domain in A3/R09.** (a) Keep the below-`0xD800` domain (unchanged learner-visible behaviour, error `ClassRange` beyond it). (b) Lower every scalar, skipping the surrogate block, so `[\u{E000}-\u{10FFFF}]` works. *Recommend (a)* now; (b) changes R09's grammar, captures and positions, and could be a later R16 `rexc` extension.

**D-A3 · The Dafny name for "u32".** (a) `newtype Cp` (code point), (b) `newtype U32` (clashes with R01's own `U32`; avoid.sh may flag Q's names), (c) a subset type of `int`. *Recommend (a).* Wording-level, listed because learners see it.

**D-A4 · When the `u32` migration lands.** (a) Early (step 2): migrate A2/A3 and port R07–R09 before the systemic passes, so their captures are redone once; R03's kit still comes last. (b) As agreed: everything with R03 at the end, re-capturing R07–R09 twice. *Recommend (a);* it reorders the agreed sequence.

**D-L1 · Lab α's GPU and call ceiling.** (a) Raise R12's ceiling to ≈ 10,700 Qwen calls / ≈ 22 GPU-h (at 7.3 s per call) for design C + pilot + a descriptive subset. (b) Keep 10 GPU-h: primary arms only on design B (5,200 calls, MDE ≈ 0.10), no descriptive regimes beyond the pilot. (c) Decide after DV4 step 3d's throughput probe, with (a)'s call count fixed now. *Recommend (c).* This changes the registry budget (Δ75/Δ176) and what the lab can describe.

**D-L2 · Confirmatory size.** (a) 80 clusters (design C, MDE ≈ 0.08–0.10 AUC). (b) 60 clusters (D49's floor, ≈ 0.10–0.11). (c) 100 clusters at two repeats (design D, ≈ 0.08–0.09; needs more public clusters). *Recommend (a)*, falling back to (c) if regex admission yields < 50 clusters.

**D-L3 · R13/R14-derived tasks in an R12 lab.** (a) Seal them in `Hidden/labs/R12/`, show the learner ids and verdicts only, audit transcripts from R06–R11 and public clusters. (b) Exclude them (≈ 8 fewer families, more public clusters needed). (c) Run Lab α after R14. *Recommend (a);* (c) breaks the module order.

**D-L4 · Who owns the primary contrast in the learner's pre-registration.** (a) The course fixes it (D49) and the learner registers it plus their own descriptive analyses; the pre-registration problem and rubric change accordingly. (b) The learner chooses, the course's run uses the fixed one. *Recommend (a).* It changes what the learner writes in R12's written pair.

**D-L5 · Statistics code location.** (a) Add the AUC, cluster bootstrap and simulation-based MDE to the frozen `fvh.stats` (additive, Q unchanged, a frozen-core DELTAS entry). (b) Put them in `fvh_r` (breaks "statistics code exists only in `fvh.stats`"). *Recommend (a).*

**D-L6 · The D45 deferral for the pilot.** The pilot needs live local Qwen calls (960, ≈ 1.9 GPU-h); PLAN §14 extends D45 to Lab α's model arms. (a) Lift D45 for local Qwen calls in the pilot only (Claude stays deferred). (b) Keep D45; build everything to the freeze with replayed runs, and run the pilot later. *Recommend (a).*

**D-R08 · R08's new interface.** (a) The step-matcher interface with two engines and four hand obligations (§2.3). (b) Keep today's `MatchWord` interface and replace the holes by an early-exit derivative matcher plus a dead-state lemma. *Recommend (a);* it changes R08's given F6 file and every R08 item the learner sees, at unchanged minutes.

**D-R14 · `trigscan`'s evidence.** (a) Trigger notes and source spans only; matching loops are reported as potential cycles (honest, reduced scope). (b) Add an author-approved `--log smt` route for R14's tools (a wrapper change, Δ entry). *Recommend (a)* for now; it limits what R14's toolsmith can claim.

**D-E1 · The exemplar.** (a) R02 (shipped, A1-only, every defect category). (b) R06 (band-1 resolution, checkpoint). (c) R05 (adds the Python pattern). *Recommend (a);* it means revising a module already on `basic`.

**D-B1 · Bank depth.** (a) 12 questions at the full Q06 schema (≈ 900–1,400 lines per bank). (b) 8 at the full schema plus 4 short ones, which keeps two disjoint six-question draws only if each draw holds 4 full questions. *Recommend (a)* (PLAN §1.2's 12-question rule stays).

## 7. Decisions taken (2026-10-17)

The user's (asked as multiple-choice questions):
- **D50 (D-L1, D-L2):** 80 confirmatory clusters (design C); the call count is fixed now (about 10,700 local Qwen calls including the pilot and a descriptive subset); the GPU-hour ceiling is set after DV4 step 3d's throughput probe. Fallback: 100 clusters at two repeats (design D) if regex admission yields fewer than 50 clusters.
- **D51 (D-L4):** the course fixes the primary contrast; the learner pre-registers it plus their own descriptive analyses; R12's pre-registration problem and rubric change to match.
- **D52 (D-L6):** run the 5-cluster pilot now on local Qwen (Claude not involved); its clusters are excluded from the confirmatory sample.
- **D53 (D-R14):** add an author-approved `--log smt` route to the wrapper for R14's tools (a wrapper change with its own DELTAS entry), keeping R14's full trigger/matching-loop scope.

The orchestrator's (implementation choices within the approved design; each is the plan's recommendation): D-A1 (a) one hidden class API re-supplied by A2 plus a read-only range accessor, A3's `SpanClass` copy deleted; D-A2 (a) keep the below-0xD800 lowering domain; D-A3 (a) `newtype Cp`; D-A4 (a) the u32 migration lands early, before the systemic passes; D-L3 (a) R13/R14-derived tasks sealed in `Hidden/labs/R12/`; D-L5 (a) AUC, cluster bootstrap and simulation-based MDE added to the frozen `fvh.stats` with a frozen-core DELTAS entry; D-R08 (a) the step-matcher interface; D-E1 (a) R02 is the exemplar (after D46 it is on `authoring`, not on `basic`); D-B1 (a) 12 questions per bank at the full Q06 schema.
