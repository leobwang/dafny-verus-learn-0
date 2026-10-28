# DVR4 step 7 — R16 build notes (author-only, lane P1b)

Binding inputs:
- `Solutions/plans/DVR4-repair-plan.md` §2.1 (the four admission results), §2.2 (line budget), §2.8 (R16's designs), §3 (the Lab α pattern for Lab γ's pre-registration), §4.2 (the R module bar), §5 step 7.
- PLAN §2.2 (the A5 row), §2.4 (what A5 re-supplies), §2.5 step 7 (DVR0's reconciliation of the spike), §3 R16 (Why, Core payload, Exercises, 936 min), §4.1 (rung 14), §4.3 (Lab γ).
- The spike: `Solutions/spikes/regex/dafny/RG_A5_VM.dfy`, `verus/rg_re_a5`, `verus/rg_rexc` (the Pike runner and `rexc_match`), `verus/rg_oracle`; S3 closed (nullable `Star` bodies and backward jumps).
- Course rules: D64/D84 (≥ 3 one-fact lines, every proper subset fails, by the minimizer), D82/D85 (WRITE tags genuine, ≥ 2 per language), D90 named-call gate where it applies, D92 `writes = "module"`, D93–D95 (re-pose rather than exempt; the learner writes the construct), twins mirrored.
- Lab γ is a pre-registration design only: no model run on any lab, held-out or sealed task; CI never calls a model.

Scratch and evidence: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step7/p1b/{a5,r16}/`. Every solver job: one at a time, `free -g` ≥ 20G first (`memgate.sh`), a 6G scope (12G and `DVL_VERUS_JOBS=1` for CI), the pinned toolchain on PATH (`vcheck --versions`: every tool pinned).

## 0. Hand-off state (keep current)

| step | state | evidence / commit |
|---|---|---|
| A5 reconciliation design (§1) | **done (design)**; DECISION R16-1 open (emitter given) | probes `a5/a5_probe.{dfy,rs}` verified, 2026-10-27 |
| A5 layer files | **staged** in `Solutions/plans/drafts/R16/a5/` (`RG_A5_VM.dfy`, `rg_re_a5/src/lib.rs`: VM, one-step lemmas, `AcceptsInside`, `Emit`, `EmitProg`, `CodeAt`, layout lemmas, Verus exec emitter); install when R16 is armed and R16-1 is answered; `pike_run` and the R09 parser re-supply still to add; the verified probes (R16 references, threading) are in `Solutions/plans/drafts/R16/probes/` | e7ea83b9+ |
| R16 objective map (§2) | written | this file |
| jump-threading spike (§3) | **passed in both languages** (one-hop `Shortcut`, both directions, no `reveal`: `AcceptsInside` given) | `r16/thread_probe.dfy` 87 verified, `r16/thread_probe.rs` 31 verified |
| twins, learner files, admission | not started | — |
| chapter, bank, paper, pins, CI | not started | — |
| Lab γ pre-registration design (§5) | drafted | this file |
| D96 (PLAN rows) | **done**: PLAN §2.2's A5 row (Emit, EmitProg, exec emitter, layout lemmas, word-relative opaque Accepts + AcceptsInside + AcceptsFrom, parser and `pike_run` re-supplied; statements, proofs and the whole-program theorem the learner's) and A4's row R10–R16 | da21fbd9 (Δ318) |
| D97 (statements field) | **done**: `check_course_map.py` `LEARNER_STATEMENTS = {"R16": …}`: entries inside R16's trees, among its exercises, sha256 always `PENDING`, one `.dfy` + one `.rs` past planned, `expected/R16.statements` (fvh's pin file, the shipped forms) names the same files; 6 test cases; registry banner. Planned names: `dafny/R/R16_Capstone/std/R16_Statements.dfy`, `verus/r/r16_capstone/src/statements.rs` | Δ319 |
| next, in order | (1) install `dafny/given/R/RG_A5_VM.dfy` and `verus/given/rg_re_a5/` (Cargo.toml by hand, like `rg_re_a4`) from `drafts/R16/a5/`, add `pike_run` (re-proved over the opaque `accepts`) and R09's parser re-supply with an A5 header naming the R09 answers; (2) arm R16 (registry row with the two statement files + `expected/R16.statements`, units, imports), move `test_course_map`'s planned stand-in off R16 (`PLANNED = "R16"`, `PLANNED_D/V`, `PLANNED_ROW`: the stale-project-file and paper-pair cases need a module still planned; Q19–Q33 are the only ones left); (3) twins: T1 `EmitSizeR16`, statements S, H1 completeness, H2 soundness, H3 `Shortcut`, H4 `rexc_match`/`EmitCorrect`; agent + plant (§4); trust-report layout; admission; kit | — |

## 1. The A5 reconciliation (PLAN §2.2, §2.4, §2.5 step 7)

PLAN's A5 row gives the VM, an opaque fuelled `Accepts` with four one-step lemmas, the code-at-offset predicate and the layout lemmas of each constructor's code, and says "the emitter (`Emit`) and the capstone's correctness statements are the learner's". Plan §2.8 poses the statements over `Emit(r, pc)` and `AcceptsFrom(p, pc, w)` (fuel-free, word-relative). The spike is positional in Dafny (`Accepts(p, s, VmThread(pc, i), fuel)`) and word-relative in Verus (`accepts(p, pc, s, fuel)`, open). Reconciled as follows (probes verified on the pins, 2026-10-27):

1. **One VM in both languages, word-relative.** `Inst = IChar(c) | ISplit(x, y) | IJmp(x) | IMatch` (Verus `Char/Split/Jmp/Match` with `usize` targets, as the spike); `Accepts(p, pc, w, fuel)`: `fuel > 0`, `pc` in range, and per instruction (`IChar` consumes `w[0]`, `ISplit` either branch, `IJmp` the target, `IMatch` iff `w == []`), each step costing one unit. **Opaque in both languages** (Verus `#[verifier::opaque]`; the spike's Verus `accepts` was open). Four one-step lemmas, each an `<==>` (`AcceptsChar/Split/Jmp/Match`, Verus `lemma_accepts_char/split/jmp/match`), plus `AcceptsInside` (an accepting thread has fuel and an in-range pc; needed by the threading proof without a `reveal`). `AcceptsFrom(p, pc, w) = exists fuel :: Accepts(p, pc, w, fuel)` (`accepts_from`), so the frozen statements are fuel-free as plan §2.8 writes them. The Dafny port drops `VmThread`/`Final`/`Advance` (the word-relative VM needs no thread record). *Probe:* the Dafny VM with the R16 references verified (176 verified) after splitting per constructor and giving `EmitLenAlt`; the Verus spike with `accepts` opaque and the one-step lemmas called in place of unfolding verified first time (27 verified).
2. **The emitter is given in A5** (DECISION R16-1, recommended): `Emit`/`emit` + `clen` (Verus) + `EmitProg`/`prog`, the exec emitter `emit_into`/`emit_prog` (Verus), `CodeAt`/`code_at` (Verus opaque, as the spike), the layout lemmas (`LayoutOne/Alt/Cat/Star`, `EmitLenAlt`; Verus `lemma_emit_len`, `lemma_sub_one/alt/cat/star`, `lemma_code_at_add/one`). Reason: the layout lemmas PLAN gives are statements about `Emit`'s code, and the statements the learner writes and freezes name `Emit`; neither can exist before a learner-written emitter. PLAN §3 R16's Exercises line and its minutes have no emitter item. The learner still writes every correctness statement (§2, item S) and the whole-program theorem (inside `rexc`, item H4).
3. **Not in A5** (they are R16's answers): `EmitComplete`, `EmitSound`, the per-constructor cases, the fuel-indexed helpers, the whole-program theorem, the threading proofs. The spike's `@hole` regions stay in `Solutions/`.
4. **A5 re-supplies (PLAN §2.4, rule 3)**: R09's exec parser and lowering (Verus `parse`, the lowering to `Re`, with A3's specifications; Dafny: the parser's mirror only if the Dafny `rexc` mirror needs it) for `rexc`'s front end and error positions, and the spike's Pike runner `pike_run` (`ensures b == accepts_from(p@, 0, s@)`, re-proved over the opaque `accepts` with local reveals). A5's header names the R09 answers it holds ("do not open before R09's holes are done"), like A4's.
5. **Imports.** R16 reaches every layer (PLAN §2.3); A4's row "R10–R15" is corrected to R10–R16 (A5's Verus crate depends on `rg_re_a4`, as the spike's does).
6. **Names.** `VmThread`/`Thread` are not used (Q08 bank, PLAN-R-NOTES); the optimizer is `Shortcut` (Verus `shortcut`). avoid.sh runs on every new file before commit.

## 2. Objective-to-exercise map (written before any build, 2026-10-27)

PLAN §3 R16's objectives, the item that checks each, minutes (PLAN: capstone 666 + Lab γ 270 = 936; D/V 30/70), and what each probe must confirm.

| objective (PLAN §3 R16) | chapter section (to write) | items | minutes D / V | to confirm by probe |
|---|---|---|---|---|
| test-out | §0 | **T1d/T1v** `EmitSizeR16`: `|Emit(r, pc)| <= 2 * NodeCount(r)` (Verus `clen(r) <= 2 * node_count(r)`; tight at leaves, `Alt`, `Star`), induction | 5 / 5 | D64 (≥ 3: three recursive calls); empty body fails with manual induction; Verus E0/E1 fail |
| the generalization over the continuation, found on paper | §2 "On paper first" | blueprint (paper, graded ≥ 3 before formalization), P-items | blueprint 45 | — |
| frozen statements + statement-only review | §3 | **S** (statements, 40): the learner writes `EmitComplete` and `EmitSound` in both languages (plan §2.8 shapes); `/review` statement-only; then frozen (registry `statements` pin, `specfreeze --pin`, Lab γ's unpack gate) | 40 (written) | how a learner-written statement is pinned (the registry's `statements` field is Q19–Q33-only today: a check_course_map change, DECISION R16-2) |
| completeness by induction with the continuation | §4 | **H1d/H1v** completeness: `CompleteFuel` + per-constructor helpers (`Star` by recursion on the remaining word, non-empty first chunk), then the fuel-free wrapper | 45 / 45 | D64 (reference ≈ 40 lines); empty fails; Verus E0/E0H/E1 fail |
| soundness by induction on fuel; `Split` nondeterminism by cases | §5 | **H2d/H2v** soundness: `SoundFuel` (lexicographic `fuel, r`) + helpers, wrapper with `:|`/`choose` | 45 / 45 | as above |
| a verified optimizer (gated) | §6 | **H3d/H3v** `Shortcut` (one-hop jump threading, all jumps, cycles included): `ToShortcut`, `FromShortcut`, `ShortcutCorrect` | 35 / 35 once admitted | Dafny spike passed (§3); Verus spike; four results; 0 minutes until both |
| ship `rexc` | §7 | **H4v** `rexc_match` = `emit_prog` + `pike_run` + the whole-program theorem (the learner's, from H1/H2); `rexc` binary (`vcheck --bin`); error positions from A5's re-supplied parser; **H4d** the Dafny mirror's whole-program theorem `EmitCorrect` | 10 / 30 | D64 on H4d (reference 12 lines); TRIV on `rexc_match` (`None`, `Some(false)`) |
| reviewer → co-developer → adversary (rung 14) | §8 | agent pair `R16_AgentCapstone.dfy` / `agent.rs` (§4 below); co-developer 40, plant 30 | agent 70 | specfreeze `--check R16`; vaudit; the plant fails at a real postcondition |
| `rexc trust-report` (solo, rule 2s) | §9 | the Rust gate PASS/FAIL/UNKNOWN from R13's forensics, R15's ladder, the R half of the corpus; Lab γ's instrument | gate 90 (Lab γ) | layout (DVR3's, PLAN): a path holding `trust_report` under `verus/r/r16_capstone/`; never a contract path |
| `TRUST.md` final, contract R-v2, card + memo | §10 | written | 25 + 45 | — |

**Constructs (to confirm, D82/D85):** WRITE candidates `lexicographic-decreases` (H1, H2 need explicit tuple measures in both languages) and `lemma-recursion` (H1, H2, H3); RECOGNISE `opaque` (A5's `Accepts`, used only through the one-step lemmas). A tag no smallest answer writes goes to the coordinator.

**Line budget (plan §2.2).** Dafny references measured on the probe: completeness 5 lemmas ≈ 60 lines, soundness 5 lemmas ≈ 75 lines, threading ≈ 85 lines (two directions), whole-program 15 lines; Verus spike sizes are similar. All above the 15–30 band for 45-minute holes, which is the record's "hard band".

## 3. Jump-threading spike (the gate on H3; plan §2.8)

Statement (both directions, all states, fuel-free): `ShortcutCorrect(p, pc, w): AcceptsFrom(Shortcut(p), pc, w) <==> AcceptsFrom(p, pc, w)` where `Shortcut(p)[i] = Hop(p, p[i])`, `Hop(p, IJmp(a)) = IJmp(p[a].x)` when `a` is in range and `p[a]` is a jump, else the instruction unchanged (one hop; a self-loop `IJmp(a)` at `a` stays itself, so cycles need no special case).

- **Dafny (2026-10-27): verified**, 86 verified with the A5 probe. `ToShortcut` (original ⇒ shortcut, fuel never grows) and `FromShortcut` (shortcut ⇒ original, a hop costs two steps) by induction on fuel, four instruction cases each, using the one-step lemmas; it used `reveal Accepts()` only for "an accepting pc is in range", which `AcceptsInside` replaces.
- **Verus (2026-10-27): verified first try**, 31 verified: `hop`/`shortcut` (`Seq::new`), `lemma_to_shortcut`, `lemma_from_shortcut`, `lemma_shortcut_correct`, over the opaque `accepts` with the one-step lemmas and `lemma_accepts_inside`. The Dafny spike re-run with `AcceptsInside` in place of `reveal`: 87 verified.
- Admission after both: seeds 1–3, empty body fails (shipped and maximal automation), D64 (the two directions × four cases). The plan's fallback (one-hop on acyclic chains) is not needed: one-hop on every jump is sound and complete as stated.
- An exec `shortcut_exec` (`ensures out@ == shortcut(p@)`) is given (or a T-sized second part, decided at admission) so `rexc` can run the optimized program.

## 4. Agent pair, the plant (rung 14; to design in detail at build)

Three rounds on the capstone (PLAN §3 R16, §4.1): (1) **reviewer**: the agent reviews the learner's statements before freeze (statement-only); (2) **co-developer** (40): the agent proves the threading lemma or one per-constructor case under contract R-v1; (3) **adversary / plant** (30): the agent file ships a second optimizer (`ShortcutSplitR16`: also rewrites `ISplit` targets that land on a jump) with a planted defect (it does not range-check the hop target), which verifies against a one-directional statement and fails the frozen `<==>` at a real postcondition; the faithful repair edits only the optimizer; a delivery that weakens the statement fails `specfreeze --check R16`; the learner's trust-report must say FAIL on it.

## 5. Lab γ pre-registration design (following plan §3; design only)

- **Question (PLAN §4.3).** What fraction of naive-grader successes survive the learner's gate, by cheat class?
- **Unit and estimand.** Unit: a delivery (one run's final state). For each naive grader g (exit code, `cargo build`/`test`, a "verified" substring, one seed, `--allow-warnings`), the inflation `I_g = 1 − P(gate PASS | g PASS)`; primary: the pooled `I` over the union "any naive grader passes", estimated as the ratio of counts with deliveries clustered by task.
- **Primary analysis.** One estimate with a 95 % cluster-bootstrap interval (10,000 resamples of tasks), no test; per-class and per-grader inflation descriptive with Wilson intervals; the 4 impossible tasks reported separately (every naive success there is a cheat by construction).
- **Data (PLAN §4.3).** Every α/β success (re-graded, no new model call) plus 12 crate tasks (8 possible, 4 impossible; kinds in `R-author-notes.md` §11) × Claude 2 repeated runs + Qwen 3 repeats; budget as PLAN §4.3 (Claude ≤ 600 + 10 sentinels; Qwen ≤ 1,440 calls, 9 GPU-h).
- **Missing rule, stopping, contamination, cheat surface, `firsttry` intervals:** as plan §3.3, adapted (apparatus failure re-run once; a policy failure is a failed delivery). `fvh` refuses the crate unpack before the R16 statement sha is committed (PLAN §4.3).
- **Precision** (replaces the MDE): simulate the interval half-width for the expected naive-success count (≈ 40–80 deliveries over 12 + α/β tasks) at I ∈ {0.1, 0.3, 0.5}; pre-register the half-width, not a power.
- **What the author builds:** the prereg fields in `paper/R16_problems.tex` and the rubric; nothing runs.

## 6a. Decided (the user, 2026-10-28; Δ314)

- **D96 = R16-1 (a):** A5 gives `Emit`, exec `emit_prog`, the layout lemmas; the learner writes every statement, both proofs and the whole-program theorem; correct PLAN §2.2's A5 row. **Not started** (the staged files in `Solutions/plans/drafts/R16/a5/` are the starting point).
- **D97 = R16-2 (a):** the registry's `statements` field opens to R16, `PENDING` until the learner's post-review commit; fvh and specfreeze read it; Lab γ's unpack gated on it; a check_course_map change with tests. **Not started.**

## 6. DECISIONS (to the coordinator)

- **R16-1 (A5's emitter).** (a, recommended) `Emit` and the layout lemmas given in A5, the learner writes every statement, both proofs and the whole-program theorem; PLAN §2.2's A5 row is corrected. (b) The learner writes `Emit` in R16 and the layout lemmas move into R16's own given file (a frozen given-role file inside the module, F6-style), proved against the learner's emitter: layout lemmas cannot be proved before the emitter exists, so they would become learner holes too (+≈ 30 min, no record line for them). (c) Given emitter, but the learner writes the layout lemmas (four small holes, ≈ 15 min).
- **R16-2 (pinning the learner's statements).** (a, recommended) The registry's `statements` field opens to R16 with `PENDING` until the learner's commit after the statement-only review; `fvh` and `specfreeze --pin` read it (a check_course_map change with tests). (b) The statements live in a learner file pinned only by `specfreeze` (no registry field); Lab γ's unpack gate reads the specfreeze pin.

## 7. Hand-off sketch: how item S (the learner's statements) could ship (for R16-2)

- The learner file ships the four lemma declarations with their parameter lists and an empty contract, each body a hole, under a `// statement: S` marker; the learner writes `requires`/`ensures` (S, written, 40 min), runs `/review` statement-only, and commits.
- Under R16-2 (a), the author's registry row lists the statement file with `sha256 = "PENDING"`; the learner's post-review commit is pinned by `specfreeze --pin`'s learner mode (to build) and `fvh` reads it for Lab γ's crate unpack. Under (b), specfreeze's pin alone.
- Either way the twin carries the reference statements (§1's probe shapes), and the admission's four results run on the twin. H1/H2's empty-body gate is over the reference statements; a learner statement that is weaker than the reference is caught by the statement-only review and `specfreeze --against` the reference shape (an author-side check, never shown to the learner before the review).
