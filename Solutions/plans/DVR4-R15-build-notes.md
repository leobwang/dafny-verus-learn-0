# DVR4 step 7 — R15 build notes (author-only, lane P1b)

Binding inputs:
- `Solutions/plans/DVR4-repair-plan.md` §2.1 (four admission results), §2.2 (line budget), §2.7 (R15's designs), §3 (the Lab α pattern, for Lab β's pre-registration), §4.2 (the R module bar), §5 step 7.
- PLAN §3 R15 (Why, Core payload, Exercises; 744 min = practice 384 + Lab β 360; D/V/py 45/45/10), §4.1 rung 9 (red-teamed contractor → R-v1), §4.3 (Lab β; validity rules: hidden truth out of every loop, `roundtrip` on the pinned Qwen, CI never calls a model).
- DESIGN §10.3 / W10 / W18 (Q15's oracles and card audit waived to Lab β: mutation kill is shared, oracle agreement stays new).
- Course rules: D64/D84, D82/D85, D90, D92–D95 (re-pose rather than exempt; the learner writes the construct), twins mirrored.

Scratch and evidence: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step7/p1b/r15/`. Solver rules as R16's notes §0.

## 0. Hand-off state (keep current)

| step | state | evidence / commit |
|---|---|---|
| objective map (§1) | written | this file |
| H1 references and measurements (§2) | not started | — |
| H2v property rung | **DECISION R15-1** (mechanism) | §4 |
| Python holes (`spectest`, `roundtrip`) design (§3) | drafted | this file |
| twins, learner files, agent pair, admission | not started | — |
| chapter, bank, paper, pins, CI | not started | — |
| Lab β pre-registration design (§5) | drafted | this file |

## 1. Objective-to-exercise map (written before any build, 2026-10-27)

| objective (PLAN §3 R15) | chapter section (to write) | items | minutes | to confirm by probe |
|---|---|---|---|---|
| the escalation ladder: run → executable checks → property testing → proof → audit | §1 the ladder; diagram 1 | W1dv (A2's anchored `DerivMatch` read as rung 4), the compiled `#[test]`/`expect` checks (rung 2), H2v (rung 3), T1/H1 (rung 4), `vaudit` (rung 5) | ladder 70 | — |
| test-out (rung 4, small) | §0 | **T1d/T1v** `PrefixMatchR15(r, s)`: `b == exists j \| 0 <= j <= \|s\| :: Matches(r, s[..j])`, one loop restarting nothing (one derivative per character) | 5 / 5 | D64; TRIV `false`/`true` fail; the loop invariant clauses each needed |
| unanchored search, the R-owned anchoring theme (R04) on `rexc`'s matcher | §2 | **H1d/H1v** `ContainsMatchR15(r, s)`: `b == exists i, j \| 0 <= i <= j <= \|s\| :: Matches(r, s[i..j])`, nested loops restarting the derivative at each `i` | 20 / 20 | D64 on the reference and on the "call `DerivMatch` per slice" answer (§2); TRIV fails |
| property testing against an independent oracle (the `regex` crate, whole-string vs unanchored) | §3 | **H2v**: the oracle wrapper and the anchoring translation (`^(?:…)$` vs bare) in a deterministic generator test outside `verus!` | 15 | **DECISION R15-1**: the dev-dependency and the hole count (§4) |
| statement review as the irreducible human job | §4 | six frozen candidate statements for `ContainsMatchR15` (faithful, weak, vacuous, over-strong, anchoring error, empty-string error), each classified with a witness; written, rubric-graded (paper problem 2) | 30 | each candidate's verdict captured (the faithful one verifies with the reference body; each defective one has a witness pinned) |
| grade-the-grader; grader injection | §5 | fresh `/grade-paper` on `tests/instructor/fixtures/R15_flawed_answers.tex`; an injected string in a delivered artifact (paper problem 3) | 20 + 15 | fixtures; the rubric pins |
| contamination control (post-cutoff authorship, novelty review, perturbation probes, in-context isolation) | §6 | written (Lab β's card audit uses it) | 15 | — |
| red-teamed contractor → R-v1 (rung 9) | §7 | agent pair `R15_AgentRedTeam.dfy` / `agent.rs`: `rexc`'s leftmost-shortest end `FirstMatchEndR15` under a hostile brief (the brief invites weakening the spec, editing a check, or adding an assumption); acceptance `vcheck --gate`, `vaudit`, `specfreeze --check R15`; the learner writes R-v1 from the transcript | 30 | the plant fails at a real postcondition; a weakened delivery fails specfreeze |
| Lab β's oracles | §8 | **H1py** `spectest` soundness (35), **H2py** `spectest` completeness (40), **H3py** `roundtrip` (65) in `harness/r/fvh_r/{spectest,roundtrip}.py`; frozen tests `harness/tests/r/r15_cases/` on Mock/Scripted/Replay and a stand-in runner | Lab β 140 | the tests fail on the shipped holes and on TRIV bodies; pass on the references |
| Lab β pre-registration | §8, paper problem 4 | the learner's prereg (§5 design) | 35 | `prereg` refuses an incomplete plan |

**Minutes reconcile:** practice 384 = setup 8, test-out 10, read 70, worked 25, cards 6, predicts 15, ladder 70 (T1 not here; H1d 20 + H1v 20 + H2v 15 + run/checks/audit walk-through 15), statement review 30, grade-the-grader 20, injection 15, contamination 15, red-team + R-v1 30, paper 30, viva 30, calib 10. Admissible rows: T1d 5, T1v 5, H1d 20, H1v 20, H2v 15, H1py 35, H2py 40, H3py 65 (= 205).

**Predictions (≥ 2 `dv`, R-owned, to draft):** P1dv the empty slice (does `ContainsMatchR15(Star(Chr('a')), "")` return true; verdict of a body that starts `i` at 1); P2dv anchored vs unanchored oracle values on `b` for `a*` (value); P3dv a vacuous candidate statement (`ensures b ==> …` with `b := false`) — does it verify (verdict); P4d/P4v the roundtrip implication check between two specs that differ only on the empty input (obligation: which direction fails).

**Constructs (to confirm, D82/D85):** WRITE `invariant` (T1 and H1 are loops whose smallest answers write invariant clauses, in both languages); RECOGNISE `property-test` (one item, H2v; Q's WRITE slug, not R's here). No other WRITE tag.

## 2. H1 — what the smallest answer is (to measure)

- **Reference (the design):** outer loop over `i` with `forall i' < i, j' :: !Matches(r, s[i'..j'])`; inner loop keeps `d` with `forall w :: Matches(d, w) <==> Matches(r, s[i..j] + w)` and `forall j' in [i, j) :: !Matches(r, s[i..j'])`; each step `DerivCorrect` and `NullableCorrect` with the slice fact `s[i..j+1] == s[i..j] + [s[j]]`.
- **The cheaper answer:** call A2's `DerivMatch(r, s[i..j])` for every slice (cubic). It meets the spec; its smallest form (two loops, two quantified invariants, the calls) must still be ≥ 3 one-fact lines (expected 4–6). Measured both; if the cheaper one is the smallest and meets D64, it is recorded as acceptable (the chapter discusses the cost; the property rung and the bank's PP use the derivative-restart form). No re-pose unless D64 fails.

## 3. `spectest` and `roundtrip` (Lab β's oracles; Python holes)

Names disjoint from Q15's `mutants`/`kill_rate`/`vacuity`/`implication`/`classify` (avoid.sh). Every generated file is verified through `fvh.tools.run` (the frozen core), never a subprocess; the acceptance tests use a stand-in runner and Scripted/Replay policies only.

- **H1py `spec_sound_r15(card, spec, pairs, run) -> SoundReport`:** for each reference pair (input, output), render a check (Dafny: a method that asserts the spec's postcondition at the concrete values; Verus: a proof fn with `assert(...) by (compute)`-free unfolding through the spec fn), run it; a pair is `holds`/`rejects`/`unknown` (a killed or inconclusive run is unknown, never holds); the spec is sound iff every pair holds.
- **H2py `spec_complete_r15(card, spec, pairs, mutate, run) -> CompleteReport`:** for each pair and each output mutant (the card's mutation operators: off-by-one, swapped, emptied, a constant; equal-to-reference mutants dropped), render `!post(input, mutant)`; killed / survived / unknown; the kill rate over decided mutants and the survivors listed. Survivors are not verdicts (an equivalent mutant is decided only by the hidden reference, after the batch, in the grader container).
- **H3py `roundtrip_r15(card, spec, policy, run) -> RoundtripReport`:** two policy calls (spec → NL with the code redacted; NL → spec with the original redacted), then two implication checks (`spec ⟹ spec'` and back) rendered as lemmas over the card's signature; verdict `equivalent`/`weaker`/`stronger`/`incomparable`/`unknown`, with token and call accounting for the prereg's cost fields.
- Frozen tests (author, `harness/tests/r/r15_cases/`): synthetic cards in both languages; a stand-in runner that answers from a table; TRIV bodies (`return SoundReport(all holds)`, kill rate 1.0, always `equivalent`) fail; the unknown rule; redaction (the NL prompt never contains the spec text; the second prompt never contains the original spec).

## 4. H2v — the property rung (DECISION R15-1)

Findings (2026-10-27): `vcheck --test` compiles Verus tests with `verus --compile --test` (not cargo), so a crate dependency outside `vstd` and the layers needs a wrapper change; `regex` 1.13.1, `regex-automata` 0.4.18 and `regex-syntax` 0.8.11 are in the local cargo cache (offline build possible). Plain Rust outside `verus!` is allowed only under `#[cfg(test)]`/`#[test]` (lint V9/Δ42), and no Verus hole form counts a `todo!()` there, so a plain-Rust hole is not tool-counted today.

Options:
- **(a, recommended)** Two small tool changes, each with tests and a Δ entry: `vcheck --test` builds a module crate's declared `[dev-dependencies]` (only `regex`, offline, pinned in the lock) and passes them as `--extern`; the hole counter counts `todo!("<item id>")` inside a `#[cfg(test)]` item as a hole of a new kind `test-todo` (so the learner loop and `firsttry --strict` see H2v). The learner writes the translation `re_to_pattern_r15` and the wrapper `oracle_r15(r, s, anchored)`; the given generator and `#[test]` compare `contains_match_r15` and A2's `deriv_match` against it on 500 seeded cases.
- (b) The oracle is a second verified matcher (`deriv_match` over every slice, given), not the `regex` crate; H2v becomes the generator's shrinking/minimization of a counterexample in a `#[test]` (no external crate; still needs the `test-todo` count). Loses the record's "independent oracle".
- (c) Drop H2v as a hole: the property rung is a given, run-and-read demonstration (the chapter captures a planted divergence), and its 15 minutes move to the ladder's walk-through. Loses a hand item.

## 5. Lab β pre-registration design (following plan §3; design only, nothing run)

- **Question (PLAN §4.3).** Do two independent oracles agree, with each other and with hidden verdicts, and how often is "verified" also "faithful", D vs V?
- **Units.** 24 R cards × 4 specification variants (faithful, weak, over-strong, vacuous-on-a-case) × 2 languages = 192 spec units; cluster = card (24 clusters). Deliveries: Qwen 24 cards × 4 rounds × 8 repeats (PLAN §4.3: 768 calls), Claude 20 × 4 (80).
- **Primary estimand (one).** Cohen's κ between the two oracles' binary "faithful" verdicts (`spectest`: sound ∧ every decided mutant killed; `roundtrip`: equivalent) over the 192 units, with a cluster-bootstrap 95 % interval (10,000 resamples of cards). No test: the claim is "agreement = κ̂ [CI] on these cards with this model".
- **Secondary, descriptive:** each oracle's confusion matrix against the hidden verdicts (`Hidden/labs/R15/`, compared after the batch in the grader container), sensitivity/specificity with Wilson intervals; the verified-but-unfaithful rate of deliveries, D vs V, paired by card (difference with a cluster-bootstrap interval, no test); roundtrip's unknown rate; cost per arm.
- **Precision instead of power:** simulate κ's interval half-width at 24 clusters for κ ∈ {0.2, 0.4, 0.6} and within-card correlation ρ ∈ {0, 0.3} (the plan §3.4 code pattern, standard library, seed fixed); pre-register the half-width and say plainly that 24 clusters cannot separate κ = 0.4 from 0.6.
- **Missing results, stopping, accounting:** as plan §3.3 (apparatus failure re-run once with the same seed, then excluded and counted; policy failure is a failed delivery; identical generation settings per arm; feedback cap equal; the prereg sha before any run).
- **Contamination (W18):** post-cutoff authorship for the 14 author cards, a perturbation probe per card (renaming), the card audit (30 min) before freeze.
- **What the author builds now:** the prereg fields in `paper/R15_problems.tex` and the rubric; `fvh.prereg`'s required fields for Lab β (estimand, primary, aggregation, missing rule, cluster rule, precision sim sha256) as a later harness step; the 24 cards and the hidden verdicts are a later corpus step (not in step 7's scope).

## 6. DECISIONS (to the coordinator)

- **R15-1:** the property rung's mechanism (§4); recommend (a).
