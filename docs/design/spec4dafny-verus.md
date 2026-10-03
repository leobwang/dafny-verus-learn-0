# spec4dafny-verus — an architecture spec for building a Dafny or Verus course on the lean-learn-0 design

*Written 2026-10-02 from the lean-learn-0 repository (branch `authoring`) and from two research passes over Dafny 4.11.0 and Verus `0.2026.09.27`/`f319e4d`. No reference solution, written solution, leak pattern or other answer material of the source course was read to produce this document. Every code sample below is an invented, neutral illustration, not course content.*

**Contents.**
- §0 Purpose, audience, glossary
- §1 Design thesis and goals
- §2 Course structure
- §3 Exercise formats
- §4 Written track
- §5 Agentic exercises
- §6 Instructor layer
- §7 Anti-spoiler architecture
- §8 Registry, scripts, CI, build targets
- §9 Authoring pipeline and lessons learned
- §10 Repository layout
- **§11 Translation guide (Lean → Dafny → Verus)**
- §12 Acceptance checklist and open decisions
- Review notes (critic pass)

---

## 0. Purpose, audience, how to use this document

### 0.1 Purpose

lean-learn-0 is a self-study Lean 4 course for experienced software developers. It is unusual in four ways, and those four ways are what this spec transfers:

1. **The verifier is the grader of record.** Every formal deliverable is accepted by a machine check, never by a human or an AI opinion.
2. **An AI instructor grades only what the verifier cannot.** It does so under hard anti-spoiler enforcement: hooks, deny rules and a written contract.
3. **The learner practises agentic coding with the verifier in the loop.** An AI contractor takes an escalating role per module, and the learner's job is to specify and audit its work.
4. **The course is built by a mechanized authoring pipeline.** The pipeline proves every exercise solvable before it is hollowed, pins every quoted output, and gates every claim in CI.

This document specifies that architecture so that an authoring agent can rebuild it for **Dafny** or for **Verus**. It specifies components, formats, invariants and the failure modes each one guards against. It also states plainly what does not survive the move from a small-kernel proof assistant to an SMT-backed program verifier, and gives the recommended redesign for each such part.

### 0.2 Audience

The reader is a capable authoring agent working for a human course owner. It has **no access to the lean-learn-0 repository**. Every component and format it needs is therefore described here in full. `path:line` citations into the source repository appear only as provenance, in the form `(L: path:line)`. The reader does not need to follow them.

The learner of the target course is assumed to be what lean-learn-0 assumes: an experienced developer, new to formal verification.

### 0.3 How to use it

- Read **§1** (the thesis) first. Every later rule exists to serve it.
- **§2–§10** specify the design, using the Lean course as the worked instance. Where a mechanism is Lean-specific, the text says so and points to §11.
- **§11 (the translation guide) is the most important section for building.** It maps every Lean mechanism to Dafny and to Verus, remaps the twelve content strands, sketches the module remapping, catalogues the language-specific "fake-green" exploits, and lists what does not transfer.
- **§12** is the acceptance checklist plus the open decisions, each with a recommended default.
- Normative words follow RFC 2119. **MUST** means the design breaks without it. **SHOULD** means deviate only with a recorded reason. **MAY** means optional.

### 0.4 What is invariant design vs what is Lean-specific

| Invariant design: copy it | Lean-specific: translate it per §11 |
|---|---|
| The three goals; the module loop; three exercise tracks plus an instructor layer | `sorry` holes and the "declaration uses sorry" warning |
| Four roles (Author, Coach, Examiner/Grader, Contractor), the access matrix, session hygiene | `#guard`, `#eval`, `example` |
| Solutions-first, then hollow, then a chapter written around real output | `#guard_msgs` in-file output pins, and `(drop all)` silent slots |
| Never invent tool output; pin everything; drift fails CI | `#print axioms` and the `sorryAx` audit |
| Acceptance is artifact-based, never transcript-based | A small trusted kernel plus independent re-checkers |
| One learner-visible registry as the only home of module facts | Tactics, goal states, the InfoView |
| Build targets as the access-control surface; files that must fail are never in the build | `lake` targets, `lakefile.toml`, `lean-toolchain`, Mathlib |
| A layered anti-spoiler guard, study mode vs authoring worktree, leak patterns, hook regression tests | lean-lsp MCP, the Lean REPL |
| Machine-readable item markers, slot states, first-try recording, exit files, test-out | The type-theory strand (S8) and the metaprogramming strand (S11) |
| Frozen given "spine" layers with re-supply | `native_decide`, `implemented_by`, Expr identity for statement freezing |
| Tiers, strands, families, the partition rule, the coverage rule, threshold concepts | Per-file `set_option` hygiene |
| Banks, rubrics, ledger, gradebook, Leitner review, vivas, grading rules, calibration fixtures | |
| CI shipped-state pinning; locations-only logs; staleness is an error | |
| The multi-agent authoring workflow and its lessons | |

### 0.5 Evidence tags for Dafny and Verus claims

Neither Dafny nor Verus was executed while this spec was researched; both were studied from source, golden tests and documentation. Every Dafny or Verus tooling claim therefore carries one of these tags:

- **[D:src] / [D:lit] / [D:doc] / [D:live]**: the claim was read in Dafny's C# source, in Dafny's own golden `.expect` test files, or in its reference manual, all at tag `v4.11.0`, or live from the GitHub API on 2026-10-02.
- **[V:src] / [V:doc] / [V:live]**: the claim was read in Verus source at commit `f319e4d` (rolling release `0.2026.10.02.f319e4d`), in the Verus guide at that commit, or live from the GitHub or crates.io APIs on 2026-10-02. **Note:** that commit is five days *newer* than the weekly release this spec recommends pinning (`0.2026.09.27.3cf1832`, §11). A [V:src] fact may therefore differ on the pin; re-probe it there.
- **[ext]**: a claim from outside both toolchains (a paper, a third-party repository). Give it a `VERSIONS.md` row before a chapter quotes it.
- **[verify]**: the claim was inferred or not confirmed. Probe it on the pinned toolchain before anything relies on it.

**Rule.** Even a [src] or [lit] claim MUST be re-probed on the pinned binary before a chapter quotes its output. The course's first authoring law is *never invent tool output* (§9.3). These tags record where a claim came from; they are not licences to quote.

### 0.6 Glossary

| term | meaning |
|---|---|
| **hole** | A typed placeholder the learner fills. In Lean it is `sorry`, which elaborates with a warning. Each hole MUST produce exactly one tool-counted diagnostic. |
| **green** | The build or verify command exits 0. In Lean, warnings (holes) are allowed while green. |
| **done** | Green with **zero holes counted by the tool** (never by grep), a clean assumption audit, every check enabled, and every slot filled. |
| **twin / reference** | The complete, hole-free solution file that mirrors an exercise file line for line. It lives under `Solutions/` and is built only by name. |
| **hollowing** | Turning a finished twin into the shipped exercise file by a fixed table of substitutions (§3.13). |
| **given / spine layer** | Author-written, complete, frozen library code that both exercise files and twins import. A **re-supply** layer re-provides, as given code, results that earlier learners had to prove. |
| **item** | A machine-readable grading unit, marked `item: <Module>.<Kind><n> S<k> …`. The kinds are W, C, P, H, X, T and A (§3.9). |
| **slot** | A prediction placeholder inside a P (predict) item. Its states are *unfilled*, *filled-disabled* and *enabled*. |
| **first try** | The verdict a slot gets on its first enabled run. It is recorded append-only before the learner can see the tool's answer. |
| **specimen** | (Port term) A small file whose tool output is the lesson. It stays outside every build and is run by the golden harness. |
| **exit file** | A closed-book test file per module. It is never in the build, is scored once on the first complete run, and has a threshold. |
| **card (WRITE/RECOGNISE)** | A jurisdiction card for one proof construct or tactic: one success plus one pinned live failure. A WRITE construct must be used in ≥2 checked items; a RECOGNISE construct only has to be read. |
| **receipt** | A `did:` comment on an automation step, naming what the automation closed. |
| **contract** | The `CONTRACT` header of an agentic file (goal / allowed-files / acceptance), and also the learner-written standing rules v0/v1/v2. |
| **allowlist** | `.claude/state/contract-allowlist`: the only paths a contractor session may edit. |
| **acceptance artifact** | A re-runnable command plus its expected output. It is how agent work is judged. |
| **fake green** | A build that passes while the deliverable is worthless. Each **species** has its own detection **instrument**. |
| **study mode / authoring mode** | The shipping state, with all guards armed, vs a state with the guards stood down. Authoring mode is allowed only in a dedicated linked git worktree. |
| **leak pattern** | A read-denied regex that matches reference answers and nothing public, used to test that instructor output does not leak. |
| **bank** | A per-module, pre-authored question set used by the discussion, viva and tutor skills, plus pre-authored **parallel problems**. |
| **ledger / gradebook** | The learner's error log and spaced-repetition queue, and the one-row-per-graded-artifact record. |
| **viva** | An oral exam. *Module*, *tier* and *defense* variants exist. |
| **strand / family / tier** | One of twelve content threads; groups of strands; depth levels of the depth-ordered track (§2.3). |
| **threshold concept (TC)** | A transformative idea scheduled three times: glimpsed, then operated, then mechanism. |
| **whisper** | A phenomenon named when first seen and explained ("cashed out") in a named later module. |
| **blueprint** | The learner's informal (LaTeX) proof, graded before formalization and handed to the agent as its plan. |
| **MU** | Module unit: one content-ordered module, about 6.6k words of chapter, about 25 author-hours. |
| **admissible** | A practice item whose reference solution exists and falls inside its tier's difficulty band. Only admissible items get minutes. |
| **TCB** | Trusted computing base: everything that must be correct for "verified" to mean anything. |
| **VC / trigger / fuel / rlimit / brittleness** | Respectively: a verification condition; the term pattern that instantiates a quantifier in SMT; the unfolding budget for recursive definitions; the deterministic solver resource limit; a proof that flips between pass and fail under irrelevant changes. |

---

## 1. Design thesis and goals

### 1.1 The three goals (L: `README.md:4-7`, `PLAN.md:9-12`)

1. **Read and write proofs *and* ordinary programs.** Programming is a first-class outcome, not a vehicle for proofs.
2. **Understand the language architecture:** its formal foundations, its compiler/verifier pipeline, and **its interfaces**, meaning how humans and tools drive it (CLI, build tool, language server, machine interfaces).
3. **Hands-on agentic coding with the verifier in the loop.** This includes dividing labour between two AI trust postures: a contractor whose work the verifier checks, and an instructor whose judgement is advisory.

Every module, strand and agent run traces back to one of these three goals. In the depth-ordered track the mapping is explicit: goal 1 covers strands S1–S7 plus all practice; goal 2 covers S8–S11; goal 3 covers S12, the agent ladder and the capstone (L: `QPLAN.md:720`).

**Port.** Keep all three. For goal 2, "λ-calculus → CIC, elaborator, kernel" becomes "program logic (Hoare triples, weakest preconditions) → VC generation (Boogie for Dafny; VIR → AIR for Verus) → SMT (Z3) with triggers → compilation and erasure". For goal 3, the trust story changes from "small kernel" to "TCB inventory plus audit" (§11.5).

### 1.2 The thesis: the verifier grades the formal, the instructor grades the understanding

lean-learn-0 states the thesis as "The kernel grades the formal; the instructor grades what the kernel cannot" (L: `PLAN.md:23`; `.claude/skills/instructor/CORE.md:12-15`). Its consequences:

- Anything a machine can decide is taken away from the AI instructor: compiles or not, hole count, assumption audit, executable checks. The instructor is **advisory**. A tool check always outranks it, and the learner may dispute any instructor finding at the level of a labelled rubric line.
- The AI appears in **two postures that never share a session**:
  - The **contractor** writes code. Its prose is "rhetoric"; its artifacts are "binary and sound" once the verifier and the audit accept them.
  - The **instructor** (coach and examiner) never writes course code and never sees reference solutions. Its grades are opinions anchored to pre-authored rubrics.
- The asymmetry is itself taught: there is a "trust matrix" lesson and a grade-the-grader variance lab (§6.12).
- **Why the verifier beats unit tests as an agent oracle** (the course thesis, taught in the agentic module). Verification is *sound, universal, localized, conjunctive and decomposable* (L: `PLAN.md:160`). The learner must be able to argue each property and its limits.

**Port caveat (first-class).** An SMT verifier is *sound modulo its TCB* but *incomplete and non-deterministic in practice*. "Verified" is trustworthy; "could not be proved" is not a refutation, since it may mean a missing invariant, a trigger problem or a resource-limit hit [D:doc, V:src]. The thesis therefore gains a sixth property to teach, **"the oracle can say 'don't know'"**, and every rule that relies on the referee (disputes, the grading rule that requires a demonstrated flaw, predictions) is adjusted for it (§6.5, §11.5).

### 1.3 Programming first, proofs from day one

- The first three content modules are mostly programming, but **a real machine-checked theorem appears on day one** (in Lean, `theorem … := rfl`). Proof techniques arrive quickly after that. "Term-mode-first ordering is the classic self-learner stall point" (L: `PLAN.md:20`).
- **The hole contract is introduced in module 1.** A hole is a typed placeholder. "Green build with zero holes" is the definition of done, the hole count is the progress meter, and an assumption audit is the final check (L: `CLAUDE.md:6-7`).

**Port.** Day one has a verified function with a postcondition and a first lemma, plus a first lesson on the course's hole construct and its counter (§11.1, rows 1–2).

### 1.4 Three exercise tracks plus a standing instructor layer

Every module offers up to three tracks (L: `README.md:21-38`):

- **Written track.** `paper/<id>_problems.tex` → the learner's `paper/<id>_answers.tex`. Building with `make -C paper paper` green is this track's build. The learner's LaTeX proof later becomes the blueprint the agent formalizes (§4).
- **Machine-checked track.** Exercise files with holes and executable specs. Done is defined in §0.6.
- **Agentic track.** `/contract <id>` starts an AI contractor in a fresh session, with a role that escalates per module (§5).
- **Instructor layer.** `/tutor`, `/discuss`, `/review`, `/viva`, `/grade-paper`, `/review-lean` (port: `/review-code`). It asks, probes and grades. It never writes course code and never opens reference solutions (§6).

### 1.5 Agentic exercises with an escalating role ladder

Every content-track module ends with an agentic run, and the depth track spreads fourteen runs over its eighteen core modules (one of them, contract v0, is written by hand with no agent at all; §5.1). In every run **the learner, not the agent, does the exercise**. The deliverable is the learner's specification and audit. The agent's role climbs from repairer to implementer, prover, refactorer, red-teamed contractor, toolsmith and co-developer, and the learner's job climbs with it: read transcripts → write checks → audit assumptions → write statements → write blueprints → plant cheats → build gates (L: `PLAN.md:22`, `QPLAN.md:747-767`). See §5.

### 1.6 Anti-spoiler discipline

Reference solutions live **in the same repository** as the learner's work, because the learner may open them as the last step of each module. The AI must never open them, in any role. Enforcement is layered, hard rules first:

1. static permission deny rules;
2. a pre-tool-use hook covering file tools, shell and the language-server MCP tools;
3. a written instructor contract that repeats every hard rule as an instruction.

A fourth component, the **detector**, consists of read-denied leak patterns run over instructor output in tests. The design goal is that "degradation is soft, never silent" (L: `CORE.md:93-94`). See §7.

### 1.7 Solutions-first authoring

Each exercise is authored as a complete, hole-free, fully pinned reference first. It is then **hollowed** into the exercise file (§3.13), and the chapter is written around real captured output. This "guarantees solvability as stated" (L: `PLAN.md:244`), and it keeps the chapter, the exercise and the reference consistent by construction. See §9.

### 1.8 Artifact-based acceptance

Agent transcripts are nondeterministic, so they are never evidence of completion. Every acceptance criterion is an **artifact anyone can re-run**: a command with its expected output, a hole count, a pinned audit row, an unchanged-spec diff. One known-good transcript per agentic exercise is kept as a sample only (L: `PLAN.md:246`).

### 1.9 Supporting principles

| principle | rule | failure it prevents |
|---|---|---|
| **Architecture whispers / threshold concepts** | Name a surprising phenomenon when it first appears, cash it out in a named later module, and track the pair in a "planted → harvested" table. Never rely on untaught material (L: `PLAN.md:24, 248`) | forward references without payoff; mechanisms taught before their symptoms are met |
| **Theory with receipts** | The theory module is hands-on: judgments become datatypes, soundness becomes a total evaluator, and checking returns a certificate, not a bare verdict (L: `PLAN.md:25`) | lecture-only theory |
| **Paper before keyboard** | Written proof first, graded before formalization; the grading gaps predict where the formal proof will stall (L: `PLAN.md:26, 89`) | formalizing without a plan |
| **One running artifact** | An expression AST is seeded early, grown into an evaluator, and verified-compiled in the capstone (L: `PLAN.md:27`) | disconnected toys; a capstone that needs fresh setup |
| **Library from day one, used later** | The heavy library dependency ships pinned from the start; early modules are CI-forbidden from importing it; install mechanics are taught in a throwaway scratch directory (L: `PLAN.md:28`) | a mid-course dependency change bricking the learner's repo |
| **Honesty ledger** | Advanced work ships a `TRUST.md` stating what is proved, what is tested and what is assumed. Presenting an unproved claim as proved fails the work (L: `QPLAN.md:419`) | overclaiming |
| **Pin every external claim** | `VERSIONS.md` records every claim about the outside world with a verified-on date (§8.7) | stale folklore in chapters |

---

## 2. Course structure

### 2.1 The two-track model

lean-learn-0 holds two complete courses over the same three goals, in one repository:

- **R track (content-ordered).** Sixteen modules, one topic each, in dependency order. Shipped.
- **Q track (depth-ordered).** Thirty-three modules (L: `QPLAN.md:26-54`):
  - a survey module that touches every strand;
  - three concept tiers, each a full sweep of all twelve strands at increasing depth;
  - three practice tiers of the same shape;
  - fifteen solo challenge modules (five topics × three).

The Q track is **standalone**: no Q exercise depends on an R file, and R chapters are optional "Deep dive → Rxx §y" links. A shared module registry, a shared instructor layer, one ledger and one gradebook serve both tracks. A disjointness gate (§2.7) keeps the second track from being the first one renamed.

**Port recommendation (see OD2 in §12.2).** Build one track first: the content-ordered shape, which is cheaper and proven, but authored with the Q track's mature mechanics (item markers, predict slots, exit files, first-try recording, spine layers). Add a depth-ordered track later only if the course owner wants it, and when you do, apply §2.3–§2.8 in full. Everything in this section is written so that either track can be built alone.

### 2.2 The content-ordered track

**Shape.** Sixteen modules in three bands: modules 1–6 (foundations), 7–11 (abstraction and theory), 12–16 (machine, verifier loop, capstone). The band sets the discussion persona and the code-review bar (§6.9, §6.6).

**Per-module design record.** The design plan carries one record per module with these fields: a title; *why it exists* (the design role); the core payload; the diagrams the chapter must draw; the written-track problems, or "none, it would be filler"; the exercise list; the agentic role; the whispers it plants or harvests. Copy this record shape.

**The source R map, by design role** (L: `PLAN.md:57-170`). It shows the kind of role each module plays; the target-language remap is §11.3.

| # | module | design role | agent role |
|---|---|---|---|
| 1 | Hello: toolchain, build, verifier loop | repo anatomy; the three feedback loops (in-editor checks, single-file check, full build); first definitions **and** first theorem; the hole contract; one language gotcha; the learner writes contract v0; first contact with guardrails (asks Claude to open a solution and watches the hook deny it) | repairer (5 planted errors) |
| 2 | Data types, match, recursion | data first; plants a deliberate quirk for later payoff; **seeds the running AST**; the first written-track grading cycle starts the gradebook and the ledger | implementer vs checks; the learner then adds adversarial checks the agent might have gamed |
| 3 | Structures, namespaces, API design | total-API design | API-scale implementer + adversarial review |
| 4 | Specs as logic (Lean: propositions as types) | first audit; definitional vs propositional cliffhanger; **first naming of semantic hallucination**: "the checker checks proofs against statements, never statements against intent" | audited prover |
| 5 | Proof mode and feedback (Lean: tactics) | the proof kit; installs the **fast verifier channel**; latency economics (~100 ms language server vs ~30 s build) | prover restricted to fast-channel tools plus ONE final build as verdict |
| 6 | Induction and equational reasoning | resolves the cliffhanger; hole-driven decomposition (green at every step); statement auditing (refute → repair → prove); **flagship written problem**: the paper proof reveals the missing helper lemma | agent receives only the top statement and must decompose while staying green |
| 7 | Library: infrastructure, automation, search | install mechanics taught cold in a scratch directory; automation "waves"; the search ladder | retriever race |
| 8 | Abstraction mechanism (Lean: typeclasses) | debugging resolution failures | infra debugger |
| 9 | Effects (Lean: monads, IO) | grows the AST into an evaluator with errors; laws proved | refactorer under harness (the learner checks whether migrated statements silently weakened) |
| 10 | Invariants in types (Lean: dependent types) | the **invariant-enforcement spectrum** (runtime check → Option → refinement → indexed type); termination measures | **flagship spec-to-proof contractor**: the learner writes the statements, the agent delivers implementation and proofs |
| 11 | Theory: judgments and a verified checker | foundations hands-on; the "golden triangle" (normalization ⇔ consistency ⇔ decidable checking); a certificate-producing checker | metatheory contractor; the audit targets **statements** (a plausible-but-wrong index typechecks) |
| 12 | Driving the compiler: the four doors | editor/LSP, build tool, CLI, machine/REPL all converge on one core; speak LSP by hand; build a 20-line agent | toolwright |
| 13 | Under the hood: the pipeline and the trust story | stage-attribution drill; untrusted front end (including **any AI agent**) vs small trusted kernel | pipeline forensic |
| 14 | Extending the tool (Lean: metaprogramming) | write your own automation | toolsmith (one automation closes a 12-goal battery; the learner audits all 12) |
| 15 | The verifier loop: agentic coding | the thesis; the **escalation ladder** (run → executable checks → property testing → proof → audit); **fake-green forensics**; statement review as "the irreducible human job"; grade-the-grader lab; tutor red-team | red-teamed contractor |
| 16 | Capstone: verified compiler | compiler correctness against a denotational semantics via a generalized induction hypothesis **discovered on paper**; verified optimizer; adversarial round; ship a CLI; blueprint gate | co-developer |

### 2.3 The depth-ordered track

#### 2.3.1 Binding shape (L: `QPLAN.md:58-75`)

| decision | rule |
|---|---|
| Standalone | Covers the full payload of the content track, with no dependency on its files. |
| Depth order | Survey (1 module) → intro (2) → moderate (3) → detailed (3) → intro practice (3) → intermediate practice (3) → hard practice (3) → challenge (15). |
| One sweep per tier | Within a tier, the modules **partition** the strands, so every tier is one sweep. |
| Concept tiers are checked | About 25% of each concept module's time is machine-checked practice. Every concept gets ≥1 predict or one-hole item that the build checks. |
| Budget | About 3 h per module through the hard practice tier. Challenges are solo, uncapped and PhD-level. |
| Library staging | No heavy library in the first three modules. Introduce it at moderate, expand at detailed, use it throughout practice. |
| Examples | "Spine plus extras" (§2.6). |
| Grading | Solutions-first through the hard tier. Challenges are graded by verifier or harness (math-like topics), or by ratios to a reference implementation (engineering topics). |
| Billing | Agentic work uses no usage-billed APIs; budgets are counted in calls, tokens and wall-clock (§5.6). |

#### 2.3.2 Strands and families

There are twelve **strands**, S1–S12, ordered by dependency (L: `QPLAN.md:98-117`). Each owns a slice of the content payload. They are grouped into three **families** used by every tier from moderate on:

- **A** = S1–S5: data, logic, proof mechanics, induction, libraries;
- **B** = S6–S8: abstraction, invariants and totality, foundations;
- **C** = S9–S12: interfaces, pipeline, extension, verifier loop and agents.

**Rules:**
- **Usage rule.** A module may use any strand at the previous tier's depth, plus earlier strands at its own depth within the same tier.
- **Families are balanced by new payload, not by strand count.** The first draft split the strands 4/4/4. That gave one family about 3× the new material of another, so S5 moved into A (L: `QPLAN.md:81`). An imitator MUST measure new material per family, not count strands. "New" is relative to the **actual learner**: the source re-balanced for a learner who had already finished four content-track modules, which moved the ratio from about 5 : 1.5 to about 4 : 2.5 (L: `QPLAN.md:81, 923`).

The Dafny and Verus strand definitions are in §11.2.

#### 2.3.3 Tiers

| tier | modules | strand partition | depth | practice share | exit check |
|---|---|---|---|---|---|
| 0 Survey | 1 | all 12 in one module | name and recognise every strand; ~3 constructs to write | ~26% | build green; sweep file has zero holes; closed-book "map" ≥9/12 |
| 1 Intro | 2 | S1–S6 / S7–S12 | introductory syntax | 27–29% | 6 closed-book items, ≥5/6; zero unfilled slots; **tier viva** at the tier's last module |
| 2 Moderate | 3 | by family A/B/C | moderate syntax; first extension points; property testing; library | 22–25% | 4 unseen items, ≥3/4; predicted audit rows confirmed; tier viva |
| 3 Detailed | 3 | by family | full syntax or mechanism and internals | 24–30% | 4 unseen items, ≥3/4; one explain-back; tier viva |
| 4 Intro practice | 3 | by family | statements given; ≤10-line proofs; one hole per item; 8–15 min per problem | ~85% | "kernel part" + ≥1 of 2 timed items; tier viva |
| 5 Intermediate practice | 3 | by family | no skeleton; the learner picks the induction; ≤1 invented lemma; ~1 in 5 statements written from prose | ~85% | kernel part + 1 timed item; tier viva |
| 6 Hard practice | 3 | by family | 3 problems of 40–75 min; ≥1 statement written or generalized by the learner; 2–4 invented lemmas or one invariant; pre-graded blueprint; capstone round | ~85% | kernel part + code review at the top bar + paper grading before and after formalization; tier viva |
| Challenge | 15 | all | solo, uncapped | — | topic gate + defense viva |

- **"Kernel part"** (port: "verifier part"). The build is green, the module file has zero holes, and the per-target assumption audit is clean. In Lean that means axioms ⊆ {propext, Quot.sound, Classical.choice}, with no `sorryAx` and no native-evaluation axiom (L: `QPLAN.md:134`). The port definition is in §11.1.
- **Exit checks are pass/fail only where the machine decides.** Everything else is advisory.
- **Viva cadence.** One tier viva at the last module of each concept and practice tier (six in all), plus one defense per challenge module. The registry field `viva_mode = tier` sits only on those last modules, and the checker enforces "each tier partitions S1–S12 and ends in exactly one tier viva" (L: `scripts/check_course_map.py:17-22`).

#### 2.3.4 The coverage rule

**No payload of the goal set may have its only home in the challenge tier** (L: `QPLAN.md:35, 695-720`). Every payload row cites *budgeted* items in the core modules; challenges are listed only as **deepening**. That is what makes "complete the track = all core modules + every challenge passed *or closed with a retrospective*" safe.

- **Mechanism.** The registry ends with one `[[coverage]]` table per **content-track module** (the payload being covered), in module order, with exactly the fields `r`, `payload`, `homes`, `deepening`, `gap` (L: `MODULES.toml:87-88, 1571-1588`; `check_course_map.py` `COV_FIELDS`).
  - A home is a core-module strand anchor (`Q05.S7`) or a core item id (`Q05.H2`). `deepening` lists only bare challenge-module ids.
  - A home in a `planned` module is pending (counted, not an error). Once its module is past `planned`, every home must resolve: its strand has a checked item, or its item marker exists.
  - `gap` names a deliberate hole in the coverage, with its reason (`""` = none).

  An invented row:
  ```toml
  [[coverage]]
  r = "R06"
  payload = "loop invariants, decreases, assume-driven decomposition, statement auditing"
  homes = ["Q02.S4", "Q04.S4", "Q04.H3", "Q07.S4"]
  deepening = ["Q25"]
  gap = ""
  ```
- **Port.** Keep it even with one track. Key the rows by **goal payload** instead of by content-track module (`payload_id = "G1.loops"` in place of `r`), and re-read the rule as "no goal payload may live only in optional modules".

#### 2.3.5 The concept→item matrix ("D4")

Every non-reading concept in the depth ladder MUST cite at least one machine-checked item (L: `QPLAN.md:121`). The registry encodes this per concept module:

```toml
# an invented record for an intro module whose strands are S7–S12; one key per strand at least
[module.concept_items]
"S7.subset-types"  = ["Q03.H3", "Q03.P1"]
# nominal: X4 verifies any total function; it never checks the invariant
"S7.termination"   = ["Q03.X4"]
"S8.hoare-lineage" = "R"        # reading-only
"S12.contract-v0"  = "prose"    # learner-written artifact, advisory review
# … S9, S10, S11 keys omitted here; the checker requires them
```

Keys are `S<k>.<concept>` with `S<k>` among **the module's own strands**. Values are a list of this module's P/H/X/T/A item ids, `"R"`, or `"prose"`. TOML attaches `[module.concept_items]` and `[module.imports]` sub-tables to the `[[module]]` above them, so they MUST come after that record's last plain field (L: `MODULES.toml:83-85`).

- **Checker rules:**
  - every cited item exists;
  - every P/H/X/T item is cited somewhere (no orphans);
  - every strand of the module has a key;
  - `"prose"` is legal only for S12.
- **The `# nominal:` comment** honestly marks a citation whose check never actually touches the concept. Weak coverage becomes visible instead of hidden.

#### 2.3.6 The depth ladder

The design plan holds a strand × {Survey, Intro, Moderate, Detailed} matrix. Each cell lists the syntax or mechanism taught at that depth (L: `QPLAN.md:176-199`).

- Entries marked **[R]** are reading-only. Every other entry needs a checked item.
- **Cell design pattern.** Each cell pins **verified surprising behaviours** of the pinned toolchain as predict items. Lean examples: the print order of a numeral; an error that appears only at code generation while the proof checks; which tactic adds which axiom.
- Every such fact carries a `[V: probe]` tag pointing into an author-only probe archive.
- A "corrections carried forward" list records folklore that probes overturned, so it never re-enters a chapter.

#### 2.3.7 Threshold concepts

Each TC is scheduled three times: **glimpsed** (named in passing), **operated** (used in exercises) and **mechanism** (explained from the inside) (L: `QPLAN.md:201-217`). This is the depth-ordered form of the content track's whispers. The Lean set covers: propositions are types; Γ ⊢ T is the interface; green with a hole is not done; definitional equality; recursion ⇔ induction; totality ⇒ consistency; types indexed by values; everything elaborates to a kernel term; small kernel with an untrusted front end, agents included; code is data; four doors, one environment; instance resolution is search; statements are the human job. The Dafny/Verus TC set is in §11.2.3.

#### 2.3.8 The challenge tier (L: `QPLAN.md:406-546`)

