# Shared concept vocabulary (both tracks)

Ledger tags are `<module id>/<tag>`; `<tag>` must be a canonical tag or an alias below.
`/review` resolves aliases and compares canonical tags across the tracks, so `Q04/loop-invariant`
and `R06/loop-invariant` are one concept to it. Never rename a tag once a ledger uses it.

- **Banks.** A bank's `## Controlled tag vocabulary` lists the tags its module logs; each one is a
  tag or an alias in this table. A module that teaches a concept another module already tagged
  reuses that tag, in either track. A concept that no row fits gets a new row here first, before
  any bank or ledger line uses it.
- **One tag per concept, not per language.** Dafny and Verus forms of one idea share a tag
  (`loop-invariant` covers both `invariant` clauses); a construct that exists in one language
  only keeps a tag of its own (`auto-induction`, `tracked-ghost`). Construct slugs in the
  registry (`write_d`, `uses:`) are a separate namespace: a tag names the concept a learner gets
  wrong, a slug the construct an item exercises.
- **Aliases** are spelling variants of one tag, nothing more (`loop-invariants` →
  `loop-invariant`). Concepts that are merely close stay separate tags (see *Near neighbours*).
- **Spelling.** Tags and aliases are kebab-case.
- **Declared by** names the modules whose banks are expected to declare the tag. This is the
  seed vocabulary of design phase DV1a, written before any bank exists, so the column is the
  plan (design §7.4, §8.2); each bank's author confirms or extends it. Rows are grouped by the
  strand that owns the concept (design §7.2).
