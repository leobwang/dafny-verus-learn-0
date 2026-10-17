# Notes from the R-plan lane to the DVR0 spike lanes (2026-10-07)

> **Author-only.** Coordination between `PLAN.md` (the R-track plan) and the regex spikes. The plan's item ids and answers are in `Solutions/plans/R-author-notes.md`; this note lists only what the spike files should change or gate. Read against the spike files as of 06:30 today.

## 1. Names (the avoid list, `PLAN.md` §5.5)

`avoid.sh` compares normalized declaration names (camelCase and snake_case split into words, lower-cased) against Q's hole-bodied names, banks, written problems and chapter fences, and a curated list of the Lean course's exercise names (Lean R01–R06 declare `size`, `mirror`, `size_mirror`, `mirror_mirror`, `reverse`, `reverse_append`, `reverse_reverse`, `length_append`, `Tree`, `Expr`, `eval`; Q's exercise files declare `Size`, `size`, `Rev`, `RevRev`, `RevAppend`, `mid`, `MidBetween`, and the decimal parser's `is_digit`, `parse_digit`, `Digit`, `ParseTwo`). On a collision R renames.

| spike name now | hit | plan name |
|---|---|---|
| `NodeCount` | — | `NodeCount` (same; thanks) |
| `Mirror` | Lean `mirror` | `Backwards` (Verus `backwards`) |
| `MirrorMirror` | Lean `mirror_mirror` | `BackwardsInvolution` |
| `MirrorSound`, `MirrorCorrect` | (word `mirror`) | `BackwardsSound`, `BackwardsCorrect` |
| `Reverse` (on `seq<char>`) | Lean `reverse` | `BackwardsStr` |
| `ReverseAppend`, `ReverseReverse` | Lean `reverse_append`, `reverse_reverse` | `BackwardsStrAppend`, `BackwardsStrInvolution` |
| `ReverseLength` | (word `reverse`) | `BackwardsStrLength` |
| `NodeCountFacts` | — | the plan poses `NodeCountBackwards(r) ensures NodeCount(r) >= 1 && NodeCount(Backwards(r)) == NodeCount(r)` (R02.H2); keep `NodeCountFacts` if it states more, but gate the plan's statement |

## 2. Layer content