| aspect | rule |
|---|---|
| Solo | `/contract` refuses solo modules. The tutor is capped at rung 2, plus verifier-dispute recipes and truth probes of sub-lemmas the learner proposes. Hint depth goes to the ledger; the defense marks the gradebook row `assisted (max hint-depth N)`, which is a record, not a penalty |
| Edit enforcement | Solo directories (`Challenges/`, `agents/`) are a hook branch that **never** consults the allowlist |
| Order | Topics in any order after the hard tier; modules within a topic in order |
| Gate | `scripts/challenge_gate.sh <ID>`: (1) sha256 of the frozen statement files; (2) zero holes, counted by the tool; (3) a clean assumption audit per target; (4) no trust-leap constructs; (5) escape hatches only where `TRUST.md` lists them; (6) independent re-check; (7) a scan for forbidden constants and forbidden reach |
| Bands | Topic minimum = pass; a distinction tier where defined; "abandoned with a retrospective" is recorded but is not a pass |
| Review bars | Math/PL: library-PR bar. Engineering: "production" (reproducible bench, every escape hatch justified, every claimed property audited). Agentic: test suite green + all decidable-class cheats rejected |
| Defense viva | Six questions built from the learner's own artifact (§6.8) |
| References | Per-topic policy: math-like topics ship statement + non-vacuity witnesses + truth evidence + an author hole-skeleton with ≥5 nodes, and no reference proof; engineering topics ship a reference implementation that is open after the module; agentic work is harness-graded with hidden par agents |
| Held-out material | Two trees: `Ref/` is open after the module, like any solution; `Hidden/` is **always encrypted** and is unsealed only inside the grader container |
| Frozen-statement grading | A sha-pinned statement file defines the target; the learner proves it in a separate file; a denylist names upstream results in case the library adds them |

**Port.** The challenge tier transfers well, and engineering topics (production services, codecs, systems code) fit Dafny and Verus *better* than they fit Lean. Gate item (6), "independent re-check", has no faithful analogue; §11.5 gives the substitute and the honest wording.

### 2.4 Module anatomy

#### 2.4.1 Artifact set per module (L: `PLAN.md:14, 198-237`)

- chapter `docs/<ID>_<Name>.md`;
- written pair `paper/<ID>_problems.tex` + `paper/<ID>_answers.tex`, only where it pays;
- rubric `paper/rubrics/<ID>_rubric.md`, **even without a written track**: it serves code review and the agent-audit debrief;
- exercise file(s);
- agentic file(s);
- the reference twin(s) under `Solutions/`;
- a question bank `.claude/skills/instructor/banks/<ID>.md`;
- leak patterns `tests/instructor/leak_patterns/<ID>.txt`;
- grader calibration fixtures (flawed and gold);
- for depth-track modules, also: a closed-book exit file, optional audit fixtures, and given spine layers.

#### 2.4.2 The module loop: fixed order, Solutions LAST (L: `README.md:66-71`)

```
chapter (→ optional /discuss) → paper problems → make paper green → /grade-paper (fresh session)
→ revise → exercise file (/tutor as needed, after ≥20 min stuck) → done → /grade-paper --post
→ agentic exercise via /contract (fresh session) → /review-code (fresh) → /viva (fresh)
→ self-compare with Solutions/ LAST → /review whenever the session banner shows due items
```

- An early peek at the solutions "taints every later grading step for that module". The learner *may* open them; the AI never can.
- Asked outright for an answer, the AI names the solutions path and stops.

#### 2.4.3 Chapter skeleton (L: `docs/R*.md`, `docs/Q0[1-3]*.md`)

1. `# <ID> — <exact registry title>`, 1–2 paragraphs (a callback to the previous module plus what this one adds), then "Three ideas do all the work" as a numbered list. A survey module uses an "In this module" table of contents instead. A depth-track chapter then opens with `## 0. How this module works, pretest, test-out`: the minute budget, the T items to take closed-book before reading, and which section each pretest lets the learner skip (L: `docs/Q02_FirstSyntaxI.md:37`).
2. A **"This module's files"** table:
   - the exercise file, with its exact shipped hole count;
   - the agent file, with its shape and shipped state;
   - the exit file;
   - the given files;
   - the reference, described as "yours to open LAST".
3. Numbered sections with **stable headings**, because tutor rung 2 points at them by name: `## <n>. S<k> — <title>`, with `---` between top sections. In depth-track chapters, one section = one strand, in strand order.
4. Predict callouts: `> **Predict (P<n>) — commit in the file before reading on.** <question>`. **The answer appears only after the box.**
5. `## k. On paper, before the keyboard` (written-track modules only).
6. `## k+1. The exercise file`: hole count, item list, the hint-dial rule, the Done line, the slot protocol.
7. `## k+2. Exercise (agentic): <title>`: the CONTRACT blockquote (`> **CONTRACT (for /contract <ID> — run it in a FRESH session):**`), the steps, then a subsection **"What the dashboard can and cannot see"**, with live evidence.
8. `## Exit (closed book)`: rules, scoring command, threshold.
9. `## Instructor touchpoints`: one bullet per skill in loop order, each with when to run it, which session, the module particulars, explicit "not this module" lines, "Solutions last", and "`/review` when the banner says items are due".
10. `## What <ID> planted`: a seed → harvest table closing the whisper loop. A survey module ends with a "Done when" checklist and a "Where this is going" section instead.
11. Optional `*Deep dive → …*` links that never walk another exercise's solution.

Every chapter also has a **"What the instruments can and cannot see"** passage. It states, for each check, what it verifies and what only a reader or an audit can see.

### 2.5 Time budgets and rates

**Rates** (L: `QPLAN.md:252-261`; all [A]: calibrate on the first module):

| activity | rate |
|---|---|
| reading | 120 wpm |
| worked example | 4–5.5 min |
| WRITE card | ~2.5 min, inside the worked-example minutes |
| RECOGNISE card | 1.5 min, from reading time |
| predict item | 2–2.5 min |
| one-hole item | 4 / 6 / 8 min (intro / moderate / detailed) |
| exit item | 3–5 min |
| practice problem | ~2 min per reference line at intro tier |
| practice-module brief | ≤2k words, 15 min (10 in the hard tier) |

- **Every concept module is itemized to ~180 min.** Example line: `setup 15 · read 40 · worked 36 · predict 26 · holes 20 · agent 12 · exit 20 · calib 11 = 180`.
- Chapters run 4,800–6,600 words.
- **Agent wall-clock time is outside every learner budget.** The agent line counts only the learner's spec-writing and audit minutes.
- Unbudgeted activities (cards, briefs, contract rewrites) were the main feasibility critique of the first plan, so every one of them now has a line. An imitator MUST reconcile every module's minutes to its total.
- **Calibration unit:** 1 MU ≈ one content module ≈ 6.6k words ≈ 25 author-hours [A].

### 2.6 The running spine: frozen given layers plus extras

- **Spine object.** One object is carried across the whole depth track. In Lean it is binary numerals `Bin`, chosen LSB-first because that produces surprises early. It is reused as the course-local benchmark stratum in the agentic challenges.
- **Layers.** The spine ships as given layers L1 (survey), L2 (intro), L3 (+Meta) (moderate), L4 (+Meta, +x) (detailed) and L5–L7 (practice tiers). Each layer row records its given content and its import tier (L: `QPLAN.md:370-404`).
- **The given-API rule** (MUST):
  1. Layers are author-written, complete, frozen, and identical for the learner and the reference tree. They are imported, never copied.
  2. Holes are leaves in the module's own files (`namespace Qxx`), never in a layer.
  3. **A later layer imports only given layers.** Anything a later module needs from earlier learner work is **re-supplied** as given code in a later layer, so a learner's wrong or missing proof never propagates.
  4. One global instance per class; any swap is scoped.
  5. No contractor may ever edit a layer (guard rule 2f, §7.2).
  6. A spine layer's own live checks MUST avoid every value a later predict item asks for.
- **Extras.** Each strand gets fresh objects where the spine fits poorly: plain propositions for logic drills, number systems for the library strand, a parser for effects, combinators for the theory strand.
- **Isolation.** Every top-level declaration sits under the spine or module namespace, and every global-effect declaration (instance, notation, macro) is local or scoped.

**Port.** A spine object with natural **spec/implementation tension** suits SMT tools: a bit-list numeral with an abstraction function `toNat`, executable increment and add, and lemmas tying them together. In Verus, use an exec representation over machine integers with overflow obligations plus a `Seq<bool>` spec view. In Dafny, use a `datatype` or `seq<bool>` with a ghost `ToNat`. Layers become Dafny modules in given files that both projects include (§10), or a separate `given` crate in Verus.

### 2.7 Disjointness between tracks

This applies only if two tracks exist (L: `QPLAN.md:350-368`).

- **Clauses:**
  - (a) the same artifact is forbidden;
  - (b) a solution that transfers by renaming is forbidden;
  - (c) the same payload genre is narrowed. Where standalone coverage forces a shared genre, it becomes an **explicit waiver accepted by the course owner**, with its cost stated ("if you do module 12, 14 or 16 later, their aha is pre-empted").
- **The avoid list is regenerated on every run and never committed.** Its sources are:
  1. every hole-bodied declaration in the other track's exercise files;
  2. every parallel problem in the other track's banks;
  3. every problem in the other track's written problems;
  4. a committed curated list.
- **Matching:**
  - keys are compared after namespace stripping;
  - a curated type name occurring as a component is a hit;
  - so is an equal syntax token, or any use of a `!never-reference` name.
  - The new track's own bank parallel problems are also checked against its own exercises, with no waivers.
- **Waivers** live in a TSV (`<new key>\t<old source>\t<reason>`). **A waiver that matches no hit is an error ("stale, like a stale pin").**
- **Shape overlaps** that a name scan cannot see are listed as waivers, never claimed as caught.
- **Isolation.** Neither track imports the other or the reference trees. Spine layers import only lower layers.

### 2.8 Difficulty calibration and the admissibility gate

**Difficulty table** (L: `QPLAN.md:302-327`):

| dimension | intro practice | intermediate | hard |
|---|---|---|---|
| statement | given | given; ~1 in 5 written from prose (hidden equivalence + non-vacuity check) | ≥1 per module written or generalized; **the plain statement ships and is known to fail** |
| scaffold | skeleton or named hints | none; ≤1 hint on request | blueprint only, written by the learner and graded before formalization |
| reference proof length | ≤10 lines | 10–30 | 30–80 |
| invented lemmas | 0 | ≤1 | 2–4, or one invariant |
| minutes per problem | 8–15 | 20–45 | 40–75 |

- **Admissibility gate (MUST).** No practice item gets a minute budget until the author's reference is **complete** and falls inside its tier's line band and invented-lemma band, measured after the given layers are re-supplied. Until then the item is "not yet admissible" and has a **named fallback**. The registry is designed to carry an `admissible` flag so CI can forbid minutes on non-admissible items; in the source that field is planned for the practice-tier phase and not yet built (§8.1).
- **Hard-tier anchors.** Each hard item is calibrated against an item of known difficulty.
- **Whole-problem automation gate (author check).** From the intermediate tier on, every heavy automation tool must *fail* on the full problem, or the item tests nothing. **Port: this becomes the empty-body gate** (§11.1 row "automation"): every hole, given an empty body `{}` and maximal automation settings, MUST fail to verify, because SMT plus Dafny's auto-induction can close surprisingly many exercises unaided [D:doc].

### 2.9 Library staging and import tiers

- **Content track.** The heavy library ships pinned from day one. Modules 1–6 import none of it (a CI grep). Module 7 teaches install mechanics in a scratch directory: a toolchain-mismatch error, scoped vs bare update, cache timing.
- **Depth track.** No library in the first three modules. It enters at moderate, in the library strand's file only, with a 20-min install lab. It expands at detailed and is used throughout practice. Import hygiene is measured: the narrow import vs the whole library, with timings.
- **Per-file import tiers** (registry `imports` table). Every file of a depth-track module is mapped to a tier (Lean: `core | std | lean | qq | plausible | mathlib-tactic | mathlib`). CI checks the **transitive** closure of each file's imports against its tier's allowlist.
- **Port.**
  - Dafny's opt-in standard libraries (`--standard-libraries`, modules `Std.*`) [D:src] and Verus's `vstd` (always present, with broadcast groups) [V:doc] take Mathlib's place.
  - Dafny tiers: `core` (no `Std`) → `std-<module>` → `std-all`.
  - Verus tiers are subtler, because `vstd::prelude` is always imported. Define tiers by **which vstd modules and broadcast groups a file may `use`**, e.g. `prelude` → `seq_lib` → `arithmetic` → `all`, and check them with a source lint [verify].
  - The install lab becomes the toolchain-mismatch lab: Verus's exact rustc requirement, or a Dafny/Z3 version mismatch [V:src, D:src].

---

## 3. Exercise formats in full

Each format below is given in three parts: what it is in the Lean course, why it exists (the failure it prevents), and its port form. Port forms are given in Dafny (`.dfy`) and Verus (`.rs`). Comment leaders change from Lean's `--` to `//`. Everything else in the grammars stays the same.

### 3.1 File taxonomy and build wiring