- **Checked by** `python3 scripts/check_course_map.py --only vocab`: tags and aliases are unique
  and disjoint, every bank vocabulary is inside this table, and every ledger tag is known (and
  in its module's bank vocabulary when that bank exists).

| tag | aliases | covers | declared by |
|---|---|---|---|
| `datatypes-and-match` | | datatypes and Rust enums; `match` exhaustiveness; constructors as data | Q01, Q02, R02 |
| `nat-vs-machine-int` | `nat-vs-machine-integers` | unbounded `nat`/`int` vs `u64`: subtraction, wraparound, where the overflow obligation comes from | Q01, Q02, Q10, R01, R09 |
| `exec-overflow` | | overflow obligations in executable code; checked and wrapping operations; widening to `u128` | Q02, Q04, Q10, R09 |
| `spec-vs-exec` | | spec functions vs executable code (`function`/`method`, `spec fn`/`fn`); what may call what | Q01, Q03, R02, R03 |
| `sequences-and-views` | | `seq`/`Seq`, slices, a `Vec` and its view; indexing obligations | Q02, Q07, R02, R07 |
| `running-verified-code` | | `dafny run`/`test --target py`, `verus --compile`, `cargo test` beside `verus!`; what a passing test shows | Q01, Q04, R01, R02 |
| `limb-arithmetic` | | little-endian limbs, carries and borrows, non-canonical zeros, the `ToNat` abstraction | Q01, Q04, Q07, Q10 |
| `requires-ensures` | `requires-and-ensures` | preconditions and postconditions as the contract; who must prove which | Q01, Q02, R01, R04 |
| `quantifiers` | | `forall`/`exists` in specs; bounded vs unbounded quantification | Q02, Q04, R04, R14 |
| `vacuity` | `vacuous-spec` | contradictory `requires`; vacuous truth; a green proof of nothing | Q03, Q07, Q18, R04 |
| `witnesses` | | a satisfying input that shows a spec or subset type is non-vacuous | Q03, Q18, R04, R10 |
| `spec-strength` | | weak, faithful, over-strong and vacuous specs; verified is not correct | Q04, Q13, Q15, R04, R10, R15 |
| `spec-wellformedness` | | a specification expression that is itself checked: an index or a division in an `ensures`; Dafny's well-formedness against Verus's total spec operations | Q10, R04 |
| `anchoring` | | anchored vs unanchored match specs; empty-string and boundary traps | R04, R15 |
| `assert-by` | | `assert … by { }` / `assert(…) by { }`: scoping a proof step to one fact | Q02, Q04, R01, R04 |
| `calc-chains` | | `calc` steps and the relation they compose, written step by step | Q04, Q07, R06 |
| `lemma-call` | | calling a lemma to put its conclusion in context; lemmas as reusable proof | Q01, Q04, R02, R06 |
| `verdict-reading` | | reading a verdict: which obligation failed, where, and what the message licenses | Q01, Q02, Q07, R01, R05 |
| `assertion-repair` | | a proof blocked by one missing fact: localize the failure, then name the term the solver will not build | Q10, Q12, R05 |
| `no-goal-state` | | no goal display: probing what the verifier knows with asserts; bisection | Q02, Q04, R05 |
| `assume-after-failure` | | a failed assertion is assumed afterwards; one error per independent obligation | Q02, R05 |
| `false-friends` | | `calc`, `assert`, `forall`, `old`, `decreases`, `==>` behave differently in Dafny and Verus | Q01, Q04, R01 |
| `loop-invariant` | `loop-invariants` | establishment, maintenance and use at exit; the invariant one step short | Q02, Q04, Q10, R06 |
| `termination-measure` | | `decreases` clauses, lexicographic tuples, well-founded measures | Q02, Q04, Q05, R02, R06 |
| `induction-as-recursion` | | a recursive lemma is an induction; the recursive call is the IH | Q04, Q07, R06 |
| `auto-induction` | | Dafny's automatic induction; `{:induction false}` and manual lemma induction | Q02, Q03, Q04, R06 |
| `fuel` | | the unfolding depth of recursive definitions in both verifiers | Q07, R14 |
| `invariant-generalization` | | strengthening an invariant or lemma so the induction goes through | Q13, Q16, R06 |
| `refute-repair-prove` | | refute a false claim with a counterexample, repair the statement, then prove it | Q15, R06 |
| `standard-library` | | Dafny `Std` and Verus `vstd` lemma libraries: finding and calling them | Q04, Q07, R07 |
| `import-tiers` | | which library modules a file may reach; narrow imports and their cost | Q04, R07 |
| `toolchain-mismatch` | | exact Rust and Z3 version requirements; what a mismatched toolchain does | Q04, R07 |
| `broadcast-use` | | Verus `broadcast use` groups after explicit lemma calls; their cost, memory included | Q04, R07 |
| `search-then-name` | | find a library lemma by search, then replace the search with the named call | Q04, Q10, R07 |
| `nonlinear-arith` | | nonlinear arithmetic: why SMT struggles; `nonlinear_arith`, arithmetic lemmas, turning it off | Q04, Q07, R14 |
| `bit-vector` | | bit-vector reasoning (`bit_vector`, `bv64`): what that theory proves and what it costs | Q07 |
| `prover-choice` | | which prover a goal needs: default SMT, nonlinear or bit-vector | Q04, Q07, R14 |
| `frames` | `frame` | Dafny `reads`/`modifies`; dynamic frames with `Repr` and `Valid()` | Q02, Q05, Q11, R09 |
| `ownership-and-mut-ref` | | Verus ownership and `&mut`; `old(..)`/`final(..)` in specs | Q05, Q11, R09 |
| `error-propagation` | | native result propagation (`:-` / `?`), compatible failures and enclosing branch/state postconditions | Q05, R09 |
| `module-visibility` | | Dafny export sets; Verus `open`/`closed` specs and views | Q02, Q05, R03 |
| `opacity` | | `opaque`/`reveal`: hiding a definition from the solver and revealing it locally | Q05, Q06, Q08, R08 |
| `traits-and-interfaces` | | Dafny traits and abstract modules; Verus traits with specs | Q08, Q14, R08 |
| `refinement` | | `refines`: what a refinement may add (`ensures`) and may not (`requires`) | Q08, Q14, R08 |
| `ghost-and-modes` | | ghost vs compiled code; Verus spec, proof and exec modes | Q01, Q03, R03, R10 |
| `subset-types` | `subset-type` | Dafny subset types with witnesses; Verus `type_invariant`; invariants carried by types | Q03, Q11, R10 |
| `erasure` | | ghost code is erased: what runs is not what was proved about | Q03, Q05, R10 |
| `tracked-ghost` | | Verus `Ghost<T>` and `Tracked<T>`; linearity of tracked state | Q08, R11 |
| `function-by-method` | | Dafny `function … by method`: a spec function with an efficient body | Q05, R10 |
| `wp-vc` | `wp-and-vc` | weakest preconditions and verification conditions, by hand | Q03, Q05, R04, R11 |
| `hoare-logic` | | Hoare triples, the loop rule, invariants as induction hypotheses | Q05, Q08, R06, R11 |
| `verified-metatheory` | | a verified wp or derivation checker: proving a prover's rules sound | Q08, Q11, Q17, R11 |
| `permissions` | `permission` | Verus `PointsTo` permissions and linear ownership of memory | Q11, Q14, Q17, R11 |
| `exit-codes-and-doors` | | the CLI, IDE and build doors; exit codes and what each one licenses | Q01, Q03, Q06, Q18, R01, R12 |
| `json-verdicts` | | the verifiers' JSON channels; parsing verdicts and obligations | Q06, Q12, R12 |
| `lsp` | `language-server-protocol` | `dafny server` and LSP framing; what a client sees and sends | Q09, Q15, R12 |
| `fast-channel` | | the pinned wrapper and per-symbol runs; fast feedback vs the full gate | Q03, Q06, R05, R12 |
| `verdict-loop` | | a client that retries on verifier feedback; a parser before a model | Q12, R12 |
| `pipeline-stages` | | parse, resolve, verify, compile; rustc, VIR, AIR, SMT; which stage fails first | Q01, Q03, Q09, R13 |
| `tcb` | `trusted-computing-base` | what must be trusted: solver, translator, specs, `assume`, `external_body`, `{:axiom}` | Q03, Q06, R07, R13 |
| `hole-contract` | | loud Dafny holes vs silent Verus holes; done = verified and zero holes, tool-counted | Q01, Q03, R01, R04 |
| `fake-green` | | a green result that proves nothing; the instruments that detect it | Q09, Q15, Q18, R13, R16 |
| `build-poisoning` | | project files, `build.rs` and Cargo `[patch]` changing what gets verified | Q09, Q18, R13, R16 |
| `trust-ledger` | | `TRUST.md`: every trusted assumption, listed and justified | Q06, Q18, R13, R16 |
| `triggers` | `trigger` | quantifier instantiation; how triggers are chosen and written | Q06, Q09, Q15, R14 |
| `matching-loop` | | a trigger that feeds itself; instantiation blow-up | Q09, R14 |
| `resource-limits` | `resource-limit` | deterministic resource limits vs time limits; verdict kinds | Q06, Q12, Q18, R05, R14 |
| `brittleness` | | seed sensitivity, solver swaps, resource-count variation; repair without weakening | Q09, Q15, Q18, R14, R16 |
| `proof-splitting` | | isolating assertions and splitting a proof to stabilise it | Q07, Q09, Q18, R14 |
| `smt-log` | | what the solver was given (each quantifier's `:pattern` and `:qid` in the SMT query) versus what it did; a pattern is not an instance | R14 |
| `contract-allowlist` | | the CONTRACT block (goal, allowed files, acceptance); rules without gates are suggestions | Q03, Q09, Q18, R01, R15, R16 |
| `agent-roles` | | the role ladder from repairer to adversary; each role's first failure mode | Q01, Q06, Q09, R01, R04, R10 |
| `escalation-ladder` | | tests, property tests, then verification: the cheapest refutation first | Q06, R02, R15 |
| `property-testing` | | proptest beside `verus!`, bounded `expect` loops in Dafny; what sampling misses | Q06, R02, R15 |
| `grade-the-grader` | | grader variance at the line, band and prose levels | Q12, R15 |
| `gate-design` | | a gate that rejects every decidable cheat and says UNKNOWN where it cannot decide | Q09, Q18, R13, R16 |
| `matched-compute` | | comparing search regimes at equal calls, not equal attempts | Q12, R12 |
| `frozen-statements` | | frozen, hash-pinned statements; statement-only review | Q18, R15, R16 |
| `agent-output-is-data` | | agent output comes back as data, is judged in a sandbox, and is never merged | Q12, R12 |
| `statistics` | | pass@k, confidence intervals, paired tests, minimum detectable effect | Q06, Q09, Q18, R05, R07 |
| `variance` | | run-to-run variance and the CV of verifier and agent results | Q06, R05 |
| `eval-reporting` | | `EVAL.md` reports with full disclosure | Q06, Q09, R07, R12 |
| `pre-registration` | `preregistration` | claim, metric, estimator, budget arithmetic and MDE fixed before a run | Q12, Q15, Q18, R12, R15, R16 |
| `spec-oracles` | | mutation kill and subset implication as spec-quality oracles | Q15, R15 |
| `prose-to-spec` | | a spec written from prose, with a witness and a reference implication | Q13, Q15, R04, R10, R15 |
| `contamination` | | benchmark contamination and its controls: authorship dates, perturbation, isolation | Q12, Q15, R15 |
| `vericoding` | | implementing and proving against one's own spec, then re-judging against the reference | Q15, R15 |
| `fidelity-audit` | | a Dafny-to-Verus port with a fidelity audit; why implication lemmas alone are circular | Q07, R09 |
| `research-framing` | | scoping a claim to a small-n replication: proposal, card, memo | Q18, R16 |
| `paper-cards` | | reading a paper on fixed fields: task, oracle, trust, cheat surface, metric, budget | Q01, Q06, R01, R12 |
| `grader-inflation` | | how far naive graders inflate success, by cheat class | Q18, R16 |

## Near neighbours (distinct tags, never aliases)

These look alike but name different concepts. Log the one that matches the error; `/review`
treats them as different tags when it interleaves.

- holes and empty proofs: `hole-contract`, `fake-green`, `vacuity`
- specs under pressure: `spec-strength`, `vacuity`, `witnesses`, `prose-to-spec`, `spec-oracles`
- induction: `induction-as-recursion`, `auto-induction`, `invariant-generalization`, `loop-invariant`
- controlling what the solver sees: `fuel`, `opacity`, `triggers`, `matching-loop`, `smt-log`
- trust: `tcb`, `trust-ledger`, `gate-design`, `fake-green`, `build-poisoning`
- stability: `brittleness`, `resource-limits`, `variance`, `proof-splitting`
- measurement: `statistics`, `variance`, `matched-compute`, `pre-registration`
- kinds of code: `spec-vs-exec`, `ghost-and-modes`, `erasure`, `tracked-ghost`
- arithmetic: `nat-vs-machine-int`, `exec-overflow`, `nonlinear-arith`, `bit-vector`, `prover-choice`
- reading results: `verdict-reading`, `no-goal-state`, `assume-after-failure`, `pipeline-stages`
- tests and proofs: `running-verified-code`, `property-testing`, `escalation-ladder`
