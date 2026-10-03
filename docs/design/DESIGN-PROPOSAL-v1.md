# dafny-verus-learn-0 - design proposal (draft for decisions)

*This is the design stage, and nothing has been authored yet. The target repo is `/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0`. Section, OD, TC and G/V/X ids refer to `spec4dafny-verus.md`. Tags used below:*
- *[verify]: probe or re-read before anything ships;*
- *[A]: an assumption to calibrate;*
- *"probed 2026-10-03": checked on this host during design.*

*All toolchain pins and behaviours come from the spec's research (2026-10-02), and DV0 re-probes every one of them.*

## 1. Summary

The course is one repo with one depth-ordered track. It teaches Dafny and Verus comparatively, and it aims at research in agentic formal verification. It has five parts:

- **F00 setup prework:** toolchains from pins, plus self-tests.
- **Concept tiers F01–F09:** one survey, two intro, three moderate and three detailed modules. Each tier partitions 13 strands.
- **Practice tier F10–F12:** three pre-registered research labs, one problem family each.
- **Challenge menu F13–F17:** you complete one as the capstone.

The two languages are **staggered**. Through the intro tier, Dafny carries the hand-written (WRITE) items, and Verus appears only as Rosetta cards, divergence cards and cross-language predicts. From F04 on, Verus leads exec code, loops, proof statements, ownership and modes, and it dominates the labs.

Three artifacts run through the course: `BigNat` (the verified-object spine), `fvh` (your agent and evaluation harness) and `bench/local` (a held-out task stratum).

The spec's invariant design is kept: the verifier as grader of record under the asymmetric referee (§6.5), the four guard layers, the contractor ladder, solutions-first authoring, never inventing output, and pinning everything. New: a research layer (paper cards, pre-registration, `EVAL.md`), per-run Docker containers for tool-using agents, and authoring state isolated outside the repo.

| aspect | design |
|---|---|
| languages | Dafny 4.11.0 + Verus `0.2026.09.27.3cf1832`, one repo, staggered lead/shadow (D1) |
| shape | F00 → F01 → F02–F03 → F04–F06 → F07–F09 → labs F10–F12 → one of F13–F17 (D2) |
| learner time | ≈84 h core + 25–35 h capstone ≈ 115 h. The research-ready minimum (F00–F06 + F10) is ≈44.5 h (D0, D3) |
| authoring | ≈34 MU. You start F00 after Release A (≈11 MU). Subscription quota binds, not hours (D4) |
| model access | Claude subscription CLI: interactive `/contract`, plus headless `claude -p` with all tools off. opencode + Ollama. Tool-using agents run only in per-run containers. CI never calls a model (D6) |
| research core | F10: proof completion and matched-compute search. F11: spec quality. F12: gates at crate scale (D5) |

**Two findings that affect lean-learn-0 today:**
1. **Claude Code state.** Claude Code keeps session transcripts, file-edit backups and scratch clones under `~/.claude/` and `/tmp/claude-1000/`, under your own user (probed 2026-10-03: names only, no contents read). The Lean authoring sessions' copies live there too. They sit outside every path the four guard layers cover, so none of the layers blocks a study-mode session from reading them; at most a permission prompt does.
2. **The `local-assistant` skill.** It starts opencode with file tools in the current directory. opencode ignores `.claude/settings.json`, so the guard does not apply to it.

This design fixes both for the new course (N1, and guard rules 1e and 1f in §10.2). I recommend applying the same fixes to lean-learn-0 before more Q authoring.

## 2. Decisions needed

Ask these in the order listed. Each has a recommended default.

| id | question | recommended default | impact |
|---|---|---|---|
| D0 | How many hours per week can go to this course, and what is your target date for "research-ready"? | 4–6 h/week (planning assumption) | shapes everything |
| D1 | How should the course carry two languages, given OD1's one-language advice? | Staggered comparative | shapes everything |
| D4 | How do this course and its quota share sit against Lean R study and Lean Q authoring? | Finish in-flight QA1/QA2, pause QA3–QA7 until Release B ships; keep studying Lean R | shapes everything |
| D3 | How large should the course be? | Standard, with a go/no-go after F10 | shapes everything |
| D2 | Which track shape? | Depth-ordered + research labs | major |
| D6 | Which model engines, within your no-billing rule? | Three engines, Docker sandbox | major |
| D5 | Which research families get core lab time? | Trust-first balanced, plus a matched-compute search comparison in F10 | major |

**Calendar.** Weeks = learner hours ÷ hours per week available to *this* course. Agent wall-clock time is excluded.

| milestone | hours | 3 h/wk | 5 h/wk | 8 h/wk |
|---|---|---|---|---|
| intro tier done (F00–F03) | 17 | 6 wk | 3.5 wk | 2 wk |
| research-ready minimum (F00–F06 + F10) | 44.5 | 15 wk | 9 wk | 6 wk |
| core (F00–F12) | 84 | 28 wk | 17 wk | 11 wk |
| core + capstone | ≈115 | 38 wk | 23 wk | 14 wk |

Your observed pace is about 4 Lean R modules in 9 weeks. That suggests Lean R alone already uses most of your current study time, and R05–R16 at one module every 3 weeks would take about 36 weeks. Under D4's default, this course gets what is left. We calibrate on F01 before committing Release B.

## 3. Assumed defaults (veto if you disagree)

**Non-negotiable (safety).** These are listed so you can see them, not asked:
- **N1. Isolated authoring account.** All authoring runs as a separate Unix user (for example `dvauthor`), with its own `~/.claude`, `CLAUDE_CONFIG_DIR` and `TMPDIR`, all mode 0700. File permissions then make transcripts, file-history and scratch clones unreadable to your study sessions. The deny rules and hook rule 1e are only defence in depth. Whether one subscription login works in two config directories is [verify].
- **N2. Agent output never runs on the host.** Agent-mode work runs in per-run containers. Returned files are filtered, then re-verified in a second container with no network (§10.3).

**Ordinary defaults:**