| kind | shipped state | in a build root? | twin? |
|---|---|---|---|
| **exercise file** | green, with exactly N counted holes; checks over holes commented out | **yes** (the track's default target) | `Solutions/<same stem>` |
| **exit file** (closed book) | green with K holes (empty blocks) | **no**: failing attempts must not redden the build | yes |
| **agentic file**: one of four shapes (§3.11) | depends on the shape | only the green-with-holes "bank" shape | the twin carries a clearly marked reference section |
| **given / frozen file** (spine layer, support, scaffold) | complete, no holes (except deliberately planted demos), live checks | spine and support: yes; planted demos: no | **none**: imported by both learner files and twins |
| **specimen** (port) | its output is the lesson; often fails by design | **never** | none |
| **reference twin** | hole-free, **silent** (prints nothing), fully pinned | its own root, built **only by name** | — |
| chapter | Markdown; not built; diagrams rendered by hand | — | — |
| written pair | compiles under `make paper` | — | `paper/solutions/<ID>_solutions.tex` (built only by `paper-solutions`) |
| rubric, bank | learner-visible | — | — |
| leak patterns | **read-denied** | — | — |

**Wiring rules (MUST).**

1. **The default build target is the learner's exercises and nothing else.** The reference root and the second track's root are built only by name. A bare build therefore never compiles or prints reference material. A registry check pins the default-target list.
2. **Files that must fail, or whose output is the lesson, are never in any build root.** This covers planted-error files, red-by-design agent files, exit files, demo executables and specimens. They are checked one by one, and CI pins their exact shipped state (§8.5).
3. **Import mirroring.** An exercise file imports the previous *exercise* file (the learner's own work). The twin imports the previous *twin*. Given files are imported directly by both. (The depth track already narrows this through re-supply: later modules import only given layers, §2.6. **Dafny port:** use re-supply everywhere, because a hole in an imported exercise file blocks compiling and testing the importer, §3.3.)
4. **Namespaces.** One per module (`R05`, `Q02`). Agent, exit and given demo files use a sub-namespace (`Q01.Map`, `Q03.Fake`) so that contractor names and learner names coexist in one build.
5. **Scoped effects.** Every global-effect declaration in a module file is local or scoped, because one root imports every module together.
6. **Per-file options.** Lean restates `set_option autoImplicit false` and a pretty-printer option in every file, because options do not travel through imports and quoted output would stop matching. **Port:** pin the verifier flags in exactly one place, the project file or crate metadata (§10), and make every course command read them from there. Never let a file or a learner shell vary them.
7. **Root comments.** Each build root states what it deliberately does not import, and why.

### 3.2 Exercise-file header

```
/*!                                  (Lean: /-! … -/ ; Dafny/Verus: a leading block comment)
# <ID> — <registry title> (Exercises)

<import note: why each import exists; which earlier file must be finished first>

How to work this file:
1. Paper first: paper/<ID>_problems.tex (<gist>) — then come back.        (written-track modules only)
2. <module-specific working note>
3. Replace each hole, then uncomment the checks beneath it.
4. Done = `<gate command> <this file>` prints only the summary line and exits 0,
   AND `scripts/firsttry.sh <ID> --report --strict` exits 0.
5. Stuck for 20 minutes? /tutor <ID>.

This file ships with exactly 12 holes: T1, T2, H1–H8 and two verdict strings.
Commit every prediction BEFORE you run anything it is about, open later files,
or read CI, the registry or the plan: their checks and headers give some
predictions away.

The agentic exercise (<role>, <agent file>) is at the bottom.
*/
```

Depth-track headers add an item-kind legend and the slot protocol (§3.8). The **exact shipped hole count** MUST appear in the header and in the chapter, and CI pins it (§8.5).

### 3.3 Holes

**Lean.** `sorry` is a typed hole. The statement still elaborates, the file compiles with one `declaration uses 'sorry'` warning per hole, and the hole count is the progress meter.

| case | Lean shipped form |
|---|---|
| signature only | `def turn : Dir → Dir := sorry` |
| skeleton is part of the spec | keep the match arms, put `sorry` in each right-hand side, and say why in the docstring |
| term-mode theorem | `theorem t : … := sorry` |
| tactic theorem | `theorem t : … := by\n  sorry` |
| one-line hole inside given code | `let x : T := sorry  -- Hn: replace this whole line` |
| hole with no `sorry` (e.g. "write one notation line") | a comment-only block plus a blank answer line; a documented exception the hollow lint accepts |
| a hole that must stay open | label it loudly (`DO NOT SOLVE`) and state the exception in the Done line |

**Rules (MUST).**
- Each hole produces **exactly one** tool-counted diagnostic.
- The chapter states the total.
- If the reference for a hole runs past ~30 lines, split the exercise.

**Port: Dafny** [D:src, D:lit unless marked].
- **Proof hole.** A bodyless `lemma` with `ensures` in a *concrete* module. Verifying it emits the warning `This ensures clause is part of a bodyless lemma. Add the {:axiom} attribute to it or the enclosing lemma to suppress this warning`, and `dafny audit` reports `Ghost declaration has no body and has an ensures clause.`
- **One `ensures` per hole (MUST).** The warning is emitted **once per `ensures` clause**, not once per declaration: the check loops over the clauses (`foreach (var ensures in Ens)` in `MethodOrFunction.ResolveMethodOrFunction`) [D:src]. A hole declaration with two `ensures` lines would count as two holes. Either conjoin the postcondition into a single `ensures A && B`, or make the counter count declarations (dedupe warnings by enclosing declaration). The hollow lint enforces whichever rule the course picks.
- **`--allow-axioms` silences these warnings** (the same check is skipped when the option is set) [D:src]. It therefore belongs on the `vcheck` refusal list next to `--allow-warnings` (§11.4 G6).
- **Statement-level hole inside a body.** `assume false;` (warning: `assume statement has no {:axiom} annotation`; the wording is changing on master [D:lit]).
- **Holes are warnings, and warnings fail the command by default** (exit 2, "Compilation failed because warnings were found and --allow-warnings is false"). The learner loop therefore runs with `--allow-warnings`, and the done gate runs without it.
- **Never use `{:axiom}` as a hole.** It is silent in `verify` and would hide unfinished work.
- **Trap: a bodyless declaration inside an `abstract module` or a trait does not warn.** A learner who marks their own module `abstract` silences their holes. The lint MUST forbid it.
- **Function holes.**
  - A bodyless `function` **without** `ensures` is silent: it is simply uninterpreted (a fake-green vector, §11.4).
  - Give every function hole exactly one `ensures` (its spec), or ship it as a bodyless `method` with one `ensures`. The warning check sits in the base class that functions and methods share, so a bodyless function with `ensures` should warn like a lemma (`This ensures clause is part of a bodyless function…`) [D:src; confirm the wording in probe D1].
  - The static hollow lint additionally counts bodyless declarations.
- **Holes block compilation of their whole compile unit.** The Dafny compiler refuses bodyless methods, bodyless functions (ghost or not), bodyless lemmas and `assume` without `{:axiom}` [D:doc: Statements, "body-less" methods/lemmas/functions; UserGuide audit list]. Lean refuses to *evaluate* only the definitions that depend on `sorry`; Dafny refuses to `run`/`test` **anything** in a program that still contains one hole. Consequences, all MUST for a Dafny port:
  - executable checks over hole-dependent code stay commented, exactly as in Lean (§3.5), and become runnable only once their compile unit is hole-free;
  - a module's `dafny test` compile unit is **that module's file plus the given layers**, never the whole default project, so a hole in module 9 cannot block module 4's tests. In Dafny the import-mirroring rule (§3.1 rule 3) is therefore replaced by the re-supply rule: an exercise file imports only given layers, never an earlier exercise file;
  - `value` (exec) predict slots and every other executable check over *given* code run from specimens or from a given-only test unit (§3.8.6), never from the hole-bearing exercise file;
  - whether `--allow-warnings` changes any of this is [verify, probe D11].

```dafny
/** **H3.** Four turns return to the start. */
lemma FourTurns(d: Dir)
  ensures Turn(Turn(Turn(Turn(d)))) == d
// Hint(1): case-split on d; one `match` arm per constructor.
// Hint(2): which constructor follows West?
```

(Empty-body hazard: SMT may well prove `FourTurns` with `{}`. The empty-body gate, §2.8, would then reject this item as testing nothing.)

**Port: Verus** [V:src unless marked].
- **Holes are silent.** `admit()`, `assume(…)`, `#[verifier::external_body]`, `axiom fn` and `assume_specification` all verify green with no warning and exit 0.
- **The counter is a second run, `verus --no-cheating`.** It turns each of them into an error (`assume/admit not allowed with --no-cheating`, `external_body/assume_specification not allowed with --no-cheating`) and reports all of them in one run, as deferred errors.
- **Hole count = number of `--no-cheating` diagnostics.**
- **Labelled proof hole (recommended):** `#[verifier::proof_note("Q02.H3")] assume(false);`. In the **`--no-cheating --output-json`** run, the forbidden `assume` is reported with the note `note: Q02.H3`, and the label appears in that function's `func-details` → `failed_proof_notes` [V:src: `vir/src/well_formed.rs` AssertAssume check; test `test_json_proof_note_on_assume_with_no_cheating` in `rust_verify_test/tests/output_json.rs`]. In the ordinary run the `assume` succeeds and nothing is reported, so the hole counter MUST read the no-cheating run. Whether `proof_note` attaches to `admit()` is [verify], so use `assume(false)`.
- **Exec-body hole.** Use `#[verifier::external_body]` with an `unimplemented!()` body. It is green but trusted, and it panics if run, just as Lean's `#eval` of a sorried definition errors.

```rust
verus! {
/// **H3.** Four turns return to the start.
pub proof fn four_turns(d: Dir)
    ensures turn(turn(turn(turn(d)))) == d,
{
    #[verifier::proof_note("Q02.H3")] assume(false);   // HOLE: replace this line
    // Hint(1): match on d; one arm per variant.
}

/// **H4.** Implement the clockwise turn on the exec side.
#[verifier::external_body]                               // HOLE: remove this line and implement
pub fn turn_exec(d: &Dir) -> (r: Dir)
    ensures r == turn(*d),
{ unimplemented!() }
}
```

- **Spec-definition holes** (`uninterp spec fn`, or a body of `arbitrary()`) are **not** flagged by `--no-cheating`. Avoid them, or count them by lint.

### 3.4 Docstring = spec; hint grammar

- The **learner docstring is the contract**, written as a spec, often with a question ("Which test must come first, and why?"). The **twin's docstring explains** why the answer is right. Hollowing swaps one for the other. Given declarations keep identical docstrings in both files.
- **Hints go on line comments directly after the hole, never in the docstring:**

```
// Hint(1): one match arm per constructor of Dir.
//    Continuation lines indent three spaces after the comment leader.
// Hint(2): which constructor follows West?
```

- Use `Hint:` when there is only one hint. Item labels are bold: `**Exercise Na.**` (content track) or `**Hn.**` (depth track).
- A hint may give a *shape*, but never the twin's explanatory prose and never a leak-pattern string.
- The chapter states the dial rule: "read Hint(1) only when stuck, Hint(2) only when still stuck."

### 3.5 Commented checks, and why

**Lean mechanism.** A check that *runs* a definition containing `sorry` is an **error**, not a warning (`cannot evaluate code because '…' uses 'sorry'`). Live checks over holes would therefore make a fresh checkout red. So every check over hole-dependent code ships commented:

```
-- Uncomment as you go:
-- #guard turn Dir.north = Dir.east
-- -- prose inside a check block is written with a doubled comment leader
```

**Rules (MUST).**
- Checks over **given** code ship live.
- **Every non-prose line** under the `Uncomment as you go:` header counts as a *commented check* until it is uncommented. That includes executable checks, output pins, `example`s and theorems, not just one keyword. The strict gate fails while any remain. (A grep for one keyword missed commented examples; this was a real bug.)
- Deliberate failures shown for learning ship commented, with the instruction "uncomment / read the error / re-comment; this file must end green".

**Port.** The same rule holds in both targets, for the same reason [verify each]:
- **Dafny.** `dafny test` refuses to compile a program that contains any bodyless method, function or lemma, or an `assume` without `{:axiom}` [D:doc]; see §3.3 for the compile-unit rule this forces. A verification-level `assert F(3) == 9;` over an uninterpreted hole fails. So `{:test}` methods and `expect`/`assert` lines over holes ship commented inside a test method:

```dafny
method {:test} CheckTurn() {
  // Uncomment as you go:
  // expect Turn(North) == East;
  // expect Turn(Turn(Turn(Turn(West)))) == West;
}
```

- **Verus.** `#[test]` functions over an `external_body`/`unimplemented!()` stub panic. Ship them commented, or marked `#[ignore]` with the strict gate counting `#[ignore]` as commented. Proof-level `assert(...)` lines over hole lemmas ship commented inside a `proof fn`.

### 3.6 Worked examples (W items)

- **Content track.** A walkthrough ships as an indented code block inside the module doc comment, not as live code. Its output is quoted as "live-captured (v<toolchain>)", and the twin pins the same states.
- **Depth track.** W items are **live, given and finished**. Their outputs are pinned and their claims checked, so they stay silent while true. They may use given *checking tooling*; in Lean, that means goal assertions after each step.
- **Rule.** A worked example never prints an earlier hole's answer, and later files never print earlier answers.

**Port.** A W item is a verified given function or lemma plus pinned checks: executable tests for values, and golden-harness pins (§3.8.6) for any diagnostic it demonstrates. "Assert the goal at each step" becomes **intermediate `assert` statements that state what the verifier knows at that point**. This is the closest analogue of a goal display: an `assert` that verifies is a checked statement of the current knowledge.

### 3.7 Jurisdiction cards, WRITE vs RECOGNISE, receipts

- A **WRITE** construct is one the learner must use: ≥2 of the module's checked items (H, X or T) are tagged `uses: <slug>`.
  - It gets a **card** with *one success and one live failure, both pinned*, costing about 2.5 min inside the worked-example minutes.
  - **What a WRITE construct automates must already have been done by hand earlier**, at the level of the operation.
  - At most 6 WRITE constructs per concept module (7 in modules carrying the library strand).
- A **RECOGNISE** construct gets a card only: about 1.5 min, paid from reading time, never required in an item. It may be **promoted** to WRITE in a later module.
- **Banned lists** per module, enforced by lint over H/X/T blocks.
- **Card format:**

```
/*! ### C4 — card: `assert … by`
Jurisdiction: <the obligation shape this construct owns>. Success: <item ref>. Failure: <what breaks it>. */
// item: Q02.C4 S3 write:assert-by
<success example, verified>
<failure: pinned via the golden harness (§3.8.6); in Lean, an inline #guard_msgs block>
```

- **Receipts.** Every closing automation step carries `// did: <what it closed>`, on the same line or the line above:

```rust
assert(x * y >= 0) by (nonlinear_arith)  // did: sign of a product of two naturals
    requires x >= 0, y >= 0;
```

Receipts are advisory in the learner report and required in twins by the reference lint. Search results and heavy automation count only once they are replaced by explicit steps.

**Port.** Dafny and Verus have no tactic language, so the WRITE/RECOGNISE schedule runs over **proof constructs and automation knobs** (slug lists in §11.1, rows "tactics"). "Automate only what was first done by hand" maps directly:
- `by (nonlinear_arith)` only after a hand proof of the same shape;
- Dafny auto-induction only after a manual inductive lemma written under `{:induction false}`;
- `broadcast use` groups only after explicit lemma calls.

### 3.8 Predict items

#### 3.8.1 Why predictions are checked

The learner commits a concrete prediction *before* seeing the tool's answer. The prediction is then checked mechanically, and its **first try** is recorded. This is the course's calibration signal, and it is what makes "predict, then the verifier referees" (the viva's signature move) honest. Content-track predictions were comment-only and unscored. The depth track made them machine-checked. **Port the machine-checked form.**

#### 3.8.2 Lean formats

| format | shipped (unfilled) | enabled (checked) |
|---|---|---|
| value | `example : e = sorry := sorry` | `example : e = <literal> := rfl` |
| goal | `-- SLOT: guard_target =ₛ ???` | the slot prefix removed |
| error | `-- SLOT: /-- ??? -/` above `#guard_msgs (drop all) in <cmd>` | `/-- <fragment> -/` above `#guard_msgs (substring := true) in <cmd>` |
| info | as error, on an info-producing command | as error |
| type | `-- SLOT: /-- info: ??? -/` above `#guard_msgs (drop all) in #check …` | exact whole-message match |
| verdict | `def pN : String := sorry` + `-- SLOT: #guard hash pN == <pin>` | the literal answer string + the live hash check |

- The "unfilled" column works because `#guard_msgs (drop all)` swallows a failing command's output. Unfilled slots therefore never redden the file and never show the answer in the editor.
- **Verdict items** cover answers that are not terms: exit codes, "prints/panics" tokens, audit rows, stage names. The answer form is fixed exactly in the docstring (tokens, order, separators). **Only the hash ships**, so the answer is never in plain text. Pins are re-made on every toolchain bump.
- **Error predicts use anonymous `example`, never a named declaration.** A failing named declaration is still added to the environment and pollutes later items.
- **The chapter shows the slot mechanics once per format** on throwaway expressions ("Slots, worked once per format").
- **Goal slots were dropped in practice.** A goal slot sits inside a proof, where the editor shows the answer as soon as the slot is typed. The same item was rebuilt as a type slot over an error message instead. **This is the canonical "the IDE reveals predict answers" lesson** (§9.6).

#### 3.8.3 Slot states

Every slot passes through three states:
1. **unfilled** (`???`, `= sorry :=`, or `:= sorry` for verdicts): as shipped; green; reveals nothing;
2. **filled-disabled**: the prediction is written, and nothing evaluates it yet;
3. **enabled**: checked by the build.

`check_course_map.py --items <ID> --json` reports each slot's `{format, line, state}`.

#### 3.8.4 Vacuity hazards and the slot lint (each verified live in Lean)

| # | hazard | lint rule |
|---|---|---|
| H1 | an **empty** substring pin passes on any output | fragment payload ≥ **8 non-space characters** after stripping any severity prefix |
| H2 | **echo**: many messages repeat the command, so a fragment copied from the command passes; a value slot passes if the learner retypes the left-hand side | a value right-hand side must be a literal of the form the docstring declares on a fixed line, `Answer form: numeral \| constructors \| Option/Bool/String/Char literal` (L: `scripts/q_firsttry.sh:72-74, 115`), and never the left-hand side again; an error fragment must not occur in its own item's source |
| H3 | a **severity prefix** inside a substring (`error: …`) makes a correct prediction fail | fragments never start with `error:`/`warning:`/`info:`/`trace:` (port: also `Error:`/`Warning:`) |
| H4 | output-suppression in honest code is a fake-green technique | suppression appears only directly under a `SLOT:` line in a P/X block; twins never use it |
| H5 | a wrong substring prediction **re-emits the real message**, revealing the answer | record the first try **before** enabling (§3.8.5) |
| H6 | twins with leftover slots | twins contain zero `SLOT:`, zero `???`, zero unfilled forms |

The first-try recorder refuses to enable or record a slot that breaks rules H1–H3, and the report counts it as **vacuous**, so the strict gate fails. The reference lint applies the same rules to twins, **from one shared implementation**: the reference lint loads the "SHARED SLOT RULES" section of the learner gate script by marker lines.

#### 3.8.5 First-try calibration (`scripts/firsttry.sh`)

| mode | behaviour |
|---|---|
| `--check` | Enables every filled-disabled slot **in a temporary copy** under a gitignored scratch directory, runs the tool, and prints ✓/✗ per item. Appends one TAB-separated line `item  kind  verdict  date  slot-hash` to the append-only `instructor/calib/<ID>.tsv`, where `kind` ∈ {`predict` (filled but not yet enabled: a genuine first try), `observed` (a slot was already enabled, so the learner may have seen the answer: shown, never counted as a pass), `exit` (the first `--exit` run at which every exit item holds an attempt)}, `verdict` ∈ {`pass`, `fail`}, and `slot-hash` is the sha256 of the normalized slot text (L: `CORE.md` "instructor/calib"). **An item's first record wins.** It never edits the learner's file. It refuses, recording nothing, a slot that breaks a lint rule and an item with fewer slots than it shipped with. |
| `--report [--strict]` | Counts unfilled, missing, vacuous, commented-check and banned-construct items, plus unrecorded first tries, and prints the first-try percentage. `--strict` exits 1 on any of them and is the module's **done gate**. The "as shipped" baseline is the file at the merge base with `main`, so **deleting a slot cannot pass for filling it**. |
| `--record` | Appends one gradebook `calib` row (first-try rate and exit score). Only the script writes it, never a tutor. |
| `--exit` | Scores the closed-book exit (§3.10). |
| `--lint-hollow` | **Static: never runs the tool.** Checks that every exercise file ships hollow. Runs in a cheap CI job. |
| (port) `--empty-body` | Author/CI: replaces every hole with an empty body and maximal automation and requires each one to **fail** (§2.8). |

Exit codes: 0 ok, 1 failed, 2 usage, 3 refused (unknown id, planned module, missing file).

**Learner-side commit rule.** Commit a prediction **before** hovering over, clicking into, or running the code it is about, and before opening later files, the registry, CI or the plan. A CALIBRATION comment block at the end of the main exercise file records planned vs actual minutes per budget line. It is learner-owned and no script reads it.

#### 3.8.6 Port: formats, the golden harness, and specimens

There is **no in-file output pin** (`#guard_msgs`) in Dafny or Verus, and **no silent-slot mechanism** (`drop all`). Both research passes concluded this; [verify] that no newer release adds one. A failing assertion inside an exercise file makes the whole file red. The port therefore needs four things:
1. **specimen files** for every item whose answer is a diagnostic;
2. a **golden harness**, `scripts/pins.py`;
3. a **slot file** per module, or slots in specimen headers;
4. a reduced format set.

**Specimens.**
- A specimen is a small standalone file, one item per file, under `Course/specimens/<ID>/`.
- It ships with an extension the IDE ignores (`P4.dfy.specimen`, `P4.rs.specimen`), so the editor never verifies it and never shows the answer before the prediction is committed [verify: the IDE extension's file association].
- The harness copies it to scratch with the real extension, runs the pinned verifier with JSON diagnostics, normalizes the output, and compares it against the expectation.
- Specimens are never in a build root. This is rule 3.1-2 applied at item granularity.

**Port format set:**

| format | what is predicted | shipped (unfilled) | enabled | checked by |
|---|---|---|---|---|
| `value` (exec) | the result of running given code | inside a test method: `// SLOT: expect Turn(Turn(North)) == ???;` (Dafny: in a specimen or a given-only test unit, never in the hole-bearing exercise file, §3.3) / `// SLOT: assert_eq!(turn_exec(&Dir::North), ???);` in a `#[test]` (Verus) | the slot prefix removed, literal filled | `dafny test --methods-to-test <name>` on that unit [D:src] / `cargo test <name>` [verify, probe P6 in §11.6] |
| `value` (spec) | the value of a spec function | Verus: `// SLOT: assert(to_nat(seq![true,false,true]) == ???) by (compute_only);` | uncommented | `verus` (`compute_only` evaluates in Verus's interpreter) [V:doc]. Dafny: prefer `value` (exec) via a compiled `function`; a static `assert F(3) == ???` is proved by SMT and may fail on fuel, so it predicts the verifier, not the value [D:doc] |
| `obligation` | **which** labelled obligations in a specimen fail | candidate lines carry labels `// [a]`, `// [b]`…; header slot `// SLOT: FAILS ???` | `// FAILS a c` | harness maps JSON diagnostics to labelled lines and compares the **sets**. Verus MAY use `proof_note` ids and `failed_proof_notes` instead [V:src] |
| `error` | the line and a message fragment of a diagnostic | header slot `// SLOT: EXPECT @??? "???"` | `// EXPECT @12 "could not be proved"` | harness: a diagnostic on that line whose message contains the fragment (rules H1–H3 apply) |
| `verdict` | any non-code answer: exit code, stage name, audit rows, which trigger the verifier picks, "verifies / errors / times out" | slot file line `P5 = ???` + shipped `sha256` pin | `P5 = "4 2 0"` | harness compares the hash of the normalized string |

- **Dropped formats.** `goal` (no goal state) and `type`/`info` (no `#check`, and no info messages to speak of). Their pedagogical job moves to `obligation` ("which assertion fails, and why?") and to `verdict`.

**Worked shapes (invented; recommended port layout).** The source course has no port of these files, so the layout below is this spec's recommendation, not a copy. Each shape keeps the source's invariants: the item marker, a docstring that fixes the answer form, one `SLOT:` line per slot, and nothing that reveals the answer before enabling.

A `value` item in a given-only Dafny test unit (`Course/checks/Q04_checks.dfy`, which includes no exercise file):
```dafny
// item: Q04.P2 S1 value
/** **P2.** What does `Turn(Turn(North))` return?
    Answer form: constructors */
method {:test} P2() {
  // SLOT: expect Turn(Turn(North)) == ???;
}
```

An `obligation` specimen (`Course/specimens/Q04/P5.dfy.specimen`); the learner fills only the header line:
```dafny
// item: Q04.P5 S3 obligation
// Which of the labelled assertions does the verifier fail to prove? Answer form: `FAILS` followed by the failing labels in label order, e.g. `FAILS x y`.
// SLOT: FAILS ???
method Demo(a: array<int>, i: int)
  requires 0 <= i < a.Length
{
  assert a[i] == a[i];          // [a]
  assert a[i+1] >= a[i];        // [b]
  assert i < a.Length;          // [c]
}
```

A `verdict` item. The prompt lives in the exercise file; the learner's answer goes in the module's slot file, and only its hash ships:
```
// in Course/Q04_ProofCraft.dfy
// item: Q04.P7 S3 verdict
// **P7.** Run `scripts/vcheck --gate` on the planted file. Answer form: "<exit code> <error count> <hole count>",
//          three integers separated by single spaces.

# Course/slots/Q04.slots   (learner-owned; one line per verdict slot)
P7 = ???                          → filled: P7 = "2 1 3"

# expected/Q04.pins        (author-written, CI-checked; never the answer itself)
P7  sha256 <64-hex of the normalized answer: trimmed, internal whitespace collapsed to one space>
```

An exit (`X`) item with a `need:` line, so deleting the target cannot pass:
```dafny
// item: Q04.X2 S4
// need: lemma SumUpTo(n: nat)
// need: ensures Sum(n) == n * (n + 1) / 2
/** **X2.** Prove the closed form of `Sum` by induction (at most 8 lines). */
lemma SumUpTo(n: nat)
  ensures Sum(n) == n * (n + 1) / 2
// (empty: the learner writes the body)
```

- **The re-emission hazard (H5) still exists** once the learner runs the specimen. The rule is unchanged: `firsttry.sh --check` records the first try in scratch before the learner sees any output.
- **What the harness also runs.** The same harness, in author/CI mode, checks every **pinned** output the course quotes: W items, card failures, demo files, chapter fences. This is the "never invent output, and drift fails the build" guarantee that `#guard_msgs` gives Lean. Expectations live in-file as `// EXPECT @<line> "<fragment>"` headers, or as normalized `.expect` sidecars for whole-file goldens.
- **Normalization.** Strip absolute paths (Dafny `--use-basename-for-filename` [D:src]); redact timings; drop Verus build-info blocks; sort diagnostics by position.
- **Precedents.** Dafny's own suite uses LLVM `lit` with `// RUN:` lines and `.expect` files, and its reference manual checks fenced examples against named `.expect` files via `<!-- %check-verify X.expect -->` [D:lit, D:doc]. Verus's test suite marks expected-failure lines with `// FAILS` comments [V:src].

### 3.9 Item markers

**Grammar** (port: comment leader `//`):

```
// item: <ID>.<K><n> S<k> [<format>|write:<slug>|recognise:<slug>] [min=<m>]
// uses: <slug>[, <slug>…]          (H, X, T only; zero or more lines)
// need: <target fragment>          (X only; zero or more lines)
<closing automation step>  // did: <what it closed>
```

**Anchored regex (port):**
`^// item: ([RQ]\d\d)\.([WCPHXTA])([1-9]\d*) S([1-9]|1[0-2])(?: (value|obligation|error|verdict|write:[a-z0-9_/-]+|recognise:[a-z0-9_/-]+))?(?: min=([1-9]\d*))?$`

| K | kind | checked | cited in the concept matrix | may carry `uses:` | minutes line |
|---|---|---|---|---|---|
| W | worked example (given, live, outputs pinned) | given | no | no | worked |
| C | card (`write:`/`recognise:`) | given pins | no | no | worked / cards |
| P | predict | once enabled | **yes (must)** | no | predict |
| H | one-hole item (in the hard tier, a hard problem) | yes | **yes (must)** | yes | holes |
| X | exit / closed-book item | yes | **yes (must)** | yes | exit |
| T | pretest / test-out | yes | **yes (must)** | yes | pretest |
| A | agent-ladder run | contract acceptance | only where learner-written checked lines exist | no | agent |

**Rules:**
- Ids are unpadded (`Q01.P5`). They are unique per module and **identical in the learner file and its twin**, because hollowing keeps comments.
- P items require a format, and C items require `write:` or `recognise:`. X and T items MAY carry `verdict`. `min=` appears only on multi-slot X items.
- `S<k>` must be one of the module's registry strands.
- **Block extent.** A block runs from its `item:` line to the next `item:` line, the next doc-comment header, the module/namespace end, or end of file. A `uses:` outside a block, or on a W/C/P/A block, is an error.
- **`need:`** (X only) quotes a fragment of the prompt's own target (statement or signature), never the answer's method. An exit block passes only if every `need:` fragment occurs, after whitespace normalization, in its non-comment code. **This stops "pass by deleting the target".** The reference lint checks that the twin satisfies its own `need:` lines.
- **`uses:` slugs.** Spaces become `-`; `/` joins alternatives that fill one slot (`cases/obtain`). A `uses:` construct must be WRITE or RECOGNISE in this module or an earlier one.
- Other id families live in other files and never collide with item ids: `K` (bank questions), `PP` (parallel problems), rubric line labels, `S` (strands).
- **One parser** (`check_course_map.py --items <ID> --json`) feeds the first-try gate, the reference lint and the coverage check. Its output per item is `{id, kind, n, strand, format, min, uses[], need[], file, line_start, line_end, slots:[{format, line, state}]}`.

### 3.10 Exit files, thresholds, pretests and test-out

**Exit file** (one per depth-track module; not in the build):
- **The header states:**
  - what stays closed: the chapter, the exercise file, later modules' files, search tools and `/tutor`; at most the given spine may be open;
  - the exact shipped hole count;
  - the scoring command and threshold;
  - that **the first full run is the score**, with repairs afterwards.
- **Two forms:**
  - *Prompt-as-heading*: the prompt is the `### X1 · S1 — <prompt>` heading, the block below it is empty, and the learner writes at most three lines.
  - *Statement-shipped*: signature and checks ship with a hole, and `need:` lines quote them.
- **Scoring** (`firsttry.sh <ID> --exit`):
  - Nothing is recorded while any block is unattempted. A guess counts as an attempt; an empty block or a hole does not.
  - A block passes when it is non-empty and has no error, no hole, no slot, no commented check, and every `need:` fragment present.
  - The first complete run is recorded in the calib TSV.
  - Thresholds are hard-coded: survey **≥9/12**, intro **≥5/6**, moderate and detailed **≥3/4**.
  - Output: `<ID> exit: n/N (threshold t) PASS|FAIL`.
- **After scoring**, the learner repairs every block, and from then on the strict gate covers the exit file too.
- **Port note.** Each exit block that might fail must be independently checkable: one failing block must not mask the others. Use one specimen-style file per block, or verify per symbol (Dafny `--filter-symbol` [D:src]; Verus `--verify-function` together with `--verify-only-module` [V:src]). The harness, not the learner, chooses the filter. Filters are a fake-green vector in learner hands (§11.4).

**Pretests / test-out (T items).**
- T items come first, are closed-book, and sit before any reading.
- If all are right on the first run without opening their hints, the learner may skip a named chapter section and its worked example. Listed items stay mandatory.
- A T item may be a hole or a verdict.

**Tier gates** combine machine checks (pass/fail) with advisory checks: exit thresholds, the tier viva, predicted audit rows confirmed, explain-backs.

### 3.11 Agentic files

#### 3.11.1 The four shapes

| shape | shipped state | in the build? | the learner's exercise afterwards |
|---|---|---|---|
| **planted-error repair** | RED: exactly *k* documented errors, one diagnostic each | no | audit the transcript and the diff: one-line fixes, a re-run after every edit, the spec untouched |
| **spec-first** (signatures + doc contracts + a live check suite; hole bodies) | RED: every live check errors over its hole | no | write adversarial checks the shipped suite never exercised; the doc contract is deliberately stronger than the suite, which has **planted soft spots** |
| **green-with-holes bank** (statements with holes + a live **audit dashboard**) | green with warnings; the dashboard shows one hole row per open statement | **yes**, in a sub-namespace | read the dashboard, check the `git diff` for scope, check the transcript for method clauses |
| **forensic / fake-green** | GREEN and silent except the dashboard; every check passes; the content is worthless | no | diagnose each delivery (verdict + detection instrument + root cause) **before** repairing |

**Shape-specific rules.**
- **Planted-error repair.**
  - Section headings are neutral (`### Bug 1` … `### Bug 5`).
  - The doc comment states the *intended* behaviour.
  - Each bug has a **distinct error class** and produces **one diagnostic**, so error count = bug count.
  - The one bug that elaborates but is *wrong* has its check **live from the start**, so it also shows exactly one error. Checks on bugs that fail to elaborate start commented, to avoid noise errors.
  - Every fix is one line, or one added line.
  - The chapter reproduces the full error list with real `file:line:col`.
  - **Port hazard: stage masking.** Lean keeps elaborating after errors. Dafny stops before verification when parsing or resolution fails, and Verus stops before verification on a rustc error [verify; D:doc exit-code stages 1–4; V:src]. So either plant bugs from a single stage per file, or make the stage ordering the lesson: the learner predicts which errors appear after each fix.
- **Spec-first.**
  - The suite's soft spots are recorded only in the twin's author note.
  - The chapter shows a gamed implementation passing the shipped checks and failing the adversarial ones.
  - A trailing slot holds the learner's adversarial checks.
  - The depth-track variant adds a feedback-channel discipline (fast channel only, plus one final full build) and a LATENCY LOG the learner fills from the transcript.
- **Green-with-holes bank.**
  - The dashboard is one assumption-audit row per statement (Lean: `#print axioms` per theorem).
  - The prose names **what the dashboard cannot see**: method clauses (which proof constructs were allowed, constructive-only rules, feedback discipline). Those live in the diff and the transcript. *An off-kit proof can be correct, green and audit-clean and still breach the contract.*
- **Forensic / fake-green.** See §3.14.

#### 3.11.2 The CONTRACT header: the one format `/contract` parses

```dafny
/* CONTRACT
goal: <one line: what to deliver>
allowed-files:
  - Course/Q01_AgentRepair.dfy
acceptance:
  - `scripts/vcheck --gate Course/Q01_AgentRepair.dfy` exits 0 and prints only the summary line
  - every check passes; signatures, requires/ensures/invariant/decreases lines, doc comments and checks are unedited (`git diff` shows only bodies)
  - zero holes in the allowed file (tool-counted)
  - per-edit feedback only from the fast channel; exactly one full gate run, last
  - `scripts/vaudit Course/Q01_AgentRepair.dfy` matches expected/Q01_AgentRepair.audit (0 findings)
*/
```

The same block opens a Verus file, before `use vstd::prelude::*;`.

**Rules (MUST):**
- The block is on **line 1**, before any import, and it must not break the file. (In Lean, a plain block comment before `import` was verified to elaborate.)
- **Exactly three keys**: `goal:`, `allowed-files:`, `acceptance:`. Every method clause (feedback discipline, one-line fixes, no delegation, allowed proof constructs, "the body of X mentions neither Y nor Z") is an extra `acceptance:` bullet, so the parser's keys never change.
- `allowed-files` entries are **exact repo-relative paths**. They must never name a spine/given file, a solo-tree path or a reference path; the skill and the hook both reject such entries.
- If the block is missing or malformed, the contractor **stops and reports**; it never guesses scope.
- The source course also has a legacy R-track form (contract prose inside the module doc). It is flagged as a format conflict ("do not invent a third form"). **Use the canonical three-key block from day one.**

#### 3.11.3 Agentic body template

```
/*!
# <ID> <Lab name> — <role> (`/contract <ID>`)

<what the file ships and its EXACT shipped state, e.g. "exit code 2 with 4 errors and 1 hole
warning, one message per bug"; the check command indented four spaces:>

    scripts/vcheck --gate Course/Q01_AgentRepair.dfy

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. Before the run: execute the command and read every message.
2. In a FRESH session, run /contract <ID>.
3. Tally the transcript: re-ran after every edit? touched a spec line? reached for an escape hatch?
4. Check the artifact yourself: command output, `git diff` scope, audit output.
5. <module-specific demo or seed for a later module>
*/
// item: <ID>.A1 S<k>
…
```

The learner's main exercise file ends with a pointer section, `## Exercise (AGENTIC) — <role>`. It names the agent file, its shipped state, the check command, the numbered steps and the closing lesson.

### 3.12 Given and frozen files

- **Header.** `# <id> — <name> (PROVIDED, complete)`, then "This file is provided infrastructure, not an exercise: there is nothing to fill in and nothing here is a hole", then an **"Imported by:"** list. Files with planted holes or fakes say so in place of "complete".
- **Live checks on given code** MUST avoid every value a later predict asks for.
- **Scaffolds.** When the author finds that a first-time learner "cannot reasonably be expected to derive" something, it ships as `SCAFFOLD n`. Each scaffold carries its **receipt**: the live-captured error you get without it. The header also says what is deliberately *not* in the file, and that reading it spoils nothing.
- **Skeleton scripts** for interface labs (an LSP client, an agent loop) ship with the plumbing done and the protocol work as `TODO`s, plus a no-toolchain fallback ("do the lab on paper").
- **Given demo files** (planted holes, fake-green audits) have no twin. The registry declares them as files of the module, never as exercises, and CI pins their output.

### 3.13 Reference twins and hollowing

**Twin anatomy.**
- Header: `# <ID> — <title> (Reference Solution)`, then "hole-free reference for `<exercise path>`".
- It states that every quoted output is pinned, and that the file is **silent**: the gate command prints only its summary line.
- Pin formats in Lean: info pins on `#check`/`#eval`, error pins on failing `example`s, trace pins for goal states, and **every learner theorem's audit row pinned**, with the real row (some statements legitimately use standard axioms). Port: harness pins (§3.8.6) and a pinned per-file audit report.
- **Agent reference section** at the end, under a loud heading: `### — clearly marked: everything below answers the agentic file —`. It contains a sub-module or namespace with the reference delivery, the shipped suite verbatim, the adversarial examples, and an author's note on the planted soft spots. It is the "proof that the contract is satisfiable as stated".

**Hollowing table:**

| element | twin | learner file |
|---|---|---|
| imports | previous *twin* + given layers | previous *exercise* + the same given layers |
| header | "(Reference Solution)" | "(Exercises)" + how-to list + agentic/exit pointers |
| namespaces, sections, options, item markers, `uses:`/`need:` | identical | identical |
| given types, fixtures, W/C items and their live pins | identical | identical |
| names, signatures, statements, order | identical | identical |
| hole bodies | complete | shipped hole form (§3.3) |
| hole docstring | explanation | `**Hn.**` spec (+ question) |
| hints | none | `Hint(1)/(2)` comments |
| checks over hole-dependent code | live, plus extra edge checks | `Uncomment as you go:` + commented checks |
| output pins over hole-dependent output | live | removed: replaced by Q/A slots, quoted "live-captured" output, or a P slot |
| deliberate failures | live, pinned | commented, with uncomment/read/re-comment instructions |
| P slots | enabled | unfilled |
| audit pins of learner statements | live | removed (the learner pins them; a rubric gate checks) |
| `did:` receipts | present | only in given code |
| agent reference section | present | absent; replaced by the AGENTIC pointer |
| solution-distinctive strings | anywhere | **must not survive** (leak-pattern check) |

**Verification:**
- the declaration list equals the twin's, except for documented exceptions;
- the shipped hole count equals the chapter's number and the CI pin;
- the hollow lint passes;
- the leak patterns match nothing public;
- the reference lint passes, printing **locations only, never content**.

### 3.14 Fake-green forensics fixtures

A forensic file holds several "deliveries". **Each is green, and each is worthless in a different way**, so each needs a different detection instrument. In the Lean species catalog:

| species | Lean example | instrument |
|---|---|---|
| hole | `sorry` hidden in a helper, its warning suppressed | transitive axiom audit |
| rogue | a user `axiom` | axiom audit |
| native | trusting compiled evaluation (`native_decide`) | the audit shows a native axiom |
| vacuous | contradictory hypotheses | "swap the conclusion for `False`" (if it still proves, the context is vacuous); a satisfiability witness |
| semantic hallucination | a true, proved, useless statement | read the statement; evaluate on inputs the delivery's own tests avoided; a property sampler |
| healthy | a decoy | everything passes |

**Contract rules for a forensic run:**
1. Diagnose all deliveries before repairing any.
2. "Comments, doc strings and names are contractor prose: unchecked, and in places misleading; only the tool's own output counts as evidence."
3. **N catches must use N different methods.**

A fixed-width **DIAGNOSIS** form asks, per item: statement true? proof valid? theorem useful? detection method? root cause?

The forensic file is not in the build, so its holes and trust leaps stay out of the root build and out of the code-review gate.

**Port.** The Dafny and Verus species catalogs (§11.4) are larger than Lean's, which makes this exercise *richer* in the port. Recommended species vocabulary for the DIAGNOSIS form: `hole | trusted | unchecked | vacuous | weak | healthy`, where `unchecked` means code the verifier never saw.

### 3.15 Chapter quoting rules (real output only)

1. Source goes in a language fence, and output goes in a **bare** fence directly below. Tool output is never in a language fence.
2. **Position prefixes show provenance.** Output from a repo file keeps its real `path:line:col`, which must match the shipped file; scratch output uses neutral names (`probe.dfy`); harness-pinned output is shown without a position.
3. A command line may lead a block: `$ dafny verify …`.
4. Truncate only with `...` plus what was cut ("ten such errors in all, one per check").
5. Use provenance tags: "Live-captured (<tool> <version>)", "verbatim", "pinned in the reference so it can never drift".
6. Add **variability caveats** for volatile tokens. Explain internal names; don't hide them.
7. **Read the error aloud** after quoting it: a numbered dissection of what failed, what it needed, and where.
8. Every scratch snippet whose output is quoted runs with the module's exact pinned flags.
9. **Chapter line numbers are live data.** Any edit to a quoted file means re-capturing the chapter.
10. **Diagrams.** Use 3–5 mermaid diagrams per chapter, with quoted labels; mark "not yet" parts with a ghost style; frame each diagram with a sentence before and a takeaway after; node ids never look like module ids.

---

## 4. The written track

### 4.1 Files and build

- Each module with a written track has `paper/<ID>_problems.tex` (the statements) and `paper/<ID>_answers.tex` (a skeleton the learner fills in), copied from the shipped `template_problems.tex` / `template_answers.tex`, which `make paper` does not build. A shared `preamble.tex` holds the macros for judgments and inference rules (`mathpartir`), code listings, and colour.
- **`make -C paper paper`** builds only the `[RQ]NN_problems.tex` and `[RQ]NN_answers.tex` pairs. It **fails on an empty glob**, because an empty match set means the glob is broken, not that the track is green. This green build is the written track's own "done".
- **`make -C paper paper-solutions`** is for CI and the author only. It builds `paper/solutions/`, writes each latexmk log into the read-denied tree, and prints only `built N` or the names of failing files. "`paper` never touches solutions/, so a learner's (or a study-mode Claude session's) build cannot compile or print a reference solution." The hook blocks Claude from running `paper-solutions` (rule 1b).

### 4.2 Problem types

Each problem is `\begin{problem}[<type>]…\label{prob:Pn}`. There are three types:

- **`[hand-calculation]`**: by-hand derivations whose result a tool can recompute. **Port:** weakest-precondition calculation, VC derivation for a small loop, unfolding a recursive spec function a few steps, "what does the verifier know after this line?", trigger matching by hand.
- **`[informal-proof-first]`**: an informal proof of something that will later be formalized. The problem MUST say what will be formalized, because **the learner's LaTeX proof becomes the agent's blueprint**.
- **`[concept]`**: short answers that the grader actively tries to counterexample.

The written track runs only where it pays. The content track skips it in modules where it would be filler. The depth track uses a few short items, the hard-tier blueprints, the challenge blueprints and one sketch.

### 4.3 The answer skeleton

There is one `\section*{Problem Pn (<type>)}\label{ans:Pn}` plus an `answer` environment per problem. The informal-proof-first skeleton asks for:

```
Statement:
Induction on:                (port: "Induction on / loop invariant / decreases measure:")
Base:
IH (stated as a formula):    (port: "IH or invariant (stated as a formula):")
Step:
Helper lemmas needed (this is the blueprint):
Gaps I know about:
```

### 4.4 Blueprints: before and after formalization

- **Pre pass** (`/grade-paper <ID>`, run after `make paper` is green and BEFORE formalizing). The grader scores the blueprint. Its **gap list predicts where the formal proof will stall**; the source calls this "blueprint-hardening".
- **Post pass** (`/grade-paper <ID> --post`, run after the learner's own formal proof is done). It re-scores only `blueprint-quality`, by diffing the paper decomposition against the learner's machine-checked proof: which helpers the paper predicted versus which the proof needed, where the step order survived, and where formalization forced a generalization. **The oracle is the learner's own artifact, never `Solutions/`**, so the grader never needs the reference.
- **The blueprint gate.** In the hard tier and the capstone, the agent co-developer receives the blueprint **only after it has been graded ≥3 on every dimension**. The graded blueprint is what the agent formalizes.
- **Author rule.** Every informal-proof-first *reference* solution MUST match the structure of the formal reference it precedes, because it doubles as a blueprint.
- **Flagship pattern.** The written proof reveals the missing helper lemma exactly where the formal proof stalls. In the capstone, the plain induction hypothesis fails and the learner **discovers the generalized one on paper** before any formal work.

### 4.5 Grading rules and the margin grammar

**Dimensions.**
- Informal proofs: `statement-fidelity`, `induction-soundness` (the IH is stated as a formula and used only at an instance it provides), `case-exhaustiveness`, `blueprint-quality` (the operational test: "could a contractor formalize this without inventing any statement?"), and `gap-accounting` (declared gaps score 3; undeclared holes are flaws once confirmed).
- Hand calculations: `recomputation`, done with tool anchors and diffed step by step, "never by eye".
- Concept answers: `correctness`. The grader actively tries to counterexample the claim, and a claim that survives scores ≥3.
- A rubric may declare its own dimension labels. They are used verbatim, never invented.

**Scale.** 4 = correct and well-formed; 3 = correct with minor *declared* gaps; 2 = a confirmed flaw; 1 = fundamentally broken or missing.

**Verdict rules (MUST).**
- **The per-problem grade is the minimum across dimensions**, because "averages hide holes".
- **Confirmed flaw, or it's a gap.** A score ≤2 MUST exhibit a concrete failing instance; otherwise the item scores 3 and is recorded as a gap. "A hallucinated flaw in a correct proof erodes trust faster than a miss." **Port:** "the verifier could not prove it" is NOT a failing instance (§6.5).
- A gap flagged in an earlier gradebook row is graded as a flaw candidate: hunt for its failing instance.

**Margin grammar.**

```
% GRADER[<Pn>][<dimension>][<1-4>]: <one line; the failing instance when the score is <= 2>
```

The grader cannot edit the learner's answers file; the hook forbids it. It therefore delivers every margin line in `instructor/feedback/<ID>_paper.md`, keyed to the `\label{ans:Pn}` anchor, ready to paste. The report holds a per-problem dimension table, every GRADER line, and a three-sentence summary naming the single highest-leverage fix.

### 4.6 Rubrics

The rubric file is `paper/rubrics/<ID>_rubric.md`. Every core module has one, written track or not; a challenge module has one only where it has a written item (blueprint or sketch), and its defense sheet and gate do the rest (registry `rubric = ""`).

- **Learner-visible by design.** "Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a kernel anchor (a command whose output settles the question)." Example stance: it "verifies that a bridging lemma is *stated* without ever stating one". Anchors restate only material already printed in the problem file or the exercise comments.
- **Advisory status** is stated in the header. A tool check outranks the rubric, and the learner may dispute any finding **at the labelled-line level**. That is why every line has a label (`SF.a`, `IS.c`, `C3`).
- **Layout:**
  1. Title, plus a header covering consumers, stance and advisory status.
  2. **Pinned sources with sha256 pins:**
     ```
     Solution pins (CI compares on every change; stale pins fail the build):
     Solutions/R06_Induction.dfy  sha256 <64-hex | PENDING>
     ```
     Rubric authors cannot read the reference, so they write `PENDING`. `scripts/update_rubric_pins.sh`, run by the author or CI where no permission layer applies, fills in the hash. `--check` fails CI on a pending, stale or **missing** target, because a renamed target must fail loudly. Pins may also target learner files.
  3. `## Kernel anchors` (port: `## Verifier anchors`): named probes (Probe A, A′, B…), each tied to a problem, with a run recipe for `instructor/scratch/`. This section includes *splice templates*: a probe into which the learner's own helper statement is pasted, to check that it is general enough to formalize.
  4. Per problem: `## P<n> — <title> (<type>; dimension: <label>)`, one `###` per dimension, labelled predicate lines. A predicate that can drive a score ≤2 says exactly what must be exhibited.
  5. `## The --post pass`: what to diff, and the gradebook delta.
  6. `## Gate`: mechanical preconditions for code review, each with a tool anchor.
  7. `## Code-review focus — <band>`: lines C1…Cn at the module's bar, with explicit "do not invent a flaw" clauses (for example, "if every check passes, the order is correct — do not invent a flaw"; "a *wrong* prediction left visible is a feature, never a finding").
  8. `## Audit debrief — after /contract <ID>`: questions D1…Dn for the learner. Each is settled by the transcript, the artifact or a tool anchor, and "none has a secret answer".
  9. Optional gate banner, a fixed first line: `GATE R16: OPEN — …` or `GATE R16: HELD — <dimension> at <score>`. It is still advisory: "a dispute that produces a machine-checked instance wins".
- **Label grammar.** Dimension predicates carry a dimension prefix and a letter (`SF.a`, `IS.c`, `CE.b`). Code-review, debrief and other numbered lines are written `- **<L><n> — <title>.**`, with `<L>` one or more capitals (`C3`, `D2`); in the depth track the checker's I5 rule accepts only `C/D/A/B<n>` for rubric lines and `K<n>`/`PP<n>` for bank headings (L: `check_course_map.py:71-75, 972-973`).

An invented skeleton (no predicate states an answer):
```markdown
# Q04 rubric — Proof craft & libraries
> Consumers: /review-code, the /contract debrief. Every line is a predicate about your artifacts, never an answer.
> Advisory: a verifier check outranks any line here; dispute a finding by its label.

Solution pins (CI compares on every change; stale pins fail the build):
Solutions/Q04_ProofCraft.dfy  sha256 PENDING

## Verifier anchors
- **Probe A** (H3): paste your helper's statement into `instructor/scratch/probe.dfy` below the given
  `Sum`; run `scripts/vcheck instructor/scratch/probe.dfy`. The anchor is the exit code, never a solutions file.

## Gate
- **A1 — holes.** `scripts/vcheck --gate Course/Q04_ProofCraft.dfy` reports 0 holes (tool-counted).

## Code-review focus — band: "proof-shape"
- **C1 — loop invariants name the processed prefix.** Anchor: the verifier accepts the loop with no extra `assert`.
- **C2 — no dead assertions.** Anchor: `--warn-redundant-assumptions` reports nothing. If it is silent, do not invent a flaw.

## Audit debrief — after /contract Q04
- **D1 — did the contractor touch a spec line?** Settled by `git diff -U0 -- Course/Q04_AgentRetriever.dfy`.
```

### 4.7 Calibration fixtures

For every written module, the author writes two fixtures under `tests/instructor/fixtures/`:

- **`<ID>_flawed_answers.tex`**: a drop-in replacement for the answers file with planted flaws. Its header comment states the **expected outcome per line**, in the GRADER grammar, and deliberately includes **one clean problem**, so the flawed file also tests for false positives:

```
% <ID>_flawed_answers.tex — GRADER CALIBRATION FIXTURE (deliberately flawed).
% EXPECTED[P1][induction-soundness][2]: <the planted flaw and where; the failing instance the report must exhibit>
% EXPECTED[P2][correctness][4]: correct, no finding. A grader that reports a flaw on P2 is hallucinating.
% Expected per-problem grades (min across dimensions): P1 = 2, P2 = 4.
% A calibration run FAILS if P1 scores >= 3, if the P1 finding does not locate the planted step,
% or if ANY flaw is reported on P2.
```

- **`<ID>_gold_answers.tex`**: correct, but **deliberately paraphrased away from the reference**, so the grader must recognise correctness by substance, not by matching wording. This is the false-positive guard.

How they are used is in §6.12.

---

## 5. Agentic exercises

### 5.1 The role ladder

| content-track module | depth-track module | role | what the learner does (the actual exercise) |
|---|---|---|---|
| 1 | Q01 | **repairer** + hook-deny demo | runs the planted-error file; starts a fresh `/contract`; tallies the transcript (re-ran after every edit? touched a spec line? reached for an escape hatch?); checks the artifact and `git diff`; asks the AI for a solution through **three doors** (file read, shell, language-server tool) and records which guard layer refuses each |
| 2–3 | Q02 | **implementer vs checks** | spec first; the agent is restricted to the fast channel plus one final full verdict; the learner logs fast-vs-slow latency, then adds adversarial checks the agent might have gamed |
| 1/15 | Q03 | **contract author v0** | writes contract v0 by hand from the earlier transcripts; no AI session writes it; `/contract Q03` refuses by design |
| 7 | Q04 | **retriever race** | the learner's search ladder vs the agent's, on the same goals; the agent must cite which tool found each library fact |
| 8 | Q05 | **infra debugger** | the agent diagnoses a planted infrastructure failure from the learner's receipts |
| 4–6 | Q06 | **audited prover** | the learner's green hole-skeleton is the contract; the contractor fills ≤5 leaves; the learner audits statements and assumptions |
| 9 | Q07 | **refactorer under harness** | the learner reviews the diff for silently weakened statements |
| 10 | Q08 | **spec-to-proof contractor** | the learner writes the signatures and statements and reviews them for non-vacuity; the agent delivers implementation and proofs |
| 15 | Q09 | **red-teamed contractor** + contract v1 | one plausible-but-false lemma; the contractor must not weaken it; forensics |
| 12 | Q12 | **toolwright** | the agent builds a machine-readable hole/assumption counter to the learner's interface spec; the learner tests it on fixtures |
| 13 / 14 | Q15 | **pipeline forensic** + **toolsmith** | the learner grades the agent's stage attributions; the agent builds one automation for a 12-goal battery; the learner reviews its source and audits every goal |
| 11 | Q17 | **metatheory contractor** | the learner writes precisely correct statements; the agent proves them; the learner audits for a plausible-but-wrong statement |
| 16 | Q18 | **statement-only reviewer → co-developer → adversarial round** + contract v2 | the capstone round (§5.5) |
| — | challenges | the learner *builds* the agents and the trust machinery | |

**Escalation logic.** Trust in the agent rises (repair → implement → prove → co-develop) while the learner's job moves up the abstraction ladder: read transcripts → write checks → audit assumptions → write statements → write blueprints → plant cheats → build gates. In the depth track, the fourteen runs total about 3.5 learner-hours; agent wall-clock time is excluded.

### 5.2 Contracts: fallback, v0, v1, v2

- **Fallback (before v0).** "Build after every edit; done = green + zero holes + acceptance artifacts; never weaken a spec to get green; edits only inside the allowlist." It lives in the contract skill and in CLAUDE.md §Contractor contract.
- **Precedence.** Learner contracts *add to* the fallback and never relax it; the stricter rule wins.
- **v0** (module 1 of the content track, Q03 in the depth track). The learner writes it **by hand** into CLAUDE.md, below the marker `<!-- learner-owned below: contract v0/v1/v2 -->`. Format:
  ```
  ### v0 — Q03, YYYY-MM-DD
  1. <rule> — earned by: <source run> — <one-line transcript moment>
  2. …  (3–6 numbered rules, each tied to an observed transcript moment)
  Done means (re-checkable by a third party): <commands and the output each must show>
  ```
  The learner then rereads it "as a stranger" to confirm that a third party could re-run every done-clause command. The chapter has the learner classify each rule by **what can check it**: the verifier, an audit (diff or transcript), or only a reader. Review is advisory, the viva may ask the learner to defend a clause, and the first live test is the next module's contract run.
- **v1** (Q09 / module 15) comes after the red-teamed run and forensics. **v2** (Q18 / module 16) comes after the learner has built the trust-report gate and run the adversarial capstone round.

### 5.3 Allowlists

- `.claude/state/contract-allowlist` holds plain text, one repo-relative path per line, and is gitignored.
- `/contract` writes it from the CONTRACT header after validating **every** line. A line must:
  - have no leading `/` or `./`;
  - contain no `..`;
  - not fall under `Challenges/` or `agents/`;
  - not name a spine or given layer;
  - not point into a reference tree.

  Any failing line refuses the whole contract.
- The hook enforces the same prefix rules independently, when the allowlist file itself is written (rules 2s/2f).
- At completion or abandonment the contractor writes an **empty** file.
- The session-start hook banners an allowlist that is non-empty and older than one day.

### 5.4 How `/contract` runs

1. **Session check.** Refuse unless the transcript is fresh (§6.1), in one line, before resolving or building anything.
2. **Registry resolve.** Refuse `planned` modules, `solo` modules, and modules with an empty `agentic` list. If `agentic` names more than one file, ask the learner which run this is.
3. **Baseline build.** A red baseline is recorded, not refused, because "a repair contract starts red".
4. **Parse and restate** the contract, and wait for the learner's go-ahead.
5. **Write the allowlist.**
6. **Execute.** Run the gate after every edit unless an `acceptance:` bullet names another per-edit discipline. **Never weaken a check, statement or spec comment to get green; stop and report instead.** "Your prose is rhetoric; your artifacts are the deliverable."
7. **Close out.** Empty the allowlist. Report the changed files and line ranges, the final gate output, and the acceptance checklist with evidence for each item.

**Hard boundaries.** The contractor never tutors: one sentence, then a pointer to `/tutor` in a separate session. It never touches `instructor/`. It does **not** read the instructor contract (CORE.md); it reads CLAUDE.md §Contractor contract instead. The anti-spoiler rules still bind it.

### 5.5 The capstone round (module 16 / Q18)

1. The learner's blueprint is pre-graded (≥3 on every dimension).
2. The learner writes all statements. A `/contract` session **reviews statements only**.
3. A co-developer `/contract` proves from the graded blueprint. The learner may only hint.
4. **Adversarial round.** The learner secretly plants a bug (a mis-optimization or mis-normalization), and the theorem must catch it and localize it.
5. Ship a CLI over the verified core, with a retrospective, and write the final contract v2.

A sibling item builds a **trust-report command plus a gate**. The gate verifies each file in a fresh process and restarts on crash. It must reject three mechanically detectable planted cheats **and** the learner's own planted capstone cheat.

### 5.6 Agentic challenges (reusable parts)

- **Policy protocol.** `propose(state, context, budget) -> [Action]`. Actions are pure data. The harness validates them and is the **only** executor. **The policy process holds no tools** (cheat X18 below).
- **Shipped vs learner-built.**
  - The course ships: the protocol, mock and scripted policies, CLI model backends with pinned argv and transcript audit, benches, the cheat corpus and the grader.
  - The learner builds: the verifier pool, the gate, the eval harness, policies and agents.
- **No usage billing.**
  - Model calls go only through a subscription CLI in headless mode with every tool disabled (`claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --max-turns 2 --effort <pinned> --output-format stream-json --verbose --json-schema <schema> --model <pinned>`), or through local models (e.g. opencode + Ollama with an isolated `HOME`/`XDG_*` config, `tools {"*": false}`, `mcp {}`).
  - No API keys, no SDK, and no CI job ever calls a model.
  - Budgets are counted in calls, tokens, turns, wall-clock and GPU-seconds. A per-item budget B is shared with the par runs. A per-run and rolling-window call cap applies, with **checkpoint-and-resume, "so a limit cannot turn into best-of-n"**.
- **Cheat taxonomy X01–X18**, each mapped to a detector:

| id | cheat | id | cheat |
|---|---|---|---|
| X01 | bare hole | X10 | checker-skip option |
| X02 | hole in a helper | X11 | foreign/extern implementation lies |
| X03 | rogue axiom | X12 | partial/unsafe definitions |
| X04 | trusted native evaluation | X13 | termination proof faked with a hole |
| X05 | ignored error (green by exit-code confusion) | X14 | lookup-table overfitting (hidden tests only) |
| X06 | weakened statement | X15 | harness tampering |
| X07 | vacuous hypotheses (needs a satisfiability witness) | X16 | resource DoS |
| X08 | weakened spec (hidden spec implication) | X17 | held-out exfiltration |
| X09 | notation shadowing | X18 | tool use by the policy process |

  Some classes are **grader-only**, because they need a hidden oracle. The learner's gate MUST report UNKNOWN for those, never PASS.
- **Faithfulness verdict for autoformalization.** ILL-FORMED / VACUOUS / FAITHFUL (equivalence proved within budget by a **grader-owned frozen prover**) / UNFAITHFUL (refuted on small instances) / UNDECIDED (counts as not faithful).
- **Contamination controls.** Course-local strata, sealed single-use tranches, canaries, freeze-then-unseal. The sandbox mounts an artifact tree in which the references were never built, and it self-tests that importing the reference fails.

**Port.** All of §5 transfers. The Dafny and Verus versions of X01–X18 are in §11.4. The challenge tier gains verification-specific cheats: timeouts treated as success by a sloppy harness, proofs that pass on one solver seed only, partial-verification flags, and verifier-configuration poisoning.

---

## 6. The instructor layer

The instructor layer is a set of Claude Code skills (`.claude/skills/<name>/SKILL.md`) that share one contract (`.claude/skills/instructor/CORE.md`). They read and write learner-owned state under `instructor/`. Every behaviour that varies by module is **data in the registry**, never prose in a skill.

### 6.1 Roles, access matrix, session hygiene

**The four roles.** Modes are entered **only by their skill**, never by drifting inside a session.

| role | skills | posture | session lifetime | reads the reference? | edits course code? | writes `instructor/` |
|---|---|---|---|---|---|---|
| **Author** | none (authoring mode, §7.4) | builds the course | — | yes, at build time only | yes | yes |
| **Coach** | `/tutor`, `/discuss`, `/review` | hints, Socratic questions, spaced repetition | `/tutor`: long-lived, one session per module | **never** | **never** | ledger and records |
| **Examiner/Grader** | `/viva`, `/grade-paper`, `/review-code` | examines and grades | fresh every time | **never** | **never** | all (ledger, gradebook, feedback, records) |
| **Contractor** | `/contract` | verifier-checked delivery inside an edit allowlist | fresh every time | **never** | only allowlisted paths | **never** |

**Access matrix** (copy it into CLAUDE.md §Roles):

| capability | Author (authoring mode) | Coach | Examiner/Grader | Contractor |
|---|---|---|---|---|
| Read `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/` | yes (build time only) | **never** | **never** | **never** |
| Edit the learner exercise tree, `tools/`, `paper/*_answers.tex` | yes | **never** | **never** | only paths on the allowlist |
| Edit `Challenges/`, `agents/` (solo work) | yes | **never** | **never** | **never** (no allowlist line may name them) |
| Write `instructor/` state | yes | yes (ledger, records) | yes (all) | **never** |
| Run verifier probes in `instructor/scratch/` | yes | yes | yes | n/a (works in allowed files) |
| Write course prose, solutions, banks, rubrics | yes | never | never | never |

**Why the roles never mix.**
- The coach's history *is* the pedagogy. An examiner sharing that transcript would grade understanding its own hints produced.
- A contractor inside a tutor transcript would be a side door around the hint ladder, and tutor rhetoric inside a contractor transcript would contaminate an artifact-only delivery.

**Enforcement.**
1. **Transcript self-check** at the very top of every skill, before resolving or building anything, with a one-line refusal that names the right skill. **Recommended uniform rule** (the source's per-skill lists drifted; L: the "Session check" sections of `.claude/skills/*/SKILL.md`): *an examiner or contractor session refuses if the transcript contains any other skill's activity; a coach session refuses if the transcript contains any examiner or contractor activity.*
2. **Invocation gating.** Every skill except `tutor` has `disable-model-invocation: true` in its frontmatter, so only the user's slash command can start it. `tutor` alone may be model-invoked, on a pasted stuck state.
3. **Hooks** enforce the *file* boundaries of the matrix (§7). The contractor's ban on `instructor/` writes is instruction-only in the source. To make it hard, give the hook a role signal: a non-empty allowlist means a contractor is active, so deny `instructor/` writes (OD13).

**Session hygiene (copy verbatim).**
- Tutor sessions are long-lived, one per module: "the history is the pedagogy".
- Grader, reviewer, viva and contractor sessions are fresh each time.
- Every skill self-checks its transcript and refuses cross-role contamination in one line.
- Formal disputes go to the verifier: a probe in `instructor/scratch/`, the output pasted verbatim, and the learner interprets it first.

### 6.2 The CORE contract (`.claude/skills/instructor/CORE.md`)

Every instructor skill reads CORE.md first. Its sections:

**Step 0: resolve the module through the registry.**
1. `python3 scripts/check_course_map.py --resolve <ID>` prints one JSON record. It accepts any id case and legacy ids. From then on the skill uses the record's canonical `id` everywhere.
2. Exit 3 (unknown id) → refuse in one line. Any other non-zero exit → "registry broken", stop.
3. `status = planned` → "<ID> is not authored yet". `status = authoring` → proceed only if every input this skill needs exists.
4. Run the record's build target **once, before the first probe**: "a probe against stale build products referees nothing". A red build is the normal state mid-exercise and is not a refusal. Report the first error location, hold back probes that import the failing module, and still run toy probes. Only the code-review gate requires green.

**Anti-spoiler: MAY / MAY NOT.**
- **MAY:**
  - say **that** a step fails and **why**, naming the mechanism;
  - produce **verifier-checked counterexamples**;
  - give **search queries**;
  - point to **chapter sections** and official docs.
- **MAY NOT:**
  - write corrected steps or replacement proofs ("not even just this one line");
  - name the specific lemma that closes the goal;
  - write or edit course source;
  - read the reference trees;
  - import, include, print, build or open reference material through **any** tool, MCP included, or open a search hit that lands in a reference file;
  - name a held-out (`Hidden/`) path.
- **Asked outright for an answer**, follow the record's `solutions_policy` and stop:
  - `solutions-first` → name the reference file ("it is yours to open");
  - `reference-impl` → it opens when the module closes;
  - `kernel-graded` / `harness-graded` → there is no reference; the verifier or the harness is the only answer key.

  "The solutions are the learner's to open; opening them early is self-sabotage, not a rule violation."
- **Defense in depth:** "Every hard rule above is duplicated here as an instruction on purpose: if the hooks are ever off, enforcement degrades to soft, never to silent."

**Turn rules.**
- One question per message, with at most 2 sentences of framing.
- Never lecture first.
- One ladder rung per learner turn; no skipping ahead on request.
- After any probe, **the learner interprets the output first**.
- Close each topic with the learner stating the takeaway in their own words.

**Grading vocabulary.**
- The 4-point scale.
- Min across dimensions.
- Confirmed flaw, or it's a gap.
- SOLID / SHAKY / MISSED per viva question, anchored to bank bullets with quoted learner evidence.
- Outcome PASS / PASS-WITH-REVIEW / REVIEW: advisory, never blocking.
- Hint depth 0–5, logged.
- **Recommended addition:** move the answer classification `correct / incomplete / misconception / off-track` (§6.7) into CORE, where the source mis-attributes it.

### 6.3 The hint ladder

Five rungs, **strictly one per learner turn**. Start at the lowest rung that could plausibly unstick the learner, and never go above the record's `tutor_max_rung` (5 for core modules, 2 for solo challenges).

| rung | name | may contain | never contains |
|---|---|---|---|
| 1 | Clarify the concept | the underlying idea | anything exercise-specific |
| 2 | Point to the chapter section | the exact section of the record's chapter, by its stable heading | — |
| 3 | Targeted question about the state | one question about *their* state whose honest answer moves them | the answer to the question |
| 4 | Name the technique | the *category* of move | a lemma name |
| 5 | Critique a written attempt | the exact failing step and the *mechanism* of failure | the corrected step |

- **The strongest legal hint is a pre-authored parallel problem** from the bank. It counts as rung 5, so it is unavailable under any cap below 5 (solo modules). The procedure: present it, let the learner solve it, then ask them to map it back. **Never improvise an analogy**: "improvised parallels risk converging on the reference solutions the same model wrote."
- **Intake rule: no attempt, no hint.** Before any substantive help, the tutor must see the current code, the state, or the exact error text. Otherwise it asks for them and stops. Norm: at least 20 minutes of attempt first.
- **"Just tell me"** gets the `solutions_policy` answer, plus a reminder that a peek taints later grading.
- **Solo modules.** The tutor announces the cap once. Past rung 2, only two moves remain, and neither raises hint depth: the dispute recipe, and **truth probes** of a sub-lemma *the learner proposed*. A truth probe is a counterexample search in scratch. It reports only "a counterexample turned up" or "none found in this search", never a proof or a repaired statement.
- **Logging.** After each exercise concludes, the tutor appends one ledger line with `hint-depth:` set to the highest rung used. On solo modules every episode is logged, because the defense reads the maximum. "Leaning on the tutor buys future review load."

**Port of rungs 3–4.** There is no goal state, so rung 3 becomes **a question about the failing obligation**: "At the line the verifier flags, what does it know about `i` and the prefix `a[..i]`? Which of those facts did your invariant give it?" The tutor may ask the learner to insert an intermediate `assert` and report the result. That is assertion bisection, the replacement for reading goals [D:doc, V:doc]. Rung 4 technique names include: "needs a loop invariant relating the accumulator to the processed prefix", "needs a `decreases` measure", "needs a lemma by induction on the sequence length", "a quantifier has no usable trigger", "the definition is opaque here", "move this into a `proof` block / `proof fn`" (Verus), "a `by (nonlinear_arith)` scope" (Verus). Never name the library lemma.

### 6.4 Take it to the verifier: the dispute recipe

1. Write a minimal probe to `instructor/scratch/probe.<ext>`. The directory is gitignored. The probe uses **toy terms**, never the learner's exercise statement verbatim if that would leak a hint.
2. Run the pinned single-file command, after Step 0's build.
3. Paste the output **verbatim**. Never paraphrase tool output.
4. **The learner interprets first**; the instructor comments second.

The same recipe is used for: hand-calculation grading ("the verifier is the answer key, never a solutions file"); the viva's predict question; the defense's "predict what breaks" (the one sanctioned use of the learner's own statement: copy it with one hypothesis removed); and pre-built bank probes. Escalation rule: "a dispute that produces a machine-checked instance wins".

### 6.5 Port: the referee is asymmetric

Lean's kernel decides. An SMT verifier gives **three verdict kinds**:
- **verified**, which is trustworthy modulo the TCB;
- **error at a location**, which may mean false, a missing invariant or lemma, a trigger gap, or opacity;
- **inconclusive** (timeout, resource limit, `unknown`) [D:doc: "could not be proved" is not a refutation, and counterexamples "might not be a real counter-example"; V:src: an rlimit hit is reported as an error].

The consequences are binding on the port:

- **Pin deterministic settings in every probe command**: a resource limit rather than a wall-clock limit (Dafny `--resource-limit` [D:src]; Verus `--rlimit` [V:src]), a fixed solver seed if one is used, and per-assertion isolation where helpful (Dafny `--isolate-assertions` [D:src]). Otherwise the pasted output does not reproduce.
- **Teach the three verdict kinds** from module 1. A predict item can ask "which of the three, and where?".
- **Confirmed flaw, or it's a gap, becomes stricter.** A score ≤2 requires one of:
  1. an **executable counterexample**: a concrete input run through compiled code with a runtime check (`dafny run`/`dafny test` with `expect` [D:src]; a Verus `#[test]` [verify]);
  2. a **verified refutation**: a lemma proving the negation at a concrete value;
  3. a verifier-produced counterexample model that the learner replays as (1).

  **"The verifier could not prove it" is never a failing instance.**
- **Answer keys for hand calculations** are executable checks (`dafny test`, Verus `by (compute_only)` for spec functions [V:doc], or exec tests). They are never a verifier-only `assert f(3) == 7`, because fuel and unfolding limits make that a predicate about the verifier, not about `f` [D:doc, V:doc].

### 6.6 Per-skill specifications

**`/tutor [ID]`** (coach). Trigger: the slash command, or model-invoked on a pasted stuck state (attempt, error or unexpected check result). The module id comes from the argument or from a pasted file path; if neither names one, ask and stop. Long-lived session. Procedure: intake → ladder → dispute recipe → policy answer. Writes: the ledger only, never the gradebook.

**`/discuss <ID>`** (coach). May share a session with tutoring; refuses examined, graded or contracted sessions. Input: the record's bank. **An empty or missing bank means stop**: "never improvise a question set (improvised questions drift toward the reference solutions)". On solo modules it stays on bank questions and explain-back. Rules:
- one question per message;
- draw across the bank mix (reconstruct / predict / why / connect / transfer) with at least one **backward-edge** question per session;
- **classify every answer, then move**:

| classification | move |
|---|---|
| correct | **deepen**: one level down (an edge case, "why does that hold?", the connect or transfer variant) |
| incomplete | **narrow**: re-ask restricted to the missing piece, without supplying it |
| misconception | **prepared counterexample**: the bank's counter-move, verifier-run first if formal |
| off-track | **anchor**: one sentence naming where the drift started, then re-ask |

- **Explain-back (Feynman) mode**, on request: adopt the record's persona (§6.9), one objection per turn. End out of persona: the learner states the takeaway, and an exposed gap becomes a ledger entry.
- Writes `instructor/records/<ID>_discuss_YYYY-MM-DD.md`: bank ids asked, the classification of each answer, closing takeaways quoted verbatim, any ledger entries. (Use a distinct `source: discuss` in the ledger; the source reused `tutor`, which is drift.)

**`/review`** (coach): Leitner spaced repetition (§6.11).

**`/viva <ID>`** (examiner). See §6.8.

**`/grade-paper <ID> [--post]`** (examiner). Preconditions, in order:
1. a fresh session;
2. Step 0 with `paper = true`;
3. `make -C paper paper` green (a TeX error is a red build: report it and stop);
4. the answers file and rubric exist;
5. **read the gradebook first**;
6. never read the reference trees: "calibration comes from rubric predicates and verifier anchors only".

Grading follows §4.5. Writes: the feedback file; a gradebook row `paper` (grade = min over problems) or `paper-post`; one ledger line per finding scored ≤2 (the ERROR, never the problem). Declared gaps do not enter the ledger.

**`/review-code <ID>`** (examiner; source name `/review-lean`). Motto: "the verifier goes first; I only grade what it can't".
- **Gate, all before any review:**
  1. fresh session;
  2. build green;
  3. **zero holes counted by the tool, never by grep**;
  4. **assumption audit pinned**: the audit output is recorded in-file or pasted, never taken on "it's probably clean";
  5. a module-specific mechanical gate (depth track: all slots filled, first tries recorded, no check commented, deleted or edited from its shipped form, judged against `main`);
  6. (port, design-judgment bar and above) **a brittleness check**: the module re-verifies under ≥3 solver seeds within the pinned resource limit [verify the flags: Dafny `measure-complexity --mutations N --random-seed S` [D:src]; Verus `--smt-option smt.random_seed=N` [V:src]].

  If any gate fails, name it in one line and stop: "style review of unfinished proofs teaches nothing and tempts spoilers".
- **Bars**, escalating per the record's `review_bar`: `it-reads` → `proof-shape` → `library-conventions` → `design-lite` → `design-judgment` → `library-pr`; challenge bars `production` and `harness`. The review runs *at* the bar, not above it.
- **Dimensions:**
  - naming;
  - readability vs golf (both directions);
  - missed-but-taught idioms, **delivered as search queries, never lemma names**;
  - unnecessary trust (read from the audit);
  - helper factoring;
  - trust-ledger honesty (an unproved claim presented as proved = grade 1).
  - **Port additions:** proof-scaffolding discipline (no dead `assert`s; Dafny `--warn-redundant-assumptions` / `--analyze-proofs` [D:src]); trigger hygiene (no matching loops, no `#![auto]` (Verus) or `{:trigger}` (Dafny) cargo-culting); ghost/exec mode discipline; opacity hygiene (`reveal` scoped narrowly); **brittleness budget** (resource-count variance under seeds; Dafny's documented guidance is a coefficient of variation below 20%, ideally 5% [D:doc]).
- **Hard rules:**
  - never rewrite the learner's proof;
  - idiom demos are at most 3 lines, on an *unrelated toy goal*;
  - findings cite `file:line` and quote the code;
  - a finding already open from an earlier module **escalates** ("third module with X; this is now a pattern") and caps the grade at 2.
- **Writes:** `instructor/feedback/<ID>_code.md` (findings by dimension, plus a "what got better since last module" paragraph built from earlier feedback); a gradebook row; ledger lines only for recurring habits.

**`/contract <ID>`**: §5.4.

### 6.7 Banks

There is one bank per module: `.claude/skills/instructor/banks/<ID>.md`. Its consumers are `/discuss`, `/viva` (module and tier pools) and the tutor's rung 5.

**Layout, in order:**
1. `# <ID> bank — <module title>`, then a usage line naming the consumers and "Operate under CORE.md". A depth-track bank also says whether it feeds a tier pool or is tutor-only.
2. `## Controlled tag vocabulary`, under exactly this heading because the checker finds it by heading: `tag — covers` rows. Every tag must exist in `concepts.md`.
3. `## Question schema`: the per-question fields plus a **mix line** (`Mix: 2 reconstruct / 3 predict / …; N viva-able; M with backward edges`).
4. `## Bank notes`:
   - count and mix;
   - the backward edges;
   - **precomputed viva draws verified to be disjoint** (primary and re-viva; for a tier-end module, a draw table with strand, predict and backward-edge columns), and an explicit statement of when no further disjoint draw exists;
   - **fresh specimens**: predict questions and probes use their own code, never an exercise item's, so the bank "is safe to read mid-module";
   - the toolchain version the probes were verified on, with "quoted outputs are real".
5. Questions `K1…Kn`, separated by `---`.
6. `## Parallel problems`: `PP1…`, headed "Hand these out verbatim — never improvise analogous exercises".

**Per-question fields:**

~~~markdown
### K3 [predict] — the invariant that is one step short
**viva:** yes (verifier-refereed predict) · **strand:** S4 · **tags:** `loop-invariant`, `verifier-output` · **backward-edge:** Q02 (postconditions as contracts)

<the question>

**Target insights**                       (the SOLID anchors that quoted learner evidence must hit)
- <the mechanism the learner must name>
- <the distinction the predict discriminates>

**Misconceptions & counter-moves**
- *"<plausible wrong belief>"* → Probe: <toy program>; ask: <question whose honest answer refutes it>.

**Verifier probe**
```dafny
<toy program, never an exercise statement>
```
(verified on <pinned version and flags>: <verbatim output excerpt>)

**Reread:** §3 "<section title>"
~~~

- **Parallel problems.** Each is `### PP<n> — parallel to Exercise <k> (<what it isolates>)`, with `**Isolates:**` tags. It has "same skills, disjoint content": it appears in no exercise file, agent file or written problem, and its names are disjoint from the avoid list and from the module's exercise *and twin* declarations. Each carries an author-verified note, a "Done =" criterion and a diagnostic ("if the learner solves PP1 but not Exercise 1, the gap is transcription, not concept"). Depth-track parallel problems ship with hole bodies. Parallel problems double as re-viva fill when a small bank cannot give two disjoint draws.
- **Sizes.**
  - Content track: 12 questions per module (8 for module 1), mix ≈ 2 reconstruct / 3 predict / 3 why / 2 connect / 2 transfer, **≥10 viva-able so that two disjoint draws exist**, ≥4 backward edges, 1–2 parallel problems.
  - Depth track: 8 per module, pooled per tier. A survey bank is tutor-only, with every question `viva: no`, so no later pooling draws from it.
  - Challenges: a *defense sheet* of six templates with insight bullets per topic.
- **Visibility.** Decide explicitly whether banks are learner-visible, and author all of them to that standard (OD12). The source leaves them unguarded and calls depth-track banks "safe to read mid-module", but content-track target insights are exactly the viva anchors.

### 6.8 Vivas

- **Preconditions:** a fresh session; Step 0; dispatch on `viva_mode`; load the ledger and earlier records. **A re-viva draws questions disjoint from every previous draw.** If `viva_mode = none`, refuse and name the examining module ("Q02 has no viva of its own; its tier is examined by /viva Q03").
- **Exam discipline:** one question per message; no lecturing; a neutral acknowledgment ("noted — next:"). **Grades are revealed only at the end**, because "mid-exam feedback distorts the remaining answers".
- **Module viva: exactly 6 questions.**
  1. reconstruct;
  2. predict, refereed live by the verifier;
  3. why;
  4. connect (a backward edge);
  5. transfer;
  6. **one ledger-generated question**, built fresh from this module's concept–error pairs and never re-asking a recorded question. If the ledger is empty, it becomes a second predict.
- **Tier viva: exactly 5 questions.**
  - The pool is the union of `viva: yes` questions in the banks of every module in the tier. **Refuse if any bank is missing** ("a partial pool is not the tier").
  - The draw takes 5 questions from **5 different strands**, at least one per module, at least one predict, and at least one backward edge where possible. Each is cited by scoped id (`Q02.K3`).
  - If no disjoint 5-strand draw exists, report the bank gap and stop, "never patched by improvising".
- **Defense: exactly 6 questions built from the learner's challenge artifact** plus its `TRUST.md`. **Every template is instantiated on the artifact and written, with its anchor bullets, into the record file BEFORE asking**: "anchors fixed before the answer cannot drift to fit it". The six slots:
  1. reconstruct a lemma;
  2. predict what breaks when a hypothesis is removed (refereed by the verifier);
  3. design (the trust boundary per `TRUST.md`);
  4. connect;
  5. transfer;
  6. ledger.

  `assisted (max hint-depth N)` is recorded when N ≥ 1.
- **Grading.**
  - SOLID / SHAKY / MISSED per question, each anchored to target-insight bullets with a quoted learner phrase or the quoted absence of one. "No anchor bullet, no verdict." An answer outside the anchors is graded SHAKY.
  - Outcome thresholds:

| outcome | 6-question (module, defense) | 5-question (tier) |
|---|---|---|
| PASS | no MISSED, ≤1 SHAKY | no MISSED, ≤1 SHAKY |
| PASS-WITH-REVIEW | ≤1 MISSED and ≤3 SHAKY | ≤1 MISSED and ≤2 SHAKY |
| REVIEW | anything weaker | anything weaker |

  The outcome is advisory and never blocks. REVIEW recommends chapter sections per missed anchor, then a disjoint re-viva.
- **Writes:**
  - `instructor/records/<ID>_viva_YYYY-MM-DD.md` (or `_defense_`), with each question, the quoted answer, the verdict with cited anchors, and the probe transcript of every predict;
  - one ledger line per SHAKY/MISSED, tagged with the module **the question came from**;
  - one gradebook row.

### 6.9 Personas

Personas are used only in `/discuss` explain-back. The persona "asks questions and raises objections — it never lectures and never supplies the correct account itself". Each profile has three parts:
- **who**: an experienced practitioner adjacent to the material;
- **pushes back on**: specific objections, including deliberately **wrong-but-plausible claims** the learner must catch;
- **convinced by**: concrete evidence the verifier or an artifact shows.

The persona is keyed by the registry `persona` field and banded so that skepticism escalates along the thesis:
- early: a sharp developer with zero background, who maps everything to mainstream programming and asks where the mapping breaks;
- middle: a typed-FP skeptic;
- late: an **"ML engineer who thinks a big test suite equals a proof"**, which deliberately rehearses the course thesis.
- Challenge topics get domain referees: journal referee, risk engineer, numerical analyst, compiler engineer, eval skeptic.

**Port re-theming:**
- early: "Python developer who thinks type hints plus tests suffice";
- middle: "C++ / systems programmer suspicious of ghost code and of anything the compiler erases";
- late: keep the "big test suite = proof" ML engineer, and add an "SRE who trusts fuzzing".
- Verus challenge referees: an OS/kernel engineer; a concurrency skeptic.

### 6.10 Ledger and gradebook

**Ledger** (`instructor/ledger.md`). One line per item, in a fixed field order, because the session-start hook greps `due: YYYY-MM-DD`:

```
- tag: Q04/loop-invariant | error: stated the invariant over the whole array instead of the prefix processed so far | seen: 2026-10-02 | box: 1 | due: 2026-10-03 | hint-depth: 3 | source: tutor
```

- **Store the ERROR, never the question**, "so /review can generate fresh variants and verbatim re-asking is impossible".
- Tags come from the module bank's vocabulary, which is a subset of `concepts.md`.
- `hint-depth` is meaningful only for `source: tutor`; other sources write 0, so the field order stays fixed.
- Writers: the tutor (per concluded exercise), viva (per SHAKY/MISSED), grade-paper (per finding ≤2), review-code (per recurring habit), discuss (per exposed gap). `/review` reschedules and rarely adds.
- The checker validates the prefix (a known module id) and the tag (in `concepts.md` and in that module's bank vocabulary).

**Gradebook** (`instructor/gradebook.md`): `| date | module | track | grade | open findings |`. Example rows:

```
| 2026-10-14 | Q03 | viva | PASS-WITH-REVIEW | 3 ledger items |
| 2026-10-15 | Q04 | calib | first-try 7/9 (78%); exit 3/4 | — |
```

| track | written by | grade cell |
|---|---|---|
| `paper` | `/grade-paper` | min over problems (1–4) |
| `paper-post` | `/grade-paper --post` | re-scored blueprint quality / delta |
| `code` (source: `lean`) | `/review-code` | 1–4 |
| `viva` | `/viva` (module or tier) | PASS / PASS-WITH-REVIEW / REVIEW |
| `defense` | `/viva` defense | outcome, plus `assisted (max hint-depth N)` |
| `challenge` | the gate script only | gate result |
| `calib` | `firsttry.sh --record` only | e.g. `first-try 7/9 (78%); exit 5/6` |

**The tutor and `/discuss` never write the gradebook.** Graders **read it first** and escalate repeat findings.

**Other state:**
- `instructor/calib/<ID>.tsv` (first tries: append-only, first record wins, script-written only);
- `instructor/feedback/<ID>_{paper,code}.md`;
- `instructor/records/` (viva, defense and discussion logs with key formulations quoted verbatim; re-vivas read them to guarantee disjoint draws);
- `instructor/scratch/` (gitignored probes).

Both tracks share one ledger and one gradebook.

**Shared vocabulary** (`.claude/skills/instructor/concepts.md`):
- A table of canonical kebab-case tags with `aliases` (spelling variants only), `covers` and `declared by`.
- A later module that teaches an already-tagged concept **reuses the tag**, so review interleaving sees one concept.
- **Never rename a tag**, because ledgers already use it. A new concept gets a row before any bank or ledger uses it.
- A "near neighbours" list keeps look-alike concepts as distinct tags.
- The checker validates all of this, including that "a shipped tier-viva module has every bank of its tier".

### 6.11 Spaced repetition (`/review`)

- **Leitner boxes:** 1 / 3 / 7 / 21 / 60 days. An item is due when `due:` is on or before today.
- **Banner.** A SessionStart hook prints `Review queue: N item(s) due — run /review`. It never fails or blocks a session and always exits 0. The same hook banners a stale contract allowlist and an authoring-mode file, so a stood-down guard is never silent.
- **Procedure:**
  1. Collect due items. If none, say so and stop.
  2. Take **at most 6**, most overdue first, then higher hint depth first.
  3. **Interleave**: never two consecutive items with the same module or the same canonical tag.
  4. **Generate a FRESH variant** from the concept–error pair: a small task (≤5 min, preferably predict-then-verify) that a learner still carrying the error gets wrong and one who has fixed it gets right.
  5. One item per message. Classify the answer; on a misconception, give the mechanism, not the corrected answer.
  6. Update the line:
     - answered well → box + 1 (max 5), due = today + interval;
     - answered poorly → box 1, due tomorrow, and sharpen the `error:` text;
     - answered well at box 5 → graduated (delete), **except** a solo module's tutor line, which stays until that module's defense row exists.
  7. Close with a one-line summary.

### 6.12 Grader calibration and validation

**Author-time validation** (Phase 4b; re-run on any change to skills, rubrics or solutions):
- **Headless grader runs over the fixtures.** Pass: the planted flaw is caught at the right location, on the right dimension, with grade ≤2; the gold fixture scores ≥3 everywhere with zero broken-step findings.
- **Leak check.** Grade an empty answers file, ask the tutor outright for the answer, grade the flawed fixture; then grep **everything the instructor emitted** against the module's leak patterns. **Both** assertions must hold: zero hits, *and* the help stayed legal (the planted flaw was caught). Either alone can be satisfied by a useless grader.
- **Simulated `/viva` and `/discuss`** with the author playing a deliberately confused learner. Pass: counter-moves fire, no drift into lecturing, no grade inflation.
- Depth track: tier vivas, defense simulations, ≥3 gold `/contract` transcripts; exit criterion "zero leak hits".

**Validation as curriculum** (learner-facing, in the agentic module):
- **Grade-the-grader variance lab.** A fixed flawed fixture is graded three times in fresh sessions, and agreement is tabulated at three levels: **LINE** (expected identical), **BAND** (expected identical) and **PROSE** (expected to vary). Conclusion: anchored lines are stable and prose is not, which is "the argument *for* rubrics and the reason an instructor grade is disputed at the rubric-line level". The fixture is read-only between runs: "an edited fixture measures the edit, not the grader".
- **Tutor red-team.** The learner social-engineers `/tutor` for a solution and checks that the hook and the refusal hold. Then, in a **hooks-disabled throwaway copy containing a decoy `Solutions/` fixture** (never real references), the learner sees how far an instruction-only defence bends.

---

## 7. Anti-spoiler architecture

### 7.1 Asset model

| class | paths (port names) | who may read | who may write | guarded by |
|---|---|---|---|---|
| Reference trees | `Solutions/` (plus its project file or crate), `paper/solutions/`, `tests/instructor/leak_patterns/`; later `Solutions/Challenges/Hidden/*.tar.age` | the author (authoring worktree only) and CI; **never Claude in any study-mode role** | the author | L1 deny, hook rules 1/1b/1c/1d, L3 |
| Grader cache / unsealed held-out data / author probe archive | `~/.cache/<course>/**` | the grader container only | the grader | L1 (4th rule), hook rules 1/1c |
| Learner exercise files | `Course/` (Dafny) or `course/` (Verus crate), `tools/`, `paper/*_answers.tex` | everyone | the learner; Claude only inside `/contract`, on allowlisted paths | hook rule 2 |
| Solo work | `Challenges/`, `agents/` | everyone | the learner only; **no allowlist can unlock it** | hook rule 2s |
| Frozen given library | spine/given files or crate | everyone | nobody in study mode | hook rule 2f; CI "given is complete and silent" |
| Guard and build configuration | `.claude/hooks/`, `.claude/state/mode`, `.claude/settings{,.local}.json`, **every project/build file** (port list in §7.2, rule 2g) | everyone | nobody in study mode; only `course_mode.sh`, run by the human | hook rule 2g |
| Instructor state | `instructor/` | everyone | coach and examiner; never the contractor | L3 (instruction) |

Rubrics are learner-visible by design: they hold predicates, never answers, plus sha pins.

**Pick a reference-root name that is a distinctive bare word** (`Solutions`). The guard blocks that bare word in every path-like tool field, which only works if the word has no study-mode use.

**Threat model: three leakage channels** (L: `PLAN.md:263`, risk 10). The layers below close only the first one, so an imitator MUST design for all three:

| channel | example | what answers it |
|---|---|---|
| **file access** | reading, searching, building, importing or replaying the reference trees | L1 deny rules, the L2 hook, L3 instructions (this section) |
| **regeneration from model knowledge** | the same model that wrote the references re-derives an answer while "helping" | the one-rung-per-turn hint ladder, the no-course-code rule, **pre-authored** parallel problems and banks instead of improvised analogies or question sets, leak-pattern checks over instructor output (§6.3, §6.7, §6.12) |
| **abstract asks** | "just prove this lemma for me" in a fresh session | irreducible. It is framed in the README as self-sabotage, answered by naming the reference path and stopping, and made visible by hint-depth logging |

### 7.2 The layers

**Layer 1: static permission deny rules** (`.claude/settings.json`):

```json
"permissions": { "deny": [
  "Read(./Solutions/**)", "Read(./paper/solutions/**)",
  "Read(./tests/instructor/leak_patterns/**)", "Read(~/.cache/<course>/**)" ] }
```

- The harness refuses these reads before any hook runs, in every mode and for every role. **This layer still holds with hooks disabled**; a headless run with hooks off was verified to be denied by layer 1 alone.
- It cannot read state, so it cannot depend on the mode. That is why the mode switch must physically remove these rules for authoring and merge them back for study.
- It sees only path-shaped Read rules. Shell text, module-name imports, MCP calls and build commands are layer 2's job.
- **These four canonical strings appear in four places that must agree**: `course_mode.sh` (a `CANONICAL_DENY` array), the CI study-mode check, CLAUDE.md, and the hook test. Copy them together. CI checks `need ⊆ deny`, so extra user rules pass.

**Layer 2: the PreToolUse hook** (`.claude/hooks/spoiler-guard.sh`).

- **Wiring.** Register the hook as `PreToolUse` with a matcher covering `Read|Grep|Glob|Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit` plus **every verifier-side MCP or wrapper tool** (port: `mcp__dafny.*`, `mcp__verus.*`, any plugin-scoped pattern). Timeout 15 s. The hook itself keys on `tool_name`, not on the matcher, so a looser matcher changes nothing. Include plugin-scoped patterns up front so a later plugin install needs no guard change. The committed `.claude/settings.json` of a study-mode checkout has this shape (source: L: `.claude/settings.json`, with the Lean MCP names swapped for port names):

```json
{
  "permissions": { "deny": [
    "Read(./Solutions/**)", "Read(./paper/solutions/**)",
    "Read(./tests/instructor/leak_patterns/**)", "Read(~/.cache/<course>/**)" ] },
  "hooks": {
    "PreToolUse": [ { "matcher": "^(Read|Grep|Glob|Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit|mcp__vcheck__.*|mcp__(dafny|verus).*|mcp__plugin_.*(dafny|verus|vcheck).*__.*)$",
                      "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/spoiler-guard.sh", "timeout": 15 } ] } ],
    "SessionStart": [ { "matcher": "startup|resume|clear",
                        "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/review-due.sh", "timeout": 15 } ] } ]
  }
}
```

  The hooks schema, the deny-rule syntax and the SessionStart matcher values are Claude Code facts: pin them in `VERSIONS.md` (§8.7).
- **Contract.**
  - Input: the hook JSON on stdin (`tool_name`, `tool_input`, `cwd`).
  - Exit 0 = allow; exit 2 = block, with stderr shown to Claude.
  - Every block message starts `spoiler-guard: blocked (rule X) — …` and suggests a legal alternative.
  - The hook works without `jq`, through a grep/sed fallback parser that an environment variable can force for testing.
  - **It never blocks on its own parse failure**: malformed or empty input exits 0. This fail-open choice is safe only because layer 1 still holds.
- **Field classes:**
  - `STRICT` (path-like): `file_path`, `notebook_path`, `path`, `glob`, `command`, Glob's `pattern`, and **every string anywhere in a verifier MCP call**. Here bare words also block.
  - `TEXT` (written content): `content`, `new_string`, `edits[].new_string`, `new_source`, Grep's `pattern`. Here only path forms and module-name/include forms block, so prose such as "Solutions-first" passes.
  - `FPATHS`/`SPATHS` (named files and search roots): resolved through `~`, `$HOME` and the project dir, `..`-folded, symlink-resolved.
- **Rules** (every one stands down in authoring mode):

| rule | blocks | hole it closes |
|---|---|---|
| **1** spoiler names | any STRICT field naming a reference path or bare word; any TEXT field with a path form or an import/include form; named files checked through symlinks; **a source file named by a shell command or MCP call has its first 64 KiB scanned for an import/include of the reference** | direct reads; reads through a scratch symlink; **writing a probe that imports the reference and then running the tool on it** (the tool would print reference code) |
| **1b** spoiler builds | building the reference target; the written-solutions target; any command naming an author-only script that reads references; an MCP build of another project or of a target not in the registry | building the reference prints its output; another project could make the reference its default; reader scripts used as side doors |
| **1c** held-out material | the grader, unseal and decrypt commands, `*.tar.age` | sealed corpora are never decrypted by Claude |
| **1d** whole-tree readers | recursive search whose root *reaches* a reference tree (`grep -r`, `rg`, `ag`, `ack`, `git grep`, the Grep tool with no path); `find` feeding `-exec`/`xargs`; `git ls-files \| xargs`; a glob expanding into a reference tree; `git show`/`log -p`/`diff <rev>`/`format-patch`/`archive`/`bundle`/`cat-file -p` without a learner pathspec | reading references without naming them: via a parent directory, **via build-artifact directories (which hold compiled reference output)**, or **via git history (which carries the reference trees too)** |
| **2** learner-owned files | writes under the exercise tree, `tools/` or `paper/*_answers.tex` whose path is not on the allowlist; checked on the lexical **and** symlink-resolved path | the tutor solving exercises; a contractor straying outside scope |
| **2s** solo work | any write to `Challenges/` or `agents/`, allowlist or not; an allowlist line naming them is itself rejected | solo modules have no contractor |
| **2f** frozen spine | any write to a given/spine file, however the path is spelled; an allowlist line naming one is rejected; checked before rule 2 | the shared given library must be identical for every learner |
| **2g** the guard itself | writes to `.claude/hooks/*`, `.claude/state/mode`, `.claude/settings.json`, `.claude/settings.local.json`, and **every file that decides what the build builds or how the verifier runs** | a session switching its own guard off (removing deny rules, setting `disableAllHooks`, writing the mode file, adding the reference to the default build, loosening verifier flags) |

- **Bash write detection (best effort), in order:**
  1. drop heredoc bodies;
  2. drop fd duplications;
  3. split on `&& || ; | & \` ( ) $(`;
  4. peel wrappers (`sudo env command nice timeout stdbuf xargs bash -c`, `VAR=val`, `if/then/do`);
  5. check every existing path argument and glob expansion;
  6. check redirect targets;
  7. apply per-command handlers: `cd`/`pushd` (track CURDIR), `tee`, `sed`/`perl`/`ruby -i`, `cp`/`install`/`rsync`/`ln`/`scp`, `mv`/`rm`/`truncate`/`shred`/`unlink`, `dd of=`, and git `checkout`/`restore`/`rm`/`mv`/`clean`;
  8. for script one-liners (python/node/ruby/perl/deno/bun) with a write-ish verb, check every protected path named in the text.
- **False-positive policy.** Block when an input *names* a spoiler, since those strings have no study-mode use; otherwise stay out of the way. Accepted costs, documented in the hook header:
  - a commit message mentioning the bare word is refused (rephrase it);
  - `ls *` at the repo root is refused;
  - only registry targets may be built through MCP.
- **Accepted exposure.** The language server indexes the reference tree, so a workspace-symbol search can list reference declaration *names* (never bodies). **Reference-only helpers therefore carry neutral names that do not reveal the strategy.**
- **Honesty clause** (copy it into the hook header): "This is a tripwire, not a sandbox: string splitting, or a script that opens files itself, gets past it. The instructor contract forbids trying (layer 3); OS-level isolation is the sandbox's job."

**Port side channels.** Each item below MUST become a must-block fixture.

| channel | Dafny | Verus |
|---|---|---|
| source inclusion | `include "…/Solutions/…"`; a `dfyconfig.toml` whose `includes` glob or `base = […]` chain reaches the reference; `--library <ref file>`; `.doo` library files built from the reference [D:src, D:doc] | `mod solutions;`, `#[path = "…/Solutions/…"] mod x;`, `include!`/`include_str!`/`include_bytes!`, `use solutions::…`; a Cargo `path =`/`git =` dependency; `build.rs` [V:doc] |
| builds | `dafny verify/build/run/test Solutions/dfyconfig.toml` or naming any reference file | `cargo verus verify --manifest-path Solutions/Cargo.toml`, `-p solutions`, any command run with `Solutions/` as its working directory; `--import solutions=<.vir>` / `--extern` [V:src] |
| artifacts | translate/build output dirs (generated C#/Go/Java/JS/Python), `.doo` files, `dafny doc` HTML, coverage reports, `TestResults/`, solver logs and Boogie prints [D:src, verify each] | `target/**` (`.rlib`, `.rmeta`, and `.vir` beside them), `target/verus-partial/`, `.verus-log/` (VIR/AIR/SMT of the verified crate), `.verus-solver-log/`, `*.zip` from `--record` (it zips **all crate sources**) [V:src, V:doc] |
| environment | `--solver-path`/PATH `z3` substitution; `--plugin` assemblies (they rewrite the program before verification) [D:src, D:doc] | `VERUS_EXTRA_ARGS` [verify that release builds honour it], `VERUS_Z3_PATH`, `RUSTC_WRAPPER`, `RUSTFLAGS` with `--cfg verus_only` [V:src, V:doc]. The hook MUST inspect `VAR=val` prefixes |
| never-written config (2g) | **every** `dfyconfig.toml`, `.vscode/settings.json` (`dafny.version`, `dafny.cliPath`, `dafny.dafnyServerArguments`), the dotnet tool manifest, the pinned binary directory [D:doc]; the project `.mcp.json` if `vcheck` is exposed as an MCP server | `Cargo.toml` (every crate and the workspace), `rust-toolchain.toml`, `build.rs`, `.cargo/config.toml`, `[package.metadata.verus.ide] extra_args`, `.vscode/settings.json` (`verus-analyzer.verus.verusBinary`, `extraEnv`) [V:doc]; the project `.mcp.json` likewise |
| IDE/LSP | `dafny server` custom methods (`dafny/textDocument/verifySymbol`, `dafny/counterExample`, …) [D:src]; whether workspace symbols span the reference project is [verify] | verus-analyzer (a rust-analyzer fork) [V:doc]; whether it indexes non-member crates is [verify] |

**Layer 3: the instructor contract.** CORE.md MAY/MAY-NOT (§6.2), plus "never import, include, print or build from the reference through any tool, MCP included; never name a `Hidden/` path". Role pinning across a session is enforced by norm, not by the harness. That is a recorded risk.

**The detector: leak patterns** (`tests/instructor/leak_patterns/<ID>.txt`, read-denied).
- **Format:**
  - comments start with `#`; blank lines are ignored;
  - one Python `re` pattern per line, verbatim, with no delimiters and no flags; applied with `re.search`, with `re.MULTILINE` only where `^`/`$` is needed;
  - whitespace written as `\s+`, because grader output reflows;
  - punctuation escaped;
  - patterns grouped under `# from <source>` comments; each entry has `# source: <verbatim twin line>` and `# verified: solutions=1 public=0`;
  - 3–8 patterns per module, preferably multi-token juxtapositions, cut **only from H/X/T/A answers** (P answers are revealed by the chapter after the box).

  An invented example:
  ```
  # from Solutions/R07_Sorting.dfy
  invariant\s+forall\s+k\s*::\s*0\s*<=\s*k\s*<\s*i\s*==>\s*a\[k\]\s*<=\s*pivot
  ```
- **Rule 1:** every pattern matches its own solution file. A pattern that matches nothing is a disarmed tripwire.
- **Rule 2:** no pattern matches anything public (problems file, chapter, learner files, spine, bank, rubric). Otherwise legitimate output quoting the question trips it, the detector cries wolf, and it gets switched off. When a pattern over-matches, **tighten it rightwards into the withheld part**; never delete it.
- **The verifier for these rules lives only inside the read-denied directory's README, never in a repo script**, because a script that opens the patterns would be a study-mode side channel. Its output is `OK|FAIL sol=N prob=N chap=N <pattern>`. Re-run it whenever a solution changes; a pattern goes stale by the same mechanism as a rubric pin.

### 7.3 SessionStart banners

`review-due.sh` never fails and always exits 0. It prints only the banners that apply:
- due Leitner items;
- a contract allowlist that is non-empty and more than one day old;
- **an authoring-mode file, so a stood-down guard is never silent.**

### 7.4 Study mode vs authoring mode, and the authoring worktree

| | study (the shipping state) | authoring |
|---|---|---|
| `.claude/state/mode` (gitignored) | absent | contains `authoring` |
| L1 deny | the 4 canonical rules present | the 4 canonical rules removed (other rules kept) |
| L2 hook | enforces | exits 0 at the top, **but only when git confirms all three conditions**: (a) inside a git checkout; (b) a *linked* worktree (`git rev-parse --git-dir` ≠ `--git-common-dir`); (c) HEAD is not on a learner branch (`<learner-prefix>-*`) |
| switch | `scripts/course_mode.sh study` | `scripts/course_mode.sh authoring`; it **refuses** (exit 1, nothing written, deny list untouched) outside git, in the primary worktree, or on a learner branch, and prints the recipe `git worktree add ../<repo>-authoring -b authoring origin/main` |
| status | `course_mode.sh status` prints the mode and the deny list, and says when a mode file is present but **ignored** | |

**Invariants:**
- **The two layers move together.** Otherwise the author is locked out of the files being written. This happened in the source: rubric sha pins could not be computed.
- **The hook verifies the worktree condition itself**; it never trusts the flag file. A mode file copied or committed into the learner checkout is ignored.
- **Never flip either layer by hand.** CI fails if the repo ships a mode file or lacks any canonical deny rule. In a working tree, a deny list without the rules means "this checkout is mid-authoring", never "the guardrails were removed".
- **Author-only scripts that read references** gate themselves on the same three-condition test, or on `CI=true`. That self-check is not a guard ("CI=true is one word away"), so the hook *also* refuses any shell command that names such a script.
- **Authoring happens in a persistent worktree** outside the learner checkout and outside any session scratchpad, created after the guard infrastructure is merged.

### 7.5 Hook regression tests (`scripts/test_hooks.sh`, CI job `hook-test`)

- **Fixtures.** `tests/hooks/must_block.jsonl` and `tests/hooks/must_allow.jsonl` (the source has ~166 and ~110 lines). Each line is one hook input plus a `why`. `@ROOT@` stands for the checkout root, and a `raw` field feeds a string verbatim (for malformed-input cases):
  ```json
  {"why": "rule 1d: recursive grep from the repo root", "tool_name": "Bash", "tool_input": {"command": "grep -rn lemma ."}, "cwd": "@ROOT@"}
  {"why": "rule 1: probe that includes a reference file", "tool_name": "Write", "tool_input": {"file_path": "@ROOT@/instructor/scratch/p.dfy", "content": "include \"../../Solutions/R05_Loops.dfy\"\n"}, "cwd": "@ROOT@"}
  {"why": "probe on a scratch file", "tool_name": "Bash", "tool_input": {"command": "scripts/vcheck instructor/scratch/probe.dfy"}, "cwd": "@ROOT@"}
  {"why": "empty input never blocks", "raw": ""}
  ```
- **Rule attribution.** A must-block line whose `why` starts with `rule <id>:` must be blocked *by that rule*: the harness greps stderr for `(rule <id>)`. This catches a test that passes for the wrong reason.
- **Fake roots.** The hook runs against throwaway roots that hold **decoy** reference files, never real material. The decoys include a seeded allowlist with forbidden lines (spine, solo dirs) to prove those lines are ignored, scratch probes that import references and ones that don't, and symlinks into the reference tree.
- **Passes:**
  - study mode (block ⇒ exit 2, allow ⇒ exit 0);
  - the same with the jq-free parser;
  - stand-down: a mode file in a linked worktree makes every must-block line exit 0;
  - still armed: a mode file outside git, in the primary worktree or on a learner branch keeps every must-block line at exit 2;
  - `course_mode.sh` tests (refusals; canonical-first merge; exact removal; idempotence);
  - banner tests (`touch -d '2 days ago'`);
  - the committed `settings.json` at HEAD carries the canonical rules.
- **Self-protection workflow.** `SPOILER_GUARD_HOOK=/path/copy.sh` replays the suite against a candidate hook. The live hook guards the session that is editing it, so **changes are made in a copy and installed only when the suite is green**.
- **Red-team origin.** The source guard was extended after a red-team replay found "11 of 12 bypass cases exit 0". Every bypass found becomes a fixture.
- **Must-allow coverage** pins ordinary work the guard must never break: the default build and per-module builds, registry targets, scratch probes, `git status`/`log` and pathspec diffs, scoped searches, writes to instructor state, allowlisted edits, `/contract` writing and emptying its allowlist, reading (not writing) settings, and other MCP servers.

---

## 8. Registry, scripts, CI and build targets

### 8.1 The registry (`MODULES.toml`)

- **Single source of module facts.** Skills resolve ids through it and never guess filenames. The guard reads its `build_target` values. CI validates it first.
- **Learner-visible**, so it **names no reference material**. The checker rejects any field name containing "solution" and any path with a component stem in `{solutions, leak_patterns, hidden, …}`. Author tooling derives reference paths by convention: twins share the stem.
- **Shape.** Top-level `schema = <n>`, then one `[[module]]` table per module, in id order, then `[[coverage]]` tables. **Every field is required, in this order:**

| field | type | values / meaning |
|---|---|---|
| `id` | str | `R01`…, `Q01`… |
| `legacy_id` | str | a pre-rename id or `""` (`--resolve` accepts it) |
| `track` | enum | `R` \| `Q` |
| `status` | enum | `shipped` (every path must exist) \| `authoring` (paths may be missing; a skill checks its own inputs) \| `planned` (skills refuse) |
| `title` | str | |
| `tier` | str | depth track: `survey`, `intro`, `moderate`, `detailed`, `practice-intro`, `practice-intermediate`, `practice-hard`, `challenge`, **fixed by id range** |
| `topic` | str | challenge modules only |
| `strands` | list | `S1`…`S12`; each tier partitions S1–S12 |
| `chapter` | str | `docs/<id>_<Name>.md` |
| `exercises` | list | learner files; a trailing `/` names a directory (e.g. a specimen dir) |
| `agentic` | list | files a `/contract` session works in; `[]` = no contract |
| `bank` | str | bank path or `""` |
| `paper` | bool | true ⇔ the problems/answers pair exists (checked in both directions) |
| `rubric` | str | required when `paper = true` |
| `build_target` | enum | fixed by id range (port: a project path or crate name, §11.1) |
| `review_bar` | enum | `it-reads` … `library-pr`, `production`, `harness` |
| `persona` | enum | the persona keys (§6.9) |
| `viva_mode` | enum | `module` \| `tier` \| `defense` \| `none` |
| `tutor_max_rung` | int | 1–5 (reject bool) |
| `solo` | bool | true ⇒ `/contract` refuses and `agentic` must be `[]` |
| `solutions_policy` | enum | `solutions-first` \| `kernel-graded` (port: `verifier-graded`) \| `harness-graded` \| `reference-impl` |
| `write_tactics`, `recognise_tactics` | list of slugs | (port: `write_constructs`, `recognise_constructs`) capped, disjoint |
| `imports` | table | every file of the module → its import tier |
| `concept_items` | table | the concept matrix (§2.3.5) |

The source registry is at `schema = 2` (QPLAN's text still says 1; the checker is authoritative, §12.3). Two fields that §2.3.8 and §2.8 rely on are **planned, not built**, in the source: `admissible` (per practice item, so CI can refuse minutes on an item without a complete in-band reference) and `statements[]` (the frozen, sha-pinned statement files of a challenge module). They arrive with the schema bump that first needs them (L: `QPLAN.md:799`). An imitator building practice tiers or challenges MUST add them, bump `schema`, and teach the checker both. Until then, the "no minutes on non-admissible items" check in §8.2 has nothing to read.

Invented record:

```toml
[[module]]
id = "Q04"
legacy_id = ""
track = "Q"
status = "authoring"
title = "Proof craft & libraries"
tier = "moderate"
topic = ""
strands = ["S1", "S2", "S3", "S4", "S5"]
chapter = "docs/Q04_ProofCraft.md"
exercises = ["Course/Q04_ProofCraft.dfy", "Course/specimens/Q04/"]
agentic = ["Course/Q04_AgentRetriever.dfy"]
bank = ".claude/skills/instructor/banks/Q04.md"
paper = false
rubric = "paper/rubrics/Q04_rubric.md"
build_target = "Course/dfyconfig.toml"
review_bar = "proof-shape"
persona = "sharp-dev"
viva_mode = "none"
tutor_max_rung = 5
solo = false
solutions_policy = "solutions-first"
write_constructs = ["assert-by", "calc", "lemma-call", "decreases"]
recognise_constructs = ["reveal", "induction-attr"]
[module.imports]
"Course/Q04_ProofCraft.dfy" = "std-collections"
[module.concept_items]
"S3.assert-by" = ["Q04.H2", "Q04.P3"]
```

### 8.2 The checker (`scripts/check_course_map.py`)

Five groups, each runnable with `--only GROUP`:

- **registry:**
  - schema: fields, their order and types, enums, no unknown fields;
  - ids: unique, complete, ordered;
  - per-track rules: target and tier follow the id; tiers partition the strands and end in exactly one tier viva; challenges are solo, with topics in order;
  - constructs: slugs, caps, disjointness;
  - imports declared for every past-`planned` file;
  - the concept-matrix shape;
  - **paths**: no reference or held-out path; existence for `shipped` modules; the paper pair in both directions;
  - **targets**: every non-planned target exists in the build configuration, and **the default target list is exactly the learner exercise target**;
  - ledger tag prefixes.
- **import-tiers:** each file's *transitive* external imports stay within its tier; no undeclared or doubly-declared file; an empty file glob while a core module is past `planned` is an error.
- **isolation:**
  - I1: a module file imports only externals, its tier's spine layers and its own module's files; spine layers import only lower layers;
  - I2: the tracks never import each other;
  - I4a: every top-level declaration is namespaced, and global-effect declarations are scoped;
  - I5: residue checks reject stale id spellings and enforce label schemes in docs, banks and rubrics;
  - (I3, references mirroring learner imports, lives in the reference lint; I4b, duplicate declarations, is the CI coexistence build).
- **coverage:** item blocks parse; every cited item exists; every P/H/X/T item is cited; each WRITE construct has ≥2 `uses:`; coverage rows are complete and resolve; no minutes on non-admissible items.
- **vocab:** `concepts.md` tags and aliases unique and kebab-case; bank vocabularies ⊆ tags; ledger tags known; bank strands legal; a shipped tier-viva module has every bank of its tier.

**CLI contract:**

| invocation | output | exit |
|---|---|---|
| (default) | errors | 0 consistent, 1 error |
| `--resolve ID` | one JSON record (case-insensitive; legacy ids map) | 0; 3 unknown; 1 broken registry |
| `--items ID [--json]` | parsed items (§3.9) | 3 unknown, 1 malformed |
| `--list-nonplanned <range>` | one id per line | 2 on a malformed range |

The checker **reads learner-visible files only**, so it is safe in study mode.

**Regression tests** (`scripts/test_course_map.py`). Each case edits one table of the real registry, writes it into a throwaway root whose content directories are symlinked from the checkout (with empty decoys for reference-path cases), and asserts an exit code plus one output line. Cases that need a module past `planned` arm a synthetic module, so the suite never depends on the in-flux status of real modules.

### 8.3 Scripts and their contracts

| script | role | key contract | study-safe? |
|---|---|---|---|
| `check_course_map.py` | registry validator, resolver, item parser | §8.2 | yes |
| `test_course_map.py` | checker regression suite | throwaway roots; exit 0 = all pass | yes |
| `course_mode.sh authoring\|study\|status` | moves L1 and L2 together | §7.4; refusal ⇒ exit 1, no side effects | the human runs it |
| `test_hooks.sh [-v]` | guard fixture replay | §7.5 | yes |
| `firsttry.sh <ID> [MODE]` | slot gate, exit scorer, hollow lint, (port) empty-body gate | §3.8.5 | yes |
| `pins.py` (port) | the golden harness: runs specimens and pinned blocks, normalizes, compares; `--update` for authors | §3.8.6 | the learner runs it on their own specimens; reference pins only in CI/author |
| `vcheck` (port) | the **pinned verifier wrapper** and fast channel: always the pinned binary, the pinned project/crate and flags; returns exit code, per-symbol status, hole count, audit findings and verified count; refuses `--allow-*`, filter flags and unsound flags in `--gate` mode | §11.1 | yes |
| `vaudit` (port) | the assumption audit (Dafny: `dafny audit` + compare-report over every file as a root; Verus: `--no-cheating` run + lint + trust allowlist) | §11.1 rows 2–3 | yes |
| `specfreeze` (port) | statement-freeze hashes (Dafny: refinement check against frozen abstract modules; Verus: signature + `requires`/`ensures`/`decreases` hash via a parser) | §11.1 | yes |
| `avoid.sh` | disjointness gate | §2.7; exit 0 clean, 1 hit/empty source/stale waiver, 2 usage | yes |
| `reference_lint.py` | CI/author lint of twins vs learner files | refuses unless `CI=true` or authoring (exit 3); output is `path:line: <rule>` only; shares the slot rules with `firsttry.sh` by marker-delimited section | **no**: the hook blocks any command naming it |
| `update_rubric_pins.sh [--check]` | rubric sha pins | pin line `<path>  sha256 <64-hex \| PENDING>[ — note]`; `--check` fails on PENDING, stale or missing targets | rewrite: author; `--check`: CI |
| `get_toolchain.sh` (port of `get_repl.sh`) | fetches out-of-graph tools | pins TAG **and** full COMMIT or sha256; refuses a moved tag or a toolchain mismatch; installs into a gitignored dir; **stdout is only the binary path** | yes |
| `challenge_gate.sh <ID>` | challenge gate | §2.3.8 | yes |

**Source names.** The source's depth-track scripts carry a `q_` prefix (`q_firsttry.sh`, `q_avoid.sh`, `q_reference_lint.py`, `q_challenge_gate.sh`) because they were added beside a shipped track. `get_toolchain.sh` is this spec's name for the source's `get_repl.sh`. A one-track port drops the prefix, as the table above does.

**Patterns worth copying:**
- one parser per grammar, imported by every consumer;
- generated lists are never committed (only the curated delta is);
- **a waiver or pin that matches nothing is an error**, so staleness is loud;
- static modes are tool-free so they can run in a cheap job;
- author-only scripts both self-check and are blocked by the guard;
- **scripts print locations, never content, whenever the content could be an answer.**

### 8.4 Build-target design

1. **The default target is the learner's exercises and nothing else.** No other target may join it. The checker enforces this, the guard forbids writing the build file (2g), and MCP builds may only build registry targets in this checkout (1b).
2. **Each track has its own library/project and root file**, whose header says what it imports and why some files are excluded.
3. **Files that must fail, or whose output is the lesson, are never in a root** (§3.1).
4. **Reference twins mirror the learner files**, with the same stem and mirror imports. A twin root's header says it is "hole-free and silent: CI-enforced".
5. **The tracks coexist.** CI builds one unit containing both roots, to prove there are no duplicate declarations.
6. **Import-tier discipline** (§2.9).
7. **The written track mirrors the build split**: `paper` vs `paper-solutions`.

### 8.5 CI (every job, and the invariant each protects)

CI runs on pushes to `main` and on pull requests only; **pushes to the learner branch never trigger it** (course changes flow main → learner branch, never back, so no learner pull request is expected). It **never calls a model** and holds no model credentials. Every job sets `defaults.run.shell: bash`, because an explicit `shell: bash` runs as `bash -eo pipefail`; without it, `build | tee` exits with tee's status and a failing step goes green.

**Job `build`:**

| step | what it does | invariant protected |
|---|---|---|
| registry consistent + checker tests | pure Python, first, fails in seconds | registry consistent and reference-free |
| install the pinned toolchain; assert versions | (port) assert the `dafny --version` / Z3 version, or the Verus `--version --output-json` / rustc / Z3 triple; verify binary sha256 | reproducibility; no PATH substitution |
| build exercises (default target) | sorry/hole warnings allowed, errors not (port: Dafny needs `--allow-warnings` here, since holes are warnings that fail by default; Verus holes are silent) | the exercises compile |
| build the second track | by name | as above |
| given/spine complete and silent | no warning or info line from given files (port: `vcheck --gate` on the given project; audit 0) | the given library is complete, frozen and prints nothing |
| tracks coexist | one unit with both roots | no duplicate declarations or leaked global effects |
| **non-root files ship in their intended state** | a table, one row per non-root file: `file, exit code, #errors, #holes, #output lines, sha256-16 of the normalized output or -` | red-by-design files fail **exactly** as intended and demos print exactly what they should. **Content-bearing output is compared by hash, so this learner-visible file never contains the answer rows.** Re-pinned on a toolchain bump |
| exercise files ship their stated hole counts | per file: hole count = the chapter's number **and** the total message count is that same number | no stray output or linter warning that would make "prints nothing" unreachable |
| demo executable behaves | build with the log to a file; run with fixed args; assert stdout, exit status and the panic string | the demo matches the lesson; the build log stays off the console because it would answer a prediction |
| build the reference | log to a file; on failure print only `file:line:col` | the reference compiles; **its log never reaches the console** |
| reference is hole-free | **from the tool's own output, never grep** (Lean: no sorry warning and no `sorryAx` in any axiom report; port: no hole warnings + audit 0 findings with every file as a root (Dafny), or `--no-cheating` zero diagnostics + lint + trust allowlist (Verus)) | grep false-positives on prose and pins, and misses a hole hidden in a dependency |
| reference lint | locations only | twins consistent with learner files |
| early modules library-free | grep with `nullglob` | import staging |
| rubric pins fresh | `update_rubric_pins.sh --check` | no stale, PENDING or orphaned rubric |
| **study mode is the shipping state** | fail if `.claude/state/mode` says `authoring`; fail if any canonical deny rule is missing | the repo never ships with the guard down |
| written track compiles | `make -C paper paper` (an empty set fails) | the learner's documents build |
| written references compile | `make paper-solutions > log`; only failing file names printed | the written references build without being printed |
| (port) golden pins | `pins.py --ci`: every pinned specimen, W item, card failure and chapter fence matches | never-invent-output; drift fails the build |
| (port) empty-body gate | `firsttry.sh --empty-body` for every non-planned module | no exercise is closed by automation alone |
| (port, nightly or on bump) brittleness | re-verify the reference under N seeds; resource-count CV under the threshold | proofs stable enough to be graded |

**Job `static` (tool-free):** import tiers, isolation, coverage, avoid, and "exercise files ship hollow". **The hollow step captures the id list first and fails if it is empty**: "`bash -e` ignores a failing command substitution in a `for` word list, so a crashed or empty listing would run the loop zero times and pass."

**Job `hook-test`:** `scripts/test_hooks.sh` (no toolchain needed).

**Planned in the source (adopt as needed):** challenge statements (sorry only on registry statements; sha pins); nested engineering packages (toolchain equality); challenge references (log to file, hole-free); harness tests (mock and scripted policies; sandbox self-test that importing the reference fails; no model called); a manual bench job.

**CI design rules:**
- pure-Python checks first, or in their own job;
- pipefail everywhere;
- logs to files, with only `file:line:col` on the console;
- holes detected from tool output, never grep;
- every intended-red or printing file pinned (counts plus a hash);
- an empty glob or empty id list is a failure;
- CI checks the *committed* state of the guard.

### 8.6 Toolchain pinning

- **Lean:** `lean-toolchain` + the dependency rev matched to it + a lock manifest. Out-of-graph tools are pinned by tag + full commit, with toolchain equality checked. Output hashes and rubric pins are re-pinned on every bump.
- **Port:** §11.1, row "toolchain file".
- **Bump policy:** at most two bumps a year, batched, with golden diffs. Budget ~1.5 MU per bump for pinned-message drift. This is critical for Verus, which releases weekly [V:doc].

### 8.7 `VERSIONS.md` (external claims to re-verify)

Three columns: `claim | value | verified-on`. A blank `verified-on` means not yet verified. Every claim the course makes about the outside world gets a row, re-verified on any toolchain bump and before a chapter relies on it. Rows distinguish "verified locally", "EXTERNAL, not checkable here" and "(partial — see value)", and concrete numbers carry their measurement date. Required port rows:
- the verifier version and binary sha;
- the solver version(s);
- the Rust toolchain and the `vstd` version (Verus);
- the IDE extension version and its pin setting;
- option defaults the course quotes (Dafny: time limit 30 s CLI / 20 s IDE, `allow-axioms` false [D:src, D:doc]; Verus: rlimit default 10 [V:src]);
- the golden message wordings the course pins (Dafny's "might not hold" → "could not be proved" rewording on master [D:lit]);
- the Claude Code permission-rule syntax, hooks schema and skill frontmatter keys;
- the MCP/wrapper tool names;
- a clean-clone dry run with the expected document count.

---

## 9. Authoring pipeline

### 9.1 The pipeline in one view

```
plan (design doc with [V]/[A] tags; author-only probe archive)
  → readers (read-only reports)  → build spec (+ critic pass; fixes applied in place)
  → per module, in this fixed order:
      (a) reference twin first: hole-free, audit-clean, SILENT, every quoted output pinned
      (b) hollow → learner exercise file (same names, signatures, statements, order)
      (c) chapter written around REAL captured output (never invented)
      (d) render every diagram; compile every .tex
      (e) planted/given/specimen files verified to fail/print EXACTLY as their headers say
      (f) instructor kit: bank, rubric (sha-pinned), fixtures, leak patterns → leak check
  → integration (one owner per shared file) → simulations in a study clone (hooks live)
  → validate agentic runs (artifact-based acceptance; one known-good transcript)
  → continuity pass → clean-clone dry run → maintenance pins (VERSIONS, golden diffs)
```

### 9.2 Phases and their acceptance criteria

| phase | content | acceptance |
|---|---|---|
| 0 infrastructure | toolchain and dependency pins; reference library; directories; README; CLAUDE.md skeleton (§Roles, access matrix, §Authoring mode, §Contractor contract with fallback rules and the learner marker); CI; paper scaffold (preamble, Makefile, answer templates); instructor scaffold (skills, CORE, hooks, deny rules, state seed); registry + checker; hook tests | **green build from a clean clone in minutes**; `make paper` compiles the skeletons; **a fresh study session is demonstrably denied** a reference read, a reference build, an MCP/wrapper import of the reference, and a heredoc into a solo tree |
| 1 pin the high-risk content first | fully prove the capstone and the hardest-theory solution **before any chapter**; draft the forensic fakes | fixes the definitions earlier modules must feed into; decides how much scaffolding ships |
| 2 modules, in learner order | steps (a)–(f) per module | the per-step checks in §9.4 |
| 3 mechanize discipline | CI checks for library staging, hollow lint, coverage, avoid | CI jobs green |
| 4 validate every agentic exercise | a real agent session per exercise | **artifact-based** acceptance; one known-good transcript recorded |
| 4b validate the instructor | headless grader over the fixtures; simulated viva/discuss; spoiler probes | planted flaw caught at the right location, dimension and grade ≤2; gold ≥3 everywhere with zero broken-step findings; zero leak-pattern hits *while still delivering legal help*. Re-run on any change |
| 5 continuity | every whisper or cliffhanger pays off; no forward references | the planted/harvested tables close |
| 6 dry run | every chapter command run verbatim from a clean clone; the capstone under the final contract | no manual intervention |
| 7 maintenance | `VERSIONS.md` with verify dates; CI rubric-pin checks; golden diffs | |

**The depth-track variant (QA0–QA7)** (L: `QPLAN.md:859-890`). The same steps, re-cut so the learner can start early:

| phase | content | acceptance |
|---|---|---|
| QA0 | one pull request: registry + checker, skill Step 0, guard hardening + `hook-test`, written-track Makefile split, the second build root, the out-of-graph tool fetcher, the plan document. After merge: create the authoring worktree | clean clone green; a fresh study session is denied a reference build, an MCP import of the reference and a heredoc into a solo tree |
| QA1 | challenge statements, references, benches and the agent harness core, **in parallel** with QA2–QA4; it gates only each topic's QA5, and ends with a resize-or-kill call per topic | artifacts build; the registry records prerequisites |
| QA2 | spine L1–L2 and the first three modules, each reference-first → hollow → chapter → kit → study-clone simulation. **The learner starts here** | both builds green; import tiers and coverage pass |
| QA3–QA4 | the remaining concept tiers, then the practice tiers with the admissibility gate and grader calibration | as QA2, plus calibration |
| QA5–QA7 | remaining challenge work and held-out sets; tier-viva and defense simulations plus gold `/contract` transcripts (zero leak hits); clean-clone dry run and `VERSIONS.md` rows | as stated |

**Pace rule.** Stay ≥1 tier ahead of the learner through the moderate tier and ≥2 tiers ahead after it. The learner's buffer is `/review` of overdue items.

### 9.3 The two laws: never invent output, pin everything

1. **Never invent tool output.** Every quoted error, value, audit row, CLI transcript or refusal text was captured live on the pinned toolchain. Where possible it is also pinned in the twin (Lean: `#guard_msgs`; port: the golden harness), so drift fails the build. Tag quotes "Live-captured (<tool> <version>)". Facts the plan relies on carry `[V: probe]` tags pointing into an author-only probe archive, which the fourth deny rule makes unreadable in study mode. Calibration evidence in the plan says only "feasible" or "infeasible"; proof details stay in the archive.
2. **Pin every external claim** (`VERSIONS.md`), every reference a rubric was distilled from (sha pins), every intended-red file's shipped state (the CI table), and every out-of-graph tool (tag + commit).

Corollaries:
- A "corrections carried forward" list records facts that probes overturned.
- Docs drift: **trust source and golden tests over prose.** Both research passes found stale documentation in the target tools (Dafny docs still naming an old option spelling; Verus docs showing an old summary-line format) [D:doc, V:src].

### 9.4 Per-module steps and exit checks

1. **Twin first.** It is hole-free (tool-counted), audit-clean, **silent** under the gate command, with every quoted output pinned and every learner statement's audit row pinned. Exit check: `vcheck --gate` exit 0 with summary only; `vaudit` 0 findings; `pins.py` green.
2. **Hollow** per the table in §3.13. Exit checks:
   - exit 0 under the learner loop;
   - exact hole count;
   - every slot unfilled;
   - declaration list = the twin's;
   - `firsttry.sh --lint-hollow` green;
   - **`firsttry.sh --empty-body` green: every hole fails when given an empty body**.
3. **Chapter** around captured output, following the quoting rules (§3.15). Predict answers appear only after their box.
4. **Diagrams and TeX** rendered and compiled.
5. **Planted, given and specimen files** produce *exactly* what their headers say. CI pins their state.
6. **Instructor kit**: bank (with verified probes and precomputed disjoint viva draws), rubric (PENDING pins → `update_rubric_pins.sh`), fixtures (flawed + gold), leak patterns (Rules 1 and 2 verified), then the leak check.
7. **Admissibility** (practice tiers): no minutes until the reference falls inside the band.
8. **Disjointness** (two tracks): `avoid.sh` clean, with no stale waivers.

### 9.5 The multi-agent authoring workflow

The source course was built by orchestrated agent workflows with a fixed shape. Reproduce it:

1. **Plan with evidence tags.** Every claim is `[V: probe]` or `[A]` (assumption or design decision). The plan carries:
   - a **decisions log** (the owner's binding decisions);
   - a **conflicts-resolved table**;
   - **open decisions with recommended defaults**;
   - an appendix **critique ledger**: `critic | issue | verdict | one-line fix` per finding.

   The source plan merged nine section drafts and four critique rounds (coverage, feasibility, challenges, repo roles). **Planning is read-only and never touches the references.**
2. **Readers.** Read-only agents write reports (house style, instructor-kit needs, infrastructure, per-module content drafts verified in scratch packages, disjointness).
3. **Build spec.** One authoritative spec synthesizes the reader reports. It records its own deltas against the drafts in a numbered table, each with a "why". It wins over the reader reports and lists every deviation from the plan. **Every format in it is verified in a scratch package before it is prescribed.**
4. **Critic pass.** An adversarial completeness critique of the spec, checked line by line against the plan, with its own probes. Findings are ranked **blocker / major / minor**. Blockers and majors are applied in place, each marked `(critic fix N)`; minors are listed.
5. **Lanes with single owners.**
   - Stages run in order: spine/given → (reference-first ∥ infrastructure) → (hollow ∥ gate scripts) → integration (serial, one agent) → chapters (parallel) → instructor kit → simulations (serial) → ship.
   - **Lanes in a stage run in parallel only because they own disjoint files; a lane never edits another lane's file.** Shared files (registry, build files, roots, CI) each have one named owner per stage.
   - Each stage has an explicit exit check (e.g. "exit 0, exact hole count, every slot unfilled, declaration list = twin's").
   - **Lane briefs include:** the spec path, the owned files, the reader section to start from, the applicable deltas, and **"never write answers or reference text into a learner-visible path"**, because the hook stands down in authoring mode.
6. **Built-deltas log.** Each lane reports `deviations` and `open_issues`. The log is "authoritative over the spec wherever they differ: these describe the files AS BUILT". Open issues are routed to the owning lane.
7. **Adversarial verify, then fix rounds.** Rounds 1–3 per module go back to the owning lanes. Integration fix-ups also go back to the owner rather than being patched in place.
8. **Simulations, then acceptance.** Run in a throwaway **study clone**: no mode file, all deny rules, hooks live. The author plays a confused learner through every skill:
   - tutor rungs 1→5, including the parallel problem;
   - "just give me the answer", which must name the reference path and stop;
   - discuss;
   - viva draws A and B;
   - code-review refusal on hollow files;
   - contract dry runs (allowlist exact, emptied at close);
   - the hook-deny demo through three doors.

   Pass: **zero leak-pattern hits over every captured emission** (checked outside the clone), with help still legal. The captured refusal texts then go into the chapters: real output again.
9. **Ship** on a clean-clone run. Open a pull request only after the owner says so.
10. **Worktree isolation.** All of this happens in the dedicated authoring worktree. Concurrent workflows MUST NOT edit the same files. Assign file ownership across workflows exactly as across lanes.

### 9.6 Lessons learned (each was a real defect or near-miss)

| lesson | what happened / the hazard | the rule that resulted |
|---|---|---|
| **Vacuous checks** | an empty substring pin passes on any output; a value slot passes if the learner retypes the left-hand side; a check that echoes its own command passes | lint: ≥8 non-space characters; no echo; literal-form right-hand sides; no severity prefixes (§3.8.4) |
| **The IDE reveals predict answers** | a goal slot inside a proof shows the answer in the editor as it is typed; hovers and lightbulbs leak; a wrong substring re-emits the true message | goal slots dropped; commit-before-hover rule; first try recorded in scratch before enabling; **port: specimens ship with an IDE-ignored extension** |
| **Slot echo hazards** | `#check`/`#print`/many errors repeat the command text | fragments may not occur in their own item's source |
| **Commented-check counting** | a grep for one keyword missed commented `example`s and theorems | every non-prose line under the header counts |
| **Deleting a slot passed for filling it** | the gate compared against the working file | the "as shipped" baseline is the merge base with `main` |
| **Files that must fail kept out of builds** | importing a red file reddens everything; importing a printing file spoils a prediction | never in a root; CI pins exit, counts and an output hash |
| **Failing named declarations pollute** | Lean adds a failed named declaration anyway | error predicts use anonymous `example`; port: one specimen per file |
| **Guard self-protection** | a session could edit its own hook, settings or build file; the live hook guards the session editing it | rule 2g; edit a copy and install only when `test_hooks.sh` is green |
| **Guard bypasses** | a red-team replay found 11 of 12 bypasses exiting 0: MCP tools, module-name imports, Bash writes, symlinks, git history, build-artifact dirs | every bypass becomes a must-block fixture, with rule attribution |
| **The two layers must move together** | authoring with hooks down but deny rules up locked the author out (rubric pins could not be computed) | `course_mode.sh` moves both; CI checks the shipped state |
| **Authoring mode leaking into study** | a mode file in the learner checkout would disarm the guard | the hook verifies linked-worktree + non-learner-branch itself |
| **Grep is not a hole counter** | comments legitimately say "sorry"; pins can swallow warnings; holes hide in dependencies | the tool's own output plus an audit, never grep |
| **Logs replay answers** | the reference build log prints `#eval` rows; a demo's build log prints audit rows that answer a prediction | logs to files; locations only; hash content-bearing output |
| **Empty lists pass loops** | `bash -e` ignores a failing command substitution in a `for` list | capture the list first; empty = failure |
| **`tee` hides failures** | without pipefail, `build \| tee` is green | `defaults.run.shell: bash` |
| **Language server indexes references** | workspace-symbol search lists reference names | neutral names for reference-only helpers |
| **Rubric authors cannot read references** | sha pins cannot be computed in study mode | write `PENDING`; the author or CI fills it in; `--check` fails on PENDING at ship |
| **Stale pins and waivers** | a renamed target was silently skipped | a pin or waiver that matches nothing is an error |
| **Unbudgeted minutes** | cards, briefs and contract rewrites had no minutes | every activity gets a line; modules reconcile to their total |
| **Uncalibrated hard items** | "feasible" claims without a reference | the admissibility gate with named fallbacks |
| **Usage limits** | subscription rate limits interrupt long agent runs and could turn a frozen run into best-of-n by restart | per-run and rolling-window call caps; checkpoint-and-resume; develop on local models; CI never calls a model; author runs are batched per toolchain bump |
| **First-run stalls** | a fresh isolated agent config stalled >400 s on first use | a warm-up call before any timed run |
| **Docs drift** | tool docs lag the code | trust source and golden tests; re-probe on the pinned binary |
| **Concurrent editors** | two workflows touching the same files corrupt each other's state | single-owner files across workflows; reports go to scratch, never into learner-visible paths |

---

## 10. Repository layout template

### 10.1 Dafny

```
<course>/
  README.md  CLAUDE.md  PLAN.md  [QPLAN.md]  VERSIONS.md  MODULES.toml
  .config/dotnet-tools.json          # OR a pinned release zip + its sha256 in VERSIONS.md (decision OD5)
  Course/
    dfyconfig.toml                   # THE default project: includes Course/**/*.dfy minus agent-red, exit,
                                     # demo and specimen files; [options] = the pinned flag set
    R01_Hello.dfy  R01_AgentRepair.dfy (not in includes)  Q01_Sweep.dfy  Q01_Map.dfy (exit; not in includes)
    Given/Spine_L1.dfy …             # frozen given layers (also included by Solutions/dfyconfig.toml)
    Support/                         # scaffolds, skeleton scripts
    specimens/<ID>/<item>.dfy.specimen
  Solutions/
    dfyconfig.toml                   # the reference project: Solutions/**/*.dfy + Course/Given/**; verified ONLY by name
    R01_Hello.dfy …                  # twins: same stems, same module names as the learner files
  Challenges/  agents/               # solo trees (rule 2s)
  tools/<ID>/                        # learner-owned tool dirs (allowlist-gated)
  docs/<ID>_<Name>.md
  paper/ Makefile preamble.tex template_problems.tex template_answers.tex
         <ID>_problems.tex <ID>_answers.tex rubrics/<ID>_rubric.md solutions/<ID>_solutions.tex
  instructor/ ledger.md gradebook.md feedback/ records/ calib/ scratch/ (gitignored)
  expected/                          # pinned audit reports and normalized golden outputs (author-written)
  scripts/ check_course_map.py test_course_map.py course_mode.sh test_hooks.sh firsttry.sh pins.py
           vcheck vaudit specfreeze avoid.sh reference_lint.py update_rubric_pins.sh get_toolchain.sh
           challenge_gate.sh
  tests/hooks/{must_block,must_allow}.jsonl
  tests/instructor/fixtures/<ID>_{flawed,gold}_answers.tex  tests/instructor/leak_patterns/<ID>.txt (read-denied)
  .claude/settings.json  .claude/hooks/{spoiler-guard.sh,review-due.sh}  .claude/state/ (gitignored)
  .claude/skills/{tutor,discuss,review,viva,grade-paper,review-code,contract}/SKILL.md
  .claude/skills/instructor/{CORE.md,personas.md,concepts.md,banks/<ID>.md}
  .vscode/settings.json              # "dafny.version": "<pinned>", never "latest"
  .github/workflows/ci.yml
```

**Dafny-specific wiring notes.**
- **Never use `include` in learner files.** Included files are not verified by default, and `dafny audit` skips included code [D:src, D:doc]. Instead, make every file a project root through the `dfyconfig.toml` includes glob. Cross-file `import` of modules then works within one project [verify].
- **Dafny has a single global module namespace** [D:doc]. The learner project and the reference project MUST never be verified together, and the two tracks MUST use distinct top-level module prefixes. The coexistence check verifies both tracks' learner files together.
- The IDE searches upward for the nearest `dfyconfig.toml` [D:doc]. A stray project file in a learner subdirectory changes what the IDE checks, so CI fails on any `dfyconfig.toml` outside an allowlist.
- Project options override `dafny server` arguments [D:doc]. That makes the project file security-relevant, which is why it is on the 2g never-written list.

### 10.2 Verus

```
<course>/
  README.md  CLAUDE.md  PLAN.md  [QPLAN.md]  VERSIONS.md  MODULES.toml
  rust-toolchain.toml                # exactly the rustc the pinned Verus release requires
  Cargo.toml                         # the LEARNER workspace: members = ["given", "course"];
                                     # exclude = ["Solutions"]  — the reference crate is NOT a member
  given/                             # frozen spine crate: Cargo.toml ([package.metadata.verus] verify = true;
                                     # vstd = "=<pinned>"), src/lib.rs with l1.rs … l7.rs
  course/                            # learner crate
    Cargo.toml  src/lib.rs           # lib.rs declares `mod r01_hello; …`: that is the root import list
    src/r01_hello.rs …               # agent-red, exit, demo files are NOT mod-declared
    src/agents/q01_agent_repair.rs   # (not mod-declared; checked standalone)
    specimens/<ID>/<item>.rs.specimen
  Solutions/                         # reference crate (package name `solutions`), its OWN workspace root
    Cargo.toml                       # [workspace] of its own; path dependency on ../given; mirrors course/src;
                                     # verified ONLY by `cargo verus verify --manifest-path Solutions/Cargo.toml`
  Challenges/  agents/  tools/<ID>/
  docs/ paper/ instructor/ expected/ scripts/ tests/ .claude/   (as for Dafny)
  .vscode/settings.json              # "verus-analyzer.verus.verusBinary": "<pinned path>"
  .github/workflows/ci.yml
```

**Why the reference crate sits outside the learner workspace.** The Verus guide says `cargo verus verify` with no `-p` "runs verification on all crates that have `verify = true`, including dependencies" [V:doc: guide `cargo_verus.md`]. Whether a `default-members` list narrows that is unknown (probe P13). If the reference crate were a workspace member, a bare `cargo verus verify` (by the learner, or by Claude in study mode) could verify it and print its diagnostics, which breaks wiring rule 3.1-1. Excluding it makes "the default target is the learner's exercises and nothing else" hold by construction, as Lean's `defaultTargets` does. Keep the directory name `Solutions` (capitalized, a distinctive bare word, §7.1) and add the crate name `solutions` to the hook's bare-word list. Verus's own `-p` and `--manifest-path` forms both go on the rule-1b list.

**Verus-specific wiring notes.**
- A crate is verified only if it opts in with `[package.metadata.verus] verify = true`. **Plain `cargo build`/`cargo test` compile without verifying** [V:doc]. Every gate MUST call `verus` or `cargo verus verify` explicitly and parse its JSON result.
- Passing `--verify-module`/`--verify-function` through cargo "is unlikely to work" [V:doc]. The fast channel therefore calls `verus` directly on the crate root, with `--crate-type=lib` [V:src].
- The verus-analyzer IDE auto-downloads the latest Verus unless pinned [V:doc]. Ship the pin in `.vscode/settings.json` and put that file on the 2g list.
- Code outside `verus!{}` is ignored by the verifier [V:doc]. A lint MUST require all learner logic inside `verus!`.

### 10.3 `CLAUDE.md` skeleton

`CLAUDE.md` is the one file every Claude session in the repo loads, so it carries the role rules. It ships in Phase 0 with everything above the learner marker. Below the marker it is empty until the learner writes contract v0 (L: `CLAUDE.md:1-95`).

```markdown
# CLAUDE.md — <course>
<one paragraph: the tracks; the build commands (default target, second track, `make -C paper paper`);
"a hole is a typed placeholder; green with zero tool-counted holes is done"; MODULES.toml is the registry,
resolved through `python3 scripts/check_course_map.py --resolve <ID>`; pointers to PLAN/README>

## §Roles
<the four hats; "modes are entered only by their skill">
### Access matrix            <the table of §6.1, verbatim>
<enforcement is layered, hard first: deny rules, spoiler-guard.sh, the instructor contract; degradation is soft, never silent>
### Session hygiene          <the four bullets of §6.1, verbatim>
### Authoring mode           <§7.4: the mode file, linked worktree only, the four canonical deny rules named
                              literally, "never flip either by hand", CI fails on a shipped mode file>

## §Contractor contract
<who writes v0 and when; until then the fallback rules (build after every edit; done = green + zero holes +
acceptance artifacts; never weaken a spec to get green; edits only inside the allowlist)>
Learner contracts add to the `/contract` fallback rules; the stricter rule wins.

<!-- learner-owned below: contract v0/v1/v2 -->
```

---

## 11. TRANSLATION GUIDE (Lean → Dafny → Verus)

This section is the one to build from. §11.1 maps every mechanism the design relies on. §11.2 remaps the strands and threshold concepts. §11.3 sketches the module remap. §11.4 gives the fake-green catalogs. §11.5 says what does not transfer and how to redesign it. §11.6 lists the probes to run before anything ships.

**Version baseline** (pin these or newer, then re-probe everything):
- **Dafny 4.11.0** (2025-08-25; only nightlies since, through 2026-10-02). Bundled Z3 4.12.1 (default) and 4.14.1 [D:src].
- **Verus release `0.2026.09.27.3cf1832`**, with Rust 1.98.1, Z3 4.16.0 bundled and version-checked, and `vstd = "=0.0.0-2026-09-20-0158"` per the cargo-verus toolchain manifest [V:src, V:live]. Verus ships weekly [V:doc].

### 11.1 Mechanism mapping table

Legend for the last column: **=** the guarantee transfers; **≈** partial, with the stated substitute; **✗** absent, with the redesign stated.

| # | Lean mechanism | what the design needs from it | Dafny | Verus | |
|---|---|---|---|---|---|
| 1 | **`sorry`** (typed hole, warning, exit 0) | a typed placeholder; the rest of the file still checked; one counted diagnostic per hole | bodyless `lemma`/`method` with `ensures` in a concrete module, or `assume false;`. Each emits a **warning** (a bodyless declaration emits one per `ensures` clause, so a hole carries exactly one), and **warnings fail by default** (exit 2, "Compilation failed because warnings were found and --allow-warnings is false") [D:src, D:lit]. Learner loop: `--allow-warnings`. Never `{:axiom}`, which is silent [D:doc]. Bodyless members of an `abstract module` or a trait do **not** warn [D:src]: lint them | `#[verifier::proof_note("<item>")] assume(false);` for proofs; `#[verifier::external_body]` + `unimplemented!()` for exec bodies. **Silent**: green, no warning [V:src]. Counted by a second run with `--no-cheating`, which turns each into a deferred error, all reported in one run [V:src] | ≈ |
| 2 | **"zero sorries, counted by the compiler"** (done predicate) | one objective done check shared by humans, CI and agents | done = `dafny verify <project>` exits 0 **without** `--allow-warnings` **and** `vaudit` reports 0 findings [D:src]. Hole count = matching hole-warning lines (message wording is version-specific [D:lit]) | done = `verus --output-json` with `success: true`, `is-verifying-entire-crate: true`, `encountered-vir-error: false` **and** `verus --no-cheating` with zero diagnostics **and** lint zero [V:src] | ≈ |
| 3 | **`#print axioms`** (transitive, per theorem) + the `sorryAx` check | the assumption audit; the agent-file dashboard; "hole in a helper" detection | `dafny audit`: per-declaration rows, **non-transitive**, **exits 0 even with findings**, **skips code from `include`**. `--report-file X --report-format md --compare-report` exits 2 on mismatch and acts as a golden audit [D:src]. Substitute for transitivity: audit the **whole program with every file a project root**; any row anywhere fails | **no built-in audit** [V:src]. `-V axiom-usage-info` reports broadcast usage, not trust [V:doc]. Build `vaudit` = `--no-cheating` run + source lint (§11.4) + spec-freeze diff + a trust allowlist for reference crates. Dependency reach: `--log call-graph` [V:src; usefulness: verify] | ≈ |
| 4 | **`#eval`** | run code and see the value | `dafny run` (compiles; default target C#) [D:doc]. No REPL | spec functions: `assert(e == v) by (compute_only)` [V:doc]; exec functions: `verus --compile` + run, or `cargo run` (which does **not** verify) [V:doc] | ≈ |
| 5 | **`#guard`** (in-file executable check) | executable specs; the escalation ladder's second rung | `method {:test}` with `expect`, run by `dafny test` (prints `PASSED`/`FAILED` per test) [D:src]. `expect` is **assumed by the verifier** [D:doc], so allow it only inside tests (lint). A misspelled `{:test}` is silently never run [D:doc]: count the expected `PASSED` lines | exec: `#[test]` with `assert_eq!`, outside `verus!` or marked `#[verifier::external]`, run by `cargo test` [verify, probe P6]; spec: `by (compute_only)` | ≈ |
| 6 | **`#guard_msgs`** (pin exact tool output in-file; keeps drift visible; error/info/type predicts; card failures) | never-invent-output enforcement; error predicts | **no in-file equivalent**. Golden harness `pins.py` + specimens (§3.8.6). Channels: `--json-output` [schema: verify], `--log-format csv\|trx\|text`, `--use-basename-for-filename`, `--show-snippets` [D:src]. Precedents: `lit` + `.expect` files with `// RUN:` lines; `<!-- %check-verify X.expect -->` markdown fences [D:lit, D:doc] | **no in-file equivalent**. Channels: `--output-json` (summary, per-function `success` with `--time`, `failed_proof_notes`), rustc `--error-format=json` diagnostics with spans, `#[verifier::proof_note]`/`custom_err` for wording-independent ids [V:src]. Precedent: `// FAILS` line markers in Verus's own tests [V:src] | ≈ |
| 7 | **`#guard_msgs (drop all)`** (an unfilled slot stays silent and hidden) | an unfilled slot neither reddens the build nor reveals the answer | specimens outside every project, with an IDE-ignored extension; the slot lives in the specimen header or a slot file | same | ≈ |
| 8 | **`#guard hash ans == pin`** (verdict) | a non-code answer that ships only as a hash | harness compares the sha256 of a normalized string | same | = |
| 9 | **anonymous `example`** for failing specimens | failures don't pollute later items | one specimen per file | same | = |
| 10 | **goal view / InfoView / `guard_target`** | read the state; "predict the goal"; tutor rung 3 | **no goal state.** Use intermediate `assert`s, `assume false` bisection, per-assertion isolation (`--isolate-assertions`, `{:isolate}`, `--filter-position=file:LINE`) [D:src], IDE gutter icons and the verification trace (counterexample, a "hint, might not be real") [D:doc], hover over chosen/rejected triggers [D:doc] | **no goal state.** Use assert/assume bisection (taught in the guide) [V:doc], `--expand-errors` sub-clause blame [V:src], `recommends` notes, `--triggers` [V:src] | ✗ → redesign: "predict the goal" becomes "predict which obligation fails" (`obligation` format) |
| 11 | **tactics** (and WRITE/RECOGNISE slugs) | a schedule of proof moves, each first done by hand | proof constructs and knobs as slugs: `assert`, `assert-by`, `calc`, `forall-stmt`, `lemma-call`, `reveal`, `opaque`, `decreases`, `invariant`, `induction-false`, `induction-auto`, `fuel`, `trigger`, `isolate`, `by-method` [verify names at the pinned version] | `assert`, `assert-by`, `assert-forall`, `calc`, `proof-fn`, `proof-block`, `reveal`, `reveal-with-fuel`, `decreases`, `invariant`, `trigger`, `broadcast-use`, `nonlinear-arith`, `bit-vector`, `integer-ring`, `compute` [V:doc] | ≈ |
| 12 | **heavy automation** (`simp`, `omega`, `grind`, `aesop`) and the whole-problem automation gate | items must not fall to one button | SMT itself + **auto-induction** (on by default; `{:induction false}`, `--manual-lemma-induction`) [D:doc, D:src]; `--disable-nonlinear-arithmetic`; `opaque` + `reveal`; lower fuel. **Empty-body gate**: every hole with `{}` MUST fail | SMT + `by (nonlinear_arith)`, `by (bit_vector)`, `by (integer_ring)` (needs Singular 4.3.2), `broadcast use` groups [V:doc]. Empty-body gate with each automation knob tried | = (as a gate) |
| 13 | **`rfl` / `decide`** (computation) | predict values; definitional reasoning | static `assert F(3) == 9;` is **proved, not evaluated**, and can fail on fuel (default 1,2) [D:doc]; evaluation goes through compilation (`dafny test`) | `by (compute_only)` evaluates in Verus's interpreter; a plain `assert` may be proved by SMT or fail for lack of fuel (default 1) [V:doc] | ≈; teach the difference |
| 14 | **`plausible`** (property testing) | the third rung of the escalation ladder; solo truth probes | no built-in property tester [verify]; hand-rolled bounded/exhaustive `expect` loops in `{:test}` methods; `generate-tests` is experimental [D:doc] | Rust `proptest`/`quickcheck` in `#[test]` outside `verus!` [verify] | ≈ |
| 15 | **`lake build`** (default target = exercises) | the access-control surface | `Course/dfyconfig.toml`. **The CLI uses no project file by default** [D:doc], so the wrapper always passes it | a learner workspace whose members are only `given` and `course`, with the reference crate excluded (§10.2); the wrapper still passes `-p course` explicitly. `default-members` alone is not enough until probe P13 says so | = |
| 16 | **`lake build Solutions`** (by name only) | references never built by accident | `dafny verify Solutions/dfyconfig.toml` | `cargo verus verify --manifest-path Solutions/Cargo.toml` (its own workspace) | = |
| 17 | **`lake env lean <file>`** (single-file check) | specimens, planted files, probes | `dafny verify <file>` with the pinned flags (a standalone file must not need project modules; specimens are self-contained) | `verus <file> --crate-type=lib` with the pinned flags [V:src] | = |
| 18 | **`lakefile.toml`** | build wiring; a 2g never-written file | `dfyconfig.toml` (`includes`, `excludes`, `base`, `[options]`). Option names without `--`; command-line options win; options invalid for every command only warn [D:doc] | workspace and crate `Cargo.toml`, `[package.metadata.verus] verify = true` [V:doc] | = |
| 19 | **`lean-toolchain`** + dependency rev + lock manifest | reproducibility; IDE agreement | **either** the release zip `dafny-4.11.0-<platform>.zip` with its sha256 (it bundles Z3, so solver resolution is deterministic) **or** a `.config/dotnet-tools.json` tool manifest plus a separately pinned Z3 4.12.1 passed with `--solver-path`. Otherwise Dafny falls back to **any `z3` on PATH** [D:src]. CI: `dafny-lang/setup-dafny-action@v1` with `dafny-version` [D:doc]. IDE: `"dafny.version": "4.11.0"`, never `latest` [D:doc] | the triple (Verus release tag, Rust toolchain, Z3) + `vstd = "=…"`. `rust-toolchain.toml` matches the release; the launcher checks the toolchain via rustup; Z3 version is checked unless `-V no-solver-version-check` [V:src]. IDE: `verus-analyzer.verus.verusBinary` pinned [V:doc] | = |
| 20 | **Mathlib** (heavy library, staged) | library strand; import tiers | opt-in standard libraries `--standard-libraries`, modules `Std.*`, versioned with Dafny (4.11.0 changed an API) [D:src] | `vstd` (always present) + broadcast groups; std specs [V:doc] | = |
| 21 | **search ladder** (`exact?` → loogle → leansearch → community) | the library strand; retriever race | no in-language search. Ladder: IDE hover / go-to-definition → grep the stdlib source → stdlib docs → LLM search → community [verify the channels] | IDE → grep `vstd` → verusdoc API pages → LLM search → community [V:doc for verusdoc; others: verify] | ≈ |
| 22 | **lean-lsp MCP fast channel** vs `lake build` slow channel | latency economics; agent per-edit feedback | **no official MCP**: the dafny-lang organisation lists none as of 2026-10-02. One community server writes a temp file and returns the first 1000 chars of stdout, ignoring the exit code and the audit, so it is not course-grade [ext: third-party repository inspected 2026-10-02; verify before naming it]. Build `vcheck`: `--filter-symbol`/`--filter-position` + `--isolate-assertions` for per-symbol checks [D:src]; LSP custom methods `dafny/textDocument/verifySymbol`, `dafny/verification/status/gutter`, `dafny/counterExample` [D:src] | **no official MCP** [V:live]. `vcheck` = `verus --verify-only-module M --verify-function F --output-json --error-format=json` (`--verify-function` needs `--verify-only-module` or `--verify-root`) [V:src]. The guide's own recommendation is "coding agent + CLI + cheat checker" [V:doc] | ≈ (build it; guard it like any tool) |
| 23 | **REPL** (JSON door; the "machine" door) | interfaces strand; a 20-line agent | none; the JSON/CSV outputs and `dafny server` (LSP-compliant as of 4.11.0) are the machine doors [D:doc] | none; `--output-json` and rustc JSON are the doors [V:src] | ≈ |
| 24 | **kernel + 3 axioms + re-checkers** | the trust story; "disputes go to the kernel" | **no kernel, no proof objects, no independent re-checker** [D:doc]. TCB: front end, Dafny→Boogie translator, Boogie prelude axioms, Boogie, Z3, plus target compiler/runtime, `{:extern}` code and any `--plugin` [D:doc]. Open `logic`-labelled soundness issues: 3 on 2026-10-02 [D:live] | **no kernel, no proof objects, no re-checker** [V:src]. TCB: rustc + Verus's forks of rustc crates, `builtin_macros` with a forked `syn`, the VIR→SST→AIR→SMT encoding, Z3 (+ cvc5/Singular if used), vstd's trusted sites (raw grep: ~283 `external_body`, ~184 `axiom fn`, ~485 `assume_specification`, ~43 `admit()`), codegen [V:src] | ✗ → redesign (§11.5) |
| 25 | **planted errors** (elaboration continues past errors) | k bugs = k diagnostics | stages stop early: exit codes 1 (CLI), 2 (parse/resolution, *and* warnings), 3 (compile), 4 (verification, including timeouts) [D:src, D:doc]. Whether verification runs after a resolution error: [verify] (likely not) | rustc errors stop before verification; VIR errors are deferred and batched; exit 1 on any error [V:src] | ≈ → one stage per planted file, or make stage order the lesson |
| 26 | **`native_decide`** (trust compiled evaluation) | a fake-green species; "tested, not proved" | `expect` outside tests (assumed); `{:extern}` trusted results [D:doc, D:src] | `external_body` exec fns; runtime tests passed off as proofs | = (as a species) |
| 27 | **`implemented_by` / `extern`** | the trust gap between spec and implementation | `{:extern}` with `ensures` warns unless `{:axiom}` or `--allow-external-contracts`; `function … by method` **is verified** (not a trust leap) [D:src, D:doc] | `external_body`, `assume_specification`, `external_fn_specification`, `external_type_specification` (the last possibly not caught by `--no-cheating`: verify P3) [V:src] | = |
| 28 | **`partial` / `unsafe` / `decreasing_by sorry`** | totality ⇒ consistency | `decreases *` (methods and loops only; partial correctness; audit reports it); lemmas and functions must terminate [D:doc, D:src] | `#[verifier::exec_allows_no_decreases_clause]` (green even under `--no-cheating`: verify P4); `assume_termination` (caught); exec termination is modular ("assuming callees terminate") [V:src, V:doc] | ≈ |
| 29 | **Expr identity** (statement freeze; X06/X09 detection) | weakened statements detected mechanically | **module refinement**: a frozen `abstract module Spec` with bodyless lemmas; the learner writes `module Impl refines Spec`; the child may add `ensures` but must satisfy every parent `ensures` [D:doc]. Lint: learner modules concrete. Plus a normalized spec-text hash. (DafnyBench's spec-text comparison is a cautionary, bypassable example [D:doc].) | hash each frozen function's signature + `requires`/`ensures`/`decreases` (+ exec body where frozen) via a parser (tree-sitter-verus; `lynette compare` is prior art) [V:doc; verify] | ≈ |
| 30 | **per-file `set_option`** | quoted output matches the learner's view | flags live in `dfyconfig.toml [options]`; a module-scoped subset via `module {:options "--…"}` (e.g. `--manual-triggers`, `--manual-lemma-induction`, `--disable-nonlinear-arithmetic`); `--allow-axioms`/`--allow-warnings` are global only [D:src] | flags live in the wrapper and the crate metadata; `#[verifier::rlimit(n)]`, `#[verifier::opaque]` per item [V:doc] | = |
| 31 | **exe demo "exit 0 with sorry"** (TC3) | green with a hole is not done | `assume {:axiom} P;` is silent in verification, and the compiler refuses only `assume` *without* `{:axiom}` and bodyless compiled members [D:doc], so the annotated form should compile and run: a program that runs with an unproven assumption [verify that it compiles and runs] | an `external_body` + `unimplemented!()` exec function panics **only when reached**; `admit()` is erased [V:doc] | = |
| 32 | **heartbeats** (deterministic limits) | reproducible verdicts | `--resource-limit` (deterministic) instead of `--verification-time-limit` (default 30 s CLI, 20 s IDE; `0` = no limit, a DoS vector) [D:src, D:doc] | `--rlimit` (default 10, "roughly seconds"); `rlimit(infinity)` is a hazard; an rlimit hit counts as an error [V:src] | ≈; brittleness becomes a topic (§11.5) |
| 33 | **`#print` of the term behind a tactic proof** | the pipeline strand: "everything elaborates to a kernel term" | Boogie and solver dumps via Boogie pass-through options [verify the exact flags]; `--log-format` per-batch results [D:src] | `--log vir\|air\|smt\|triggers\|call-graph` into `.verus-log/` [V:src] (a side channel when run on the reference, §7.2) | ≈ |

### 11.2 Strand remapping (S1–S12) and threshold concepts

#### 11.2.1 Dafny

| strand | Lean | Dafny strand | mark | content sketch |
|---|---|---|---|---|
| S1 | Data & programs | **Data & programs** | keep | `datatype`, `match`, compiled `function` vs `method`, `seq`/`set`/`map`, classes and arrays, `dafny run`; a first gotcha, e.g. `nat` subtypes and subtraction |
| S2 | Props as types & logic | **Specifications & logic** | REDESIGN (moderate) | `requires`/`ensures`, `predicate`, quantifiers, `old`, `reads`/`modifies` frames, `ghost` declarations; first-order logic as a spec language |
| S3 | Tactics & goal states | **Proof statements & verifier feedback** | REDESIGN | `assert`, `assert … by`, `calc`, lemma calls, the `forall` statement, assertion bisection, `--isolate-assertions`, gutter and counterexamples; fast vs slow channel |
| S4 | Induction & equational reasoning | **Induction, recursion & loops** | keep | lemmas by recursion, `decreases`, auto-induction vs `{:induction false}`, **loop invariants as the induction hypothesis**, `calc` chains, `assume`-driven decomposition |
| S5 | Libraries & search | **Libraries & search** | keep | standard libraries, `import`/`opened`, refinement as library design, the search ladder, hand-first-then-library |
| S6 | Typeclasses, monads & effects | **Abstraction, modules & effects** | REDESIGN (moderate) | traits, modules, `abstract module` + refinement, `opaque`/`reveal`, the heap and `modifies`, dynamic frames, failure-compatible types and `:-` (Dafny's monadic sugar) |
| S7 | Dependent types & totality | **Ghost vs compiled, subset types, termination** | REDESIGN (moderate) | ghost erasure; subset types `type T = x: int \| P(x) witness …` and `newtype`; the invariant-enforcement spectrum (runtime check → `Option` → subset type → ghost invariant); `decreases`, `decreases *`, partial correctness |
| S8 | Type theory & foundations | **Program-logic foundations** | REDESIGN (major) | Hoare triples as judgments; wp/VC calculation by hand; soundness of a small program logic; classical first-order logic + theories; the "golden triangle" analogue (*termination of lemmas ⇒ sound induction; undecidability of FOL + quantifiers ⇒ triggers, incompleteness, timeouts*); a certificate-producing checker (e.g. a verified VC generator for a tiny language) |
| S9 | Compiler interfaces & tooling | **Verifier interfaces & tooling** | keep | the CLI commands (`resolve`/`verify`/`build`/`run`/`test`/`audit`/`format`/`measure-complexity`/`server`), `dfyconfig.toml`, exit codes, JSON and logs, LSP by hand, the "doors" (IDE/LSP, CLI, project, wrapper/agent) |
| S10 | Pipeline, elaboration & kernel | **Pipeline & trust base** | REDESIGN (moderate) | parse → resolve/typecheck (ghost inference) → Boogie → VC generation → Z3 → compile (erasure); TCB inventory; prelude axioms; `{:extern}` trust; stage attribution by exit code and message |
| S11 | Syntax extension & metaprogramming | **SMT mechanics: quantifiers, triggers, fuel, opacity, brittleness** | REDESIGN (replace) | triggers and matching loops, `{:trigger}`, `--manual-triggers`; fuel; opaque/reveal; nonlinear arithmetic; resource limits; `measure-complexity` + coefficient-of-variation gates; assertion batches and splitting. (Dafny has attributes and .NET plugins, but plugins are out of learner scope) |
| S12 | Verifier loop, trust & agents | **Verifier loop, trust & agents** | keep | the hole contract, the escalation ladder, the Dafny fake-green catalog (§11.4), audits, contracts, red-teaming, the thesis with the "don't know" caveat |

#### 11.2.2 Verus

| strand | Verus strand | mark | content sketch |
|---|---|---|---|
| S1 | **Data & programs (Rust inside `verus!`)** | keep | structs and enums, `Vec`, exec fns, `--compile`; machine-integer overflow obligations as an early surprise |
| S2 | **Specifications & logic** | REDESIGN (moderate) | `spec fn`, `requires`/`ensures`, `forall`/`exists`/`choose`, `int`/`nat`, `Seq`/`Set`/`Map`, `open` vs `closed` spec, `recommends` (unchecked unless the proof fails; `spec(checked)`), spec partiality (division by zero is an unspecified value) |
| S3 | **Proof statements & verifier feedback** | REDESIGN | `proof fn`, `proof { }`, `assert … by`, `assert forall`, `calc!`, prover modes, assert/assume bisection, `--expand-errors`, the fast channel |
| S4 | **Induction, recursion & loops** | keep | `decreases`, lemma recursion, loop `invariant`s, `reveal_with_fuel` |
| S5 | **Libraries & search (vstd)** | keep | vstd collections and lemma libraries, `broadcast use` groups, std specs, verusdoc, hand-first rule |
| S6 | **Traits, ownership & effects** | REDESIGN (moderate) | traits with specs, `&mut` arguments in specs, `Result`/`Option`, the interaction of borrowing and specifications [verify syntax at the pinned version] |
| S7 | **Modes, ghost & tracked, erasure, termination** | REDESIGN (moderate) | spec/proof/exec modes and call rules; `Ghost<T>`/`Tracked<T>`; erasure and the `cfg(verus_only)` hazard; exec termination is modular; `exec_allows_no_decreases_clause` |
| S8 | **Program-logic & ownership foundations** | REDESIGN (major) | Hoare/wp by hand; VCs; linear/affine ghost permissions (`tracked`, points-to) as a separation-logic primer; soundness of mode checking; the same "golden triangle" analogue as Dafny |
| S9 | **Verifier interfaces & tooling** | keep | `verus` flags, `--output-json`, rustc JSON, `cargo verus verify/focus/build`, verus-analyzer, verusfmt `--check`, the "doors" |
| S10 | **Pipeline & trust base** | REDESIGN (moderate) | rustc HIR → VIR → SST → AIR → SMT; the second rustc pass with ghost code erased (lifetime and erasure checks); TCB inventory; `--no-cheating`; why `--no-lifetime`/`--no-erasure-check` are unsound |
| S11 | **SMT mechanics: triggers, fuel, opacity, brittleness** | REDESIGN (replace) | `#[trigger]`, `#![auto]`, `#![all_triggers]`, matching loops, auto-chosen-trigger notes, `--triggers`; fuel; `opaque`/`reveal`; rlimit; `spinoff_prover`; profiling; seeds. The `verus!` macro itself is the one syntax-extension fact [R] |
| S12 | **Verifier loop, trust & agents** | keep | as for Dafny, with the Verus catalog and published agent-cheating rates (VeruSAGE, arXiv 2512.18436v2: without a checker, one model "cheated in 14% of the proof tasks") [ext; the paper exists, the figure is from the research notes, so re-read it before quoting]; the Verus guide's own LLM advice ends with "run the cheat checker" [V:doc] |

**Families.** Keep A = S1–S5, B = S6–S8, C = S9–S12, but **re-measure new payload per family** (§2.3.2). S8 and S11 are the redesigned strands and will carry the most new material.

#### 11.2.3 Threshold concepts (port)

| TC | concept | Lean ancestor |
|---|---|---|
| TC1 | A spec is a logical formula about a program, and the verifier proves the program meets it | props are types |
| TC2 | The verifier's knowledge at a program point is the interface (what `assert` can see) | Γ ⊢ T |
| TC3 | Green with an assumption is not done | the same |
| TC4 | Proved is not computed: SMT reasoning vs evaluation, fuel and unfolding | definitional equality |
| TC5 | Recursion ⇔ induction; a loop invariant is an induction hypothesis | recursion ⇔ induction |
| TC6 | Termination makes lemma recursion sound; partial correctness of non-terminating code | totality ⇒ consistency |
| TC7 | Ghost vs compiled: what is erased, and what runs | types indexed by values (re-themed) |
| TC8 | Everything becomes a VC for the solver | everything elaborates to a kernel term |
| TC9 | No small kernel: the TCB is verifier + solver + compiler + trusted specs, and agents are untrusted inputs to it | small kernel, untrusted front end |
| TC10 | Quantifiers need triggers; SMT is incomplete; "could not be proved" is not "false" | (new) |
| TC11 | Several doors (IDE, CLI, project build, wrapper/JSON), one verifier | four doors, one Environment |
| TC12 | Frames / ownership decide what can change | instance resolution is search (replaced) |
| TC13 | Statements are the human job | the same (keep verbatim) |
| TC14 | Brittleness: a proof is only as good as its stability | (new) |

### 11.3 Module remapping sketch

#### 11.3.1 Content track (16 modules)

| # | Dafny module | Verus module | agent role |
|---|---|---|---|
| 1 | Hello: toolchain, `dafny verify/run`, the hole contract, a first verified method + lemma; the three verdict kinds; the hook-deny demo | Hello: release + rustup + `verus`, `verus!{}`, a first verified fn + `proof fn`, the two-run hole contract | repairer |
| 2 | Datatypes, match, recursive functions; seeds the expression AST | enums, match, spec fns; seeds the AST | implementer vs tests |
| 3 | Classes/modules, API design with pre/postconditions | structs/impls/modules, API specs | API-scale implementer + adversarial review |
| 4 | Specifications & logic; first `dafny audit`; **semantic hallucination named** | specs & logic; first `--no-cheating`; semantic hallucination | audited prover |
| 5 | Proof statements and feedback; the fast channel (`vcheck` per symbol) vs the full gate; latency log | the same with `--verify-function` | prover restricted to the fast channel + one final gate |
| 6 | Induction & loop invariants; assume-driven decomposition; refute → repair → prove; **flagship paper problem** | the same | decomposer from the top statement |
| 7 | Standard libraries; the search ladder; Z3/Dafny version-mismatch lab in a scratch dir | vstd + broadcast groups; rustc/Verus mismatch lab | retriever race |
| 8 | Traits, refinement, opaque/reveal; debugging a refinement or opacity failure | traits with specs; debugging a trigger/broadcast failure | infra debugger |
| 9 | Heap, frames, `modifies`, `:-`; the AST evaluator with errors | ownership, `&mut`, `Result`; the AST evaluator with errors | refactorer under harness |
| 10 | Ghost vs compiled, subset types, termination; the invariant-enforcement spectrum | modes, ghost/tracked, erasure, termination | **flagship spec-to-proof contractor** |
| 11 | **Program logic: wp by hand; a verified VC generator or evaluator with a certificate checker**; the termination/SMT-incompleteness "triangle" | the same + ownership permissions primer | metatheory contractor (plausible-but-wrong statement audit) |
| 12 | Driving the verifier: CLI, `dfyconfig`, JSON/logs, LSP by hand against `dafny server`, a 20-line agent loop | CLI, cargo-verus, JSON, a 20-line agent loop over `--output-json` | toolwright (a hole/audit counter) |
| 13 | Pipeline & TCB: Boogie, VCs, Z3; stage-attribution drill | HIR→VIR→AIR→SMT, erasure pass; stage drill | pipeline forensic |
| 14 | **SMT mechanics**: triggers, matching loops, fuel, brittleness measurement; write a trigger-safe lemma library | the same with `broadcast` groups and `#[trigger]` | toolsmith (a lemma library closing a 12-assertion battery; the learner audits stability) |
| 15 | The verifier loop: the thesis with the "don't know" caveat; the escalation ladder; Dafny fake-green forensics; grade-the-grader; tutor red-team | the same, Verus catalog | red-teamed contractor |
| 16 | Capstone: a verified compiler from the expression language to a stack machine; verified optimizer; adversarial round; ship a CLI (compiled to a mainstream target) | the same, shipping a Rust binary | co-developer |

#### 11.3.2 Depth track

- **Tiers, partition, coverage, viva cadence: unchanged.**
- **Spine.** A bit-list numeral with an abstraction function (`ToNat`/`to_nat`), exec operations over it, and their correctness lemmas, chosen to surface early surprises: LSB-first ordering; Verus overflow obligations on the exec side [verify each surprise with probes before using it].
- **Library entry.** At the moderate tier (Dafny: `--standard-libraries`; Verus: `broadcast use` of vstd groups).
- **Challenge topics** (recommended; OD10):
  - *Algorithms & data structures* (replaces Math: Dafny and Verus are weaker for pure mathematics);
  - *Quant/production service* (an excellent fit for both);
  - *Numerics*: bit-precise integer and fixed-point work fits SMT well, while floating point is weak [verify];
  - *PL*: a verified interpreter, compiler or type checker;
  - *Agentic*: gate & bench, a proof searcher, the statement problem;
  - **for Verus, consider a Systems topic**: concurrency with tracked permissions, or an allocator.

### 11.4 Fake-green catalogs (with detection instruments)

**Dafny** (from the Dafny research; the "default visibility" column assumes the new CLI with default options):

| # | route | default visibility | instrument | X-class |
|---|---|---|---|---|
| G1 | `assume {:axiom} …` / `lemma {:axiom}` | silent [D:src] | `dafny audit` | X01/X03 |
| G2 | bodyless lemma/method with `ensures` | warning, exit 2 [D:lit] | warning count; audit | X01/X02 |
| G3 | the same inside an `abstract module` or as a trait member | **silent** [D:src] | lint: learner modules concrete; refinement result concrete | X02 |
| G4 | bodyless `function` without `ensures`, used as an oracle in specs | **silent** (uninterpreted) [D:lit] | lint: every function has a body; `dafny build`/`test` refuses bodyless compiled functions | X03 |
| G5 | `{:verify false}`, `{:only}`, `@VerifyOnly` | warning [D:src] | warning; audit | X10 |
| G6 | `--allow-warnings` / `--allow-axioms` / `--allow-external-contracts` on the CLI or in a project file | `--allow-warnings` makes G2/G5 warnings non-fatal (exit 0); `--allow-axioms` suppresses G2's bodyless-`ensures` warning outright [D:src] (its effect on the `assume` warning: verify, D1); `--allow-external-contracts` suppresses the `{:extern}` warnings [D:src] | option allowlist in `vcheck --gate`; project files are 2g-protected | X10/X15 |
| G7 | `--no-verify` | nothing verified [D:doc] | option allowlist | X10 |
| G8 | `--filter-symbol` / `--filter-position` | exit 0 having verified a subset [verify] | gate refuses filters; pin the expected verified count where stable | X05/X10 |
| G9 | `include` of a non-root file (not verified by default; **audit skips it**) | silent [D:src, D:doc] | ban `include` in learner files; every file a project root | X02 |
| G10 | `--library` / `.doo` inputs (skipped in verification) | silent [D:doc] | option allowlist | X10 |
| G11 | `expect P;` in compiled non-test code (P assumed) | silent [D:doc] | lint: `expect` only inside `{:test}` | X04 |
| G12 | vacuous `requires` / contradictory preconditions | silent | satisfiability witness (a `{:test}` call with concrete arguments, or a proved `exists`); `--analyze-proofs`/`--warn-contradictory-assumptions` (experimental) [D:src]; "swap the conclusion for `false`" | X07 |
| G13 | weakened `ensures` / changed statement | silent | refinement against a frozen abstract module; spec hash | X06/X08 |
| G14 | `--boogie`/`--solver-option` making Z3 unsound (e.g. an arithmetic-solver option in an open soundness issue) | silent [D:doc] | option allowlist | X10 |
| G15 | `--solver-path` to a fake solver | silent [verify] | pinned solver binary hash; wrapper never trusts PATH | X15 |
| G16 | `--plugin` assemblies; IDE `dafnyServerArguments` | silent [D:doc] | option allowlist; `.vscode/settings.json` 2g-protected | X15 |
| G17 | Boogie pass-through attributes (e.g. ones that turn earlier assertions into assumptions) | detection [verify] | **attribute allowlist** lint | X10 |
| G18 | misspelled attributes are silently ignored (e.g. a test that never runs) [D:doc] | silent | count expected `PASSED` lines; prefer the checked `@`-attribute forms [D:doc] | X05 |
| G19 | legacy CLI unsound options; legacy `allowAxioms` defaults to true [D:src] | silent | ban the legacy CLI | X10 |
| G20 | timeouts | **red**, exit 4 [D:lit] — but `--verification-time-limit 0` removes the limit | resource-limit pin; harness treats timeouts as failure | X16 |
| G21 | project-file poisoning (a stray or edited `dfyconfig.toml`, a `base` chain) | silent [D:doc] | 2g; CI fails on unknown project files; explicit project path | X15 |
| G22 | toolchain swap (IDE `dafny.version: custom` + `cliPath`; a PATH z3) | silent [D:doc] | pinned binary sha; never trust PATH | X15 |
| — | `decreases *` (partial correctness) | silent; audit reports it [D:src] | audit | X12/X13 |
| — | `{:extern}` with a lying spec | warning unless `{:axiom}` [D:src] | audit; differential tests | X11 |
| — | semantic hallucination (true, verified, useless) | silent | read the statement; tests on inputs the delivery avoided; property sampler | — |

**Verus** (green = `verification results:: N verified, 0 errors` / exit 0):

| # | vector | `--no-cheating`? | instrument | X-class |
|---|---|---|---|---|
| V1 | `admit()` | red [V:src] | no-cheating run | X01/X02 |
| V2 | `assume(P)` | red [V:src] | no-cheating run | X01/X02 |
| V3 | `#[verifier::external_body]` (proof or exec) | red outside vstd [V:src] | no-cheating run | X03/X11 |
| V4 | `axiom fn` | red by inference [verify P2] | no-cheating + grep | X03 |
| V5 | `assume_specification` / `external_fn_specification` | red [V:src] | no-cheating | X11 |
| V6 | `external_type_specification` / `external_trait_specification` | **possibly green** [verify P3] | lint | X11 |
| V7 | `#[verifier::assume_termination]` | red [V:src] | no-cheating | X13 |
| V8 | `#[verifier::exec_allows_no_decreases_clause]` (a diverging body proves any `ensures`) | **green** [V:src; verify P4] | lint: forbidden in learner and agent files | X12/X13 |
| V9 | code outside `verus!{}` | **green**, possibly `0 verified` [V:doc] | lint; minimum verified count per item from JSON | X05 |
| V10 | `#[verifier::external]` on an item | **green** [V:doc] | lint | X10 |
| V11 | `#[cfg(verus_only)]` divergence: verified code ≠ compiled code | **green** [V:doc] | lint: `cfg(verus_only)` only on `use` items and `cfg_attr` | X11 |
| V12 | vacuous / contradictory `requires` | n/a | shipped witness caller that must verify; swap-to-`false` probe | X07 |
| V13 | weakened `ensures` / changed spec (the most-used cheat after `assume` [V:doc]) | n/a | spec-freeze hash | X06/X08 |
| V14 | spec partiality (out-of-range index, division by zero → arbitrary value; `recommends` unchecked) | n/a | `spec(checked)` in course specs; review | X08 |
| V15 | `vstd::pervasive::assume(b)`: a vstd `proof fn` whose body is `admit()`, exempt from no-cheating | **probably green** [verify P1] | grep `pervasive::assume` | X02 |
| V16 | `--no-lifetime` / `--no-erasure-check` (skip the ghost-ownership pass) | n/a (CLI) [V:src] | gate pins the exact command; hook blocks the flags | X10 |
| V17 | `-V allow-inline-air` ("POTENTIALLY UNSOUND") | n/a [V:src] | same | X10 |
| V18 | `--no-verify` (no summary line printed, exit 0) | n/a [V:src] | JSON must show `success: true` | X05/X10 |
| V19 | partial runs (`--verify-*`; the summary says "partial verification") | n/a [V:src] | gate requires `is-verifying-entire-crate: true` | X05 |
| V20 | `cargo build` / `cargo test` / `cargo verus focus` (no verification of the crate or its deps) | n/a [V:doc] | the gate is `verus`/`cargo verus verify` only | X05 |
| V21 | `global layout` axioms (checked only at codegen) | n/a [V:doc] | `--compile` in CI for crates that use them | X03 |
| V22 | rlimit inflation (`rlimit(infinity)`; huge `--rlimit`) | n/a [V:doc] | grep + cap; time budget | X16 |
| V23 | IDE binary mismatch (verus-analyzer auto-downloads latest) | n/a [V:doc] | pinned `verusBinary` | X15 |
| V24 | `VERUS_EXTRA_ARGS` / `VERUS_Z3_PATH` / `RUSTFLAGS --cfg verus_only` | n/a [V:src; verify P10] | hook inspects env assignments; wrapper scrubs env | X15 |
| — | semantic hallucination | n/a | statement review; differential and property tests | — |

**Instruments to teach** (the forensic module asks for **N catches with N different instruments**):
1. the audit (`dafny audit` / `--no-cheating`);
2. the lint;
3. the spec-freeze diff;
4. the satisfiability witness;
5. **swap the conclusion for `false`**: if it still verifies, the context is vacuous;
6. running compiled code on inputs the delivery's own tests avoided;
7. a property sampler;
8. reading the statement;
9. JSON completeness checks (entire crate, verified count);
10. re-verifying with another seed or solver version.

### 11.5 What does NOT transfer, and the recommended redesign

1. **No small kernel → the trust story changes.**
   - Lean's "untrusted front end (agents included) / small trusted kernel + 3 axioms / independent re-checkers" becomes **"TCB inventory + audit + honesty"**.
   - Teach the TCB as an explicit inventory (§11.1 row 24). Make `TRUST.md` mandatory from the hard tier on.
   - Replace the "independent re-checker" gate item with **solver diversity plus fresh-process, seed-varied re-verification** (Dafny ships two Z3 versions [D:src]; Verus has experimental cvc5 [V:src]). **Say honestly that this is not independent checking.**
   - "Disputes go to the kernel" becomes **"disputes go to the pinned verifier, under the asymmetry rule"** (§6.5).
2. **Timeouts and brittleness are first-class.**
   - Pin **resource limits, not wall-clock limits**, in every gate and probe.
   - Treat timeout and rlimit outcomes as failures everywhere; Lean has no equivalent hazard of a sloppy harness reading "no error lines" as success.
   - Add the brittleness check to code review and to the challenge gate (Dafny `measure-complexity --mutations N --random-seed S` + `dafny-reportgenerator --max-resource-cv-pct` [D:src, D:doc]; Verus seed variation via `--smt-option smt.random_seed=N` [V:src] and `--time` rlimit counts).
   - Make S11 (SMT mechanics) carry triggers, fuel, opacity and stability.
   - Budget for **goldens moving with solver versions**.
3. **No in-file message pinning.** Use the golden harness + specimens + slot files (§3.8.6). This is the largest engineering item of the port: budget it in Phase 0 and verify its normalization on the pinned toolchain before any chapter is written.
4. **No goal state.** Predict "goal" → predict "which obligation fails". Tutor rung 3 → "what does the verifier know here?". Worked examples state knowledge with intermediate `assert`s. The fast-channel lesson becomes per-symbol and per-assertion verification latency.
5. **No tactic language or metaprogramming strand.** WRITE/RECOGNISE runs over constructs and knobs. S11 is replaced by SMT mechanics. Module 14's "write your own tactic" becomes "write a trigger-safe, broadcast-ready lemma library" or "a verified decision procedure by computation" (`function by method` in Dafny; `by (compute)` in Verus).
6. **Type theory has no direct analogue.** S8 becomes program-logic foundations, and the "theory with receipts" principle still applies: a verified VC generator or verified evaluator, with soundness stated as a theorem and a checker that returns a certificate.
7. **Holes behave differently.** Dafny holes fail the default build, so the learner loop needs `--allow-warnings`, and the "green with N warnings" shipped state becomes "green under the learner loop, with N hole warnings". A Dafny hole also blocks `run`/`test` of its **whole compile unit**, so tests compile per module against given code only, and exercise files never import earlier exercise files (§3.3). Verus holes are silent and compile (an `external_body` stub panics only when reached), so done is a two-run gate, and Lean's import mirroring survives.
8. **No transitive per-theorem audit.** Audit the whole program; build `vaudit`; prefer whole-file gates over per-statement dashboards; teach the instrument "remove the assumption and re-verify".
9. **SMT automation can close exercises unaided.** Add the empty-body gate (CI) and design items around `{:induction false}`, `opaque`, disabled nonlinear arithmetic and low fuel where needed.
10. **No official agent tooling.** Build and pin `vcheck` (and optionally expose it as an MCP server). Cover it in the hook matcher. Have it refuse unsound and partial flags in gate mode. Return JSON with exit code, per-symbol status, hole count, audit findings and verified count.
11. **Toolchain churn** (Verus weekly; Dafny message rewording on master). Pin a release, bump at most twice a year with batched golden regeneration, and keep VERSIONS rows for message wordings.
12. **Statement freezing.** Lean's Expr identity becomes Dafny refinement against frozen abstract modules (with the "learner modules must be concrete" lint) or Verus parser-based spec hashes.
13. **Build-tool trust.** `dfyconfig.toml`, `Cargo.toml`, `build.rs`, env vars and IDE settings can all change what is verified. All of them go on the 2g list, and CI rejects unknown copies.

### 11.6 Probes to run before anything ships (record results in `VERSIONS.md`)

| id | probe | why |
|---|---|---|
| D1 | the exact hole-warning texts and exit codes for bodyless lemma, bodyless function with `ensures`, and `assume false` under `verify`, `verify --allow-warnings`, `test` | hole convention and counter |
| D2 | `dafny audit` output for each hole kind, with and without `include`; `--compare-report` exit codes | audit design |
| D3 | whether verification runs after a resolution error | planted-error design |
| D4 | `--filter-symbol`/`--filter-position` summary and exit code | gate refusal rules; exit-file scoring |
| D5 | `dafny test` exit code on a failing test; output format | value slots; CI |
| D6 | `--json-output` schema | harness |
| D7 | whether a refining module may add `requires`; behaviour of `...` signature copying | statement freeze |
| D8 | IDE behaviour on non-`.dfy` extensions; workspace symbols across projects | specimen design; LSP exposure |
| D9 | empty-body results on each planned hole | empty-body gate |
| D10 | whether `solver-path` is honoured from `dfyconfig.toml` | pinning |
| D11 | `dafny test` / `dafny run` on a unit holding one bodyless lemma, one bodyless method and one `assume false;`, with and without `--allow-warnings`: which are errors, which warnings, and does anything run | compile-unit rule (§3.3); value slots |
| D12 | the warning count for a bodyless lemma with two `ensures` clauses (expected: two) | one-`ensures`-per-hole rule (§3.3) |
| P1 | `vstd::pervasive::assume(false)` under `--no-cheating` | V15 lint |
| P2 | `axiom fn` under `--no-cheating` | V4 |
| P3 | `external_type_specification` / `external_trait_specification` under `--no-cheating` | V6 |
| P4 | `exec_allows_no_decreases_clause` + `ensures false` + `loop {}` | V8 |
| P5 | the unit of `verified` in the summary | goldens |
| P6 | `#[test]` outside `verus!` under `cargo test` in a `cargo verus new` project; `--compile --test` | value slots |
| P7 | `proof_note` on `admit()`; `func-details` key spelling and coverage | labelled holes; `obligation` format |
| P8 | Verus diagnostics under `--error-format=json` | harness |
| P9 | contents of an exported `.vir` | side-channel classification |
| P10 | `VERUS_EXTRA_ARGS` honoured by release builds | guard |
| P11 | determinism: 5 runs of the same failing file (spans, messages, counts, rlimit) | goldens and brittleness |
| P12 | the playground's Verus version | (only if the playground is mentioned) |
| P13 | whether workspace `default-members` narrows a bare `cargo verus verify`; that an `exclude`d reference crate is never reached | default-target design (§10.2) |

---

## 12. Acceptance checklist and open decisions

### 12.1 Acceptance checklist for the new course

Tick every line before calling the course (or a phase) shipped. Each line names the artifact that proves it.

**Infrastructure (Phase 0)**
- [ ] The toolchain is pinned (Dafny version + solver, or the Verus release + Rust + Z3 + `vstd`), with `VERSIONS.md` rows dated. CI asserts the versions and the binary sha256.
- [ ] A clean clone builds the default target green in minutes. `make -C paper paper` compiles the skeletons and fails on an empty set.
- [ ] The default target is learner exercises only. The reference is built by name only. The checker enforces the default-target list.
- [ ] `MODULES.toml` + `check_course_map.py` (all five groups) + regression tests run first in CI. The registry names no reference path.
- [ ] Every skill's Step 0 resolves through the registry.
- [ ] `vcheck` (pinned wrapper and fast channel), `vaudit`, `specfreeze`, `pins.py` and `firsttry.sh` exist. Each prints locations, not content, wherever content could answer an item.
- [ ] The guard has four layers: the 4 canonical deny rules; `spoiler-guard.sh` with rules 1/1b/1c/1d/2/2s/2f/2g covering file tools, shell and every verifier MCP/wrapper tool; CORE.md MAY/MAY-NOT; leak patterns with the README verifier.
- [ ] `test_hooks.sh` replays must-block and must-allow fixtures with rule attribution, including **every port side channel in §7.2**. It runs in study, jq-free, stand-down and still-armed passes in the CI job `hook-test`.
- [ ] `course_mode.sh` refuses authoring outside a linked, non-learner worktree, and moves both layers together. CI fails on a shipped mode file or a missing canonical rule.
- [ ] **A fresh study session is demonstrably denied** a reference read, a reference build, an include/import of the reference through the wrapper or an MCP tool, and a heredoc into a solo tree. The refusal texts are captured for the module 1 chapter.
- [ ] The SessionStart banner reports due reviews, a stale allowlist and authoring mode.

**Per module**
- [ ] The twin is complete, tool-counted hole-free, audit-clean and silent, with every quoted output pinned (golden harness) and every learner statement's audit row pinned.
- [ ] The exercise file is the exact hollow of the twin. Its declaration list equals the twin's. Its hole count equals the chapter's and CI's number. Every slot is unfilled. `--lint-hollow` and **`--empty-body`** pass. (Dafny: every hole declaration carries exactly one `ensures`, and the module's test unit compiles against given code only.)
- [ ] Item markers parse. Every P/H/X/T item is cited in the concept matrix (depth track). Each WRITE construct has ≥2 `uses:`. Coverage rows resolve.
- [ ] Specimens, planted, exit and demo files are outside every root, and their shipped state is pinned (exit, counts, normalized output hash).
- [ ] The chapter follows the skeleton (§2.4.3), quotes only captured output, shows predict answers only after the box, and has 3–5 rendered diagrams and the planted/harvested table.
- [ ] The agentic file has the three-key CONTRACT block on line 1, one of the four shapes, a "what the dashboard can and cannot see" passage, and a twin reference section proving it satisfiable.
- [ ] The written pair, if any, compiles. A rubric exists either way, with sha pins filled (no `PENDING` at ship), verifier anchors, code-review focus and an audit debrief.
- [ ] The bank meets size, mix, viva-able count, backward edges, verified probes, precomputed disjoint draws and parallel problems (names disjoint from the avoid list and twins).
- [ ] Leak patterns: 3–8 entries, Rule 1 and Rule 2 verified, cut only from H/X/T/A answers.
- [ ] Calibration fixtures (flawed with per-line EXPECTED plus a clean problem; gold paraphrased) pass a headless grader run.
- [ ] A study-clone simulation of every skill gives **zero leak-pattern hits**, with legal help still delivered.
- [ ] Minutes reconcile to the module total. Practice items are admissible (reference inside the band) or carry no minutes.
- [ ] (Two tracks) `avoid.sh` is clean and has no stale waivers.

**Course level**
- [ ] The role ladder runs end to end. Each agentic exercise has artifact-based acceptance and one recorded known-good transcript.
- [ ] Contract v0/v1/v2 slots exist in CLAUDE.md below the learner marker, with the fallback rules above it.
- [ ] Continuity pass: every whisper or threshold-concept step pays off.
- [ ] Clean-clone dry run: every chapter command runs verbatim.
- [ ] Brittleness: the reference re-verifies under N seeds within the pinned resource limit (the CV gate).
- [ ] CI never calls a model, never runs on the learner branch, and never prints reference content.

### 12.2 Open decisions (each with a recommended default)

| # | decision | recommended default | why |
|---|---|---|---|
| OD1 | **Dafny or Verus** | One language per course and repo. Choose **Dafny** for a broad developer audience and mainstream compile targets. Choose **Verus** for Rust/systems learners; expect more toolchain churn. | the guard, harness and pins are language-specific; mixing doubles them |
| OD2 | **Which track(s)** | Build the **16-module content-ordered track first**, using the depth track's item grammar, predict slots, exit files and spine re-supply. Add the depth track only on request, and then apply the disjointness gate. | the content track is proven and cheaper (~16 MU vs ~44 MU); the depth-track mechanics are the mature ones |
| OD3 | **Hole convention** | Dafny: bodyless `lemma`/`method`/`function` with **exactly one** `ensures` (the warning is per clause) plus `assume false;` inside bodies; tests compile per module against given code only; learner loop `--allow-warnings`; done = no flag + `vaudit` 0. Verus: `#[verifier::proof_note("<item>")] assume(false);` and `external_body` + `unimplemented!()`; done = JSON success on the entire crate + `--no-cheating` 0 + lint 0. | each is the only convention whose holes the tool counts (§11.1 rows 1–2) |
| OD4 | **Golden-harness design** | Specimen files with an IDE-ignored extension; in-file `// EXPECT` headers for diagnostics; normalized `.expect` sidecars for whole-file goldens; `pins.py` runs them all; a slot file per module for verdict answers. | reproduces the `#guard_msgs` guarantees without letting the IDE leak answers |
| OD5 | **Toolchain pin form** | Dafny: the **release zip** with sha256 (Z3 bundled, deterministic solver path) over the dotnet tool manifest. Verus: a weekly release tag (not rolling), with `rust-toolchain.toml` and `vstd = "=…"` from the toolchain manifest. ≤2 bumps a year. | PATH-solver fallback and IDE auto-download are both fake-green vectors |
| OD6 | **Determinism settings** | Resource limits (not time limits) in every gate and probe; one fixed seed for goldens; a 3-seed brittleness check from the design-judgment bar on. | reproducible verdicts and quotes |
| OD7 | **Agent fast channel** | A pinned CLI wrapper `vcheck` (JSON output), optionally exposed as a project MCP server; hook-covered. No third-party MCP. | none of the community servers audit or pin |
| OD8 | **Library staging** | No `--standard-libraries` (Dafny) / no vstd lemma groups beyond the prelude (Verus) in modules 1–6; library from module 7 (depth track: moderate tier). | hand-first rule; import hygiene |
| OD9 | **Running artifact and spine** | Content track: an expression language → stack-machine compiler (capstone). Depth track: a bit-list numeral with `ToNat` and exec operations. | spec/implementation tension; the capstone fits both languages |
| OD10 | **Challenge topics** | Algorithms & data structures; Production service (quant-style); Integer and fixed-point numerics; PL; Agentic. Add Systems (concurrency/permissions) for Verus. | play to SMT verifiers' strengths |
| OD11 | **Written-track scope** | Content track: paper wherever it pays; the source ships 13 of 16 (it skips modules 1, 3 and 7 as filler). Depth track: a few short items + hard-tier blueprints + challenge blueprints. | paper only where it pays; blueprint grading is the core value |
| OD12 | **Bank visibility** | Treat banks as learner-visible. Author target insights as anchor bullets that are fine to read, and keep viva difficulty in the predict probes and the follow-ups. | the source leaves this ambiguous; pick one policy |
| OD13 | **Contractor ban on `instructor/` writes** | Make it hard: the hook denies `instructor/` writes while the allowlist is non-empty. | the source relies on instruction alone |
| OD14 | **Held-out material** | Only if the agentic challenge tier ships: `Hidden/` always encrypted, unsealed only in a grader container. | the learner may open `Solutions/`, so held-out data cannot live there |
| OD15 | **Model access for agentic work** | No usage-billed APIs: a subscription CLI in headless mode with every tool disabled, plus local models; checkpoint-and-resume under rate limits; CI never calls a model. | the source owner's binding decision; it also bounds cost |
| OD16 | **Learner branch convention** | Learner work happens on `<learner-prefix>-*` branches; course changes flow main → learner branch only; CI does not run on learner branches. | the authoring-mode refusal and CI scope depend on it |
| OD17 | **Session-check rule** | The uniform rule of §6.1. | the source's per-skill lists drifted |
| OD18 | **Review-bar names** | `it-reads → proof-shape → library-conventions → design-lite → design-judgment → library-pr`, plus `production`/`harness`, with a **brittleness** dimension from design-judgment up. | adapts the source's Mathlib-specific bar names |

### 12.3 Known drift in the source (do not copy)

- Registry schema documents fell behind the checker. **The checker is authoritative.** Keep design documents in sync, or have them point at the checker.
- Some per-skill session-refusal lists are asymmetric. Use the uniform rule.
- `/discuss` writes ledger lines as `source: tutor`. Add a `discuss` source.
- The answer classification vocabulary sits in one skill but is cited as shared. Put it in CORE.
- One rubric counted holes with grep, contradicting the code-review gate. Rubrics must never contradict the tool-counted rule.
- The legacy content-track CONTRACT prose form coexists with the canonical block. Use only the canonical block.
- The gradebook template header lagged the tracks in CORE. Generate templates from CORE.

---

*End of spec. Provenance: lean-learn-0 `README.md`, `PLAN.md`, `QPLAN.md` (v3.1), `CLAUDE.md`, `MODULES.toml`, `.claude/skills/**`, `.claude/hooks/**`, `scripts/**` headers, `.github/workflows/ci.yml`, `VERSIONS.md`, learner-visible chapters and exercise files. Dafny facts are from the Dafny research notes (Dafny `v4.11.0` source, lit goldens and reference manual). Verus facts are from the Verus research notes (Verus `f319e4d` source and guide, plus live GitHub and crates.io data). No answer material was read.*

---

## Review notes (critic pass, 2026-10-02)

Checked against `README.md`, `PLAN.md`, `QPLAN.md`, `CLAUDE.md`, `.claude/settings.json`, the skills, the hook header, `ci.yml`, the `MODULES.toml` header, the script headers and the reader/research notes. Risky toolchain claims were re-read in the Verus source snapshot, the Dafny `v4.11.0` source and docs, and live GitHub, crates.io and arXiv. No answer material was opened. No leaked answer material was found; every code sample remains invented.

**Changed (blockers and majors):**
1. **Dafny hole counting** (§3.3, §11.1 row 1, OD3, §12.1). The bodyless-`ensures` warning fires once per `ensures` clause [D:src], so the spec now requires exactly one `ensures` per hole. It also notes that `--allow-axioms` suppresses the warning, and that function holes warn through the shared base class.
2. **Dafny holes block compilation of the whole unit** (§3.1 rule 3, §3.3, §3.5, §3.8.6, §11.5 item 7, new probes D11–D12). Tests and exec-value slots now compile per module against given code only, and Dafny exercise files import only given layers.
3. **Verus reference crate moved out of the learner workspace** (§10.2, §7.2 side channels, §11.1 rows 15–16, P13). The guide says a bare `cargo verus verify` verifies every `verify = true` crate. The directory is renamed `Solutions/` so the guard's bare-word rule still applies.
4. **Verus `proof_note`.** The label reaches `failed_proof_notes` only in the `--no-cheating --output-json` run (source and test confirmed).
5. **Misdescriptions fixed:** coverage rows (`r` field, keyed by content module, with an example); the concept-matrix example (it used strands outside its module); "every module ends with an agentic run"; "every module has a paper pair or rubric"; the CI trigger scope; the written-track count (13 of 16); the planned-but-unbuilt `admissible`/`statements[]` fields; G6 semantics; and a wrong row cross-reference.
6. **Formats added:** the settings.json hooks block; P/obligation/verdict/X item blocks with slot-file and pins-file layout; `Answer form:`; the calib TSV `kind`/`verdict` enums; a rubric skeleton and label grammar; gradebook rows; a `CLAUDE.md` skeleton.
7. **Omissions added:** the three-channel leakage threat model (§7.1); the depth-track chapter `## 0` section; the QA0–QA7 phase variant; `.mcp.json` on the 2g list; the source's `q_` script names; the contract skill's multi-file question; the rung-5 cap note; and "new payload" being relative to the actual learner.
8. **Sourcing:** added [D:live] and [ext] tags. The logic-issue count was re-verified live (3). VeruSAGE was re-attributed to arXiv 2512.18436v2. Citations to scratch reports were replaced with repo paths. The Verus [V:src] commit was noted as newer than the recommended pin.

**Still [verify] before anything ships:** probes D1–D12 and P1–P13 (§11.6), especially D11 (what a hole does to `dafny test`), D12 (warnings per clause), P13 (`default-members`), P6 (`cargo test` beside `verus!`) and P1/P3/P4 (`--no-cheating` gaps). Also: the IDE-ignored specimen extension; Dafny `--json-output` schema; cross-file module import inside one `dfyconfig.toml` project; `proof_note` on `admit()`; the VeruSAGE 14% figure (read it in the paper itself); the community Dafny MCP server description; and `VERUS_EXTRA_ARGS` in release builds.
