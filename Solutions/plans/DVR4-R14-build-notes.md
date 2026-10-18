# DVR4 R14 rebuild — build notes (author only)

Step 3 of `Solutions/plans/DVR4-repair-plan.md`, item §2.6, on `authoring`. The
parked commit 932dd47 (DVR3's R14: `PrefixCapR14`, `OddSquareR14`,
`ClearLowBitR14`, a battery over `PrefixMassR14`, the trigscan toolsmith) is the
input. Its hand items and battery are replaced; its toolsmith (`trigscan`, the
frozen tests and the native trigger capture) and its executor (`battery.py`) are
kept and extended. The user's D53 adds the `--smt-log` wrapper route.

## Objective-to-hole table (written before the code)

The plan's objective for R14: triggers, fuel and nonlinear facts on R14's own
`Matches` variant, a 12-assertion battery, the trigscan toolsmith, CV sweeps.

| objective | where the learner meets it | item(s) | why it is not trivial |
|---|---|---|---|
| a quantifier is used only through its trigger; a proof supplies the trigger term | §1, C1d/C1v (write:trigger), C4dv | **H1d/H1v** `CatIntroV` / `lemma_cat_intro_v` | the goal's existential is never instantiated without a `s[..|u|]` (Verus `s.subrange(0, u.len())`) term; facts without the term do not help (probe: empty body fails in both) |
| fuel unfolds a fixed depth; induction reaches every depth | §4, P5dv, C2d/C2v (recognise:fuel) | **H2d/H2v** `StarPowV` / `lemma_star_pow_v` | for unknown `n` no fuel suffices; the induction step needs the Star case's trigger term as well (Dafny ships `{:induction false}`) |
| nonlinear facts: Dafny's default Z3 arithmetic vs Verus `by (nonlinear_arith)` | §5, P2dv, C5dv (diverge) | **H3d/H3v** `DerivSizeV` / `lemma_deriv_size_v` | structural induction whose cases end in a product inequality; Verus also needs `node_count` unfolded three levels in the Cat case |
| bit-vector theory on code points | §5, P3d, P4v, C3d/C3v (recognise:bit-vector) | battery `bv-d`, `bv-v` | Dafny's int-to-bv32 conversion; Verus `by (bit_vector)` with its own requires |
| matching loops | §3, P1dv | battery `loop-d`, `loop-v` | the hypothesis feeds its own trigger; the goal needs the H1 lemma |
| isolation splits the resource budget | §7 | battery `iso-d`, `iso-v` | probe: eight cube identities are inconclusive in one query, verified one query each (3 seeds both ways) |
| what the solver was given (SMT log) vs what it proved | §2, §7, §9 | trigscan `--smt` (provided), the toolsmith A1py | patterns are evidence of input, not of instantiation |
| stability is measured | §6, B2 | CV sweep (no item: the written problem) | three seeds are the done rule, not an estimate of spread |

Minutes are unchanged from the registry: H1 10, H2 10, H3 15 per language (70).

## Divergences from the plan's §2.6 text (all reported)

- Verus trigger. The plan's Verus trigger, `#[trigger] matches_v(*a, s.subrange(0, i))`,
  names the fuel-indexed copy of `matches_v` inside its own definition; probes show no
  outside proof can match it (the chapter's `rectrig-v` pin: fails even with the
  equations and fuel 2). R14's Verus `matches_v` triggers on `s.subrange(0, i)`. The
  lesson is kept as card C4dv (diverge:trigger).
- H2's fuel card. The plan says the concrete `n = 3` instance closes with fuel 4 and
  fails at fuel 3. Probes: no fuel closes a concrete power on `MatchesV` (`star-v` with
  fuel 6 fails), because opening the Star case does not produce the split's trigger
  term. The fuel lesson moved to `NodeCount` (P5dv, C2d/C2v: three Stars fail by
  default, verify with fuel 4), where it is true.