| id | default | note |
|---|---|---|
| D7 training / RL | Only as optional challenge F16; the core has a reward audit without training (F11) | GPU contention; F16 needs Hugging Face weights, not Ollama GGUF [verify] |
| D8 instructor scope | All skills; about 8 bilingual questions per bank; 4 tier vivas + a capstone defense; LaTeX only where it pays | Lean banks + rubrics outweighed the chapters (131k vs 105k words) |
| D9 capstone | Menu F13–F17; default F14, a stage-wise bilingual mini-benchmark | Claims only the stage-wise, bilingual, held-out angle against AlgoVeri, VeriContest, Verus-SpecBench [verify]; a gated mini-CryptoProver would overlap F12 |
| D10 pins | One course pin per language, at most 2 bumps a year. A benchmark's own pin runs only inside a sandbox, for an exact-setup replication | OD5 settles the pin form |
| D11 spine | BigNat limb numeral. Its scope is set by the DV0 admissibility spike. Named fallback: L4 = multiply by a single limb, with full multiply moved to a challenge | |
| D12 visibility | Private remote; `bench/local` in the repo; `Hidden/` encrypted (OD14); CI on a self-hosted runner under a separate user with no model credentials | Held-out tasks on GitHub would contaminate future models; private Actions minutes are limited [verify]. Publishing F14 is a later decision |
| D13 sharing with Lean | Fork and adapt; per-repo ledger | Extract a shared kit later |
| exits | Every concept module has a closed-book exit (§2.4.1), not only tier modules | ≈20 min each, budgeted |
| spec ODs | ids F00–F17 frozen before the first commit; OD3, OD6, OD7 (`vcheck` CLI, no MCP), OD8, OD12, OD13, OD16 (`leobwang-*`), OD17; `--target py` unless the IDE probe forces .NET [verify] | |
| budgets | Per lab: ≤200 headless Claude calls (one final arm) and ≤10 GPU-h of Qwen. Capstone: ≤400 calls [A; calibrate on F10] | §8 |

## 4. Goals and exit competencies

The three goals of §1.1, re-aimed at research:

1. **Hand fluency in both verifiers, good enough to judge an agent,** on the failure classes agents hit: DafnyPro's tactic classes; the AutoVerus residuals (overflow bounds, vstd knowledge, quantifiers); inductive invariants; specs that are neither too weak nor leaky. Programming stays first-class: a `bignat` CLI in both languages (F07), a Rust binary (F12), and `fvh` as a tested Python codebase.
2. **The verifier as an environment:** the VC pipeline down to Z3 and erasure; JSON, exit codes, filters and resource limits; the three verdict kinds (TC10); brittleness and the TCB. You should know exactly what a `dafny verify` or `verus` reward certifies, and every way it can lie.
3. **Agentic verification as experimental science:** specify and audit contractors; build harnesses, gates and spec oracles; pre-register matched-budget experiments with variance, cost and contamination controls on subscription and local models; frame an open problem.

| # | you can… | measured by (core home) | anchors |
|---|---|---|---|
| E1 | close unseen proof items by hand | closed-book exits: Dafny at F03/F06/F09, Verus at F06/F09; F10 hand part ≥3/4 per language on course-local items from the named failure classes | DafnyBench, DafnyPro, AutoVerus, VeruSAGE |
| E2 | triage a failure (false / not inductive / needs a hint / trigger gap / resource limit) and say what each verdict licenses | predicts F01–F06; F06 exit | foundations §2.11; Mariposa |
| E3 | write a spec from prose with a satisfiability witness, a mutant-kill score ≥ a pinned threshold [A], and a proof that it is ⊇ or ≡ a reference; spot the planted weak spec among five | F11 | Lahiri; Clover; VERINA; vericoding audit |
| E4 | diagnose ≥10 fake greens across the G and V catalogs, caught by N distinct instruments, with zero false accusations | F09 forensic file | CryptoProver audit; AlphaVerus |
| E5 | ship a gate that rejects every decidable cheat in a ≥40-specimen corpus (build-tool poisoning included) plus your own; answers UNKNOWN, never PASS, on grader-only classes; agrees with `vaudit`/`specfreeze`; has a measured FP rate | F06 → F09 → F12 | CryptoProver gates; Lynette; CAPRI |
| E6 | build spec-quality oracles (subset implication, soundness/completeness, spectests, mutation) | F11 | Re:Form; SpecRL; Lahiri |
| E7 | report results cleanly: `EVAL.md` plus a disclosure block with unbiased pass@k/SR_n and CIs, paired tests, timeout = failure, clean-checkout re-verification, a contamination statement, cost (calls, tokens, GPU-s) and apparatus versions | F06, F09, every lab | Mariposa; DafnyBench metric hazards |
| E8 | measure proof stability; repair a fragile or solver-sensitive proof without weakening it | F09 | Mariposa; CryptoProver App. D |
| E9 | port a verified Dafny module to Verus with a fidelity audit (§5.4) | F07 | AlphaVerus; vericoding BigNum weakening |
| E10 | run a pre-registered, small-scale replication with model substitution that reproduces from its logs | F10, F11, F12 | DafnyBench; VeruSAGE; Baldur |
| E11 | frame and defend research: a 1-page proposal; a capstone with a benchmark card and `TRUST.md` | F12, capstone | VERINA; AlgoVeri |
| E12 | compare independent sampling, sequential feedback and best-first search at matched compute, with paired statistics | F10 (Qwen only) | AlphaVerus/REBASE; VerMCTS; Baldur |

**Coverage rule** (§2.3.4), keyed by competency. Every E has a core home, and F13–F17 are deepening only. Two gaps are recorded, both for lack of hours: protocol and state-machine invariants (lit topic 07), and data engines (SAFE, APRIL), are deepening only.

**Threshold concepts.** TC1–TC14 (§11.2.3) are kept, plus five research concepts, each scheduled glimpsed → operated → mechanism:

| id | concept | schedule |
|---|---|---|
| R1 | Verified is not correct; the spec is the attack surface | F01 → F03 → F11 |
| R2 | A score without an exploit audit is an upper bound | F03 → F06 → F10 |
| R3 | Rules without gates are only suggestions | F03 → F09 → F12 |
| R4 | Scaffolding must match model strength | F04 → F10 → F12 |
| R5 | A small-n result needs pre-registration, variance and cost | F03 → F06 → F10 |

## 5. Language strategy

### 5.1 Why both, against OD1

OD1's reason ("the guard, harness and pins are language-specific; mixing doubles them") holds for content, not for infrastructure. The Lean inventory has about 3k language-specific lines out of about 9.5k, and Dafny and Rust share `//` comments. One item parser, one hook with per-language tables and one CLI (`vcheck|vaudit|specfreeze --lang`) therefore cost only about 1.5–2k extra lines.

The research case for both: vericoding's union success rate is 82.2% in Dafny vs 44.3% in Verus; AlphaVerus bootstraps Verus from Dafny; and the industrial frontier (VeruSAGE, CryptoProver) is in Verus. A harness that speaks one verifier cannot study that gap. The honest third language is Python: `fvh` has its own holes, reference twin and side channels (§10.2), budgeted at +1 MU.