0. **Revision (after both spike reports and the plan review):** the lemmas R06 and later need are given in a new layer A1b declared by R06 (`NullableCorrect`, `CatEpsLeft`, `CatEpsRight`, `CatAssoc`, `StarOne`, `StarConcat`); A2 re-supplies only the class API and the `Deriv` family; A3's bounds become single digits (no digit-run parser); A5's `Step`/`Compile` are renamed `Advance`/`Emit`. The full list is `PLAN.md` §2.5 (DVR0's reconciliation step).
1. **A1 ships definitions only**: `Re`, `Matches`, `Nullable`, `NodeCount`, `Backwards`, `BackwardsStr`; Verus also `is_nullable` and `copy_re`. Every lemma region now in `RG_A1_Re.dfy` is a module hole (R02, R05) or the R06 decomposer's helper, so none of them may be given in A1 (the module-order law, `PLAN.md` §2.1 rule 3). A2 re-supplies `NullableCorrect`, `StarOne`, `StarConcat` with the class API and the derivative family.
2. **Dafny `Matches` should be a `ghost predicate`.** As a compiled `predicate`, R06.H2d's exec matcher can answer itself with `b := Matches(r, s)`. `Nullable` stays compiled (the matcher returns it).
3. **R06 needs `StarFree(r)`** (no `Star` node) as given code for its fallback (S1) and for R06.H5 (`DerivStarFree`) and the checkpoint item X1 (`StarFreeBackwards`); it is module-local in R06, not an A1 definition.

## 3. Items to gate beyond the spike's own regions

All with `--empty-body` in the shipped configuration and 3 seeds, both languages unless marked:

- R01 (no layer; on `CountChar` from the front): `CountCharSingle`, `CountFirstTwo`, `Midpoint` (over a `newtype U32` / `u32`), `CountCharAppend` (`{:induction false}`), `MeanOfTwo` (its `requires` is the learner's).
- R02: `NullableCorrect`, `NodeCountBackwards`, `NullableBackwards`, `CatEpsLeft`, `IsVoid` (exec, against a structural `VoidSpec`); Dafny levers `{:induction false}` on the first three.
- R03: `ClassMember`, `ClassRange` (total, no `requires`), `ClassUnion` over the given `ClassInsert`, `Union3` (client), `ClassOfString`.
- R04: `SomeWordMatches` (exists-witness), the three `RX_Witness` lemmas, `PrefixMatch` with its three checks, `MutantKilled`.
- R05: `CatAssocLR`, `CatAssocRL`, `StarOne`, `StarConcat` as an annotation hole (the three slice asserts blanked).
- R06: `AllNullable` (loop), `DerivCorrect` (S1; fallback `requires StarFree(r)`), `DerivMatch` (invariants and post-loop facts blanked, the body's proof call kept), `NaiveCatRefuted`, `CatStep` (`requires !Nullable(a)`), `DerivStarFree`, the decomposer's `BackwardsCorrect` (S1; fallback `CatAltDistrib`), and the checkpoint items `StarFreeBackwards`, `SumNodeCounts` (statements in the author notes §7.3).

Record each result where the plan's DVR1 lanes can find it (a results file beside your tools), with the band (proof lines) of each reference.

## 4. Status after the DVR0 follow-up lane (2026-10-07, afternoon)

Applied to the spike files (PLAN §2.5 steps 1–7); results in `dafny/summary.json` and `verus/summary.json`, raw runs under `~/.cache/dafny-verus-learn-0/author-probes/dvr0-{dafny,verus}/recon/` (INDEX.txt in each).

- **Layout.** Layer files: Dafny `RG_A1_Re` (definitions only, `ghost predicate Matches`), `RG_A1b_Facts`, `RG_A2_Deriv`, `RG_A3_Syntax` (definitions and the parser's specification predicates only), `RG_A4_Norm`, `RG_A5_VM`; Verus crates `rg_re_a1`, `rg_re_a1b`, `rg_re_a2` (with `char_class`), `rg_re_a3`, `rg_re_a4`, `rg_re_a5`. Module references beside them: Dafny `RX_R02`, `RX_R06_Decomp`, `RX_R09_Syntax`, `RX_Items`; Verus `rg_ref_r02`, `rg_ref_r06`, `rg_ref_r09` (plus `rg_rexc`, `rg_arena`, `rg_oracle` as before).
- **§1 renames** applied in both languages (`Backwards`, `BackwardsStr`, `BackwardsInvolution`, `BackwardsSound`, `BackwardsCorrect`, `BackwardsStr{Append,Involution,Length}`, `NodeCountBackwards`); A5 `Step`/`Compile` → `Advance`/`Emit` (`EmitProg`, `EmitSound`, `EmitComplete`, `EmitCorrect`; Verus `emit`, `emit_into`, `emit_prog`, `lemma_emit_len`). Further renames from this lane's names-only scan of Q's learner-visible files and from `scripts/avoid.sh --track R --extra-r Solutions/spikes/regex` (now clean: 0 hits, 1 waived): Dafny `Upto` → `CopiesUpTo` (Q02.X1d's `Upto`), `Rep` → `RepRange` and Verus `Rx::Rep` → `Rx::RepRange` (Q04 bank `Rep`), `Plain` → `NoSpecialFrom` (Q07 prediction scenario `Plain`), A5 `Thread` → `VmThread` (Q08 bank `Thread`), Verus `pow` → `copies` (Q's `Pow`), and in the oracle and rexc helpers `below` → `pick`, `classify` → `classify_pattern`, `Outcome` → `PatternOutcome`, `good` → `thread_ok`. Verus A2 follows the R06 hole names: `lemma_deriv` → `lemma_deriv_correct`, `matches_vec` → `deriv_match`. A5's `Advance` (the plan's choice) has the key of Q08's given trait method `advance` (`verus/q/q08_internals_ii/src/lib.rs`); it is not hole-bodied, so `avoid.sh` reports no hit.
- **A3**: single-character bounds; the decimal digit-run parsers are gone from every file; `ClassItems` and `Counted` (Verus `parse_counted`) carry completeness clauses. The expansion budget (orchestrator decision on R09) is not built here (R09 is DVR2's).
- **Verus**: `node_count`, `backwards`, `backwards_str`, A1b's six lemmas, the class API and the decomposer exist and are gated.
