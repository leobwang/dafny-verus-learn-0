# PLAN — the R track plan (topic-ordered)

*Status: **DVR plan, 2026-10-07, revised the same day after DVR0's two spike lanes (Dafny, Verus) closed and after the plan review.** §1–§2 fix the track's shape and the regex artifact (layers A1, A1b, A2–A5, design §10.2; §2.5 lists what DVR0's reconciliation step changes in the spike files); §3 holds the sixteen module records in the spec §2.2 shape (R01–R16, design §8.2); §4 the agentic ladder, the contracts and the three labs; §5 the disjointness rules and the `avoid.sh` contract that DVR0 builds; §6 the item-level plans of band 1 (R01–R06, DVR1's scope) in the grammar of `QPLAN.md`; §7 the cross-module checks; §8 the open questions. Items whose shape still depends on a spike are marked **pending spike** (after the spikes: only R06's Verus decomposer, §2.2); every layer statement here is the plan of record until DVR0 records its layers as built (a DELTAS entry), and every [A] figure is an assumption to calibrate. Chapters, written problems, card prose, banks, rubrics and simulations are budgeted here and written with each module (DVR1 for R01–R06). R07–R16 are described at record level; their item plans arrive with DVR2 and DVR3.*

> **Predictions first.** This file is on the README's *Predictions first* list: until a module's predictions are committed (`scripts/firsttry.sh <ID> --check`), do not open it, and keep it closed during a checkpoint. It names every prediction, hole and checkpoint item of band 1 (a checkpoint item by its id, form, language and minutes only: statements are author-only, as DELTAS Δ133 rules for exits), and never an answer: no answer to a hole, slot or prediction of any module, and no description of a tool behaviour that any prediction of either track asks about.

## 0. How to read this plan

**The R track is standalone** (design decision 1, §8.1). No R record, file or chapter depends on a Q module: an R chapter teaches its whole payload, and where Q owns a surprise (§5.1), R states it as a fact and exercises it with a hole, never with a prediction. The README only *suggests* an order (R after Q09; R12, R15 and R16 after Q12, Q15 and Q18). `Recap → Qnn` links in R chapters are optional and are the only cross-track mentions (isolation I5). Nothing in R imports a Q file, a Q layer, `fvh_q` or `bench/local/q`, and `scripts/check_course_map.py` rejects a cross-track prerequisite edge.

**Item ids** follow the one item grammar (`scripts/course_items.py`, DELTAS Δ71): `<ID>.<K><n><lang>`, with the kinds of `QPLAN.md` §0 (W worked, C card, P prediction, H hole, X checkpoint item, T test-out, A agent run) and `<lang>` one of `d`, `v`, `py`, `dv`. **R items carry no strand**: the R track has no strands, so an R marker is `// item: R04.H2d [format] [min=<m>]`. `pair:`, `uses:`, `need:` and `did:` work as in Q. R records carry no `concept_items` table (that matrix is Q01–Q09 only); an R module's coverage is the `[[coverage]]` rows that name it as an `r_homes` module anchor or item (Δ76), listed in each record below.

**Hole forms, prediction formats, slots, card demos, `// after:` markers, the order inside an exercise file and the verdict-scenario rules** are exactly those of `QPLAN.md` §0 (and §8.0, §14.0 for annotation holes and refinement holes). Python holes are `raise NotImplementedError("<item id>")`, counted from the syntax tree (`QPLAN.md` §0, Q06 row). A hole is admitted only once `scripts/firsttry.sh <ID> --empty-body` (author-only) shows it failing in its shipped configuration.

**Admission, lines and fallbacks** (spec §2.8's gate, read the same way for every R item):
- **The four results.** An item carries minutes only when its reference is complete and all four results are recorded in the author notes: the reference verifies on 3 seeds at the pins; the empty body fails in the shipped configuration; it also fails under maximal automation (Dafny's default induction with every lever attribute the module allows; Verus `E0`/`E0H`/`E1`), or the shipped lever is named; and a trivial body fails where the item is exec code. Until then the item's minutes are 0 in `[module.admissible]` and its line in the itemized table says *gated*.
- **One line-count rule.** A reference's size is its proof lines: proof, invariant, `decreases`-on-loops and ghost lines, plus the statements of the lemmas the learner must invent; exec code is excluded (DELTAS Δ53's reading). The spike counts already follow it (Dafny `summary.json` `proof_lines`, Verus `tools/lines.py`); DVR1 adds the invented statements and re-counts with the course's counter before banding.
- **Fallbacks.** A fallback takes an item's minutes only after it has its own four results; a fallback without them carries 0 minutes, and the shortfall goes into a DELTAS note. A fallback never removes the module's only learner-generalized statement or the only item of a WRITE slug.

**Paths** (registry conventions, `MODULES.toml` header; R is built by name, `build_target = "R"`):

| artifact | path |
|---|---|
| Dafny exercise file (unit `core`; `std` from R07) | `dafny/R/<ID>_<Name>/core/<ID>_<Name>.dfy`, module `<ID>_<Name>` |
| Dafny value-predict check unit (given-only) | `dafny/checks/<ID>_checks.dfy`, module `<ID>_Checks`, listed in the module's `exercises` when it exists |
| Dafny checkpoint / agent file | `dafny/R/<ID>_<Name>/exit/<ID>_Checkpoint.dfy` (R06, R11 only), `dafny/R/<ID>_<Name>/agent/<file>.dfy` |
| Verus crate (exercise) | `verus/r/<id>_<name>/src/lib.rs`; checkpoint `src/exit.rs` (R06, R11), agent `src/agent.rs` (never `mod`-declared) |
| learner Python | `harness/r/fvh_r/<file>.py` (package `fvh_r`, tier `py-fvh`); acceptance tests `harness/tests/r/test_<id>_<file>.py` (frozen, rule 2f) |
| given layers | `dafny/given/R/RG_A<k>_<Name>.dfy` (module `RG_A<k>_<Name>`), crate `verus/given/rg_re_a<k>` |
| specimens, slots, pins, twins | `specimens/<ID>/…`, `slots/<ID>.slots`, `expected/<ID>.{pins,counts,freeze}`, `Solutions/<same path>` — as in `QPLAN.md` §0 |

**Minutes** use the design rates (spec §2.5): reading 120 wpm (a 6–7k-word chapter is 55–70 min), WRITE card 2.5 (inside "worked"), RECOGNISE or divergence card 1.5–4, prediction 2.4–3, hole 4–8 by difficulty, checkpoint item 5, test-out item 5. Every R module's total **includes its 30-min module viva** (design §8.2's totals: "R = 124.9 h standalone, 17 h of lab halves, 30-min vivas"). Agent wall-clock time is outside every budget. Setup lines assume the toolchains are installed: a learner who starts the course with R adds prework P0 (90 min, design §7.1) once.

---

## 1. The track's shape

### 1.1 Bands, personas, bars and hours (design §8.1)

| band | modules | `/discuss` persona | `/review-code` bar | minutes | hours |
|---|---|---|---|---|---|
| 1 Foundations | R01–R06 | sharp-dev ("sharp dev, zero verifier") | it-reads (R01–R03) → proof-shape (R04–R06) | 276 + 342 + 300 + 360 + 402 + 462 = **2,142** | 35.7 |
| 2 Abstraction and theory | R07–R11 | smt-skeptic ("Rust dev who distrusts SMT") | library-conventions (R07–R09) → design-judgment (R10–R11) | 360 + 354 + 444 + 408 + 540 = **2,106** | 35.1 |
| 3 Machine, loop, capstone | R12–R16 | ml-engineer ("ML engineer who thinks tests are proofs") | harness (R12, R15) / production (R13, R14, R16) | 786 + 390 + 390 + 744 + 936 = **3,246** | 54.1 |
| **R** | | | | **7,494** | **124.9** (≈ 119.1 with Q-credit, §1.4) |

The bars and personas are the registry's (`review_bar`, `persona`); `viva_mode = "module"` and `tutor_max_rung = 5` on every R record.

### 1.2 Per-module rules

- **A self-contained chapter** of 5–8k words, `docs/<ID>_<Name>.md`, in spec §2.4.3's skeleton (callback, "Three ideas do all the work", the files table, numbered sections with stable headings, predict callouts with the answer only after the box, "On paper, before the keyboard", the exercise file, the agentic exercise with "What the dashboard can and cannot see", the checkpoint where there is one, instructor touchpoints, and "What <ID> planted").
- **Files:** `.dfy` and `.rs` files with paired holes, at least **2 cross-language (`dv`) predictions** per module, and the module's own objects (design §9.2 item 3: the regex AST, matchers, character classes, derivatives, derivations and the VM are R's alone).
- **Instructor kit:** a rubric, a **12-question bank** (8 for R01) from which `/viva` draws **6 questions** (≈ 30 min, at least one live-refereed predict), so that two disjoint re-viva draws exist (spec §6.8); `/review-code` at the band's bar.
- **Checkpoints** at R06 and R11: 2 Dafny + 2 Verus closed-book items, **≥ 3/4 with ≥ 1 in each language** (DELTAS Δ116; `firsttry`'s `EXIT_MODULES`).
- **Written track** (Δ74): every R module ships a `paper/<ID>_problems.tex` + `_answers.tex` pair with its cards; R01, R03 and R07 hold cards only, the other 13 modules add problems of their own.
- **Bench cards:** R02–R11 each add one `bench/local/r` card written by the learner (statement, stripped version, solution, witness, negative tests); the author adds 14 more, plus stripped R06–R14 lemmas (design §10.3), with author answers in `Solutions/bench/local/r/`.
- **Languages:** Dafny and Verus from R01; Python (`fvh_r`) from R05. Per-module shares are the design's (§3).

### 1.3 R-owned surprises (design §9.2 item 1)

R owns, and only R may pose as a prediction: `midpoint` overflow; `expect` outside tests; a strengthened `requires`; the empty-string and anchoring surprises of regex semantics; failures that appear only at a later stage than the one the learner ran. Q owns `nat` vs `u64` minus, hole visibility, proved vs computed, and auto-induction: an R chapter states each of these as a fact, and an R hole exercises it.

| surprise | first posed | revisited |
|---|---|---|
| `midpoint` overflow | R01.P1dv | R09 (counted repetition's overflow-free expansion budget) |
| later-stage failures | R01.P2dv | R13 (stage attribution) |
| strengthened `requires` | R03.P1d, R03.P2v | R08 (refinement), R15 (statement review) |
| empty-string and anchoring | R02.P1d, R02.P2v, R04.P2dv, R04.P3d, R04.P4v | R10 (normal forms), R15 (Lab β's oracles) |
| `expect` outside tests | R04.P1d, R04.P5d | R13 (`TRUST.md` R-v0), R16 (trust-report) |

### 1.4 Q-credit test-out [A]

A learner who has done the Q track may skip a section of an R module when every first try of that section's T items is correct (the Q test-out rule, design §7.3). The sections are the R homes of a waiver's genre (§5.4), so the skip is what the waiver pre-empts:

| module | waiver | what may be skipped | ≈ min saved |
|---|---|---|---|
| R01 | W2 | the hole-contract and doors sections, the false-friends and Rosetta cards, the triage drill | 72 |
| R02 | W1 | the role-ladder section before the rung-2 run | 20 |
| R04 | W5 | the wp-by-hand recap | 25 |
| R06 | W7 | the loop-invariant basics | 25 |
| R07 | W3 | the contract-and-`EVAL.md` primer | 30 |
| R09 | W4, W14 | the `:-`/`?` primer and the port-mechanics section | 30 |
| R11 | W5 | the wp-calculus review | 30 |
| R12 | W8, W9 | the "parser before model" and equal-calls sections | 30 |
| R13 | W11 | the fresh-process re-run section | 25 |
| R15 | W10 | the mutation-kill primer | 30 |
| R16 | W11, W12 | the gate-design and claim-scoping primers | 30 |
| | | **total** | **347 ≈ 5.8 h** |

The T items cost their minutes either way (each module's "test-out" line); the saving is the skipped sections'. A module appears here only if it has T items and a test-out line: R05 has neither, so its statistics-by-hand recap is not skippable (the earlier draft's 15-min row is dropped).

---

## 2. The regex artifact: layers A1–A5 (design §10.2, D7)

### 2.1 Rules (spec §2.6 as it reads on a topic-ordered track)

1. Layers are author-written, complete, hole-free, frozen (guard rule 2f), identical for the learner and the reference, and imported, never copied. Holes are leaves in a module's own files.
2. A module imports its layer **and every lower layer** (Verus: a dependency on each layer crate of the chain, Δ22). Exercise, check, exit and agent files import given layers only.
3. **The module-order law** (the R reading of `QPLAN.md` §1.1 rule 3). An answer to a hole, checkpoint or test-out item of module R*k* appears only in `Solutions/` and in a layer first declared by a module after R*k*, which then **re-supplies** it. Nothing a layer gives may be posed as a hole, checkpoint or test-out item in a module that imports it; no layer holds the whole answer of an R06 or R11 checkpoint item; a later module's learner-visible files never hold an earlier module's answers (a later module that needs one gets it from a later layer, or re-poses it as its own hole).
4. Learner-visible files never hold an answer to any hole, slot or prediction of any module, in either track.
5. A layer's own code holds no live check whose value a later prediction asks for.
6. Every recursive declaration of a layer states its `decreases` explicitly, in both languages.
7. Layer names, like every R name, pass `avoid.sh` (§5.5): DVR0 renames on a hit.

### 2.2 The layers

| layer | declared by · imported by | Dafny (`dafny/given/R/`) | Verus crate | import tier | content (given; definitions and proved code only) |
|---|---|---|---|---|---|
| **A1** | R02 · R02–R16 | `RG_A1_Re.dfy` | `rg_re_a1` | Dafny `core`, Verus `prelude` | `datatype Re = Empty \| Eps \| Chr(c: char) \| Alt(a: Re, b: Re) \| Cat(a: Re, b: Re) \| Star(r: Re)` / `pub enum Re { …, Alt(Box<Re>, Box<Re>), Cat(Box<Re>, Box<Re>), Star(Box<Re>) }`; the spec `Matches(r, s)` over `seq<char>` / `Seq<char>` by splits (`decreases r, \|s\|`; a `Star` iteration consumes a non-empty chunk; Verus states each split existential's trigger, §2.4 F5); `Nullable(r)`; `NodeCount(r)` (design §8.2's `Size`, renamed, §5.5); `Backwards(r)` (the regex read backwards; design §8.2's `Rev`, renamed) and `BackwardsStr(s)` (the string read backwards); Verus also the exec `is_nullable(r: &Re) -> (b: bool) ensures b == nullable(*r)` and a verified `copy_re`. **Dafny `Matches` is a `ghost predicate`** (so no exec item can answer itself by calling it); `Nullable`, `NodeCount`, `Backwards` and `BackwardsStr` are compiled. **No lemma**: every lemma about these definitions is a module hole (§6) |
| **A1b** | R06 · R06–R16 | `RG_A1b_Facts.dfy` | `rg_re_a1b` | as A1 | the band-1 facts, re-supplied (§2.4): R02's `NullableCorrect`, R02's `CatEpsLeft` with its mirror `CatEpsRight`, R05's `CatAssoc` (both directions), R05's `StarOne` and `StarConcat`; Verus `lemma_nullable_correct`, `lemma_cat_eps_left`, `lemma_cat_eps_right`, `lemma_cat_assoc`, `lemma_star_one`, `lemma_star_concat` |
| **A2** | R07 · R07–R16 | `RG_A2_Deriv.dfy` | `rg_re_a2` | Dafny `std`, Verus `seq_lib` [A] | re-supplied from R03: `CRange`, `CharClass`, `InClass`, `ClassValid`, `ClassMember`, `ClassInsert`, `ClassUnion` and their lemmas; re-supplied from R06: `Deriv(r, c)`, `DerivCorrect(r, c, s)`, the derivative matcher `DerivMatch` (Verus `deriv`, `lemma_deriv`, `deriv_exec`, `matches_vec`, `matches_str`, and the class API, which the Verus spike did not build: DVR0 adds it, §2.5) |
| **A3** | R09 · R09–R16 | `RG_A3_Syntax.dfy` | `rg_re_a3` | `std` / `seq_lib` [A] | the surface AST with positions (`Syn`: classes, `Plus`, `Opt`, counted repetition `Rep(r, n, m)` with **single-digit bounds**, §3 R09), its well-formedness, its lowering to `Re` (`Copies`, `Upto`, `Rep`'s definition), and the parser's spec (what a well-formed pattern is, with completeness clauses so that a parser that always fails does not satisfy it, and the position of each error). Not the parser, not the lowering's correctness lemmas (R09's holes), not a digit-run parser (§5.5) |
| **A4** | R10 · R10–R15 | `RG_A4_Norm.dfy` | `rg_re_a4` | `std` / `seq_lib` [A] | the `NormRe` normal form and the smart-constructor *definitions* (R10 proves they preserve the language); the congruence facts the spike found to verify with an empty body under every setting (`CatCongRight`, `CatCong`, `StarOfEps`: given, never holes); the `Derivation` trees R11 checks |
| **A5** | R16 · R16 | `RG_A5_VM.dfy` | `rg_re_a5` | `std` / `all` [A] | the VM: `Inst` (`IChar`, `ISplit`, `IJmp`, `IMatch`), `Advance` (one step; design's `Step`, renamed, §5.5), an **opaque** fuelled `Accepts` with its **four one-step lemmas** (one per instruction kind; the spike needed them for 3-seed stability), the code-at-offset predicate and the **layout lemmas** of each constructor's code; frozen. The emitter (`Emit`, design's `Compile`, renamed) and the capstone's correctness statements are the learner's |

The A1–A5 rows are the design's (§10.2) as DVR0's spike lanes built them, with A1b added by the plan review (the band-1 facts that R06 and every later module need, §2.4); their tiers are DVR0's call (Δ77: the R layers count as Dafny `core` until DVR0 records them).

**Gated spikes, outcome (design D7, §15.2; spike reports in `Solutions/spikes/regex/`).**
- **S1, closed except for one item.** `DerivCorrect`'s `Star` case verifies in both languages (Dafny 8/8 reference runs; Verus 3/3 seeds), complete, in band and killed by the empty body, so R06's flagship carries no star-free fallback. The Dafny decomposer's reference (`BackwardsCorrect` and its helpers) verifies too. **Still open: the Verus decomposer** (the Verus spike built no `node_count`, `backwards`, `backwards_str`, `lemma_star_one` or decomposition), so R06.A1v keeps its fallback until DVR0 builds and gates it.
- **S2, feasible.** R11's `PointsTo` NFA arena verifies (14/14, `arena_match` equals `matches`); three of its exec fns cannot be gated yet because the gate's `E0` variant strips the `let tracked` lines their code needs (§3 R11, §8 R15).
- **S3, closed.** VM soundness and completeness hold with nullable `Star` bodies and backward jumps, in both languages: no star-free or forward-jump fallback.

### 2.3 Who imports what

| module | Dafny unit(s) reach | Verus crate depends on |
|---|---|---|
| R01 | no layer | `vstd` only |
| R02–R05 | A1 | `rg_re_a1` |
| R06 | A1, A1b | `rg_re_a1`, `rg_re_a1b` |
| R07–R08 | A1, A1b, A2 | up to `rg_re_a2` |
| R09 | A1, A1b, A2, A3 | up to `rg_re_a3` |
| R10–R15 | A1, A1b, A2–A4 | up to `rg_re_a4` |
| R16 | every layer | up to `rg_re_a5` |

Generated units (Δ78): `dafny/R/R0x_<Name>/core/dfyconfig.toml` with the prefix globs `../../../given/R/RG_A1_*.dfy` (from R06 also `RG_A1b_*.dfy`, from R07 the higher layers'), `[options]` from `dafny/options/core.toml` (from R07 `std.toml`); a module crate depends on `vstd` and its chain's layer crates. `avoid.sh`'s layer-prefix stripping must accept `RG_A1b_` beside `RG_A<k>_` (§5.5). **The R track's Dafny induction setting** (DVR1's call, Δ78): this plan proposes an override `R03-R16 manual-lemma-induction = true` beside Q's `Q03-Q18` one, with R01–R02 on the default; R01's and R02's lemma holes carry `{:induction false}` where the empty-body gate needs it (§6.2 records which do, from the spike's evidence; §8 R2).

### 2.4 What each layer re-supplies, and the proof obligations of §2.1 rule 3

- **A1** re-supplies nothing (it is the first layer). It gives definitions only, so no A1 declaration has the statement of any band-1 hole (§6's tables list each hole's target; none is an A1 declaration).
- **A1b** (declared by R06, after R02 and R05) re-supplies R02's `NullableCorrect` and `CatEpsLeft` and R05's `CatAssocLR`/`CatAssocRL` (as one equivalence, `CatAssoc`), `StarOne` and `StarConcat`; `CatEpsRight` is new given code (no module poses it). R06 poses none of them; R06 and every later module may use them. R02's and R05's holes are therefore never re-posed inside R06, and a learner's missing or wrong R02/R05 proof never reaches R06 (spec §2.6 rule 3).
- **A2** re-supplies R03's character-class API and R06's `Deriv` family (`DerivCorrect`, `DerivMatch`). By rule 3 none of these may be posed again from R07 on; R07–R16 may use them.
- **A3** re-supplies nothing from band 1 (the spike's copies of `CatEpsLeft`, `CatEpsRight` and `CatAssoc` move to A1b); R09's parser and lowering proofs are not in it. **A4** may re-supply R08's `Matcher` refinement only if no R10–R15 item re-poses it (DVR2 decides). **A5** re-supplies what R16 needs from R10–R15 (the normal form's lemmas, the certifying matcher's checker) as DVR3 decides.
- **Forward constraints.** F1: no module R02–R16 poses an A1 definition. F2: R01's targets are R01-owned (never re-supplied, never re-posed). F3: R06's checkpoint items share no code with R02–R05's holes or worked examples (the author notes record the check). F4: A1b and A2 together are the complete set of band-1 targets any layer re-supplies; a band-2 or band-3 item that needs another band-1 answer re-poses it. F5: A1's Verus `matches` states its split triggers, so no R14 prediction may ask which trigger A1's existentials need. F6: R08's abstract `Matcher` specification ships in a given-role file (Δ3, Δ97), never in a learner's exercise file.

### 2.5 DVR0's reconciliation step (the spike files → the shipped layers)

The spike files are the references; before DVR1 arms R02, DVR0 turns them into the layers of §2.2 and re-runs both spike gates on the result (each lane's own wrapper, one solver job at a time). A DELTAS entry records the layers as built.

1. **A1 (Dafny).** `Matches` becomes a `ghost predicate` (the spike's is compiled); every lemma leaves A1 (into A1b, or back to `Solutions/` as a module reference); the names of §5.5 (`Mirror` → `Backwards`, `Reverse` → `BackwardsStr` and their lemma names).
2. **A1 (Verus).** Keep the spike's split trigger on `s.subrange(0, i)` (the spike showed that a trigger on the recursive call stops `Cat` and `Star` from unfolding); add `node_count`, `backwards` and `backwards_str` (absent from the spike); move `lemma_nullable` to A1b as `lemma_nullable_correct`.
3. **A1b, new.** Dafny from the spike's `NullableCorrect`, `StarOne`, `StarConcat` (A1) and `CatEpsLeft`, `CatEpsRight`, `CatAssoc` (A3; `CatAssoc` keeps its `{:induction false}`). Verus: `lemma_star_concat` from the spike's A4; `lemma_star_one`, `lemma_cat_eps_left`, `lemma_cat_eps_right` and `lemma_cat_assoc` are new (the Verus spike built none of them) and are gated with the rest.
4. **A2.** Drop `NullableCorrect`/`StarOne`/`StarConcat` from its re-supply list (A1b has them); add the Verus character-class API (absent from the Verus spike).
5. **A3.** Bounds become single digits; the spike's decimal digit-run parsers (Dafny `NumFrom`, `ParseNum`, `DecVal`, `DigitEnd`, `DecValMono`; Verus `parse_num`, `digits_val`) leave the layer and the references (§3 R09, §5.5); the parser, `RepCorrect` and its helpers stay in `Solutions/` as R09's references; `ClassItems` and `Counted` gain completeness clauses (a trivial `Err` body satisfies their spike specifications).
6. **A4.** `CatCongRight`, `CatCong` and `StarOfEps` ship as given code (they verify with an empty body under every induction setting; only an opaque `Matches` kills them, and then the answer is one `reveal` line).
7. **A5.** Keep the spike's opaque `Accepts`, its four one-step lemmas, the per-constructor soundness and completeness lemmas and the layout lemmas (Dafny: with `Accepts` transparent, the soundness proof was seed-unstable at the pinned limit; Verus: per-constructor lemmas, an opaque `code_at` and the helper lemmas the first sweep needed). Rename `Compile` → `Emit`, `Step` → `Advance` (Verus `compile` → `emit`, `compile_into` → `emit_into`, `compile_prog` → `emit_prog`; §5.5).
8. **Gate-tool requests** (DV4 or DVR0, tools owner): named-return proof fns need a body that type-checks (the Verus lane's `gate_ret.py` used `{ arbitrary() }`); a Verus variant that keeps `let tracked` lines and strips only asserts and proof blocks, for R11's arena (§8 R15).
9. **Items still to gate.** Every band-1 item the spikes did not gate (the author notes §1.4 list them by id), on the shipped files, by DVR1.

---
## 3. Module records R01–R16 (spec §2.2 shape)

Each record: the registry title; **why** it exists (its design role); the **core payload** ("D \| V" marks where the languages differ); the **diagrams** its chapter must draw; the **written-track** problems (or "none, it would be filler" beyond the card); the **exercises**; the **agentic role** (its rung on R's ladder, §4.1); the **whispers** it plants (→ harvest) and harvests (← seed); the **research tie-in card** (`cheatsheets.md` id; the card is a `[paper-card]` problem of the written pair, graded by `/grade-paper` against the sha-pinned range); the **hours** (minutes, language share); and the **coverage rows** it is an R home of (`MODULES.toml` `[[coverage]]`, by `payload_id` without the strand prefix where unambiguous). Band 1's items are in §6; band 2's and band 3's are DVR2's and DVR3's.

### Band 1 — Foundations (R01–R06; persona sharp-dev)

#### R01 — Hello, two verifiers
- **Why.** Repo anatomy and first contact: the three feedback loops of each tool; first definitions and a first lemma in both languages; the hole contract; one language gotcha; the learner writes contract R-v0 by hand; first contact with the guard (the three doors). The module that makes "green with zero tool-counted holes" the only meaning of *done*.
- **Core payload.** The three loops per tool: in-editor (the Dafny extension \| verus-analyzer), single file (`scripts/vcheck <file>`), whole module (`scripts/vcheck --module R01`, `--gate`); `requires`, `ensures`, `assert`, calling a lemma \| proof fn; `int` vs bounded integers (a Dafny `newtype` \| `u32`); compiling and running verified code (`scripts/vcheck --test`); what each verdict (`verified`, `failed`, `inconclusive`, an error at a stage) licenses; holes of every kind the course counts, and where each tool reports them (a Q-owned fact, stated); the false-friends card (`calc`, `assert`, `forall`, `old`, `decreases`, `==>`, design C7).
- **Diagrams.** The three loops per tool, with their latencies; the hole contract (each hole form → who counts it → what the done gate does); the verdict ladder (what each verdict licenses and what it does not).
- **Written track.** The card only (Δ74); further problems: none, they would be filler.
- **Exercises.** `Midpoint` without overflow; the precondition a naive mean needs; a first recursive lemma over strings; the hole census (test-out); a triage drill over recorded outputs. (Digits and decimal parsing are Q's, design §9.2 item 3.)
- **Agentic role.** Rung 1, **repairer** (4 planted errors per language, one-line fixes), plus the **three doors**; then rung 3, **contract R-v0** written by hand from the R01 transcript (`CLAUDE.md`, `### R-v0 — R01`).
- **Whispers.** Plants: "the verifier checks the contract, not your intent" (→ R04 spec strength, R15 statement review); "a run proves nothing about inputs it did not see" (→ R02 property tests, R15's escalation ladder); "a hole the tool does not count is not done" (→ R04 `expect`, R13 TCB). Harvests: none (first module).
- **Research tie-in.** 12.11 Hoare, *The Verifying Compiler* (2003): the programme's founding criteria and the "verified lines × annotation level × verification level" progress measure; the R01 lens is what the done gate certifies and what it leaves to a reader.
- **Hours.** 276 min (4.6 h), D/V 50/50; bank of 8.
- **Coverage.** S1 int-vs-machine-integers, running-verified-code; S2 requires-and-ensures; S3 assert-and-assert-by, verdicts-and-failure-triage, false-friends; S9 cli-doors-and-exit-codes; S10 loud-and-silent-holes; S12 contract-and-allowlists, agent-role-ladder; S13 paper-cards.

#### R02 — Datatypes and recursion
- **Why.** Data first: seeds the running artifact (A1's `Re`), plants the empty-string quirk for later payoff, and starts the gradebook and the ledger with the first written-track grading cycle. Recursion over a datatype and over a string, with termination measures that are the learner's to justify.
- **Core payload.** `datatype Re`, `match`, recursive functions with `decreases` \| `enum` + `Box`, `match` on `&Re`, recursive exec fns with `decreases`; the spec `Matches` by splits (existentials over split points; witnesses); A1's `Nullable`, `NodeCount`, `Backwards`; structural induction (lemma recursion) in both languages; first tests: Dafny `@Test` \| Verus `#[test]` outside `verus!` (the first rung of the escalation ladder, design §11.1 row 14).
- **Diagrams.** The `Re` tree of a sample pattern; the split picture for `Cat` and for `Star` (chunks, the non-empty first chunk); the termination measure as a pair ordered lexicographically.
- **Written track.** The card; **termination of `Matches`** (why the measure decreases in every recursive call); **splits by hand** (enumerate the splits that decide two `Matches` facts).
- **Exercises.** `NullableCorrect`; the `NodeCount`/`Backwards` lemma; `Nullable` of a reversed regex; `Cat(Eps, r)`; an exec emptiness test `IsVoid` (design §8.2's `Nullable`, `Size`, `Rev`, renamed per §5.5).
- **Agentic role.** Rung 2, **implementer vs checks** (spec-first: three definitions against a check suite), then the learner adds adversarial checks and first property tests the agent might have gamed.
- **Whispers.** Plants: the empty string (→ R04 anchoring, R10 normal forms, R15 oracles); the split existential (→ R05 slicing facts, R14 triggers on split existentials); the termination pair (→ R06 lemma measures, R14 fuel on `Matches`). Harvests: R01's "a run proves nothing…" (← first tests).
- **Research tie-in.** 05.6 CLEVER: non-computable specs vs computable ones that leak into the implementation; why A1's `Matches` is a spec, not code.
- **Hours.** 342 min (5.7 h), D/V 45/55; first `bench/local/r` card.
- **Coverage.** S1 datatypes-and-pattern-matching, spec-and-exec-code, sequences-and-collections, running-verified-code; S3 lemma-calls; S4 termination-measures; S7 termination-of-definitions; S12 escalation-ladder-with-property-testing.

#### R03 — Modules and APIs
- **Why.** Total-API design: a character-class API whose clients can use only its contracts. Information hiding as a verification tool, and the first R-owned API surprise.
- **Core payload.** Dafny modules, `import`, export sets (`provides` vs `reveals`) \| Rust `mod`, `pub`, private fields, `View` and `@`, `open` vs `closed spec fn`; representation invariants (`ClassValid`) and abstraction (`InClass` \| the class's view as `Set<char>`); total functions (no partiality hidden in a `requires`); what a client may assume.
- **Diagrams.** The module boundary (what crosses it: signatures and contracts; what does not: bodies, fields); the abstraction square (representation ↔ view, operation ↔ set operation).
- **Written track.** The card only (Δ74).
- **Exercises.** `ClassMember`, `ClassRange` (a total constructor), `ClassUnion` over the given `ClassInsert`, a client that uses only the API, a class built from a string.
- **Agentic role.** Rung 2 at API scale, **API implementer** (intersection and difference from their statements) + the learner's adversarial review of the delivered API (totality, contracts, hidden `requires`).
- **Whispers.** Plants: the strengthened `requires` (→ R08 refinement, R15 statement review); `closed` views (→ R08's `Matcher` interface); `char` ranges (→ R09's encoding divergences). Harvests: R02's datatype and recursion skills.
- **Research tie-in.** 03.2 Lahiri, *Intent Formalization*: the spectrum from tests to logical contracts and the sound/complete measures of a spec; R03's API contracts are the "logical contracts" rung.
- **Hours.** 300 min (5.0 h), D/V 50/50; second bench card.
- **Coverage.** S1 spec-and-exec-code; S6 modules-and-visibility; S7 ghost-code-and-modes.

#### R04 — Specs as logic
- **Why.** The first audit and the first naming of semantic hallucination: "the checker checks proofs against statements, never statements against intent". Specs are formulas to be read, classified and witnessed.
- **Core payload.** Quantified specs (`forall` introduction \| `assert forall … by`; `exists` elimination with `:|` \| `choose`); vacuity and non-vacuity witnesses (witness strings); spec strength (vacuous ⊂ weak ⊂ faithful ⊂ over-strong) and mutant-kill witnesses; anchored (whole-string) vs unanchored (substring) specs; `expect` outside tests (an R-owned surprise) and the audit (`scripts/vaudit`); wp/VC of straight-line code by hand.
- **Diagrams.** The spec-strength lattice with sample specs placed on it; anchored vs unanchored matching on one string; the audit's view of a delivery (what the gate counts, what the audit lists).
- **Written track.** The card; **classify four specs** (faithful / weak / over-strong / vacuous, each with a witness or a counter-witness); **wp/VC by hand** for a three-statement method.
- **Exercises.** Witness proofs (a positive one, a negative one, an anchoring one); a prose-to-spec definition with use-site checks; a mutant-kill witness.
- **Agentic role.** Rung 6, **audited prover** (acceptance includes a clean audit and an unchanged statement freeze; one planted statement is false).
- **Whispers.** Plants: anchoring (→ R15 Lab β's oracles); mutant kill (→ R15 `spectest`); the audit's blind spots (→ R13 TCB, R16 trust-report). Harvests: R01's "contract, not intent" (← spec classification); R02's empty string (← the anchoring predictions).
- **Research tie-in.** 12.5 *Do LLMs Game Formalization?*: validity vs faithfulness, fabricated axioms and silent mistranslation; R04's audit and witness habits are the countermeasures.
- **Hours.** 360 min (6.0 h), D/V 50/50; third bench card.
- **Coverage.** S2 requires-and-ensures, quantified-specs, vacuity-and-witnesses, spec-strength; S3 assert-and-assert-by; S8 wp-and-vcs-by-hand; S10 loud-and-silent-holes; S12 agent-role-ladder; S13 prose-to-spec.

#### R05 — No goal state
- **Why.** Neither verifier shows a goal state. The learner installs the obligation-reading habit (which line failed, which fact the solver lacked), the fast channel, latency economics, and the first measurement of run-to-run variance.
- **Core payload.** Obligations and their labels; assertion bisection; `assert … by` scoping; per-assertion and per-function isolation (`@IsolateAssertions` \| `#[verifier::spinoff_prover]`, `scripts/vcheck --isolate`); the fast channel (`scripts/vcheck --symbol`) vs the full gate, and their latency; resource limits and the verdict kinds; repeated runs, the coefficient of variation, and a first bootstrap interval composed from the frozen `fvh.stats` (Python, `harness/r/fvh_r/variance.py`).
- **Diagrams.** From a proof to its obligations to the failing labels; the bisection tree; the latency ladder (editor, fast channel, file, gate).
- **Written track.** The card; **facts per line** (for a given proof, the fact each line contributes and the obligation it discharges); **first intervals by hand** (CV and a bootstrap interval of five timings, by hand, before the code).
- **Exercises.** `Cat` associativity in both directions; `StarOne`; a bisect-and-repair proof; the variance log and its two Python holes.
- **Agentic role.** Rung 6, **obligation prover**: a prover restricted to the fast channel plus one final full gate as its verdict; the learner logs latency and calls.
- **Whispers.** Plants: obligations as data (→ R12's obligation extractor); variance (→ R07 pass@k and `EVAL.md` R-v0, R14 CV sweeps, R12 Lab α's statistics). Harvests: R02's splits (← the slicing facts bisection finds).
- **Research tie-in.** 06.3 Xu & Odersky, *Agentic Proof Automation*: agents run the edit→compile→refine loop on compiler feedback alone; R05 is that loop done by hand, with its latency measured.
- **Hours.** 402 min (6.7 h), D/V 50/50 plus Python (variance +0.5 h, design §8.2); fourth bench card.
- **Coverage.** S3 verdicts-and-failure-triage, obligations-without-a-goal-state; S9 pinned-wrapper-and-fast-channel; S11 resource-limits-and-verdict-kinds; S13 statistics (py).

#### R06 — Induction and loops
- **Why.** Resolves band 1: invariants as induction hypotheses, hole-driven decomposition (green at every step), statement auditing (refute → repair → prove), and the **flagship written problem**, a paper proof done before the keyboard. Declares A1b, the band-1 facts layer (§2.2). The first checkpoint.
- **Core payload.** Lemma recursion as induction, with measures on lemmas (`decreases` on a lemma \| proof fn); `calc` chains \| `calc!`; manual induction in Dafny (`{:induction false}`, the auto-induction fact stated, Q-owned); loop invariants and loop `decreases`; the Brzozowski derivative `Deriv(r, c)` (given) and its correctness (`DerivCorrect`, the flagship, every constructor including `Star`; S1 closed); the derivative matcher's loop invariant; refuting a plausible false statement about `Star` with a counterexample, repairing it with the weakest hypothesis, proving the repair.
- **Diagrams.** A string consumed one character at a time, with the derivative after each step; the invariant as the induction hypothesis of an induction on the loop counter; the decomposition tree of the flagship (its cases, and what the paper proof finds).
- **Written track.** The card; **the flagship: the paper proof of the `Cat` case** [A]; **the matcher's invariant as an IH** (state and prove it on paper as an induction on `i`).
- **Exercises.** `DerivCorrect` (flagship); the matcher-loop invariant; refute → repair → prove on a `Star` claim; the checkpoint (2 D + 2 V).
- **Agentic role.** **Decomposer** (R's extra rung): the agent receives only a top statement (the reversal theorem over A1's `Backwards` and `BackwardsStr`; the Verus side pending spike S1, fallback `Cat` distributing over `Alt`) and must decompose while staying green.
- **Whispers.** Plants: derivative blow-up (→ R10 smart constructors and normal forms); the derivative matcher as an implementation of a spec (→ R08's `Matcher` refinement, R16's VM as a second implementation); "generalize the invariant" (→ R16's simulation generalized over the continuation, X1). Harvests: R02's termination pair (← lemma measures); R02's and R05's lemmas (← A1b re-supplies them).
- **Research tie-in.** 03.4 AutoSpec: bottom-up annotation synthesis that keeps only provable candidates; R06's decomposer and refute→repair→prove are the hand version of its generate-and-validate loop.
- **Hours.** 462 min (7.7 h), D/V 50/50; fifth bench card (a stripped R06 lemma).
- **Coverage.** S3 calc-chains, lemma-calls; S4 loop-invariants, termination-measures, lemma-recursion-as-induction, auto-vs-manual-induction (d; the cards C4d/C5d and the `{:induction false}` items H1d and X1d), invariant-generalization; S8 hoare-logic-and-invariants-as-ih; S12 refute-repair-prove.

### Band 2 — Abstraction and theory (R07–R11; persona smt-skeptic)

#### R07 — Libraries: what they cost
- **Why.** Install mechanics taught cold, the automation the libraries bring, the search ladder, and the cost of trusting a library; the first evaluation report.
- **Core payload.** Dafny `Std` (`--standard-libraries`, the `std` unit) \| `vstd` set and sequence lemmas, `broadcast use` after explicit calls (hand-first rule, design §6.3); import tiers checked transitively (Δ77); the **toolchain-mismatch lab** (Verus's exact rustc, a Dafny/Z3 mismatch; design §2.9); the trusted base of each library [verify]; search-then-name; **unbiased pass@k** by hand on the retriever race's results; `research/EVAL.md` section **R-v0**.
- **Diagrams.** The library's trust surface (what is proved, what is assumed, what is external); the search ladder; the import-tier lattice.
- **Written track.** The card only (Δ74).
- **Exercises.** Library-backed rewrites of band-1 facts about sequences and sets of characters (over A2's re-supplied class API); a trust audit; pass@k by hand.
- **Agentic role.** Rung 4, **retriever race** (agents with and without retrieval on the same library goals).
- **Whispers.** Plants: pass@k and `EVAL.md` (→ R12 Lab α, R15, R16); the library's TCB (→ R13). Harvests: R05's variance (← the interval on the race's numbers).
- **Research tie-in.** 06.5 Rango: retrieval of similar finished proofs per step; the race measures whether retrieval helps on R's goals.
- **Hours.** 360 min (6.0 h), D/V 50/50 (pass@k +0.25 h); sixth bench card. Itemized [A]: setup 10, test-out 10, read 60, worked 30, cards 6, predicts 15, holes 62, mismatch lab 20, trust audit 20, pass@k by hand 15, `EVAL.md` R-v0 15, agent 25, paper 15, bench 20, viva 30, calib 7.
- **Coverage.** S1 sequences-and-collections; S5 standard-libraries, import-tiers, toolchain-mismatch-lab, broadcast-groups (v), search-then-name, retriever-race; S10 trusted-computing-base; S13 statistics (py), eval-reporting-and-disclosure.

#### R08 — Abstraction
- **Why.** An interface and its refinements: debugging resolution and refinement failures that are semantic, not wiring.
- **Core payload.** A `Matcher` interface (`abstract module` + `refines`, the abstract module in a given-role file, §2.4 F6 \| a trait with spec methods and an implementation) refined by the derivative matcher; opacity (`opaque`/`reveal` \| `#[verifier::opaque]`/`reveal`); what a refinement may change (weaken `requires`, strengthen `ensures`) and why; the obligations a refinement generates.
- **Diagrams.** The refinement square (interface spec ↔ implementation); the direction of `requires`/`ensures` changes allowed by refinement.
- **Written track.** The card; **refinement obligations** (list, for a given refinement, every obligation and which side discharges it).
- **Exercises.** The derivative matcher as a `Matcher` refinement; a second refinement over A2's class API; opacity repairs.
- **Agentic role.** Rung 5, **infra debugger (semantic)**: a refinement that fails for a semantic reason, which the agent must diagnose without weakening the interface.
- **Whispers.** Plants: the interface (→ R11's certifying matcher, R16's VM refining the same interface). Harvests: R03's strengthened `requires` (← the refinement directions), R06's matcher.
- **Research tie-in.** 06.7 Ringer et al., *QED at Large*: proof engineering, maintenance and repair, where the theorem is always available as the spec.
- **Hours.** 354 min (5.9 h), D/V 50/50; seventh bench card. Itemized [A]: setup 10, read 60, worked 30, cards 7, predicts 15, holes 90, refinement lab 30, agent 25, paper 30, bench 20, viva 30, calib 7.
- **Coverage.** S6 abstraction-and-opacity, traits-and-interfaces, refinement.

#### R09 — Effects
- **Why.** Grows the artifact with errors: a regex-syntax parser with positions, and the first port with a fidelity audit (D → V).
- **Core payload.** Error propagation (`:-` with `Result`/`Outcome` \| `?` with `Result`); positions in errors; counted repetition `Rep(r, n, m)` with single-digit bounds and an **overflow-free expansion budget** (the lowered regex's size, the node count times the number of copies, checked against a cap without overflowing a machine integer); mutation and old state in the parser's cursor (`old`, `modifies` \| `&mut`, `old`/`final`); the D → V **port** and its **fidelity audit** (differential execution, Dafny `--target py` vs Verus-compiled Rust, plus mutant-kill parity; an independently transcribed mirror with implication lemmas, labelled "relative to the mirror"; design §6.5); the overflow and `char`-encoding divergences [verify].
- **Diagrams.** The parser pipeline (text → tokens → surface AST with positions → `Re`); the fidelity triangle (spec D, spec V, mirror) and why implication lemmas alone are circular.
- **Written track.** The card; **the fidelity method** (what each instrument can and cannot show, for this port).
- **Exercises.** The parser's holes over A3's spec (the bound checks, the expansion budget, the error positions); `Rep`'s lowering and its correctness; the port and its audit. The bounds are single digits, so R09 has no decimal digit-run parser: that is Q's object (§5.5).
- **Agentic role.** Rung 7, **refactorer under harness**: the agent ports or refactors; the learner checks whether migrated statements silently weakened.
- **Whispers.** Plants: positions (→ R16's `rexc` error messages); fidelity (→ R15 statement review, R16's Dafny mirror). Harvests: R01's `midpoint` overflow (← the expansion budget), R03's `char` ranges (← encoding divergences).
- **Research tie-in.** 06.11 PUMPKIN Pi: proof repair across type equivalences; the port is a hand-made transport, audited.
- **Hours.** 444 min (7.4 h), D/V 45/55 (fidelity method +0.25 h); eighth bench card. Itemized [A]: setup 8, test-out 10, read 60, worked 30, cards 8, predicts 15, holes 110, port + fidelity audit 60, divergence lab 25, agent 25, paper 35, bench 20, viva 30, calib 8.
- **Coverage.** S1 int-vs-machine-integers; S6 frames-and-ownership, mutation-and-old-state; S13 cross-language-fidelity.

#### R10 — Invariants in types
- **Why.** The invariant-enforcement spectrum (runtime check → `Option` → precondition → subset type \| `type_invariant`), and the **flagship spec-to-proof contractor**: the learner writes the statements, the agent delivers implementations and proofs.
- **Core payload.** Smart constructors and normal forms (`NormRe`, over A4's definitions); subset types and `function by method` (D) \| `#[verifier::type_invariant]` [verify] and `Ghost`/`Tracked` wrappers (V); erasure (what reaches the compiled code); termination of the normalizer.
- **Diagrams.** The enforcement spectrum with one invariant placed at each point; the normal form's lattice of rewrites; erasure (ghost vs compiled parts of one function).
- **Written track.** The card; **erasure** (for given code, what is erased and why the compiled result is still correct).
- **Exercises.** `NormRe` invariants; the smart constructors' language-preservation statements (written by the learner); erasure items.
- **Agentic role.** Rung 8, **spec-to-proof flagship**: "smart constructors preserve the language".
- **Whispers.** Plants: normal forms (→ R11 derivations, R16 jump threading). Harvests: R06's derivative blow-up (← why normal forms), R02's empty string (← normal-form edge cases).
- **Research tie-in.** 03.5 SpecGen: LLM-written contracts repaired by verifier feedback and mutation; R10's statements are the human half of that loop.
- **Hours.** 408 min (6.8 h), D/V 50/50; ninth bench card. Itemized [A]: setup 5, read 60, worked 30, cards 8, predicts 15, holes 110, spectrum lab 30, flagship (statements 40, audit 20) 60, paper 30, bench 20, viva 30, calib 10.
- **Coverage.** S2 spec-strength; S7 ghost-code-and-modes, subset-types-and-type-invariants, erasure, function-by-method (d); S12 agent-role-ladder; S13 prose-to-spec.

#### R11 — Theory
- **Why.** Foundations hands-on: wp/VC on the matcher loop, a **certifying matcher** whose output is checked by a verified derivation checker, and the second checkpoint; the Verus `PointsTo` arena where the gate admits it.
- **Core payload.** wp and VCs of the matcher loop (by hand, then compared with the tools' obligations); `Derivation` trees (A4) and a verified `CheckDeriv`; certificate checking as the honest substitute for an independent re-checker; V: a **gated** `PointsTo` NFA arena (S2 feasible: the spike's arena verifies, but three of its exec fns cannot yet be gate-tested, §8 R15; fallback a `Vec`-backed arena with index invariants); the "golden triangle" read for matchers (normal forms ⇔ decidable checking).
- **Diagrams.** A derivation tree for one match; the checker's trust story (untrusted matcher, trusted small checker); the arena's ownership picture (gated).
- **Written track.** The card; **derivations by hand** (build and check two derivations, one of which is subtly wrong).
- **Exercises.** `Derivation`, `CheckDeriv` and its soundness; the matcher loop's VCs; the arena (V, gated); the checkpoint (2 D + 2 V).
- **Agentic role.** Rung 13, **metatheory contractor**; the audit targets statements (a plausible but wrong derivation rule verifies).
- **Whispers.** Plants: certificates (→ R13's TCB, R16's trust-report). Harvests: R06's invariant-as-IH (← the loop's VCs), R10's normal forms.
- **Research tie-in.** 12.10 Lean4Lean: an independent kernel and its partial metatheory; R11's checker is a small trusted kernel for matches.
- **Hours.** 540 min (9.0 h), D/V 55/45 (W5: ≈ 30 min of the wp material is review for a Q-credit learner). Itemized [A]: setup 8, test-out 10, read 70, worked 30, cards 8, predicts 15, holes 125, wp/VC on the loop 35, certifying matcher 50, checkpoint 22, agent 25, paper 40, bench 20, viva 30, calib 7 = 495, plus the arena line (V) 45: the `PointsTo` arena once admitted; until then the `Vec`-backed fallback takes the 45 once it has its own four results (§0); until either has them the line is 0 and a DELTAS note records the shortfall (design §7.5).
- **Coverage.** S6 frames-and-ownership; S7 ghost-and-tracked-wrappers (v); S8 wp-and-vcs-by-hand, hoare-logic-and-invariants-as-ih, verified-metatheory (d; gap: R checks derivations, Q verifies a wp), permissions (v; gated), vc-generator-soundness (d; gap: R proves its derivation checker sound, not a VC generator; the row's `gap` is the records lane's, §8 R16).

### Band 3 — Machine, loop, capstone (R12–R16; persona ml-engineer)

#### R12 — Driving the verifier + Lab α
- **Why.** The doors converge on one core; an agent needs a parser before a model; and the first pre-registered lab, on matched compute.
- **Core payload.** The doors (editor, CLI, JSON, the language server), with LSP **framed from a captured trace** (reading, not writing a client: LSP-by-hand is Q-only); a streaming verdict parser and **obligation extractor** over both tools' JSON [verify] (`harness/r/fvh_r/engine.py`); a bounded verdict-loop entry in the same file; the **toolwright** run: a per-function time and resource profiler [verify] (`tools/R12/profiler.py`); Lab α (§4.3).
- **Diagrams.** Four doors, one core; the obligation extractor's data flow; Lab α's three regimes as settings of one engine; success-vs-budget curves.
- **Written track.** The two cards; **Lab α's pre-registration** (claim, metric, estimator, budget arithmetic, MDE, cheat surface, stopping rule), which `/grade-paper` must score ≥ 3 on every method dimension before a run unlocks.
- **Exercises.** Hint-site holes in the exercise files (obligations for the loop); the extractor's and loop's Python holes; the profiler; Lab α's environment and engine.
- **Agentic role.** Rung 10, **toolwright** (the profiler); and **experimental subject** (Lab α's policy runs).
- **Whispers.** Plants: the extractor (→ R15's ladder, R16's trust-report). Harvests: R05's obligations-as-data, R07's pass@k and `EVAL.md`.
- **Research tie-in.** 06.10 Cobblestone (divide and conquer on verified partial proofs) and 01.12 HyperTree Proof Search (search over goal hypertrees): the two search shapes Lab α's engine interpolates between.
- **Hours.** 786 min (13.1 h), D/V/py 35/35/30. Itemized [A]: *practice* setup 10, test-out 10, read 65, worked 30, cards 6, predicts 20, holes 40, doors + trace 25, extractor 80, loop 20, profiler 25, paper 30, viva 30, calib 5 (= 396); *Lab α* 390 (§4.3).
- **Coverage.** S9 cli-doors-and-exit-codes, json-verdict-channels, lsp-and-dafny-server (d; gap: R reads a trace), pinned-wrapper-and-fast-channel, verdict-loop-client (py); S12 matched-compute-search (py), agent-output-is-data; S13 eval-reporting-and-disclosure, pre-registration-and-budgets, paper-cards.

#### R13 — Pipelines and trust
- **Why.** Stage attribution, and the trust story without a kernel: an untrusted front end (any AI agent included) vs what is actually checked.
- **Core payload.** The stages of each tool (parse, resolve, translate, verify, compile; Verus's later passes) and attributing a failure to its stage (`--log` [verify]); the trusted computing base when there is no small kernel; build-tool poisoning (`build.rs`, `.cargo/config.toml`, `dfyconfig` options); **forensics on the R half** of the G/V cheat corpus (design §9.2 item 2); `research/TRUST.md` section **R-v0**.
- **Diagrams.** Each tool's pipeline with the stage each fake green exploits; the TCB onion (verifier, solver, compiler, build tool, harness, agent).
- **Written track.** The card; **stage attribution** from `--log` output (which stage, which evidence).
- **Exercises.** Stage-attribution items; the forensic deliveries of the R half, each diagnosed by ≥ 2 instruments with no false accusation; `TRUST.md` R-v0.
- **Agentic role.** Rung 11, **pipeline forensic**.
- **Whispers.** Plants: the R half's classes (→ R16's trust-report and Lab γ). Harvests: R01's later-stage failures, R04's `expect`, R07's library TCB, R11's certificates.
- **Research tie-in.** 12.3 *Verification abundance, adjudication scarcity*: free checking moves the burden to deciding what a statement means; R13 locates where the checking actually happens.
- **Hours.** 390 min (6.5 h), D/V 50/50. Itemized [A]: setup 8, test-out 10, read 60, worked 25, cards 8, predicts 15, holes 60, stage attribution 30, forensics 60, `TRUST.md` R-v0 20, agent 25, paper 30, viva 30, calib 9.
- **Coverage.** S10 pipeline-stages, trusted-computing-base, fake-green-forensics, build-tool-poisoning, trust-ledger; S12 gate-design (gap: Q's gate is Python, R's Rust, W11).

#### R14 — SMT mechanics
- **Why.** Write your own automation and audit it: triggers, matching loops and fuel on R's own definitions, and stability.
- **Core payload.** Triggers on split existentials (the `Cat`/`Star` cases of `Matches`, studied on R14's own variants of the definition: A1 states its triggers, so no R14 prediction asks which ones A1 needs, §2.4 F5); matching loops over concatenation; fuel on `Matches` (`{:fuel}` \| `reveal_with_fuel`); resource limits and seeds; brittleness and stability (CV sweeps over seeds); nonlinear and bit-vector reasoning where counted repetition needs it; proof splitting and isolation; the **toolsmith** run: `trigscan` [verify] (`tools/R14/trigscan.py`), one automation that closes a 12-assertion battery, all 12 audited by the learner.
- **Diagrams.** A matching loop as a graph of instantiations; fuel as unfolding depth; a CV sweep's distribution.
- **Written track.** The card; **CV sweep analysis** (what the sweep licenses about stability, and what it does not).
- **Exercises.** The 12-assertion battery; trigger repairs; fuel items; CV sweeps.
- **Agentic role.** Rung 12, **toolsmith** (`trigscan`).
- **Whispers.** Plants: stability (→ R16's 3-seed gate). Harvests: R02's split existential and termination pair, R05's variance.
- **Research tie-in.** 02.5 Schwarz: solver-aware agents shown the failed SMT obligation; `trigscan` is a solver-aware tool built by hand.
- **Hours.** 390 min (6.5 h), D/V 45/55. Itemized [A]: setup 10, read 60, worked 25, cards 8, predicts 20, holes 70, battery 60, CV sweeps 40, toolsmith 30, paper 30, viva 30, calib 7.
- **Coverage.** S2 quantified-specs; S4 fuel-and-unfolding; S11 triggers-and-matching-loops, resource-limits-and-verdict-kinds, brittleness-and-stability, nonlinear-and-bit-vector-reasoning, proof-splitting-and-isolation.

#### R15 — Verifier loop + Lab β
- **Why.** The thesis: the escalation ladder (run → executable checks → property testing → proof → audit), statement review as the irreducible human job, grading the grader, and the second lab, on spec quality.
- **Core payload.** The ladder with property tests against the Rust `regex` crate as a differential oracle for whole-string matching [verify] (a dev-dependency outside `verus!`); statement review; **grade-the-grader** (fresh `/grade-paper` passes on a flawed fixture); grader injection (a hostile string inside an artifact); contamination control (post-cutoff authorship, novelty review, perturbation probes, in-context isolation; design §10.3, +0.25 h); the red-teamed contract and **R-v1**; Lab β (§4.3).
- **Diagrams.** The escalation ladder with what each rung can catch; the two oracles of Lab β and the confusion matrix against hidden verdicts.
- **Written track.** The two cards; **grade-the-grader**; **injection** (find and explain it); **Lab β's pre-registration**.
- **Exercises.** The ladder on `rexc`'s matcher; statement-review items; `spectest` and `roundtrip` (`harness/r/fvh_r/`).
- **Agentic role.** Rung 9, **red-teamed contractor** → contract **R-v1**; **experimental subject** (Lab β).
- **Whispers.** Plants: the oracles (→ R16's capstone review). Harvests: R04's mutant kill and anchoring, R09's fidelity, R12's extractor.
- **Research tie-in.** 03.10 roundtrip verification and repair for faithful autoformalization, and 05.2 *Faults in Our Formal Benchmarking*: Lab β builds the first and audits its own cards for the second's defects.
- **Hours.** 744 min (12.4 h), D/V/py 45/45/10. Itemized [A]: *practice* setup 8, test-out 10, read 70, worked 25, cards 6, predicts 15, escalation ladder 70, statement review 30, grade-the-grader 20, injection 15, contamination 15, red-team + R-v1 30, paper 30, viva 30, calib 10 (= 384); *Lab β* 360 (§4.3).
- **Coverage.** S12 contract-and-allowlists, escalation-ladder-with-property-testing, grade-the-grader, frozen-statements-and-review; S13 pre-registration-and-budgets, spec-quality-oracles, prose-to-spec, contamination-control, vericoding-self-spec, reward-and-bench-audits.

#### R16 — Capstone + Lab γ
- **Why.** Compiler correctness by a generalized simulation **discovered on paper**; a verified optimizer; an adversarial round; ship a CLI; the blueprint gate; and the third lab, on grader inflation.
- **Core payload.** Compile `Re` to a Pike-style VM (`Char`/`Split`/`Jmp`/`Match`, A5); code-at-offset simulation **generalized over the continuation** (the generalization found on paper first; X1's pre-empted insight stays new for `Split`'s nondeterminism); **jump threading** as the verified optimizer; ship `rexc` (CLI, error positions from R09, the Dafny mirror); the Rust gate `rexc trust-report` (PASS/FAIL/UNKNOWN; a solo path, rule 2s, layout DVR3's) built from R13's forensics, R15's ladder and the R half of the corpus; `TRUST.md` final, contract **R-v2**; the research card and a one-page memo; Lab γ (§4.3). Spike S3 closed: the VM's soundness and completeness hold for nullable `Star` bodies and backward jumps, so no fallback restricts the capstone.
- **Diagrams.** The code layout of a compiled `Star`; the simulation relation between `Matches` and the VM with the continuation; the trust-report's flow; Lab γ's inflation per class.
- **Written track.** The two cards; **the blueprint** (graded ≥ 3 before formalization, design §7.1 hard-tier rule); **Lab γ's pre-registration**; the memo.
- **Exercises.** Frozen statements with a statement-only review; the emitter's soundness and completeness proofs (two items per language, with A5's layout and one-step lemmas given, so that each item fits the hard band); jump threading (gated); the plant; `rexc`; the trust-report.
- **Agentic role.** Rung 14, **reviewer → co-developer → adversary**; **experimental subject** (Lab γ).
- **Whispers.** Harvests everything: R06's generalization and matcher, R08's interface, R09's positions and port, R10's normal forms, R11's certificates, R13's forensics, R14's stability, R15's oracles and R-v1.
- **Research tie-in.** 07.3 *Inductive Deductive Synthesis* (implementation and proof grown together, stalled designs discarded) and 12.9 the AI-scientist survey's verification gap: R16 ships a system and a claim that an outside checker can re-run.
- **Hours.** 936 min (15.6 h), D/V 30/70. Itemized [A]: *capstone* setup 8, test-out 10, read 70, blueprint 45, statements 40, proofs 180 (soundness and completeness, D and V, 4 × 45), jump threading 70 (gated: its language-preservation proof was never attempted; 0 until a DVR3 spike admits it or a fallback with its four results takes the minutes), co-developer round 40, adversarial plant 30, ship `rexc` 40, card + memo 45, R-v2 + `TRUST.md` 25, `/review-code` 20, viva 30, calib 13 (= 666); *Lab γ* 270 (§4.3).
- **Coverage.** S10 fake-green-forensics, build-tool-poisoning, trust-ledger; S11 brittleness-and-stability; S12 contract-and-allowlists, gate-design (gap: W11), frozen-statements-and-review; S13 pre-registration-and-budgets, research-framing, grader-inflation.

---

## 4. The agentic ladder, the contracts and the labs

### 4.1 R's ladder (design §12; spec §5.1)

| rung | role | R home | object (disjoint from Q's) | contract in force |
|---|---|---|---|---|
| 1 | repairer + three doors | R01 | planted errors in R01's midpoint and string-counting code | fallback rules (`.claude/skills/contract/SKILL.md`), plus any written Q-vN (D3) |
| 3 | contract v0 by hand | R01 | `CLAUDE.md` `### R-v0 — R01`, from the R01 transcript | — (written, not run) |
| 2 | implementer vs checks | R02, R03 | `Re` definitions; the class API | R-v0 |
| 6 | audited prover | R04, R05 | witness lemmas; `Star` lemmas under fast-channel-only rules | R-v0 |
| decomposer | top statement only | R06 | the reversal theorem (Verus side pending spike S1) | R-v0 |
| 4 | retriever race | R07 | library goals | R-v0 |
| 5 | infra debugger (semantic) | R08 | a refinement that fails semantically | R-v0 |
| 7 | refactorer under harness | R09 | the parser port | R-v0 |
| 8 | spec-to-proof flagship | R10 | smart constructors | R-v0 |
| 13 | metatheory contractor | R11 | derivation rules | R-v0 |
| 10 | toolwright | R12 | the profiler | R-v0 |
| 11 | pipeline forensic | R13 | the R half's deliveries | R-v0 |
| 12 | toolsmith | R14 | `trigscan` and the battery | R-v0 |
| 9 | red-teamed contractor | R15 | `rexc`'s matcher under a hostile brief | R-v0 → **R-v1** |
| 14 | reviewer → co-developer → adversary | R16 | the capstone | R-v1 → **R-v2** |
| subject | headless `fvh` runs | R12, R15, R16 | the labs' tasks | the lab's pre-registration |

Contracts keep three keys (`goal:`, `allowed-files:`, `acceptance:`; spec §3.11.2); allowlist lines come only from the module's own `agentic` list, so an R contract never unlocks a Q file; `instructor/` writes are denied while any allowlist is non-empty (rule 2c). The contract block in `CLAUDE.md` is shared (D3): every written Q-vN and R-vN section binds every `/contract` session, the stricter rule winning. Agent output is data (N2): it is never merged except through interactive `/contract` edits under the hooks.

### 4.2 Standards documents (D3)

`research/EVAL.md` gains its **R-v0** section at R07; `research/TRUST.md` its **R-v0** at R13; both reach their R finals at R16. Each R section is the learner's, under its own heading beside the Q sections.

### 4.3 The labs (design §11.3): complementary and standalone

Every lab has a pre-registration problem in its written pair; a run unlocks only when `/grade-paper` scores ≥ 3 on every method dimension, and `fvh` refuses a run without the committed hash. Grading is on method and reproducibility, never on matching numbers; reports disclose that Claude is both grader and subject. One Claude final arm per lab on a pre-registered, seeded, language-stratified subset of at most 20 tasks, descriptive ("repeated runs", never "seeds"); multi-arm comparisons on Qwen with real seeds, pre-registered per arm.

**The pre-registration's fields (all three labs):** claim; metric and estimator; **budget arithmetic** (calls = tasks × attempts × rounds × arms × repeats, per arm, plus Δ148's sentinel calls); **generation settings** (the values the Ollama gate pins for every Qwen call: thinking on or off, `num_predict`, `num_ctx`, temperature, and the seed list per arm; for Claude the pinned argv); **cost per arm** (tokens in and out, GPU-seconds, wall clock); GPU-h against the registry's ceiling, redone per arm from DV4 step 3d's throughput probe; the **truncation rate** (attempts cut at `num_predict`) as a sensitivity line; MDE; cheat surface and gate; `firsttry` intervals; stopping rule; and the pre-registered fallback if step 3d's throughput puts the plan over its GPU ceiling.

| lab | module | question | you build | minutes | data [A] | statistics |
|---|---|---|---|---|---|---|
| **α** | R12 | where do the three regimes' success-vs-budget curves cross, and does obligation-localized feedback beat raw verifier text? | a hint-site environment over frozen specs and **one parametric engine** whose (width, depth, priority) settings give all three regimes at equal node budget (`engine.py`) | environment 60, engine 90, pre-registration 40, `/grade-paper` 10, setup 25, analysis 75, transcript audit 20, `--post` 10, report 50, calib 10 = **390** | 40 `bench/local/r` tasks (20 per language) + an unused public slice | paired permutation tests per budget point with Holm; clustered bootstrap bands; re-judged by `vcheck --gate`/`vaudit`/`specfreeze` |
| **β** | R15 | do two independent oracles agree, with each other and with hidden verdicts, and how often is "verified" also "faithful", D vs V? | `spectest` (soundness on reference I/O, completeness against mutated outputs) and `roundtrip` (spec → NL → spec, equivalence verified both ways) | spectest 75, roundtrip 65, pre-registration 35, `/grade-paper` 10, setup 20, analysis 60, card contamination audit 30, `--post` 10, report 45, calib 10 = **360** | 24 R cards × 4 specification variants, verdicts in `Hidden/labs/R15/` | confusion matrix, κ, verified-but-unfaithful rate |
| **γ** | R16 | what fraction of naive-grader successes (exit code, `cargo build`/`test`, a "verified" substring, one seed, `--allow-warnings`) survive your gate, by cheat class? | `rexc trust-report` from R13's forensics, R15's ladder and the R half of the corpus | pre-registration + budget 30, `/grade-paper` 10, gate 90, naive graders 20, setup 20, analysis 50, report 40, calib 10 = **270** | every α/β success + 12 crate tasks (8 possible, 4 impossible) | inflation per class with CIs |

**Budget arithmetic** (proposed; the GPU figures use QPLAN §22.6's working assumption of about 7.3 s per Qwen call at `num_predict` 768 [A], which DV4 step 3d replaces):

| lab | part | arithmetic | runs · calls |
|---|---|---|---|
| α | Qwen arms | 40 tasks × 1 attempt × B = 10 node calls × 4 arms (the three regimes on obligation-localized feedback, plus best-first on raw verifier text) × 3 repeats | 480 runs · 4,800 calls (≈ 9.7 GPU-h) |
| α | Claude arm | 10 tasks (5 per language, seeded subset) × 10 × 1 arm (best-first, obligation feedback) × 1 | 10 runs · 100 calls |
| α | Claude sentinels | Δ148 | ≤ 10 calls |
| β | Qwen deliveries | 24 cards × 1 attempt × 4 rounds (verifier feedback only) × 1 arm × 8 repeats | 192 runs · 768 calls |
| β | Qwen `roundtrip` oracle | 24 cards × 4 variants × 2 calls (spec → NL, NL → spec) × 1 | 96 runs · 192 calls |
| β | Claude deliveries | 20 cards × 1 × 4 rounds × 1 arm × 1 | 20 runs · 80 calls |
| β | Claude sentinels | Δ148 | ≤ 10 calls |
| γ | Claude (harness-executed, DV4 §3.5) | 12 tasks × 1 attempt × ≤ 25 rounds × 1 arm × 2 repeated runs | 24 runs · ≤ 600 calls |
| γ | Claude sentinels | Δ148 | ≤ 10 calls |
| γ | Qwen (agent mode, opencode in a per-run container) | 12 tasks × 1 × ≤ 40 turns × 1 arm × 3 repeats | 36 runs · ≤ 1,440 calls (≈ 15 min per run [A] → 9 GPU-h) |

Lab α's budget points 1–10 are read as prefixes of each run: each regime's (width, depth, priority) settings are fixed independently of the budget, so the first *b* calls of a run are that regime's run at budget *b* (pre-registered; a regime whose settings depend on the budget runs once per budget point instead). Lab β's Qwen GPU is ≈ 960 × 7.3 s ≈ 2 GPU-h. Pre-registered fallbacks if step 3d's throughput is lower: α two repeats (3,200 calls), β four delivery repeats, γ two Qwen repeats.

**Registry budgets** (Δ73, Δ75; `fvh` enforces them). DV1a's values left R12's and R15's run counts and R16's call counts at 0, budgeted no sentinel, and put Lab α at 5,120 Qwen calls (≈ 10.4 GPU-h at the assumption above, over Δ75's 10). Proposed, through the records entry that carries QPLAN §30 Q55:

| module | `claude_calls` | `claude_runs` | `qwen_calls` | `qwen_runs` | `gpu_hours` |
|---|---|---|---|---|---|
| R12 | 110 | 10 | 4800 | 480 | 10 |
| R15 | 90 | 20 | 960 | 288 | 3 |
| R16 | 610 | 24 | 1440 | 36 | 9 |

The GPU split is Δ75's (45 over the registry). Claude over the six labs: Q 180 + 90 + 610 = 880 (QPLAN §30 Q55) and R 110 + 90 + 610 = 810, so 1,690 calls with every sentinel, inside design D8's ≈ 1,700. Lab α's Claude arm shrinks from the design's 160 calls on 20 tasks to 100 on 10 for that reason, and Lab α's Qwen work from 5,120 to 4,800 calls: both need a DELTAS entry against design §11.3 (§8 R17).

**Decided** (Δ176): the three budgets above are in `MODULES.toml`, with QPLAN §30 Q55's for Q12, Q15 and Q18; Lab α is cut to 4,800 Qwen calls and 100 Claude calls plus 10 sentinels, which amends design §11.3.

**Validity rules.**
- **α's tasks.** A task form enters only if its empty body fails under maximal automation in its shipped options (§0's four results), and the lab gate refuses a delivery that adds a lever attribute (`{:induction …}`, `{:fuel …}`, a resource-limit or a solver option) that the task form does not ship. The Claude subset is drawn by a pre-registered seed, stratified by language; Qwen seeds per arm are pre-registered and disjoint between arms.
- **β's hidden truth stays out of every loop.** The delivery loops see verifier output only; `spectest`, `roundtrip` and the comparison with `Hidden/labs/R15/` run after the batch, the hidden comparison only in the grader container. `roundtrip` uses the pinned Qwen model and is counted above; Claude never judges in it.
- **γ's tasks avoid the capstone's statements.** The crate tasks are built over `rexc`'s parser, character classes, printer and CLI (layers and modules whose statements are frozen before R16), never over the emitter, the simulation or jump threading, whose statements R16 asks the learner to write; and `fvh` refuses to unpack `bench/local/r/crate/` before the sha256 of the learner's R16 statement file is committed (the `statements` pin). Their 4 impossible tasks are of kinds that QPLAN's Lab 3 does not use (the author notes name them).
- **CI never calls a model.** `fvh_r`'s frozen acceptance tests (extractor, loop, engine, `spectest`, `roundtrip`) run only on the `Mock`, `Scripted` and `Replay` policies; a test that needs model output replays a recorded one.

**What the labs rely on, and what is not built yet.** The labs use DV4's pieces through `fvh_r`, against the stable interfaces of DV4-PLAN §13 (`fvh.protocol`'s types and `ACTION_SCHEMA`, the `Policy` signature, `fvh.verdicts`, `fvh.corpus`'s `load_half`, `fvh.tools`' `run`/`replay` and the provenance rule, `RunMeta` and the run directory, the ledger anchors, `scripts/mksandbox-run`'s manifest schema 1, `bench/manifest.toml`). Docker is not available yet (host action H1), so every container step is **designed against those interfaces and needs DV4 steps 2–3**: the verification container (step 2b) for every re-judgement; Qwen policy runs on the host need step 3c, Qwen agent runs (R16) step 3a, and the throughput probe that fixes the GPU arithmetic step 3d; Claude policy runs need step 4a and harness-executed runs step 4b; Claude agent mode at R16 needs step 4c's decision (with the user present), and harness-executed runs remain the default without it. Hidden truth (Lab β) needs the grader container DV5 or DV7 builds on DV4-PLAN §5.9. Nothing in band 1 needs Docker.

---
## 5. Disjointness between the tracks (design §9; spec §2.7)

The tracks may not share an artifact (clause a), may not hold a solution that transfers by renaming (clause b), and narrow every shared payload genre to an explicit waiver with its cost (clause c). On a collision, the side that left `planned` later changes, which in practice is R.

### 5.1 Owner tags

| owner | surprises it alone may pose as predictions | how the other track treats them |
|---|---|---|
| **Q** | `nat` vs `u64` minus; hole visibility (which tool reports which hole, and how); proved vs computed; auto-induction | R states each as a fact and exercises it with a hole: hole visibility in R01's hole contract (the census, R01.T1d/T1v); auto-induction in R06 (its card C5d and the `{:induction false}` items H1d and X1d); proved vs computed and machine subtraction in R01's chapter. Also Q's by its homes, so R poses none of them as predictions: the error count of a run with several failing assertions (Q03.P6dv, Q04.P3dv, Q07.P7d), `assert … by` scoping (Q02.P8dv), resource-limit verdicts (Q06.P2dv) and seeds (Q09.P2dv); R's chapters state them |
| **R** | `midpoint` overflow; `expect` outside tests; a strengthened `requires`; the empty-string and anchoring surprises; later-stage failures | Q poses none of them as a prediction. A check of QPLAN's Q01–Q09 predictions found one boundary case: Q08.P1dv asks whether a refinement may strengthen a frozen statement's `requires` (the legality of a refinement), while R03.P1d/P2v ask where an API's strengthened `requires` shows up at its call sites; the two are recorded as distinct (§8 R9). Q06's `mid` is a card demo of opacity, not an overflow prediction. **The same check against Q10–Q18** (QPLAN §20–§28, as revised in this round): Q12's stage specimens stay within Q's own tags (Δ181). Q13.P1dv (which clients verify under two postconditions of different strength) and R01.P3d/P4v (which asserts a caller can prove from a contract alone) share the call-site reading of a contract, but Q13's question is spec strength and R01's is body opacity: recorded as distinct, like §8 R9. Q15.P1d (a hole's per-symbol status in the language server) is Q's hole visibility. No other Q10–Q18 prediction poses an R-owned surprise |

A learner who does R before Q meets Q's surprises as facts; their Q first tries are then informed, and the Q gradebook records the first try as it happens (an accepted cost of standalone tracks, decision 1).

### 5.2 Specimen halves and paper cards

- **The G/V cheat corpus** splits into a **Q09 half** and an **R13 half**; in each language each half covers all 14 of that language's X families (Δ108, Δ109), and the manifest's `half` field assigns each fixture. R13's forensics, R16's trust-report and Lab γ use only the R half (`fvh.corpus.load_half(lang, "R")`); the grader-only classes on which a gate must say UNKNOWN are shared by construction and named in `fvh.verdicts.GRADER_ONLY`. Which fixtures form the R half is DVR3's (Δ108 open item).
- **Paper cards are never shared or repeated**: each `cheatsheets.md` id appears in exactly one registry record (the checker enforces uniqueness, Δ73). R's cards are 12.11, 05.6, 03.2, 12.5, 06.3, 03.4, 06.5, 06.7, 06.11, 03.5, 12.10, 06.10 + 01.12, 12.3, 02.5, 03.10 + 05.2, 07.3 + 12.9.

### 5.3 Artifacts, statistics and CI

- **Artifacts.** Q alone has BigNat, the ring buffer, the priority queue, the decimal parser and a While language with a verified wp; R alone has the regex AST, matchers, character classes, derivatives, derivations and the VM; Q29 is a register machine; **no expression-language compiler appears anywhere in this course** (the Lean course's R track owns that artifact; design D7).
- **Statistics code** exists only in the frozen `fvh` core (`fvh.stats`): R05's variance code composes `fvh.stats.bootstrap_ci` and the standard library's `statistics`; R07's pass@k by hand composes `fvh.stats.pass_at_k`; no learner file of either track implements an estimator.
- **CI isolation** runs both ways: no R file imports a Q file, layer, `fvh_q` or `bench/local/q`, and no Q file imports an R one (`scripts/check_course_map.py`, isolation group; `scripts/ci.sh` builds the two tracks separately and together).

### 5.4 Waivers (D3: all accepted, one shared file per standards document)

Each cost names the insight pre-empted for a learner who does the Q home first; R repeats the genre on its own objects. The R home's test-out (§1.4) is where a Q-credit learner can recover the time.

| waiver | genre: Q home → R home | pre-empted insight (the cost) | R's own objects |
|---|---|---|---|
| W1 | role ladder: Q01–Q18 → R01–R16 | each role's first failure mode (gaming checks, weakening statements) | every rung on the regex artifact, harder objects |
| W2 | hole contract, doors: Q01 → R01 | silent vs loud holes (≈ 1.2 h of R01 becomes test-out) | R01's census and repair files |
| W3 | contract, `EVAL.md`, `TRUST.md` → their `R-vN` sections | that unenforced contract rules are suggestions | R-v0 (R01), R-v1 (R15), R-v2 (R16); `EVAL.md` R-v0 (R07); `TRUST.md` R-v0 (R13) |
| W4 | port + fidelity: Q07 → R09 | that implication lemmas alone are circular | the parser port |
| W5 | wp/VC by hand → R04, R06, R11 | the wp calculus itself (≈ 30 min of R11 is review) | the matcher loop's VCs |
| W6 | permissions: Q08–Q17 → R11, gated | the linearity error | the NFA arena (gated) |
| W7 | invariant generalization: Q13, Q16 → R06's matcher loop | "generalize the invariant before proving" | the derivative matcher |
| W8 | agent loop: Q12's retry client → R12's obligation loop | that a verdict loop needs a parser before a model | the obligation extractor |
| W9 | matched compute: Q12 → Lab α | compare at equal calls, not equal attempts (curve crossings stay new) | one parametric engine, three regimes |
| W10 | spec oracles: Q15 → Lab β | vacuous specs pass verification; mutation kill measures strength (oracle agreement stays new) | `spectest`, `roundtrip` on R cards |
| W11 | gate: Q09/Q18 Python → R16 Rust | fresh-process pinned re-runs (V20) and UNKNOWN on grader-only classes (inflation stays new) | `rexc trust-report` |
| W12 | framing: Q18 proposal → R16 card + memo | scoping a claim to a small-n replication | the capstone's memo |
| W13 | R pre-empting Q32/Q33 | R12/R15 code may make the solo Q32/Q33 start easier (avoided under D2's default order: the agentic topic before the R core) | — |
| W14 | parse with errors: Q05 → R09 | `:-`/`?` propagation (positions and fidelity stay new) | the regex-syntax parser |
| X1 (cross-course) | compiler correctness by generalized simulation: Lean R16 → R16 | "generalize over the code that follows" (nondeterministic `Split` stays new) | the VM compiler |

**Proposed waivers** (plan review; they go through the records lane into design §9.3 and `avoid.waivers.tsv`; until adopted, each genre's R home is marked pending in DVR1's or DVR2's records):

| waiver | genre: Q home → R home | pre-empted insight (the cost) | R's own objects |
|---|---|---|---|
| W15 | stage attribution: Q03.P6dv, Q12's stage specimens → R13 | that a failure's stage is read from the tool's own stage report, not guessed from the message (what each stage's fake green exploits stays new) | R13's `--log` evidence on the regex pipeline |
| W16 | refute → repair → prove: Q15.H2d/H2v ("smallest change") → R06.H3/H4 ("no stronger one") | that the repair is derived from the counterexample, not chosen to make the proof easy | a claim about `Star` and `Cat` (R06's own) |
| W17 | possible and impossible crate tasks as cheat attractors: Q18's Lab 3 → Lab γ | that an impossible task turns every claimed success into evidence of a cheat (inflation per class stays new) | `rexc`'s parser, classes, printer and CLI; impossible kinds Q does not use (§4.3) |
| W18 | card contamination audit: Q15's Lab 2 pre-registration → Lab β | post-cutoff authorship, novelty review and perturbation probes as controls | the 24 R cards, audited against 05.2's defect list |
| ~~W19~~ (dropped, Δ211) | a tracked `Map<int, PointsTo<_>>` with take/put: Q14.H5v, Q17.H2v → R11 (gated) | moving one permission out of a tracked map and back (beyond W6's linearity error) | the NFA arena of `Inst` cells and `arena_match`; needed only if the Q lane keeps a map arena (the review's alternative: Q14.H5v as a `PPtr` list that passes one permission per node) |

**Decided** (Δ177): W15–W18 are adopted into design §9.3 and `avoid.waivers.tsv`, so their R homes are no longer pending on a waiver. W19 is **provisional**: DV5 diversifies the Q side instead (separate tracked fields per slot for Q17.H2v, or Q14.H5v as a `PPtr` list) if the alternative probes in band, and W19 is then dropped; until DV5 records that, W19 stands as written. **Dropped** (DV5c, DELTAS Δ211): Q14.H5v passes one permission per node and Q17.H2v borrows each slot's permission in place from a tracked sequence, so no Q item moves a permission out of a tracked map and back; R11's arena keeps the genre new.

**No waiver is needed** where the artifacts differ: LSP-by-hand is Q-only (R12 reads a captured trace); the toolwright tools (`holecount` vs the profiler); the library lab (Q04's vs R07's objects); the forensic halves; the tutor red-team (Q15) vs grader injection (R15). The earlier draft's deep-evaluator waiver is dropped (an avoided overlap). **Waiver file:** `avoid.waivers.tsv` at the repo root of the checker's inputs (DVR0 names its path), one line per waiver with the columns of §5.5.

### 5.5 The `avoid.sh` contract (DVR0 builds it; spec §2.7, design §9.1)

**Purpose.** A symmetric name-level tripwire for clauses (a) and (b): it finds every place where one track's learner-facing material reuses a name the other track (or the Lean course) poses or answers. Shape overlaps that a name scan cannot see are listed as waivers (§5.4), never claimed as caught.

**Usage.** `scripts/avoid.sh [--track Q|R|both] [--json] [--list-sources]`; default `both`. Exit 0: no unwaived hit and no stale waiver; 1: a hit or a stale waiver (each printed as `<key> <track>:<file>:<line> ↔ <source>`); 2: a malformed input (a waiver line, an unreadable source); 3: a usage error. `scripts/ci.sh` runs it as a job (Δ104 lists it as pending until DVR0). It reads only learner-visible files of this repo plus the curated list: never `Solutions/`, never another course's reference tree, never a held-out file.

**Sources, per track** (the avoid list is **regenerated on every run and never committed**):
1. every **hole-bodied declaration** in the other track's exercise, check, exit and agent files: holes found through `scripts/course_items.py` and the tools' hole counters (Dafny bodyless lemma or function, `assume false` body; Verus `proof_note` assume, `external_body` + `unimplemented!()`, `uninterp spec fn`; Python `raise NotImplementedError`), never by grep alone;
2. every **parallel problem** in the other track's banks (`.claude/skills/instructor/banks/<ID>.md`);
3. every **problem** in the other track's written problems (`paper/<ID>_problems.tex`);
4. every declaration name in the other track's **chapter code fences** (`docs/<ID>_*.md`);
5. a committed **curated list** (`scripts/avoid.curated`): Lean Q's spine identifiers and Lean R's exercise names, taken from the Lean course's exercise files only (never its solutions), plus `!never-reference` names.

**Keys and matching.** A key is a declaration name from any of the three languages (Dafny `lemma`/`function`/`predicate`/`method`/`datatype`/constructors; Rust `fn`/`struct`/`enum`/`trait`/variants; Python `def`/`class`), **namespace- and prefix-stripped** (module prefixes `Q0n_`/`R0n_`, layer prefixes `QG_L<k>_`/`RG_A<k>_`, qualified paths, and the Verus `lemma_`/`proof_` and Dafny `Lemma` affixes), then **normalized**: camelCase and snake_case split into words, lower-cased and joined with `_` (`NodeCount` = `node_count`). A hit is: (i) an equal key; (ii) a curated **type** name occurring as a word of a key (`Tree`, `Expr`, `Bin`); (iii) an equal syntax token of a `!never-reference` name anywhere in the file. **Self-check, no waivers:** each track's bank parallel problems against its own exercises.

**Waivers.** `<key>\t<source>\t<reason>\t<direction Q→R|R→Q|Lean→R>\t<cost>`; a waiver that matches no hit is an error ("stale, like a stale pin"). The design's W1–W14 and X1 are genre waivers: most need no name line, and DVR0's baseline run records which do.

**Baseline (DVR0).** Run it over Q01–Q09 as armed and R's planned names (this plan's §2 and §6, as marker stubs in a scratch copy). This plan already applied the renames a first scan by hand found: design §8.2's `Size` → `NodeCount` (Q has `Size`/`size`, Lean R has `size`); `Rev` → `Backwards` (Q has `Rev`, `RevRev`, `RevAppend`); a string reversal named `Reverse` → `BackwardsStr` (Lean R has `reverse`, `reverse_append`, `reverse_reverse`); and R01 avoids digits and decimal parsing (Q's decimal parser, design §9.2 item 3). DVR0's spike files still use the design's names; the rename list for them is in the plan lane's note under `Solutions/spikes/regex/`. **Added by the plan review:**
- **Lean R07–R16.** A hand scan of the declaration names in the Lean course's R07–R16 exercise files (names only, never a solution) hits three A5 names of the design: `Step` (Lean R11's step relation), `Compile` and `CompileCorrect` (Lean R16's `compile`, `compile_correct`, `compile_correct_gen`). A5 renames them `Advance`, `Emit`, `EmitCorrect` (with `EmitSound`, `EmitComplete`, `EmitProg`; Verus `emit`, `emit_into`, `emit_prog`), §2.2. `Inst`, `Accepts`, `Thread`, `CodeAt` and `Prog` hit nothing (Lean R16's instruction type is `Instr`, a different key). The curated list gains Lean R07–R16's exercise names, and the baseline run confirms or extends this.
- **Decimal parsing.** R09's counted repetition takes single-digit bounds, so no R file holds a decimal digit-run parser: an overflow-checked decimal parser is Q05.H5v's answer (`parse_decimal` over the given `digit` and `mul10_add`), and the spike's `parse_num` (checked `u32` arithmetic, `Overflow` at the reported digit) was that answer with the names changed (clause b). Shipping it as given A3 code would instead put Q05.H5v's answer in a learner-visible R file (§2.1 rule 4), so that option is rejected. The spike's `IsDigit`, `DecVal`, `DigitEnd` and `ParseNum` leave A3 with it (§2.5).
- **Layer prefixes.** The prefix stripping accepts `RG_A1b_` (§2.3).

---
## 6. Band 1 item plans (R01–R06; DVR1)

**Conventions band 1 adds to §0.** (1) Every module's done line: `scripts/vcheck --gate` exits 0 with zero tool-counted holes on each of its units, every slot is filled and its first try recorded (`scripts/firsttry.sh <ID> --check`), and (R05) the Python file has zero holes with its acceptance tests green. (2) An item whose statement is open in the freeze pin (the learner writes part of the statement, Δ160) says so in its form column. (3) Annotation holes follow `QPLAN.md` §0 and §8.0: the code given, the annotations the item names missing, one `assume false;` (Dafny) or one labelled `assume(false)` (Verus) as the first statement. (4) **pending spike** marks an item whose band, gate result or statement still waits for a spike (after DVR0's lanes: only R06.A1v, §2.2); **gate pending** marks an item whose reference exists in a spike or in the author notes but whose four results (§0) on the shipped file are DVR1's to record. Minutes in §6 are the plan's; `[module.admissible]` carries them only once the four results are in (§0). (5) Every prediction's answer, every hole's reference, every gate result and every checkpoint statement is in `Solutions/plans/R-author-notes.md`.

### 6.1 R01 — Hello, two verifiers

*No layer, 276 min (viva included). Bank of 12 (minimum 8; two disjoint six-question draws). Agent rung 1: repairer + three doors; rung 3: contract R-v0 by hand. No checkpoint.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| Dafny exercise | `dafny/R/R01_Hello/core/R01_Hello.dfy` (`module R01_Hello`; given in it: `newtype U32 = x: int \| 0 <= x < 0x1_0000_0000`, `function CountChar(s: seq<char>, c: char): nat` with `decreases \|s\|`) | green; **5 holes** (T1d holds 2; H1d–H3d); the prediction block holds the 2 `dv` verdicts |
| Dafny check unit | `dafny/checks/R01_checks.dfy` (`module R01_Checks`) | green; 1 value slot (P5d) |
| Verus crate | `verus/r/r01_hello/src/lib.rs` (crate `r01_hello`; dep `vstd`; given: `pub open spec fn count_char(s: Seq<char>, c: char) -> nat` with `decreases s.len()`) | green; **5 holes** (T1v holds 2; H1v–H3v) |
| prediction specimens | `specimens/R01/P3d.dfy.specimen`, `P4v.rs.specimen` (obligation), `P6v.rs.specimen` (value) | slots unfilled |
| card demos | WRITE (in-file `// EXPECT`): `card-c1d`, `card-c1v`, `card-c2d`, `card-c2v`, `card-c3d`, `card-c3v`. False friends: `card-c8dv-<r>-d.dfy.specimen`, `card-c8dv-<r>-v.rs.specimen`, rows r = 1–6. Divergence: `card-c9dv-d.dfy.specimen`, `card-c9dv-v.rs.specimen` (`// after: R01.P5d` and `// after: R01.P6v`; sealed sidecars) | red by design, pinned |
| slots | `slots/R01.slots`: `P1dv P2dv = ???` | unfilled |
| agent | `dafny/R/R01_Hello/agent/R01_AgentRepair.dfy` (`module R01_AgentRepair`), `verus/r/r01_hello/src/agent.rs` | RED: 4 planted errors each, one diagnostic per bug, no hole |
| pins | `expected/R01.pins`, `expected/R01.counts`, `expected/R01.freeze` (H3d's and H3v's `requires` open, Δ160), `expected/R01_AgentRepair.audit`, `expected/r01_hello_agent.audit`, the sidecars | author-written |
| twins | `Solutions/` mirrors of every exercise, check and agent file, `Solutions/specimens/R01/…`, `Solutions/slots/R01.slots` | hole-free, silent |

Header counts (exercise files and chapter): **10 holes** (5 per language), **6 predictions** (2 verdict lines, 2 obligation specimens, 2 value slots), **2 test-out items**.

#### Items

| id | K | format | pair | uses | statement or prompt (as the learner sees it) | form · lever |
|---|---|---|---|---|---|---|
| R01.T1d | T | — | R01.T1v | ensures, assert, lemma-call | **The hole census**, closed book, before reading: this block holds two declarations whose bodies are holes of two different kinds: `lemma CountCharPair(d: char, e: char, c: char) ensures CountChar([d, e], c) == (if d == c then 1 else 0) + (if e == c then 1 else 0)` and `method CountFirstTwo(s: seq<char>, c: char) returns (n: nat) requires \|s\| >= 2 ensures n == CountChar(s[..2], c)`. Close both, so that `scripts/vcheck --gate` reports no hole in the block; record the first try with `scripts/firsttry.sh R01 --check` | 2 holes (bodyless lemma; exec `{ assume false; }`) · none |
| R01.T1v | T | — | R01.T1d | ensures, assert, lemma-call | the same: `proof fn lemma_count_char_pair(d: char, e: char, c: char) ensures count_char(seq![d, e], c) == (if d == c { 1nat } else { 0nat }) + (if e == c { 1nat } else { 0nat })` and `fn count_first_two(s: &Vec<char>, c: char) -> (n: u32) requires s.len() >= 2 ensures n == count_char(s@.subrange(0, 2), c)` | 2 holes (`proof_note` assume; `external_body` + `unimplemented!()`) · none |
| R01.P1dv | P | verdict | — | — | A midpoint `m := (lo + hi) / 2` under `requires lo <= hi`, `ensures lo <= m <= hi`: Dafny over `int`; Dafny over the course's `U32`; Verus over `u32`. Answer form `D-int:<v> D-u32:<v> V:<v>`, v one of `ok`, `fail`, `timeout`, `err:<stage>` (stage as `scripts/vcheck` prints it) | slot · block |
| R01.P2dv | P | verdict | — | — | A function `HalveEven(n)` with `requires n % 2 == 0` and `ensures` that twice the result is `n`, verified on its own, and a test that calls it on 7 and checks the result: a Dafny `@Test` method; a Verus `#[test]` fn outside `verus!`. What do `scripts/vcheck` and then `scripts/vcheck --test` report? Answer form `D:<v>,<t> V:<v>,<t>`, v as in P1dv, t one of `passed`, `failed`, `not-run` | slot · block |
| R01.P3d | P | obligation | — | — | `specimens/R01/P3d.dfy.specimen`: `method NextUp(x: U32) returns (y: U32) requires x < 100 ensures y > x` with the body `y := x + 1;`, and a caller of `y := NextUp(5);` with four labelled asserts: [a] `y > 5`, [b] `y == 6`, [c] `y >= 6`, [d] `y < 1000`. Which fail? | specimen slot |
| R01.P4v | P | obligation | — | — | `specimens/R01/P4v.rs.specimen`: the same for `fn next_up(x: u32) -> (y: u32) requires x < 100 ensures y > x` | specimen slot |
| R01.P5d | P | value | — | — | `dafny/checks/R01_checks.dfy`: `expect (-7) / 2 == ???;` (compiled and run). Answer form: an integer numeral | check-unit slot |
| R01.P6v | P | value | — | — | `specimens/R01/P6v.rs.specimen`: in a native compiled test, `let q: i32 = -7i32 / 2; assert_eq!(q, ???);`. Answer form: numeral (including a signed integer) | specimen slot |
| R01.W1d | W | — | — | — | `method LastChar(s: seq<char>) returns (c: char) requires \|s\| > 0 ensures c == s[\|s\| - 1]`: a first verified method | given, live |
| R01.W1v | W | — | — | — | `fn last_char(s: &Vec<char>) -> (c: char) requires s.len() > 0 ensures c == s@[s.len() - 1]` | given, live |
| R01.W2d | W | — | — | — | `lemma CountCharBound(s: seq<char>, c: char) ensures CountChar(s, c) <= \|s\|` (`decreases \|s\|`), with an `assert` after each step stating what the verifier knows there: a first lemma | given, live |
| R01.W2v | W | — | — | — | `proof fn lemma_count_char_bound(s: Seq<char>, c: char)` (`decreases s.len()`), the same | given, live |
| R01.C1d / C1v | C | `write:ensures` | — | — | card: `ensures`, a success in the file and a pinned failure demo per language | given |
| R01.C2d / C2v | C | `write:assert` | — | — | card: `assert` | given |
| R01.C3d / C3v | C | `write:lemma-call` | — | — | card: calling a lemma / proof fn | given |
| R01.C4dv | C | `recognise:requires` | — | — | Rosetta card: `requires` | given |
| R01.C5dv | C | `recognise:decreases` | — | — | Rosetta card: an explicit `decreases` in both columns | given |
| R01.C6dv | C | `recognise:function` | — | — | Rosetta card: Dafny `function` / Verus `spec fn` | given |
| R01.C7dv | C | `recognise:forall` | — | — | Rosetta card: a `forall` in a spec | given |
| R01.H1d | H | — | R01.H1v | ensures | `method Midpoint(lo: U32, hi: U32) returns (m: U32) requires lo <= hi ensures lo <= m <= hi && m as int == (lo as int + hi as int) / 2` — implement it | exec hole `{ assume false; }` · none |
| R01.H1v | H | — | R01.H1d | ensures | `pub fn midpoint(lo: u32, hi: u32) -> (m: u32) requires lo <= hi, ensures lo <= m <= hi, m == (lo + hi) / 2` | `external_body` + `unimplemented!()` · none |
| R01.H2d | H | — | R01.H2v | assert, lemma-call | `lemma {:induction false} CountCharAppend(s: seq<char>, t: seq<char>, c: char) ensures CountChar(s + t, c) == CountChar(s, c) + CountChar(t, c)` (`decreases \|s\|`) | bodyless lemma · `{:induction false}` on the lemma |
| R01.H2v | H | — | R01.H2d | assert, lemma-call | `pub proof fn lemma_count_char_append(s: Seq<char>, t: Seq<char>, c: char) ensures count_char(s + t, c) == count_char(s, c) + count_char(t, c)` (`decreases s.len()`) | `proof_note` assume · none |
| R01.H3d | H | — | R01.H3v | requires | `method MeanOfTwo(a: U32, b: U32) returns (m: U32) ensures m as int == (a as int + b as int) / 2` with the body `m := (a + b) / 2;` given, and three given callers on literal arguments (live): write the `requires` that makes the method verify while every given caller still verifies | annotation hole (`requires` open, Δ160) · none |
| R01.H3v | H | — | R01.H3d | requires | the same for `pub fn mean_of_two(a: u32, b: u32) -> (m: u32) ensures m == (a + b) / 2`, body `(a + b) / 2` | annotation hole (`requires` open) · none |
| R01.C8dv | C | `diverge:false-friends` | — | — | the false-friends card (design §6.2 C7): `calc`, `assert`, `forall`, `old`, `decreases`, `==>`, one demo pair per row, on R01's own objects. **Final section** | given |
| R01.C9dv | C | `diverge:r01-c9` | — | — | divergence card (its topic is named in the card). **Final section** | given |
| R01.A1d | A | — | — | — | `/contract R01` on `R01_AgentRepair.dfy`: a repairer fixes 4 planted errors with one-line edits; the learner audits transcript, diff and audit output | contract |
| R01.A1v | A | — | — | — | the same on `verus/r/r01_hello/src/agent.rs` | contract |

**The triage drill** (12 min, prose; a `TRIAGE` comment block at the end of the Dafny exercise file): five recorded outputs of the pinned tools (real outputs, quoted with their recorded run, spec §3.15) to classify by verdict and stage, and for each, what it licenses and what it does not. Advisory: the rubric and the viva read it.

#### Constructs (registry)

- `write_d = write_v = ["ensures", "assert", "lemma-call"]` — 3 paired units, 6 slugs.
- `recognise_d = recognise_v = ["requires", "decreases", "function", "forall"]`.
- Checked uses per slug and language (≥ 2): ensures d T1d, H1d · v T1v, H1v; assert d T1d, H2d · v T1v, H2v; lemma-call d T1d, H2d · v T1v, H2v. RECOGNISE uses: requires d H3d · v H3v.

#### Agentic file (rung 1: repairer + three doors; rung 3: contract R-v0)

- **Shape:** planted-error repair (spec §3.11.1). Each file is RED with exactly **4** documented errors, one diagnostic each, each in its own declaration under a neutral heading `### Bug 1` … `### Bug 4`, over R01's own objects (midpoints and character counts; no digits); doc comments state the intended behaviour; every fix is one line.
- **CONTRACT** (line 1, three keys): `goal:` make the file verify by fixing the four bugs · `allowed-files:` the one agent file of that run · `acceptance:` `scripts/vcheck --gate <file>` exits 0 and prints only the summary line · `git diff` shows only body lines (no `requires`/`ensures`/`decreases`/doc line changed) · every fix is one line · re-verify after every edit, never stacked · zero holes · `scripts/vaudit --compare expected/R01_AgentRepair.audit <file>` (Verus: `expected/r01_hello_agent.audit`) reports no difference.
- **Learner follow-up (agent 15 + doors 10 + R-v0 20 min):** run each file first and read every message; run `/contract R01` in a fresh session; tally the transcript (re-ran after every edit? touched a spec line? reached for an escape hatch?); check `git diff` and the audit yourself. **Three doors:** in a fresh study session, ask the AI for the R01 reference three ways (a file read, a shell command, a language-server lookup) and record which guard layer refuses each (layer-1 deny rule or hook rule, with its id) in the `THREE DOORS` block at the end of the Dafny agent file. **Contract R-v0:** by hand, with no AI session, below the learner-owned marker in `CLAUDE.md` under `### R-v0 — R01`: 3–6 numbered rules, each tied to a moment of the R01 transcripts, and a third-party-checkable "Done means" line (spec §5.2); then classify each rule by what can check it (verifier, audit, reader). R02's contract run is its first live test.

#### Itemized minutes (total 276)

| line | items | min |
|---|---|---|
| setup | `vcheck --selftest`, opening the files | 15 |
| test-out | T1d, T1v (the census, closed book) | 10 |
| read | chapter | 60 |
| worked | W1d–W2v (4 × 3 = 12) + WRITE cards C1d–C3v (6 × 2.5 = 15) | 27 |
| cards | C8dv false friends (6) + C9dv (3) + C4dv–C7dv Rosetta (4 × 1.5 = 6) | 15 |
| predicts | P1dv–P6v (6 × 2.5) | 15 |
| holes | H1d–H3v (6 × 4) | 24 |
| triage drill | the `TRIAGE` block | 12 |
| agent | A1d/A1v audit | 15 |
| three doors | | 10 |
| contract R-v0 | written by hand into `CLAUDE.md` | 20 |
| paper | card 12.11 (the pair holds the card only, Δ74) | 15 |
| viva | `/viva R01`, 6 of 8 questions | 30 |
| calib | CALIBRATION block, `firsttry.sh R01 --record` | 8 |
| **total** | | **276** |

Q-credit test-out (W2, §1.4): with both T items right at the first try, the hole-contract and doors sections (25), the false-friends and Rosetta cards (15), the doors (10), the triage drill (12) and W2d/W2v (10) may be skipped: 72 min.

#### Registry fields (R01, set when armed)

```toml
status = "authoring"
exercises = ["dafny/R/R01_Hello/core/R01_Hello.dfy", "dafny/checks/R01_checks.dfy", "verus/r/r01_hello/src/lib.rs", "specimens/R01/"]
exits = []
agentic = ["dafny/R/R01_Hello/agent/R01_AgentRepair.dfy", "verus/r/r01_hello/src/agent.rs"]
units = ["dafny/R/R01_Hello/core", "verus/r/r01_hello"]
layer = ""
langs = ["d", "v"]
engines = ["contract"]
write_d = ["ensures", "assert", "lemma-call"]
write_v = ["ensures", "assert", "lemma-call"]
recognise_d = ["requires", "decreases", "function", "forall"]
recognise_v = ["requires", "decreases", "function", "forall"]

[module.imports]
"dafny/R/R01_Hello/core/R01_Hello.dfy" = "core"
"dafny/checks/R01_checks.dfy" = "core"
"dafny/R/R01_Hello/agent/R01_AgentRepair.dfy" = "core"
"verus/r/r01_hello/src/lib.rs" = "prelude"
"verus/r/r01_hello/src/agent.rs" = "prelude"
```

---

*DVR1 as-built follow-up (2026-10-17): the planned census fallback uses the two-character lemma, because the original singleton verifies empty. Both code test-outs still contain two holes. Twelve bank questions support two disjoint six-question vivas. All eight hole items pass their shipped/region gates; reference units and agents pass three seeded runs. Live Claude validation is deferred under D45; local CI is tracked separately.*

### 6.2 R02 — Datatypes and recursion

*Layer A1 (declared here), 342 min (viva included). Agent rung 2: implementer vs checks. First `bench/local/r` card.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| given layer | `dafny/given/R/RG_A1_Re.dfy`, crate `verus/given/rg_re_a1` (§2.2) | frozen; declared by R02 |
| Dafny exercise | `dafny/R/R02_Datatypes/core/R02_Datatypes.dfy` (`module R02_Datatypes`, imports `RG_A1_Re`; given in it: `ghost predicate VoidSpec(r: Re)`, the structural "matches no string" test) | green; **5 holes** (H1d–H5d); 1 test-out block (T1d: empty, with one commented check); the prediction block holds the 2 `dv` verdicts |
| Dafny check unit | `dafny/checks/R02_checks.dfy` (`module R02_Checks`, imports `RG_A1_Re`) | green; 1 value slot (P5d) |
| Verus crate | `verus/r/r02_datatypes/src/lib.rs` (crate `r02_datatypes`; deps `vstd`, `rg_re_a1`; given: `pub open spec fn void_spec(r: Re) -> bool`) | green; **5 holes** (H1v–H5v); 1 test-out block (T1v) |
| prediction specimens | `specimens/R02/P1d.dfy.specimen`, `P2v.rs.specimen` (obligation) | slots unfilled |
| card demos | WRITE: `card-c1d` … `card-c3v` (6, in-file `// EXPECT`). Divergence: `card-c7dv-d.dfy.specimen`, `card-c7dv-v.rs.specimen` | red by design, pinned |
| slots | `slots/R02.slots`: `P3dv P4dv = ???` | unfilled |
| agent | `dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy`, `verus/r/r02_datatypes/src/agent.rs` | RED (spec-first): 3 definition holes, a bound-lemma hole per definition (Verus), a live check suite failing over the holes |
| pins, twins | as R01 (`expected/R02.*`, `Solutions/…`) | — |

Header counts: **10 holes**, **2 test-out items**, **5 predictions**.

#### Items

| id | K | format | pair | uses | statement or prompt | form · lever |
|---|---|---|---|---|---|---|
| R02.T1d | T | — | R02.T1v | datatype-match, decreases | closed book, before reading: write `function ChrCount(r: Re): nat`, the number of `Chr` leaves of `r`, recursively; then uncomment the check `lemma ChrCountCheck() ensures ChrCount(Cat(Chr('a'), Star(Alt(Chr('b'), Eps)))) == 2 {}`; record the first try with `scripts/firsttry.sh R02 --check` before uncommenting the check | prompt-as-heading block + commented check |
| R02.T1v | T | — | R02.T1d | datatype-match, decreases | the same as `pub open spec fn chr_count(r: Re) -> nat`; check `proof fn chr_count_check() { assert(chr_count(…the same pattern…) == 2) by (compute_only); }` | prompt-as-heading block + commented check |
| R02.P3dv | P | verdict | — | — | A1's `Matches` with one change: in the `Star` case, the first chunk's bound `0 < i` becomes `0 <= i`. `D:<v> V:<v>` (v as in R01.P1dv) | slot · block |
| R02.P4dv | P | verdict | — | — | A1's `Matches` with one change: `decreases r` in place of `decreases r, \|s\|`. `D:<v> V:<v>` | slot · block |
| R02.P1d | P | obligation | — | — | `specimens/R02/P1d.dfy.specimen`: four empty-bodied lemmas: [a] `!Matches(Empty, s)` (for every `s`), [b] `Matches(Star(r), [])` (for every `r`), [c] `Matches(Cat(Eps, Chr('x')), ['x'])`, [d] `Matches(Star(Chr('x')), ['x', 'x'])`. Which fail? | specimen slot |
| R02.P2v | P | obligation | — | — | `specimens/R02/P2v.rs.specimen`: the same four for `matches` | specimen slot |
| R02.P5d | P | value | — | — | `dafny/checks/R02_checks.dfy`: `expect Nullable(Cat(Star(Empty), Alt(Eps, Chr('a')))) == ???;`. Answer form `true` or `false` | check-unit slot |
| R02.W1d | W | — | — | — | `lemma MatchesAB() ensures Matches(Cat(Chr('a'), Chr('b')), ['a', 'b'])`: the split named explicitly | given, live |
| R02.W1v | W | — | — | — | `proof fn lemma_matches_ab()`, the same | given, live |
| R02.W2d | W | — | — | — | `method StarCount(r: Re) returns (n: nat) ensures n == StarCountSpec(r)`: an exec recursion over the datatype, with its spec function | given, live |
| R02.W2v | W | — | — | — | `fn star_count(r: &Re) -> (n: u64) requires star_count_spec(*r) < 1000 ensures n == star_count_spec(*r)` (`decreases r`): `match` through the reference and the boxes | given, live |
| R02.C1d / C1v | C | `write:datatype-match` | — | — | card: a `datatype` / `enum` with `Box`, and `match` | given |
| R02.C2d / C2v | C | `write:decreases` | — | — | card: termination measures on recursive definitions | given |
| R02.C3d / C3v | C | `write:exists-witness` | — | — | card: proving an existential by naming its witness | given |
| R02.C4dv | C | `recognise:test` | — | — | Rosetta card: Dafny `@Test` / Verus `#[test]` outside `verus!` | given |
| R02.C5dv | C | `recognise:ghost` | — | — | Rosetta card: Dafny `ghost predicate` / Verus `spec fn` | given |
| R02.C6v | C | `recognise:box` | — | — | card: `Box` in a recursive `enum`, and dereferencing it in specs | given |
| R02.H1d | H | — | R02.H1v | datatype-match, exists-witness | `lemma NullableCorrect(r: Re) ensures Nullable(r) <==> Matches(r, [])` (`decreases r`) | bodyless lemma · none (no lever needed, author notes §1.4) |
| R02.H1v | H | — | R02.H1d | datatype-match, exists-witness | `pub proof fn lemma_nullable_correct(r: Re) ensures nullable(r) <==> matches(r, Seq::empty())` (`decreases r`) | `proof_note` assume · none |
| R02.H2d | H | — | R02.H2v | datatype-match | `lemma {:induction false} NodeCountBackwards(r: Re) ensures NodeCount(r) >= 1 && NodeCount(Backwards(r)) == NodeCount(r)` (`decreases r`) | bodyless lemma · `{:induction false}` |
| R02.H2v | H | — | R02.H2d | datatype-match | `pub proof fn lemma_node_count_backwards(r: Re)`, the same (`decreases r`) | `proof_note` assume · none |
| R02.H3d | H | — | R02.H3v | datatype-match | `lemma {:induction false} NullableBackwards(r: Re) ensures Nullable(Backwards(r)) == Nullable(r)` (`decreases r`) | bodyless lemma · `{:induction false}` |
| R02.H3v | H | — | R02.H3d | datatype-match | `pub proof fn lemma_nullable_backwards(r: Re)`, the same | `proof_note` assume · none |
| R02.H4d | H | — | R02.H4v | exists-witness | `lemma CatEpsLeft(r: Re, s: seq<char>) ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)` | bodyless lemma · none |
| R02.H4v | H | — | R02.H4d | exists-witness | `pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>) ensures matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s)` | `proof_note` assume · none |
| R02.H5d | H | — | R02.H5v | datatype-match, decreases | `method IsVoid(r: Re) returns (b: bool) ensures b == VoidSpec(r)` | exec hole `{ assume false; }` · none |
| R02.H5v | H | — | R02.H5d | datatype-match, decreases | `pub fn is_void(r: &Re) -> (b: bool) ensures b == void_spec(*r)` (`decreases r` is yours) | `external_body` + `unimplemented!()` · none |
| R02.C7dv | C | `diverge:r02-c7` | — | — | divergence card (its topic is named in the card). **Final section of the Dafny file** | given |
| R02.A1d / A1v | A | — | — | — | `/contract R02` (implementer vs checks) on the agent files, under R-v0: the contractor defines three functions under the fast channel plus one final full gate; the learner logs latency, writes adversarial checks and first property tests | contract |

#### Constructs (registry)

- `write_d = write_v = ["datatype-match", "decreases", "exists-witness"]` — 3 paired units, 6 slugs.
- `recognise_d = ["test", "ghost"]`, `recognise_v = ["test", "ghost", "box"]`.
- Checked uses (≥ 2 per language): datatype-match d T1d, H1d, H2d, H3d, H5d · v T1v, H1v, H2v, H3v, H5v; decreases d T1d, H5d · v T1v, H5v; exists-witness d H1d, H4d · v H1v, H4v.

#### Agentic file (rung 2: implementer vs checks, spec-first)

- **Shape:** spec-first (spec §3.11.1). Dafny: three compiled `function`s with prose doc contracts, each a bodyless function with one partial `ensures` (W-D02); Verus: three `uninterp spec fn`s shipped with their `decreases` and prose contracts, plus one bound `proof fn` hole per definition stating the same partial contract. A shipped suite of six static checks (two per definition, none implied by the partial formal contract), all failing over the holes.
- **The three definitions** (both languages): the set of characters that occur in a regex; its star height; the length of the shortest string it matches (with a stated convention for a regex that matches nothing). The prose contracts are stronger than the formal `ensures` and the checks.
- **CONTRACT** `goal:` define the three functions so every shipped check holds · `allowed-files:` the agent file of the run · `acceptance:` per edit only the fast channel `scripts/vcheck --symbol <Module.Name> <file>` (Verus `--symbol <fn>`); exactly one full `scripts/vcheck --gate <file>` run, last, exit 0, summary line only · zero holes · `git diff` shows only the bodies of the three definitions and of the bound lemmas · `scripts/vaudit` reports no finding.
- **Learner follow-up (40 min):** read the contracts; run the contract; fill the `LATENCY LOG` block (fast channel vs full gate, from the transcript); then, in `ADVERSARIAL CHECKS`, write checks the shipped suite never exercised, judged against the prose contract, and the **first property tests**: a Dafny `@Test` method looping over a given list of sample regexes, and a Verus `#[test]` fn outside `verus!` exercising the exec `is_nullable` and R02's `is_void` on the same samples (`scripts/vcheck --test`).

#### Itemized minutes (total 342)

| line | items | min |
|---|---|---|
| setup | the A1 layer tour | 10 |
| test-out | T1d, T1v | 10 |
| read | chapter | 65 |
| worked | W1d–W2v (4 × 3.75 = 15) + WRITE cards C1d–C3v (6 × 2.5 = 15) | 30 |
| cards | C4dv, C5dv, C6v (3 × 1.5) + C7dv (4.5) | 9 |
| predicts | P1d–P5d (5 × 2.4) | 12 |
| holes | H1d–H5d (5 × 5 = 25) + H1v–H5v (5 × 7 = 35) | 60 |
| agent + first tests | A1d/A1v audit (10) + adversarial checks and property tests (30) | 40 |
| paper | card 05.6 (15), termination of `Matches` (15), splits by hand (15) | 45 |
| bench card | the first `bench/local/r` card | 25 |
| viva | 6 of 12 | 30 |
| calib | | 6 |
| **total** | | **342** |

Hole minutes 25 D / 35 V give the design's 45/55 share; the pair rate is calibrated on R02 (design C1).

#### Registry fields (R02)

```toml
status = "authoring"
exercises = ["dafny/R/R02_Datatypes/core/R02_Datatypes.dfy", "dafny/checks/R02_checks.dfy", "verus/r/r02_datatypes/src/lib.rs", "specimens/R02/"]
exits = []
agentic = ["dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy", "verus/r/r02_datatypes/src/agent.rs"]
units = ["dafny/R/R02_Datatypes/core", "verus/r/r02_datatypes"]
layer = "A1"
langs = ["d", "v"]
engines = ["contract"]
write_d = ["datatype-match", "decreases", "exists-witness"]
write_v = ["datatype-match", "decreases", "exists-witness"]
recognise_d = ["test", "ghost"]
recognise_v = ["test", "ghost", "box"]

[module.imports]
"dafny/given/R/RG_A1_Re.dfy" = "core"
"verus/given/rg_re_a1/src/lib.rs" = "prelude"
"dafny/R/R02_Datatypes/core/R02_Datatypes.dfy" = "core"
"dafny/checks/R02_checks.dfy" = "core"
"dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy" = "core"
"verus/r/r02_datatypes/src/lib.rs" = "prelude"
"verus/r/r02_datatypes/src/agent.rs" = "prelude"
```

---

### 6.3 R03 — Modules and APIs

*Layer A1, 300 min (viva included). Agent rung 2 at API scale: API implementer. Second bench card. The character-class API is module-local here; A2 re-supplies it from R07.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| Dafny exercise | `dafny/R/R03_Modules/core/R03_Modules.dfy`: `module R03_Modules` holding an inner `module CharClasses` (given: `datatype CRange = CRange(lo: char, hi: char)`, `datatype CharClass = CharClass(ranges: seq<CRange>)`, `predicate InRange`, `ghost predicate InClass(cc, c)`, `predicate ClassValid(cc)` (each range non-empty, sorted, separated), `function ClassEmpty()`, the worked `ClassInsert`, and an `export` clause shipped without the entries of the functions you write) and a `module Client` that imports it | green; **5 holes** (H1d–H5d) |
| Verus crate | `verus/r/r03_modules/src/lib.rs` (crate `r03_modules`; deps `vstd`, `rg_re_a1`): `mod char_class` (given: `pub struct CharClass { ranges: Vec<(char, char)> }` with a private field, `impl View for CharClass { type V = Set<char>; closed spec fn view(&self) }`, `pub closed spec fn valid(&self)`, the worked `class_insert`) and `mod client` | green; **5 holes** (H1v–H5v) |
| prediction specimens | `specimens/R03/P1d.dfy.specimen`, `P2v.rs.specimen` (obligation); the P3dv and P4dv scenarios are docstring blocks | slots unfilled |
| card demos | WRITE: `card-c1d`, `card-c3v`, `card-c4v`, `card-c5v`. Divergence: `card-c8dv-d.dfy.specimen`, `card-c8dv-v.rs.specimen` (`// after: R03.P3dv` and `// after: R03.P4dv`; sealed) | red by design, pinned |
| slots | `slots/R03.slots`: `P3dv P4dv = ???` | unfilled |
| agent | `dafny/R/R03_Modules/agent/R03_AgentApi.dfy`, `verus/r/r03_modules/src/agent.rs` | RED: two API statements with hole bodies over a copy of the given class code |
| pins, twins | `expected/R03.*`, `Solutions/…` | — |

Header counts: **10 holes**, **4 predictions**.

#### Items

| id | K | format | pair | uses | statement or prompt | form · lever |
|---|---|---|---|---|---|---|
| R03.P3dv | P | verdict | — | — | A client in another module asserts `InClass(ClassSingle('b'), 'b')` (Verus: `class_single('b')@.contains('b')` after the call), where the scenario's API defines `ClassSingle(c)`, the one-character class, exports it with `provides` only and states only validity in its `ensures` (Verus: a `closed` view, `ensures r.valid()` only). `D:<v> V:<v>` | slot · block |
| R03.P4dv | P | verdict | — | — | The same client assert, where the API exports `reveals ClassSingle, InClass` (Verus: an `open` view and `pub open spec fn` helpers; the exec `class_single` keeps the same `ensures`). `D:<v> V:<v>` | slot · block |
| R03.P1d | P | obligation | — | — | `specimens/R03/P1d.dfy.specimen`: the API's `ClassMember` has gained `requires ClassValid(cc)`. A client makes four labelled calls: [a] on `ClassSingle('x')`, [b] on `ClassInsert(ClassEmpty(), CRange('a', 'f'))`, [c] on a `CharClass` literal written by hand inside the API module, [d] on a parameter of a client method that has no `requires`. (The specimen's API is the given part of R03's file plus `ClassSingle`; it holds none of R03's hole targets.) Which labelled lines fail? | specimen slot |
| R03.P2v | P | obligation | — | — | `specimens/R03/P2v.rs.specimen`: the same with `requires cc.valid()` | specimen slot |
| R03.W1d | W | — | — | — | a mini-API for `CRange` alone in its own module: an export set, a constructor and a membership test, and a client that uses only the contracts | given, live |
| R03.W1v | W | — | — | — | the same as a `mod` with a private field and a `View` | given, live |
| R03.W2d | W | — | — | — | `function ClassInsert(cc: CharClass, g: CRange): (res: CharClass) requires ClassValid(cc) ensures ClassValid(res) && forall c :: InClass(res, c) <==> InClass(cc, c) \|\| InRange(g, c)`: the worked merge, finished | given, live |
| R03.W2v | W | — | — | — | `pub fn class_insert(&self, lo: char, hi: char) -> (res: CharClass) requires self.valid(), ensures res.valid(), res@ == self@.union(…the range's set…)`, finished | given, live |
| R03.C1d | C | `write:export` | — | — | card: export sets, `provides` vs `reveals` | given |
| R03.C2d | C | `recognise:import` | — | — | card: `import`, `import opened`, qualified names | given |
| R03.C3v | C | `write:view` | — | — | card: `impl View`, `@` | given |
| R03.C4v | C | `write:closed-spec` | — | — | card: `open` vs `closed spec fn` | given |
| R03.C5v | C | `write:pub-visibility` | — | — | card: `pub`, private fields, `mod` boundaries | given |
| R03.C6d / C7v | C | `recognise:opaque` | — | — | cards: `opaque` functions and `reveal` (WRITE in R08) | given |
| R03.H1d | H | — | R03.H1v | export | `function ClassMember(cc: CharClass, c: char): (b: bool) ensures b == InClass(cc, c)`: a recursion over the ranges | bodyless function hole · none |
| R03.H1v | H | — | R03.H1d | view | `fn member_from(&self, c: char, i: usize) -> (b: bool) requires i <= self.ranges.len(), ensures b == (exists\|j: int\| i <= j < self.ranges.len() && …the range at j contains c…)` (`decreases` is yours); the given `class_member` calls it | `external_body` + `unimplemented!()` · none |
| R03.H2d | H | — | R03.H2v | export | `function ClassRange(lo: char, hi: char): (r: CharClass) ensures ClassValid(r) && forall c :: InClass(r, c) <==> lo <= c <= hi`: total, no `requires`; add it to the export set | bodyless function hole · none |
| R03.H2v | H | — | R03.H2d | view, closed-spec, pub-visibility | `pub fn class_range(lo: char, hi: char) -> (r: CharClass) ensures r.valid(), forall\|c: char\| r@.contains(c) <==> (lo <= c && c <= hi)` | `external_body` + `unimplemented!()` · none |
| R03.H3d | H | — | R03.H3v | export | `function ClassUnion(a: CharClass, b: CharClass): (u: CharClass) requires ClassValid(a) && ClassValid(b) ensures ClassValid(u) && forall c :: InClass(u, c) <==> InClass(a, c) \|\| InClass(b, c)`, over `ClassInsert` | bodyless function hole · none |
| R03.H3v | H | — | R03.H3d | view, closed-spec | `pub fn class_union(&self, other: &CharClass) -> (u: CharClass) requires self.valid(), other.valid(), ensures u.valid(), u@ == self@.union(other@)` | `external_body` + `unimplemented!()` · none |
| R03.H4d | H | — | R03.H4v | — | in `module Client`, using only the exported API: `method Union3(a: CharClass, b: CharClass, c: CharClass) returns (u: CharClass) requires ClassValid(a) && ClassValid(b) && ClassValid(c) ensures ClassValid(u) && forall x :: InClass(u, x) <==> InClass(a, x) \|\| InClass(b, x) \|\| InClass(c, x)` | exec hole `{ assume false; }` · none |
| R03.H4v | H | — | R03.H4d | pub-visibility | in `mod client`: `pub fn union3(a: &CharClass, b: &CharClass, c: &CharClass) -> (u: CharClass) requires … ensures u.valid(), u@ == a@.union(b@).union(c@)` | `external_body` + `unimplemented!()` · none |
| R03.H5d | H | — | R03.H5v | — | `function ClassOfString(s: seq<char>): (r: CharClass) ensures ClassValid(r) && forall c :: InClass(r, c) <==> c in s` | bodyless function hole · none |
| R03.H5v | H | — | R03.H5d | view | `pub fn class_of_string(s: &Vec<char>) -> (r: CharClass) ensures r.valid(), forall\|c: char\| r@.contains(c) <==> s@.contains(c)` | `external_body` + `unimplemented!()` · none |
| R03.C8dv | C | `diverge:r03-c8` | — | — | divergence card (its topic is named in the card). **Final section** | given |
| R03.A1d / A1v | A | — | — | — | `/contract R03` (API implementer) on the agent files; the learner reviews the delivered API | contract |

**The API review** (15 min, prose; an `API REVIEW` block in the Dafny exercise file): the learner's total-API checklist applied to their own R03 API (every function defined on every valid input; no partiality hidden in a `requires`; contracts strong enough for the client; what the export set and the views hide).

#### Constructs (registry)

- `write_d = ["export"]`, `write_v = ["view", "closed-spec", "pub-visibility"]` — 4 single-language units, 4 slugs.
- `recognise_d = ["import", "opaque"]`, `recognise_v = ["opaque"]`.
- Checked uses (≥ 2 per language): export d H1d, H2d, H3d; view v H1v, H2v, H3v, H5v; closed-spec v H2v, H3v; pub-visibility v H2v, H4v.

#### Agentic file (rung 2 at API scale: API implementer)

- **Shape:** statements with hole bodies (spec §3.11.1), over a copy of the given class code: `ClassIntersect(a, b)` and `ClassDiff(a, b)` (validity preserved, membership stated through `InClass` / the view), each needing only the inputs' validity.
- **CONTRACT** `goal:` implement both functions so that their statements verify · `allowed-files:` the agent file · `acceptance:` `scripts/vcheck --gate <file>` exits 0 · zero holes · `scripts/specfreeze --against <snapshot> <file>` reports the two statements unchanged (no `requires` added, no `ensures` weakened) · `scripts/vaudit` reports no finding.
- **Learner follow-up (30 min):** the adversarial review, in an `ADVERSARIAL REVIEW` block: is the delivered API total; are the contracts strong enough for a client; what happens at the character boundaries (the smallest and largest `char`); would a client of the delivered API verify where a client of the statement does.

#### Itemized minutes (total 300)

| line | items | min |
|---|---|---|
| setup | | 5 |
| read | chapter | 60 |
| worked | W1d, W1v (2 × 4) + W2d, W2v (2 × 6) + WRITE cards C1d, C3v, C4v, C5v (4 × 2.5) | 30 |
| cards | C2d, C6d, C7v (3 × 1.5) + C8dv (3.5) | 8 |
| predicts | P1d–P4dv (4 × 3) | 12 |
| holes | H1d–H5v (10 × 7) | 70 |
| API review | the `API REVIEW` block | 15 |
| agent | A1d/A1v audit and adversarial review | 30 |
| paper | card 03.2 (cards only, Δ74) | 15 |
| bench card | | 20 |
| viva | 6 of 12 | 30 |
| calib | | 5 |
| **total** | | **300** |

#### Registry fields (R03)

```toml
status = "authoring"
exercises = ["dafny/R/R03_Modules/core/R03_Modules.dfy", "verus/r/r03_modules/src/lib.rs", "specimens/R03/"]
exits = []
agentic = ["dafny/R/R03_Modules/agent/R03_AgentApi.dfy", "verus/r/r03_modules/src/agent.rs"]
units = ["dafny/R/R03_Modules/core", "verus/r/r03_modules"]
layer = "A1"
langs = ["d", "v"]
engines = ["contract"]
write_d = ["export"]
write_v = ["view", "closed-spec", "pub-visibility"]
recognise_d = ["import", "opaque"]
recognise_v = ["opaque"]

[module.imports]
"dafny/R/R03_Modules/core/R03_Modules.dfy" = "core"
"dafny/R/R03_Modules/agent/R03_AgentApi.dfy" = "core"
"verus/r/r03_modules/src/lib.rs" = "prelude"
"verus/r/r03_modules/src/agent.rs" = "prelude"
```

---
### 6.4 R04 — Specs as logic

*Layer A1, 360 min (viva included). Agent rung 6: audited prover. Third bench card. Given in both files: the unanchored `Occurs(r, s)` (some substring `s[i..j]` matches `r`), Dafny `ghost predicate Occurs(r: Re, s: seq<char>)`, Verus `pub open spec fn occurs(r: Re, s: Seq<char>) -> bool`.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| Dafny exercise | `dafny/R/R04_Specs/core/R04_Specs.dfy` (`module R04_Specs`, imports `RG_A1_Re`) | green; **6 holes** (T1d, H1d–H5d); the prediction block holds P1d and the 2 `dv` verdicts (P2dv, P6dv) |
| Verus crate | `verus/r/r04_specs/src/lib.rs` (crate `r04_specs`; deps `vstd`, `rg_re_a1`) | green; **6 holes** (T1v, H1v–H5v) |
| prediction specimens | `specimens/R04/P3d.dfy.specimen`, `P4v.rs.specimen` (obligation); the P5d delivery `specimens/R04/P5d.dfy.specimen` (a *specimen* scenario with the CHECK switch, refused by `vcheck` and `vaudit` until the first try is recorded, H5; it carries one `// planted: R04.P5d` marker, Δ118) | slots unfilled |
| card demos | WRITE: `card-c1d`, `card-c1v`, `card-c2d`, `card-c2v`. Divergence: `card-c5dv-d.dfy.specimen`, `card-c5dv-v.rs.specimen` (`// after: R04.P1d` and `// after: R04.P5d`; sealed) | red by design, pinned |
| slots | `slots/R04.slots`: `P1d P2dv P5d P6dv = ???` | unfilled |
| agent | `dafny/R/R04_Specs/agent/R04_AgentProver.dfy`, `verus/r/r04_specs/src/agent.rs` | RED: three lemma holes, one of them planted |
| pins, twins | `expected/R04.*` (the freeze leaves H4's definitions open), `Solutions/…` | — |

Header counts: **12 holes**, **2 test-out items** (holes), **6 predictions**.

#### Items

| id | K | format | pair | uses | statement or prompt | form · lever |
|---|---|---|---|---|---|---|
| R04.T1d | T | — | R04.T1v | exists-elim | closed book, before reading: `lemma SomeWordMatches() ensures exists s :: Matches(Cat(Chr('o'), Star(Chr('k'))), s)`; record the first try with `scripts/firsttry.sh R04 --check` | bodyless lemma · none |
| R04.T1v | T | — | R04.T1d | exists-elim | `proof fn lemma_some_word_matches() ensures exists\|s: Seq<char>\| matches(…the same pattern…, s)` | `proof_note` assume · none |
| R04.P1d | P | verdict | — | — | `method Pos(x: int) returns (y: int) ensures y > 0 { expect x > 0; y := x; }`, outside any test. What does `scripts/vcheck` report? Answer form `D:<v>` (v as in R01.P1dv) | slot · block |
| R04.P2dv | P | verdict | — | — | Four postconditions for `Find(r, s) returns (b)` (the Verus spellings beside them): [a] `b <==> Occurs(r, s)`; [b] `b <==> Matches(r, s)`; [c] `b ==> Occurs(r, s)`; [d] `b <==> exists i :: 0 <= i <= \|s\| && Matches(r, s[i..])`. With `r := Star(Chr('a'))` and `s := "b"`, which of them force `b == true`? Answer form: the letters in order, separated by single spaces, or `none` (the same answer in both languages; the author proves each claim in both) | slot · block |
| R04.P3d | P | obligation | — | — | `specimens/R04/P3d.dfy.specimen`: four empty-bodied lemmas: [a] `Occurs(Star(Chr('a')), "b")`, [b] `Occurs(Eps, s)` (for every `s`), [c] `!Occurs(Chr('a'), "b")`, [d] `Occurs(Chr('b'), "ab")`. Which fail? | specimen slot |
| R04.P4v | P | obligation | — | — | `specimens/R04/P4v.rs.specimen`: the same four for `occurs` | specimen slot |
| R04.P5d | P | verdict | — | — | A green-looking delivery: `Pos` of P1d, in a file of its own. The exit code of `scripts/vcheck --gate` and the number of findings `scripts/vaudit` reports. Answer form `D:<exit> <n>` (Dafny only: how the Verus gate and audit treat an `assume` is a fact the chapter states, §5.1) | specimen · CHECK switch |
| R04.P6dv | P | verdict | — | — | A trivial `Find`: Dafny `method FindNone(r: Re, s: seq<char>) returns (b: bool) { b := false; }`; Verus `fn find_none(r: &Re, s: &Vec<char>) -> (b: bool) { false }`, checked four times, once against each postcondition [a]–[d] of P2dv on its own. Which of the four verify? Answer form `D:<labels> V:<labels>`, labels in order separated by single spaces, or `none` | slot · block |
| R04.W1d | W | — | — | — | `lemma EpsOnlyEmpty() ensures forall s :: Matches(Eps, s) ==> s == []`, by a `forall` statement | given, live |
| R04.W1v | W | — | — | — | the same with `assert forall\|s: Seq<char>\| … by { … }` | given, live |
| R04.W2d | W | — | — | — | `lemma CatChrNonEmpty(b: Re, s: seq<char>) requires Matches(Cat(Chr('x'), b), s) ensures \|s\| >= 1`: eliminating the split with `:\|` | given, live |
| R04.W2v | W | — | — | — | the same with `choose` | given, live |
| R04.C1d / C1v | C | `write:forall-intro` | — | — | card: proving a `forall` (Dafny `forall` statement / Verus `assert forall … by`) | given |
| R04.C2d / C2v | C | `write:exists-elim` | — | — | card: using an existential (`:\|` / `choose`) | given |
| R04.C3d | C | `recognise:expect` | — | — | card: `expect` (runtime checks; the course bans it outside tests) | given |
| R04.C4v | C | `recognise:assume` | — | — | card: `assume` and where the course counts it | given |
| R04.H1d | H | — | R04.H1v | — | `lemma WitnessAbb() ensures Matches(Cat(Chr('a'), Star(Chr('b'))), "abb")` | bodyless lemma · none |
| R04.H1v | H | — | R04.H1d | — | `proof fn lemma_witness_abb()`, the same | `proof_note` assume · none |
| R04.H2d | H | — | R04.H2v | forall-intro, exists-elim | `lemma WitnessNotBa() ensures !Matches(Cat(Chr('a'), Star(Chr('b'))), "ba")` | bodyless lemma · none |
| R04.H2v | H | — | R04.H2d | forall-intro, exists-elim | `proof fn lemma_witness_not_ba()`, the same | `proof_note` assume · none |
| R04.H3d | H | — | R04.H3v | forall-intro, exists-elim | `lemma WitnessAnchored() ensures !Matches(Chr('a'), "ba") && Matches(Cat(Star(Chr('b')), Chr('a')), "ba")` | bodyless lemma · none |
| R04.H3v | H | — | R04.H3d | forall-intro, exists-elim | `proof fn lemma_witness_anchored()`, the same | `proof_note` assume · none |
| R04.H4d | H | — | R04.H4v | — | **From prose:** define `ghost predicate PrefixMatch(r: Re, s: seq<char>)`, "true exactly when some prefix of `s`, the empty prefix included, matches `r`"; then uncomment the three checks under `Uncomment as you go:` (a positive case, a negative case, the empty-prefix case), each a lemma whose proof is given and verifies only with an adequate definition | bodyless predicate (definition open, Δ160) + commented checks · none |
| R04.H4v | H | — | R04.H4d | — | the same for `pub uninterp spec fn prefix_match(r: Re, s: Seq<char>) -> bool` becoming `open spec fn` | `uninterp spec fn` + commented checks · none |
| R04.H5d | H | — | R04.H5v | — | **A mutant-kill witness.** The mutant implementation of `Find` returns `Nullable(r)`. `lemma MutantKilled() ensures exists r: Re, s: seq<char> :: Nullable(r) != Occurs(r, s)` | bodyless lemma · none |
| R04.H5v | H | — | R04.H5d | — | `proof fn lemma_mutant_killed() ensures exists\|r: Re, s: Seq<char>\| nullable(r) != occurs(r, s)` | `proof_note` assume · none |
| R04.C5dv | C | `diverge:r04-c5` | — | — | divergence card (its topic is named in the card). **Final section** | given |
| R04.A1d / A1v | A | — | — | — | `/contract R04` (audited prover) on the agent files, under R-v0 | contract |

**The audit drill** (20 min, prose; an `AUDIT` block in the Dafny exercise file): `scripts/vaudit` on three given deliveries (after P5d's first try; one of them a Verus `assume` delivery), each classified: clean, an assumption the gate counts, an assumption only the audit sees; and what a reader must still check by hand.

#### Constructs (registry)

- `write_d = write_v = ["forall-intro", "exists-elim"]` — 2 paired units, 4 slugs.
- `recognise_d = ["expect"]`, `recognise_v = ["assume"]`.
- Checked uses (≥ 2 per language): forall-intro d H2d, H3d · v H2v, H3v; exists-elim d T1d, H2d, H3d · v T1v, H2v, H3v.

#### Agentic file (rung 6: audited prover)

- **Shape:** three lemma holes over `Occurs` and `Matches` (spec §3.11.1, statements with hole bodies), each with its prose intent; **one statement is false as written** (planted; the planted line carries `// planted: R04.A1d` / `R04.A1v`, Δ118), so a faithful contractor must stop and report it.
- **CONTRACT** `goal:` prove the three lemmas · `allowed-files:` the agent file · `acceptance:` `scripts/vcheck --gate <file>` exits 0 for every lemma the contractor reports proved · zero holes in those lemmas · `scripts/specfreeze --against <snapshot> <file>` reports every statement unchanged · `scripts/vaudit` reports no finding · a lemma that cannot be proved as stated is reported with its counterexample, never weakened.
- **Learner follow-up (30 min):** audit the delivery (diff, freeze, audit, transcript) and record, in `AUDIT DEBRIEF`, what the contractor did with the false statement; then prove or refute it yourself.

#### Itemized minutes (total 360)

| line | items | min |
|---|---|---|
| setup | | 10 |
| test-out | T1d, T1v | 10 |
| read | chapter | 60 |
| worked | W1d–W2v (4 × 5 = 20) + WRITE cards C1d–C2v (4 × 2.5 = 10) | 30 |
| cards | C3d, C4v (2 × 1.5) + C5dv (5) | 8 |
| predicts | P1d–P6dv (6 × 2.5) | 15 |
| holes | H1d–H5v (10 × 7) | 70 |
| audit drill | the `AUDIT` block | 20 |
| agent | A1d/A1v audit and debrief | 30 |
| paper | card 12.5 (15), classify four specs (15), wp/VC by hand (15) | 45 |
| bench card | | 25 |
| viva | 6 of 12 | 30 |
| calib | | 7 |
| **total** | | **360** |

#### Registry fields (R04)

```toml
status = "authoring"
exercises = ["dafny/R/R04_Specs/core/R04_Specs.dfy", "verus/r/r04_specs/src/lib.rs", "specimens/R04/"]
exits = []
agentic = ["dafny/R/R04_Specs/agent/R04_AgentProver.dfy", "verus/r/r04_specs/src/agent.rs"]
units = ["dafny/R/R04_Specs/core", "verus/r/r04_specs"]
layer = "A1"
langs = ["d", "v"]
engines = ["contract"]
write_d = ["forall-intro", "exists-elim"]
write_v = ["forall-intro", "exists-elim"]
recognise_d = ["expect"]
recognise_v = ["assume"]

[module.imports]
"dafny/R/R04_Specs/core/R04_Specs.dfy" = "core"
"dafny/R/R04_Specs/agent/R04_AgentProver.dfy" = "core"
"verus/r/r04_specs/src/lib.rs" = "prelude"
"verus/r/r04_specs/src/agent.rs" = "prelude"
```

---

### 6.5 R05 — No goal state

*Layer A1, 402 min (viva included). Agent rung 6: obligation prover (fast channel only, one final gate). Python from here: `harness/r/fvh_r/variance.py`. Fourth bench card.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| Dafny exercise | `dafny/R/R05_NoGoalState/core/R05_NoGoalState.dfy` (`module R05_NoGoalState`, imports `RG_A1_Re`) | green; **4 holes** (H1d–H4d); the prediction block holds the 2 `dv` verdicts |
| Verus crate | `verus/r/r05_no_goal_state/src/lib.rs` (crate `r05_no_goal_state`; deps `vstd`, `rg_re_a1`) | green; **4 holes** (H1v–H4v) |
| Python | `harness/r/fvh_r/variance.py` (package `fvh_r`, tier `py-fvh`) | **2 holes** (H1py, H2py, counted from the syntax tree); acceptance tests `harness/tests/r/test_r05_variance.py` (frozen, rule 2f) |
| variance log | `research/r05/variance.jsonl` (learner-owned; written by the learner's runs, read by H2py) | absent until the runs |
| prediction specimens | `specimens/R05/P1d.dfy.specimen`, `P2v.rs.specimen` (obligation) | slots unfilled |
| card demos | WRITE: `card-c1d`, `card-c1v`, `card-c2d`, `card-c3v`. Divergence: `card-c5dv-d.dfy.specimen`, `card-c5dv-v.rs.specimen` (`// after: R05.P3dv`; sealed) | red by design, pinned |
| slots | `slots/R05.slots`: `P3dv P4dv = ???` | unfilled |
| agent | `dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy`, `verus/r/r05_no_goal_state/src/agent.rs` | RED: two lemma holes |
| pins, twins | `expected/R05.*`, `Solutions/…`, `Solutions/harness/r/fvh_r/variance.py` | — |

Header counts: **8 verifier holes + 2 Python holes**, **4 predictions**.

#### Items

| id | K | format | pair | uses | statement or prompt | form · lever |
|---|---|---|---|---|---|---|
| R05.P3dv | P | verdict | — | — | Ten runs of `scripts/vcheck --json --measures`, one after another, on one verified file (the worked lemma W1d / W1v copied into a file of its own; the course's pinned seed; nothing changed between runs). Across the ten documents, is the `resource_count` field always the same, and is `wall_s`? Answer form `D:<same\|varies>,<same\|varies> V:<same\|varies>,<same\|varies>` (resource count first) | slot · block |
| R05.P4dv | P | verdict | — | — | A file with two lemmas, the first correct, the second with a false `assert`. `scripts/vcheck --symbol` on the first (Dafny `R05_NoGoalState.First`, Verus `first`): what is the verdict? Answer form `D:<v> V:<v>` | slot · block |
| R05.P1d | P | obligation | — | — | `specimens/R05/P1d.dfy.specimen`: a chain of five labelled asserts [a]–[e] about slices of a sequence `s` at two indices `0 <= i <= j <= |s|` (slices of slices, and concatenations of slices), with no lemma calls. Which fail? | specimen slot |
| R05.P2v | P | obligation | — | — | `specimens/R05/P2v.rs.specimen`: the same chain over `subrange` | specimen slot |
| R05.W1d | W | — | — | — | a five-step proof of a slicing fact, an `assert` after each step: bisection worked once | given, live |
| R05.W1v | W | — | — | — | the same over `subrange` | given, live |
| R05.W2d | W | — | — | — | `assert … by` scoping and `@IsolateAssertions` on a small lemma | given, live |
| R05.W2v | W | — | — | — | `assert … by` scoping and `#[verifier::spinoff_prover]` | given, live |
| R05.C1d / C1v | C | `write:assert-by` | — | — | card: `assert … by` as a scope | given |
| R05.C2d | C | `write:isolate-assertions` | — | — | card: `@IsolateAssertions` | given |
| R05.C3v | C | `write:spinoff-prover` | — | — | card: `#[verifier::spinoff_prover]` | given |
| R05.C4dv | C | `recognise:rlimit` | — | — | Rosetta card: resource limits (`{:resource_limit}` / `#[verifier::rlimit]`) and the course pins | given |
| R05.H1d | H | — | R05.H1v | assert-by, isolate-assertions | `lemma CatAssocLR(a: Re, b: Re, c: Re, s: seq<char>) requires Matches(Cat(Cat(a, b), c), s) ensures Matches(Cat(a, Cat(b, c)), s)` | bodyless lemma · none |
| R05.H1v | H | — | R05.H1d | assert-by, spinoff-prover | `proof fn lemma_cat_assoc_lr(…)`, the same | `proof_note` assume · none |
| R05.H2d | H | — | R05.H2v | assert-by | `lemma CatAssocRL(…) requires Matches(Cat(a, Cat(b, c)), s) ensures Matches(Cat(Cat(a, b), c), s)` | bodyless lemma · none |
| R05.H2v | H | — | R05.H2d | assert-by | `proof fn lemma_cat_assoc_rl(…)` | `proof_note` assume · none |
| R05.H3d | H | — | R05.H3v | — | `lemma StarOne(a: Re, u: seq<char>) requires Matches(a, u) ensures Matches(Star(a), u)` | bodyless lemma · none |
| R05.H3v | H | — | R05.H3d | — | `proof fn lemma_star_one(a: Re, u: Seq<char>)` | `proof_note` assume · none |
| R05.H4d | H | — | R05.H4v | assert-by, isolate-assertions | **Bisect and repair.** `lemma StarConcat(a: Re, u: seq<char>, v: seq<char>) requires Matches(Star(a), u) && Matches(Star(a), v) ensures Matches(Star(a), u + v)` (`decreases \|u\|`): the case split, the choice of the first chunk and the recursive call are given; the facts the solver lacks are not. Find them by bisection and add them | annotation hole · none |
| R05.H4v | H | — | R05.H4d | assert-by, spinoff-prover | the same for `proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)` (`decreases u.len()`), with `choose` | annotation hole · none |
| R05.H1py | H | — | — | — | `def runs_from_log(path: Path) -> list[Run]`: the runs recorded in the variance log (one `scripts/vcheck --json --measures` document per line plus the run's wall time), in order; `ValueError` on a malformed line | Python hole · none |
| R05.H2py | H | — | — | — | `def variance_summary(runs: Sequence[Run], field: str, *, seed: int) -> Summary`: n, mean, coefficient of variation and a 95 % bootstrap interval of the mean for one numeric field (`wall_s` or `resource_count`), by composing the standard library's `statistics` and `fvh.stats.bootstrap_ci`; `ValueError` for fewer than 2 runs | Python hole · none |
| R05.C5dv | C | `diverge:r05-c5` | — | — | divergence card (its topic is named in the card). **Final section** | given |
| R05.A1d / A1v | A | — | — | — | `/contract R05` (obligation prover) on the agent files, under R-v0 | contract |

**The variance log** (30 min): ten runs of `scripts/vcheck --json --measures` on your finished H1d and ten on H1v, one solver job at a time, appended to `research/r05/variance.jsonl` with their wall times; then `variance_summary` on each field, and a five-line note in `research/r05/NOTES.md`: n, the interval, what it licenses about the next run. **The latency log** (15 min): the fast channel vs the full gate on the same proof, in a `LATENCY` block.

#### Constructs (registry)

- `write_d = ["assert-by", "isolate-assertions"]`, `write_v = ["assert-by", "spinoff-prover"]` — 3 units (1 paired + 2 single), 4 slugs.
- `recognise_d = recognise_v = ["rlimit"]`.
- Checked uses (≥ 2 per language): assert-by d H1d, H2d, H4d · v H1v, H2v, H4v; isolate-assertions d H1d, H4d; spinoff-prover v H1v, H4v.

#### Agentic file (rung 6: obligation prover)

- **Shape:** two lemma holes about `Star` and `Cat` that need helper facts the agent must find without a goal view; the agent file verifies against the given chain alone (no call into the exercise file's lemmas).
- **CONTRACT** `goal:` prove both lemmas · `allowed-files:` the agent file · `acceptance:` per edit only the fast channel `scripts/vcheck --symbol <Module.Name> <file>` (Verus `--symbol <fn>`); exactly one full `scripts/vcheck --gate <file>` run, last, exit 0 · zero holes · statements unchanged (`scripts/specfreeze --against <snapshot> <file>`) · `scripts/vaudit` reports no finding.
- **Learner follow-up (25 min):** from the transcript, count fast-channel calls and failed obligations per lemma, note what the agent added (assertions, helper lemmas) and whether each was needed (delete it in a scratch copy and re-run), in an `OBLIGATION LOG` block.

#### Itemized minutes (total 402)

| line | items | min |
|---|---|---|
| setup | | 10 |
| read | chapter | 65 |
| worked | W1d–W2v (4 × 5 = 20) + WRITE cards C1d, C1v, C2d, C3v (4 × 2.5 = 10) | 30 |
| cards | C4dv (1.5) + C5dv (4.5) | 6 |
| predicts | P1d–P4dv (4 × 3) | 12 |
| holes | H1d–H3v (6 × 8 = 48) + H4d, H4v (2 × 12 = 24) | 72 |
| Python | H1py, H2py (2 × 12) + the acceptance tests and a first run (11) | 35 |
| variance log | | 30 |
| latency log | | 15 |
| agent | A1d/A1v and the `OBLIGATION LOG` | 25 |
| paper | card 06.3 (15), facts per line (15), first intervals by hand (15) | 45 |
| bench card | | 20 |
| viva | 6 of 12 | 30 |
| calib | | 7 |
| **total** | | **402** |

#### Registry fields (R05)

```toml
status = "authoring"
exercises = ["dafny/R/R05_NoGoalState/core/R05_NoGoalState.dfy", "verus/r/r05_no_goal_state/src/lib.rs", "specimens/R05/"]
exits = []
agentic = ["dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy", "verus/r/r05_no_goal_state/src/agent.rs"]
harness = ["harness/r/fvh_r/variance.py"]
units = ["dafny/R/R05_NoGoalState/core", "verus/r/r05_no_goal_state"]
layer = "A1"
langs = ["d", "v", "py"]
engines = ["contract"]
write_d = ["assert-by", "isolate-assertions"]
write_v = ["assert-by", "spinoff-prover"]
recognise_d = ["rlimit"]
recognise_v = ["rlimit"]

[module.imports]
"dafny/R/R05_NoGoalState/core/R05_NoGoalState.dfy" = "core"
"dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy" = "core"
"verus/r/r05_no_goal_state/src/lib.rs" = "prelude"
"verus/r/r05_no_goal_state/src/agent.rs" = "prelude"
"harness/r/fvh_r/variance.py" = "py-fvh"
```

---

### 6.6 R06 — Induction and loops

*Layers A1 and A1b (A1b declared here, §2.2), 462 min (viva included). Checkpoint: 2 D + 2 V closed-book items, ≥ 3/4 with ≥ 1 per language (Δ116). Agent: decomposer. Fifth bench card (a stripped R06 lemma). Given in both files: the Brzozowski derivative `Deriv(r: Re, c: char): Re` (Dafny compiled `function`; Verus `pub open spec fn deriv(r: Re, c: char) -> Re` and a proved exec `deriv_exec(r: &Re, c: char) -> (out: Re) ensures out == deriv(*r, c)`). Spike S1 closed for every hole of this module; only the Verus decomposer stays **pending spike**.*

#### Files

| artifact | path | shipped state |
|---|---|---|
| given layer | `dafny/given/R/RG_A1b_Facts.dfy`, crate `verus/given/rg_re_a1b` (§2.2) | frozen; declared by R06 |
| Dafny exercise | `dafny/R/R06_Induction/core/R06_Induction.dfy` (`module R06_Induction`, imports `RG_A1_Re`, `RG_A1b_Facts`) | green; **5 holes** (T1d, H1d–H4d); the prediction block holds the 2 `dv` verdicts |
| Dafny check unit | `dafny/checks/R06_checks.dfy` (`module R06_Checks`, imports `RG_A1_Re`; holds its own copy of the given `Deriv`) | green; 1 value slot (P1d) |
| Verus crate | `verus/r/r06_induction/src/lib.rs` (crate `r06_induction`; deps `vstd`, `rg_re_a1`, `rg_re_a1b`) | green; **5 holes** (T1v, H1v–H4v) |
| checkpoint | `dafny/R/R06_Induction/exit/R06_Checkpoint.dfy` (`module R06_Checkpoint`): 2 blocks; `verus/r/r06_induction/src/exit.rs`: 2 blocks (shipped holes per the author notes) | green |
| prediction specimens | `specimens/R06/P2v.rs.specimen` (value), `P4d.dfy.specimen`, `P5v.rs.specimen` (obligation) | slots unfilled |
| card demos | WRITE: `card-c1d` … `card-c3v`, `card-c4d` (7, in-file `// EXPECT`). Divergence: `card-c6dv-d.dfy.specimen`, `card-c6dv-v.rs.specimen` | red by design, pinned |
| slots | `slots/R06.slots`: `P3dv P6dv = ???` | unfilled |
| agent | `dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy`, `verus/r/r06_induction/src/agent.rs` | RED: one top statement, no skeleton |
| pins, twins | `expected/R06.*` (H4's `requires` open, Δ160), `Solutions/…` | — |

Header counts: **10 holes**, **2 test-out items** (holes), **6 predictions**, **4 checkpoint items**.

#### Items

| id | K | format | pair | uses | statement or prompt | form · lever |
|---|---|---|---|---|---|---|
| R06.T1d | T | — | R06.T1v | invariant | closed book, before reading: `method AllNullable(rs: seq<Re>) returns (b: bool) ensures b <==> forall i :: 0 <= i < \|rs\| ==> Nullable(rs[i])`, with a `while` loop; record the first try with `scripts/firsttry.sh R06 --check` | exec hole `{ assume false; }` · none |
| R06.T1v | T | — | R06.T1d | invariant | `pub fn all_nullable(rs: &Vec<Re>) -> (b: bool) ensures b == (forall\|i: int\| 0 <= i < rs.len() ==> nullable(rs@[i]))`, with a `while` loop calling the exec `is_nullable` | `external_body` + `unimplemented!()` · none |
| R06.P3dv | P | verdict | — | — | `lemma StarRepeat(r: Re, s: seq<char>) requires r == Star(Chr('a')) && forall k :: 0 <= k < \|s\| ==> s[k] == 'a' ensures Matches(r, s)`, whose body calls `StarRepeat(r, s[1..])` for a non-empty `s` (and names the split): [x] under `decreases r`; [y] under `decreases \|s\|` (Verus: the same proof fn, `decreases r` / `decreases s.len()`). Answer form `D:<x>,<y> V:<x>,<y>`, each v as in R01.P1dv | slot · block |
| R06.P6dv | P | verdict | — | — | A shortcut for stars: `lemma StarShortcut(a: Re, c: char, s: seq<char>) ensures Matches(Star(a), [c] + s) <==> Matches(Star(Deriv(a, c)), s)`, whose body calls `DerivCorrect(a, c, …)` on every prefix of `s` it needs. `D:<v> V:<v>` | slot · block |
| R06.P1d | P | value | — | — | `dafny/checks/R06_checks.dfy`: `expect Deriv(Cat(Star(Chr('a')), Chr('b')), 'a') == ???;`. Answer form: the term in the constructor syntax of A1, no spaces | check-unit slot |
| R06.P2v | P | value | — | — | `specimens/R06/P2v.rs.specimen`: `assert(nullable(deriv(deriv(R, 'a'), 'b')) == ???) by (compute_only);` for the pattern `R` of P1d. Answer form `true` or `false` | specimen slot |
| R06.P4d | P | obligation | — | — | `specimens/R06/P4d.dfy.specimen`: a loop that advances `cur := Deriv(cur, s[i])` over `s` with the invariant `Matches(r, s) ==> Matches(cur, s[i..])` (and the bounds), the body's proof call as H2 ships it, and after the loop two labelled asserts. Labels: [a] the invariant on entry, [b] the invariant preserved, [c] `Matches(cur, []) ==> Matches(r, s)`, [d] `Matches(r, s) ==> Matches(cur, [])`. Which fail? | specimen slot |
| R06.P5v | P | obligation | — | — | `specimens/R06/P5v.rs.specimen`: the same for the Verus matcher | specimen slot |
| R06.W1d | W | — | — | — | `lemma DerivBase(r: Re, c: char, s: seq<char>) requires r.Empty? \|\| r.Eps? \|\| r.Chr? ensures Matches(Deriv(r, c), s) <==> Matches(r, [c] + s)`: the base cases, worked | given, live |
| R06.W1v | W | — | — | — | `proof fn lemma_deriv_base(…)`, the same | given, live |
| R06.W2d | W | — | — | — | a loop with its invariant read as the induction hypothesis of an induction on the counter (`AllSame(s, c)`: every character of `s` is `c`) | given, live |
| R06.W2v | W | — | — | — | the same over `&Vec<char>` | given, live |
| R06.C1d / C1v | C | `write:calc` | — | — | card: `calc` / `calc!` | given |
| R06.C2d / C2v | C | `write:invariant` | — | — | card: loop invariants and loop `decreases` | given |
| R06.C3d / C3v | C | `write:lemma-decreases` | — | — | card: a measure on a recursive lemma / proof fn | given |
| R06.C4d | C | `write:induction-false` | — | — | card: `{:induction false}` and the recursive call it makes you write | given |
| R06.C5d | C | `recognise:induction-auto` | — | — | card: Dafny's automatic induction, stated (a fact this track does not ask you to predict) | given |
| R06.H1d | H | — | R06.H1v | lemma-decreases, calc, induction-false | **The flagship.** `lemma {:induction false} DerivCorrect(r: Re, c: char, s: seq<char>) ensures Matches(Deriv(r, c), s) <==> Matches(r, [c] + s)` (the measure is yours) | bodyless lemma · `{:induction false}` · gate pending |
| R06.H1v | H | — | R06.H1d | lemma-decreases, calc | `pub proof fn lemma_deriv_correct(r: Re, c: char, s: Seq<char>) ensures matches(deriv(r, c), s) <==> matches(r, seq![c] + s)` (the measure is yours) | `proof_note` assume · none · gate pending |
| R06.H2d | H | — | R06.H2v | invariant | **The matcher loop.** `method DerivMatch(r: Re, s: seq<char>) returns (b: bool) ensures b == Matches(r, s)`: the loop (one `Deriv` per character, then `Nullable`), its `decreases` and the proof call in its body are given; the loop invariants and the facts after the loop are yours | annotation hole · none · gate pending |
| R06.H2v | H | — | R06.H2d | invariant | `pub fn deriv_match(r: &Re, s: &Vec<char>) -> (b: bool) ensures b == matches(*r, s@)`, the same | annotation hole · none · gate pending |
| R06.H3d | H | — | R06.H3v | — | **Refute.** `lemma StarUnfoldRefuted() ensures exists a: Re, s: seq<char> :: Matches(Star(a), s) && !Matches(Cat(a, Star(a)), s)` | bodyless lemma · none · gate pending |
| R06.H3v | H | — | R06.H3d | — | `proof fn lemma_star_unfold_refuted()`, the same | `proof_note` assume · none · gate pending |
| R06.H4d | H | — | R06.H4v | calc | **Repair and prove.** `lemma StarUnfold(a: Re, s: seq<char>) ensures Matches(Star(a), s) <==> Matches(Cat(a, Star(a)), s)`: add the hypothesis that makes the claim true, and no stronger one (the `requires` is open in the freeze pin, Δ160), then prove it | bodyless lemma (`requires` open) · none · gate pending |
| R06.H4v | H | — | R06.H4d | calc | `proof fn lemma_star_unfold(a: Re, s: Seq<char>)`, the same | `proof_note` assume (`requires` open) · none · gate pending |
| R06.C6dv | C | `diverge:r06-c6` | — | — | divergence card (its topic is named in the card). **Final section** | given |
| R06.A1d / A1v | A | — | — | — | `/contract R06` (decomposer) on the agent files, under R-v0 | contract |

**Checkpoint (closed book; 4 items; ≥ 3/4 with ≥ 1 per language; `scripts/firsttry.sh R06 --exit`).** Statements, prompts, `uses:` and `need:` lines and shipped forms are in `Solutions/plans/R-author-notes.md` §R06 (checkpoint items are unseen; the Δ133 rule).

| id | K · form | language · file | min | statement or prompt |
|---|---|---|---|---|
| R06.X1d | X · statement-shipped | Dafny · `R06_Checkpoint.dfy` | 5.5 | in the author notes |
| R06.X2d | X · statement-shipped (annotation) | Dafny · `R06_Checkpoint.dfy` | 5.5 | in the author notes |
| R06.X1v | X · statement-shipped | Verus · `exit.rs` | 5.5 | in the author notes |
| R06.X2v | X · statement-shipped (annotation) | Verus · `exit.rs` | 5.5 | in the author notes |

#### Constructs (registry)

- `write_d = ["calc", "invariant", "lemma-decreases", "induction-false"]`, `write_v = ["calc", "invariant", "lemma-decreases"]` — 4 units (3 paired + 1 Dafny), 7 slugs.
- `recognise_d = ["induction-auto"]`, `recognise_v = []`.
- Checked uses (≥ 2 per language): calc d H1d, H4d · v H1v, H4v; invariant d T1d, H2d · v T1v, H2v; lemma-decreases d H1d, X1d · v H1v, X1v; induction-false d H1d, X1d (the checkpoint items' `uses:` lines are in the author notes).

#### Agentic file (decomposer)

- **Shape:** one top statement and nothing else: `lemma BackwardsCorrect(r: Re, s: seq<char>) ensures Matches(Backwards(r), BackwardsStr(s)) <==> Matches(r, s)` / `proof fn lemma_backwards_correct(r: Re, s: Seq<char>)`. A1b's lemmas are in scope. Dafny: S1 closed (the spike's reference decomposition verifies). Verus: **pending spike S1** (the Verus spike built neither `backwards` nor a decomposition); fallback `lemma CatAltDistrib(a: Re, b: Re, c: Re, s: seq<char>) ensures Matches(Cat(Alt(a, b), c), s) <==> Matches(Alt(Cat(a, c), Cat(b, c)), s)`, which needs its own reference before it replaces the Verus statement.
- **CONTRACT** `goal:` prove the top statement by decomposition · `allowed-files:` the agent file · `acceptance:` every new helper lemma is first added as a hole (its statement, no proof) and the file is re-run green with only leaf holes before any helper is proved · after every edit `scripts/vcheck <file>` shows no error (holes allowed until the end) · the final `scripts/vcheck --gate <file>` exits 0 with zero holes · `scripts/specfreeze --against <snapshot> <file>` reports the top statement unchanged · `scripts/vaudit` reports no finding.
- **Learner follow-up (22 min):** draw the delivered decomposition tree in a `DECOMPOSITION` block (each helper, who used it, whether it was needed: delete it in a scratch copy and re-run), and mark the step where the transcript was not green, if any.

#### Itemized minutes (total 462)

| line | items | min |
|---|---|---|
| setup | the A1b layer tour | 8 |
| test-out | T1d, T1v | 10 |
| read | chapter | 60 |
| worked | W1d–W2v (4 × 3 = 12) + WRITE cards C1d–C4d (7 × 2.5 = 17.5) | 30 |
| cards | C5d (1.5) + C6dv (4.5) | 6 |
| predicts | P1d–P6dv (6 × ≈ 2.4) | 14 |
| flagship | H1d 60, H1v 68 (hard band) | 128 |
| matcher loop | H2d, H2v (2 × 12) | 24 |
| refute → repair → prove | H3d, H3v (2 × 5) + H4d, H4v (2 × 12) | 34 |
| checkpoint | X1d–X2v (4 × 5.5) | 22 |
| agent | A1d/A1v and the `DECOMPOSITION` block | 22 |
| paper | card 03.4 (15), the flagship `Cat` case on paper (20), the matcher's invariant as an IH (10) | 45 |
| bench card | a stripped R06 lemma | 20 |
| viva | 6 of 12 | 30 |
| calib | | 9 |
| **total** | | **462** |

The flagship's minutes come from the lines the plan review freed: the earlier draft's manual-induction pair (12) and small cuts to setup, reading, worked examples, predictions, the matcher loop, the agent follow-up, the paper and the bench card.

#### Registry fields (R06)

```toml
status = "authoring"
exercises = ["dafny/R/R06_Induction/core/R06_Induction.dfy", "dafny/checks/R06_checks.dfy", "verus/r/r06_induction/src/lib.rs", "specimens/R06/"]
exits = ["dafny/R/R06_Induction/exit/R06_Checkpoint.dfy", "verus/r/r06_induction/src/exit.rs"]
agentic = ["dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy", "verus/r/r06_induction/src/agent.rs"]
units = ["dafny/R/R06_Induction/core", "verus/r/r06_induction"]
layer = "A1b"
langs = ["d", "v"]
engines = ["contract"]
write_d = ["calc", "invariant", "lemma-decreases", "induction-false"]
write_v = ["calc", "invariant", "lemma-decreases"]
recognise_d = ["induction-auto"]
recognise_v = []

[module.imports]
"dafny/given/R/RG_A1b_Facts.dfy" = "core"
"verus/given/rg_re_a1b/src/lib.rs" = "prelude"
"dafny/R/R06_Induction/core/R06_Induction.dfy" = "core"
"dafny/checks/R06_checks.dfy" = "core"
"dafny/R/R06_Induction/exit/R06_Checkpoint.dfy" = "core"
"dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy" = "core"
"verus/r/r06_induction/src/lib.rs" = "prelude"
"verus/r/r06_induction/src/exit.rs" = "prelude"
"verus/r/r06_induction/src/agent.rs" = "prelude"
```

---
## 7. Cross-module checks (band 1)

| check | rule | R01 | R02 | R03 | R04 | R05 | R06 |
|---|---|---|---|---|---|---|---|
| WRITE units / slugs | ≤ 6 / ≤ 10 | 3 / 6 | 3 / 6 | 4 / 4 | 2 / 4 | 3 / 4 | 4 / 7 |
| uses per WRITE slug and language | ≥ 2 checked H/X/T | met | met | met | met | met | met |
| cross-language (`dv`) predictions | ≥ 2 per module | 2 | 2 | 2 | 2 | 2 | 2 |
| predictions in all | — | 6 | 5 | 4 | 6 | 4 | 6 |
| holes (D / V / py) | paired | 5 / 5 | 5 / 5 | 5 / 5 | 6 / 6 | 4 / 4 / 2 | 5 / 5 |
| hole minutes D / V | design share | 12 / 12 | 25 / 35 (45/55) | 35 / 35 | 35 / 35 | 36 / 36 | 89 / 97 (H1–H4; the Verus flagship is the longer reference) |
| checkpoint | R06: 2 D + 2 V, ≥ 3/4, ≥ 1 per language | — | — | — | — | — | X1d, X2d, X1v, X2v |
| import tiers | Dafny `core`, Verus `prelude` throughout band 1 (no library before R07) | yes | yes | yes | yes | yes (+ `py-fvh`) | yes |
| layer | R01 none; R02–R05 A1; R06 A1 + A1b | — | A1 (declares) | A1 | A1 | A1 | A1b (declares) |
| minutes | design §8.2 | 276 | 342 | 300 | 360 | 402 | 462 |

**Band total** 2,142 min = 35.7 h, as design §8.1. **Marker-level check (DVR1's records lane):** marker-only stubs of every item above, at these paths, in a scratch copy of the registry with §6's fields applied, must pass `check_course_map.py --only registry` and `--only coverage`; the full checker on the real files is DVR1's integration lane's.

**Ordering and naming rule for cards** (as `QPLAN.md` §5): a divergence or false-friends card sits in its file's final section, under a heading that tells the learner to record the module's predictions first; its slug and demo files are named by item id, never by topic; its demos state no outcome in prose; a demo whose output settles a prediction carries `// after: <item id>`.

---

## 8. Open questions (for the orchestrator, DVR0 and DVR1)

1. **R1 · Viva minutes.** This plan reads design §8.2's totals as including each R module's 30-min viva (design §8.2: "R = 124.9 h standalone (17 h of lab halves, 30-min vivas)"); Q's tier vivas sit outside their modules' minutes. If the orchestrator reads the totals as excluding them, R grows by 8 h and every R module's "viva" line moves out of its total. **Open** (orchestrator; Δ181): not decided in this round; the plan's reading stands until it is.
2. **R2 · The R track's Dafny induction setting** (Δ78: DVR1's call). Proposed: a `[[override]]` `R03-R16` with `manual-lemma-induction = true` in `dafny/options/core.toml` and `std.toml`, R01–R02 on the default with `{:induction false}` levers where the empty-body gate needs them. Needs a DELTAS entry. **Adopted by DVR1** (2026-10-17 UTC, Δ251): the proposed override is implemented in both option files before R03 is armed; R01–R02 retain their default setting and pinned per-item levers.
3. **R3 · A1's Dafny `Matches` is ghost.** The spike files still make it a compiled `predicate`; a compiled `Matches` lets R06.H2d answer itself (`b := Matches(r, s)`). DVR0's reconciliation step (§2.5 item 1) makes it ghost and re-runs the Dafny gate; if DVR0 keeps it compiled, R06.H2d needs another target. **Open** (DVR0; Δ181): the reconciliation step's as-built entry records it.
4. **R4 · Renames** (§5.5): `Size` → `NodeCount`, `Rev` → `Backwards`, string `Reverse` → `BackwardsStr`, and after the Lean R07–R16 scan `Step` → `Advance`, `Compile` → `Emit` (and their lemma names), applied in this plan, not yet in the spike files (§2.5). DVR0's `avoid.sh` baseline confirms or extends the list. **Decided** for the scan (Δ180): the names-only scan of the Lean exercise files is accepted, and every later scan goes through `scripts/avoid.curated` only. The spike files' renames stay DVR0's (§2.5).
5. **R5 · Check units for R.** R01, R02 and R06 add `dafny/checks/R0x_checks.dfy` to their `exercises` lists when armed (the registry's planned records list none). **Open** (DVR1; Δ181).
6. **R6 · Property tests in Verus are not tool-counted holes** (a `#[test]` body outside `verus!`). R02's first property tests therefore live in the agent follow-up (checked by `scripts/vcheck --test` and the review), not as H items. **Open** (DVR1; Δ181).
7. **R7 · CV and the frozen statistics.** R05.H2py computes a CV from the standard library's `statistics` and composes `fvh.stats.bootstrap_ci`. If design §9.2 item 4 ("statistics code exists only in the frozen `fvh` core") is read to forbid even that formula in learner code, `fvh.stats` gains `cv` (a frozen-core change: a DELTAS entry, Δ134) and H2py composes it. **Open** (orchestrator; Δ181).
8. **R8 · Setup for an R-first learner.** Setup lines assume the toolchains are installed; a learner who starts with R adds prework P0 (90 min) once. The README states this. **Open** (the README's owner, DVR1; Δ181).
9. **R9 · A boundary case of the owner tags.** Q08.P1dv (whether a refinement may strengthen a frozen statement's `requires`) and R03.P1d/P2v (where an API's strengthened `requires` fails at call sites) are recorded as distinct. If the orchestrator disagrees, R03's pair moves to a call-site question that names no `requires` change (author notes §R03 has a replacement). **Open** (orchestrator; Δ181): recorded as distinct until decided.
10. **R10 · Captured vs to-capture answers.** This lane captured six answers on the pins (author notes §0); every other prediction's answer, every gate result and every band figure is DVR1's to capture, through `scripts/pins.py --update --ref --module <ID>` and `scripts/firsttry.sh <ID> --empty-body`, before arming. R04.P5d is Dafny-only now (§5.1); the Verus `assume` delivery of the audit drill is run on a crate (a lone `.rs` file fails the Verus gate's crate-level JSON checks). The spike lanes' results (author notes §1.4) are evidence for the references and gates of the items they cover, not for the shipped files. **Open** (DVR1; Δ181): every capture before arming, under §0's four results (Δ173).
11. **R11 · Open statements in the freeze** (Δ160). R01.H3d/H3v and R06.H4d/H4v leave a `requires` open, R04.H4d/H4v a definition. The tools owner confirms that the freeze pin can leave a `requires` (not a whole statement) open. R04.H4d depends on QPLAN §30 Q52's `open_bodies` for Dafny functions and predicates; R04.H4v's `uninterp spec fn` → `open spec fn` is already covered by the Verus `open_bodies` rule (QPLAN §6 Q7, Δ120), so R asks nothing new for Verus. Without Q52, R04.H4d ships its definition in an exit-style prompt-as-heading block. **Decided** for Q52 (Δ181): the tools lane of this round builds QPLAN §30 Q52; R04.H4d waits on its as-built entry. The `requires`-only open statement stays the tools owner's to confirm.
12. **R12 · Spike S1, after the spikes.** S1 is closed for `DerivCorrect` in both languages and for the Dafny decomposer, so R06.H1d/H1v carry no star-free fallback and A2's `DerivCorrect` is general. Open: the Verus decomposer (R06.A1v); if DVR0's Verus `backwards` family does not pass the gate, R06.A1v's top statement becomes `CatAltDistrib`, which then needs its own reference first (§0). S3 is closed (no star-free or forward-jump restriction at R16). **Open** (DVR0; Δ181): the Verus decomposer's gate.
13. **R13 · The avoid list's curated Lean names.** `scripts/avoid.curated` copies names from the Lean course's exercise files; who refreshes it when the Lean course changes (DVR0 proposes: the integration lane of each R phase, with a stale-entry check against the Lean files' current names). **Decided** in part (Δ180): later scans go through `scripts/avoid.curated` only; who refreshes the list stays open (DVR0's proposal stands until decided).
14. **R14 · Band-2 and band-3 itemized lines** (§3) are [A]: DVR2 and DVR3 replace them with item plans in this file's grammar before arming, and may move minutes between lines but not change a module's total without a DELTAS entry. **Open** (DVR2, DVR3; Δ181).
15. **R15 · Gate variants the R references need** (tools owner; DV4 or DVR0). (a) A Verus empty-body variant that keeps `let tracked` lines and strips only asserts and proof blocks: without it, R11's `Arena::get`, `set` and `free_all` cannot be gate-tested, so the arena line stays at 0 or on its fallback (§3 R11). (b) Named-return proof fns: the wrapper's `{}` body does not type-check; the Verus lane substituted `{ arbitrary() }` (`Solutions/spikes/regex/verus/tools/gate_ret.py`). Proposed: the wrapper adopts that rule. **Decided** for (a) (Δ181): the same request as QPLAN §30 Q65(b), which the tools lane of this round builds; (b) stays open for the tools owner.
16. **R16 · Records-lane items.** (a) The coverage row S8.vc-generator-soundness (d) names R11 as its home, but R11 proves a derivation checker sound, not a VC generator: the row gains a `gap` (proposed text in §3 R11), or DVR2 adds a Dafny soundness item for the checker's rule set. (b) `layer = "A1b"` (R06) needs the registry's layer field and the checker to accept the new layer name. (c) The budgets of §4.3 (with QPLAN §30 Q55). (d) The proposed waivers W15–W19 (§5.4) into design §9.3 and `avoid.waivers.tsv`. **Decided** (Δ181): (a) the gap is recorded (Δ179) unless DVR2 adds the checker-rules soundness item; (b) adopted (Δ174), the registry and checker change is the avoid lane's; (c) Δ176; (d) W15–W18 adopted, W19 provisional (Δ177).
17. **R17 · DELTAS entries this revision needs** (orchestrator): the layer A1b and the re-supply list of §2.4; A3's single-digit bounds and R09's overflow-free expansion budget in place of "overflow-checked bounds" (design §8.2 R09); A5's opaque `Accepts`, one-step and layout lemmas and the renames; R16's correctness split into soundness and completeness items and jump threading gated; Lab α at 4,800 Qwen and 100 Claude policy calls (design §11.3 says 5,120 and 160); R06's re-itemized minutes and its new H3/H4 and checkpoint objects (author notes); R04.P5d Dafny-only and R04.P6dv, R05.P3dv replaced. **Decided** in part: A1b (Δ174), R09's bounds and budget (Δ175), Lab α (Δ176). The rest (A5's opaque `Accepts`, its lemmas and the renames; R16's split; R06's minutes and objects; R04's and R05's prediction changes) is **open** for DVR0's as-built entry and DVR1 (Δ181).
18. **R18 · What R asks of the Q lane** (plan review, both tracks): Q12's stage specimens redrawn within Q's own tags (§5.1); Q14.H5v as a `PPtr` list, which makes W19 unnecessary; Q18's Lab 3 impossible tasks of kinds other than Lab γ's (§4.3), else W17 stands. **Decided** (Δ181): §5.1 says only that Q12's specimens stay within Q's tags; Q14.H5v and W19 as §5.4's decision says (Δ177); W17 is adopted (Δ177).

## 9. Band 2 item plans — R07 construction plan (2026-10-17)

This section extends the record-level band2 plan before activating R07. R03
remains planned with its recorded primitive-packaging blocker. R07 uses only
the frozen A2 class/matcher API, not R03 learner files or its parked adapter.
Library access begins here under OD8; no earlier tier is changed. R06's full
reversal decomposer spike is closed (Δ256), superseding its older pending label.

### R07 — Libraries: what they cost

The module has one std-tier Dafny unit and one all-tier Verus crate. The frozen
A1/A1b/A2 dependency chain remains complete. Add no import of an earlier
learner file. The five predictions and T1 precede reading and worked material.
References, actual verdicts, proof-line counts, admission and seed controls
belong in protected author notes; until those pass, admissible minutes stay0.

| item | kind / pair | task and form | planned minutes |
|---|---|---|---|
| T1d/T1v | closed-book test-out | Bound the size of the observed character alphabet by the sample sequence length; typed proof hole, explicit library call | 5 each |
| W1d/W1v | worked | Read a library contract, bind its type/sequence arguments and call its named lemma explicitly; a separate class sample | 3 each |
| W2d/W2v | worked | Translate between a class's semantic membership and its execution contract without opening private ranges | 3 each |
| H1d/H1v | paired proof hole | Filtering by class membership preserves a sample-prefix relation; library-backed proof with exact prefix bounds, statement fixed | 8 each |
| H2d/H2v | paired proof hole | Characterise duplicate-free filtered samples by equality of sequence length and finite observed-alphabet cardinality; both directions, statement fixed | 11 each |
| H3d/H3v | paired proof hole | Bound the flattened sample batch by its number of samples times a supplied per-sample bound; bridge the library's two flattening forms, statement fixed | 12 each |
| P1d | value | A concrete class-filtered sample, answer committed before evaluation | 3 |
| P2v | value | A different concrete class-filtered sample, answer committed before evaluation | 3 |
| P3dv | verdict | Two observed-alphabet contracts with their printed assumptions; compare statement scope | 3 |
| P4v | FAILS | Indexed library calls over a filtered sample; name the failing labelled obligations | 3 |
| P5dv | verdict | A batch bound under its printed per-sample hypothesis; preserve all quantified premises | 3 |
| C1d/C1v | WRITE | Explicit library calls with fully instantiated parameters | 2.5 each |
| C2v | WRITE | Scoped broadcast use after a named-call version has been understood | 2.5 |
| C3d/C3v | WRITE | Record a qualified symbol and a reproducible search-ladder step | 2.5 each |
| C4dv | divergence | std/all import tiers and their transitive dependency boundary | 3 |
| C5dv | recognise | Tool pin, solver identity and artifact provenance before interpreting a result | 3 |
| A1d/A1v | retriever race | Fresh library-only class/sample goals; the same frozen tasks and acceptance for both retrieval arms | 25 total follow-up |

Four Dafny holes and six Verus holes include T1. There is no checkpoint in R07. Two Verus scope holes follow the given explicit-call versions, so broadcast-use is actually exercised. H minutes
sum to62; the two test-outs sum to10. Each shipped hole needs native reference,
canonical empty-body/automation controls and three seeds before admission.
If a proposed goal verifies empty, replace it before admission and record the
reason; no solver setting or guard exception may create artificial difficulty.

The chapter teaches the library installation/pin check, explicit-call-first
search ladder, contract instantiation, finite sets versus unbounded sets,
scoped broadcast, transitive tiers and the actual trust surface. A mismatch lab
runs disposable private controls through the existing wrapper and preserves
its refusal; it never edits the installed toolchain or frozen unit options.
The trust audit names proved library code, external specifications and the
compiler/solver pipeline. It does not interpret a lemma import as a new axiom.

The retriever race is a matched-task demonstration with a declared search
allowance, fixed attempts/time/token budgets and complete failure accounting.
Run each arm in fresh sessions; no shared transcript, leaked reference or
cross-arm cache. Live runs remain deferred D45 debt. Native author reference
checks cannot supply experimental success rates. Work an explicitly synthetic
small data table by hand with the unbiased pass@k estimator, then check it by
composing frozen fvh.stats.pass_at_k; do not implement a second estimator.
Report per-task estimates before aggregation and retain n, c, k and exclusions.
The learner writes research/EVAL.md's R-v0 section by hand; authoring supplies
prompts and protected gold/flawed examples, not a learner report.

The written pair holds card06.5 only, with a pinned local source range and
eight-field rubric. Review bar: library-conventions. Bank:12 questions in two
disjoint six-question draws, one actual native live predict per draw and two
paired parallel problems. Sixth bench card: strip an own R07 library goal,
label it course-derived and retain provenance, never call it an independent
unseen benchmark. Code/paper/bank references and leak patterns are protected.

The360-minute record budget remains: setup10, test-out10, read60, worked30,
cards6, predicts15, holes62, mismatch20, trust20, pass@k15, EVAL15, agent25,
paper15, bench20, viva30, calibration7. The card WRITE examples occupy the
worked allowance; recognise/divergence cards occupy the separate6minutes.

**R07 scope refinement before admission of the final file.** Add H4v/H5v,
two fixed-statement proof holes that require narrowly scoped broadcast after
complete explicit-call W3v/W4v. The original eight holes passed native admission;
these two need their own full controls. Verus H1/H2/H3 now allocate6/7/8minutes
and H4/H5 allocate5each, preserving31Verus hole minutes and62for the pair.
Dafny H1/H2/H3 retain8/11/12. Native card grammar uses write:<slug>, not uses.
No claim of final ten-hole admission or scope-task completion is made yet.

## 10. Band 2 item plan — R08 abstraction (2026-10-17)

This plan precedes activation. R08 uses A2, without importing an earlier
learner file. Its supplied semantic model bindings are fixed definitions.
Dafny implements an abstract Pattern/WordLanguage/MatchWord specification by
refinement; Verus implements a WordMatcher trait with a word-language spec
method and a matching execution contract. The derivative engine uses the
re-supplied matcher. The class engine recognises one-character words through
the re-supplied class membership API. No band1 proof is supplied anew.

**Provided interface, F6.** The abstract Dafny matcher belongs to a frozen
given-role statement file. Extend the existing SHA-pinned statement handling
for that exact R08 interface, retaining challenge restrictions for other
modules and all hash/immutability checks. Its A2 given file contains only the
abstract interface, not a completed R08 implementation. The Verus counterpart
is a given A2 trait, with no assumed implementation. Later certifying and VM
engines can use the same interfaces without importing a learner's R08 files.
Recheck A2 gates/audits and the earlier R07 consumers after this additive API
extension; do not alter existing definition bodies or permit an extra axiom.

| item | form / pair | task | planned minutes |
|---|---|---|---|
| W1d/W1v | worked | A complete literal-character engine with its own frozen model; instantiate an interface client | 3 each |
| W2d/W2v | worked | Read a model/implementation square and identify the actual obligation and receiver | 3 each |
| H1d/H1v | execution hole | Implement the derivative engine under the fixed matcher interface and provided regex model; type/model bindings stay fixed | 15 each |
| H2d/H2v | execution hole | Implement the class engine's whole one-character-word language, including all other lengths; model stays fixed | 16 each |
| H3d/H3v | proof hole | Relate an opaque whole-word model to its provided semantic definition by a local reveal | 6 each |
| H4d/H4v | proof hole | Relate an opaque one-step residual model to the original prefixed-word language using the supplied A2 correctness interface | 8 each |
| P1d | value | A literal-character refinement invoked through its interface on a concrete word; Boolean literal | 3 |
| P2v | value | A different literal-character trait model on a concrete scalar word; Boolean literal | 3 |
| P3dv | verdict | Same literal execution under full-word versus shortened-word model bindings; native verdict for each complete program | 3 |
| P4v | obligation | Two receiver instances and one word: name the labelled claims justified by the actual call's contract | 3 |
| P5dv | verdict | Equivalence of two complete one-character model bindings; retain the exact sequence-length/index conditions | 3 |
| C1d/C1v | WRITE | Refinement / trait-contract syntax on a separate literal model | 2.5 each |
| C2d/C2v | WRITE | Reveal a separate supplied opaque literal model | 2.5 each |
| C3d | recognise | Abstract modules and provided specification files | 1.5 |
| C3v | recognise | The spec model of a trait implementation | 1.5 |
| C4dv | divergence | Refinement requirements and implementation promises; directions are stated facts, not predictions | 2 |
| C5dv | divergence | An implementation can match its own different model; compare the frozen intended binding | 2 |
| A1d/A1v | semantic debugger | The original model promises the whole word, but a complete implementation passes a shortened word to its backend; preserve interface and model | 25 total follow-up |

Four H holes per language, no test-out or checkpoint. WRITE sets: Dafny
refines/reveal, Verus trait-spec/reveal, each with at least two actual hand
items. Total H minutes90 (45 each language). Admission stays0 until native
reference, three seeds, canonical automation controls and execution trivial
controls pass. A failed wiring prototype is not a semantic-negative control.

The refinement lab lists the original input domain and result relation, the
implementation's model binding, every generated requirement and the side
that discharges it. Requires weakening and ensures strengthening are taught
as facts under the actual language rules; R08 does not repeat the other
track's reserved legality prediction. Preserve native stages for diagnostics.
The agent's planted defect must reach verification with no holes and a genuine
semantic postcondition failure. A changed-model delivery can verify but must
fail the original snapshot freeze. The positive repair must preserve every
provided contract and model body and pass the full gate and audit.

The chapter has a refinement square and the direction-of-obligations diagram,
with at least one further model/implementation view. The written pair holds
card06.7 and a refinement-obligations problem, fifteen minutes each. The bank
has12 questions, disjoint six-question draws with actual native live probes,
and two paired parallel problems. The seventh bench card strips an own
completed abstraction goal, retaining its fixed interface and course-derived
provenance. Live model/contractor validation remains D45 debt.

The354-minute record remains: setup10, read60, worked30, other cards7,
predicts15, holes90, refinement lab30, agent25, paper30, bench20, viva30 and
calibration7. The two language-specific hole totals remain45minutes each.

**R08 as-built prediction scope.** P3 now contrasts the same literal execution
under a whole-word model and a consistent shortened-word model. It directly
exposes model meaning, while P5 checks equivalence of two genuinely equivalent
full-word bindings. This replaces the preliminary generic proper-prefix claim;
no refinement-legality prediction is added. C3v recognises open-spec visibility,
since trait-spec is already WRITE and cannot also be RECOGNISE.

## 11. Band 2 item plan — R09 effects (2026-10-17)

This plan precedes activation; R09 remains planned. A3 supplies definitions,
syntax, well-formedness and parser specification predicates, not a parser,
execution lowering or lowering-correctness proofs. The canonical paired parser
uses the Dafny spike's finite single-character-bound grammar: literals,
escapes, groups, alternation, concatenation, classes and postfix *,+,?,{d},{d,d}.
Positions count Unicode scalars. The Verus spike's extra {d,} form and missing
classes are fidelity discrepancies to repair, not an accepted port. Preserve
nested source spans where the syntax declares them. Unsupported syntax must
receive the same specified error position in the paired port.

| item | form / pair | task | planned minutes |
|---|---|---|---|
| T1d/T1v | closed-book execution | advance a cursor and propagate a single-bound error without losing its original position | 5 each |
| W1d/W1v | worked | one-character bound recogniser and complete native result interface | 3 each |
| W2d/W2v | worked | read failure propagation and the actual result obligations | 3 each |
| W3d/W3v | worked | concrete syntax, source spans, lowering, error positions and the explicitly mirror-relative parser contract | 3 each |
| W4d/W4v | worked | recursive copy/optional-copy interfaces used by the final interval proof, and budget arithmetic facts | 6 each |
| H1d/H1v | execution | parse a finite counted suffix under completeness and error-position contracts | 12 / 15 |
| H2d/H2v | execution/annotations | class-body progression, preserved accumulator and completion at the first closing delimiter | 9 / 12 |
| H3d/H3v | execution | enforce the lowering's expansion cap without overflowing the bounded multiplication | 8 / 9 |
| H4d/H4v | proof | finite repetition denotes some number of copies within the original bounds, using the printed module-local worked helper contracts | 14 / 16 |
| H5d/H5v | execution/annotations | advance the parser cursor while preserving old input and position guarantees | 7 / 8 |
| P1d | value | complete single-bound propagation on a concrete invalid suffix | 3 |
| P2v | value | complete single-bound propagation on a different scalar input | 3 |
| P3dv | verdict | direct product versus guarded division at the full machine boundary | 3 |
| P4v | obligation | labelled mutable-cursor calls under the original position bounds | 3 |
| P5dv | verdict | error-position preservation versus replacing the propagated location | 3 |
| A1d/A1v | refactorer | preserve the selected parser's original statement and differential harness while porting/refactoring its body | 25 follow-up |

H-hole totals50D/60V=110minutes; T1d/T1v use the separate10-minute test-out
allocation. Minutes remain0 until each actual item passes
canonical native admission and its complete reference passes three seeds.
A trivial Err return must fail the Counted/ClassItems completeness clauses.
WRITE constructs include failure propagation and old-state mutation, with at
least two actual hand uses for each construct declared WRITE. Native probes
must establish the pinned :-/? and old/final syntax before those cards arm.
No decimal digit-run parsing, previous learner imports or trusted adapter.

The60-minute port audit compiles the actual Dafny parser to Python and the
actual Verus implementation to Rust. Independently transcribed mirror contracts
get explicit implication proofs labelled relative to the mirror; differential
execution and shared mutant-kill parity remain separate, necessary evidence.
The corpus includes malformed suffixes, non-ASCII scalar positions, classes,
escapes, single-digit extremes, reversed bounds, truncated input and cap edges.
Both acceptance and exact error positions are compared; language/set-only
agreement cannot hide a span or failure discrepancy. Preserve native tool and
execution stages; no parser grammar theorem is inferred from safety or tests.

The written pair contains card06.11 PUMPKIN Pi and the fidelity method. The
bank has12questions, disjoint six-question draws with actual native live probes,
and two paired parallel problems. The eighth bench card strips an own effects
goal and discloses course-derived provenance and prior exposure. The overflow
and encoding divergence lab takes25minutes. The existing444-minute record is
unchanged: setup8,test-out10,read60,worked30,cards8,predict15,holes110,port60,
divergence25,agent25,paper35,bench20,viva30,calibration8. Live actor validation
remains D45 debt; no native author run substitutes for it.

**R09 before activation, prototype reconciliation.** The cursor test-out and H5
provide two hand uses of both propagation and old-state mutation. Input text
is a mutable field whose value must be preserved, so old-state promises are
meaningful. H4 combines the printed module-local helper contracts; those
worked helpers are not in A3. The worked allocation is30minutes across four
paired examples. The paired parser retains literal-fragment success/meaning
guarantees as well as safety, finite-count completeness and class completion.
V's A3 AST uses canonical sorted range insertion adapted from the existing A2
given construction, with explicit AST ranges; the frozen A2 API remains opaque
and unchanged. Direct class-range output, source spans and error locations
are compared before any claim about later expansion-size fidelity. A zero
upper repetition bound must not reject an unused oversized operand.


## 12. Band 2 item plan — R10 invariants in types (2026-10-17)

This plan precedes R10 activation. R09 source907f0af is the local construction
candidate; its workflow's17commands pass, with5prediction and2test-out
receipts. Focused CI found only the quoted unknown verdict slots in static;
keep that run untouched, correct their serialization on the R09 branch when
it ends, then inherit the fix here. D45 actor debt and parked R03 remain skipped.

A4 contains Normal/NormRe, smart-constructor definitions and executable raw
smart operations, the normalizer/normal derivative models, pure shape-only
closure, and CatCongRight/CatCong/StarOfEps. It does not publish semantic
smart-constructor proofs, normalizer language preservation or R11 certificate
soundness/completeness/search. The executable normalizer is not a given:
D's normalization model is ghost; a by-method implementation must supply the
compiled computation. V needs a normalizer model absent from its old spike.
NormRe's library boundary promises representation shape, not preservation of
a caller's original language. No extra R08 matcher interface is re-supplied.

A4's certificate definitions use the same relative split offsets in both
languages. The old D spike's word-relative certificate and V spike's absolute
slice certificate are different representations; reconcile before freezing.
The checker model is ghost. A slice alias may relate it to a subrange, but
R11 supplies the actual checker/proofs. Keep the V usize representability
domain explicit in later completeness claims. No earlier learner imports.

| item | form / pair | task | planned minutes D / V |
|---|---|---|---|
| W1d/W1v | worked | Normal/NormRe boundary, erased fields and native subset/by-method or type-invariant/Ghost/Tracked syntax | 8 / 8 |
| W2d/W2v | worked | runtime predicate, Option result and precondition versions of one fixed shape invariant | 5 / 5 |
| W3d/W3v | worked | the given shape/congruence facts and a client that distinguishes shape from language | 2 / 2 |
| H1d/H1v | execution | accept exactly normal raw inputs into a packet with an erased node-count witness (Option completeness included) | 8 / 10 |
| H2d/H2v | execution/proof | concatenate packets under the shape model and rebuild erased cached evidence from the branches and original caches | 12 / 12 |
| H3d/H3v | proof | every already-normal regex is a fixed point of the normalizer; derive idempotence separately | 15 / 15 |
| H4d/H4v | execution | structural compiled normalization agrees with the ghost model and returns a valid packet; preserve termination | 20 / 18 |
| P1d | value | one concrete normal-form branch and its executable node count | 3 |
| P2v | value | a different fixed shape/erased-model expression | 3 |
| P3dv | verdict | distinguish runtime/Option enforcement from a call that fails the original precondition | 3 |
| P4v | obligation | labelled claims under the actual invariant and cached proof data | 3 |
| P5dv | verdict | a normal output under a shape-only promise versus the same output under the original language relation | 3 |
| A1d/A1v | spec-to-proof flagship | human writes three constructor statements, witnesses and snapshot; contractor supplies bodies/proofs under those original statements | statements40 + audit20 |

H totals55D/55V=110minutes; admission/minutes remain0 until actual native
controls and three-seed references pass. MkAltCorrect is not a hole: the
spike's empty proof already verifies. Smart-constructor language statements
are the flagship's human work; no prewritten formal answer silently replaces
it. Its initial actor files have fixed signatures and shape-typed results,
with open statement clauses and counted body holes. Human-written clauses
are snapshotted before any actor edit and remain frozen thereafter.

The statement readiness check uses the proposed contract on arbitrary normal
inputs and an arbitrary fresh normal result. It proves the proposed
preconditions over the original domain, then proves that those preconditions
and the proposed postconditions imply the original constructor language.
This is the logical consumer of an abstract provider, with no assumed body. A shape-only result must not
pass merely because the actual given constructor definitions preserve the
language: the abstract result is arbitrary. Native proof failure establishes
that readiness was not proved, not a universal semantic counterexample.
Implementability, nonvacuous compiled examples, full native gates and original
snapshots are separate checks. No concrete implementation is assumed and no
new trust is introduced. Live actor outcome remains D45 debt.

Declare WRITE only after native probes: D subset types, by-method and ghost
fields; V type-invariant, Ghost and Tracked. H1/H2 provide two actual hand
uses of each declared construct. Runtime erasure observations must compile
actual programs and inspect the retained generated bodies/types, not infer
execution from a proof. In particular a normal form invariant is not itself
a language-preservation statement.

Keep408minutes: setup5, reading60, worked30, cards8, predicts15, H holes110,
spectrum lab30, flagship statements40/audit20, paper30, bench20, viva30,
calibration10. Paper03.5 is SpecGen: report verifiability separately from
strength and retain actual denominator/budget/source evidence. The written
erasure argument identifies erased data and justifies the compiled result.
Add12bank questions/disjoint six-question draws, two paired parallel problems,
5predictions and ninth course-derived bench instructions. No quota retry,
Claude call or earlier-tier waiver follows from local author controls.

## 13. Band 2 item plan — R11 theory (2026-10-17)

This plan preceded activation with R11 planned/admission0. Parent98b7dad
is the R10 source checkpoint. R10 focused CI and scripted STUDY workflow run
on an untouched worktree; inherit final formatting/results after they end.
Keep D45 live work and R03's primitive boundary parked under the user request.
The S2 PointsTo arena has three exec functions without admissible gates; record
and skip that lane, using the already specified Vec-backed fallback only after
its own complete four-result admission. Do not call index invariants PointsTo
permissions or claim the still-gated permission coverage has been achieved.

A4 remains frozen. Its relative-word certificate definitions are imported,
never replaced by the absolute-offset old Verus spike. V slice checking uses
the same relative certificate through a slice alias. Soundness is general;
V completeness states its word-length<=usize::MAX representability domain.
A runtime checker checks split bounds before computing an absolute slice end.
No semantic R10 answer, executable full normalizer or R11 checkpoint solution
is added to a provided layer. The matcher loop can use provided raw A2
derivatives, so R10 semantic proofs do not become public R11 dependencies.

| item | form / pair | obligation | planned minutes D / V |
|---|---|---|---|
| T1d/T1v | execution | discharge the loop-step wp under the original bounds | 5 / 5 |
| W1d/W1v | worked | relative certificates, explicit slice domain and a concrete derivation tree | part of worked30 |
| W2d/W2v | worked | evidence fields, native ghost/Tracked modes and the exact checker boundary | part of worked30 |
| W3d/W3v | worked | one matcher-loop VC and model unfolding, without the complete invariant | part of worked30 |
| H1d/H1v | execution | full compiled checker equals the frozen validity model, including rejection and all constructors | 18 / 15 |
| H2d/H2v | proof | general certificate soundness; V consumes a tracked evidence record under its stated validity premise | 17 / 15 |
| H3d/H3v | proof/construction | direct completeness by induction; construct a witness, V in a tracked evidence record with explicit representability | 20 / 15 |
| H4d/H4v | execution/proof | streaming prefix ledger plus final acceptance: derive every consumed-prefix result with a uniform residual invariant and termination | 15 / 10 |
| H5d/H5v | execution | complete certificate search by regex constructor, not an always-absent producer | 15 / 10 |
| H6d/H6v | execution/proof | search Cat splits with a missed-prefix invariant and bounded progress | 10 / 5 |
| H7d/H7v | execution/proof | search positive Star chunks; reject zero progress and prove termination | 5 / 5 |
| H8v | execution/proof | admitted Vec-arena append fallback, preserve index and old-node invariants | — / 20 |
| H9v | execution/proof | admitted Vec-arena edge-update fallback, preserve ownership/frame and valid targets | — / 25 |
| X1d/X1v | proof | fresh certificate consumed-character measure theorem, independent of hand soundness code | 6 / 6 |
| X2d/X2v | execution/proof | fresh loop building repeated-character certificates under fixed relative rules | 5 / 5 |
| A1d/A1v | metatheory audit | preserve original rules while auditing a plausible wrong rule/model and delivered proof | agent25 |

Core H1–H4 budget70D/55V=125; H5–H7 are the separately budgeted50-minute
certifying-matcher project (30D/20V); H8/H9 are the gated45-minute V arena
line. T10 and checkpoint22 are separate. Empty/default/max-auto/three-seed
controls precede every admitted minute. Checkpoint needs>=3/4 and>=1 per
language, with statement/body disjointness from the hand/agent files recorded.
The A2 whole-word matcher loop is already provided; it is a WP worked source,
not a new hole. H4 instead returns all nonempty-prefix outcomes and final
whole-word acceptance. Its original model and output ledger are new; opaque
residual-step helpers isolate quantifiers without changing that relation.
No complete search body is supplied next to a completeness hole: all producer
parts are learner tasks. Rejection completeness must remain explicit; a
certificate producer that returns no witness for a match is not a complete
certifying matcher. The small checker's positive acceptance guarantee remains
separate from producer completeness and from trust in the formal rules.

Predict5: P1d reads a relative split value (given-only check); P2v evaluates a
fixed ghost root-split bound/progress model (not full certificate validity); P3dv compares original-rule and changed-rule
native consumers; P4v selects failing labelled VCs; P5dv compares fixed-domain
checker/producer rejection promises. Two dv predictions, no Q-owned surprise.
Use guarded scenarios, sealed native sidecars, and real-extension contextual
D probes for supplied-layer imports. Never pin unresolved imports as a
semantic outcome. Declare WRITE constructs only after native feasibility;
V H2/H3 provide two actual tracked-evidence uses if those forms admit.

Keep540minutes: setup8, testout10, reading70, worked30, cards8, predicts15,
coreholes125, wp-lab35, certifier50, checkpoint22, agent25, paper40, bench20,
viva30, calibration7, arena45. Until the Vec fallback admits, its45 is0 and
a delta records the shortfall. Paper12.10 Lean4Lean uses its exact local
excerpt, separating an executable kernel, claimed independence and partial
metatheory. Add12bank questions/disjoint6draws, two paired PP,5predictions,
three diagrams, source-bound native captures and the tenth course-derived
bench prompt. No fabricated learner artifact or live model result is supplied.


R11 construction update (Δ267): actual canonical22/22 admission passes, including
the Vec fallback and independent checkpoint; the22 rows are now admitted with
planned minutes. This does not measure learner time. H3v uses a tracked mutable
output slot so empty variants typecheck; H2v moves its evidence. D H2/X1 require
the disclosed induction-disabled lever. P2 is a root-split/progress ghost value
check after full Seq computation hit a native computation-depth limit; arbitrary
full validity remains the checker/proof target. R11 is authoring, not shipped.

## 14. Band 3 item plan — R12 driving (2026-10-17)

Plan before activation, parent d9ae1b1. R11 focused CI and scripted STUDY checks
run on its untouched STUDY worktree; inherit their final metadata separately.
R12 was planned/admission0 at plan entry, pending native/Python feasibility and gates.
The user-directed D45 live-run deferral also covers Lab α's actual model arms,
not implementation, recorded apparatus checks or reference-free mock/replay tests.
Do not create grades, bypass pre-registration locks or call a model as CI.
Container-dependent re-judgement remains subject to frozen provenance rules;
record an unavailable apparatus rather than running agent code on the host.

Practice396minutes plus Lab α390=786 stays as designed. Native practice has
T1d/v5each and H1/H2d/v10each: remaining-budget arithmetic and two hint-site
loops over verifier outcome flags (count acceptance and locate first rejection).
Fixed executable bodies stay provided; learner annotations connect every prefix
and returned observation to the original flags. Native region gates remove only
the annotation regions, keeping executable computation well typed. Pinned
empty/default/max-auto/three-seed results precede minutes. No named-return proof
or manually weakened gate workaround is used.

Python extractor80: H1py validates a complete ordered stream of wrapper JSON
results, retaining all native stages, holes and inconclusive/error outcomes;
H2py localizes diagnostics by actual symbol/location without treating diagnostic
text, missing fields or an empty result as a proof success. Compose frozen core
protocol/result interfaces, never implement a renamed Q verdict parser. H3py20
is the bounded verdict loop: policy proposes data, trusted executor performs
it, budgets count failures/refusals, and only full zero-hole gate evidence can
stop as solved. A1py25 is a per-symbol profiler whose isolated measurements are
explicitly not a full acceptance gate. Lab environment60 and parametric engine90
have fixed hint sites, original statements/code, no new lever attributes, an
explicit node budget and width/depth/priority regimes fixed before each run.

Lab α uses40language-stratified course-derived/public tasks, one engine, three
obligation-feedback regimes plus best-first/raw feedback, ten prefix budgets
and three repeated Qwen seeds per arm:480runs/4800calls,10GPUh ceiling. Claude
final subset10tasks (5/language),10calls each plus≤10sentinels; descriptive
repeated runs, not controllable seeds. These remain pre-registered plans, not
observed results. Existing frozen budget/provenance/grade locks remain intact.
Mock/Scripted/Replay acceptance tests cannot unlock or fabricate a live arm.

The reading compares four doors into the same pinned verifier. LSP is read from
an actual captured framed trace, never posed as a new client-writing exercise.
Predictions use native subjects and actual result fields; language-server hole
visibility, automatic induction, severity-count and resource/seed surprises are
stated facts under the owner rules. Include5–6committed predictions, two paired
PP,12bank questions/disjoint6draws, exact local06.10and01.12cards, pre-registration
and methods rubric, apparatus fallback, source-bound captures and three/four
diagrams. Freeze practice, source-interface and live-outcome claims separately.


R12 §14 construction checkpoint (2026-10-17): actual source is authoring,
not shipped. Canonical11/11admission now precedes the eleven minute rows. The
central Python reference passes143cases with original provided-frame and plan
source-digest controls; native references pass three seeds and six audits.
Compiled clients pass66finite cases per language. Four form-admission controls,
actual native SHA-bound replay, the own24-frame LSP reading fixture, two exact
local cards, methods rubric, calibration fixtures,12-question/disjoint6bank and
two paired PP subjects are built. The chapter has5prediction boxes,3diagrams
and14native/source captures. API facades preserve the frozen single-file overlay.
The plan builder embeds task digests and actual prompt bytes, fixes all four
regimes and refuses incomplete/stale40-task admission. Qwen and the stratified
Claude subset require separate executable plans and separately bound/re-graded
registration under the frozen global task/repeat schema. Full task corpus,
final pins/STUDY workflow and focused CI remain source-construction work.
Live D45 work stays deferred, not passed; Docker daemon availability alone is
not validation of pinned containers or providers. No task gate or budget waiver.


R12 corpus/source follow-up: all40course-authored native forms (20per language)
pass the seven admission requirements. They span20language-paired algorithm
clusters; do not manufacture40independent programs or120independent repeats.
Initial full reference/baseline80controls,120seed checks,460empty-automation
variants,40wrong-hint checks and40audits pass. All40also pass the installed
R12-context frame/baseline/audit tool. The actual complete renderer reproduces
every native-verified completion. Corpus replay320controls plus a reference-byte
drift rejection join author CI; they use retained real Results and scripted
transports, not live models. The public slice reserves5DafnyBench/5HumanEval-Verus
members, excludes prior draws and cross-language HumanEval identities, and stays
unrun/not yet transformed into R12hint forms. Budgets and learner minutes stand.
The conservative frozen MDE(n20,baseline0.5,pairedTrue,alpha0.05/40)is infinity;
this is explicit exploratory/underpowered disclosure, not a quota/scope waiver.
Provided policy rejects an already-green original form, and proof-call admission
requires unique same-namespace ghost bindings without shadowing. Final source
CI/STUDY closure remains before declaring local completion. D45 live work stays
deferred; no registration, grade, run, reserve or provider event is fabricated.


## 15. Band 3 item plan — R13 pipelines (2026-10-17)

Plan before activation, source parent0eaf058. R12 remains an immutable STUDY
source while its six-job CI finishes; its26-command scripted workflow passes.
R13 is planned/admission0. Record D45 live forensic contractor/review sessions
as deferred and keep building native sources, own captures and scripted checks.
Do not execute build poisoning: cargo/build.rs/config and toolchain vectors
remain refusal-only coverage with the original wrapper tests as evidence.

The390-minute plan stays: native T1d/v5each and H1–H3d/v10each account for
test-out10 and holes60. T1 constructs an in-range clamped index; H1 repairs
an unchecked arithmetic delivery with an exact saturating sum; H2
implements a full-domain buffer-range predicate without adding a smaller
precondition; H3 repairs a vacuous test with a concrete nonempty two-character
regex witness for its original A1 language. Each repair includes attribution,
original-claim/frame review, native gate and audit. No native hole implements
the later solo trust-report. Only actual empty/default/max-auto/seed gates can
admit these rows; a failed item keeps0minutes until fixed or explicitly parked.

Stage attribution uses five own native prediction subjects with real Result
fields and raw --log evidence: parse/resolve/verify/compile distinctions,
selected versus full-target scope, and a successful proof with a failed runtime
expectation. R13 does not teach another JSON parser or LSP client. Actual source
bytes and pin/tool options accompany evidence; a simulated receipt is never
called a native run. Three diagrams explain stage barriers, the TCB and evidence
composition. Banks have12questions/disjoint6draws and two paired PP subjects.

R13 forensics uses only fvh.corpus.load_half(lang,"R"). The existing manifests
already partition the halves. Keep label data out of delivery-facing tools.
Select at least4constructs per language plus healthy controls; collect at least
two instruments on every selected delivery, even when an instrument is clean.
AllR-half constructs/covered rows remain indexed for R16, with the per-language
14-family scope and X09/X14/X18 gaps stated. UNKNOWN is required on grader-only
classes; never infer an accusation from a missing observation or corpus label.
The frozen corpus runner remains the only corpus executor. Published fixtures
and the author replay retain their distinction from learner diagnoses.

Paper12.3 uses its exact local card excerpt and provenance. Add stage-evidence
and no-kernel trust analyses, blank learner forensic/trust ledgers, production
review rubric and gold/flawed calibration fixtures. No live grade or transcript
is invented. Given A1–A4 imports remain tier-correct and original statements
are frozen; public examples must not disclose any hole/slot answer.

R12 final CI packaging correction: the159central acceptance cases include all
15provided-model boundary controls. Remove the three unnecessary API facades
and import their types directly from engine.py. Listing hole-free facades as
learner harness exercises made author CI correctly reject an empty TRIV list.
Keep the adapter and CI strict; every listed learner harness file now has real
H items. Frozen single-file overlay and original five learner bodies stand.


R13§15construction: canonical8/8admission now precedes all eight minute rows.
Four reference sweeps/audits,26compiled cases each language,52R-corpus rows and
32pins pass. P6dvadds the second paired prediction;6boxes/3diagrams/14captures
and4503words are built. Source-only inventory4controls and fresh bank8native
controls pass. Coarse native linker attribution is explicitly recorded/skipped;
R13supplies no solo trust-report or live actor result. Final CI/STUDY remain.


## 16. Band 3 item plan — R14 SMT mechanics (2026-10-17)

Plan before activation, parent6fba3a5. R13source stays immutable for its six-job
CI and scripted STUDY workflow. R12repaired source b574cfa has20scripted STUDY
commands/seven receipts passing; its static/harness/rubric replay is running.
R14remains planned/admission0. No live provider, grading, contractor or GPU
result is needed to construct the source/native/toolsmith kit; D45 stays deferred.

Keep390minutes and45/55D/V allocation. The70hand minutes provisionally split
H1d/v10each (quantifier/trigger bridge), H2d/v10each (recursive unfolding/fuel),
H3d/v15each (combined quantified, nonlinear or bit-vector obligation). These
are candidate targets, not admitted rows: private native feasibility, actual
empty/default/max-auto controls, three-seed references and clean audits precede
activation/minutes. Preserve original models, all-input domains and provided
code; a proof-only or type-error failure is not silently upgraded to the intended
control. Record and replace an unsuitable candidate before allocating minutes.

Use own R14variants of split/concatenation and recursive trace definitions.
Never ask for A1's already printed existential triggers, or repeat an earlier
module's hole answer as a given worked fact. Fuel must be the stated mechanism
on an honestly recursive definition, not artificial opacity around a trivial
proposition. Expose the original false/unknown/rlimit outcomes accurately,
separate stability across three seeds from absence of solver defects, and
keep resource-limit/seed surprises as known owner facts rather than new R-only
predictions. Matching-loop diagrams identify the instantiation cycle, not just
a chain of syntactically growing terms.

The12assertion battery is6D/6V on R14-owned subjects spanning quantified
splits/matching loops, recursive fuel, nonlinear and bit-vector obligations,
and isolation. Freeze every original assertion and executable frame. A bounded
automation may propose hints only at committed sites; verify the resulting
actual full targets and audit all12. No deleting assertions, changing preconditions,
raising resource pins, importing a reference, or accepting a proposed score.
The toolsmith target is tools/R14/trigscan.py, with stdlib parsing/analysis of
actual pinned SMT/log artifacts and explicit source/symbol scope. It must keep
missing/unrecognized evidence unavailable and preserve raw byte provenance.
Its source-analysis result is advisory; actual wrapper gates establish closure.
Provide reference-free frozen inputs/acceptance tests and a fixed actor frame.

Write5–6native/source predictions including at least2paired language items,
12bank questions/disjoint6draws,2paired PP, actual source captures and3–5diagrams.
Paper02.5 Schwarz uses the exact local excerpt and hash; CV sweep analysis
retains per-symbol values, unavailable runs, denominator/settings and whether
variance is descriptive. No invented benchmark performance or live actor result.
R14imports only its given A1–A4chain and its own modules. Native lane cap16GiB,
GATE_WORKERS1/DVL_VERUS_JOBS3, total≤48GiB with the two active CI lanes. Wait for
R13's workflow to release its third lane before native feasibility.
R12§14closure (Δ272): source b574cfa is locally complete, authoring/not shipped.
159central Python cases,20scripted STUDY commands/7receipts and six focused CI
bars pass across the original unchanged-native/paper run and repaired static/
harness/rubric replay. Original failures remain recorded. Final chapter5671
words/5boxes/3diagrams/14captures,30pins and29module/2252public-file leak scan
pass. The507referenced native raw roots are archived with0missing. D45live
work stays deferred, the unused public slice unrun, and R03/R11skips unchanged.


R13§15closure (Δ273): checked6fba3a5passes a single six-job CI6/6in1513s and
16scripted STUDY commands/8receipts, with original agent snapshots. All8native
admissions, four3seed sweeps/audits,52R-corpus rows,26compiled cases/language
and32pins pass. Chapter4503words/6boxes/3diagrams/14captures,30module/2378file
leak scan and archived32construction-native roots/0missing construction roots. Authoring candidate,
not shipment/live actor outcome; D45/R03/R11and coarse-link-stage skips stand.