### 5.2 Staggered lead/shadow

- **Lead and shadow.** Every strand × module cell has a **lead** and a **shadow**.
  - The lead carries the WRITE items, with ≥2 checked uses per construct *within the module*, which is the checker's rule.
  - The shadow carries RECOGNISE cards and, from F04 on, one port item. It also carries one divergence card (`diverge:<slug>`), with both behaviours captured on the pins.
- **F01–F03: Dafny leads everything.** Verus is RECOGNISE only: a Rosetta card, divergence cards, and cross-language predicts ("D: verified, V: error@line"). This keeps two proof syntaxes in flight (Lean and Dafny), not three.
- **From F04: Verus leads** S1, S3, S4 and S5 in F04 (exec code, proof blocks, loops/invariants/overflow, vstd); ownership (S6) and modes (S7) in F05; tracked permissions in F08; all of F07 and F12.
- **Dafny leads** S2 in F04; ghost and subset types (S7) and S8 in F05; S11 in F06; refinement (S6) and S8 in F08; and F11.
- **Hours** split about 35% Dafny-led, 40% Verus-led and 25% neutral or harness work [A].

| taught… | content |
|---|---|
| once (neutral, two-column code) | Hoare/wp/VC (foundations §2.1–2.3); invariants as induction hypotheses; termination; triggers; verdict asymmetry; TCB; vacuity; spec metrics; evaluation; gate design |
| twice (lead WRITE, shadow port) | holes and counters; `assert … by`, `calc`, `decreases`; quantifiers; `opaque`/`reveal`; audit; statement freeze; Std vs vstd; G/V catalogs |
| divergence cards | loud vs silent holes; `int` vs machine overflow; frames vs ownership; auto-induction; fuel; V20; V9; G9; legacy CLI; churn |
| one language only | Verus: modes, `Ghost`/`Tracked`, views, `broadcast use`, `nonlinear_arith`/`bit_vector`, crate gating. Dafny: `{:induction false}`, refinement modules, `function by method`, compile targets |

### 5.3 Course pins vs research pins

- **Course content** uses exactly one pin per language, and goldens never mix pins.
- **Labs prefer pools that already validate on the course pins:**
  - the LemmaScript Dafny benchmark (MIT, 28 tasks, 4.11.0) [verify];
  - MINIF2F-DAFNY (MIT, 4.11.0) [verify];
  - HumanEval-Verus, re-validated on our pin [verify];
  - DafnyBench and vericoding subsets, re-validated on 4.11.0.
- **Exact-setup replications** may use a benchmark's own pin, for example VeruSAGE `ddc6611` or Laurel's Dafny 4.3.0 [verify]. They run only in a sandbox, with a `VERSIONS.md` row.
- **Strata are picked per model, from a pilot.** Verus-Bench and CloverBench are saturated for frontier agents but probably not for `qwen3.8` (17 GB). DafnyBench is near the ceiling for Claude (Claude 3 Opus 67.8%; no-hint floor 26.9%) and may sit near the floor for small Qwen.
- **The gate takes a per-benchmark trust allowlist**, because miniF2F-Dafny axiomatizes its definitions [verify].

### 5.4 Cross-language fidelity

No verifier sees a Dafny spec and a Verus spec together. Fidelity "by implication lemma" alone is therefore circular: the source spec must first be transcribed, and the transcription is the translation being audited. The instrument has two parts:
- **(a) Differential execution** on shared test vectors: Dafny `--target py` vs Verus `--compile`, plus parity of mutant-kill scores.
- **(b) An independently transcribed mirror** of the source spec, statement-reviewed, with implication lemmas inside the target language, labelled "relative to the mirror".

