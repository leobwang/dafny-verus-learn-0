# dafny-verus-learn-0 - design proposal v2 (two tracks, final)

*Design stage; nothing is authored yet. Target repo: `/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0`.*

*Ids (§, OD, TC, G/V/X) refer to `spec4dafny-verus.md`; "v1" is `DESIGN-PROPOSAL-v1.md`; "Lean R"/"Lean Q" are lean-learn-0's `PLAN.md`/`QPLAN.md`. [verify] = probe on the pins before shipping or quoting; [A] = assumption to calibrate; "probed" = checked on this host, 2026-10-03. Pins: Dafny 4.11.0 (no nightlies); Verus weekly `0.2026.09.27.3cf1832` with Rust 1.98.1, Z3 4.16.0, `vstd =0.0.0-2026-09-20-0158`. No Lean answer material was read; predict themes name questions, never answers.*

### Changes from v1

1. **Shape.** v1's single depth-ordered track (F00–F17) becomes two Lean-style, standalone tracks in one repo: **Q** (33 modules, by depth) and **R** (16, by topic). They share one registry, instructor layer, ledger and gradebook. The disjointness gate (§2.7) returns.
2. **Comparative from day one** in both tracks; the staggered lead/shadow plan is gone.
3. **Labs:** Q's sit inside its family-C practice modules (Q12, Q15, Q18); R adds three complementary, standalone labs (R12, R15, R16). Five domain challenge topics replace F13–F17; RL is optional.
4. **Kept from v1:** E1–E12, R1–R5, the research layer, cheat corpus, engines, sandbox, rules 1e/1f, pins, `fvh`, BigNat, the instructor table, and the security findings.

### Changes in this revision (after the adversarial review)

- **R is standalone and ungated**, with standalone labs (+8.7 h), and its artifact is now a regex engine, not Lean R's expression language (D7).
- **Safety.** The guard is a tripwire against accidental exposure, as the spec intends (§7.2 honesty clause); the separate authoring account and host changes are optional hardening (H1/H2, §4). The Claude login may enter containers only under D6's safeguards, and agent output is never merged (N2).
- **Minutes** are itemized; Q12/Q15/Q18 keep S9–S11 practice. Q core is 93.3 h; research-ready 58.0 h.
- **Wiring and spoilers.** One Verus crate per spine layer; given-only Dafny check units; author answers in `Solutions/bench/`; hidden lab truth in `Hidden/labs/`.
- **Disjointness.** Statistics are frozen course code, LSP-by-hand is Q-only, and waivers state pre-empted insights.
- **Quota.** ≈102 MU and a 25% reserve. A simulation shows the Q-core finish is insensitive to the Lean split (D1).

### Revision after review (2026-10-03, threat model)

The adversarial passes had escalated the guard from the spec's tripwire into sandbox-grade isolation against a deliberately escalating agent: a separate Unix authoring account (N1), removing the learner from `docker`/`lxd` (D5) and a sudoers change. That is not the course's threat model. The guard exists so that a tutor, grader or contractor does not *accidentally* see reference material; the learner owns the references and may open them at any time. N1 and the host changes are therefore **optional hardening (H1, H2)**, not requirements. What stays: the four guard layers, rules 1e/1f as tripwires, the Docker sandbox for agent experiments (it serves research validity, not anti-spoiler), and N2.

## 1. Summary

One repo, two complete standalone tracks teaching Dafny and Verus side by side. **Q** climbs by depth across 13 strands; each practice tier's family-C module adds a pre-registered lab (matched-compute proof completion; spec quality and vericoding; gates at crate scale with a BigNat capstone), and Q19–Q33 are solo domain challenges. **R** follows topic order, growing a regex engine into a verified compiler to a Pike-style VM (`rexc`), with three complementary labs. Both keep lean-learn-0's invariant design: verifier as grader under an asymmetric referee, four guard layers, the contractor ladder, solutions-first, no invented output, everything pinned.

| aspect | design |
|---|---|
| tracks | Q: Q01–Q18 core + Q19–Q33 challenges, studied and authored first. R: R01–R16, authored in parallel, ungated. Disjoint by gate |
| languages | Dafny + Verus from Q01/R01; Python (`fvh`) as the tool language from Q06/R05. Split ≈45/45/10 [A] |
| learner hours | Q core 93.3 h (incl. 1.5 h prework; lab blocks 21.2 h); research-ready 58.0 h; R 124.9 h (≈119 with Q-credit); challenges 675–1,165 h, a menu |
| milestones (mid case, D1/D2 defaults) [A] | Release A ≈ Jan 24 2027; research-ready ≈ Apr 26 2027; Q core ≈ Jun 1 2027; agentic topic ≈ Nov 2027; R core ≈ Mar 2028 |
| authoring | ≈102 MU (≈85–124): infra 15.5, Q core 28.5, Q challenges 26, R 32; ≈142 with Lean Q. Release A = 14.5 MU |
| model access | Claude subscription CLI: interactive `/contract` on the host; tool-less `claude -p` policy runs; Claude Code agent runs inside per-run containers with safeguards (D6). opencode + local Qwen in containers. CI never calls a model |
| research core | labs in Q12/Q15/Q18 and R12/R15/R16, then the agentic topic Q31–Q33. RL optional |

**Findings about this host (probed 2026-10-03), at tripwire scale:**
1. **Claude Code state** (session transcripts, file-edit backups, scratch clones, including the Lean authoring copies) lives under `~/.claude/` and `/tmp/claude-1000/` outside the guard's deny rules, so a broad search in a study session could stumble into reference material. Most of it expires by itself: `/tmp` is cleared at boot and after 30 days, and Claude Code deletes transcripts after 30 days by default.
2. **Author notes in the learner project's memory** are loaded into study sessions; keep author-only notes in the authoring session's own memory.
3. **`local-assistant`** runs opencode with file tools, and opencode ignores `.claude/settings.json`; it matters only if a study session delegates to it.
4. **Host privilege** (`docker`/`lxd` membership, `NOPASSWD` sudo) would only matter against an agent deliberately escalating, which is outside the course's threat model; it is general machine hygiene (H2), not a course requirement.

Items 1–3 are handled by tripwire rules (deny rules and hook rules 1e/1f) and by authoring discipline; lean-learn-0 gets the same small fix (D4).

## 2. Decisions made (2026-10-03)

1. **Two parallel standalone tracks exactly like Lean** (R by topic, Q by depth), sharing registry, instructor layer, ledger and gradebook, with a disjointness gate. *Overrides OD2.*
2. **Comparative from day one.** *Overrides OD1.*
3. **Trust-first balanced labs**; RL not core.
4. **7+ h/week.**
5. **All in parallel** with Lean R study and Lean Q authoring (≈40 MU); shared quota.
6. **Q first**; R follows in parallel.
7. **Q mirrors Lean at 33 modules**; challenges lazy.
8. **Domain challenge topics** (a)–(e); research prep lives in the core labs and (e).

**Carried constraints:** no usage-billed API; a 32-core, 123 GB, 96 GB-GPU host with Docker and two local Qwen models; a Rust-fluent learner with a 152-paper agentic-FV review (`cheatsheets.md`).

## 3. Decisions made, round 2 (2026-10-03)

Every v2 decision is now settled; the course has no open design decisions. Each answer records its consequence.

