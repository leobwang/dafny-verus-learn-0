# DVR4 step 3 — R08 rebuild build notes (author-only)

Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2.1–§2.3 (the step-matcher interface, D-R08 (a)), §4.2 (the R module bar), §5 step 3; PLAN §3 R08 (Why, Core payload, Exercises) and PLAN §10's 354-minute record. Scratch: `/tmp/dvl0-dvr4-s3/r08/`; probes and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-s3/r08/`.

## Objective-to-hole table (written before the code)

PLAN §3's objectives for R08 and the item that carries each. "Line budget" is plan §2.2's counter (proof lines of the reference body); a reference under 3 lines is redesigned.

| objective (PLAN §3 R08) | item | what the learner proves or reads | minutes D/V | line budget (reference) |
|---|---|---|---|---|
| the derivative matcher as a refinement of the step-matcher interface | W1d/W1v (worked) | the derivative engine: Config = Re, Step = Deriv, Final = Nullable; each law one call to A2/A1b; `Run` is the interface's, verified once | worked (30 min record line) | — |
| a second refinement over A2's class API, whose obligation is semantic | **H1d/H1v** `WordStepLaw` / `lemma_word_step_law` | the class-word engine's step law: case split alive / dead / exhausted, and the index shift `([c] + w)[i + 1] == w[i]` inside a `forall` | 10 / 10 | 6–12 |
| an engine's own lemma that a refinement obligation rests on | **H2d/H2v** `PartsLaw` / `lemma_parts_law` | structural induction; moving an index across `Parts(a) + Parts(b)` both ways (existential witnesses) | 15 / 15 | 15–30 |
| the interface obligation of the alternative-set engine (semantic: it composes `PartsLaw` and A2's `DerivCorrect`) | **H3d/H3v** `AltFeedLaw` / `lemma_alt_feed_law` | induction on the state's length; an existential split over `head + tail`; a local reveal of the opaque `Res` | 15 / 15 | 15–30 |
| opacity repairs | **H4d/H4v** `AltFinalLaw` / `lemma_alt_final_law` | reveal the opaque `Res` in exactly this lemma; induction on the state; `NullableCorrect` per element | 5 / 5 | 5–15 |
| what a refinement may change (weaken `requires`, strengthen `ensures`) and the obligations it generates | C4dv (divergence card), the refinement lab (30 min) | facts, not predictions | — | — |
| a refinement that fails for a semantic reason | A1d/A1v (agent, rung 5) | a pruning engine that drops `Eps` alternatives as if they were `Empty`: zero holes, a real postcondition failure in its pruning lemma; the faithful repair edits only the engine | agent 25 | — |

Item ids follow file order (difficulty ramp): plan §2.3's table lists the same four obligations as H1 `PartsLaw`, H2 alternative-set `StepLaw`, H3 class-word `StepLaw`, H4 `FinalLaw`. Here H1 is the class-word step law, H2 `PartsLaw`, H3 the alternative-set step law, H4 the final law. Content, minutes (45 per language) and objectives are the plan's; only the labels moved, so that the shortest obligation comes first and every hole follows the cards it uses.

## Design decisions found by probes (2026-10-18)

- **A refining lemma cannot recurse.** The interface's lemmas and functions inherit a decreases clause over the abstract `Config`, and Dafny refuses a decreases clause on a refining declaration (`decreases clause on refining method not supported`). Recursive `Step`/`Final` are therefore given helpers (`FeedAll`, `AnyNullable`), and each engine discharges the interface's laws by calling its own named lemmas (`FeedLaw(st, c, w) { AltFeedLaw(st, c, w); }`). The class-word engine does the same for uniformity. A bodyless refining lemma that restates the `ensures` is counted twice (once at the abstract declaration), so the holes are the engine's own lemmas, which live in the learner file.
- **The inline existential in an `ensures` was not matched**; the same statement through a named `AnyMatches` predicate verifies. The alternative-set engine therefore states its model through `AnyMatches(st, w)` (given, transparent) and an engine-level opaque `Res`.
- **Verus.** Associated types and proof fns in a trait work on the pinned Verus (the plan's [probe]). Exec state and spec model differ (a `Vec<Re>` cannot be built in spec mode), so the trait carries `type Model` and `spec fn model(st) -> Model`; the laws are stated over models. `start` and `step` take their argument by value (no class copies). `#[verifier::opaque]` on a trait-impl spec fn is accepted and revealed as `reveal(<AltEngine as StepMatcher>::res)`.