Cross-verifier fidelity is taught as an open problem (vericoding's BigNum weakening; AlphaVerus mistranslations).

## 6. Structure

### 6.1 Strands and families

These are §11.2's S1–S12, merged across both languages, plus S13. Families are balanced by material new to you (§2.3.2), and are re-measured after F01.

| family | strands (Dafny / Verus anchors as in §11.2) |
|---|---|
| A | S1 data & programs (overflow on the Verus side); S2 specs & logic; S3 proof statements & feedback; S4 induction, recursion, loops; S5 libraries & retrieval (Std / vstd) |
| B | S6 abstraction & effects (refinement, frames / traits, ownership); S7 ghost/modes, erasure, termination; S8 program-logic foundations (wp/VC, a small verified wp / tracked permissions); S9 interfaces & tooling (`--json-output` [verify schema] / `--output-json`) |
| C | S10 pipeline & TCB; S11 SMT mechanics & brittleness; S12 verifier loop, trust & agents (G/V catalogs, gates); **S13 evaluation & spec quality** (pass@k/SR_n, CIs, paired tests, contamination, spec metrics, `verus-spec-check` [verify]) |

### 6.2 Modules

Hours are learner hours, and agent wall-clock time is excluded (§2.5). Each module has at most 5 graded deliverables besides its exit and viva. Every concept module ends with a closed-book exit (thresholds: survey ≥10/13, intro ≥5/6, moderate/detailed ≥3/4) and a 15-minute task card for `bench/local`.

| id | tier | title | lead | graded deliverables | agent role | paper card | h |
|---|---|---|---|---|---|---|---|
| F00 | prework | Setup | — | toolchains from pins; `vcheck`/`vaudit`/`fvh` self-tests (ungraded checklist) | — | — | 1.5 |
| F01 | survey, S1–S13 | One spec, two verifiers | Dafny; Verus RECOGNISE | 6 survey holes (`SumUpTo`, hole contract both ways, verdict kinds); repairer audit; three-door demo; exit map | repairer (one Dafny file, one stage) | Clover; topic map | 5.0 |
| F02 | intro, S1–S6 | Programs, specs, proofs | Dafny | 10 holes (contracts, assert/calc, invariants, spine L1–L2); adversarial checks + latency log; exit | implementer vs checks | DafnyPro | 5.0 |
| F03 | intro, S7–S13, viva | Modes, logic, trust | Dafny; Verus cards | 6 holes (ghost, termination); wp by hand (LaTeX); contract v0; exit + viva | contract v0 by hand (`/contract F03` refuses) | vericoding | 5.5 |
| F04 | moderate A, S1–S5 | Loops, arithmetic, libraries | Verus S1/S3/S4/S5; Dafny S2 | 10 holes + 1 port (overflow, invariants, spine L3); library + mismatch lab; retriever audit; exit | retriever race vs interactive Claude | AutoVerus; Laurel | 5.5 |
| F05 | moderate B, S6–S9 | Frames vs ownership; statement freeze | Verus S6/S7; Dafny S7/S8 | 9 holes + 1 port; wp→VC hand calculation; `specfreeze` both ways; audited-prover audit; exit | audited prover (≤5 leaves) | Lemur; Lynette | 5.5 |
| F06 | moderate C, S10–S13, viva | Trust, triggers, metrics | Dafny S11; both S10/S12 | 6 trigger/opaque/rlimit holes; statistics + `EVAL.md` v0 + `TRUST.md` v0; gate v0 (solo); toolwright audit; exit + viva | toolwright (counter to your interface spec) | VeruSAGE checker ablation (cheating ≤14% → <1.5%) | 6.0 |
| F07 | detailed A, S1–S5 | Proof engineering & translation | Verus | 6 holes (decomposition, opaque, `bit_vector`, `nonlinear_arith`, spine L4); Dafny→Verus module port + fidelity audit + `bignat` CLI; spec-to-proof audit; exit | spec-to-proof (flagship); Qwen arm in sandbox | AlphaVerus | 6.0 |
| F08 | detailed B, S6–S9 | Refinement, permissions, the machine door | Dafny S6/S8; Verus S7 | 6 holes (refinement as freeze, tracked permissions); verified wp for assign/seq/if (loops stay on paper); JSON + a 20-line policy (Mock, Qwen); refactorer audit; exit | refactorer under harness | CertiCoq ANF; CAPRI | 6.0 |
| F09 | detailed C, S10–S13, viva | Brittleness & forensics | both | flake meter + repair under a solver swap (Z3 4.12.1 → 4.14.1, both bundled [verify]); forensic file; gate v1 + FP/FN; red-team → contract v1; headline memo + `EVAL.md` v1; exit + viva | red-teamed contractor | Mariposa; CryptoProver audit (prompt-only: 97.1% claimed, 11 fabricated axioms) | 6.5 |
| F10 | lab A | Proof completion & search | both | hand problems (4 + 4); pre-registration; policies (incl. best-first, dense score) + `fvh report`; experiment report (one Claude arm + Qwen matched-compute arms, successes re-judged by your gate); 2 task cards | benchmarked subject (policy mode) | DafnyBench; Baldur | 10.5 |
| F11 | lab B | Specs & vericoding | Dafny → Verus | specs from prose + graded blueprint; 2 oracles (mutation, subset implication); role-reversal experiment + reward audit (no training); `bench/local` oracle audit; 2 task cards | role reversal: agent writes specs, you score | Re:Form; SpecRL; Clover | 10 |
| F12 | lab C, viva | Gates, not rules | Verus | statements + blueprint for a spine mini-crate; capstone round (§5.5) + shipped binary; gated vs prompt-only agent-mode case study; seven gates + `TRUST.md` + contract v2; 1-page proposal | reviewer → co-developer → adversary | CryptoProver; VeruSAGE | 11 |

### 6.3 Minute reconciliation (§2.5 MUST)

Each line sums to its module total.

| id | minutes | total |
|---|---|---|
| F00 | toolchains + sha check 25, IDE pins 15, `vcheck`/`vaudit` self-test 15, `uv sync` + `fvh` self-test 10, Ollama digests + GPU calendar 10, readiness checklist 15 | 90 |
| F01 | setup 10, read 40, worked 30, Rosetta/divergence cards 20, predicts 20, holes 24, Verus RECOGNISE runs 10, repairer 25, three doors 20, paper card 30, task card 15, exit 30, verdict JSON 15, calib 11 | 300 |
| F02 | setup 10, pretest 10, read 40, worked 35, cards 15, predicts 18, holes 40, agent 30, paper 30, task 15, exit 25, spine tour 20, calib 12 | 300 |
| F03 | setup 10, pretest 10, read 35, worked 25, cards 15, predicts 18, holes 24, wp on paper 35, first fake greens 20, contract v0 30, paper 30, task 15, exit 25, viva 30, calib 8 | 330 |
| F04 | setup 10, pretest 10, read 40, worked 30, predicts 15, Verus holes 42, Dafny holes 18, port 10, library lab 20, search ladder 15, agent 30, paper 30, task 15, exit 20, spine L3 15, calib 10 | 330 |
| F05 | setup 10, pretest 10, read 40, worked 30, predicts 15, Verus holes 30, Dafny holes 24, port 10, wp→VC 30, specfreeze 15, fast-channel latency 10, agent 30, paper 30, task 15, exit 20, calib 11 | 330 |
| F06 | setup 10, pretest 10, read 35, worked 20, predicts 15, holes 36, specimens + vacuity 15, TCB/TRUST v0 10, statistics 35, EVAL v0 15, gate v0 45, agent 20, paper 20, task 15, exit 20, viva 30, calib 9 | 360 |
| F07 | setup 10, pretest 10, read 40, worked 35, predicts 15, holes 48, port + audit + CLI 85, agent 35, paper 30, task 15, exit + explain-back 25, calib 12 | 360 |
| F08 | setup 10, pretest 10, read 45, worked 36, predicts 15, holes 48, verified wp 26, JSON 15, policy 45, agent 30, paper 30, task 15, exit + explain-back 25, calib 10 | 360 |
| F09 | setup 10, pretest 10, read 40, worked 20, predicts 15, brittleness + repair 45, forensics 60, gate v1 45, red-team + v1 35, memo + EVAL v1 35, task 15, exit 20, viva 30, calib 10 | 390 |
| F10 | brief 15, hand problems 150, pre-registration 60, `/grade-paper` pre 15, policies + report 120, run setup 30, analysis 90, transcript audit 30, `--post` 20, `/review-code` 20, paper 35, task cards 30, calib 15 | 630 |
| F11 | brief 15, specs from prose 150, blueprint grade 15, pre-registration 45, oracles 90, run setup 25, analysis 90, reward audit 15, bench audit 40, `--post` 15, `/review-code` 20, paper 35, task cards 30, calib 15 | 600 |
| F12 | brief 15, statements + blueprint 90, blueprint grade 15, capstone round + binary 120, gated vs prompt-only (pre-registration, setup, analysis) 110, gate suite 90, TRUST + v2 45, binary packaging 30, proposal 60, `/review-code` 20, viva 30, paper 25, calib 10 | 660 |

Totals:
- concept tiers including F00: 3,150 min = 52.5 h;
- labs: 1,890 min = 31.5 h;
- **core: 84 h.**

Test-out (T items on Hoare/wp/induction theory, which transfers from `foundations.md` but not as syntax) saves 1–2 h in F02–F03.

### 6.4 Challenge menu (one required as the capstone)

Every challenge is solo; the gate is `challenge_gate.sh` or a harness with hidden par runs (§2.3.8); a graded pre-registration opens it, and a defense viva closes it.

| id | topic | lang | h |
|---|---|---|---|
| F13 | **Hands-off agents on real Verus:** a 20–30-task VeruSAGE slice, with and without the checker; warm-up on CryptoProver's chacha20 | Verus | 25–30 |
| F14 | **Stage-wise bilingual mini-benchmark (default):** 20–30 spec/code/proof/end-to-end tasks from audited `bench/local`, a red-teamed grader, a benchmark card positioned against AlgoVeri, VeriContest and Verus-SpecBench. A pilot, not a gap-filler | both | 30–35 |
| F15 | **Verifier-guided search:** VerMCTS on Verus, or AlphaVerus-lite (REBASE, critique on/off) | both | 25 |
| F16 | **Verifier reward on one GPU:** scaled Re:Form GRPO (0.5–1.5B) or a repair LoRA | Dafny | 30–40 |
| F17 | **Interface research:** obligation-level tool ablation, or code-proof co-design | either | 20–25 |

Optional extras, with no budget:
- the full verified VC generator with loops;
- a Verus bump lab (proof repair under toolchain change), run when a scheduled bump lands;
- protocol state machines.

### 6.5 The module loop

```
paper card (re-read your cheatsheet card) → chapter (≤5k words; theory links foundations.md)
→ pretest/T items → W/C/P/H items (lead, then port) → specimens & predicts (first try recorded)
→ /contract (fresh) → exit → [tier: /viva]
→ [labs] prereg paper/<ID>_prereg.tex → /grade-paper (fresh, ≥3 on every dimension unlocks the run)
   → harness increment (pytest + lint) → run (unattended) → fvh report from logs
   → /grade-paper --post → /review-code (fresh) → [/viva]
→ Solutions/ last → /review when due
```

## 7. Running artifacts

1. **`BigNat`, the object spine.** A little-endian limb numeral with an abstraction function:
   - Dafny: `seq<nat>` with a ghost `ToNat`.
   - Verus: exec `Vec<u64>` with a `Seq` view and overflow obligations.

   Layers L1–L5 are frozen, given and re-supplied (§2.6). Dafny exercise files import only `given/`. The DV0 spike proves L3–L4 in both languages before any chapter is written. The spine seeds the `bignat` CLI (F07) and the F12 mini-crate.
2. **`fvh`, the tool spine.** A Python (uv) package behind a frozen interface: the policy protocol `propose(state, ctx, budget) -> [Action]`, typed records, backends (Mock, Scripted, Replay, `claude -p`, opencode), budgets, fetchers, the sandbox client and the public cheat corpus. **It ships complete except four learner-written parts:** `gate/` (solo; rule 2s), the policies (F08, F10), `report` (F10) and two spec oracles (F11). That keeps the Python hollowing small. Holes are `raise Hole("F06.H2")`, counted statically by an AST counter (a tool, not grep). The reference lives in `Solutions/harness/` as its own uv project, never a workspace member, with a grader-only cheat corpus on which your gate must answer UNKNOWN.
3. **`bench/local`, the held-out stratum.** Every module ends with a task card in its lead language: statement, stripped version, your solution, satisfiability witness, negative tests. Solutions and ground truth go in `bench/*/answers/`, which sandboxes never copy; about 30 tasks exist by F12. Contamination control has four parts: authorship after the models' training cutoffs; a semantic-novelty review (BigNat ops are semantically everywhere, whatever they are named); AutoSpec-style perturbation probes; and in-context isolation (§10.3). The repurposed `avoid.sh` catches only lexical overlap with public benchmarks. Every task passes the F11 oracles before it enters F14, because novice cards from F01–F03 will often have weak specs.
4. **Trust documents.**
   - `TRUST.md`: v0 at F06, final at F12.
   - `EVAL.md`: v0 at F06, v1 at F09, binding on every lab.
   - Contracts v0/v1/v2 in CLAUDE.md, below the learner marker.

## 8. Research layer

- **Reading track.** One paper card per module, graded by `/grade-paper` against line ranges in `cheatsheets.md` and `lit-rev/NN-*.md`. Fixed fields: task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact.
- **Pre-registration** replaces the blueprint gate for experiments. It holds the claim (quoted), metric and estimator, the **budget arithmetic** (calls = tasks × attempts × feedback rounds × arms × repeats; tokens; GPU-h), the **minimum detectable effect** at that n, cheat surface and gate, prediction intervals and a stopping rule. `firsttry` records the intervals. `fvh` refuses a "registered" run unless the pre-registration is committed and its hash is recorded.
- **Design under the quota.**
  - Each lab has **one pre-registered final arm on Claude, on ≤20 tasks** (for example 20 tasks × 3 attempts × ≤3 rounds = ≤180 calls). It is reported descriptively, with CIs of about ±20 pp at that n, against the paper's figure.
  - Every multi-arm comparison runs on Qwen through Ollama, which accepts real seeds and temperature, with more tasks and samples.
  - Claude repeats are labelled "repeated runs", never "seeds", because the CLI exposes neither.
  - F06 teaches paired designs (McNemar, paired bootstrap over tasks), MDE and Holm correction.
- **Acceptance is artifact-based.** All three must hold:
  1. `fvh report` reproduces every table from the logs.
  2. Your gate passes every claimed success when re-run from a clean checkout in the verification container.
  3. The disclosure block is present: runs, repeats, selection rule, agent context, cost, apparatus versions.

  Reference runs are stored as evidence in `Solutions/runs/`. **Grading is on method and reproducibility, never on matching numbers.**
- **Grader independence.** `/grade-paper`, which is Claude, scores method dimensions only: hypothesis precision, budget parity, variance, contamination, cheat audit, disclosure. Harness code computes every outcome metric. Reports disclose that Claude is both grader and subject.
- **Benchmarks.** `scripts/get_bench.sh` fetches against a manifest (repo, commit, sha256, licence, pin). Licences are [verify]:
  - **vendored subsets (MIT/Apache):** DafnyBench, vericoding, HumanEval-Verus, Verus-Bench, VeruSAGE, LemmaScript, MINIF2F-DAFNY;
  - **fetched only:** MBPP-DFY (GPL-3.0), AlphaVerus data (no licence), DafnyComp (CC-BY-NC).

  Every run is labelled "small-scale replication with model substitution".
- **Model engines** (OD15 binding: no usage-billed APIs; CI never calls a model):
  1. **Interactive `/contract`:** Claude Code in the repo, hooks armed.
  2. **Policy mode (experiments).** The harness is the only executor (X18).
     - **Claude:** `claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --output-format stream-json --verbose --json-schema <s> --model <pinned> --effort <pinned> --system-prompt <course policy prompt>`. Flags probed on Claude Code 2.1.288; `--max-turns` (in §5.6's argv) is not listed in `--help` [verify], nor is it confirmed that `--system-prompt` fully replaces the default [verify]. Calls run from an empty temporary cwd with an isolated `CLAUDE_CONFIG_DIR` holding only credentials, so no CLAUDE.md, contracts, hooks or skills load. **Never `--bare`**: its help says it authenticates only by API key or apiKeyHelper, which the no-billing rule forbids.
     - **opencode:** isolated HOME/XDG, `tools {"*": false}`, `mcp {}`.
  3. **Agent mode** (F07 Qwen arm, F12, F13): headless Claude Code or opencode with tools, only inside the per-run container of §10.3.
- **Apparatus pinning.**
  - Pin the `claude` and `opencode` binaries by sha.
  - Disable auto-update: `DISABLE_AUTOUPDATER=1` [verify] and opencode's `autoupdate: false` [verify].
  - Every JSONL record carries `claude --version`, the model id, a hash of the system prompt, the opencode version, the Ollama model digest and the sandbox manifest hash.
  - The disclosure block names Claude Code's own scaffolding as a known confound when comparing with raw-API papers.
- **Budgets and hardware.**
  - Registry fields cap calls, tokens, wall-clock and GPU-seconds per lab, with a rolling-window cap and checkpoint-and-resume, so a rate limit cannot become best-of-n.
  - One calendar covers the GPU, the 123 GB of RAM and the verifier pool (32 cores). `qwen3.8-flash-next` UD-Q4_K_XL (112 GB) needs CPU offload, and IQ4_XS (94 GB) nearly fills the 96 GB card; DV0 measures throughput and KV headroom [verify].
  - `qwen3.8` (17 GB) is the sampling workhorse. Training (F16) never co-runs with the big model.
- **Cheat corpus.**
  - **Two layers:** the trusted, CI-tested `vcheck`/`vaudit`/`specfreeze`, and your gate, which must agree with them differentially on the corpus.
  - **Contents:** G1–G22 and V1–V24, shipped as fixtures before any chapter, plus rlimit inflation, CryptoProver's fabricated-axiom shape, AlphaVerus exploit pairs (fetched), and **build-tool poisoning** (planted `build.rs`, `conftest.py`, `.cargo/config.toml`, `dfyconfig.toml` `--plugin`/`--solver-path`).
  - **The corrected legacy-CLI specimen** contrasts the new and legacy CLIs on a bodyless lemma (new: warning, exit 2; legacy: silent, exit 0 [verify on pin]), plus a harness that substring-matches "verified, 0 errors". `assume {:axiom} false` is silent in both CLIs (G1), so it is not the legacy-specific case.
  - **Rules:** timeouts and `unknown` count as failure; pin resource limits, never wall-clock limits; strip `<think>` blocks before scoring.

## 9. The agentic ladder

The contractor is an interactive `/contract` session (the agent as colleague). The subject is a headless run through `fvh` (the agent as experimental subject).

| mod | role | you specify | you audit with | engine |
|---|---|---|---|---|
| F01 | repairer + three-door demo | — | transcript tally, diff, `vaudit`; door 3 = an include/import of the reference through the `vcheck` wrapper | /contract |
| F02 | implementer vs checks | adversarial checks | latency log | /contract |
| F03 | contract v0 by hand | the rules | each rule classified by what can check it | none |
| F04 | retriever race | goals | citation check | /contract |
| F05 | audited prover | hole skeleton | `vaudit`, statement review | /contract |
| F06 | toolwright | interface spec + fixtures | the counter on the corpus | /contract |
| F07 | spec-to-proof (flagship) | statements + witnesses | swap-to-`false`, witness probes | /contract + Qwen (agent mode) |
| F08 | refactorer under harness | frozen statements | `specfreeze` | /contract |
| F09 | red-teamed contractor | a planted plausible-but-false lemma | forensics, N instruments → contract v1 | /contract |
| F10 | benchmarked subject | the bench config | your gate | policy mode |
| F11 | spec author (role reversal) | the prose | spec oracles | policy mode |
| F12 | reviewer → co-developer → adversary | statements + graded blueprint | gate suite, `TRUST.md` → contract v2 | /contract + agent mode |
| F13–F17 | you build the agents | — | grader harness | policy or agent mode |

Contracts keep exactly three keys (§3.11.2). `scripts/contract_local.sh` replays a contract under opencode in a container, and copies back only diffs to allowlisted files. Under OD13, the hook hard-denies `instructor/` writes while the allowlist is non-empty.

## 10. Instructor layer and isolation

### 10.1 Kept and trimmed

| decision | pieces |
|---|---|
| **keep** | the §0.4 core (verifier as grader, module loop, roles and access matrix, registry, solutions-first, never invent output, pins, shipped-state CI); the four guard layers and leak patterns; concept tiers, partition, coverage, tier vivas and per-module exits; predicts, first-try and the golden harness (5–8 predicts per concept module, plus experiment intervals); `/tutor`, `/review`, `/contract`, `/viva`, `/grade-paper` |
| **rewrite** | the CORE referee, for asymmetry (§6.5): a confirmed flaw needs an executable counterexample or a verified refutation; `review-lean` → `/review-code` (OD18 bars + `harness`/`production`, with a brittleness dimension) |
| **retarget or trim** | the written track becomes wp/VC work, blueprints, paper cards, pre-registrations and memos; banks shrink to about 8 questions, bilingual, with shared `concepts.md` tags; one lab tier; a 5-topic challenge menu; `/discuss` becomes optional |
| **drop** | the second track and its disjointness gate (`avoid.sh` is repurposed for contamination) |
| **fix on day one** (§12.3) | the classification vocabulary goes in CORE; a `discuss` ledger source; templates generated from CORE; the checker is authoritative; the canonical CONTRACT block only; never count holes with grep |

### 10.2 Guard changes beyond the spec

| change | what it closes |
|---|---|
| **N1 account** + deny rules `Read(~/.claude/projects/**)`, `Read(~/.claude/file-history/**)`, `Read(~/.claude/history.jsonl)`; **rule 1e** blocks `/tmp/claude-*` paths other than the session's own scratchpad (it identifies the session from the hook input [verify]) | reading reference copies from transcripts, file-edit backups or authoring scratch clones |
| **rule 1f** blocks `opencode`, `codex`, `docker` and tool-enabled nested `claude`, except via `scripts/mksandbox`, `scripts/contract_local.sh` and `fvh`; deny `Skill(local-assistant)` if supported [verify] | unguarded local agents; docker-group root equivalence |
| hook matcher adds `WebFetch\|WebSearch`; both are denied while a contract allowlist is active and in every experiment run | searching for public benchmark solutions (WebSearch runs server-side) |
| **Python row**: pytest `testpaths`/`norecursedirs` exclude Solutions, Hidden and `bench/*/answers`; `PYTHONPATH`, `sys.path`, `importlib` and `pip install -e` forms of the reference; stray `conftest.py`; the reference package name as a bare word | importing, installing or test-collecting the reference harness |
| rule 2 adds `harness/`, `bench/local/`, `tools/`; rule 2s adds `harness/gate/`; rule 2g adds `pyproject.toml`, `uv.lock`, `conftest.py`, the Dockerfiles and the proxy allowlist | a tutor writing your harness; the graded writing the grader |
| `target/` sits under rule 1d (reach), not 2g; the crate name `solutions` is a bare word | compiled reference output |
| `bench/**/answers/**` reads are denied while a contract is active | ground truth reaching an interactive contractor |

About 230 of the 316 Lean hook fixtures carry over. About 170 are new across Dafny, Verus, Python and the rules above [A].

### 10.3 The agent sandbox (per run)

**Probed 2026-10-03:** `bwrap --unshare-net` fails (`RTM_NEWADDR: Operation not permitted`); `unshare -rn` fails writing `uid_map`; `kernel.apparmor_restrict_unprivileged_userns=1` and there is no bwrap AppArmor profile. These probes ran inside a Claude Code session [verify outside it]. Docker 29.1.3 is present, and you are in the `docker` group. The sandbox is therefore Docker:

1. **Contents.** `scripts/mksandbox <task>` materializes only that task's stripped inputs, the pinned toolchain image (by digest) and the stdlib/vstd sources. It includes no repo mount, no git history, no `Solutions/`, `Hidden/`, `bench/*/answers/`, finished exercises, `instructor/` or run logs. This follows the LemmaScript make-attempt pattern [verify].
2. **Self-test.** Before the agent starts, a scan searches the sandbox for every task's ground-truth hash and every leak pattern, and fails on any hit. The manifest hash goes into the JSONL record.
3. **Network.** Egress goes through an allowlist proxy: Anthropic endpoints for Claude runs [verify host list], host Ollama `:11434` for opencode runs, nothing else. Access is logged. Every run passes `--disallowedTools WebSearch,WebFetch` plus a settings deny.
4. **Credentials.** Only the credentials file is mounted, read-only, into an isolated `CLAUDE_CONFIG_DIR`. `~/.claude` and the Docker socket are never mounted.
5. **Return path.** Only allowlisted source files come back, diff-filtered, and any unknown file is rejected. All project files are re-materialized from trusted copies: `Cargo.toml` with `build = false` and no new dependencies, `.cargo/`, `rust-toolchain.toml`, `dfyconfig.toml`, `pyproject.toml`.
6. **Verification.** The gate runs in a second container with no network and no repo mount. Agent output never executes on the host.

## 11. Repo layout and infrastructure

```
dafny-verus-learn-0/
  MODULES.toml (lang, tier, budgets, engines)  VERSIONS.md  CLAUDE.md  README.md  PLAN.md
  course/dafny/{core,std}/dfyconfig.toml   F0x_*.dfy   given/        # core = F01–F03 (no Std); std = F04+
  course/verus/  Cargo.toml [workspace: given, course; exclude Solutions]  rust-toolchain.toml (1.98.1)
  specimens/<ID>/*.dfy.specimen|*.rs.specimen   slots/<ID>.slots   expected/<ID>.pins
  harness/  fvh (uv; tests in harness/tests)   gate/ (solo)
  bench/public/<bench>/{tasks,answers}  bench/local/{tasks,answers}     # answers/ never enter sandboxes
  sandbox/  Dockerfile.{toolchain,verify}  proxy-allowlist
  Challenges/F13..F17/  agents/  tools/<ID>/
  Solutions/{dafny (own dfyconfig), verus (own workspace), harness (own uv project), runs}
  Hidden/ (encrypted)  docs/ paper/ instructor/ scripts/ tests/{hooks,instructor,harness}/ .claude/
```

**Dafny wiring (spec §3.3 MUST).** `vcheck` builds per-module units from the registry:
- the **verify unit** is the module file plus `given/`, with that tier's options;
- the **test unit** is the same files and runs only once they are hole-free;
- **value slots** run from given-only units.

The two `dfyconfig.toml` projects (core without Std, std with it) exist for the IDE and for library tiers, which a lint also enforces. There are no `base` chains (G21). The checker verifies that units contain given files only. Probe D11 runs in DV0.

**Toolchain pins** (every cell [verify] in DV0; CI asserts versions and sha256):

| | Dafny | Verus |
|---|---|---|
| binary | 4.11.0 release zip (x64-ubuntu-22.04), sha256 `a46a9ff7…8267179`; self-contained | weekly release `0.2026.09.27.3cf1832` (never rolling); ≈486 MB zip, ≈1.6 GB unpacked |
| solver | bundled Z3 4.12.1 (default) and 4.14.1 | bundled Z3 4.16.0, version-checked |
| deps | `--standard-libraries` from F04 | Rust 1.98.1 exactly (host has 1.92.0, probed); `vstd = "=0.0.0-2026-09-20-0158"` |
| IDE | ide-vscode with `"dafny.version": "4.11.0"` | verus-analyzer with `verusBinary` pinned; verusfmt pinned |
| run | `--target py` | `verus --compile`; `cargo test` beside `verus!` (P6) |
| hazard | no nightlies (the next release is breaking) | weekly churn: ≤2 bumps a year, batched goldens |

Other pins: Claude Code 2.1.288, opencode 1.18.25 and Ollama 0.33.2 (all probed); the model digests; Python 3.12 + `uv.lock`; the Docker image digests; latexmk.

**One core, two adapters, plus Python.**
- **Shared:** registry and checker; the `// item:` parser; the hook engine with per-language tables; `course_mode.sh`, `review-due.sh`, `firsttry`, `pins.py`; CORE and the skills; ledger and gradebook; the `fvh` interface; the static and hook-test CI jobs.
- **Per language:** `vcheck`, `vaudit`, `specfreeze`, the specimen runners, the side-channel tables, `get_toolchain.sh`, the fake-green corpora, and the CI jobs.
- **Python:** the AST hole counter, pytest scoping, the reference uv project, and the Python guard row.
- **CI jobs:** static, hook-test, dafny, verus, harness. The harness job uses only Mock, Scripted and Replay, never calls a model, and never runs on `leobwang-*` branches.

**Probes before any chapter** (results go in `VERSIONS.md`): Dafny D1–D12 and Verus P1–P13 (especially D11, D12, P6, P11, P13); legacy-CLI behaviour on a bodyless lemma; an IDE-ignored specimen extension (D8); `find-dead-code` as a vacuity instrument; `verus-spec-check` at the pinned vstd; the Docker sandbox end to end; the Ollama `/v1/messages` route (it answers HTTP 400 on an empty body, so the route exists; full Claude Code compatibility is [verify]); Qwen throughput; benchmark validity on the pins; `--system-prompt` and `--max-turns` behaviour.

## 12. Authoring plan

1 MU ≈ one content module ≈ 25 author-hours [A]. Phase 1 of §9.2 (risk-first) is kept: the hardest items are proved before any chapter.

| phase | content | MU |
|---|---|---|
| DV0 | Pins; all probes; pool validation. **Risk-first spikes** (§9.2 phase 1): BigNat L3–L4 in both languages, F08's verified wp, a 5-task F14 pilot, F12 crate feasibility; each passes the admissibility gate or triggers its fallback. Golden normalization (P11); MU per quota window | 3.0 |
| DV1 | Core port: registry/checker, hook (Dafny + Verus tables, rules 1e/1f), settings, `course_mode`, CORE and skills (referee rewrite, drift fixes), `firsttry`/`pins.py` rewrite, CI; G/V corpora (≥46 live-captured specimens); `fvh` interface skeleton | 4.5 |
| DV2 | Spine L1–L2 and F00–F03 (reference → hollow → chapter → kit → study-clone simulation). **You start here** | 3.6 |
| DV1b | Full Verus adapter: `specfreeze` parser hash, `vaudit` lint, crate gating, P13 workspace | 1.5 |
| DV1c | `fvh` complete except learner parts; Docker sandbox, egress proxy, verification container; `get_bench.sh` + licence manifests; re-validation of DafnyBench (782 programs, some broken [verify]) and the HumanEval-Verus/VeruSAGE slices | 3.5 |
| DV1p | Python adapter: guard row, AST counter, reference project, fixtures | 1.0 |
| DV3 | F04–F09 (6 × 1.2) | 7.2 |
| DV4 | F10–F12: reference increments, reference runs stored as evidence, research rubric, calibration fixtures, gold `/contract` transcripts | 4.5 |
| DV5 | Statements, pre-registration templates and gates for 5 challenges (2.0), plus the full F14 build (2.5) | 4.5 |
| DV6 | Study-clone simulations of every skill (zero leak hits); clean-clone dry run | 1.0 |
| **total** | infrastructure + spikes ≈13.5; content ≈20.8 | **≈34.3** |

**Releases:**
- **A** (DV0 + DV1 + DV2, ≈11.1 MU): you start F00.
- **B** (DV1b + DV1c + DV1p + DV3, ≈13.2 MU): it must land before F07, the first sandbox use.
- **C1** (F10, ≈1.5 MU).
- **Go/no-go at F10** (D3), based on measured pace.
- **C2** (F11–F12, the capstone and DV6, ≈8.5 MU).

**Pace rule.** Stay at least one tier ahead through the moderate tier, and two tiers ahead after it.

**Quota.** No measured MU-per-window figure exists; plan with 1.5–2.5 MU per account-week [A], so Release A is about 5–7 account-weeks. Author-side model use comes on top (lab reference runs ≤200 calls each, about 13 gold `/contract` transcripts, skill simulations); DV0 measures it. With the Lean Q track's remaining ~40 MU, the total is ~74 MU: the case for D4.

**Port map.** Copy the language-free scripts and templates. Adapt the hook, `test_hooks.sh`, the settings, the checker, CORE and the skills. Rewrite `firsttry` + `pins.py`, the wrappers, the CI matrix and `review-code`. Drop `.mcp.json` and all Lean content. Freeze the id scheme before the first commit (the Lean M → R rename cost a 155-file commit).

**Maintenance.** About 1.5 MU per Verus bump, and about 1.5 MU for Dafny's next, breaking release.

## 13. Learner time budget

| block | hours (cumulative) | checkpoint |
|---|---|---|
| F00–F03 | 17 (17) | contract v0; Dafny fluency; Verus recognised |
| F04–F06 | 17 (34) | Verus WRITE begins; gate v0, `EVAL.md` v0, statistics |
| + F10 = research-ready minimum | 10.5 (44.5) | one pre-registered replication on shipped policies |
| F07–F09 | 18.5 (52.5) | port + fidelity; contract v1; forensics; gate v1 |
| F10–F12 | 31.5 (84) | three replications; contract v2; proposal |
| capstone | 25–35 (≈115) | defended research artifact |

## 14. Risks

| risk | mitigation |
|---|---|
| Quota shared with Lean Q; capacity lower than planned | D0 and D4 first; Release A first; go/no-go at F10; calibrate on F01; DV0 measures MU per window |
| Three proof syntaxes at once | staggered D1; Rosetta and divergence cards; optional Lean R pause |
| Leaks through Claude Code state or local agents | N1; rules 1e and 1f; the same fix for lean-learn-0 |
| Agent sees ground truth, or agent code runs on the host | task-only containers; hash self-test; verification container; build-tool specimens |
| Sandbox infeasible on this host | Docker, probed in DV0; fallback is policy mode only |
| Under-powered experiments; apparatus drift | budget arithmetic + MDE; one Claude arm; paired tests on Qwen; pinned binaries; auto-update off; versions in every record |
| No in-file output pinning; toolchain churn | golden harness in DV1; P11; one pin; ≤2 bumps a year; no nightlies |
| BigNat L4 or the F08 wp is too hard; SMT closes items unaided | DV0 spikes with fallbacks; empty-body gate; `{:induction false}`, `opaque`, low fuel |
| Local models near zero on Verus; weak novice task cards | per-model strata; report the floor; oracle audit before F14 |
| GPU/RAM contention; private CI minutes | a shared calendar; a self-hosted runner under an isolated user |