- WRITE lists. The registry listed WRITE trigger, fuel, bit-vector; the coverage check
  needs two hand items per WRITE construct, and the three hand items use trigger (H1,
  H2), fuel (H3v only), nonlinear (H3). The rebuild lists WRITE trigger and RECOGNISE
  fuel, bit-vector, nonlinear-arith in both languages (DECISION NEEDED in the report).
- Battery loop cells. The plan's "one loops, one is repaired by a trigger choice" would
  need an option that changes a hypothesis, which the executor forbids; both loop
  cells close with the H1 lemma, and the chapter says so.
- Isolation cells are on polynomial identities (int parameters), not on `MatchesV`:
  no regex-shaped cell showed a real isolation effect at the pin (probes on
  `NodeCount` cubes ran out even per assertion).

## Probe findings (2026-10-18, course pins)

- Dafny: `CatIntroV` empty body fails; with `s[..|u|] == u` and `s[|u|..] == v` verifies.
- P1 (looping hypothesis, false goal): D inconclusive, V failed.
- P2 `(x + y) * (x + y) >= x * x + y * y`: D verified, V failed.
- P3d `0xDABC & 0xFFFFF800` = 55296; P4v `0xE7FF & 0xFFFF_F800` = 57344 (compute_only).
- P5 three Stars: D failed, V failed; `{:fuel NodeCount, 4}` / `reveal_with_fuel(node_count, 4)` verify.
- Dafny isolation: the first eight identities of the form `(a ± b + c ± d)(a + b ± c ± d)(± a + b + c ± d)`
  in one VC are inconclusive (gate and seeds 1-3, appended to the reference core and to a
  reordered core); each `assert {:isolate}` verifies (gate and seeds 1-3); plain assertions stay
  inconclusive. Pure cube permutations were not usable: in the core's context the combined
  query verified. Six-variable cubes failed even isolated (earlier isolated facts are assumed
  in later tasks). Verus: eight two-variable cube identities in one `by (nonlinear_arith)` are
  inconclusive; one query each verifies (seeds 1-3).
- The bank's seed example (K7, K8, K12) uses the next eight identities of the same family:
  seed 2 runs out, seeds 1 and 3 verify; ten seeds: 5 verified, 5 inconclusive.
- Verus split cell: the subrange equations alone fail; with `reveal_with_fuel(matches_v, 2)` verify.
- Dafny: plain body assertions of the same eight identities stay inconclusive.

## Admission (the four results)

| item | ref seeds 1-3 | empty body (shipped) | maximal automation | TRIV |
|---|---|---|---|---|
| H1d `CatIntroV` | verified ×3 | fails | fails | n/a (lemma) |
| H2d `StarPowV` | verified ×3 | fails | fails (shipped lever `{:induction false}` named in the row) | n/a |
| H3d `DerivSizeV` | verified ×3 | fails | out of resources (counted failing) | n/a |
| H1v `lemma_cat_intro_v` | verified ×3 | fails | fails (E0/E0H/E1) | n/a |
| H2v `lemma_star_pow_v` | verified ×3 | fails | fails | n/a |
| H3v `lemma_deriv_size_v` | verified ×3 | fails | fails | n/a |

Source: `scripts/vcheck --ref --brittleness` on both twins; `scripts/firsttry.sh R14 --empty-body` 6/6.

## Battery on the reference cores (`python3 tools/R14/battery.py`, 12/12)

| cell | baseline | tried → closing |
|---|---|---|
| split-d | failed | split-only failed → split-term |
| star-d | failed | unfold-one failed → lemma |
| loop-d | failed | lemma |
| nl-d | failed | lemma |
| bv-d | inconclusive | bv-bound |
| iso-d | inconclusive | asserts inconclusive → isolated |
| split-v | failed | split-term failed → split-term-fuel |
| star-v | failed | lemma (ordered first: the advisory scan reported terms) |
| loop-v | failed | lemma |
| nl-v | failed | nonlinear |
| bv-v | failed | bit-vector |
| iso-v | failed | one-query inconclusive → per-fact |