| id | decision | consequence |
|---|---|---|
| D1 | **Quota split 30/70, Lean Q heavier**, until Lean Q authoring is finished; then 100% here | §15.3 milestones as stated (mid case: Release A ≈ Jan 24 2027, research-ready ≈ Apr 26, Q core ≈ Jun 1 2027) [A] |
| D2 | **Agentic topic (Q31–Q33) first** after Q18, then the R core | research-capable ≈ Nov 2027, R core ≈ Mar 2028 (mid) [A]; waiver W13 avoided |
| D3 | **Waivers W1–W14 and X1 accepted; one shared file** per standards document | one `CLAUDE.md` contract block, one `research/EVAL.md`, one `research/TRUST.md`, each with `Q-vN`/`R-vN` sections; the stricter rule wins |
| D4 | **Harden lean-learn-0** (revised after review: tripwire scale) | clear stale authoring scratch (`/tmp/claude-1000/*lean-learn-0*`, or reboot); optionally add three deny rules (`Read(~/.claude/projects/*/*.jsonl)`, `Read(~/.claude/file-history/**)`, `Read(~/.claude/history.jsonl)`) and a hook pattern for other sessions' `/tmp/claude-*` folders, done in the normal Lean authoring worktree; keep author-only notes out of the learner project's memory. A separate authoring account is not required |
| D5 | **Host privilege** (revised after review: optional, H2) | not required by the course. You removed `leobwang` from `docker` and `lxd` on 2026-10-03; that is reversible (`sudo usermod -aG docker,lxd leobwang`). The sandbox runs Docker through whatever access you keep (group, `sudo`, or rootless); rootless Docker is an option, not a dependency |
| D6 | **Claude login MAY enter agent containers, with safeguards** (a recorded departure from Lean QPLAN risk 9) | §13.3 items 3–4 and §11.1 engine 3: read-only credentials in an isolated `CLAUDE_CONFIG_DIR`; Anthropic endpoints added to the egress allowlist [verify hosts]; secret scan of every returned file and log; token rotation after each batch [verify mechanism]. Token refresh on a read-only mount is a DV0 probe; if it fails, the fallback is harness-executed Claude runs (v2's D6 default) |
| D7 | **Regex engine** as R's running artifact (`rexc`) | §10.2 as written; DVR0 spikes for `Star` and the VM, with star-free / forward-jump fallbacks |
| D8 | **Full labs**, Claude arms kept | Q lab blocks 21.2 h, R labs 17 h, ≤≈1,700 Claude calls from the study reserve; trimming remains the fallback if DV0 measures low quota |

**Still to measure, not decide:** the account-weeks Lean QA0/QA2 actually consumed. DV0 replaces the assumed 1.5–2.5 MU per account-week with a measured figure, and only the dates in §15 move.

## 4. Assumed defaults (veto if you disagree)

**Threat model.** The guard is a tripwire against *accidental* exposure of reference material (spec §7.2: "a tripwire, not a sandbox"). It does not defend against an agent deliberately escalating its privileges, and the course does not require host changes for that.

**Optional hardening:**
- **H1. Separate authoring account** (optional). Authoring as a separate Unix user, with its own `~/.claude` and `TMPDIR`, keeps authoring transcripts and scratch clones physically out of study sessions' reach. It is meaningful only together with H2, and the course does not depend on it; without it, authoring discipline (clear scratch, keep author notes out of learner memory) plus the deny rules and rule 1e cover the accidental channels.
- **H2. No root-equivalent access for the learner account** (optional): no `docker`/`lxd` membership and password-only `sudo`. Probed 2026-10-03: `leobwang` has `(ALL) NOPASSWD: ALL`. Worth weighing as general hygiene for autonomous agents (a mistaken command can run as root without a prompt), independent of this course.

**Required:**
- **N2. Agent output is data** (research validity). Agent and harness-executed runs return files to `research/runs/`, judged in a network-less verification container and never merged; only interactive `/contract` edits (under the hooks) land in the tree, and `contract_local.sh` patches are applied only after you read them.

**Defaults:**
- **Ids:** R01–R16 and Q01–Q33 frozen before the first commit (Lean's rename cost a 155-file commit). Challenges: Q19–21 algorithms, Q22–24 quant, Q25–27 numerics, Q28–30 PL, Q31–33 agentic.
- **Artifacts:** Q spine BigNat (fallback: L4 multiplies by one limb). R regex engine; R16's VM is spike-gated (fallback: star-free regexes, forward jumps only).
- **Comparative mechanics:** C1–C8; ≤6 WRITE units / ≤10 slugs per module; per-language exit floors from the moderate tier; an optional RECOGNISE-only Lean column on Q01–Q03 cards, limited to Lean R01–R05 constructs; Python holes from Q06/R05.
- **Challenges:** any topic order after Q18; author (e), then (c). One lead language per module, except Q19, Q26, Q31–Q33 (+0.75 MU each).
- **Assessment:** Q exits, six tier vivas, 15 defenses, ≈8-question banks. R module vivas from 12-question banks (8 for R01), so disjoint re-viva draws exist (§6.8), plus R06/R11 checkpoints. Optional Q-credit test-out saves ≈6 h [A].
- **Wiring:** Q builds by default, R by name; one unit per (module, language, library tier); one Verus crate per spine layer; re-supply everywhere; registry schema 1; generated hook fixtures; CI as `dvci`, never on `leobwang-*`.
- **From v1:** all skills; one pin per language (≤2 bumps a year); a private remote; `Hidden/` encrypted; fork from Lean; ≤10 GPU-h per lab [A]; RL only as an unbudgeted extension [verify weights].
- **Spec ODs:** OD3–OD7, OD11 and OD12–OD18 as recommended (OD16 prefix `leobwang-`); OD8 puts the library at Q04/R07; OD9 is split (Q uses BigNat); `--target py` unless the IDE probe forces .NET [verify].

## 5. Goals and exit competencies

**Goals:** (1) hand fluency in both verifiers on the classes agents fail (DafnyPro's hint classes, AutoVerus residuals, invariants, weak specs), with programming first-class (`bignat`, `rexc`, `fvh`); (2) the verifier as an environment (pipeline, JSON, limits, verdict kinds, brittleness, TCB); (3) agentic verification as experimental science. **Every competency has a core home in both tracks**; challenges only deepen.

| # | you can… | Q home | R home |
|---|---|---|---|
| E1 | close unseen proof items by hand | exits Q03/Q06/Q09 (≥1/2 per language); Lab 1 hand part | pairs; R06/R11 checkpoints |
| E2 | triage a failure and say what each verdict licenses | predicts Q01–Q09 | R01, R05, R11, R14 |
| E3 | write a spec from prose with witness, mutant-kill ≥ threshold [A], and reference implication | Q13 → Q15 | R04 → R10 → R15 |
| E4 | diagnose ≥8 fake greens (4 D + 4 V) by ≥2 instruments each, no false accusations | Q09 → Q18 | R13 → R16 |
| E5 | ship a gate rejecting every decidable cheat (≥40 specimens), UNKNOWN on grader-only classes, FP rate measured | Q09 → Q18 (Python) | R13 → R16 (Rust) |
| E6 | build spec-quality oracles | Q15 | R15 |
| E7 | report through `EVAL.md` with full disclosure | Q06, Q09, labs | R05/R07 → R12/R15/R16 |
| E8 | measure stability; repair without weakening | Q09, Q15, Q18 | R14, R16 |
| E9 | port D → V with a fidelity audit | Q07 | R09 |
| E10 | run a pre-registered replication that reproduces from logs | Q12/Q15/Q18 | R12/R15/R16 |
| E11 | frame and defend research | Q18 proposal | R16 card + memo |
| E12 | compare search regimes at matched compute | Q12 | R12 |

**Coverage rule.** ≈70 payload-keyed rows [A], each needing a Q01–Q18 **and** an R01–R16 home in every listed language (challenge-only homes are errors; protocol invariants and data engines stay deepening-only). The full table ships at DV1, checker-enforced. Excerpt, with the two rows the review found missing:

| payload | langs | Q homes | R homes |
|---|---|---|---|
| toolchain-mismatch lab (§2.9) | d, v | Q04 S5 lab | R07 lab |
| escalation ladder with property testing (§11.1 row 14) | d, v | Q06 S12 (proptest outside `verus!`; bounded `expect` loops) | R02 first tests; R15 ladder |
| grade-the-grader | — | Q12 S12 | R15 |
| LSP | d | Q09 framing; Q15 client | R12 annotated trace |
| statistics (pass@k, CIs, paired tests, MDE) | py | Q06, Q09 | R05, R07 |
| contamination control | — | Q12, Q15 | R15 |
| permissions (`PointsTo`) | v | Q11, Q14, Q17 (gated) | R11 (gated) |

**Threshold concepts TC1–TC14** (§11.2.3): in Q, glimpsed Q01–Q03, operated Q02–Q06, mechanism Q07–Q09 (TC9, TC13, TC14 resolve in Q18); R homes TC1–2 R04/R05, TC3 R01/R13, TC4–5 R02/R06/R14, TC6–8 R10/R11/R13, TC9 R07/R13/R16, TC10–11 R04/R12/R14, TC12 R03/R09, TC13 R10/R15/R16, TC14 R14/R16.

| id | research concept | Q | R |
|---|---|---|---|
| R1 | verified ≠ correct; the spec is the attack surface | Q01 → Q06 → Q15 | R04 → R10 → R15 |
| R2 | a score without an exploit audit is an upper bound | Q03 → Q09 → Q12, Q18 | R12 → R15 → R16 |
| R3 | rules without gates are suggestions | Q03 → Q09 → Q18 | R01 → R15 → R16 |
| R4 | scaffolding must match model strength | Q04 → Q07 → Q12 | R07 → R12 → R16 |
| R5 | small-n results need pre-registration, variance and cost | Q03 → Q06 → Q12 | R05 → R07 → R12 |

## 6. Language strategy: comparative from day one

### 6.1 Why both, from the start

OD1's "mixing doubles the work" holds for content, not infrastructure: ≈3k of Lean's ≈9.5k infrastructure lines are language-specific, so shared parsers, per-language hook tables and one `--lang` CLI add only ≈1.5–2k lines. The research case: vericoding's union success is 82.2% in Dafny vs 44.3% in Verus, AlphaVerus bootstraps Verus from Dafny, and VeruSAGE and CryptoProver are in Verus; a one-verifier harness cannot study that gap. The cost, three syntaxes in flight, is softened by false-friends cards, per-language availability and exit floors, and the limited Lean column.

### 6.2 Mechanisms (both tracks)

- **C1. Paired holes.** Most holes pair one obligation in `.dfy` and `.rs` (`// pair: Q04.H3v`); differing constructs are the lesson. A first hole takes 4/6/8 min (intro/moderate/detailed), and its pair is budgeted at the same rate until calibration [A], since Verus overflow obligations can make the second harder. "Twin" keeps the spec's meaning: the hole-free reference file.
- **C2–C3. Rosetta and divergence cards:** verified D/V columns (1.5 min); `diverge:<slug>` specimen pairs with both behaviours pinned.
- **C4. Cross-language predicts:** `D:<v> V:<v>` with `v ∈ {ok, fail[labels], timeout, err:<stage>}`, hash-pinned; ≥2 per concept module.
- **C5. Slugs** `d:assert-by`/`v:assert-by`, each needing ≥2 checked uses in its language.
- **C6. Ports** with a fidelity audit (Q07, R09). **C7. A false-friends card** (`calc`, `assert`, `forall`, `old`, `decreases`, `==>`) in Q01/R01, refreshed in Q04. **C8. Python holes**, AST-counted.

### 6.3 Per-language rules

- **WRITE units:** a paired unit (≈5 min) has a success and a pinned failure per column; a single unit ≈2.5 min.
- **Availability:** a construct is usable in a language only after WRITE or RECOGNISE *in that language*.
- **Hand first:** `v:nonlinear-arith` after a Verus hand proof; `d:induction-auto` after a `{:induction false}` lemma; `v:broadcast-use` after explicit vstd calls; `Std` lemmas after one hand proof.
- **Banned (linted over H/X/T blocks):** Dafny `{:axiom}`, `assume`, `expect` outside `{:test}`, `include`; Verus `external_body` outside given code, `exec_allows_no_decreases_clause`, `cfg(verus_only)`; in both, early library imports and any `use` of a spine layer above the module's tier.

### 6.4 Taught once, twice, or in one language

- **Once, in two-column code:** Hoare/wp/VC, invariants as IH, termination, verdict asymmetry, TCB, vacuity, spec metrics, statistics, gate design.
- **Twice, as paired WRITE:** holes, `assert … by`, `calc`, `decreases`, quantifiers, `opaque`/`reveal`, triggers, fuel, audit, freeze.
- **Divergence cards:** loud vs silent holes, `int` vs overflow, frames vs ownership, auto-induction, fuel, V20, V9, G9, the legacy CLI, churn.
- **One language only:** Verus modes, `Ghost`/`Tracked`, views, `broadcast use`, `nonlinear_arith`/`bit_vector`; Dafny `{:induction false}`, refinement modules, subset types, `function by method`, frame clauses.

**Shares:** each language gets ≥40% of hole minutes per tier. A module may tilt to 35/65 (Q07, Q16) or 30/30/40 with Python (Q09). Overall ≈45/45/10 [A].

### 6.5 Pins and fidelity

- **Research pins.** One course pin per language. Labs prefer pools that validate on it (LemmaScript, MINIF2F-DAFNY, HumanEval-Verus, re-validated DafnyBench/vericoding subsets [verify]); exact-setup replications run only in a sandbox with a `VERSIONS.md` row; strata are chosen per model from a pilot; the gate takes a per-benchmark trust allowlist [verify].
- **Cross-language fidelity.** No verifier sees both specs, so implication lemmas alone are circular. The instrument: (a) differential execution (Dafny `--target py` vs Verus `--compile`) plus mutant-kill parity; (b) an independently transcribed, statement-reviewed mirror with implication lemmas, labelled "relative to the mirror". Taught in Q07 and R09, deepened in Q19, framed as an open problem.

## 7. The Q track (depth-ordered, studied first)

### 7.1 Prework and tiers

**Prework (zero MU, from today):**
- **P0 (90 min, counted in Q01's block):** install both toolchains from the §14.5 pins; DV1's `vcheck --selftest` confirms the install at Release A.
- **P1 (optional, ≈15–20 h, not counted):** read the full papers behind the lab cards (05.10, 06.1, 04.8, 04.6, 04.7, 03.8, 07.2, 02.6, 02.4).

Official tutorials are excluded: they would spend Q01–Q03's first-try predicts.

| tier | modules | depth | exit check |
|---|---|---|---|
| 0 Survey | Q01 (S1–S13; L1) | recognise all; 3 paired constructs | hole-free in both languages; map ≥10/13 |
| 1 Intro | Q02 (S1–S6), Q03 (S7–S13; L2) | introductory syntax | 3 D + 3 V closed-book, ≥5/6; Q03 viva |
| 2 Moderate | Q04 A, Q05 B, Q06 C (L3) | first knobs; library; property tests | 2 D + 2 V unseen, ≥3/4 **and ≥1/2 per language**; Q06 viva |
| 3 Detailed | Q07–Q09 (L4) | full mechanism | as moderate + explain-back; Q09 viva |
| 4 Intro practice | Q10–Q12 + Lab 1 (L5) | statements given; D ≤10 / V ≤15 lines | verifier part + ≥1 of 2 timed; lab acceptance; viva |
| 5 Intermediate | Q13–Q15 + Lab 2 (L6) | no skeleton; ≤1 invented lemma; ≈1/5 from prose | verifier part + 1 timed; viva |
| 6 Hard | Q16–Q18 + Lab 3 (L7) | 40–75 min problems; 2–4 lemmas; graded blueprint | verifier part + `/review-code` + `/grade-paper` pre/post; viva |
| Challenge | Q19–Q33 | 5 domain topics × 3, solo | `challenge_gate.sh` or harness + defense |

**The verifier part** (OD3): Dafny `vcheck --gate` (no `--allow-warnings`) exits 0 and whole-program `vaudit` reports 0; Verus `--output-json` shows `success` and `is-verifying-entire-crate` with no `encountered-vir-error` [verify names], and `--no-cheating` and the lint report 0; Python pytest is green with 0 AST holes.

### 7.2 Strands

| fam | strands (merged D/V) | payload [A] |
|---|---|---|
| A | **S1** data & programs, incl. exec overflow · **S2** specs & logic · **S3** proof statements & feedback · **S4** induction, recursion, loops, fuel · **S5** libraries & search | 17 |
| B | **S6** abstraction, frames, ownership · **S7** ghost/modes, subset types, termination, erasure · **S8** program logic (wp/VC by hand, a verified wp, permissions) | 16 |
| C | **S9** interfaces (CLIs, exit codes, JSON, `dafny server`) · **S10** pipeline & TCB · **S11** SMT mechanics · **S12** verifier loop, trust & agents · **S13** evaluation & spec quality | 18 |

S13 stays a strand: as a strand it must be swept every tier; folded into S12 it would be dropped first, and S12 would outgrow one section.

### 7.3 Rules

- **Usage:** any strand at the previous tier's depth plus earlier strands at this depth, per language. **D4 matrix:** unsuffixed keys cite a `d` and a `v` item; `@v`/`@d` keys are single-language.
- **Library (OD8):** prelude-only through Q03; enters in Q04's S5 files; import tiers (Dafny `core → std`; Verus `prelude → seq_lib → arithmetic → all` [verify]) linted transitively.
- **Empty-body gate (§2.8):** every hole must fail with `{}` under maximal automation. **Exits** sit outside every build; the first complete run scores.
- **Vivas:** 5 questions from 5 strands, ≥1 live-refereed predict, ≈30 min. **Test-out:** closed-book T items skip a section only if every first run is correct (saves 1.5–2.5 h [A]).

### 7.4 Core modules Q01–Q18

P = paired unit; D/V = single-language. "Agent" is the ladder rung (§12). Cards are `cheatsheets.md` ids.

| id | title | WRITE | predict themes (examples) | agent | card | min |
|---|---|---|---|---|---|---|
| Q01 | Hello, Dafny and Verus: the whole map | P `ensures`, `assert`, lemma call | `nat` vs `u64` minus; hole visibility per tool | 1 repairer + three doors | 02.3 | 227 |
| Q02 | First syntax I | P `assert-by`, `invariant`, `decreases`, quantified `ensures`; D frame; V divergence card | invariant one step short; empty-lemma auto-induction | 2 implementer vs checks | 02.7 | 234 |
| Q03 | First syntax II: modes, logic, tooling, trust | P ghost, exec checks, witness; D subset type; V modes | does erased code run; vacuous `requires` | 3 contract v0 by hand | 02.13 | 251 |
| Q04 | Proof craft, loops and libraries | P `calc`, `forall`, lemma recursion, library call; V `broadcast-use`, `nonlinear-arith` | auto vs manual induction; carry overflow | 4 retriever race | 02.2 | 251 |
| Q05 | Frames, ownership, modes, wp→VC | D dynamic frames, `by method`; V `&mut self` + `Result`; P `:-`/`?` (decimal parser), lexicographic `decreases` | missing `reads`; ghost in compiled output | 5 infra debugger [verify] | 03.12 | 253 |
| Q06 | The machine and the verifier loop | P `trigger`, `opaque`+`reveal`, `rlimit`, property tests | `--no-verify` exit (V18); CI width at n = 20 | 6 audited prover | 02.4 | 281 |
| Q07 | Internals I: proof engineering, translation | V `bit-vector`, `recommends`; P fuel, arithmetic library; D `isolate` | unfolding depth; port mismatch | 7 refactorer (+ Qwen replay) | 02.8 | 270 |
| Q08 | Internals II: refinement, permissions, verified wp | D `refines`; V trait specs, `tracked` | refinement adds `ensures` vs `requires`; linearity | 8 **spec-to-proof flagship** | 02.1 | 270 |
| Q09 | Internals III: brittleness, forensics, gate core | P stabilising split [verify]; trigger rewrite | seed flips; solver swap [verify]; LSP framing | 9 red-teamed contractor; contract v1 | 07.2 | 295 |
| Q10 / Q11 | Practice I-A / I-B | promotions | warm-ups | — | 02.11 / 02.12 | 182 / 177 |
| Q12 | Practice I-C + **Lab 1** | — | stage of 6 failures; intervals | 10 toolwright (`holecount`) | 05.10, 06.1, 04.8 | 576 |
| Q13 / Q14 | Practice II-A / II-B | — | — | — | 05.5 / 06.9 | 200 / 210 |
| Q15 | Practice II-C + **Lab 2** | — | trigger battery; intervals | 11 pipeline forensic, 12 toolsmith | 04.6, 04.7, 03.8 | 628 |
| Q16 / Q17 | Practice III-A / III-B | — | — | Q17: 13 metatheory | 01.13 / 12.12 | 225 / 225 |
| Q18 | Practice III-C + **Lab 3** + capstone | — | intervals | 14 reviewer → co-developer → adversary | 02.6, 05.9 | 575 |

Q08's extra is a verified wp for assign, sequence and if (Dafny; loops stay on paper). Q09 holds a fragile-proof repair pair, the solo gate core, and the Q half of the forensic corpus; its LSP content is framing only, and the client is Q15's.

### 7.5 Itemized minutes and practice content

Rates follow §2.5; agent wall-clock time is excluded; lines go into `QPLAN.md` verbatim.

| id | itemized minutes | total |
|---|---|---|
| Q01 | setup 15, read 45, worked 30, cards 15, predicts 25, holes 24, agent + three doors 25, paper 15, map exit 25, calib 8 | 227 |
| Q02 | setup 5, test-out 10, read 45, worked 32, cards 10, predicts 24, holes 48, agent 15, paper 15, exit 25, calib 5 | 234 |
| Q03 | setup 5, test-out 10, read 45, worked 26, cards 12, predicts 24, holes 32, wp on paper 20, fake-green specimens 12, contract v0 20, paper 15, exit 25, calib 5 | 251 |
| Q04 | setup 5, test-out 10, read 45, worked 30, cards 8, predicts 22, holes 54, library + mismatch lab 20, agent 15, paper 15, exit 22, calib 5 | 251 |
| Q05 | setup 5, test-out 10, read 45, worked 32, cards 8, predicts 22, holes 54, wp→VC 20, agent 15, paper 15, exit 22, calib 5 | 253 |
| Q06 | setup 5, test-out 10, read 48, worked 25, cards 8, predicts 22, holes 36, property tests 15, statistics by hand 30, `EVAL.md` v0 15, `TRUST.md` v0 10, agent 15, paper 15, exit 22, calib 5 | 281 |
| Q07 | setup 5, test-out 10, read 45, worked 30, cards 6, predicts 20, holes 56, port + fidelity 35, agent 15, paper 15, exit + explain-back 28, calib 5 | 270 |
| Q08 | setup 5, test-out 10, read 45, worked 30, cards 6, predicts 20, holes 56, verified wp 30, agent 20, paper 15, exit + explain-back 28, calib 5 | 270 |
| Q09 | setup 5, test-out 10, read 45, worked 20, predicts 20, repair pair 25, forensics 40, gate core 40, MDE on paper 10, red-team + contract v1 25, `EVAL.md` v1 10, paper 15, exit + explain-back 25, calib 5 | 295 |
| Q10 | brief 15, warm-up 8, `u64` round-trip pair 24, spec items 15, assertion repairs 16, `normalize` invariant pair 24, search-then-name 20, `Seq`-view ring buffer (V) 20, exit 20, paper 15, ledger 5 | 182 |
| Q11 | brief 15, warm-up 8, `Repr`/`Valid` class (D) 20, `&mut` + `Result` API (V) 20, subset types (D) 12, modes (V) 12, VCs by hand 20, wp soundness for `if` (D) 15, points-to primer (V, gated) 15, exit 20, paper 15, ledger 5 | 177 |
| Q12 | *practice:* brief 15, S9 retry client 20, S10 stage attribution 15, S11 trigger/fuel 15, S12 grade-the-grader 15, exit 20; *Lab 1:* hand items 96, pre-registration 45, `/grade-paper` 10, policies + report 110, run setup 20, analysis 75, transcript audit 20, `--post` 10, toolwright 15, cards 45, task cards 20, ledger + calib 10 | 576 |
| Q13 | brief 15, warm-up 5, `sub` with borrow (V) 35, `normalize` idempotent (D) 30, prose statement: comparison vs value order (V) 25, library goal (pair) 30, accumulator generalization (D) 20, exit 20, paper 15, ledger 5 | 200 |
| Q14 | brief 15, warm-up 5, abstract-BigNat refinement (D) 35, trait with ghost view (V) 30, termination + erasure (pair) 25, loop-rule soundness (D, gated) 30, permission node list (V, gated) 30, exit 20, paper 15, ledger 5 | 210 |
| Q15 | *practice:* brief 15, S9 LSP client 30, S10 pipeline forensic 20, S11 trigger battery + stability 30, S12 refute→repair→prove 15, toolsmith 20, tutor red-team 15, exit 20; *Lab 2:* prose specs 108, pre-registration 40, `/grade-paper` 10, oracles 75, vericoding arm 20, run setup 20, analysis 60, reward audit 15, bench audit 30, `--post` 10, cards 45, task cards 20, ledger + calib 10 | 628 |
| Q16 | brief 10, blueprint 30, H1 generalize before induction (D) 45, H2 `cmp` with invented invariant (V) 50, H3 `mul_limb` (V + D mirror, gated) 55, `/review-code` 15, paper 15, ledger 5 | 225 |
| Q17 | brief 10, blueprint 30, H1 priority-queue refinement with frames (D) 50, H2 permission ring buffer (V, gated) 50, H3 VC-generator soundness statements (D) 35, metatheory run 15, `/review-code` 15, paper 15, ledger 5 | 225 |
| Q18 | *practice:* brief 10, H1 brittleness repair under a solver swap 40, H2 capstone round 110, H3 gate v2 + adversarial round 85; *Lab 3:* case study 150, FP rate 20, `TRUST.md` + contract v2 30, proposal 60, `/review-code` 20, `--post` 10, cards 30, ledger + calib 10 | 575 |

**Totals:** concept 2,332 min; practice 2,998, of which lab blocks 1,269 (21.2 h). Q06/Q09 statistics are by hand and by composing the frozen `fvh.stats` (§10.3).

**Family-C practice** mirrors Lean's: Q12's retry client sends 3 candidates per goal over a given BigNat battery via `vcheck --json` (solve count pinned), and grade-the-grader runs 3 fresh `/grade-paper` passes on a flawed fixture; Q15's LSP client is written from scratch against `dafny server` [verify], and its tutor red-team uses a decoy `Solutions/`.

**Gated items** carry no minutes until DV5 admits them (fallbacks: the loop rule on paper; `Vec`-backed node list and ring buffer; Verus-only `mul_limb`). **Admissibility gate (MUST):** minutes only when the reference is complete and in band (intro D ≤10 / V ≤15 lines; intermediate 10–30 / 15–45; hard 30–80 / 45–120), the empty-body gate fails it, it is 3-seed stable, and lab pools validate on the pins.

**Task cards:** ≈14 `bench/local/q` cards by Q18 plus the Q18 crate, each with statement, stripped version, solution, witness and negative tests.

### 7.6 The challenge tier Q19–Q33

**Rules (§2.3.8).** Solo: `/contract` refuses and `/tutor` is capped at rung 2, with assists recorded. `Hidden/` is age-encrypted, unsealed only in the grader container, single-use. Results: pass, distinction, or abandoned with a retrospective. `challenge_gate.sh` checks frozen-statement sha256, zero holes per language, clean `dafny audit`/`vaudit`, the trust-leap lint, fresh-process N-seed re-verification (a second solver is labelled *not* independent checking), a reach scan, and CV and JSON completeness.

| module · lang | what is built | grading · held-out | h [A] |
|---|---|---|---|
| **(a)** Q19 Sorting · D + V | heapsort + quickselect; Verus port + fidelity audit | verifier · vectors | 25–40 |
| Q20 Hash map · V | open addressing refining `Map<K,V>` | ≤3× `std` · adversarial | 40–60 |
| Q21 Graphs · D (V port optional) | Dijkstra + union-find | proof + speed · graphs | 60–100 |
| **(b)** Q22 Codec & sequencer · V | fixed-layout codec; gap-free sequencer, idempotent replay | ≥1e6 differential vs Dafny model · fuzz | 30–50 |
| Q23 Matching engine · V | price-time book refining a `Seq` model | throughput, p99 · traces | 50–80 |
| Q24 Service · V | `dvx`: risk, torn-tail recovery, replay determinism, PnL | production bar · chaos | 80–150 |
| **(c)** Q25 Exact money · V (D model) | fixed-point `Dec`: rounding, overflow, mul-div | reference impl · vectors | 25–40 |
| Q26 Bit tricks · D + V | division by constants, popcount, saturation; `bv64` vs `bit_vector` | verifier | 30–60 |
| Q27 Multi-precision · V | Karatsuba, Montgomery, modexp | ≤3× `num-bigint` · moduli | 50–90 |
| **(d)** Q28 VC generator · D | While + invariants; VCgen soundness | planted weakened variant | 40–70 |
| Q29 Bytecode verifier · V | **register** bytecode; sound abstract interpreter | malicious/benign corpora | 50–90 |
| Q30 Re-check the oracle · choice | verified checker for Farkas certificates on a linear fragment of Q28's VCs (your oracle), or DRAT/LRAT on a propositional fragment [verify] | forgery corpus | 60–120 |
| **(e)** Q31 Gate & bench · D + V + `fvh` | Q18's gate extended; eval harness composing `fvh.stats` | hidden par · 40/60 tasks; 46 + 12 cheats | 30–45 |
| Q32 Proof-search agent · D + V | typed edits, dedup, value heuristic, retrieval | beat par at B · 3 × 40 sealed | 45–70 |
| Q33 Statement problem · D + V | autoformalization with faithfulness verdicts; red-teamed multi-agent coding with `MolePolicy` plants | 100% decidable rejection, FP ≤5% · 60 pairs | 60–100 |

Research value: (a) a bilingual held-out stratum (VERINA/CLEVER shape); (b) crate scale (VeruSAGE, Vero, CryptoProver); (c) the AutoVerus residuals; (d) certificate checking, the honest substitute for an independent re-checker; (e) the research program itself, with tool-less `claude -p` or Qwen policies. Each topic is authored statements-and-gate first and ends in a resize-or-kill call (settling Q30's scope).

### 7.7 Q hours

| block | h | cumulative | weeks at 7 h |
|---|---|---|---|
| P0 + Q01–Q03 + viva | 13.9 | 13.9 | 2.0 |
| Q04–Q06 + viva | 13.6 | 27.5 | 3.9 |
| Q07–Q09 + viva | 14.4 | 41.9 | 6.0 |
| Q10–Q12 + viva (**research-ready minimum**) | 16.1 | 58.0 | 8.3 |
| Q13–Q15 + viva | 17.8 | 75.8 | 10.8 |
| Q16–Q18 + viva | 17.6 | **93.3** | 13.3 (20 at 1.5× pace) |

**Challenges [A]:** (a) 125–200 h, (b) 160–280, (c) 105–190, (d) 150–280, (e) 135–215; all fifteen 675–1,165 h, a menu.

## 8. The R track (topic-ordered, authored in parallel)

### 8.1 Shape and module rules

| band | modules | persona / `/review-code` bar | hours |
|---|---|---|---|
| 1 Foundations | R01–R06 | "sharp dev, zero verifier" / it-reads → proof-shape | 35.7 |
| 2 Abstraction & theory | R07–R11 | "Rust dev who distrusts SMT" / library-conventions → design-judgment | 35.1 |
| 3 Machine, loop, capstone | R12–R16 | "ML engineer who thinks tests are proofs" / production + harness | 54.1 |

**Per module:** a self-contained 5–8k-word chapter; `.dfy`/`.rs` files with paired holes and ≥2 cross-language predicts; rubric, 12-question bank (8 for R01), 6-question `/viva`, `/review-code`. Checkpoints at R06/R11 (2 D + 2 V, ≥3/4, ≥1 per language); written track (OD11) in 13 modules; R02–R11 each add a `bench/local/r` card.

**Independence (decision 1).** No R record names a Q module; the checker rejects cross-track prerequisite edges. The README only *suggests* starting after Q09, and R12/R15/R16 after Q12/Q15/Q18; under the quota R ships from ≈ May 2027 (mid), so in practice it starts after Q18 or the agentic topic (D2). R teaches its whole payload: where Q owns a surprise, R states it as a fact with a hole, not a predict. `Recap → Qnn` and `Deep dive → Rnn` links are optional and the only cross-track mentions (I5). No imports from Q files, layers, `fvh_q` or `bench/local/q`.

### 8.2 Module records

"D | V" marks where the languages differ.

| id | title and core payload | exercises · written | agent | card | h · D/V |
|---|---|---|---|---|---|
| R01 | **Hello, two verifiers.** Three loops per tool; loud vs silent holes; R-owned `midpoint` overflow [verify] | `midpoint`; hole counting | repairer; three doors; R-v0 | 12.11 | 4.6 · 50/50 |
| R02 | **Datatypes and recursion.** `datatype Re`, `{:test}` \| `enum` + `Box`; spec `Matches` by splits; exec `nullable` tied to the spec [verify P6]; first property tests | `Nullable`, `Size`, `Rev` · termination of `Matches` | implementer vs checks | 05.6 | 5.7 · 45/55 |
| R03 | **Modules and APIs.** Export sets \| views; open/closed specs; a total `CharClass` API | `ClassUnion`, `ClassMember` | API implementer | 03.2 | 5.0 · 50/50 |
| R04 | **Specs as logic.** Audits, vacuity, witness strings; anchored vs unanchored specs; R-owned: `expect` is assumed | witnesses · classify specs | audited prover | 12.5 | 6.0 · 50/50 |
| R05 | **No goal state.** Obligations, bisection, latency; run-to-run variance, CV, first CIs | bisection; variance log · facts per line | obligation prover | 06.3 | 6.7 · 50/50 |
| R06 | **Induction and loops.** Invariants as IH; refute → repair → prove | **flagship** derivative correctness (`Star` spike-gated) + matcher-loop invariant; checkpoint · paper proof of the `Cat` case [A] | decomposer | 03.4 | 7.7 · 50/50 |
| R07 | **Libraries: what they cost.** Std/vstd set and sequence lemmas; toolchain-mismatch lab; trusted base [verify]; unbiased pass@k on the retriever race; `EVAL.md` R-v0 | trust audit; pass@k by hand | retriever race | 06.5 | 6.0 · 50/50 |
| R08 | **Abstraction.** A `Matcher` interface refined by the derivative matcher; opacity \| traits | refinements · obligations | infra debugger | 06.7 | 5.9 · 50/50 |
| R09 | **Effects.** Regex-syntax parser with positions, `:-` \| `?`; counted repetition with overflow-checked bounds | **port + fidelity audit** (D → V); overflow and `char`-encoding divergences [verify] | refactorer | 06.11 | 7.4 · 45/55 |
| R10 | **Invariants in types.** Smart constructors and normal forms: subset types \| `type_invariant` [verify]; erasure | `NormRe` · erasure | **flagship**: smart constructors preserve the language | 03.5 | 6.8 · 50/50 |
| R11 | **Theory.** wp/VC on the matcher loop; a certifying matcher with a verified derivation checker; V: **gated** `PointsTo` NFA arena | `Derivation`, `CheckDeriv`; checkpoint · derivations | metatheory | 12.10 | 9.0 · 55/45 |
| R12 | **Driving the verifier + Lab α.** Doors; LSP framing from a captured trace; a streaming verdict parser and obligation extractor over both tools' JSON [verify]; a 20-line loop | extractor · pre-registration | toolwright: per-function time/rlimit profiler [verify] | 06.10, 01.12 | 13.1 · 35/35/30 |
| R13 | **Pipelines and trust.** Stages; no-kernel TCB; `TRUST.md` R-v0 | `--log` [verify]; forensics (R half of G/V) | pipeline forensic | 12.3 | 6.5 · 50/50 |
| R14 | **SMT mechanics.** Triggers on split existentials, matching loops over concatenation, fuel on `Matches`, seeds | 12-assertion battery; CV sweeps | toolsmith (`trigscan` [verify]) | 02.5 | 6.5 · 45/55 |
| R15 | **Verifier loop + Lab β.** Escalation ladder with property tests against the Rust `regex` crate [verify]; statement review; grade-the-grader; contamination control | grade-the-grader; injection · pre-registration | red-teamed → R-v1 | 03.10, 05.2 | 12.4 · 45/45/10 |
| R16 | **Capstone + Lab γ.** Compile `Re` to a Pike-style VM (`Char`/`Split`/`Jmp`/`Match`); code-at-offset simulation generalized over the continuation (found on paper); jump threading; ship `rexc` | statements, proofs, plant, `rexc`, gate, card + memo · blueprint | reviewer → co-dev → adversary | 07.3, 12.9 | 15.6 · 30/70 |

**Totals.** Bands 2,142, 2,106 and 3,246 min: **R = 124.9 h standalone** (17 h of lab halves, 30-min vivas), ≈119 h with Q-credit [A]. That is ≈+10 h on the earlier draft (standalone labs +8.7; R05 variance +0.5; R07 pass@k, R09 fidelity method and R15 contamination +0.25 each). Itemized lines go into `PLAN.md` before DVR1.

## 9. Disjointness between the tracks

### 9.1 Gate

`avoid.sh` implements §2.7 symmetrically (on a collision, the side that left `planned` later changes; in practice R). It compares declaration names from all three languages, prefixes stripped, against the other track's hole-bodied declarations, bank and written problems, chapter code fences, and a curated list carrying Lean Q's spine identifiers and Lean R's exercise names (from exercise files only). Waivers record key, source, reason, direction and cost; stale waivers are errors. Each track's banks are also checked against its own exercises.

### 9.2 Partitions

1. **Owner tags.** Q owns `nat` vs `u64` minus, hole visibility, proved vs computed, auto-induction; R owns `midpoint` overflow, `expect` outside tests, strengthened `requires`, empty-string/anchoring surprises, later-stage failures.
2. **Specimens:** the G/V corpus splits into a Q09 half and an R13 half, each covering every X family. **Paper cards** are never shared or repeated.
3. **Artifacts.** Q alone has BigNat, ring buffer, priority queue, decimal parser and a While language with verified wp; R alone has the regex AST, matchers, derivations and VM; Q29 is a register machine; no expression-language compiler appears anywhere.
4. **Statistics code** exists only in the frozen `fvh` core. **CI isolation** runs both ways.

### 9.3 Shared genres and waivers (D3)

Each cost names the insight pre-empted for a learner who does the Q home first; R repeats the genre on its own objects.

| waiver | genre: Q home → R home | pre-empted insight |
|---|---|---|
| W1 | role ladder → R, harder objects | each role's first failure mode (gaming checks, weakening statements) |
| W2 | hole contract, doors: Q01 → R01 | silent vs loud holes (≈1.2 h of R01 becomes test-out) |
| W3 | contract, `EVAL.md`, `TRUST.md` → `R-vN` | that unenforced contract rules are suggestions |
| W4 | port + fidelity: Q07 → R09 | that implication lemmas alone are circular |
| W5 | wp/VC by hand → R04/R06/R11 | the wp calculus itself (≈30 min of R11 is review) |
| W6 | permissions: Q08–Q17 → R11, gated | the linearity error |
| W7 | invariant generalization: Q13/Q16 → R06 matcher loop | "generalize the invariant before proving" |
| W8 | agent loop: Q12 retry client → R12 obligation loop | that a verdict loop needs a parser before a model |
| W9 | matched compute: Q12 → Lab α | compare at equal calls, not equal attempts (curve crossings stay new) |
| W10 | spec oracles: Q15 → Lab β | vacuous specs pass verification; mutation kill measures strength (oracle agreement stays new) |
| W11 | gate: Q09/Q18 Python → R16 Rust | fresh-process pinned re-runs (V20) and UNKNOWN on grader-only classes (inflation stays new) |
| W12 | framing: Q18 proposal → R16 card + memo | scoping a claim to a small-n replication |
| W13 | R pre-empting Q32/Q33 | R12/R15 code may make solo Q32/Q33 start easier (avoided under D2's default) |
| W14 | parse with errors: Q05 → R09 | `:-`/`?` propagation (positions and fidelity stay new) |
| X1 (cross-course) | compiler correctness by generalized simulation: Lean R16 → R16 | "generalize over the code that follows" (nondeterministic `Split` stays new) |

No waiver is needed where artifacts differ: LSP-by-hand is Q-only (R12 reads a trace); the toolwright tools (`holecount` vs profiler); the library lab; the forensic halves; tutor red-team vs grader injection. The earlier draft's W14 (deep evaluator) is dropped: it was an avoided overlap.

## 10. Running artifacts

### 10.1 Q spine: BigNat (little-endian limbs)

BigNat beats the spec's bit-list numeral: a bit-list would transfer by renaming to or from Lean Q's `Bin`; `Vec<u64>` limbs force overflow, carries [verify vstd specs], nonlinear products and bit-vector facts (the AutoVerus residuals); it links to vericoding's BigNum weakening, CryptoProver's limbs and Q27; and early surprises survive (limb order, non-canonical zeros, `nat` vs `u64`). The abstraction is Horner-style over a **literal** `BASE = 2^64`, so multiplying by `BASE` stays linear. Layers are frozen (rule 2f) and re-supply the previous tier's targets; holes are leaves.

| layer · modules | Dafny `dafny/given/Q/QG_L<k>_BigNat.dfy` | Verus crate `verus/given/qg_bignat_l<k>` |
|---|---|---|
| L1 · Q01 | `seq<nat>` limbs, `BASE`, `ToNat`, `Valid`, a worked lemma | `BigNat { limbs: Vec<u64> }`, `view`, `to_nat`, `wf`, a worked `proof fn` |
| L2 · Q02–Q03 | `Normalize`, `FromNat`, `AddLimb` | `normalize`, `from_u64`, `add_limb` |
| L3 · Q04–Q06 | `Cmp`; std-tier helper | `cmp`; a lemma group for `broadcast use` |
| L4 · Q07–Q09 | `Add` with proof; `MulLimb`; `abstract module BigNatSpec` | `add` with proof; `mul_limb`; `trait NatLike` |
| L5–L6 · Q10–Q15 | earlier targets; lab pools; `Sub`; prose tasks; mutation fixtures | same |
| L7 · Q16–Q18 | Dafny mirror of the mini-crate | mini-crate with frozen spec files |

Each Verus layer crate depends only on the layer below and each module crate on exactly its tier's layer, so no module can call a later layer's re-supplied lemma (a cheat-corpus specimen). Extras: `bool` formulas, ring buffer, priority queue, decimal parser, While language, JSON fixtures, error zoo.

### 10.2 R artifact: a regex engine

| layer · from | content (`dafny/given/R/RG_A<k>_*` / crate `verus/given/rg_re_a<k>`) |
|---|---|
| A1 · R02 | `Re = Empty \| Eps \| Chr \| Alt \| Cat \| Star`; spec `Matches` over `seq<char>` by splits; `Nullable` |
| A2 · R07 | `CharClass` (re-supplied from R03); `Deriv` and its correctness lemma (re-supplied from R06) |
| A3 · R09 | concrete syntax with positions; `Rep(r, n, m)` |
| A4 · R10 | `NormRe` smart constructors; `Derivation` trees for R11 |
| A5 · R16 | VM: `Inst`, `Step`, fuelled `Accepts`, frozen (the capstone statements are yours) |

**Why regex:** absent from both Lean tracks, so nothing transfers by renaming; existential splits are a classic trigger and matching-loop problem (R14), and anchoring and empty strings classic faithfulness traps (R04, R15); the Rust `regex` crate is a ready differential oracle for whole-string matching [verify]; R16 simulates nondeterministic acceptance, not stack evaluation. **Risks:** the `Star` case and VM completeness for nullable `Star` bodies are DVR0 spikes, with star-free and forward-jump fallbacks. Q's tension is numeric, R's structural and semantic; Q ships `bignat`, R ships `rexc` and a Dafny mirror.

### 10.3 `fvh`, `bench/local`, standards documents

**`fvh`.** The frozen core (`harness/fvh/`, rule 2f) holds the protocol `propose(state, ctx, budget) -> [Action]`, the records, backends (Mock, Scripted, Replay, `claude -p`, opencode), budgets, the sandbox client, the public cheat corpus, and **`fvh.stats`** (unbiased pass@k, Wilson/bootstrap CIs, McNemar, permutation tests, Holm, MDE). Learner parts: `fvh_q` (Q12 policies and `report`, Q15 oracles, the solo `gate/`) and `fvh_r` (obligation extractor and loop, Lab α's engine, `spectest`, `roundtrip`); R's gate is Rust. Holes are AST-counted. The reference is `Solutions/harness/`, never a workspace member, with a grader-only corpus on which your gates must say UNKNOWN.

**`bench/local/{q,r}`.** Q: ≈14 cards plus the Q18 crate. R: 24 vericoding cards (your 10, plus 14 by the author [A]) and stripped R06–R14 lemmas. **Ground truth by owner:** `bench/local/*/answers/` holds only *your* answers; author answers live in `Solutions/bench/local/r/`, opened last; hidden lab truth (Lab 2's reference specs, Lab β's verdicts) lives in `Hidden/labs/<ID>/`, unsealed only in the grader container and released to `Solutions/labs/<ID>/` after acceptance. Each lab gets must-block fixtures and leak patterns; no sandbox copies answers. Cards pass oracle audits; contamination controls are post-cutoff authorship, novelty review, perturbation probes and in-context isolation.

**Standards documents (D3 default):** one `CLAUDE.md` contract block (`Q-v0…v2`, `R-v0…v2`) plus `research/EVAL.md` (Q v0 at Q06, v1 at Q09; R-v0 at R07) and `research/TRUST.md` (Q v0 at Q06; R-v0 at R13; finals at Q18 and R16).

## 11. Research layer (both tracks)

### 11.1 Shared apparatus

- **Reading.** `/grade-paper` grades each card against sha-pinned `cheatsheets.md` ranges on fixed fields (task shape, oracle, trust, cheat surface, metric, budget, variance, artifact).
- **Pre-registration (every lab, including γ)** states the claim, metric and estimator; the **budget arithmetic** (calls = tasks × attempts × rounds × arms × repeats; tokens; GPU-h) and the **MDE**; the cheat surface and gate; `firsttry` intervals and a stopping rule. A run unlocks only when `/grade-paper` scores ≥3 on every method dimension; `fvh` refuses runs without the committed hash.
- **Quota design.** One Claude final arm per lab on ≤20 tasks, descriptive (CIs ≈ ±20 pp), reported as "repeated runs", never "seeds"; multi-arm comparisons run on Qwen with real seeds.
- **Acceptance:** `fvh report` reproduces every table from logs; your gate passes each claimed success from a clean checkout; a disclosure block is present. **Grading is on method and reproducibility, never on matching numbers**; reports disclose that Claude is both grader and subject.
- **Benchmarks** come from a sha-pinned manifest: MIT/Apache sets vendored, GPL/unlicensed/NC fetch-only [verify licences]; every run is a "small-scale replication with model substitution".
- **Engines (OD15):**
  1. **Interactive `/contract`** on the host, under the hooks: the only engine whose edits land in the learner tree.
  2. **Policy mode**, with the harness as sole executor (X18).
     - Claude: `claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --json-schema <s> --model <pinned> --effort <pinned> --system-prompt <prompt>`, on the host, from an empty cwd with a credentials-only `CLAUDE_CONFIG_DIR`. Probed on 2.1.288; `--max-turns` and full prompt replacement are [verify]. Never `--bare` (API key only).
     - opencode: isolated HOME, `tools {"*": false}`, `mcp {}`.
     - **Harness-executed agent runs:** the harness applies the policy's typed actions (read, edit, run the pinned verifier) in the per-run container.
  3. **Agent mode** (tool-using agent in a per-run container): opencode + local Qwen, and Claude Code with its own tool loop under D6's safeguards (read-only credentials, Anthropic-only egress, secret scan, token rotation [verify]). Harness-executed Claude runs remain the fallback if the read-only credential probe fails.
- **Apparatus.** Sha-pinned binaries, auto-update off [verify]; records carry CLI version, model id, prompt hash, Ollama digest and sandbox manifest; disclosure states which Claude runs used Claude Code's own tool loop (agent mode) and which acted through `fvh`'s action schema (policy or harness-executed mode).
- **Budgets.** Caps on calls, tokens, wall-clock and GPU-s with a rolling window and checkpoint-and-resume, so a rate limit never becomes best-of-n; one calendar shares GPU, RAM and verifier pool with Lean's par runs; `qwen3.8-flash-next` needs CPU offload [verify], `qwen3.8` is the workhorse.
- **Cheat corpus.** Two layers: trusted `vcheck`/`vaudit`/`specfreeze`, and your gates, which must agree with them. Contents: G1–G22 and V1–V24 (≥46 live-captured), rlimit inflation, CryptoProver's fabricated axioms, AlphaVerus exploits, later-layer calls, build-tool poisoning (`build.rs`, `conftest.py`, `.cargo/config.toml`, `dfyconfig` `--plugin`/`--solver-path`), and the legacy-CLI bodyless lemma (exit 2 new, 0 legacy [verify]). Timeouts and `unknown` are failures; resource limits, never wall-clock, are pinned; `<think>` blocks are stripped.

### 11.2 Q labs

**Lab 1 (Q12, 476-min block): proof completion at matched compute.** At budget B, do sequential feedback or best-first search beat independent sampling, and does it differ by language (R4)? Hand part: 4 D + 4 V, ≥3/4 per language. Qwen policies: B independent samples; one sample + B−1 repairs; best-first over edit states ranked by failing obligations; the Claude arm runs the pre-registered pick. Budget [A]: Qwen 60 tasks × 3 arms × 8 × 3 repeats = 4,320 calls (≈6–10 GPU-h), Claude ≈180. Paired McNemar or bootstrap with Holm; MDE at n = 60 ≈15–20 pp [A].

**Lab 2 (Q15, 463-min block): spec quality and vericoding.** Do your oracles separate faithful, weak, vacuous and over-strong specs, and does oracle feedback raise agent faithfulness? **Vericoding arm:** how often does an agent that implements and proves against its *own* spec fail when re-judged against the reference spec? You build 3 D + 3 V prose specs with witnesses (graded by hidden two-way implication plus mutant kill; truth in `Hidden/labs/Q15/`), mutation and subset-implication oracles (FAITHFUL/WEAK/STRONG/VACUOUS/UNDECIDED, UNDECIDED counting as unfaithful), a reward audit (no training) and a `bench/local/q` audit. Budget [A]: Qwen ≈1,200 calls, Claude 80.

**Lab 3 (Q18, 330-min block, beside practice H2/H3): gates at crate scale.**
- **Capstone (H2):** a blueprint graded ≥3; frozen statements with a statement-only review; a co-developer; an adversarial plant; ship `bignat`.
- **Gate v2 (H3):** a fresh process per crate running the pinned command, never `cargo build`/`test` (V20); JSON completeness and minimum counts; `--no-cheating`, `vaudit`, `specfreeze`; an option allowlist (G5–G10, G14–G17, V16–V19, V22, V24); build-tool checks; a 3-seed CV. It must reject every decidable class, say UNKNOWN on X07/X08/X14, and report its FP rate.
- **Case study:** gated vs prompt-only on 12 crate tasks, with Claude ≤24 harness-executed runs and Qwen × 3 agent runs. It measures re-judged success, cheat rate by class, and cost. Then `TRUST.md`, contract v2, and a 1-page proposal.

### 11.3 R labs: complementary and standalone

**Lab α (R12, 390 min).** Where do the three regimes' success-vs-budget curves cross, and does obligation-localized feedback beat raw verifier text? You build a hint-site environment over frozen specs and **one parametric engine** whose (width, depth, priority) settings give all three regimes at equal node budget. Minutes: environment 60, engine 90, pre-registration 40, `/grade-paper` 10, setup 25, analysis 75, transcript audit 20, `--post` 10, report 50, calib 10. Data [A]: 40 `bench/local/r` tasks plus an unused public slice; Qwen 5,120 calls (≤10 GPU-h), Claude 160. Paired permutation tests per budget point with Holm, clustered bootstrap bands; re-judging by the course-shipped `vcheck --gate`/`vaudit`/`specfreeze`.

**Lab β (R15, 360 min).** Do two independent oracles agree, with each other and with hidden verdicts, and how often is "verified" also "faithful", D vs V (R1)? You build `spectest` (soundness on reference I/O, completeness against mutated outputs) and `roundtrip` (spec → NL → spec, equivalence verified both ways). Minutes: spectest 75, roundtrip 65, pre-registration 35, `/grade-paper` 10, setup 20, analysis 60, card contamination audit 30, `--post` 10, report 45, calib 10. Data [A]: 24 R cards × 4 variants, verdicts in `Hidden/labs/R15/`; Qwen ≈960 calls, Claude 80. Confusion matrix, κ, verified-but-unfaithful rate.

**Lab γ (R16, 270 min).** What fraction of naive-grader successes (exit code, `cargo build`/`test`, a "verified" substring, one seed, `--allow-warnings`) survive your gate, by cheat class (R2)? You build `rexc trust-report` from your R13 forensics, R15's ladder and the R half of the corpus (PASS/FAIL/UNKNOWN). Minutes: pre-registration + budget 30, `/grade-paper` 10, gate 90, naive graders 20, setup 20, analysis 50, report 40, calib 10. Data: every α/β success plus 12 crate tasks (8 possible, 4 impossible); Claude ≤24 harness-executed runs, Qwen × 3. Inflation per class with CIs.

**Six-lab totals [A]:** Claude ≈500 policy calls (180 + 80 + 160 + 80) plus ≤48 harness-executed runs at ≤25 calls each, ≤≈1,700 calls from the study reserve; Qwen ≈11,600 policy calls plus ≈72 agent runs in ≤45 GPU-h.

## 12. Agentic ladders (both tracks)

Contractor = an interactive `/contract` session (the agent as colleague); subject = a headless `fvh` run. The rungs come in the same order in both tracks; R's objects are disjoint and harder.

| rung | Q | R |
|---|---|---|
| 1 repairer + three doors | Q01 | R01 |
| 2 implementer vs checks | Q02 | R02, R03 |
| 3 contract v0 by hand | Q03 | R01 |
| 4 retriever race | Q04 | R07 |
| 5 infra debugger | Q05 (wiring) | R08 (semantic) |
| 6 audited prover | Q06 | R04, R05 |
| 7 refactorer under harness | Q07 | R09 |
| 8 **spec-to-proof flagship** | Q08 | R10 |
| 9 red-teamed contractor | Q09 | R15 |
| 10 toolwright | Q12 (`holecount`) | R12 (profiler) |
| 11–12 pipeline forensic; toolsmith | Q15 | R13, R14 |
| 13 metatheory contractor | Q17 | R11 |
| 14 reviewer → co-developer → adversary | Q18 | R16 |
| decomposer | — | R06 |
| experimental subject | Q12, Q15, Q18 | R12, R15, R16 |
| you build the agents | Q31–Q33 | — |

You specify and audit (diffs, `vaudit`, `specfreeze`, probes, your gates). Contracts keep three keys (§3.11.2); allowlist lines must be in the module's own `agentic` list, so a Q contract never unlocks an R file; `instructor/` writes are denied while any allowlist is non-empty (OD13). From Q07, `contract_local.sh` replays a contract under opencode + Qwen in a container and returns a patch (N2).

## 13. Instructor layer and isolation

### 13.1 Kept and trimmed

| decision | pieces |
|---|---|
| **keep** | the §0.4 core; four guard layers and leak patterns; **both tracks with the disjointness gate**; Q tiers, exits, tier vivas; R module vivas and written track; predicts, first-try, goldens; `/tutor`, `/review`, `/contract`, `/viva`, `/grade-paper` |
| **rewrite** | the CORE referee for asymmetry (§6.5: a confirmed flaw needs an executable counterexample or verified refutation); `review-lean` → `/review-code` (OD18 bars + `harness`/`production`, brittleness) |
| **trim** | written work becomes wp/VC, blueprints, cards, pre-registrations, memos; Q banks ≈8, R banks 12 (8 for R01); one `concepts.md`; `/discuss` optional |
| **fix on day one** (§12.3) | vocabulary in CORE; templates from CORE; checker authoritative; one CONTRACT block; no grep hole counts; instructor sessions never delegate |

### 13.2 Guard

| rule | covers |
|---|---|
| deny | the four canonical rules plus `Read(~/.claude/projects/*/*.jsonl)`, `Read(~/.claude/file-history/**)`, `Read(~/.claude/history.jsonl)` (other sessions' transcripts only; the project's memory dir and the session's own tool results stay readable) |
| 1e | `/tmp/claude-*` other than the session's own scratchpad (session from the hook input [verify]) |
| 1f | `opencode`, `codex`, tool-enabled nested `claude`, and container tools (`docker`, `podman`, `nerdctl`, `lxc`, `sg docker`, `docker.sock`, `DOCKER_HOST`, `curl --unix-socket`, Python `docker`), each with a must-block fixture; allowed only via `mksandbox-run`, `contract_local.sh` or `fvh`; `Skill(local-assistant)` denied if supported [verify]. The hook header states that all of this is a tripwire, not a sandbox |
| 1 | the reference set (`Solutions/` incl. `bench/` and `labs/`, `Hidden/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, `~/.cache/dafny-verus-learn-0/**`); bare words; content scans for Dafny `include`/`.doo`/`dfyconfig` reach, Verus `mod`/`#[path]`/`include!`/Cargo `path`/`--extern`, Python imports/`sys.path`/`.pth`/`pip -e` |
| 1b | reference builds in every tool (`dafny`, `vcheck --ref`, `cargo verus` into `Solutions/`, `uv run --project`, `pytest`, `make paper-solutions`, author scripts) |
| 1d | build outputs count as reach: `target/`, `build/dafny/`, `.verus-log/`, `__pycache__` |
| 2 | learner-owned: `dafny/{Q,R}/`, `verus/{q,r}/`, `harness/{q,r}/` minus gates, `slots/`, paper answers, `research/`, `bench/local/*/{tasks,answers}`, `tools/` |
| 2s | solo: `Challenges/`, `agents/`, Q's gate, R16's `trust-report` |
| 2f | frozen: `*/given/**`, `harness/fvh/**`, `expected/**`, challenge statements |
| 2g | guard and build: `.claude/` hooks and settings; `dfyconfig.toml`, `Cargo.*`, `.cargo/`, `build.rs`, `pyproject.toml`, `uv.lock`, `conftest.py`; `sandbox/`; **`MODULES.toml`**; **`scripts/`** |
| other | pytest excludes reference and answers; WebFetch/WebSearch and `bench/public/**/answers` denied during contracts and experiments |

**Fixtures:** ≈480 [A], generated from ≈210 templates over {Q,R} × {dafny, verus, python} and drift-checked.

### 13.3 The agent sandbox (per run)

Probed inside a Claude Code session [verify outside]: `bwrap --unshare-net` fails (`RTM_NEWADDR`), `unshare -rn` fails on `uid_map`, AppArmor restricts unprivileged user namespaces; Docker 29.1.3 works. So the sandbox is Docker (rootless as a separate user is optional, H2 [verify]), reached only through `mksandbox-run <manifest>`. Its purpose is research validity: the agent under test sees only the task, never ground truth.
1. **Contents:** the stripped task, the toolchain image by digest, stdlib/vstd sources; never the repo, git history, `Solutions/`, `Hidden/`, answers, finished exercises, `instructor/` or logs.
2. **Self-test:** a clean scan for ground-truth hashes and leak patterns; the manifest hash goes into the record.
3. **Network:** an allowlist proxy permits host Ollama `:11434` and, for Claude runs (D6), the Anthropic API endpoints only [verify hosts]; all access is logged; WebSearch/WebFetch are disabled by flag and settings deny; host loopback from rootless networking is [verify].
4. **Credentials (D6):** Claude runs mount only the credentials file, read-only, into an isolated `CLAUDE_CONFIG_DIR`; opencode runs get none. `~/.claude` and the Docker socket never enter a container. Every returned file and log passes a secret scan before it reaches `research/runs/`, and the token is rotated after each batch [verify mechanism]. If DV0 shows the token cannot refresh on a read-only mount, Claude falls back to harness-executed runs.
5. **Return:** allowlisted, diff-filtered files go to `research/runs/`; project files are re-materialized from trusted copies (`Cargo.toml` with `build = false`, no new dependencies).
6. **Verification** runs in a second container with no network and no repo; agent output never executes on the host and is never merged (N2).

## 14. Repo layout and infrastructure

### 14.1 Tree

```
dafny-verus-learn-0/
  README.md CLAUDE.md PLAN.md (R) QPLAN.md (Q) VERSIONS.md MODULES.toml concepts.md
  dafny/ options/{core,std}.toml  given/{Q,R}/  checks/<ID>_checks.dfy   # given-only value-predict units
         Q/Q04_<Name>/{core,std}/{dfyconfig.toml, *.dfy}  R/…
  verus/ Cargo.toml Cargo.lock rust-toolchain.toml .cargo/
         given/{qg_bignat_l1..l7, rg_re_a1..a5}/                          # one crate per layer
         q/q04_<name>/{Cargo.toml, src/lib.rs, src/agent.rs*, src/exit.rs*}  r/…   # * not mod-declared
  harness/ pyproject.toml uv.lock  fvh/ (incl. stats)  q/fvh_q/  r/fvh_r/  tests/{core,q,r}/
  research/{EVAL.md,TRUST.md,runs/}  bench/{public,local/{q,r}}/…/{tasks,answers}  specimens/ slots/ expected/ docs/ paper/ sandbox/ Challenges/ agents/ tools/
  Solutions/ dafny/ verus/ (own [workspace]) harness/ (own uv project) bench/ labs/ pins/ runs/ Challenges/Ref
  Hidden/ (age-encrypted: Challenges/, labs/)   instructor/ scripts/ tests/ .claude/ .vscode/ .github/
```

### 14.2 Wiring

1. **One verification unit per (module, language, library tier)**, so a half-edited Q05 never turns Q02 red.
   - **Dafny:** a generated `dfyconfig.toml` per tier subdirectory (the IDE uses the nearest project file), holding module roots plus the tier's given layers. Value predicts run from given-only units in `dafny/checks/` (§3.3, §3.8.6). Probes D13 (`includes` reaching `../../given`) and D14 (IDE scoping, incl. tier subdirectories) [verify]; fallback: one project per (track, tier).
   - **Verus:** one package per module, depending on `vstd` and exactly its tier's layer crate; the checker compares Cargo dependencies with the registry. Probes P13b, P14 [verify].
2. **Re-supply (I1)**: exercise, agent and exit files import given layers only. **Naming**: Dafny modules carry a track prefix; pairs share names, so a file never builds with its pair; reference identifiers start with `solutions`.
3. **Out-of-root files** (exits, red-by-design files, specimens) build standalone via `vcheck`, with CI-pinned state; projects are generated from `dafny/options/<tier>.toml`, drift-checked.
4. **Defaults:** Q builds by default (`default-members` [verify P13], pytest `testpaths`); R by name; never the reference.
5. **Coexistence** (learner files only; resolving reference files is CI-only): one `dafny resolve` over both tracks and over both languages' pair files; one Cargo lock and `vstd`, `--workspace` [verify]; one Python process importing `fvh`, `fvh_q`, `fvh_r`.

### 14.3 Registry and checker

`MODULES.toml` starts at `schema = 1`, every field required, in order. It keeps Lean's fields and adds `langs`, `exits`, `harness`, a sha-pinned `card`, `units`, `layer`, `engines` ⊆ {contract, policy, agent}, `statements`, `deep_dive`, per-language WRITE/RECOGNISE lists, `[module.budget]` (non-zero iff policy or agent) and `[module.admissible]`; there is no cross-track prerequisite field. Item ids are `<ID>.<K><n><lang>` (`lang ∈ d|v|py|dv`); coverage rows carry `payload_id`, `langs`, `q_homes`, `r_homes`, `deepening`, `gap`.

| group | checks |
|---|---|
| `registry` | Lean's checks; Q tiers partition **S1–S13** and end in a viva; derived `units`; `langs` match files; budgets match engines; **no cross-track prerequisite** |
| `units` | generated projects and members equal generator output; Verus dependencies equal the `layer` tier |
| `import-tiers` | per language, transitively |
| `isolation` | I1; **I2: tracks never import each other**; prefixes; the I5 residue check |
| `coverage` | items parse; D/V parity; ≥2 uses per slug per language; rows resolve in both tracks; no minutes on inadmissible items |
| `vocab` | one `concepts.md`; banks complete (8 Q / 12 R) |

### 14.4 CI

- **Scope:** `main` and authoring PRs, never `leobwang-*`.
- **Runner:** self-hosted as `dvci`, with a 0700 workdir, no group shared with you, no model credentials, and Anthropic hosts blocked.
- **Empty id lists** fail.

| job | content |
|---|---|
| `static` | checker + tests; symmetric `avoid.sh`; generator equality; AST hole counts; study mode shipped |
| `hook-test` | `test_hooks.sh` (incl. container-tool fixtures); `course_mode.sh`; wiring |
| `verify` ×4 ({Q,R} × {dafny,verus}) | toolchain sha; every non-planned unit builds with **hole counts by tool = chapter = CI pin**; **empty-body gate**; reference build to a log (hole-free, `vaudit` 0, `specfreeze`); `pins.py --ci`; an empty track passes **loudly** |
| `coexist`, `harness` | §14.2 rule 5; `uv sync --frozen`, ruff, pytest with Mock/Scripted/Replay, hollow learner Python, sandbox self-test; **model backends are a tripwire** |
| `paper`, `challenges`, `brittleness` (nightly), `bench` (manual) | as named |

**Never on the learner branch or in a study session:** reference builds, pin updates and lint, the leak checker, unsealing, decoy fixtures, any model call.

### 14.5 Pins and probes

Every cell is [verify] in DV0.

| | Dafny | Verus |
|---|---|---|
| binary | 4.11.0 zip (x64-ubuntu-22.04), sha256 `a46a9ff7…8267179` | weekly `0.2026.09.27.3cf1832`, never rolling (≈486 MB) |
| solver | bundled Z3 4.12.1 (default) + 4.14.1 | bundled Z3 4.16.0 |
| deps | `--standard-libraries` from Q04/R07 | Rust 1.98.1 exactly (host 1.92.0, probed); `vstd = "=0.0.0-2026-09-20-0158"`; `regex` as an R15 dev-dependency [verify] |
| IDE | ide-vscode, `"dafny.version": "4.11.0"` | verus-analyzer with pinned `verusBinary`; verusfmt |
| run | `--target py` | `verus --compile`; `cargo test` beside `verus!` (P6) |
| hazard | no nightlies | weekly churn: ≤2 bumps a year |

**Other pins (probed):** Claude Code 2.1.288, opencode 1.18.25, Ollama 0.33.2; plus model and image digests, Python 3.12 + `uv.lock`, latexmk. **Probes** (into `VERSIONS.md`): D1–D14 and P1–P15 (D13, D14, P13b, P14, P15 and `--workspace` new); the legacy CLI; D8; `find-dead-code`; `verus-spec-check`; the Docker sandbox with host-Ollama reachability (rootless optional); Ollama `/v1/messages` (empty body → HTTP 400; compatibility [verify]); Qwen throughput; pool validity; the `claude` flags.

## 15. Authoring plan, quota and calendars

### 15.1 Calibration

1 MU ≈ 25 author-hours [A]; Lean R ≈16 MU, Lean Q ≈44 (Q01–Q18 14.7, challenges ≈24.9, validation 3.0). Bilingual uplift: chapters ×1.3, pair/hollow/pins ×2.0, kit ×1.25, simulation ×1.3, weighted 35/35/20/10 → ≈1.53; working figure **×1.6 (1.45–1.8)**, higher for Verus, where authoring agents are weaker. Cost per learner-hour: Q ≈0.36 MU (with DV4), R ≈0.26. Order: solutions-first, risk-first.

### 15.2 Phases

| phase | content | MU |
|---|---|---|
| **DV0** | pins, probes, Docker sandbox; BigNat L2–L4 spikes in both languages (complete, in band, empty-body-killed, 3-seed stable); first MU/week figure | 3.0 |
| **DV1a** (PR 1) | registry, checker, generator; hook (two languages, two tracks, 1e/1f) with fixtures; CORE and skills | 2.5 |
| **DV1b** (PR 2) | `vcheck`/`vaudit`/`specfreeze` both languages; per-layer crates; check units; `firsttry`, `pins.py` | 2.5 |
| **DV1c** (PR 3) | G/V corpora; core CI. **Accepted when** a study session is denied a reference read, build and import, a solo-tree heredoc, a `~/.claude/projects` read, a stray `opencode`, and a `docker`/`lxc` call | 2.5 |
| **DV2** | L1–L2, Q01–Q03 (reference → hollow → chapter → kit → simulation), zero leak hits | 4.0 |
| **= Release A** | **you start Q01** | **14.5** |
| DV3a / DV3b | Q04–Q06 + L3 (B1) / Q07–Q09 + L4 (B2) | 4.0 / 4.0 |
| DV4 (∥ DV3) | Python adapter, `fvh` core, sandbox entry point, proxy, verification container, `harness` CI (before Q06; sandbox before Q07) | 5.0 |
| DV5 → C1–C3 | gated spikes; Q10–Q18 + L5–L7; lab templates, hidden ground truth, reference runs, research rubric | 14.0 |
| DV6 | vivas, ≥3 gold transcripts, dry run (spread over B1–C3) | 2.5 |
| DV7 (lazy) | Q19–Q33 per topic: agentic first (≈6.5), then numerics | 26 |
| DVR0 | regex layers A1–A5; spikes (R06 `Star`, R11 arena, R16 VM); `avoid.sh` baseline | 2.0 |
| DVR1 / 2 / 3 | R01–R06 / R07–R11 / R12–R16 (+ `fvh_r`, Rust gate, three lab references with runs) | 9.0 / 8.0 / 11.5 |
| DVR4 | R simulations, dry run | 1.5 |

**Totals:** infra + spikes 15.5 (13–18); Q core 28.5 (24–34); Q challenges 26 (21–34); R 32 (27–38). **≈102 MU (≈85–124); ≈142 with Lean Q.**

**Maintenance**, 4–6 MU a year (up to 2 Verus bumps at ≈2–2.5 MU, Dafny's next breaking release ≈2.5, re-par runs), is charged at ≈0.08 MU/week from Release A.

**Rules.** The infra lane owns `MODULES.toml`, CI, the hook and `scripts/`; other lanes send patches. Pace: authoring aims to stay a tier ahead; when it cannot (§15.4) you wait or fill with prework or Lean R, and no tier ships before its references, kit and simulation are complete. The Lean port copies language-free scripts; adapts the hook, checker, CORE and skills; rewrites `firsttry`, `pins.py`, wrappers, CI and `review-code`; drops `.mcp.json`.

### 15.3 Quota model and milestones [A]

**Supply.** 1.5/2.0/2.5 MU per account-week (low/mid/high); with two accounts and a **25% study reserve (20–30%)**, authoring gets **2.25/3.0/3.75 MU/week**. The reserve covers instructor sessions, Lean R study and the labs' ≤≈1,700 Claude calls; one measured study week calibrates it.

**Simulation.** A week-by-week model of both lanes and your study: this course's share goes to Release A first, then 75% Q / 25% R minus maintenance, then 100% here once Lean Q is done, then the D2 order after the Q core. Q-core finish differs by ≤1 week across D1's options. Milestones under the D1/D2 defaults (30/70, agentic first):

| milestone | low | mid | high |
|---|---|---|---|
| **Release A** (14.5 MU) | Mar 2 2027 | Jan 24 2027 | Jan 1 2027 |
| Lean Q finished | Mar 29 2027 | Feb 13 2027 | Jan 17 2027 |
| Q core shipped | Jul 27 2027 | May 13 2027 | Mar 29 2027 |
| agentic topic shipped | Aug 17 2027 | May 29 2027 | Apr 10 2027 |
| R core shipped | Oct 28 2027 | Jul 21 2027 | May 23 2027 |
| all ≈142 MU | ≈ Dec 2027 | ≈ Sep 2027 | ≈ Jun 2027 |

### 15.4 Can authoring keep up with 7 h/week?

**Not until Lean Q is done.** At 7 h/week you consume ≈2.5 MU/week of Q content. Before Lean Q is done the Q lane produces 0.7–1.3 MU/week (mid, by split), ≈2–3.5 h/week; afterwards ≈2.2 MU/week (1.6–2.7), so 7 h/week holds from ≈ mid-April 2027 (mid case; ≈5 h/week in the low case). R cannot fill the early gaps, because under Q-first it ships only after the Q core; prework P1 and Lean R fill them. After the cores this reverses: the challenges cost 26 MU for 675–1,165 learner-hours.

### 15.5 Learner calendar (7 h/week; D1/D2 defaults; mid, low–high) [A]

| stage | hours | when |
|---|---|---|
| prework P0 (+ optional P1) | 1.5 (+15–20) | from today |
| P0 + Q01–Q03 | 13.9 cumulative | ≈ Feb 6 2027 (Jan 15 – Mar 16) |
| through Q09 | 41.9 cumulative | ≈ Apr 7 2027 (Mar 6 – Jun 4) |
| research-ready minimum (through Q12) | 58.0 cumulative | ≈ Apr 26 2027 (Mar 22 – Jun 30) |
| Q core | 93.3 cumulative | ≈ Jun 1 2027 (Apr 26 – Aug 13) |
| agentic topic Q31–Q33 | +135–215 | ≈ Nov 2027 (Oct 2027 – Feb 2028) |
| R core | +124.9 (≈119 with Q-credit) | ≈ Mar 2028 (Feb – Jun 2028); ≈ Oct 2027 under "R core first" |
| everything, all fifteen challenges | ≈895–1,385 total | ≈2.5–3.8 years; the challenges are a menu |


## 16. Risks

| risk | mitigation |
|---|---|
| Quota below plan; Lean Q grows | the one number; DV0 measures MU/week; 25% reserve; prework and Lean R fill gaps |
| Accidental exposure through Claude Code state or local agents; credentials in containers | deny rules and rules 1e/1f (tripwires); clear authoring scratch; author notes outside learner memory; D6 safeguards (read-only mount, Anthropic-only egress, secret scan, rotation); optional H1/H2 |
| Three syntaxes at once; pairs cost more | false-friends card; per-language availability and floors; calibrate on Q01–Q02 |
| Renamed copies within or across courses | symmetric `avoid.sh` with cross-course list; owner tags; frozen stats; regex artifact; stated waivers |
| Later layers used as answers | one crate per layer; dependency check; specimen |
| Sandbox or Dafny units infeasible | DV0 probes; fallbacks: policy mode only, per-(track, tier) projects |
| Proofs too hard, or SMT closes them unaided | spikes with fallbacks; empty-body gate; `{:induction false}`, `opaque`, low fuel |
| Weak experiments; local models near zero on Verus | MDE arithmetic; paired Qwen tests; per-model strata; pinned apparatus |
| Labs crowd out core skills | D8; grading on method, not numbers |
