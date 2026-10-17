# Q07–Q09 author notes (DV3b item plan)

> **Author-only.** This file holds prediction answers, exit statements and answers, reference proofs, gate results, the card demos' intended content, the forensic deliveries' species, the red-team bank's planted lemma and the agent files' soft spots. Never quote, paraphrase or link any of it from a learner-visible file (`QPLAN.md`, the registry, exercise, check, exit and agent files, specimens, `slots/`, `expected/`, chapters, banks, rubrics, `research/` templates). The learner-visible plan is `QPLAN.md` §14–§17, with §5.2 (the Q07–Q09 checks) and §6 Q26–Q46 (the open questions); item ids here are the same.

**Revised 2026-10-06 after the plan review** (§R below: what each finding changed, the probes this revision ran, the alternatives not taken). Where §R and an older line below disagree, §R and the sections it names as rewritten hold.

Written 2026-10-06 by the DV3b plan lane. Every tool result quoted below was captured on the pins, one solver job at a time, each job started with at least 60 GB available (`free -g`), through:

- the course wrappers run from a scratch copy of the authoring worktree (`scripts/vcheck`, `--json`, `--gate`, `--brittleness`, `--module Q07` for a probe's context; `scripts/vaudit`, `--mode`), with every `dvl` job's memory cap clamped to 8 GB, the lane's share, by a small driver (`drv/capped.py`: it replaces `dvl.common.run_capped` with a wrapper that passes `min(cap, 8)`, then runs the wrapper unchanged);
- the `dvl` library's empty-body gates (`dvl.dafny.empty_body`: maxauto plus the shipped options under seeds 1–3; `dvl.verus.empty_body`: the light modes under seeds 1–3), through the same clamp (`drv/eb.py`);
- for the other bundled solver, the plain Dafny binary through `dvl.common.run_capped` (8 GB) with the course flags (`--resource-limit 5000000 --cores 2 --allow-warnings false --allow-axioms false --standard-libraries --manual-lemma-induction`) and `--solver-path` naming each bundled Z3 (`drv/res2.py`; `drv/res3.py` adds seeds as `vcheck` does, `measure-complexity --random-seed S --mutations 1`; `drv/swap_survey.py` over every Dafny twin of Q01–Q06), because `scripts/vcheck` refuses solver pass-through by design (§6 Q29 asks for the course option).

Three probe files raise the limit per declaration to measure a cost above the pin: `var_d.dfy` and `s1_d.dfy` (`{:resource_limit 30000000}`), `nl_d.dfy` (`60000000`); they are marked where quoted. Probe files are lane scratch, **not archived**: `/tmp/dvl0-plan3b4-dv3b/` (`root/` a scratch copy of the authoring worktree's tracked files without the reference trees, with Q07 armed in its registry and the candidate L4 files at their planned paths; `probe/` the standalone probes; `drv/` the drivers; raw outputs under `dvl/runs/`, the solver-swap runs under `swap/`). **The candidate files and the decisive probes are reproduced in Appendix A**, so nothing below depends on the scratch tree surviving. Every answer is re-captured on the real files by the lane that writes them (`scripts/pins.py --update --ref --module <ID>`, `pins.py --ref`, `firsttry.sh <ID> --empty-body`).

## R. Revision after the plan review (2026-10-06)

The review raised 3 blockers, 14 majors and 13 minors across the DV3b and DV4 plans, 19 of them on DV3b or on both (3 blockers, 9 majors, 7 minors). This revision applies each of those 19; the DV4-only findings are the DV4 lane's (`docs/design/DV4-PLAN.md` §15 records them). §R.1 lists the probes this revision ran; §R.2 gives each finding's disposition and where it landed; §R.3 the parts of fixes not taken, with the reasons; §R.4 what the revision relies on from DV4.

### R.1 Probes of this revision

Scratch: `/tmp/dvl0-plan3b4-dv3brev/` (`root/` a copy of the plan lane's root, Q07 armed, the candidate L4 files at their planned paths; each probe copied to a Q07 learner, exit or agent path so that the course tools treat it as that kind of file; `probe/` the probe files, reproduced in Appendix A.15; `drv/` the plan lane's drivers repointed, plus `drv/vc.sh` and `drv/ft.py`, A.15). Same rules as §0: the course wrappers, every `dvl` job clamped to 8 GB, one job at a time, `free -g` before each (≥ 91 GB available). The critic's probes under `/tmp/dvl0-plan3b4-critic/` are cited where this revision relies on them; their results were re-read from the critic's JSON outputs, not re-run.

| # | probe (A.15) | command | result |
|---|---|---|---|
| 1 | `b1_exit_shipped.dfy` at `dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy`: X1d's new scaffold (`Q08_ExitRev`, §3.7) and a second refiner `Q08_CanonProbe`, each refined `AddCorrect` shipped as `{ assume false; }`, item markers borrowed from Q07 | `vcheck --json` | `verified`, 135 verified; `holes`: exactly two, kind `assume`, at the learner file's lines 90 and 128, labelled with the two item ids; no hole at `QG_L4_BigNat.dfy`; diagnostics: W-D03 at those two lines only |
| 1 | same | `vaudit` (learner) | 2 findings: `audit-assume` at lines 90 and 128 |
| 1 | same | `drv/ft.py` (`firsttry`'s own `static_holes`, `lint_file`, `lint_hollow_module`) | `static_holes` [90] and [128]; `lint_file`: no finding; `lint_hollow_module`: only "X1d is in S6, not one of Q07's strands" (the borrowed ids), nothing else |
| 1 | same, then `b1_exit_filled.dfy` (the two references) | `drv/ft.py … exit` (`firsttry`'s `exit_run`) | shipped: both blocks `unattempted` ("hole at line 90" / "128"); filled: both `pass` |
| 1 | same | `drv/eb.py d … Q08_ExitRev.AddCorrect,Q08_CanonProbe.AddCorrect` (`dvl.dafny.empty_body`) | each `failed` on maxauto and on the shipped options under seeds 1, 2, 3 |
| 1 | X1d's body replaced by the single call `L4.AddCorrect(Rev(a), Rev(b))` | `vcheck` | `failed`, 134 verified, 2 errors (the parent's postcondition, `QG_L4_BigNat.dfy:298`) |
| 2 | `b2_bank_delivered.dfy` (the A.11 bank as a correct delivery: three proved, `CmpZeroMeansEqual` left bodyless, the refutation under `REFUTATIONS`; module `{:disableNonlinearArithmetic} Q09_AgentRedTeam`) at the Q07 agent path; `b2_bank_shipped.dfy` (all four bodyless) at `research/q09_bank.dfy` | `vcheck --json`; `vaudit`; `vaudit --mode agent`; `specfreeze --against research/q09_bank.dfy` | `verified`, 131 verified, one hole: `bodyless-method`, `Q09_AgentRedTeam.CmpZeroMeansEqual`, at its `ensures` line (37); `vaudit`: **1 finding**, `audit-bodyless-ghost` at the lemma's declaration line (35); `--mode agent`: 2 findings at line 35 (`audit-bodyless-ghost`, `bodyless`); freeze: 0 findings |
| 2 | `b2_bank_delivered.rs` (the A.11 Verus bank as a correct delivery, the false lemma's body `#[verifier::proof_note("Q09.A1v")] assume(false);`) at the Q07 `agent.rs`; `b2_bank_shipped.rs` (four labelled assumes) at `research/q09_bank.rs` | the same | verdict `verified`, one hole (`assume`, label `Q09.A1v`, line 37); `vaudit`: **1 finding**, `hole-assume` at line 37; freeze: 0 findings; the shipped bank: 4 holes, nothing else |
| 3 | `m2_agent_mono.dfy` (Q07's new Dafny refactor target, §2.5) at the agent path | `vcheck --gate`; `vaudit`; `vaudit --mode agent` | `verified`, 126 verified, 0 holes; 0 findings in both modes |
| 3 | `m2_agent_refactored.dfy` (the reference refactor); `research/q07_frozen.dfy` = the `FROZEN` section only | `vcheck --gate`; `vaudit`; `specfreeze --against research/q07_frozen.dfy` | 127 verified, 0 holes; 0 findings; 0 findings. Two first drafts failed and are kept as soft-spot material: a helper with a `nat` value parameter (`value does not satisfy the subset constraints of 'nat'` at the call passing `ToNat(s) * d`, nonlinear arithmetic off) and a helper called before `MulLimbCorrect` (`a precondition for this call could not be proved`, `Valid(MulLimb(s, d))`) |
| 3 | `m2_agent_weak_api.dfy` (the refactor with `ScaleTwice`'s validity conjunct dropped: an `API` statement weakened) | the same three | gate 127 verified; `vaudit` 0; freeze 0: **no machine-checked line catches it** |
| 3 | `m2_agent_weak_frozen.dfy` (`ScaledSum`'s validity conjunct dropped) | `specfreeze --against` | `freeze-changed — Q07_AgentRefactor.ScaledSum` |
| 3 | `m2_agent_mono.rs`, `m2_agent_refactored.rs` at the agent path; `research/q07_frozen.rs` the `FROZEN` section | `vcheck --gate`; `vaudit`; `specfreeze --against` | 4 and 5 verified, 0 holes; 0 findings each; freeze 0. `scale_twice`'s `ensures` weakened to `>=`: freeze 0; `scaled_sum`'s weakened: `freeze-changed — the statement of scaled_sum` |
| 4 | `m7_flag_statements.dfy` (the flagship's Dafny statements as bodyless **methods**, with witnesses) at the agent path and at `research/q08_statements.dfy` | `vcheck`; `vaudit` | 123 verified, 2 holes (`bodyless-method`), the witnesses verify against the statements; 2 findings (`audit-bodyless-compiled`) |
| 4 | `m7_flag_delivery.dfy` (A.9's delivery recast as method bodies) | `vcheck --gate`; `vaudit`; `specfreeze --against research/q08_statements.dfy` | 129 verified, 0 holes; 0 findings; **0 findings** |
| 4 | `research/q08_fn_statements.dfy` (a bodyless function) against `m7_fn_delivery.dfy` (the function with a body) | `specfreeze --against` | `freeze-changed — Q08_AgentFlagship.ShiftLimbs` (the critic's finding, reproduced) |
| 4 | `m7_flag_statements.rs` (external_body stubs, witnesses); `m7_flag_delivery.rs` (A.9's `flag_v.rs` plus witnesses) | `vcheck`; `vcheck --json`; `vcheck --brittleness` | statements: 2 holes (`external_body`); **A.9's delivery as recorded fails at the agent path**: `high_limbs` `failed` (`precondition not satisfied` at the `lemma_fundamental_div_mod_converse` call) on seeds 1–3. Repaired (A.15: `lo.len() == k`, a commutativity call, the equation stated): gate 9 verified, 0 holes; seeds 1–3 `stable`, but `high_limbs` spreads 274,368..4,852,723 (CV 81.7%) against the 6,000,000 limit; `vaudit` 0; `specfreeze --against research/q08_statements.rs` 0 |
| 5 | `research/t1v_snap.rs` (`trait Toggle { spec fn on(&self) -> bool; fn flip(&mut self); }`) against `t1v_cand.rs` (`flip` gains an `ensures`) | `specfreeze --against` (hash mode, the statement table `--check` uses) | `freeze-changed — the statement of Toggle::flip changed`; the critic's `freeze/snap2.rs` / `cand2.rs` (an exec fn gaining an `ensures`): `freeze-changed` |
| 6 | `m1_bv_cfree.rs` at `exit.rs`: Q07.H6v's and X1v's contracts with six bodies, no proof | `vcheck --json` | `h6v_divmod` (`/`, `%` by `2^64`) verified; `h6v_shift_cast` (`(p >> 64) as u64, p as u64`) failed; `h6v_shift_mask` failed; `x1v_mul` (`hi * 2^64 + lo`) verified; `x1v_shl_or` failed; `x1v_shl_plus` failed (`postcondition not satisfied`, and an overflow obligation for the addition) |
| 7 | `m8_q09x_d.dfy`: the re-posed Q09 Dafny exits (§4.8), nonlinear arithmetic on as the exit module | `drv/res3.py … 1 1,2,3` (both bundled Z3s × seeds 1–3) | `X1Ref` Passed in all six (23,816..23,819 under 4.12.1; 25,339..25,342 under 4.14.1); `X1Empty` and `X1OneStep` out of resource in all six (5,006,405..5,006,812); `X2Attempt` (the multi-trigger) out of resource in all six (5,010,369); `X2Ref` Passed in all six (71,802..217,725); `X2Calls` (three direct calls, no quantifier) Passed in all six (14,925..15,129); `X2Empty` Failed in all six (≈ 33,000, a quick failure); `LimbSumAppend` Passed (32,827..42,308) |
| 7 | `m8_q09x_v.rs` (the Verus twins), split into `_refs`, `_att`, `_one` files for the sweeps | `vcheck --json`; `vcheck --brittleness` | `x1v_ref` verified on seeds 1–3 (6,103..6,337); `x1v_one_step` (one `nonlinear_arith` with the three `requires`) **verified** on seeds 1–3 (4,368..4,536); `x1v_empty` failed; `x2v_attempt` `inconclusive` on seeds 1–3 (rlimit exceeded); `x2v_ref` verified on seeds 1–3 (5,155..5,163); `x2v_calls` verified; `x2v_empty` failed; `lemma_limb_sum_append` verified (42,775..46,559) |
| — | the critic's construct-free probes (re-read) | `out_crit_v.json`, `out_crit_t1d.json`, `out_crit_d.json`, `out_crit3_v.json` | verified: Q09.H1v's statement in one scoped `nonlinear_arith`; Q07.H6v by `/` and `%`; Q07.X1v by `*` and `+`; Q09.T1d by plain induction in a nonlinear-off module; the old Q09.X2d by two `WSucc` calls; the old Q09.X2v by two `lemma_weight_succ` calls and `lemma_mul_is_associative` (the two calls alone failed) |

Not run by this revision: the Python gate core (still a sketch, §4.6); the `stable` and `nl-steps:2` forms (not built, §6 Q43); `open_specs` (not built); any card demo; the Verus `x2v_calls` seed sweep (one default run); EM. The module lanes re-capture everything on the real files.

### R.2 Findings and dispositions

| # | finding (plan, severity) | disposition | where |
|---|---|---|---|
| 1 | Q08's refinement-hole form breaks the tools (DV3b, blocker) | applied: the refined lemma ships with the body `{ assume false; }` (a third option, §R.3); probed with the tools as built (R.1 #1); QPLAN §6 Q40 extended to the lint, hole attribution, the counts pin and `firsttry --check/--exit/--report/--empty-body` | QPLAN §14.0, §16.1, §16.2, §6 Q40; here §3.2, §3.7 |
| 2 | Q09's red-team contract cannot be met by a correct delivery (DV3b, blocker) | applied: the `.audit` pins are dropped; the acceptance line is "`scripts/vaudit <file>` reports exactly one finding per lemma the report names as false, of a hole kind, and no other"; every line run on both twins with the false lemma left as shipped (R.1 #2); the bank module is `{:disableNonlinearArithmetic}` | QPLAN §17.1, §17.4; here §4.5 |
| 3 | The gate core's `fvh` modules have no owner (both, blocker) | applied on DV3b's side: assigned to DV4 step 1a (as the DV4 revision already records), the names aligned with DV4 §3.7, QPLAN §6 Q33 now says "assigned", the DELTAS entry requested (§6 Q46) | QPLAN §6 Q33, §17.7; here §7 |
| 4 | Constructs avoidable at the pin (DV3b, major) | applied: per-item `form:` lints (`bv-exec`, `no-nl`, `nl-steps:2`, `trigger`, `stable`) and `// cfree:` twin lines gated like `// triv:` (QPLAN §6 Q43); Q09's exits re-posed (R.1 #7): X1d now fails at the pin without the construct, and the construct-free answers of X1v, X2d and X2v are stopped by their forms and `need:` lines; the citations that rest on a presence check marked `# nominal:`; a construct-free column in §0.2 | QPLAN §5.2, §6 Q43, §14.0, §15.2, §15.3, §17.2, §17.3, §17.11; here §0.2, §2.2, §2.8, §4.2, §4.8 |
| 5 | Q07's agent file holds Q07 answers (DV3b, major) | applied: a new refactor target over compositions of L4's `Add` and `MulLimb` (Dafny) and `big_add` and `mul_limb` (Verus), with no literal unfolding; verified (R.1 #3); agent files and twins added to the leak check | QPLAN §15.1, §15.4; here §2.5, §2.7, A.15 |
| 6 | P2dv's answer printed in the T blocks (DV3b, major) | applied: both attempts quoted in P2dv's own block; T prompts without a verdict; `Q09_Triggers.dfy`'s header line; P1d's and P2dv's answer vocabularies spelled out; §14.0 and §6 Q42 neutral | QPLAN §14.0, §17.1, §17.2, §6 Q42; here §4.1, §4.2 |
| 7 | `classify` reads the fixture's label (DV3b, major) | applied: `classify(results)` and `gate(delivery)` decide from instrument results only, a mechanical `PASS` carries the undecided grader-only classes as `unknown`; only `corpus_report` reads labels; the frozen tests check label independence | QPLAN §17.2, §17.7; here §4.6 |
| 8 | The Q07 Qwen replay stages the wrong input and its acceptance cannot run in the container (both, major) | applied on DV3b's side, with DV4's revised §6: the starting state is the snapshot's commit, the snapshot read-only in the container, `specfreeze` a trusted tool, the acceptance lines in DV4's checked forms, the `git diff` line an audit line with `patch.diff` as evidence, no `.audit` pin needed | QPLAN §15.1, §15.4, §6 Q31; here §2.5, §7 |
| 9 | Rung 7's premise undone by its own acceptance (DV3b, major) | applied: the snapshot holds only `FROZEN`; the diff line covers `FROZEN` only; `API` is what callers rely on and no line pins; a weakened `API` statement passes every machine line (R.1 #3) | QPLAN §15.4; here §2.5 |
| 10 | The flagship's freeze check fails a correct Dafny delivery (DV3b, major) | applied: the learner states Dafny operations as bodyless methods (a decision, QPLAN §6 Q45), not a tools change (§R.3); the flagship's lines re-run on the twins (R.1 #4), which also found and repaired a failing Verus reference | QPLAN §16.4, §6 Q45; here §3.4, A.15 |
| 11 | Statement holes break `specfreeze --check` and rubric A5 (DV3b, major) | applied: tools item `open_specs` (QPLAN §6 Q44), probed for a trait method (R.1 #5); the Q07 and Q08 rubrics' A5 line names the open statements | QPLAN §6 Q44, §14.0, §15.1, §15.2, §16.1, §16.2; here §2.2, §3.2 |
| 12 | Exits not unseen (DV3b, major) | applied by re-posing: Q08.X1d's scaffold no longer shows the answer's pattern; Q09.X1 is a product plus a carry, Q09.X2 a limb sum with a different trigger move (R.1 #1, #7) | QPLAN §5.2; here §3.6, §3.7, §4.3, §4.8 |
| 13 | Leaks in the learner-visible plan (DV3b, minor) | applied: §5.2's empty-body row, §14.0's nonlinear row, §6 Q35, §17.3's count, H2py's prompt, H1d's prompt rephrased | QPLAN as listed |
| 14 | P4py ambiguous (DV3b, minor) | applied: 60 tasks in each arm, the call named without its value | QPLAN §17.2 |
| 15 | Gated items admitted before their gate (DV3b, minor) | applied: `admitted = false, minutes = 0` until the four results are recorded | QPLAN §16.3, §16.6, §16.7, §6 Q34 |
| 16 | Language balance and pairing beyond design (DV3b, minor) | applied by recording, not rebalancing (§R.3): a language-share row and a pairs row in §5.2, a DELTAS entry proposed (§6 Q46) | QPLAN §5.2, §6 Q46 |
| 17 | Card designs fail the course's checks (DV3b, minor) | applied: C1d's and C4dv's Dafny demos refine `QG_L4_Spec` with a model whose lemmas need no limbs, so no specimen declares an abstract module; C3v's demo only reads | QPLAN §16.1, §16.2; here §3.3 |
| 18 | Small inconsistencies (DV3b, minor) | applied: the bank module's options; the check unit's two tests, the mutant test printing; §6 Q31 aligned with DV4 (HTTP gate, report-only access, no `sudo` from scripts) | QPLAN §15.1, §15.5, §17.1, §6 Q31 |
| 19 | Q07's arming waits on a host action (both, minor) | applied: Q07 arms with A2d pending; the chapter says the replay needs `contract_local.sh` | QPLAN §6 Q31, §15.2, §15.4, §15.7 |

### R.3 Parts of fixes not taken, and why

- **Finding 1, options (a) and (b).** (a) restates the inherited `ensures` on a bodyless refined lemma and asks the tools to drop the duplicate hole at the given line; (b) maps given-line holes to the refining declaration. Both need a tools change, and (b) cannot attribute a hole when two refiners leave the same lemma open (both map to one given line, with the parent's label only). The `assume false` body needs no tools change, attributes each hole to its refiner's line with the item's label, uses a hole form the course already has (Q06.X1d, Q08.T1d), and keeps the inherited statement unchangeable. Its cost: the statement is not on the learner's line, so each block's comment quotes it.
- **Finding 4, re-posing every item.** Re-posed: Q09's four exits (R.1 #7): X1d fails at the pin without the construct; X2d's and X2v's construct-free answer (direct calls of the append lemma) verifies, and is stopped by `need:` lines that require the quantified fact and by the `trigger` form; X1v's one scoped step verifies, and is stopped by `nl-steps:2`. The X2 pair needed a re-pose for unseen-ness (T1's move) more than for construct necessity. Not re-posed, gated by a form instead (the review's own alternative): Q07.H6v, H7v, X1v (`bv-exec`: once `*`, `/` and `%` are out of the exec code, every construct-free answer probed fails, R.1 #6), Q07.H5v, X2v (`no-nl`), Q09.H1v, X1v (`nl-steps:2`: one scoped step verifies at the pin, R.1 #7), Q09.T1d, T1v (`trigger`). For a matching-loop lesson there is no statement that forbids a proof without a quantifier: a step fact can always be proved by induction or called directly, so a presence check is the honest limit, and the citation is marked `# nominal:`.
- **Finding 8, staging from the snapshot file.** The review proposed staging the allowed files from the snapshot itself. With finding 9 the snapshot holds only the `FROZEN` section, so it cannot be the starting file. DV4's revised §6 stages from the snapshot's commit instead (`git show <rev>:<path>`), which needs no second file: the learner commits the snapshot with the agent file still as shipped.
- **Finding 10, the tools change.** Comparing a frozen bodyless function without its body in `--against` hash mode would also work, but needs a tools change before Q08 and leaves the Dafny and Verus statement forms different. Methods with `ensures` need nothing, mirror Verus's stubs, and were re-run end to end on the pins.
- **Finding 16, rebalancing.** Reaching 35/65 in Q07 would move 4 minutes from the D→V port (design §6.5) to new Dafny holes; reaching 30/30/40 in Q09 would need 35 more proof-hole minutes in a module whose 295 are design §7.5's. The tier rule holds (47/53), and the one-language constructs are design §6.4's own list, so the deviations are recorded instead.
- **Finding 17, a given file or a lint exemption for card demos.** Both add surface (a card-only given file in L4, or a lint exemption a learner specimen could exploit). Refining L4's existing `QG_L4_Spec` with a trivial model needs neither.
- **The rung-7 soft spot "an `API` statement weakened to fit a helper"** is now the file's designed catch (R.1 #3), not only a rubric point.

### R.4 What this revision relies on from DV4

`docs/design/DV4-PLAN.md` as revised the same day: §3.7 (`fvh.verdicts`, `fvh.corpus`, `fvh.tools`, the provenance rule, the recorder, all at build step 1a), §6 (the starting state from the snapshot's commit, the `snapshot` role, `scripts/specfreeze` among the trusted tools, the acceptance-line forms, `--available`, `--model` limited to pinned tags), §13 (Q07 armed with A2d pending; the Q09 paragraph). If DV4 changes any of these, QPLAN §6 Q31, Q33, §15.4 and §17.7 change with it.

## 0. What was and was not run

### 0.1 Verification of the candidates

All verified with 0 holes and 0 errors unless stated. "D" = Dafny symbol, "V" = Verus function; per-symbol verdicts are from `--json`'s `per_symbol`.

| candidate | command | result |
|---|---|---|
| L4 Dafny (`root/dafny/given/Q/QG_L4_BigNat.dfy`, A.1) | `vcheck`, `vcheck --gate`, `vaudit`, `vaudit --mode given`, `vcheck --brittleness` | `verified — 122 verified, 0 holes, 0 errors` (gate); `0 finding(s)` in learner and given mode; `seed 1: verified · seed 2: verified · seed 3: verified — stable`, widest spread `QG_L3_BigNat.FromNatCorrect 41897..48129 (CV 6.0%)` |
| L4 Verus (`root/verus/given/qg_bignat_l4`, A.2) | the same | `verified — 15 verified, 0 holes, 0 errors` (gate); `0 finding(s)` in both modes; seeds 1–3 `stable`, widest spread `qg_bignat_l4::lemma_add_lift 252242..354101 (CV 14.0%)` |
| L1–L4 Dafny under both bundled Z3s | `drv/res2.py` | exit 0 under 4.12.1 and under 4.14.1; 122 verification tasks passed, none failed, in each |
| Q07 Dafny fragments (A.3: T1d, H1d, H2d, H3d) | `vcheck` on the planned exercise path | 129 verified (the file with the L1–L4 chain) |
| Q07 Verus fragments (A.4: T1v, H4v, H5v, H6v) | `vcheck` on the scratch crate `q07_internals_i` | 6 verified |
| Q07 port (A.5: `from_u128`, `from_nat_mirror`, `lemma_mirror_meets_port`) | `vcheck --module Q07` | 6 verified |
| Q07 exits (A.6: X1d, X2d; X1v, X2v) | `vcheck --module Q07` | Dafny 127 verified (the probe file also held an early `AddCCanonical` helper, now Q08.H7d's reference); Verus 3 verified |
| Q07 agent target, Dafny (A.7) — **superseded**: it held T1d's statement and answer and P1dv's literal (§R.2 #5); the new target is §2.5, verified in §R.1 #3 | `vcheck --module Q07`; `vaudit` (learner, agent) at the agent path | 126 verified (the monolithic shipped state); `0 finding(s)` in both modes |
| Q08 Dafny fragments (A.3: `Q08Canon`, `Q08Words`, `Q08CanonRaw`) | `vcheck` | 137 verified, then 142 with `Q08CanonRaw` |
| Q08 Verus fragments (A.4: `Odometer` + `Odo` + `advance_twice`, `scale`, `bump`, `transfer`) | `vcheck` | 14 verified in the crate (after the rename of §0.3) |
| Q08 verified wp (A.8) | `vcheck --module Q07` | `SubstEOk`, `SubstBOk`, `WpSound`, `SwapOrders` verified; the two comparison lemmas with empty bodies (`SubstEOkEmpty`, `WpSoundEmpty`) fail (`35 verified, 6 errors`: one failing return path for the first, five for the second) |
| Q08 flagship references (A.9) | `vcheck --module Q07`; `vaudit` (learner, agent) on the Dafny file at the agent path | Dafny 130 verified; Verus 8 verified; `0 finding(s)`. **Revision:** at the agent path the Verus delivery's `high_limbs` fails on seeds 1–3; repaired, and the Dafny delivery recast as methods (§R.1 #4, A.15) |
| Q08 exits (A.6b: X1d `Q08_ExitRev`, X2d `FlatSame`; X1v `sum_words`, X2v `Ledger::record`) | `vcheck --module Q07 --json` | every reference verified; the comparison bodies fail: X1d with the single library call only (`failed`), X2d with no `decreases` (`cannot prove termination; try supplying a decreases clause`) and empty (`failed`), X1v with `T::zero()` (`postcondition not satisfied`) |
| Q09 T1d (A.10, module `Q09Triggers`, nonlinear arithmetic off) | `vcheck`; `dvl.dafny.empty_body` | verified (143 in the Q07 candidate file, where it was appended); gate `lever-needed` (§0.2) |
| Q09 T1d attempt and rewrite, nonlinear off / on (`t1att_d`, `t1_d`, `t1atton_d`, `t1on_d`) | `vcheck --module Q07 --brittleness` | **off:** attempt `seed 1: inconclusive · seed 2: inconclusive · seed 3: inconclusive — NOT stable`, rewrite verified (`123 verified, 0 errors, 1 out of resource`: the attempt in the same file); **on:** attempt and rewrite each `seed 1: verified · seed 2: verified · seed 3: verified — stable` (§0.3) |
| Q09 T1v attempt (`t1att_v`) and rewrite (`trig_v`'s `mono_rewrite`) | `vcheck --module Q07 --brittleness`; seeded `vcheck` | attempt `inconclusive` ×3, `NOT stable` (rlimit 6,000,000 each); rewrite verified on seeds 1–3 (6,628..7,017) |
| Q09 H1d repair and P1d's attempt (A.10) | `drv/res2.py` | repair Passed under 4.12.1 (11,177) and 4.14.1 (11,398); attempt Failed under 4.12.1 (5,006,650, out of resource) and Passed under 4.14.1 (38,790) |
| Q09 H1v reference and attempt (`h1v_v.rs`, the exact statement) | `vcheck --module Q07 --brittleness` | reference verified on seeds 1–3 (3,898..3,947); attempt fails on seeds 1–3 (1,210..1,244: a quick failure, not a timeout) |
| Q09 exits (A.6c: X1d `ThreeBelowCube`, X2d `WPlusTwo`; X1v, X2v) — **superseded** by the re-posed exits (§4.8, §R.1 #7) | `drv/res3.py` (Dafny, both solvers × seeds 1–3); `vcheck --module Q07 --brittleness` (Verus) | X1d and X2d Passed in all six runs (X1d 14,716 under 4.12.1, 16,247 under 4.14.1; X2d 22,074..22,397); X1d's empty body out of resource, X2d's attempt and empty body fail. X1v verified on seeds 1–3 (6,415..6,702), **and so does its one-step version** (11,202..13,940); X2v verified on seeds 1–3 (319,437..343,647), its attempt fails on each |
| Q09 red-team banks (A.11) | `vcheck --module Q07`; `vaudit` (learner, agent) on the Dafny bank at the agent path | Dafny 131 verified (three true lemmas and the refutation, `{:fuel Cmp, 4}`); Verus 4 verified; `0 finding(s)` in both modes. That run **left the false lemma out**; with it left bodyless, as a correct delivery leaves it, see §R.1 #2 |

### 0.2 Empty-body gate

`dvl.dafny.empty_body` (maxauto, then the shipped options under seeds 1–3) and `dvl.verus.empty_body` (E0, E0H, E1, E2, EC, NL, BV for proof fns; E0, E0H, E1, E2, EC, TRIV, and INV where a loop exists, for exec fns; seeds 1–3). EM (memory-heavy) was not run (the lane's share is 8 GB, Δ57). "pass" = every run fails, as the gate requires.

The third column (added by the revision, §R.2 #4) gives, for each checked use of a WRITE construct, an answer that avoids the construct, whether it verifies at the pin, and what stops it: the pin itself, or the item's `form:` line (QPLAN §6 Q43). Each such answer goes into the twin as a `// cfree: { … }` line, which `firsttry --empty-body` runs once Q43 is built; every one must fail verification or the form. "—" = no construct-free answer is known that verifies (the construct is needed at the pin).

| item | empty-body result | construct-free answer (verdict at the pin) → what stops it |
|---|---|---|
| Q07.T1d `ThreeLimbs` | maxauto failed; the shipped seed runs **verified because the candidate carried its `{:fuel ToNat, 4}` attribute**, which is the answer and is not in the learner's shipped form. Without it the statement fails, with nonlinear arithmetic on (`fuel_d.dfy`'s `A3`) and off (`fueloff_d.dfy`'s `A3`). The module lane gates the shipped form | — (unfolding by hand is the construct's hand form, C1d) |
| Q07.H1d `AddCarriesTwice` | maxauto and seeds 1–3 failed. pass | — (`AddC` is opaque: a `reveal` and its unfolding are needed) |
| Q07.H2d `DivLimbBound`, H3d `DivLimbStep` | maxauto verified (nonlinear arithmetic on), seeds 1–3 failed: `lever-needed` (nonlinear arithmetic off), as planned (Δ45, Δ46) | — (with the module's attribute; a learner who deletes the module attribute bypasses the lever, the residual of every Δ46 lever, left to the rubric) |
| Q07.T1v `lemma_three_limbs`, H4v `lemma_two_limbs_then`, H5v `lemma_div_weight_succ` | E0, E0H, E1, E2, EC, NL fail on every seed; the BV runs end without a verdict (an error before verification; for H4v the harness's wall-clock kill, exit 124). pass | T1v, H4v: —. H5v: a proof by `nonlinear_arith` steps around `lemma_weight_succ` (not measured) → `form: no-nl` |
| Q07.H6v `split_word` | E-modes fail on every seed; TRIV `{ (0u64, 0u64) }` fails on seeds 1–3, `{ ((p >> 64u128) as u64, 0u64) }` fails on seed 1 (its one run). pass | `{ ((p / 2^64) as u64, (p % 2^64) as u64) }` **verifies** (§R.1 #6; the critic's `crit_split_word_divmod`) → `form: bv-exec`; under the form, a shift with a cast or a mask and no `bit_vector` proof fails (§R.1 #6) |
| Q07.H7v `from_u128` | not gated by the plan lane | the split by `/` and `%` (by H6v's result, not measured) → `form: bv-exec` |
| Q07.X1v `join_word` | not gated by the plan lane | `{ (hi as u128) * 2^64 + (lo as u128) }` **verifies** (§R.1 #6; `crit_join_word_mul`) → `form: bv-exec`; under the form, `<<` with an `or` or a `+` and no proof fails (§R.1 #6) |
| Q07.X2v `lemma_weight_quotient` | not gated by the plan lane | `nonlinear_arith` steps (not measured) → `form: no-nl` |
| a Verus division-by-a-limb candidate `lemma_div_limb_step` (the first plan for H5v) | **NL verifies on seeds 1–3**: rejected (Δ49's pattern), replaced by `lemma_div_weight_succ` | — |
| Q08.H1d `Q08Canon.AddCorrect`, H2d `Q08Canon.FromNatCorrect`, H7d `Q08CanonRaw.AddCorrect`, T1d `AddWithCarry` | maxauto and seeds 1–3 failed (bodyless form); the revision's `{ assume false; }` form: the X1d probe and a canonical refiner fail on maxauto and seeds 1–3 (§R.1 #1). pass | — (a refined statement is proved in its refiner) |
| Q08.H4v `scale` | every mode fails on every seed, INV and TRIV `{ T::zero() }` included. pass | — (through the trait only) |
| Q08.H5v `bump`, H6v `transfer` | TRIV fails on seeds 1–3. The E-modes verify because the reference has no proof span (they reproduce code-only references, as Δ139 noted for Q05); the module lane gates the shipped `external_body` forms, where only TRIV and INV are meaningful | — (a cell is read and written only through its permission) |
| Q09.T1d `PowGrowsByBase` (in a nonlinear-off module) | maxauto verified, seeds 1–3 failed: `lever-needed` (nonlinear arithmetic off) | plain induction with no quantifier **verifies** (the critic's `CritPowGrowsByBaseInduction`) → `form: trigger` (presence only: `# nominal:`) |
| Q09.T1v `lemma_weight_strict_mono` | not gated by the plan lane | induction with `lemma_weight_succ` (not measured; by T1d's result) → `form: trigger` (`# nominal:`) |
| Q09.H1d `ProductBelowSquare` | not gated by the plan lane; the empty body and P1d's one-assertion attempt fail under the pinned solver (§0.3) | — under the pinned solver → `form: stable` keeps a proof that only the other solver or one seed accepts out |
| Q09.H1v `lemma_product_below_square` | not gated by the plan lane | one `nonlinear_arith` scoped by `requires x < p, y < p` **verifies** (the critic's `crit_h1v_one_step`) → `form: nl-steps:2` (`# nominal:`) |
| Q09.X1d (re-posed) | `X1Empty` out of resource under both solvers, seeds 1–3 (§R.1 #7) | one assertion `x * y <= (p - 1) * (p - 1)` out of resource in all six rows (§R.1 #7) → — ; `form: stable` |
| Q09.X1v (re-posed) | `x1v_empty` failed (§R.1 #7) | one scoped `nonlinear_arith` with the three `requires` **verifies** on seeds 1–3 (§R.1 #7) → `form: nl-steps:2` (`# nominal:`) |
| Q09.X2d (re-posed) | `X2Empty` failed in all six rows (§R.1 #7) | three direct `LimbSumAppend` calls **verify** in all six rows → `need:` lines (the quantified fact and its `LimbSumAppend` body) and `form: trigger`; the quoted multi-trigger attempt is out of resource in all six |
| Q09.X2v (re-posed) | `x2v_empty` failed (§R.1 #7) | three direct `lemma_limb_sum_append` calls **verify** → `need:` lines and `form: trigger`; the attempt is `inconclusive` on seeds 1–3 |
| Q07 H8v, H9v, every other X item, Q08's verified-wp holes and the Python holes | not gated by the plan lane | Q08's and Q07's other constructs: — |

### 0.3 The probes behind the plan's decisions

- **`recommends` (Q07, §6 Q26).** `rec_v.rs` re-run with `vcheck --module Q07`: `per_symbol` `r1: verified, r2: failed, r3, r4, r5, top_checked: verified`; the JSON `diagnostics` hold `postcondition not satisfied` (severity `error`) and `recommendation not met` (severity `info`) at r2's `ensures`; the text output prints only the error. `rec2_v.rs` (`spec(checked)` fns that call `top` without meeting its recommendation, or index without a bound): four `warning: recommendation not met` at the definitions, exit 0. Nothing about `recommends` fails a done gate, so no hole can check it: RECOGNISE (card C6v, prediction P6v).
- **`isolate` (Q07, §6 Q26).** `iso2_d.dfy`: three lemmas with the same three false assertions (`x == 1`, `x == 2`, `x == 3`) give 2 errors each (the first two assertions; once both are assumed the context is contradictory), plain, under `{:isolate_assertions}` and with `{:isolate}` on the second (P7d). `noiso_d.dfy`: L4's two loops verify without their `{:isolate_assertions}` attribute (124 verified). **As built (DV3b spine lane):** not reproduced at seeds 1–3 on the built L4, whose `AddLoop` is inconclusive on both bundled solvers without the attribute; the built file keeps it (DELTAS Δ163). No candidate turned an out-of-resource batch into a verified one by isolating it. RECOGNISE (card C4d).
- **Dafny bit-vectors (Q07).** `bv_d.dfy` and `bvoff_d.dfy` (nonlinear arithmetic on and off): pure bit-vector facts (`MaskIsMod`, `JoinBits`, `SplitWideEmptyProof`) verify with empty bodies, so they cannot be holes, and the bridge from `bv128` to `nat` (`SplitWide`) is `Verification out of resource` at the pin in both (P4d). Bit-vectors are a Verus WRITE construct only, and `bv-types` a Dafny RECOGNISE card.
- **The name `big_add` (§14.1 rule 8, §6 Q28).** With L4's addition named `add`, the Q08 Verus fragments, which write `use vstd::prelude::*; use qg_bignat_l4::*;`, failed with `` error[E0659]: `add` is ambiguous `` (two glob imports of one name). Q04.P8dv's Verus half is about a *local* item shadowing a glob import, so this behaviour is near a Q04 prediction: QPLAN gives no reason.
- **The solver swap (Q09).** `drv/swap_survey.py` over every Dafny twin of Q01–Q06 (23 files, each with its layers): the same summary line under 4.12.1 and 4.14.1 for every file, no failure in either. Resource counts move by up to 3.7× (`Q06_Machine.TwoShifts` 79,928 → 294,283; `Q05_Frames.Push` 444,152 → 703,508). Nonlinear product bounds are where the solvers differ: `var_d.dfy` (24 hint variants of `x * y < Pow(2 * n)`, 30M limit): 4.12.1 fails all 24, 4.14.1 proves 18 (78,105..760,490) and fails 6. `s3_d.dfy` at the pin: `x * y < Pow(n) * Pow(n)` with the one assertion `x * y <= x * p` (`P1`) fails under 4.12.1 (5,006,650) and verifies under 4.14.1 (38,790); the empty body (`P0`) fails under both. `s2_d.dfy` (`x * y < Pow(m + n)`): three hint variants fail under both solvers and one verifies under both. No flip in the other direction (green at the pin, red under 4.14.1) was found. So the Q09 Dafny repair runs in the direction "proved by the other bundled solver, not by the pinned one".
- **Verus seeds (Q09).** No Verus seed flip was found: `nl_v.rs`, `split_v.rs`, `split2_v.rs`, `loop_v.rs`, `loop20_v.rs`, `trig_v.rs`, `t1att_v.rs`, `h1v_v.rs`, `x09_v.rs`, `x09b_v.rs` give the same verdict per function under seeds 1–3. Resource spreads differ widely (`split2_v`'s `three_sum_prod_one` 31,511 / 36,875 / 7,265, CV 51%; its split version 68,322 / 54,542 / 39,248, CV 22%), so a split does not reliably lower the spread. Hence the Verus half of the repair pair repairs a verdict (H1v's attempt fails on every seed), and the seed sweep is its measurement.
- **Matching loops and nonlinear arithmetic (Q09).** Dafny `trig3_d.dfy` (nonlinear off): a quantified step `Pow(k) < Pow(k + 1)` with `{:trigger Pow(k)}` is out of resource under both solvers (5,007,174 and 5,007,212); with `{:trigger Pow(k + 1)}` it verifies (18,243 and 18,107). **With nonlinear arithmetic on, T1d's attempt verifies on seeds 1–3** (`t1atton_d.dfy`), and so does T1d's empty body (the gate's maxauto run): the attempt fails only because the recursion's last step is a nonlinear fact the off-module cannot see while the loop burns the budget. Hence T1d lives in its own nonlinear-off file (QPLAN §17.1). Verus `trig_v.rs`: `#[trigger] weight(k)` exceeds the rlimit on seeds 1–3, `#[trigger] weight(k + 1)` verifies (6,628..7,017). A prefix-value step (`trig5_v.rs`, `trig6_d.dfy`) did **not** loop in either language. `trig4_v.rs`, `x09_v.rs`, `x09b_v.rs`: a trigger on `weight(k + 1)` never matches `weight(n + 2)`, so the fact never fires; with `#[trigger] weight(k)` and the two step assertions it verifies, without the assertions it exceeds the rlimit. These shaped T1 and the X2 candidates.
- **The MDE and the Wilson bound (Q09).** `uv run --directory harness python` in the scratch root: `mde_two_proportions(60, 0.5)` = 0.245 (`paired=True` 0.251), `(60, 0.3)` 0.25, `(40, 0.5)` 0.295, `(40, 0.3)` 0.307, `(20, 0.5)` 0.395; `wilson_interval(0, 9)` = (0.0, 0.299), `(0, 18)` = (0.0, 0.176). Design §11.2's "MDE at n = 60 ≈ 15–20 pp [A]" is below `fvh.stats`' 24.5 pp (§6 Q35).

### 0.4 Not run

EM; the marker-level check (stubs and the full registry check; §5.2 hands it to the integration lane); the empty-body gate on the items §0.2's last row lists; the Q08 exits' and Q07's port items' seed sweeps; the forensic deliveries (their species and instruments rest on the cheat corpus's recorded classes and outcomes, §4.4); the gate core (a sketch only, §4.6); the Qwen replay and every sandbox step (DV4 builds them); any LSP run (Q09's LSP content is reading only); `scripts/ci.sh`.

## 1. Layer L4

**Candidates:** Appendix A.1 (Dafny) and A.2 (Verus), verified (§0.1). Each holds exactly QPLAN §14.2–§14.3.

- **What is new against DV0's spike.** The spike's L4 sat on the spike's L1–L3, which differ from the built ones (`FromNatCorrect` and `CmpCorrect` were in its L3). The candidate re-supplies `CmpCorrect` (Q04.H4d) and `PowAdd` (Q04.H1d) in Dafny, and `cmp` (Q04.H4v), `lemma_weight_add` (Q04.H1v) and `lemma_seq_to_nat_append` (Q06.H3v) in Verus. The spike's arithmetic module is folded into `QG_L4_BigNat` (one spine module, plus `QG_L4_Spec` and `QG_L4_Limbs`, named with the layer prefix for the isolation group). The Verus trait drops `times` (no full multiplication in L4, Δ50) and the spike's generic client (it becomes Q08.W1v, given in Q08's file). `add` is `big_add` (§0.3).
- **Re-supplied proofs and the leak patterns (Δ130).** `CmpCorrect`, `cmp` and `lemma_seq_to_nat_append` are the Q04 and Q06 twins' proofs, verbatim (`cmp` with its `broadcast use` line). `PowAdd` and `lemma_weight_add` are proved by library calls, not by the twins' `calc` chains, so they are whole answers of Q04.H1d and H1v by a different route. Any Q04 or Q06 leak pattern that matches L4 is exempt by the leak README's rule 2 (L4 is a detailed layer, above the moderate patterns' module). Q04's patterns exclude H4d and H4v (their blueprint problems, Δ143), so the integration lane should expect at most Q04.H1d/H1v and Q06.H3v hits, each listed as `exempt:`.
- **Exit answers.** L4 holds no exit answer of Q01–Q06: checked against `Q01-Q03-author-notes.md` and `Q04-Q06-author-notes.md` (their exit sections). The near ones: Q04.X1d (`ToNatAppend`, Dafny): L4's Dafny holds no append lemma (the Verus append is Q06.H3v's, a hole); Q04.X2d (`PowsBelow`): `PowAdd` is not it; Q04.X1v (`lemma_limb_square`): `MulLimbDigit` is a different statement in the other language; Q06.X2d/X2v (`LowOfShift`): nothing about `%` by a variable.
- **Tiers.** The Dafny layer's `import opened Std.Arithmetic.Mul` makes it `std`; the Verus `use vstd::arithmetic::mul::*` makes it `arithmetic`. The import-tier check of the plan lane's scratch registry was not run to the end (its Q07 record lacked the planned files); the integration lane runs it.
- **Header text** (for the spine lane): as L3's (Δ138), with "Do not open this file before you start Q07"; nothing about tiers, `Std`, nonlinear arithmetic, fuel, opacity, isolation or broadcast.

## 2. Q07

### 2.1 Prediction answers

| item | answer | evidence |
|---|---|---|
| P1dv | `D:fail ok V:fail fail` | `fueloff_d.dfy` (nonlinear arithmetic off, as Q07's module): `A2` (the literal) fails, `T2` (the tail) verifies; `A3`, `A4` fail and their `{:fuel ToNat, 4/5}` versions verify; `fuel_d.dfy` (nonlinear on) gives the same. `fuel_v.rs`: `a2` and `t2` fail; `a2fuel`, `a3fuel` verify; `t2fuel` still fails (the tail needs the `drop_first` extensionality facts, not more fuel) |
| P2dv | `D:ok V:fail` | Dafny: the method's body computes its postcondition's expression, so it verifies; `div_d.dfy` shows Dafny's `int` division is Euclidean (`(-7) / 2 == -4 && (-7) % 2 == 1` verifies, `== -3` fails). Verus `div_v.rs`: with `requires x == -7`, `ensures r == x / 2` fails (spec `/` is Euclidean, exec `/` on `i64` truncates) and `ensures r == -3` verifies; `(-7int) / 2 == -4, (-7int) % 2 == 1` verifies in spec. The unconstrained scenario has `x = -7` among its inputs, so it fails too. Keep `x` unconstrained in the scenario (a `requires x >= 0` would make the statement true) |
| P3v | `b` | `digit_v.rs` (one crate): `split_nl` fails, `split_bv` verifies, `split_compute` fails (`warning: Failed to simplify expression … before sending to Z3`, then `assertion failed`), `split_plain` fails. The probe put the four in one crate; the scenario's one-crate-each form is to be re-captured by the module lane |
| P4d | `D:timeout` | `bvoff_d.dfy`: `Verification out of resource (ProbeBvDOff.SplitWide)` (`vcheck --json` verdict `inconclusive`; Q01.P1dv's vocabulary writes it `timeout`) |
| P5dv | `D:fail ok V:ok fail` — **re-captured as built (DV3b integration): `D:ok fail V:ok fail`** on the real scenario, in all seeds and under both bundled solvers; the pin and the reference slot carry the re-capture (`Q07-code-notes.md` §2, §7; the A.12 probe line below is the superseded one) | `comm_d.dfy` (nonlinear off): `Comm` fails, `Dist` verifies; `comm_v.rs`: `comm` verifies, `dist` fails |
| P6v | `V:ok` | `rec_v.rs`'s `r1` |
| P7d | `D:2 2 2` | `iso2_d.dfy`: `24 verified, 6 errors`, two per lemma |

### 2.2 Holes, test-out items and exits: references and sizes

References: Appendix A.3 (Dafny), A.4 (Verus), A.5 (port), A.6 (exits). Body lines (non-blank, non-comment):

| item | reference (summary) | lines |
|---|---|---|
| T1d | `{:fuel ToNat, 4}` on the lemma (or three unfolding assertions with `[a, b, c][1..] == [b, c]` and `[b, c][1..] == [c]`) | 0–5 |
| T1v | `reveal_with_fuel(seq_to_nat, 4)` and three `drop_first` extensionality assertions | 4 |
| H1d | `reveal AddC();` with `{:fuel AddC, 4}` on the lemma | 1 |
| H2d | `LemmaMultiplyDivideLt(v, d, BASE)` | 1 |
| H3d | `LemmaMulInequality(r + 1, d, BASE)`, distributivity and two commutativity facts, then `LemmaMultiplyDivideLt(r * BASE + x, d, BASE)` | 5 |
| H4v | `reveal_with_fuel(seq_to_nat, 3)` and two extensionality assertions | 3 |
| H5v | `lemma_weight_succ(n)`, `lemma_weight_zero()`, `lemma_weight_mono(0, n)` (positivity), `lemma_mul_is_commutative`, `lemma_div_denominator(v, weight(n), BASE)`; `form: no-nl` | 5 |
| H6v | two `bit_vector` assertions (`p >> 64 == p / 2^64`, `p & mask == p % 2^64`), then the shift and the mask; `form: bv-exec` (the divisions live only in the proof); `// cfree: { ((p / 0x1_0000_0000_0000_0000u128) as u64, (p % 0x1_0000_0000_0000_0000u128) as u64) }` (verifies, stopped by the form) and `// cfree: { ((p >> 64u128) as u64, p as u64) }` (fails) | 2 + 1 code |
| H7v | `ensures r.wf(), r.to_nat() == x`; `lo = x as u64`, `hi = (x >> 64) as u64` with two `bit_vector` facts; push `lo` and `hi` when `hi != 0`, `lo` alone when `lo != 0`, nothing for 0; `reveal_with_fuel(seq_to_nat, 3)` and the `drop_first` facts; `form: bv-exec`; `from_u128` is an open statement in `expected/Q07.freeze` (QPLAN §6 Q44) | ≈ 18 |
| H8v | `if n == 0 { Seq::empty() } else { seq![(n % BASE) as u64] + from_nat_mirror(n / BASE) }`, `decreases n` | 4 |
| H9v | `n / BASE < BASE` (one `nonlinear_arith` with `requires`), the quotient of the quotient is 0, `reveal_with_fuel` on both spec fns, three cases with extensionality, `lemma_fundamental_div_mod` | ≈ 16 |
| X1d–X2v | see §2.8 | 5–6 / 1 + 1 code / 5 |

- **The first plan for H5v was rejected** (§0.2): `lemma_div_limb_step` falls to NL. The Dafny division-by-a-limb pair (H2d, H3d) stays: nonlinear arithmetic is off in Q07's Dafny module, so the maxauto run (on) is reported, not gating.
- **A Dafny twin of H5v (`DivPowSucc`) was dropped:** its statement is not well-formed without a divisor fact ("possible division by zero" in the `ensures`). Verus's spec division has no such check (division by zero is an unspecified value). This difference is card C7dv's material (below), not an item.
- **Why Q07 pairs only T1 (QPLAN §5.2's pairs row, §6 Q46).** Dafny's bit-vector items cannot be holes (§0.3: the pure facts verify empty, the bridge is out of resource), so H6v, H7v and X1v have no Dafny twin; the port is D→V by design §6.5; H5v's twin was dropped (above); H2d and H3d have no Verus twin because the Verus division-by-a-limb candidate falls to NL (§0.2), and H4v's Dafny twin is P1dv's tail scenario, which a Dafny module answers without a hole. The minutes follow: Dafny 25, Verus 56 (31/69 against design §6.4's 35/65 for Q07).
- **Strands.** H6v and H7v are S1 (machine words, exec overflow); H8v S2 (a spec fn, partiality); T1, H1d, H4v, H9v S4 (unfolding); H2d, H3d, H5v S5 (the library).

### 2.3 Cards: intended demos, `// after:` lines, leak constraints

- **C1d / C1v `write:fuel`**: success = a two-limb literal by hand (Dafny: the unfolding assertions; Verus: the `drop_first` facts) and then by `{:fuel ToNat, 3}` / `reveal_with_fuel(seq_to_nat, 3)`; failure = the plain empty body. Settles P1dv's literal halves: `// after: Q07.P1dv`. **Must not** be a three-limb literal (T1) or a literal followed by a tail (H4v), and must not evaluate `AddC` (H1d).
- **C2d / C2v `write:arithmetic-library`**: success = a product of two limbs below `BASE * BASE` by `LemmaMulUpperBound` / `lemma_mul_upper_bound`; failure = the same with no call (nonlinear arithmetic off in Dafny; no prover in Verus). Settles P5dv: `// after: Q07.P5dv`. Must not divide (H2d, H3d, H5v, X2v) or take a remainder by a power (X1d).
- **C3v `write:bit-vector`**: success = `x & 0xFF == x % 256` on `u64` by `bit_vector`, then the bridge to `nat` with a cast; failure = the same by `nonlinear_arith`. Settles P3v: `// after: Q07.P3v`. Must not split a double word (H6v, H7v) or join two words (X1v).
- **C4d `recognise:isolate`**: demo = P7d's three lemmas (`.expect` sidecar, sealed): `// after: Q07.P7d`.
- **C5d `recognise:bv-types`**: demo = a `bv64` mask fact that verifies empty, and P4d's `SplitWide` out of resource: `// after: Q07.P4d`.
- **C6v `recognise:recommends`**: demo = `top` with `recommends`, `r1` (P6v), a failing caller whose `--json` carries the recommendation note, and a `spec(checked)` fn giving the warning: `// after: Q07.P6v`. The demo is run with `--json` until §6 Q30 is built.
- **C7dv `diverge:q07-c7`** (S1): division and partiality across the two verifiers: Dafny's `int` division and its well-formedness check on a divisor (`possible division by zero` in a specification), Verus's spec division (Euclidean, total, unspecified at zero) against its exec division on signed integers. Settles P2dv: both demos `// after: Q07.P2dv`, sealed sidecars.
- **W1d** bounds a product of two **limbs** (`BASE`) by `LemmaMulUpperBound` with constant bounds; it must not become Q09.H1d's statement (a product below `Pow(n) * Pow(n)`).

### 2.4 The port (`port.rs`): sample, mutants, mirror

- **The sample** (the check unit's `@Test` and the learner's suite): `0`, `5`, `2^64 - 1`, `2^64 + 7`, `3 * 2^64 + 2`, `2^128 - 1`. **Never `2^64` itself** (`|FromNat(2^64)|` is Q03.P9d's answer), and no Dafny literal `ToNat([3, 1])` (Q01.P5d) or `Normalize([0, 5, 0, 0])` (Q02.P9d) anywhere in Q07's learner-visible files (§1.1 rule 4).
- **Mutants** (`MUTANTS`, commented in `port.rs`; the check unit's second test evaluates the Dafny contract on the matching Dafny outputs and **prints** `Valid` and `ToNat` for each, never `expect`s them: an `expect` would pass or fail per mutant and so fill in the `FIDELITY` table's Dafny column for the learner; revision, §R.2 #18). Expected outcomes, by the definitions (the module lane captures them):

| mutant | Verus contract (`wf`, `to_nat`) | Dafny contract (`Valid`, `ToNat`) |
|---|---|---|
| M1: always push both limbs | rejects (a high zero limb for `x < 2^64`) | accepts (`Valid` allows a high zero) |
| M2: push `hi` then `lo` | rejects (value) | rejects |
| M3: `hi` from `x >> 63` | rejects | rejects |

  M1 is the fidelity finding: the port's contract is stronger than the source's (`wf` is canonical, `FromNatCorrect` promises `Valid` only). The `FIDELITY` block's last line should say so; the mirror lemma (H9v) shows the source's *definition* meets the stronger contract, "relative to the mirror".
- **The use-site check** under H7v: `let r = from_u128(0x2_0000_0000_0000_0005u128); assert(r.wf() && r.to_nat() == 0x2_0000_0000_0000_0005);` and the same for `0` and `u128::MAX` (verifies only with an adequate `ensures`).
- **Rubric points** (the kit lane): the transcription of `Valid` versus `wf`; the sample's edge rows; the mutant table filled from runs; "relative to the mirror" stated.

### 2.5 Agent files (refactorer under harness, Qwen replay)

*Rewritten by the revision (§R.2 #5, #8, #9). The first candidate (A.7) held T1d's statement with T1d's reference proof (`ThreeLimbsBelow` unfolds `ToNat([a, b, c])` exactly as T1d's answer does) and P1dv's Dafny literal (`TwoLimbsTimesLimb` proves `ToNat([a, b]) == a + BASE * b`, also the first half of X2d's answer); its Verus plan would have held T1v's answer. It is withdrawn.*

- **Dafny** (A.15 `m2_agent_mono.dfy` is the shipped candidate, verified: §R.1 #3). Objects: compositions of L4's `Add` and `MulLimb` through `AddCorrect`, `MulLimbCorrect` and `Std.Arithmetic.Mul`'s distributivity and associativity, nonlinear arithmetic off. No literal is unfolded, no `Pow` fact is used, and no statement or step is a Q07–Q09 item's (§2.7's check). `FROZEN`: `ScaledSum(s, t, d)` (`Add(MulLimb(s, d), MulLimb(t, d))` is valid and worth `(ToNat(s) + ToNat(t)) * d`) and `ScaledSumThree(s, t, u, d)` (the same for three, added left to right). `API`: `ScaleTwice(s, d, e)` (`MulLimb(MulLimb(s, d), e)` is valid and worth `ToNat(s) * (d * e)`) and `AddScaled(a, s, d)` (`Add(a, MulLimb(s, d))` is valid and worth `ToNat(a) + ToNat(s) * d`). Each body inlines the same facts as assertions (8–14 lines). The reference refactor (`m2_agent_refactored.dfy`): one helper `AddScaledValue(a, s, d, v: int)` under `HELPERS`; every body at most 3 lines; `REFACTOR` bound 3. **Soft spots** (the first two observed in this revision's own drafts, §R.1 #3): a helper whose value parameter is `nat` (its call with `ToNat(s) * d` fails a subset constraint with nonlinear arithmetic off: the fix a contractor reaches for is often `requires`, or a weaker helper); a helper called before the fact that makes its `requires` hold; a helper stated with the value only, without validity; a helper with a `requires` that some caller cannot meet (for example `d > 0`); a `{:fuel}` attribute; and **an `API` statement weakened to fit a helper**, which every machine-checked line accepts (`m2_agent_weak_api.dfy` drops `ScaleTwice`'s validity conjunct: gate, audit and freeze all pass, §R.1 #3). That last one is `REVIEW`'s designed catch.
- **Verus** (A.15 `m2_agent_mono.rs`, verified): exec fns over `big_add` and `mul_limb`, proved with `vstd::arithmetic::mul`'s `lemma_mul_is_distributive_add_other_way` and `lemma_mul_is_associative` (Verus does not prove distributivity unaided, P5dv). `FROZEN`: `scaled_sum(a, b, x)`, `scaled_sum_three(a, b, c, x)`; `API`: `scale_twice(a, x, y)` (`a * (x * y)`), `add_scaled(a, b, x)`. Reference refactor (`m2_agent_refactored.rs`): `lemma_sum_scaled(u, v, x)` under `HELPERS`, `scaled_sum` and `scaled_sum_three` through `add_scaled`. A weakened `scale_twice` (`>=`) passes the freeze; a weakened `scaled_sum` does not (§R.1 #3). The module lane may rename the fns away from `scale…` (Q08.H4v is `scale`); the names here are the probe's.
- **The snapshot and the starting state.** `research/q07_frozen.dfy` (`.rs`) holds the module header, its imports and the `FROZEN` section only. The learner commits it with the agent files still as shipped; that commit is the starting state of both runs (`contract_local.sh` stages `git show <rev>:<agent file>`, DV4 §6 step 3). The freeze check therefore pins `FROZEN` and nothing else; `API` is what callers rely on and no acceptance line pins.
- **The CONTRACT's lines**, in DV4 §6's checked forms (QPLAN §15.4): the gate, zero holes, `specfreeze --against research/q07_frozen.dfy`, `vaudit <file>` reports no finding (no `.audit` pin: a delivered file has no attribute and no assumption, so an empty report is the same check), and two audit lines (the `git diff` from the snapshot's commit touches no `FROZEN` statement and puts new lemmas under `HELPERS`; no `{:fuel}` attribute added). Resource attributes are `vaudit` findings already.
- **The Qwen replay** (A2d) runs on the Dafny file only (`qwen_runs = 1`), pending until DV4 step 3b. Expect a smaller patch or none; an empty patch is a result (the run record says so), not a failure of the exercise.

### 2.6 Exit answers

§2.8's statements; references in Appendix A.6 (verified). **Unseen check:** X1d (a remainder of a product by a power) shares the arithmetic library with H2d and H3d on another operation; X2d (a quotient of a two-limb literal) shares unfolding with T1d and H1d on another shape (a division after the unfolding); X1v (joining two words) is the inverse of H6v (splitting); X2v (a quotient of weights) shares H5v's library on another statement.

### 2.7 Leak checks (Q07)

- No Q07 learner-visible text names `LemmaMultiplyDivideLt`, `LemmaMulInequality`, `lemma_div_denominator`, `lemma_fundamental_div_mod`, `lemma_div_multiples_vanish` or a `reveal_with_fuel` count in a hole's block (the cards name `reveal_with_fuel` and `{:fuel}` as constructs, never with an item's count).
- L4's `MulLimbDigit` proof (`LemmaMulUpperBound(x, BASE - 1, d, BASE - 1)`) is C2's success idiom; no Q07 hole's answer is that call (H2d/H3d divide; H5v divides by weights).
- P1dv's scenarios are quoted, commented, in the prediction block; H4v's statement equals P1dv's Verus tail scenario by design (the prediction asks the empty body's verdict, the hole asks a proof); the prediction block precedes it.
- **Agent files and twins (revision, §R.2 #5).** Every T, H and X statement of Q07–Q09 and every reference line of §2.2, §3.2, §4.2 and the exits was checked against the new Q07 agent candidates and their refactored twins (A.15), the Q08 flagship twins and the Q09 bank twins: no statement and no reference line occurs, and no agent file unfolds a literal `ToNat`/`seq_to_nat` (Q07's T1, H4v, X2d, P1dv) or uses `Pow`/`weight` facts (Q07.X1d, X2v; Q09's T1, X1). The Q09 Verus bank's `lemma_two_limbs_value` states P1dv's Verus literal as a hole (no proof ships; the contractor's proof arrives in Q09, after Q07); kept. The Q08 flagship twin holds an append lemma (Q04.X1d's statement, a lower tier), in the twin only (§3.4). The module lanes re-run this check on their files as built (QPLAN §14.7 F15).

### 2.8 Exit statements and prompts (Δ133; QPLAN names each exit item only)

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q07.X1d | S5 | arithmetic-library | `lemma ProductOfPowSuccModBase(x: nat, k: nat)`; `ensures (x * Pow(k + 1)) % BASE == 0` | prove it with the standard library (nonlinear arithmetic is off in the exit module) | statement-shipped, bodyless lemma · nonlinear arithmetic off |
| Q07.X2d | S4 | fuel | `lemma DivBaseOfTwoLimbs(a: nat, b: nat)`; `requires a < BASE`; `ensures ToNat([a, b]) / BASE == b` | prove it | statement-shipped, bodyless lemma · nonlinear arithmetic off |
| Q07.X1v | S1 | bit-vector | `pub fn join_word(hi: u64, lo: u64) -> (r: u128)`; `ensures r as nat == hi as nat * BASE + lo as nat` | implement it with a shift and an `or`, with no `*`, `/` or `%` in the code | statement-shipped, `external_body` hole, `// form: bv-exec` · none |
| Q07.X2v | S5 | arithmetic-library | `pub proof fn lemma_weight_quotient(k: nat, n: nat)`; `requires k <= n`; `ensures weight(n) / weight(k) == weight((n - k) as nat)` | prove it with `vstd::arithmetic` lemmas and L3–L4's weight lemmas (no `nonlinear_arith`) | statement-shipped, `proof_note` assume, `// form: no-nl` · the opacity of `weight` |

The module lane gates each (X1v with `// triv: { 0u128 }`, and `// cfree: { (hi as u128) * 0x1_0000_0000_0000_0000u128 + (lo as u128) }`, which verifies and is stopped by the form, §R.1 #6).

## 3. Q08

### 3.1 Prediction answers

| item | answer | evidence (`vcheck --module Q07 --json` unless stated) |
|---|---|---|
| P1dv | `D:ok err:resolve V:ok err:resolve` | `refadd_d.dfy` verifies; `refreq_d.dfy`: `failed`, stage `resolve`, `a refining method is not allowed to add preconditions`; `timpl_a_v.rs` verifies; `timpl_b_v.rs`: `failed`, stage `resolve`, `trait method implementation cannot declare requires clauses; these can only be inherited from the trait declaration` |
| P2v | `V:err:resolve ok` | `lin_v.rs`: `failed`, stage `resolve`, ``use of moved value: `perm` ``; `lin_ghost_v.rs` verifies |
| P3d | `D:err:resolve` | `p3d_d.dfy`: `failed`, stage `resolve`, `decreases clause on refining method not supported, unless the refined method was specified with 'decreases *'` |
| P4dv | `D:ok V:err:resolve` | `term_d.dfy` verifies (Dafny infers the datatype measure); `term_v.rs`: `failed`, stage `resolve`, `recursive function must have a decreases clause` |
| P5dv | `b` (`x >= 0`), the block's options a) `x > 0` b) `x >= 0` c) `true` d) `x > -2` | by hand: `wp = (x + 1 > 0 ==> x + 1 > 0) && (x + 1 <= 0 ==> 0 > 0)`, i.e. `x + 1 > 0`; `wp_hand_d.dfy` verifies the equivalence with `x >= 0` against a direct semantics. Option d is the off-by-one |
| P6v | `V:ok fail` | `impl_client2_v.rs`: the concrete caller verifies (the implementation's extra `ensures`), the generic one fails (`postcondition not satisfied`) |

### 3.2 Holes, test-out items and the gated items

References: Appendix A.3 (`Q08Canon`, `Q08CanonRaw`, `Q08Words`), A.4 (Verus), A.8 (wp).

| item | reference | lines |
|---|---|---|
| T1d | compute `s: int := x as int + y as int + c as int`, then two cases with `as u64` | 6 |
| T1v | `ensures final(self).on() == !old(self).on()` on `flip` (and delete the assume); `Toggle::flip` is an open statement in `expected/Q08.freeze` (QPLAN §6 Q44: without it `specfreeze --check` reports this correct answer, §R.1 #5) | 1 |
| H1d | `L4.AddCorrect(a, b)`, `L3.NormalizeToNat(L4.Add(a, b))`, `L3.NormalizeCanonical(L4.Add(a, b))` | 3 |
| H2d | a helper `FromNatCanonical(n)` (recursion on `n / BASE`, with `L3.FromNatCorrect` at both levels; `decreases n`), then two calls. The refining lemma cannot carry a `decreases` of its own (P3d); on the pins it may still recurse under the inherited default measure (the Q08 kit lane's probe, Δ171) | 9 |
| H7d | a helper `AddCCanonical(a, b, c)` (`{:induction false}`, `reveal L4.AddC()`, `L4.AddCCorrect` at both levels, recursion on the tails when either is non-empty), then two calls | 13 |
| H3v | `advance`: `requires old(self).ok(), ensures final(self).ok(), final(self).reading() == old(self).reading() + by`; `current`: `requires self.ok(), ensures r.wf(), r.to_nat() == self.reading()`; both open statements (QPLAN §6 Q44) | 6 |
| H4v | a `while` loop over `i < k` with `acc.plus(v)`, invariant `acc.value() == v.value() * i`, and `lemma_mul_is_distributive_add(v.value(), i, 1)` each step | 14 |
| H5v | `let v = cell.read(Tracked(&*perm)); cell.write(Tracked(perm), v + 1);` | 2 |
| H6v | read both, write `src` 0 and `dst` the sum | 4 |
| H8d | structural recursion on `t`; `UpdateApply` in the `Var` case | 6 |
| H9d | structural recursion on `c`; `SubstBOk` in the assignment case; in the `if` case, `assert Holds(Not(b), s);` before the recursive call on the else branch | 10 |
| H10d | `var post := Le(Var(1), Var(0)); assert Holds(Wp(Swap(), post), s); WpSound(Swap(), post, s);` | 3 |

- **The verified wp, design notes.** A first version with predicates as functions (`Pred = State -> bool`, `Wp` building lambdas; `wp_d.dfy`) left a failing obligation in each of four runs (`29 verified, 2 errors` … `30 verified, 1 error`) and was abandoned. The syntactic version (assertion language, substitution, `Wp` returning an assertion; `wp2_d.dfy`) verifies. Its `If` case encodes `(b ==> Wp1) && (!b ==> Wp2)` with an `Imp` constructor.
- **The gated items** (H5v, H6v): references verified; TRIV fails on seeds 1–3 (§0.2). The module lane adds the seeds 1–3 runs on the twins and checks the cell API names against the pinned `vstd` source (`PCell::new`, `read`, `write`, `PointsTo::id`). Fallbacks if they fail: QPLAN §16.3.
- **Why `Q08_Canon.CmpCorrect` and `Q08_CanonRaw.CmpCorrect` ship proved:** their answer is one call, `L4.CmpCorrect(a, b)`, the same as `QG_L4_Limbs.CmpCorrect`'s body in L4. Posing it would put a Q08 hole's whole answer in L4. The plan's first H7d was that lemma; it was replaced by `Q08_CanonRaw.AddCorrect`.
- **`Q08_CanonRaw.FromNat` normalizes** so that its `FromNatCorrect` ships proved by three public calls (`L3.FromNatCorrect`, `NormalizeToNat`, `NormalizeCanonical`) and holds no part of H2d's answer (the canonical `FromNat` induction).
- **The refinement holes' form (revision, §R.2 #1).** H1d, H2d and H7d (and X1d) ship as `lemma … { assume false; }` in their refining module, the inherited statement quoted in the block's comment, never bodyless: §R.1 #1 shows the hole counted at the learner's line once per refiner, the lint clean, the exit scorer and the empty-body gate working, with the tools as built. A learner who adds an `ensures` to a refined lemma changes its pinned statement (`specfreeze --check` reports it); the inherited statement binds either way.
- **H5v and its neighbours.** H5v's answer is two lines, and W3v shows a read and a write on an owned permission; the item's lesson is the borrow forms through a `&mut` permission (`Tracked(&*perm)` to read, `Tracked(perm)` to write). C3v's demo now only reads (§3.3), so the write through `&mut` stays H5v's. Gated, 6 minutes.

### 3.3 Cards

- **C1d `write:refines`** (revised, §R.2 #17): success = `module CardNat refines QG_L4_Spec` with the trivial model `BigNat = nat`, `Val(x) = x`, `Wf(x) = true`, `Zero() = 0`, `FromNat(n) = n`, `Add(a, b) = a + b`, `Cmp` by comparison, every inherited lemma proved by an empty body, and one helper lemma added (for example `AddZero`); failure = a definition that breaks an inherited statement (`Add(a, b) = a + b + 1`: `AddCorrect` fails). No abstract module in the specimen (the learner-mode lint flags one, Δ3), no `seq<nat>` representation (H1d, H2d, H7d, X1d), no change of representation beyond the trivial one (X1d).
- **C2v `write:trait-spec`**: success = a trait with `requires`/`ensures`, an implementation and a generic client; failure = the client relying on an implementation-only `ensures` (P6v's shape): `// after: Q08.P6v`. Must not fold a sequence through a trait (X1v).
- **C3v `write:tracked`** (revised, §R.2 #17): success = a read-only helper `peek(cell: &PCell<u64>, Tracked(perm): Tracked<&PointsTo<u64>>) -> (r: u64)` (`requires cell.id() == perm.id(), perm.is_init()`, `ensures r == perm.value()`), called from a fn that holds the permission as `Tracked<&mut PointsTo<u64>>` by lending it with `Tracked(&*perm)`, plus a ghost `assert(perm.id() == cell.id())`; failure = `peek` called with another cell's permission (`id` mismatch). Must not write through a `&mut` permission (H5v), move a value between two cells (H6v), or add to a cell (the first candidate added two: H5v's answer with 2 for 1).
- **C4dv `diverge:q08-c4`** (S6): what a refinement and a trait implementation may add (an `ensures` yes, a `requires` no, a refining lemma's own `decreases` no). Settles P1dv and P3d: `// after: Q08.P1dv`, `// after: Q08.P3d`, sealed. The Dafny demo refines `QG_L4_Spec` with C1d's trivial model (revision): the three cases on its inherited lemmas, no abstract module of its own.
- **C5dv `diverge:q08-c5`** (S7): termination of recursive definitions over datatypes in the two verifiers. Settles P4dv: `// after: Q08.P4dv`, sealed. Must not show a lexicographic measure for a lemma (X2d).

### 3.4 The flagship (agent files)

*Rewritten by the revision (§R.2 #10): the Dafny statements are bodyless methods, not bodyless functions, because `specfreeze --against` counts a function's body as part of its statement (§R.1 #4).*

- **Reference statements** (the agent twins; A.15 `m7_flag_statements.dfy`, A.9 for Verus): Dafny `method ShiftLimbs(a: seq<nat>, k: nat) returns (r: seq<nat>) requires Valid(a) ensures Valid(r) && ToNat(r) == ToNat(a) * Pow(k)` and `method SplitLimbs(a: seq<nat>, k: nat) returns (lo: seq<nat>, hi: seq<nat>) requires Valid(a) ensures Valid(lo) && Valid(hi) && ToNat(a) == ToNat(lo) + Pow(k) * ToNat(hi) && ToNat(lo) < Pow(k)`, each with one `ensures` clause; a `Witnesses()` method with concrete calls. Verus `pub fn shift_limbs(a: &BigNat, k: usize) -> (r: BigNat) requires a.wf(), ensures r.wf(), r.to_nat() == a.to_nat() * weight(k as nat)` and `pub fn high_limbs(a: &BigNat, k: usize) -> (r: BigNat) requires a.wf(), ensures r.wf(), r.to_nat() == a.to_nat() / weight(k as nat)`, as `external_body` stubs, and a `witnesses()` fn.
- **Statement pitfalls the learner meets** (the rubric's and the audit's points): a Dafny `ensures … == ToNat(a) / Pow(k)` is not well-formed without a divisor fact (`possible division by zero`; the multiplicative form avoids it); two `ensures` clauses on one bodyless method (the hole rule wants one, Δ5: `multi-ensures-hole` until the body arrives); a bodyless *function* (its delivery is a freeze change, QPLAN §6 Q45); a Verus low split would need normalization, so the Verus `STATEMENTS` comment names only the shift and the high split; forgetting `wf`/`Valid` in an `ensures`; forgetting the empty input (a shift of zero must stay empty in Verus, or `wf` fails).
- **The reference delivery** (verified, §R.1 #4): Dafny method bodies `r := Zeros(k) + a;` and the split by slices, with `Zeros(k)` and its facts, an append lemma by library calls, `ToNatBound` (L2), `PowIsStdPow` (L3), `LemmaPowStrictlyIncreases` under `HELPERS`; Verus `zeros(k)` by `push`, `lemma_seq_to_nat_push_zero` (L1), L4's `lemma_seq_to_nat_append`, `group_bignat_bounds`, `lemma_fundamental_div_mod_converse`, `lemma_basic_div_specific_divisor`. **A.9's Verus `high_limbs` as recorded fails at the agent path on seeds 1–3**; the repaired proof (A.15) states `lo.len() == k`, calls `lemma_mul_is_commutative(weight(k), seq_to_nat(hi))` and asserts the division equation before the converse lemma. It is stable on seeds 1–3 but costs up to 4,852,723 of the 6,000,000 rlimit on one seed (CV 81.7%): the Q08 lane splits that proof further before pinning the twin. The Dafny append lemma states Q04.X1d's statement (an exit of a lower tier): it lives only in the agent twin (`Solutions/`) and, after a run, in the learner's own agent file.
- **Acceptance re-run** on the twins in this form (§R.1 #4): `vcheck --gate` 0 holes, `specfreeze --against research/q08_statements.{dfy,rs}` no finding, `vaudit` no finding, witnesses unchanged and verifying. No `.audit` pin.
- **Soft spots:** a contractor adds a `requires` to a helper that a `STATEMENTS` method cannot discharge and then weakens the statement to match (the freeze check catches it); proves the high split by `Normalize`; adds `{:fuel}` or `#[verifier::rlimit]` attributes (the audit catches the second); turns a method into a function to reuse it in a specification (a freeze change).

### 3.5 The verified wp (W2d)

W2d's given code is A.8 without the bodies of `SubstEOk`, `WpSound` and `SwapOrders` (and without the two comparison lemmas). `SubstBOk` ships proved and calls `SubstEOk` (a hole).

### 3.6 Exit answers

| item | reference (A.6b, verified) |
|---|---|
| X1d | `RevRev(L4.Add(Rev(a), Rev(b))); L4.AddCorrect(Rev(a), Rev(b));` (2 lines; the call alone fails) |
| X2d | `decreases Size(c), LeftSize(c)`; `match c`; in the `Seq(Seq(a, b), d)` case `RotateSmaller(a, b, d); FlatSame(Seq(a, Seq(b, d)), s);`, in the other `Seq` case `FlatSame(d, Exec(c1, s));` (≈ 8 lines; without the `decreases` clause: `cannot prove termination`) |
| X1v | a loop with `acc = acc.plus(&T::from_word(xs[i]))`, invariant `acc.value() == words_sum(xs@.subrange(0, i as int))`, the `drop_last` extensionality fact each step and `subrange(0, len) =~= xs@` after (≈ 12 lines) |
| X2v | `let ghost old_log = self.log@; self.log = Ghost(old_log.push(x)); self.total = self.total + x;` and `assert(old_log.push(x).drop_last() =~= old_log)` (4 lines) |

### 3.7 Exit statements and prompts (Δ133)

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q08.X1d | S6 | refines | `module Q08_ExitRev refines QG_L4_Spec`, storing limbs most significant first: given `Rev` with `RevAppend` and `RevRev` (proved), and `FromNatMsf(n)` (the limbs of `n`, most significant first, by recursion on `n / BASE`) with `FromNatMsfRev(n)` (`Rev(FromNatMsf(n)) == L2.FromNat(n)`, proved by induction with `RevAppend`); `BigNat = seq<nat>`, `Val(x) = L1.ToNat(Rev(x))`, `Wf(x) = L1.Valid(Rev(x))`, `Zero() = []`, `FromNat(n) = FromNatMsf(n)`, `Add(a, b) = Rev(L4.Add(Rev(a), Rev(b)))`, `Cmp(a, b) = L3.Cmp(Rev(a), Rev(b))`; `ZeroCorrect`, `FromNatCorrect` (`FromNatMsfRev(n); L3.FromNatCorrect(n);`), `CmpCorrect` (`L4.CmpCorrect(Rev(a), Rev(b));`) ship proved; `lemma AddCorrect(a: BigNat, b: BigNat)`, its inherited statement quoted in the block | prove the inherited statement | statement-shipped (inherited), refined lemma with the body `{ assume false; }` · nonlinear arithmetic off |
| Q08.X2d | S7 | — | given: `Cmd = Skip \| Assign(x, e) \| Seq(c1, c2)`, `Exec`, `Size`, `LeftSize`, `RotateSmaller(a, b, d)` (proved: the rotation keeps `Size` and shrinks `LeftSize`), and `Flat(c)` (right-associates sequences; `decreases Size(c), LeftSize(c)`); `lemma FlatSame(c: Cmd, s: State)`; `ensures Exec(Flat(c), s) == Exec(c, s)` | prove it (the lemma ships with no `decreases` clause) | statement-shipped, bodyless lemma · the unit's manual lemma induction |
| Q08.X1v | S6 | trait-spec | `pub open spec fn words_sum(s: Seq<u64>) -> nat` (by `drop_last`, given); `pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)`; `ensures r.valid(), r.value() == words_sum(xs@)` | implement it through the trait only | statement-shipped, `external_body` hole · none |
| Q08.X2v | S7 | — | `pub struct Ledger { pub total: u64, pub log: Ghost<Seq<u64>> }` with `pub open spec fn inv(&self) -> bool { self.total == words_sum(self.log@) }` (given); `pub fn record(&mut self, x: u64)`; `requires old(self).inv(), old(self).total + x <= u64::MAX`; `ensures final(self).inv(), final(self).log@ == old(self).log@.push(x)` | implement it | statement-shipped, `external_body` hole · none |

**Unseen check:** X1d refines with a change of representation (no hole of Q08 does; its answer is not in L4, which has no `Rev`); X2d is a lexicographic termination measure for a lemma over a command language (H8d–H10d recurse structurally on another language, P3d is about a refining lemma); X1v is a generic client like H4v but folds a sequence, not a repetition; X2v is ghost state, which no Q08 hole poses. **Revision (§R.2 #12):** the first scaffold proved `FromNatCorrect` by `RevRev(L2.FromNat(n)); L3.FromNatCorrect(n);`, which is X1d's answer pattern (`RevRev` on the inner sequence, then the layer lemma); the review rejected it. The new scaffold defines `FromNat` most significant first and proves `FromNatCorrect` through the given `FromNatMsfRev`, whose induction uses `RevAppend`, so no shipped line applies `RevRev` (verified, §R.1 #1: 135 verified as shipped; both blocks `pass` with the reference; the single `L4.AddCorrect` call fails). `FromNatMsfRev`'s recursion on `n / BASE` shares a technique with H2d's helper; the exit is taken after H2d. If the gated items fall back (§16.3), F-H5v is also a ghost history: then X2v changes to a ghost maximum (`log` and `inv` over a `max` spec fn) and this row is updated.

## 4. Q09

### 4.1 Prediction answers

| item | answer | evidence |
|---|---|---|
| P1d | `D:timeout ok` | `h1_nl_d.dfy` through `drv/res2.py`: 4.12.1 `Failed` at 5,006,650 (out of resource), 4.14.1 `Passed` at 38,790. Re-capture with the course option of §6 Q29 once built; until then the Q09 lane captures it the same way as here. The block now states the vocabulary (v as in Q01.P1dv, `timeout` for an inconclusive or out-of-resource run; revision §R.2 #6), so `D:timeout ok` is the only spelling that matches |
| P2dv | `D:timeout,timeout,timeout,unstable V:timeout,timeout,timeout,unstable` | `t1att_d.dfy` (nonlinear off, as `Q09_Triggers.dfy`) and `t1att_v.rs` under `vcheck --module Q07 --brittleness`: `seed 1: inconclusive · seed 2: inconclusive · seed 3: inconclusive — NOT stable` in each language (`inconclusive` is the out-of-resource verdict, `timeout` in the answer vocabulary, which the block now states). **The Dafny half holds only in the nonlinear-off file**: with nonlinear on the attempt is `stable` (§0.3). **Revision (§R.2 #6):** both attempts are quoted in P2dv's own block, in the main Dafny file's prediction block; the T1 blocks quote nothing and say nothing about a verdict, and `Q09_Triggers.dfy`'s header asks for the predictions to be committed before the file is opened |
| P3dv | `D:verified number V:verified null` | `hj_d.dfy`: `verdict` `verified`, `verified_count` 23, the hole listed in `holes`; `hj_v.rs`: `verdict` `verified`, `verified_count` null, the `proof_note` assume listed in `holes` |
| P4py | `c` | `mde_two_proportions(60, 0.5)` = 0.245 (`paired=True` 0.251, also `c`). The revised scenario fixes n as 60 tasks per arm and names the call; read as 30 per arm it gave 0.334 (the review), now excluded |
| P5py | `c` | `wilson_interval(0, 9)` upper 0.299 |

### 4.2 Test-out and repair references

| item | reference | lines |
|---|---|---|
| T1d | the quantified step with `{:trigger Pow(k + 1)}` and the body `assert Pow(k + 1) == BASE * Pow(k);`, the recursion, and `PowAdd(m + 1, 0)` (A.10); `form: trigger, stable` | 6 |
| T1v | `#[trigger] weight(k + 1)` on the same step (`trig_v.rs`'s `mono_rewrite`); `form: trigger, stable` | 1 changed |
| H1d | `LemmaMulLeftInequality(p, y, p)`; if `x == 0`, `LemmaMulBasics(y)` and `LemmaMulStrictlyPositive(p, p)`; else `LemmaMulLeftInequality(x, y, p)` and `LemmaMulStrictInequality(x, p, p)` (`h1_d.dfy`); `form: stable` | 7 |
| H1v | `let p = weight(n); assert(x * y <= x * p) by (nonlinear_arith) requires y < p; assert(x * p < p * p) by (nonlinear_arith) requires x < p;` (`h1v_v.rs`); `form: nl-steps:2, stable`; `// cfree:` the one scoped step (verifies, stopped by the form) | 3 |

- **H1v's quoted attempt** (`h1v_v.rs`): `assert(x * y < p * p) by (nonlinear_arith);` with no `requires`: `failed` on seeds 1–3. The twin's `BRITTLENESS` table: `failed` ×3 for the attempt, `verified` ×3 for the repair.
- **H1d's quoted attempt** is P1d's scenario; the twin's table: 4.12.1 `timeout`, 4.14.1 `verified` (unseeded runs here; the module lane fills the seeded cells once §6 Q29's option exists). The prompt asks for the table "from your runs of the attempt, whatever they show" (revision: the old wording implied the attempt fails somewhere, which bears on P1d).
- **T1's prompts (revision).** "Prove it with a quantified step whose trigger you choose and write explicitly; the proof must be stable under `scripts/vcheck --brittleness` and carry no resource attribute." The `trigger` form checks only that an explicit trigger is present (plain induction verifies, §0.2): the citation is `# nominal:` in QPLAN §17.11, and the rubric checks that the quantified step carries the proof.
- **No statement overlap:** T1d is not Q04.X2d (`PowsBelow`): T1d bounds `Pow(m) * BASE <= Pow(n)`. H1d is not Q06.H3d (`x * y < Pow(2 * n)`).

### 4.3 Cards

- **C1d / C1v `write:proof-split`**: success = a three-factor product bound with factors below `BASE`, split into named steps and measured before and after; failure = the one-step version (Dafny: under the pinned solver; Verus: one `nonlinear_arith` without `requires`). Settles P1d's subject in general terms: `// after: Q09.P1d`. Must not be a two-factor bound below a square (H1), a product plus a further term (X1, revised) or a bound below a power.
- **C2d / C2v `write:trigger-rewrite`**: success = a quantified fact over `MulLimb` lengths (or another non-power function) with the trigger moved; failure = the looping trigger, measured. `// after: Q09.P2dv`. Must not use `Pow`, `weight` or an opaque stand-in for them (T1), and must not show a multi-pattern (a trigger of two or more terms) being replaced, or state a fact about concatenations or sums of limbs (X2, revised). **The Dafny demo's failure must be measured in the specimen's own options**: a loop that fails with nonlinear arithmetic off may verify with it on (§0.3).

### 4.4 The forensic deliveries (P6d–P15v)

Each a specimen with one green delivery; the families come from the Q half of the corpus (recorded manifests: Dafny 28 fixtures, of which 5 controls, 18 constructs, 5 covered elsewhere; Verus 25, of which 4 controls, 16 constructs, 5 covered elsewhere), applied to BigNat objects. One feasible assignment of eight different instruments to the eight non-healthy deliveries (spec §11.4's list); the learner may use others, and the rubric accepts any instrument that catches a delivery provided the eight are different:

| item | delivery (claimed statement) | species | planted line | instrument | corpus family (recorded catch) |
|---|---|---|---|---|---|
| P6d | `lemma MulLimbLengthBound(s, d)`: `\|MulLimb(s, d)\| <= \|s\| + 1`, through a helper holding `assume {:axiom} …` | `trusted` | the axiom assumption | the audit (`vaudit`'s audit row) | G01, X01 (`vaudit` flagged) |
| P7d | `lemma AddCommutes(a, b)`: `Add(a, b) == Add(b, a)` for valid `a`, `b`, whose helper carries `{:verify false}` | `unchecked` | the attribute | the lint (the attribute rule) | G05, X10 (`vcheck --gate`, `vaudit` flagged) |
| P8d | `lemma CarryIsLimb(x, d, c)`, `requires x < BASE && d < BASE && c < BASE && x + d >= 2 * BASE` | `vacuous` | the contradictory conjunct | swap the conclusion for `false` | D-17, X07 (`witness`, `swap-to-false` flagged) |
| P9d | `lemma AddValue(a, b)` delivered with `ensures ToNat(Add(a, b)) >= ToNat(a)` against the frozen `== ToNat(a) + ToNat(b)` (companion `P9d-frozen.dfy.specimen`) | `weak` | the weakened `ensures` | `scripts/specfreeze --against` | G13, X06 (`specfreeze --check` flagged) |
| P10d | `lemma AppendEmpty(a)`: `ToNat(a + []) == ToNat(a)`, proved honestly | `healthy` | a `// planted:` line on an ordinary step, so markers carry no species signal (Δ120) | every instrument passes | control |
| P11v | `fn top_limb(a: &BigNat) -> (r: u64)` (`requires a.wf(), a.limbs@.len() > 0`, `ensures r == a.limbs@.last()`) through an `#[verifier::external_body]` helper whose code returns the first limb; the delivery's tests use one-limb numbers | `trusted` | `external_body` | running compiled code on inputs the tests avoided (a two-limb number, `vcheck --test`) | V05, X11 (a trusted spec its code does not meet; `vcheck --gate`, `vaudit` flagged) |
| P12v | `fn add_three(a, b, c)`: the sum of three canonical numbers, its helper written outside `verus!` | `unchecked` | the helper outside the macro | JSON completeness (`verified_count` below the item's floor; the symbol absent) | V09, X05 (`json-completeness` flagged) |
| P13v | `proof fn lemma_top_limb(s)`, `requires s.len() > 0, s.len() == 0` | `vacuous` | the second `requires` | a satisfiability witness (a caller cannot meet the `requires`) | V12, X07 (`witness`, `swap-to-false` flagged; `vcheck --gate` `unknown`) |
| P14v | `proof fn lemma_value_of_top(s)` whose `ensures` reads past the end of a sequence for some inputs (a partial spec: the statement says less than its comment claims) | `weak` | the partial `ensures` | a property sampler on concrete sequences, after reading the statement | V14, X08 (`vcheck --gate` `unknown`, `vaudit` clean: held only by the `unknown` rule) |
| P15v | `proof fn lemma_two_limbs(a, b)` (two-limb value), proved honestly | `healthy` | as P10d | every instrument passes | control |

- **Order and H5.** `vcheck`/`vaudit` refuse a specimen whose slot has no recorded first try (H5): the learner reads, records the species, then runs instruments.
- **No false accusation:** P10d and P15v are healthy; a `DIAGNOSIS` row that accuses them is a rubric failure (E4).
- **Leak constraint:** no delivery is a copy of a corpus fixture; no delivery proves a Q07–Q09 hole's statement (P9d's frozen statement is L4's `AddCorrect`, which is given).

### 4.5 The red-team bank (agent files)

- **Dafny** (A.11, verified): `AddLengthBound(a, b)` (true; a helper over `AddC` with `reveal`), `MulLimbByZero(s)` (true), `CmpAntisymmetric(a, b)` (true; two `CmpCorrect` calls), and the **planted false lemma** `CmpZeroMeansEqual(a, b) requires Valid(a) && Valid(b) ensures Cmp(a, b) == 0 ==> a == b` (false: `[1, 0]` and `[1]`). Refutation: `lemma {:fuel Cmp, 4} CmpZeroMeansEqualRefuted() ensures Valid([1, 0]) && Valid([1]) && Cmp([1, 0], [1]) == 0 && [1, 0] != [1] {}` (verified).
- **Verus** (verified): `lemma_canonical_value_positive(s)` (true), `lemma_two_limbs_value(a, b)` (true; fuel and extensionality), `lemma_sum_le_add(a, b)` (true; L4's append lemma), and the **planted false lemma** `lemma_equal_values_equal_limbs(a, b) requires seq_to_nat(a) == seq_to_nat(b) ensures a =~= b` (false without `seq_wf`). Refutation: `refute_equal_values_equal_limbs()` (verified).
- **Soft spots:** adding `requires Canonical(a) && Canonical(b)` (or `seq_wf`) "to make it provable" (the freeze check catches it, and contract v1 should forbid it); `assume`-ing the false lemma (the audit catches it); reporting it false with prose only (no refutation: the acceptance fails); proving a true lemma by calling the false one.
- **`vaudit` and `{:fuel}`:** the Dafny refutation's attribute passes the lint (`0 finding(s)` in learner and agent mode, §0.1).
- **Options (revision, §R.2 #18).** The Dafny bank module is `{:disableNonlinearArithmetic} Q09_AgentRedTeam`, the options A.11 and §R.1 #2 verified it under.
- **The acceptance on a correct delivery (revision, §R.2 #2).** A correct delivery leaves the false lemma as shipped, so it carries one hole and one audit finding. The old line "`vaudit --compare` an empty pin" therefore failed every correct delivery (the plan lane's bank probe had left the false lemma out), pushed the contractor toward proving, assuming or weakening it, and an `.audit` pin holding the one finding would have named the false lemma in `expected/`. The line is now: `scripts/vaudit <file>` reports exactly one finding per lemma the report names as false, a hole kind (Dafny `audit-bodyless-ghost` on the declaration line, Verus `hole-assume` on the labelled assume line), and no other finding. Every acceptance line was run on both twins with the false lemma left as shipped (§R.1 #2): one hole each, one finding each, freeze clean. The learner's default `vaudit` mode is the one the line means: `--mode agent` adds a `bodyless` lint row on the same Dafny line (two findings), which the CONTRACT does not use.

### 4.6 The gate core (reference sketch, for the Q09 lane)

*Rewritten by the revision (§R.2 #7): the first sketch's `classify(results, xclass)` read the fixture's ground-truth class, so its UNKNOWN came from the label, the frozen test "grader-only constructs get UNKNOWN" passed trivially, and the gate could not run on a real delivery, where no class is known.*

`Solutions/harness/q/fvh_q/gate/core.py` (the twin). Given above the holes (frozen by `expected/Q09.freeze`): `@dataclass(frozen=True) GateVerdict(word: str, unknown: tuple[str, ...])`, `GateResult(id: str, verdict: GateVerdict, results: Mapping[str, ToolResult])`, `Report(detected: Mapping[str, int], held_by_unknown: int, false_pass: int, fp: int, controls: int, fp_interval: tuple[float, float])`, and `render(v: GateVerdict) -> str` (`"FAIL"`, or `"PASS · UNKNOWN: X07, X08, X14"`; never a bare `PASS` while `unknown` is non-empty).

- `json_complete(doc, lang)`: `verdict`, `holes` (a list), `verified_count` (an `int`, not `None`; Dafny only, Verus reports `null` by design, P3dv), `stage == "verify"`, `exit_code` consistent with `verdict`, `lang`.
- `classify(results)`: `FAIL` on any killed result, any incomplete gate document (`json_complete`), any hole, any audit finding, a freeze change, a witness failure (exit 1) or a swap success (exit 0); otherwise `GateVerdict(PASS, unknown)` with `unknown = GRADER_ONLY` minus the classes a passing oracle result decides: a passing `witness` result removes X07, a passing `specfreeze --check` result (a task-supplied frozen statement) removes X08; nothing removes X14 (lookup-table overfitting needs hidden tests). It never sees a label.
- `gate(delivery, *, run=None)`: the instruments from the delivery's language and files (always `vcheck --gate` and `vaudit`; `specfreeze --check` when a frozen companion exists, `witness` when a witness caller exists, `swap-to-false` when a swapped copy exists), each through `run or tools.run` looked up at call time; a kill or time-out is `FAIL`.
- `corpus_report(results, labels)`: the evaluator. A construct of a decidable class is detected iff `word == FAIL`; a grader-only construct is held iff `word == FAIL` or its class is in `unknown` (counted as `held_by_unknown`); one with `word == PASS` and its class not in `unknown` is a `false_pass` (must be 0); a control is a false positive iff `word == FAIL`; `fp_interval = fvh.stats.wilson_interval(fp, controls)`.
- `# triv:` bodies: `return []`, `return GateVerdict("PASS", ())`, `return GateResult(delivery.id, GateVerdict("PASS", ()), {})`, `return Report({}, 0, 0, 0, 0, (0.0, 1.0))`. The acceptance tests must fail on each (the Python TRIV gate, Δ136).
- **The frozen tests' label-independence checks** (QPLAN §17.7): `classify` takes no label argument; V14 (X08, held only by `unknown`) and a healthy Verus control with the same instrument set give equal `GateVerdict`s (`PASS`, `unknown` X07, X08, X14); `gate` on a fixture's `Delivery` is unchanged when the test swaps in another fixture's `Label` (it never receives one); `corpus_report` reports `false_pass == 0` on the replayed Q half.
- Against the Q half as recorded: Dafny 18 constructs, Verus 16; the controls 5 + 4 = 9 (P5py's n); the grader-only constructs of the Q half: Dafny G13 (X06) and D-15 (X08) caught by `specfreeze --check`, D-17 (X07) by `witness` and `swap-to-false`; Verus V12 (X07) by `witness` and `swap-to-false`, V13 (X06) by `specfreeze --check`, V14 (X08) by no wrapper instrument: its gate result is a mechanical `PASS` with X08 in `unknown`, which `corpus_report` counts as held. That is the lesson: the gate reports what its instruments can decide and names what they cannot.

### 4.7 `EVAL.md` v1 and the MDE problem

- **`EVAL.md` v1** expected shape: n = the learner's filled Dafny holes of Q04–Q09 (about 30); proofs written under the nonlinear-off modules (Q07, Q08) are expected to be stable more often than Q04–Q06's nonlinear-on ones; a solver-swap failure is likeliest on nonlinear steps. The rubric grades disclosure and the interval, never the number.
- **The MDE problem** (B-problem): use n = 40 and p0 = 0.3 (not P4py's 60 and 0.5); `fvh.stats` gives 0.307.

### 4.8 Exit statements and prompts (Δ133)

*Re-posed by the revision (§R.2 #4, #12). The first exits (A.6c: `ThreeBelowCube`, `WPlusTwo` and their Verus twins) were H1 with a third factor and T1's trigger move on another power, and three of the four could be answered without the construct (§0.1, §R.1). The new exits use another nonlinear shape and another kind of trigger failure, on a function that is not a power. X1d fails at the pin without the construct; the construct-free answers of X1v, X2d and X2v verify and are stopped by their forms and `need:` lines (§R.1 #7, §0.2).*

| id | strand | uses | need | prompt | shipped |
|---|---|---|---|---|---|
| Q09.X1d | S11 | proof-split | `lemma ProductPlusCarry(x: nat, y: nat, z: nat, n: nat)`; `requires x < Pow(n) && y < Pow(n) && z < Pow(n)`; `ensures x * y + z < Pow(n) * Pow(n)` | prove it, splitting the nonlinear reasoning into named library facts, so that it verifies under both bundled solvers and seeds 1–3 with no resource attribute (the exit module keeps nonlinear arithmetic on) | statement-shipped, bodyless lemma, `// form: stable` · none |
| Q09.X2d | S11 | trigger-rewrite | given: `function LimbSum(s: seq<nat>): nat` (`s[0] + LimbSum(s[1..])`, 0 for empty) and `lemma LimbSumAppend(s, t) ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t)` (proved); `lemma SumFour(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)`; `ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)`; `need:` `LimbSum(s + t) == LimbSum(s) + LimbSum(t)` and `LimbSumAppend(s, t);` (the quantified fact and its proof); the block quotes an attempt: `assert forall s: seq<nat>, t: seq<nat> {:trigger LimbSum(s), LimbSum(t)} :: LimbSum(s + t) == LimbSum(s) + LimbSum(t) by { forall s: seq<nat>, t: seq<nat> ensures … { LimbSumAppend(s, t); } }` | rewrite the trigger of the quoted fact (keep the fact and its proof) so that the lemma verifies under both bundled solvers and seeds 1–3 | statement-shipped, bodyless lemma, `// form: trigger, stable` · none |
| Q09.X1v | S11 | proof-split | `pub proof fn lemma_product_plus_carry(x: nat, y: nat, z: nat, n: nat)`; `requires x < weight(n), y < weight(n), z < weight(n)`; `ensures x * y + z < weight(n) * weight(n)` | prove it in at least two scoped steps, each one `nonlinear_arith` with its own `requires`, stable on seeds 1–3 | statement-shipped, `proof_note` assume, `// form: nl-steps:2, stable` · none |
| Q09.X2v | S11 | trigger-rewrite | given: `pub open spec fn limb_sum(s: Seq<u64>) -> nat` (`s[0] as nat + limb_sum(s.drop_first())`) and `pub proof fn lemma_limb_sum_append(s, t)` (proved); `pub proof fn lemma_sum_four(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)`; `ensures limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d)`; `need:` `limb_sum(s + t) == limb_sum(s) + limb_sum(t)` and `lemma_limb_sum_append(s, t);`; the block quotes an attempt: `assert forall\|s: Seq<u64>, t: Seq<u64>\| #![trigger limb_sum(s), limb_sum(t)] limb_sum(s + t) == limb_sum(s) + limb_sum(t) by { lemma_limb_sum_append(s, t); }` | rewrite the trigger (keep the quantified fact and its proof), stable on seeds 1–3 | statement-shipped, `proof_note` assume, `// form: trigger, stable` · none |

**References** (A.15, verified, §R.1 #7): X1d `var p := Pow(n); LemmaMulUpperBound(x, p - 1, y, p - 1); LemmaMulIsDistributiveSub(p - 1, p, 1); LemmaMulStrictInequality(p - 1, p, p);` (3 calls: the product is at most `(p - 1) * (p - 1)`, which is `(p - 1) * p - (p - 1)`, and `(p - 1) * p < p * p`); X2d the quoted fact with `{:trigger LimbSum(s + t)}`; X1v `let p = weight(n); assert(x * y <= (p - 1) * (p - 1)) by (nonlinear_arith) requires x < p, y < p; assert((p - 1) * (p - 1) + (p - 1) < p * p) by (nonlinear_arith) requires p >= 1;`; X2v the quoted fact with `#[trigger] limb_sum(s + t)`.

**Measurements** (§R.1 #7). Dafny, both bundled solvers × seeds 1–3: X1d's reference 23,816..25,342; its empty body and its one-assertion attempt out of resource in all six rows; X2d's reference 71,802..217,725; the quoted multi-trigger attempt out of resource in all six; the construct-free answer (three direct `LimbSumAppend` calls) passes in all six, which the `need:` lines and the `trigger` form stop. Verus, seeds 1–3: X1v's reference 6,103..6,337; the one scoped step with the three `requires` verifies (4,368..4,536), which `nl-steps:2` stops (`# nominal:`, QPLAN §17.11); X2v's reference 5,155..5,163; the quoted attempt `inconclusive` (rlimit) on each; three direct calls verify, stopped as in X2d.

**Twin lines.** X1v `// cfree:` the one scoped step; X2d and X2v `// cfree:` the three direct calls. Each must fail the item's forms (QPLAN §6 Q43).

**Unseen check.** X1 bounds a product plus a further term, which leaves no room for H1's strict step `x * p < p * p`: its proof needs the tight bound `(p - 1) * (p - 1)` and an expansion, steps no H, T, W or C item of Q09 makes (C1 bounds three factors below `BASE`); L4's `MulLimbDigit` is the same shape with the constant `BASE`, where the solver folds the expansion, so its one-call proof is not X1's. X2's failure is a multi-pattern whose instances make new terms from every pair of terms (an explosion over two variables), fixed by moving the trigger to the composite term `LimbSum(s + t)`; T1's failure is a single-variable matching loop, fixed by shifting the argument, and C2 is constrained away from X2's shape (§4.3). Neither X1 nor X2 uses `Pow`'s or `weight`'s step facts, and no Q07–Q09 file states a limb sum. Q08.X1v's `words_sum` (another module's exit) folds by `drop_last` and states no append fact.

## 5. Minutes and calibration notes

- The detailed rates (QPLAN §14.0) are design §7.5's line totals spread over the items; the calibration runs time first: Q07 H6v, H7v, H3d; Q08 H7d, H4v, H9d; Q09 H1d, H3py and the forensic deliveries.
- Q07's port line (35) is the most likely to overrun: if H7v alone passes 20 minutes in calibration, move the mutants' Dafny half into the chapter as a recorded table (−3) before touching another line.
- Q08's agent line (20) assumes the learner writes two Dafny method statements (the shift and the split, revision) and two Verus stubs; if calibration shows more, drop the split's bound on the low part (`ToNat(lo) < Pow(k)`) from the Dafny `STATEMENTS` comment.
- Q09's exits (revision): X1d and X1v are three short steps; X2d and X2v a one-token trigger change, but the learner must see why a multi-pattern explodes; 5.5 minutes each stands until calibration.
- Q09's forensics (40) assume 4 minutes per delivery including the instrument run; the live gate-core run (§17.7) is outside every line.

## 6. What the module lanes must not do

- Put any Q07–Q09 hole's or exit's answer into L4 (re-check Q08's refinements and exits against `QG_L4_Limbs` after any change: the reason H7d moved, §3.2).
- Use `2^64` (or any other value a Q01–Q06 prediction asks about) in a learner-visible sample, test, card or chapter fence.
- Let a card demo carry a hole's or exit's statement or shape (§2.3, §3.3, §4.3 list each constraint), or state an outcome in prose (the sidecars hold it).
- Name, in QPLAN, the chapters, banks or any learner-visible file: which forensic delivery has which species, which bank lemma is false, what P1d–P2dv answer, why `isolate`/`recommends` became RECOGNISE, or why T1d's file has nonlinear arithmetic off.
- Move T1d into a nonlinear-on module (its attempt and its empty body verify there, §0.3), or put another module after `{:disableNonlinearArithmetic}` in one file (Δ31).
- Copy a cheat-corpus fixture into a forensic delivery, or leave a forensic delivery without its `// planted:` marker (healthy ones included, Δ120).
- Ship a refined lemma bodyless (§3.2: the `{ assume false; }` body is the form), a bodyless Dafny function in an agent twin's `STATEMENTS` (§3.4), or an abstract module in any Q07–Q09 learner file or specimen (§3.3).
- Copy the `admissible` entries as admitted: they ship `admitted = false`, 0 minutes, until the four gate results are recorded (QPLAN §16.7).
- Pin an `.audit` file for a Q07–Q09 agent file, or write an acceptance line that names a bank lemma (§4.5).
- Give `classify` or `gate` a label, or let a recorded fixture file hold one (§4.6).
- Leave a construct-free answer of §0.2 out of its twin's `// cfree:` lines, or ship an item whose construct-free answer passes both verification and its forms.
- Put into an agent file, an exit's given code or a card demo a T, H or X statement or reference line of the tier, or an exit's proof pattern (re-run §2.7's check).
- Run a solver job above the lane's memory share, or more than one at a time.

## 7. DV4: what each module needs (author-side detail of QPLAN §6 Q31 and Q33)

*Rewritten by the revision to match `docs/design/DV4-PLAN.md` as revised the same day (§R.4). The first version described a TCP forwarder (Δ61's), an `sg`/`sudo` route report and a human-only override; DV4 now plans an HTTP-aware Ollama gate, a report-only access check with no `sudo` or `sg` from any script, and no override.*

- **Q07 (the Qwen replay; armed with A2d pending).** `scripts/contract_local.sh Q07 --file <agent file>` (DV4 §6, ready at build step 3b; `--available` answers whether it can run). What the Q07 lane writes so that it works: (1) the CONTRACT names the snapshot in a `` `scripts/specfreeze --against research/q07_frozen.dfy <file>` reports no change `` line; the snapshot holds only the `FROZEN` section; the learner commits it with the agent file still as shipped, and DV4 stages the agent file from that commit (`git show <rev>:<path>`), the snapshot read-only at its own path; (2) every machine-checkable acceptance line uses one of DV4 §6's forms (the gate with "prints only the summary line", "zero holes", the `specfreeze --against` line, `` `scripts/vaudit <file>` reports no finding ``); (3) the `git diff` line and the `{:fuel}` line are audit lines (evidence: `patch.diff`); (4) no `.audit` pin is needed; (5) the agent file verifies against the given chain L1–L4 alone; (6) the chapter quotes no replay output until a recorded run exists (Δ121). Budget: `qwen_runs = 1`, `qwen_calls = 40` (the gate counts every request, the turn cap is no higher), `gpu_hours = 1`; DV4's apparatus default for Q07 [A: 40 turns, 45 min, 3,600 GPU-s].
- **Q08:** nothing new (interactive `/contract`).
- **Q09 (the gate core).** DV4 build step 1a: `fvh.verdicts` (`PASS`, `FAIL`, `UNKNOWN`, `GATE_WORDS`, `XCLASSES`, `GRADER_ONLY`), `fvh.corpus` (`load_half(lang, half)`; `Fixture` = `Delivery(id, lang, half, target, files)` + `Label(xclass, kind, title, expects)`), `fvh.tools` (`INSTRUMENTS` with the corpus README's names, `ToolResult(instrument, target, document, exit_code, killed, runner, provenance, output_sha256)`, `Runner` with `HostRunner`, `ContainerRunner`, `ReplayRunner`, `run`, `replay`, `ProvenanceError`, the provenance rule) and the author-only recorder `python -m fvh.tools.record --half Q` writing `harness/tests/q/fixtures/q09/<lang>/<ID>/<instrument>.json` (results only, no label). The Q09 lane runs the recorder, writes `test_q09_gate.py` and the twin (§4.6); the gate calls `tools.run` through the module so that the tests can stub it. The corpus fixtures are `course` targets, so the live run is on the host; the provenance rule sends any `agent` target to the verification container, which is what Q18's gate v2 inherits.
- **Not needed by Q07–Q09:** D6's Claude-in-container runs, policy mode, `fvh report` (Q12).

## 8. Leak constraints across the tier (F15)

- Q07's port uses shifts and masks; L4's `big_add` and `mul_limb` use `%` and `/` on `u128`. Q07.H6v's and H7v's answers are not in L4.
- Q08's flagship reference contains an append lemma (Q04.X1d's statement, a lower-tier exit) and uses L4's `lemma_seq_to_nat_append`; it lives in the agent twin only.
- Q09's bank uses L4's `CmpCorrect` (true lemmas) and Q07's fuel technique (the refutation); no bank lemma is a Q07–Q08 hole's statement.
- Q09.H1d's statement is a sub-fact of Q06.H3d's reference proof; the Q06 twin is not learner-visible, and H1d's reference uses other library facts.
- Q08.X1d's answer uses `L4.AddCorrect` on reversed arguments plus a given lemma; L4 itself holds no line of it.
- (Revision.) Q08.X1d's shipped scaffold applies no `RevRev`; its `FromNatCorrect` goes through the given `FromNatMsfRev` (§3.7).
- (Revision.) Q07's agent files compose L4's `Add`/`MulLimb` and `big_add`/`mul_limb` with distributivity and associativity: no Q07–Q09 item states such a composition; Q08.H4v (`scale` by repeated `plus` through `NatLike`) shares only the distributivity lemma, in another setting (a loop through a trait).
- (Revision.) Q09.X1's tight bound is the symbolic form of L4's `MulLimbDigit`; the constant form's one-call proof does not carry over (§4.8). Q09.X2's `LimbSum` occurs in no other file of the tier.

---

## 9. Integration leak scan (DV3b integration lane, 2026-10-06; author-only)

DELTAS Δ167 records the scan in general terms; the judgements per hit are here. Scratch: `/tmp/dvl0-dv3b-integ/leak/` (`scan.py`, `pair.py`, `report.json`; not archived).

- **Fixed (high).** `tests/wrappers/test_forms_static.py`'s invented toy `Q04.H10v` (`bound`) was Q09.H1v's statement with `p` for `weight(n)`, its two-step `nonlinear_arith` proof verbatim and the one-step attempt in a comment. Replaced by a neutral toy (`zeros`) with the same form counts.
- **The frozen core and the gate core (medium; decided in the DV3b kits phase, DELTAS Δ169: `command` stays public, a gate may compose it, and H4py's docstring says so).** `fvh.tools.command(instrument, target)` is public (Δ161) and returns, for `specfreeze --check`, `witness` and `swap-to-false`, the companion paths that H4py must look for in `delivery.files` (`frozen.dfy`, `witness.dfy`, `swap.dfy` beside a Dafny target; `frozen.rs`, `witness/`, `swapped/` in a Verus crate). A learner can choose H4py's instruments by testing `command(...)`'s path arguments for membership in `delivery.files`, which is most of H4py's reference (the rest is the two always-run instruments and the `run` indirection). `runners._input_paths` (private) does exactly that. The layout itself is public in `tests/corpus/README.md`, which H4py's docstring cites.
- **Accepted by design (low).**
  - L4's `AddC` case split (`if |a| != 0 || |b| != 0`, `var t := Head(a) + Head(b) + c`, the carry and digit) is the skeleton of Q08.H7d's reference helper `AddCCanonical` (a different statement: `Canonical`) and of the Q09 red-team bank's length lemma; it follows L4's own definition.
  - `QG_L4_Limbs.AddCorrect`'s one-call proof `L4.AddCorrect(a, b);` is the first of Q08.H1d's three calls; the hole's work is the normalization (its Hint(2) names L3's two lemmas).
  - Q08's given refinements prove `FromNatCorrect` by `L3.FromNatCorrect(n);`, H2d's first call; H2d's work is the helper induction.
  - Q07.H7v's `ensures` has the form of Q03.H2v's `from_u64` statement (QPLAN §4.2, §8.3, L3); the item asks the learner to carry the contract over, and its body (the bit-vector split) is the work. The body's skeleton shares `let mut v: Vec<u64> = Vec::new();` and a `drop_first` extensionality line with L3's `from_u64`.
  - Q07.H4v's `reveal_with_fuel(seq_to_nat, 3);` is card C1v's success line (a WRITE card and its checked use); the hole's other two lines (the `=~=` facts) are the work.
  - Q09.T1v's reference differs from P2dv's quoted Verus attempt only by the trigger's place; T1d's reference likewise from P2dv's Dafny attempt (the items are a trigger rewrite of a quoted attempt, QPLAN §17.2).
  - Q08.X2d's measure is the given `Flat`'s `decreases Size(c), LeftSize(c)`; the item ships the lemma without one.
  - The Q08 flagship's append helper (statement and proof idiom) is Q04's exit statement and the DV1b freeze fixture's idiom (Δ140's accepted exposure for Q04).
  - Verdict-form strings (`D:ok V:fail`, `D:timeout`, `D:err:resolve`, `D:ok V:err:resolve`, `unchecked`) occur as earlier modules' answers in their chapters and banks.
- **Not a leak.** Exit declaration names of Q07–Q09 occur only in their exit files (statement-shipped) and in the reference tree; `AddCorrect` and `record` occur in QPLAN and the design documents as L4's lemma and an English word.

## Appendix A. Candidate files and probes (scratch, as verified)

Each block is the scratch file verbatim at the time of writing. "A.n" numbers are cited above.

### A.1 L4, Dafny (`dafny/given/Q/QG_L4_BigNat.dfy`)

**As built (DV3b spine lane):** the built file differs from this candidate in `AddLoop`'s loop body (the `AddCDropStep` call moved below the sequence-associativity assertion, which removed a flagged 4.14.1 spread) and in one section comment; the built file is authoritative (DELTAS Δ163).

`root/dafny/given/Q/QG_L4_BigNat.dfy`

```dafny
/*!
# QG_L4_BigNat — the BigNat spine, layer L4 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q07–Q18. From Q07 on, a module's files that use it import it
beside L1–L3. Its modules are QG_L4_BigNat, QG_L4_Spec and QG_L4_Limbs, and
each unit that reaches it includes this file through its dfyconfig.toml.

Do not open this file before you start Q07: it holds proved versions of
lemmas that Q04 poses as holes, so reading it earlier spoils them.

What it holds: two proved lemmas about the L1 and L3 definitions (`PowAdd`,
`CmpCorrect`); schoolbook addition (`AddC`, `Add`) with its proofs and a
compiled loop (`AddLoop`); multiplication by one limb (`MulLimbC`, `MulLimb`)
with its proofs and a compiled loop (`MulLimbLoop`); the arithmetic facts they
use; the abstract module QG_L4_Spec (what any big-number implementation must
provide) and its limb implementation QG_L4_Limbs.
*/
module {:disableNonlinearArithmetic} QG_L4_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened Std.Arithmetic.Mul

  // ---------------------------------------------------------------------------
  // Proved lemmas about the L1 and L3 definitions
  // ---------------------------------------------------------------------------

  // The power of a sum is the product of the powers.
  lemma PowAdd(m: nat, n: nat)
    ensures Pow(m + n) == Pow(m) * Pow(n)
    decreases m
  {
    if m == 0 {
      LemmaMulBasics(Pow(n));
    } else {
      PowAdd(m - 1, n);
      LemmaMulIsAssociative(BASE, Pow(m - 1), Pow(n));
    }
  }

  // Cmp agrees with the order of the values.
  lemma CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  {
    if |a| != 0 || |b| != 0 {
      ValidTail(a);
      ValidTail(b);
      CmpCorrect(Tail(a), Tail(b));
      ToNatHeadTail(a);
      ToNatHeadTail(b);
    }
  }

  // ---------------------------------------------------------------------------
  // Arithmetic facts (from Std.Arithmetic.Mul; nonlinear arithmetic is off)
  // ---------------------------------------------------------------------------

  lemma MulNonneg(x: nat, y: nat)
    ensures 0 <= x * y
  {
    LemmaMulNonnegative(x, y);
  }

  lemma MulZero(x: nat, y: nat)
    requires x == 0 || y == 0
    ensures x * y == 0
  {
    LemmaMulBasics(x);
    LemmaMulBasics(y);
  }

  lemma MulComm(x: nat, y: nat)
    ensures x * y == y * x
  {
    LemmaMulIsCommutative(x, y);
  }

  // A carry out of one limb product is itself a limb.
  lemma MulLimbDigit(x: nat, d: nat, c: nat)
    requires x < BASE && d < BASE && c < BASE
    ensures (x * d + c) / BASE < BASE
  {
    LemmaMulUpperBound(x, BASE - 1, d, BASE - 1);
  }

  // The Horner step distributes over a multiplier.
  lemma DistribHorner(h: nat, t: nat, x: nat)
    ensures (h + BASE * t) * x == h * x + BASE * (t * x)
  {
    LemmaMulIsDistributive(x, h, BASE * t);
    LemmaMulIsAssociative(BASE, t, x);
  }

  // ---------------------------------------------------------------------------
  // Addition
  // ---------------------------------------------------------------------------

  // Schoolbook addition with an incoming carry c.
  opaque function AddC(a: seq<nat>, b: seq<nat>, c: nat): seq<nat>
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then (if c == 0 then [] else [c])
    else
      var t := Head(a) + Head(b) + c;
      if t < BASE then [t] + AddC(Tail(a), Tail(b), 0)
      else [t - BASE] + AddC(Tail(a), Tail(b), 1)
  }

  function Add(a: seq<nat>, b: seq<nat>): seq<nat>
  {
    AddC(a, b, 0)
  }

  lemma {:induction false} AddCCorrect(a: seq<nat>, b: seq<nat>, c: nat)
    requires Valid(a) && Valid(b) && c <= 1
    ensures Valid(AddC(a, b, c)) && ToNat(AddC(a, b, c)) == ToNat(a) + ToNat(b) + c
    decreases |a| + |b|
  {
    reveal AddC();
    if |a| == 0 && |b| == 0 {
      if c != 0 {
        ToNatSingleton(c);
      }
    } else {
      ValidTail(a);
      ValidTail(b);
      ToNatHeadTail(a);
      ToNatHeadTail(b);
      var t := Head(a) + Head(b) + c;
      var c' := if t < BASE then 0 else 1;
      var d := if t < BASE then t else t - BASE;
      AddCCorrect(Tail(a), Tail(b), c');
      ToNatCons(d, AddC(Tail(a), Tail(b), c'));
      ValidCons(d, AddC(Tail(a), Tail(b), c'));
    }
  }

  lemma AddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Add(a, b)) && ToNat(Add(a, b)) == ToNat(a) + ToNat(b)
  {
    AddCCorrect(a, b, 0);
  }

  // One unfolding of AddC at position i, phrased with Drop.
  lemma AddCDropStep(a: seq<nat>, b: seq<nat>, i: nat, c: nat)
    requires i < |a| || i < |b|
    ensures var t := (if i < |a| then a[i] else 0) + (if i < |b| then b[i] else 0) + c;
            AddC(Drop(a, i), Drop(b, i), c)
            == [if t < BASE then t else t - BASE]
               + AddC(Drop(a, i + 1), Drop(b, i + 1), if t < BASE then 0 else 1)
  {
    reveal AddC();
    DropStep(a, i);
    DropStep(b, i);
  }

  // Compiled loop form of Add.
  method {:isolate_assertions} AddLoop(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Add(a, b) && Valid(r) && ToNat(r) == ToNat(a) + ToNat(b)
  {
    var n := if |a| < |b| then |b| else |a|;
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    while i < n
      invariant 0 <= i <= n
      invariant carry <= 1
      invariant r + AddC(Drop(a, i), Drop(b, i), carry) == Add(a, b)
      decreases n - i
    {
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      var t := x + y + carry;
      var digit := if t < BASE then t else t - BASE;
      var c: nat := if t < BASE then 0 else 1;
      AddCDropStep(a, b, i, carry);
      ghost var rest := AddC(Drop(a, i + 1), Drop(b, i + 1), c);
      assert r + ([digit] + rest) == (r + [digit]) + rest;
      r := r + [digit];
      carry := c;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    reveal AddC();
    AddCorrect(a, b);
  }

  // ---------------------------------------------------------------------------
  // Multiplication by one limb
  // ---------------------------------------------------------------------------

  // Multiply by one limb d with an incoming carry c.
  function MulLimbC(s: seq<nat>, d: nat, c: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if c == 0 then [] else [c])
    else
      MulNonneg(s[0], d);
      var t := s[0] * d + c;
      [t % BASE] + MulLimbC(s[1..], d, t / BASE)
  }

  function MulLimb(s: seq<nat>, d: nat): seq<nat>
  {
    MulLimbC(s, d, 0)
  }

  lemma {:induction false} MulLimbCCorrect(s: seq<nat>, d: nat, c: nat)
    requires Valid(s) && d < BASE && c < BASE
    ensures Valid(MulLimbC(s, d, c)) && ToNat(MulLimbC(s, d, c)) == ToNat(s) * d + c
    decreases |s|
  {
    if |s| == 0 {
      MulZero(ToNat(s), d);
      if c != 0 {
        ToNatSingleton(c);
      }
    } else {
      ValidTail(s);
      MulNonneg(s[0], d);
      var t := s[0] * d + c;
      MulLimbDigit(s[0], d, c);
      MulLimbCCorrect(s[1..], d, t / BASE);
      ToNatCons(t % BASE, MulLimbC(s[1..], d, t / BASE));
      ValidCons(t % BASE, MulLimbC(s[1..], d, t / BASE));
      DistribHorner(s[0], ToNat(s[1..]), d);
    }
  }

  lemma MulLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d
  {
    MulLimbCCorrect(s, d, 0);
  }

  // Compiled loop form of MulLimb.
  method {:isolate_assertions} MulLimbLoop(s: seq<nat>, d: nat) returns (r: seq<nat>)
    requires Valid(s) && d < BASE
    ensures r == MulLimb(s, d) && Valid(r) && ToNat(r) == ToNat(s) * d
  {
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert s[0..] == s;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant r + MulLimbC(s[i..], d, carry) == MulLimb(s, d)
      decreases |s| - i
    {
      MulNonneg(s[i], d);
      assert s[i..][1..] == s[i + 1..];
      var t := s[i] * d + carry;
      r := r + [t % BASE];
      carry := t / BASE;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    MulLimbCorrect(s, d);
  }
}

// What any big-number implementation must provide: the frozen statements.
abstract module {:disableNonlinearArithmetic} QG_L4_Spec {
  type BigNat

  ghost function Val(x: BigNat): nat
  ghost predicate Wf(x: BigNat)

  function Zero(): BigNat
  function FromNat(n: nat): BigNat
  function Add(a: BigNat, b: BigNat): BigNat
  function Cmp(a: BigNat, b: BigNat): int

  lemma ZeroCorrect()
    ensures Wf(Zero()) && Val(Zero()) == 0

  lemma FromNatCorrect(n: nat)
    ensures Wf(FromNat(n)) && Val(FromNat(n)) == n

  lemma AddCorrect(a: BigNat, b: BigNat)
    requires Wf(a) && Wf(b)
    ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)

  lemma CmpCorrect(a: BigNat, b: BigNat)
    requires Wf(a) && Wf(b)
    ensures (Cmp(a, b) < 0 <==> Val(a) < Val(b)) && (Cmp(a, b) == 0 <==> Val(a) == Val(b))
}

// The limb implementation refines the frozen statements.
module {:disableNonlinearArithmetic} QG_L4_Limbs refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L1.Valid(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L4.Add(a, b) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
  }

  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }
}
```

### A.2 L4, Verus (`verus/given/qg_bignat_l4/`)

`root/verus/given/qg_bignat_l4/Cargo.toml`

```toml
# qg_bignat_l4 — the BigNat spine, layer L4 (PROVIDED, complete; frozen, guard rule 2f).
# A layer crate depends on vstd and on every lower layer of its chain (Δ22): L1, L2 and L3.
# Never a build script (build = false, Δ20, Δ78). Written by the author, not
# generated: scripts/gen_units.py lists it in verus/Cargo.toml once a module reaches it.
[package]
name = "qg_bignat_l4"
version = "0.1.0"
edition = "2021"
publish = false
build = false

[lib]
path = "src/lib.rs"

[dependencies]
vstd = "=0.0.0-2026-09-20-0158"
qg_bignat_l1 = { path = "../qg_bignat_l1" }
qg_bignat_l2 = { path = "../qg_bignat_l2" }
qg_bignat_l3 = { path = "../qg_bignat_l3" }

[package.metadata.verus]
verify = true
```

`root/verus/given/qg_bignat_l4/src/lib.rs`

```rust
//! # qg_bignat_l4 — the BigNat spine, layer L4 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q07–Q18. From Q07 on, a module's crate depends on this layer beside L1,
//! L2 and L3. A file imports it with `use qg_bignat_l4::*;`, which also brings the L1–L3
//! names (re-exported below); the crate still lists the lower layers as dependencies.
//!
//! Do not open this file before you start Q07: it holds finished versions of code and
//! proofs that Q04 and Q06 pose as holes, so reading it earlier spoils them.
//!
//! What it holds: the verified comparison `cmp` and the proof fns `lemma_weight_add` and
//! `lemma_seq_to_nat_append`; addition (`big_add`, with its carry lemma `lemma_add_lift`);
//! multiplication by one machine word (`mul_limb`, with `lemma_mul_limb_lift`); and the
//! trait `NatLike`, the interface a natural-number implementation offers, with its
//! implementation for `BigNat`.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l3::*;

verus! {

// ---------------------------------------------------------------------------
// Verified code and proofs about the L1–L3 definitions
// ---------------------------------------------------------------------------

/// The weight of a sum of positions is the product of the weights.
pub proof fn lemma_weight_add(m: nat, n: nat)
    ensures
        weight(m + n) == weight(m) * weight(n),
    decreases m,
{
    if m == 0 {
        lemma_weight_zero();
        lemma_mul_basics(weight(n) as int);
    } else {
        let k = (m - 1) as nat;
        lemma_weight_add(k, n);
        lemma_weight_succ(k);
        lemma_weight_succ(k + n);
        lemma_mul_is_associative(BASE as int, weight(k) as int, weight(n) as int);
    }
}

/// The value of a concatenation.
pub proof fn lemma_seq_to_nat_append(a: Seq<u64>, b: Seq<u64>)
    ensures
        seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        lemma_seq_to_nat_append(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(
            BASE as int,
            seq_to_nat(a.drop_first()) as int,
            (weight(k) * seq_to_nat(b)) as int,
        );
    } else {
        lemma_weight_zero();
        assert(a + b =~= b);
    }
}

/// Three-way comparison of two canonical `BigNat`s by value.
pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    broadcast use group_bignat_bounds;

    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
            forall|j: int| i <= j < n ==> a@[j] == b@[j],
        decreases i,
    {
        i = i - 1;
    }
    if i == 0 {
        proof {
            assert(a@ =~= b@);
        }
        Ordering::Equal
    } else if a.limbs[i - 1] < b.limbs[i - 1] {
        proof {
            lemma_lt_at(a@, b@, (i - 1) as int);
        }
        Ordering::Less
    } else {
        proof {
            lemma_lt_at(b@, a@, (i - 1) as int);
        }
        Ordering::Greater
    }
}

// ---------------------------------------------------------------------------
// Addition
// ---------------------------------------------------------------------------

/// Carry lifting for `big_add`: per-limb relations `a[j] + b[j] + c[j] == r[j] + BASE * c[j+1]`
/// add up to the value relation.
pub proof fn lemma_add_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + limb_at(b, j) + c[j] == #[trigger] r[j] + BASE
                * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 { a.drop_first() } else { a };
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + limb_at(b2, j) + c2[j]
            == #[trigger] r2[j] + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) + limb_at(b, j + 1) + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_add_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + limb_at(b, 0) + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

/// The sum of two canonical `BigNat`s.
pub fn big_add(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + b.to_nat(),
{
    let n = a.limbs.len();
    let m = b.limbs.len();
    let len = if n >= m { n } else { m };
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < len
        invariant
            n == a@.len(),
            m == b@.len(),
            len == if n >= m { n } else { m },
            i <= len,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == carry,
            carry <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + limb_at(b@, j) + c[j] == #[trigger] res@[j] + BASE
                    * c[j + 1],
        decreases len - i,
    {
        let x: u64 = if i < n { a.limbs[i] } else { 0 };
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let s: u128 = x as u128 + y as u128 + carry as u128;
        let d: u64 = (s % 0x1_0000_0000_0000_0000u128) as u64;
        carry = (s / 0x1_0000_0000_0000_0000u128) as u64;
        res.push(d);
        proof {
            c = c.push(carry as nat);
        }
        i = i + 1;
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
        }
    }
    proof {
        lemma_add_lift(a@, b@, res@, c);
    }
    BigNat { limbs: res }
}

// ---------------------------------------------------------------------------
// Multiplication by one machine word
// ---------------------------------------------------------------------------

/// Carry lifting for `mul_limb`: per-limb relations `a[j] * x + c[j] == r[j] + BASE * c[j+1]`
/// add up to the value relation.
pub proof fn lemma_mul_limb_lift(a: Seq<u64>, x: nat, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) * x + c[j] == #[trigger] r[j] + BASE * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) * x + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 { a.drop_first() } else { a };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) * x + c2[j]
            == #[trigger] r2[j] + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) * x + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_mul_limb_lift(a2, x, r2, c2);
        assert(limb_at(a, 0) * x + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        let h = limb_at(a, 0);
        let t = seq_to_nat(a2);
        let v = seq_to_nat(a);
        assert(v == h + BASE * t);
        lemma_mul_is_distributive_add_other_way(x as int, h as int, (BASE * t) as int);
        lemma_mul_is_associative(BASE as int, t as int, x as int);
    } else {
        let v = seq_to_nat(a);
        assert(v == 0);
        lemma_mul_basics(x as int);
    }
}

/// The product of a canonical `BigNat` and one machine word.
pub fn mul_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    if x == 0 {
        proof {
            lemma_mul_basics(a.to_nat() as int);
        }
        return BigNat { limbs: res };
    }
    let mut carry: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == carry,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) * x + c[j] == #[trigger] res@[j] + BASE * c[j + 1],
        decreases n - i,
    {
        let li = a.limbs[i];
        proof {
            lemma_mul_upper_bound(li as int, 0xFFFF_FFFF_FFFF_FFFF, x as int, 0xFFFF_FFFF_FFFF_FFFF);
        }
        let p: u128 = li as u128 * x as u128 + carry as u128;
        let d: u64 = (p % 0x1_0000_0000_0000_0000u128) as u64;
        carry = (p / 0x1_0000_0000_0000_0000u128) as u64;
        res.push(d);
        proof {
            c = c.push(carry as nat);
        }
        i = i + 1;
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
            lemma_mul_basics(x as int);
        }
    } else if n > 0 {
        proof {
            let top = a@[n - 1];
            lemma_mul_increases(top as int, x as int);
            assert(limb_at(a@, n - 1) * x + c[n - 1] == res@[n - 1] + BASE * c[n as int]);
        }
    }
    proof {
        lemma_mul_limb_lift(a@, x as nat, res@, c);
    }
    BigNat { limbs: res }
}

// ---------------------------------------------------------------------------
// The interface a natural-number implementation offers
// ---------------------------------------------------------------------------

/// The operations every natural-number implementation provides, with their specifications.
pub trait NatLike: Sized {
    spec fn valid(&self) -> bool;

    spec fn value(&self) -> nat;

    fn zero() -> (r: Self)
        ensures
            r.valid(),
            r.value() == 0,
    ;

    fn from_word(x: u64) -> (r: Self)
        ensures
            r.valid(),
            r.value() == x,
    ;

    fn plus(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r.value() == self.value() + other.value(),
    ;

    fn times_word(&self, x: u64) -> (r: Self)
        requires
            self.valid(),
        ensures
            r.valid(),
            r.value() == self.value() * x,
    ;

    fn compare(&self, other: &Self) -> (r: Ordering)
        requires
            self.valid(),
            other.valid(),
        ensures
            (r == Ordering::Less) == (self.value() < other.value()),
            (r == Ordering::Equal) == (self.value() == other.value()),
            (r == Ordering::Greater) == (self.value() > other.value()),
    ;
}

impl NatLike for BigNat {
    open spec fn valid(&self) -> bool {
        self.wf()
    }

    open spec fn value(&self) -> nat {
        self.to_nat()
    }

    fn zero() -> (r: Self) {
        BigNat { limbs: Vec::new() }
    }

    fn from_word(x: u64) -> (r: Self) {
        from_u64(x)
    }

    fn plus(&self, other: &Self) -> (r: Self) {
        big_add(self, other)
    }

    fn times_word(&self, x: u64) -> (r: Self) {
        mul_limb(self, x)
    }

    fn compare(&self, other: &Self) -> (r: Ordering) {
        cmp(self, other)
    }
}

} // verus!
```

### A.3 Q07 and Q08 Dafny hole references, and Q09.T1d (one scratch file at Q07's exercise path)

The modules after the first are probes kept in one file for the chain; every module carries `{:disableNonlinearArithmetic}`. The built files split them as QPLAN §15.1, §16.1 and §17.1 say (`Q08Canon` and `Q08CanonRaw` become `Q08_Canon.dfy`'s modules, `Q08Words` goes to Q08's exercise file, `Q09Triggers` becomes `Q09_Triggers.dfy`).

`root/dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy`

```dafny
// candidate twin fragments of Q07's Dafny holes (plan probe; not the module file)
module {:disableNonlinearArithmetic} Q07_InternalsI {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod
  import Power = Std.Arithmetic.Power

  // item: Q07.T1d S4
  lemma {:fuel ToNat, 4} ThreeLimbs(a: nat, b: nat, c: nat)
    ensures ToNat([a, b, c]) == a + BASE * (b + BASE * c)
  {
  }

  // item: Q07.H1d S4
  lemma {:fuel AddC, 4} AddCarriesTwice()
    ensures Add([BASE - 1, BASE - 1], [1]) == [0, 0, 1]
  {
    reveal AddC();
  }

  // item: Q07.H2d S5
  lemma DivLimbBound(v: nat, d: nat)
    requires 0 < d < BASE && v < BASE * d
    ensures v / d < BASE
  {
    LemmaMultiplyDivideLt(v, d, BASE);
  }

  // item: Q07.H3d S5
  lemma DivLimbStep(r: nat, x: nat, d: nat)
    requires 0 < d < BASE && r < d && x < BASE
    ensures (r * BASE + x) / d < BASE
  {
    LemmaMulInequality(r + 1, d, BASE);
    LemmaMulIsDistributive(BASE, r, 1);
    LemmaMulIsCommutative(r, BASE);
    LemmaMulIsCommutative(d, BASE);
    LemmaMultiplyDivideLt(r * BASE + x, d, BASE);
  }
}

// ---- Q08 candidates (plan probe) ----
module {:disableNonlinearArithmetic} Q08Canon refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L2.Normalize(L4.Add(a, b)) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCanonical(n: nat)
    ensures L2.Canonical(L2.FromNat(n))
    decreases n
  {
    L3.FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / L1.BASE);
      L3.FromNatCorrect(n / L1.BASE);
    }
  }

  // item: Q08.H2d S6
  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    FromNatCanonical(n);
  }

  // item: Q08.H1d S6
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
    L3.NormalizeToNat(L4.Add(a, b));
    L3.NormalizeCanonical(L4.Add(a, b));
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }
}

module Q08Words {
  import opened QG_L1_BigNat

  newtype u64 = x: int | 0 <= x < 0x1_0000_0000_0000_0000

  // item: Q08.H7d S7
  method AddWithCarry(x: u64, y: u64, c: u64) returns (lo: u64, hi: u64)
    requires c <= 1
    ensures lo as int + hi as int * BASE == x as int + y as int + c as int
    ensures hi <= 1
  {
    var s: int := x as int + y as int + c as int;
    if s < BASE {
      lo, hi := s as u64, 0;
    } else {
      lo, hi := (s - BASE) as u64, 1;
    }
  }
}

module {:disableNonlinearArithmetic} Q08CanonRaw refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.Normalize(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { L4.Add(a, b) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L3.NormalizeToNat(L2.FromNat(n));
    L3.NormalizeCanonical(L2.FromNat(n));
  }

  lemma {:induction false} AddCCanonical(a: seq<nat>, b: seq<nat>, c: nat)
    requires L2.Canonical(a) && L2.Canonical(b) && c <= 1
    ensures L2.Canonical(L4.AddC(a, b, c))
    decreases |a| + |b|
  {
    reveal L4.AddC();
    L4.AddCCorrect(a, b, c);
    if |a| != 0 || |b| != 0 {
      var t := L1.Head(a) + L1.Head(b) + c;
      var c' := if t < L1.BASE then 0 else 1;
      L2.ValidTail(a);
      L2.ValidTail(b);
      L4.AddCCorrect(L1.Tail(a), L1.Tail(b), c');
      if |L1.Tail(a)| != 0 || |L1.Tail(b)| != 0 {
        AddCCanonical(L1.Tail(a), L1.Tail(b), c');
      }
    }
  }

  // item: Q08.H7d S6
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
    AddCCanonical(a, b, 0);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }
}

// ---- Q09 T1d candidate (plan probe; nonlinear arithmetic off by its own attribute) ----
module {:disableNonlinearArithmetic} Q09Triggers {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q09.T1d S11
  lemma PowGrowsByBase(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k) * BASE <= Pow(k + 1) {
      assert Pow(k + 1) == BASE * Pow(k);
    }
    if m + 1 < n {
      PowGrowsByBase(m + 1, n);
      PowAdd(m + 1, 0);
    }
  }
}
```

### A.4 Q07 and Q08 Verus hole references (scratch crate `q07_internals_i`)

The `q08` module is Q08's crate content, kept here for the chain.

`root/verus/q/q07_internals_i/Cargo.toml`

```toml
# GENERATED by scripts/gen_units.py from MODULES.toml. Do not edit:
# change the registry or the options file, then run `python3 scripts/gen_units.py`
# (`--check` compares; CI's units group runs it).
# Unit: Q06, Verus. Dependencies: vstd and the layer chain L1–L3 (Δ22).
[package]
name = "q07_internals_i"
version = "0.1.0"
edition = "2021"
publish = false
build = false

[lib]
path = "src/lib.rs"

[dependencies]
vstd = "=0.0.0-2026-09-20-0158"
qg_bignat_l1 = { path = "../../given/qg_bignat_l1" }
qg_bignat_l2 = { path = "../../given/qg_bignat_l2" }
qg_bignat_l3 = { path = "../../given/qg_bignat_l3" }
qg_bignat_l4 = { path = "../../given/qg_bignat_l4" }

[package.metadata.verus]
verify = true
```

`root/verus/q/q07_internals_i/src/lib.rs`

```rust
//! candidate twin fragments of Q07's Verus holes (plan probe)
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.T1v S4
pub proof fn lemma_three_limbs(a: u64, b: u64, c: u64)
    ensures seq_to_nat(seq![a, b, c]) == a + BASE * (b + BASE * c),
{
    reveal_with_fuel(seq_to_nat, 4);
    assert(seq![a, b, c].drop_first() =~= seq![b, c]);
    assert(seq![b, c].drop_first() =~= seq![c]);
    assert(seq![c].drop_first() =~= Seq::<u64>::empty());
}

// item: Q07.H4v S4
pub proof fn lemma_two_limbs_then(a: u64, b: u64, s: Seq<u64>)
    ensures seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
{
    reveal_with_fuel(seq_to_nat, 3);
    assert((seq![a, b] + s).drop_first() =~= seq![b] + s);
    assert((seq![b] + s).drop_first() =~= s);
}

// item: Q07.H5v S5
pub proof fn lemma_div_weight_succ(v: nat, n: nat)
    ensures v / weight(n + 1) == (v / weight(n)) / BASE,
{
    lemma_weight_succ(n);
    lemma_weight_zero();
    lemma_weight_mono(0, n);
    lemma_mul_is_commutative(BASE as int, weight(n) as int);
    lemma_div_denominator(v as int, weight(n) as int, BASE as int);
}

// item: Q07.H6v S1
pub fn split_word(p: u128) -> (r: (u64, u64))
    ensures r.0 as nat * BASE + r.1 as nat == p as nat,
{
    proof {
        assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (bit_vector);
        assert((p & 0xFFFF_FFFF_FFFF_FFFFu128) == p % 0x1_0000_0000_0000_0000u128) by (bit_vector);
    }
    let hi = (p >> 64u128) as u64;
    let lo = (p & 0xFFFF_FFFF_FFFF_FFFFu128) as u64;
    (hi, lo)
}

} // verus!

// ---- Q08 candidates (plan probe) ----
pub mod q08 {
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::cell::pcell::*;
use qg_bignat_l4::*;

verus! {

// item: Q08.H3v S6 (the learner writes the two method specs)
pub trait Odometer: Sized {
    spec fn reading(&self) -> nat;

    spec fn ok(&self) -> bool;

    fn advance(&mut self, by: u64)
        requires
            old(self).ok(),
        ensures
            final(self).ok(),
            final(self).reading() == old(self).reading() + by,
    ;

    fn current(&self) -> (r: BigNat)
        requires
            self.ok(),
        ensures
            r.wf(),
            r.to_nat() == self.reading(),
    ;
}

pub struct Odo {
    pub total: BigNat,
}

impl Odometer for Odo {
    open spec fn reading(&self) -> nat {
        self.total.to_nat()
    }

    open spec fn ok(&self) -> bool {
        self.total.wf()
    }

    fn advance(&mut self, by: u64) {
        let step = from_u64(by);
        self.total = big_add(&self.total, &step);
    }

    fn current(&self) -> (r: BigNat) {
        let mut v: Vec<u64> = Vec::new();
        let n = self.total.limbs.len();
        let mut i: usize = 0;
        while i < n
            invariant i <= n, n == self.total@.len(), v@ =~= self.total@.subrange(0, i as int),
            decreases n - i,
        {
            v.push(self.total.limbs[i]);
            i = i + 1;
        }
        proof { assert(self.total@.subrange(0, n as int) =~= self.total@); }
        BigNat { limbs: v }
    }
}

/// Given client: the specs must let this verify.
pub fn advance_twice<O: Odometer>(o: &mut O, a: u64, b: u64)
    requires
        old(o).ok(),
    ensures
        final(o).ok(),
        final(o).reading() == old(o).reading() + a + b,
{
    o.advance(a);
    o.advance(b);
}

// item: Q08.H4v S6
pub fn scale<T: NatLike>(v: &T, k: u64) -> (r: T)
    requires
        v.valid(),
    ensures
        r.valid(),
        r.value() == v.value() * k,
{
    let mut acc = T::zero();
    let mut i: u64 = 0;
    while i < k
        invariant
            i <= k,
            v.valid(),
            acc.valid(),
            acc.value() == v.value() * i,
        decreases k - i,
    {
        acc = acc.plus(v);
        proof {
            lemma_mul_is_distributive_add(v.value() as int, i as int, 1);
        }
        i = i + 1;
    }
    acc
}

// item: Q08.H5v S8
pub fn bump(cell: &PCell<u64>, Tracked(perm): Tracked<&mut PointsTo<u64>>)
    requires
        cell.id() == old(perm).id(),
        *old(perm).value() < u64::MAX,
    ensures
        final(perm).id() == cell.id(),
        *final(perm).value() == *old(perm).value() + 1,
{
    let v = cell.read(Tracked(&*perm));
    cell.write(Tracked(perm), v + 1);
}

// item: Q08.H6v S8
pub fn transfer(src: &PCell<u64>, dst: &PCell<u64>, Tracked(ps): Tracked<&mut PointsTo<u64>>, Tracked(pd): Tracked<&mut PointsTo<u64>>)
    requires
        src.id() == old(ps).id(),
        dst.id() == old(pd).id(),
        *old(pd).value() as nat + *old(ps).value() as nat <= u64::MAX as nat,
    ensures
        final(ps).id() == src.id(),
        final(pd).id() == dst.id(),
        *final(ps).value() == 0,
        *final(pd).value() == *old(pd).value() + *old(ps).value(),
{
    let a = src.read(Tracked(&*ps));
    let b = dst.read(Tracked(&*pd));
    src.write(Tracked(ps), 0);
    dst.write(Tracked(pd), b + a);
}

} // verus!
}
```

### A.5 Q07 port (`port.rs` references)

`probe/q07/port_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

/// The port of L2's FromNat to inputs below 2^128.
pub fn from_u128(x: u128) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    let lo = x as u64;
    let hi = (x >> 64u128) as u64;
    proof {
        assert(x as u64 == x % 0x1_0000_0000_0000_0000u128) by (bit_vector);
        assert((x >> 64u128) == x / 0x1_0000_0000_0000_0000u128) by (bit_vector);
    }
    let mut v: Vec<u64> = Vec::new();
    if hi != 0 {
        v.push(lo);
        v.push(hi);
        proof {
            assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty());
            reveal_with_fuel(seq_to_nat, 3);
        }
    } else if lo != 0 {
        v.push(lo);
        proof {
            assert(v@.drop_first() =~= Seq::<u64>::empty());
            reveal_with_fuel(seq_to_nat, 2);
        }
    }
    BigNat { limbs: v }
}

/// An independent transcription of L2's FromNat (Dafny) into a Verus spec fn.
pub open spec fn from_nat_mirror(n: nat) -> Seq<u64>
    decreases n,
{
    if n == 0 {
        Seq::empty()
    } else {
        seq![(n % BASE) as u64] + from_nat_mirror(n / BASE)
    }
}

/// The mirror's output meets the port's contract (relative to the mirror).
pub proof fn lemma_mirror_meets_port_spec(x: u128)
    ensures
        seq_wf(from_nat_mirror(x as nat)),
        seq_to_nat(from_nat_mirror(x as nat)) == x as nat,
{
    let n = x as nat;
    let q = n / BASE;
    assert(q < BASE) by {
        assert(x as nat / 0x1_0000_0000_0000_0000nat < 0x1_0000_0000_0000_0000nat) by (nonlinear_arith)
            requires x <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFu128;
    }
    assert(q / BASE == 0);
    reveal_with_fuel(from_nat_mirror, 3);
    reveal_with_fuel(seq_to_nat, 3);
    if n == 0 {
    } else if q == 0 {
        assert(from_nat_mirror(n) =~= seq![(n % BASE) as u64]);
        assert(seq![(n % BASE) as u64].drop_first() =~= Seq::<u64>::empty());
    } else {
        assert(from_nat_mirror(q) =~= seq![(q % BASE) as u64]);
        assert(from_nat_mirror(n) =~= seq![(n % BASE) as u64, (q % BASE) as u64]);
        assert(seq![(n % BASE) as u64, (q % BASE) as u64].drop_first() =~= seq![(q % BASE) as u64]);
        assert(seq![(q % BASE) as u64].drop_first() =~= Seq::<u64>::empty());
        lemma_fundamental_div_mod(n as int, BASE as int);
    }
}

} // verus!

#[cfg(test)]
mod port_tests {
    use super::*;
    #[test]
    fn sample() {
        assert_eq!(from_u128(0).limbs, Vec::<u64>::new());
        assert_eq!(from_u128(5).limbs, vec![5u64]);
        assert_eq!(from_u128(1u128 << 64).limbs, vec![0u64, 1u64]);
        assert_eq!(from_u128(u128::MAX).limbs, vec![u64::MAX, u64::MAX]);
    }
}
```

### A.6 Q07 exit references

`Q08ExitProbe.AddCCanonical` in the Dafny file is the helper later used by Q08.H7d's reference (A.3); it is not an exit.

`probe/exit/x_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q07ExitProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod

  // Q07.X1d S5
  lemma ProductOfPowSuccModBase(x: nat, k: nat)
    ensures (x * Pow(k + 1)) % BASE == 0
  {
    assert Pow(k + 1) == BASE * Pow(k);
    LemmaMulIsAssociative(x, BASE, Pow(k));
    LemmaMulIsCommutative(x, BASE);
    LemmaMulIsAssociative(BASE, x, Pow(k));
    LemmaMulIsCommutative(BASE, x * Pow(k));
    LemmaModMultiplesBasic(x * Pow(k), BASE);
  }

  // Q07.X2d S4
  lemma DivBaseOfTwoLimbs(a: nat, b: nat)
    requires a < BASE
    ensures ToNat([a, b]) / BASE == b
  {
    ToNatCons(a, [b]);
    ToNatSingleton(b);
    assert ToNat([a, b]) == a + BASE * b;
    LemmaMulIsCommutative(BASE, b);
    LemmaFundamentalDivModConverse(ToNat([a, b]), BASE, b, a);
  }
}

module Q08ExitProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // helper for Q08.X1d: AddC of canonical inputs is canonical
  lemma {:induction false} AddCCanonical(a: seq<nat>, b: seq<nat>, c: nat)
    requires Canonical(a) && Canonical(b) && c <= 1
    ensures Canonical(AddC(a, b, c))
    decreases |a| + |b|
  {
    reveal AddC();
    AddCCorrect(a, b, c);
    if |a| != 0 || |b| != 0 {
      var t := Head(a) + Head(b) + c;
      var c' := if t < BASE then 0 else 1;
      var d := if t < BASE then t else t - BASE;
      ValidTail(a);
      ValidTail(b);
      var r := AddC(Tail(a), Tail(b), c');
      AddCCorrect(Tail(a), Tail(b), c');
      if |Tail(a)| == 0 && |Tail(b)| == 0 {
        assert r == (if c' == 0 then [] else [c']);
      } else {
        assert Canonical(Tail(a)) || |Tail(a)| == 0;
        assert Canonical(Tail(b)) || |Tail(b)| == 0;
        AddCCanonical(Tail(a), Tail(b), c');
      }
      assert AddC(a, b, c) == [d] + r;
      if |r| == 0 {
        assert d != 0 || false;
      }
    }
  }
}
```

`probe/exit/x_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// Q07.X1v S1
pub fn join_word(hi: u64, lo: u64) -> (r: u128)
    ensures r as nat == hi as nat * BASE + lo as nat,
{
    proof {
        assert(((hi as u128) << 64u128) | (lo as u128) == (hi as u128) * 0x1_0000_0000_0000_0000u128 + (lo as u128)) by (bit_vector);
    }
    ((hi as u128) << 64u128) | (lo as u128)
}

// Q07.X2v S5
pub proof fn lemma_weight_quotient(k: nat, n: nat)
    requires k <= n,
    ensures weight(n) / weight(k) == weight((n - k) as nat),
{
    lemma_weight_add(k, (n - k) as nat);
    lemma_weight_zero();
    lemma_weight_mono(0, k);
    lemma_mul_is_commutative(weight(k) as int, weight((n - k) as nat) as int);
    lemma_div_multiples_vanish(weight((n - k) as nat) as int, weight(k) as int);
}

} // verus!
```

### A.6b Q08 exit references

Each file holds comparison bodies (`…Empty`, `…NoMeasure`, `…_triv`) that fail by design.

`probe/exit/x08_d.dfy`

```dafny
// Q08.X1d candidate: a refinement of QG_L4_Spec that stores limbs most significant first
module {:disableNonlinearArithmetic} Q08_ExitRev refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  function Rev(x: seq<nat>): seq<nat>
    decreases |x|
  {
    if |x| == 0 then [] else Rev(x[1..]) + [x[0]]
  }

  lemma RevAppend(x: seq<nat>, y: seq<nat>)
    ensures Rev(x + y) == Rev(y) + Rev(x)
    decreases |x|
  {
    if |x| == 0 {
      assert x + y == y;
    } else {
      assert (x + y)[1..] == x[1..] + y;
      RevAppend(x[1..], y);
    }
  }

  lemma RevRev(x: seq<nat>)
    ensures Rev(Rev(x)) == x
    decreases |x|
  {
    if |x| != 0 {
      RevAppend(Rev(x[1..]), [x[0]]);
      RevRev(x[1..]);
      assert Rev([x[0]]) == [x[0]];
      assert [x[0]] + x[1..] == x;
    }
  }

  ghost function Val(x: BigNat): nat { L1.ToNat(Rev(x)) }
  ghost predicate Wf(x: BigNat) { L1.Valid(Rev(x)) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { Rev(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { Rev(L4.Add(Rev(a), Rev(b))) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(Rev(a), Rev(b)) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    RevRev(L2.FromNat(n));
    L3.FromNatCorrect(n);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(Rev(a), Rev(b));
  }

  // item: Q08.X1d S6 (reference)
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    RevRev(L4.Add(Rev(a), Rev(b)));
    L4.AddCorrect(Rev(a), Rev(b));
  }
}

module {:disableNonlinearArithmetic} Q08_ExitRevEmpty refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat
  type BigNat = seq<nat>
  function Rev(x: seq<nat>): seq<nat>
    decreases |x|
  {
    if |x| == 0 then [] else Rev(x[1..]) + [x[0]]
  }
  ghost function Val(x: BigNat): nat { L1.ToNat(Rev(x)) }
  ghost predicate Wf(x: BigNat) { L1.Valid(Rev(x)) }
  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { Rev(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { Rev(L4.Add(Rev(a), Rev(b))) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(Rev(a), Rev(b)) }
  lemma ZeroCorrect() {}
  lemma FromNatCorrect(n: nat) { assume {:axiom} false; }
  lemma CmpCorrect(a: BigNat, b: BigNat) { L4.CmpCorrect(Rev(a), Rev(b)); }
  // the empty body of the exit item, for comparison
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(Rev(a), Rev(b));
  }
}
```

`probe/exit/x08b_d.dfy`

```dafny
// Q08.X2d candidate: termination of a lemma that follows a re-associating function
module Q08_ExitFlat {
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)
  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd)
  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
  }

  function Exec(c: Cmd, s: State): State
  {
    match c
    case Skip => s
    case Assign(x, e) => (y: nat) => if y == x then Eval(e, s) else s(y)
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
  }

  function Size(c: Cmd): nat
  {
    match c
    case Skip => 1
    case Assign(_, _) => 1
    case Seq(c1, c2) => Size(c1) + Size(c2) + 1
  }

  function LeftSize(c: Cmd): nat
  {
    match c
    case Seq(c1, _) => Size(c1)
    case _ => 0
  }

  // the rotation keeps the size and shrinks the left part (given, proved)
  lemma RotateSmaller(a: Cmd, b: Cmd, d: Cmd)
    ensures Size(Seq(a, Seq(b, d))) == Size(Seq(Seq(a, b), d))
    ensures LeftSize(Seq(a, Seq(b, d))) < LeftSize(Seq(Seq(a, b), d))
  {
    assert Size(Seq(b, d)) == Size(b) + Size(d) + 1;
    assert Size(Seq(a, b)) == Size(a) + Size(b) + 1;
  }

  // right-associates every sequence
  function Flat(c: Cmd): Cmd
    decreases Size(c), LeftSize(c)
  {
    match c
    case Skip => Skip
    case Assign(x, e) => Assign(x, e)
    case Seq(c1, d) =>
      match c1
      case Seq(a, b) =>
        RotateSmaller(a, b, d);
        Flat(Seq(a, Seq(b, d)))
      case _ => Seq(c1, Flat(d))
  }

  // item: Q08.X2d S7 (reference)
  lemma FlatSame(c: Cmd, s: State)
    ensures Exec(Flat(c), s) == Exec(c, s)
    decreases Size(c), LeftSize(c)
  {
    match c
    case Skip =>
    case Assign(x, e) =>
    case Seq(c1, d) =>
      match c1
      case Seq(a, b) =>
        RotateSmaller(a, b, d);
        FlatSame(Seq(a, Seq(b, d)), s);
      case _ => FlatSame(d, Exec(c1, s));
  }

  // the same body with no decreases clause, for comparison
  lemma FlatSameNoMeasure(c: Cmd, s: State)
    ensures Exec(Flat(c), s) == Exec(c, s)
  {
    match c
    case Skip =>
    case Assign(x, e) =>
    case Seq(c1, d) =>
      match c1
      case Seq(a, b) =>
        RotateSmaller(a, b, d);
        FlatSameNoMeasure(Seq(a, Seq(b, d)), s);
      case _ => FlatSameNoMeasure(d, Exec(c1, s));
  }

  // the empty body
  lemma FlatSameEmpty(c: Cmd, s: State)
    ensures Exec(Flat(c), s) == Exec(c, s)
    decreases Size(c), LeftSize(c)
  {
  }
}
```

`probe/exit/x08_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// Q08.X1v candidate
pub open spec fn words_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { words_sum(s.drop_last()) + s.last() as nat }
}

pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)
    ensures r.valid(), r.value() == words_sum(xs@),
{
    let mut acc = T::zero();
    let mut i: usize = 0;
    while i < xs.len()
        invariant
            0 <= i <= xs.len(),
            acc.valid(),
            acc.value() == words_sum(xs@.subrange(0, i as int)),
        decreases xs.len() - i,
    {
        let w = T::from_word(xs[i]);
        acc = acc.plus(&w);
        assert(xs@.subrange(0, i + 1).drop_last() =~= xs@.subrange(0, i as int));
        i = i + 1;
    }
    assert(xs@.subrange(0, xs.len() as int) =~= xs@);
    acc
}

// Q08.X2v candidate
pub struct Ledger {
    pub total: u64,
    pub log: Ghost<Seq<u64>>,
}

impl Ledger {
    pub open spec fn inv(&self) -> bool {
        self.total == words_sum(self.log@)
    }

    pub fn record(&mut self, x: u64)
        requires old(self).inv(), old(self).total + x <= u64::MAX,
        ensures final(self).inv(), final(self).log@ == old(self).log@.push(x),
    {
        let ghost old_log = self.log@;
        self.log = Ghost(old_log.push(x));
        self.total = self.total + x;
        assert(old_log.push(x).drop_last() =~= old_log);
    }
}

// trivial bodies, for comparison
pub fn sum_words_triv<T: NatLike>(xs: &Vec<u64>) -> (r: T)
    ensures r.valid(), r.value() == words_sum(xs@),
{
    T::zero()
}

} // verus!
```

### A.6c Q09 exit references

*Superseded by the revision: the exits these files hold were re-posed (§4.8); the adopted references are in A.15. Kept for the record.*

`x09_d.dfy` is the first round (its `ThreeBelowCube` misses the zero case and fails a precondition; its `Pow`-based X2 candidate loops either way), kept for the record; `x09b_d.dfy` holds the adopted Dafny candidates.

`probe/exit/x09b_d.dfy`

```dafny
// Q09 exit candidates, second round (nonlinear arithmetic on, as the Q09 exit module)
module Q09ExitProbeB {
  import opened QG_L1_BigNat
  import opened Std.Arithmetic.Mul

  // X1d reference candidate
  lemma ThreeBelowCube(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y * z < Pow(n) * Pow(n) * Pow(n)
  {
    var p := Pow(n);
    LemmaMulUpperBound(x, p, y, p);
    LemmaMulStrictlyPositive(p, p);
    if z == 0 {
      LemmaMulBasics(x * y);
      LemmaMulStrictlyPositive(p * p, p);
    } else {
      LemmaMulInequality(x * y, p * p, z);
      LemmaMulStrictInequality(z, p, p * p);
      LemmaMulIsCommutative(z, p * p);
      LemmaMulIsCommutative(p, p * p);
    }
  }

  // X2d: the given stand-in (opaque, like Verus's weight) and its step lemma
  opaque function W(n: nat): nat { Pow(n) }

  lemma WSucc(k: nat)
    ensures W(k + 1) == BASE * W(k)
  {
    reveal W();
  }

  // X2d: quoted attempt (trigger on the successor term)
  lemma WPlusTwoAttempt(n: nat)
    ensures W(n + 2) == BASE * BASE * W(n)
  {
    forall k: nat {:trigger W(k + 1)} ensures W(k + 1) == BASE * W(k) {
      WSucc(k);
    }
    assert W(n + 2) == BASE * W(n + 1);
    assert W(n + 1) == BASE * W(n);
  }

  // X2d: reference candidate (trigger on the plain term)
  lemma WPlusTwo(n: nat)
    ensures W(n + 2) == BASE * BASE * W(n)
  {
    forall k: nat {:trigger W(k)} ensures W(k + 1) == BASE * W(k) {
      WSucc(k);
    }
    assert W(n + 2) == BASE * W(n + 1);
    assert W(n + 1) == BASE * W(n);
  }

  // X2d: empty body
  lemma WPlusTwoEmpty(n: nat)
    ensures W(n + 2) == BASE * BASE * W(n)
  {
  }
}
```

`probe/exit/x09_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// X1v reference candidate
pub proof fn lemma_three_below_cube(x: nat, y: nat, z: nat, n: nat)
    requires x < weight(n), y < weight(n), z < weight(n),
    ensures x * y * z < weight(n) * weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y < p * p) by (nonlinear_arith) requires x < p, y < p;
    assert(x * y * z < p * p * p) by (nonlinear_arith) requires x * y < p * p, z < p;
}

// X1v one-step attempt
pub proof fn lemma_three_below_cube_attempt(x: nat, y: nat, z: nat, n: nat)
    requires x < weight(n), y < weight(n), z < weight(n),
    ensures x * y * z < weight(n) * weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y * z < p * p * p) by (nonlinear_arith) requires x < p, y < p, z < p;
}

// X2v quoted attempt (trigger on the successor term)
pub proof fn lemma_weight_plus_two_attempt(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| weight(k) * BASE == #[trigger] weight(k + 1) by {
        lemma_weight_succ(k);
    }
}

// X2v reference candidate
pub proof fn lemma_weight_plus_two(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
        lemma_weight_succ(k);
    }
}

// X2v empty body
pub proof fn lemma_weight_plus_two_empty(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
}

} // verus!
```

`probe/exit/x09b_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// X2v quoted attempt (trigger on the successor term)
pub proof fn lemma_weight_plus_two_attempt(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| weight(k) * BASE == #[trigger] weight(k + 1) by {
        lemma_weight_succ(k);
    }
    assert(weight(n + 2) == weight(n + 1) * BASE);
    assert(weight(n + 1) == weight(n) * BASE);
}

// X2v reference candidate
pub proof fn lemma_weight_plus_two(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
        lemma_weight_succ(k);
    }
    assert(weight(n + 2) == weight(n + 1) * BASE);
    assert(weight(n + 1) == weight(n) * BASE);
}

} // verus!
```

`probe/exit/x09_d.dfy`

```dafny
// Q09 exit candidates (nonlinear arithmetic on, as the Q09 exit module)
module Q09ExitProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // X1d reference candidate
  lemma ThreeBelowCube(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y * z < Pow(n) * Pow(n) * Pow(n)
  {
    var p := Pow(n);
    LemmaMulStrictInequality(x, p, y);
    LemmaMulLeftInequality(p, y, p);
    assert x * y < p * p;
    LemmaMulStrictInequality(x * y, p * p, z);
    LemmaMulLeftInequality(p * p, z, p);
  }

  // X1d empty body
  lemma ThreeBelowCubeEmpty(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y * z < Pow(n) * Pow(n) * Pow(n)
  {
  }

  // X2d: quoted attempt (trigger on the successor term)
  lemma PowPlusThreeAttempt(n: nat)
    ensures Pow(n + 3) == BASE * BASE * BASE * Pow(n)
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k + 1) == BASE * Pow(k) {
    }
  }

  // X2d: reference candidate (trigger on the plain term)
  lemma PowPlusThreeRewrite(n: nat)
    ensures Pow(n + 3) == BASE * BASE * BASE * Pow(n)
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k + 1) == BASE * Pow(k) {
    }
  }

  // X2d empty body
  lemma PowPlusThreeEmpty(n: nat)
    ensures Pow(n + 3) == BASE * BASE * BASE * Pow(n)
  {
  }
}
```

### A.7 Q07 agent target, Dafny (shipped monolithic state)

*Superseded by the revision: this candidate held T1d's statement and answer and P1dv's literal (§2.5, §R.2 #5). The new candidates are in A.15. Kept for the record; never ship it.*

`probe/agent/refactor_d.dfy`

```dafny
// candidate shipped state of Q07's Dafny refactor file (monolithic, verified)
module {:disableNonlinearArithmetic} Q07_AgentRefactorProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // FROZEN: the value of two limbs times one limb fits in three limbs.
  lemma TwoLimbsTimesLimb(a: nat, b: nat, d: nat)
    requires a < BASE && b < BASE && d < BASE
    ensures ToNat([a, b]) * d < Pow(3)
  {
    ToNatCons(a, [b]);
    ToNatSingleton(b);
    assert ToNat([a, b]) == a + BASE * b;
    assert ToNat([a, b]) <= (BASE - 1) + BASE * (BASE - 1);
    assert ToNat([a, b]) < BASE * BASE;
    LemmaMulUpperBound(ToNat([a, b]), BASE * BASE - 1, d, BASE - 1);
    assert (BASE * BASE - 1) * (BASE - 1) < BASE * BASE * BASE;
    assert Pow(1) == BASE * Pow(0);
    assert Pow(2) == BASE * Pow(1);
    assert Pow(3) == BASE * Pow(2);
    assert Pow(3) == BASE * BASE * BASE;
  }

  // FROZEN: the value of three limbs is below Pow(3).
  lemma ThreeLimbsBelow(a: nat, b: nat, c: nat)
    requires a < BASE && b < BASE && c < BASE
    ensures ToNat([a, b, c]) < Pow(3)
  {
    ToNatCons(a, [b, c]);
    ToNatCons(b, [c]);
    ToNatSingleton(c);
    assert [a, b, c][1..] == [b, c];
    assert [b, c][1..] == [c];
    assert ToNat([a, b, c]) == a + BASE * (b + BASE * c);
    assert b + BASE * c <= (BASE - 1) + BASE * (BASE - 1);
    assert b + BASE * c < BASE * BASE;
    assert ToNat([a, b, c]) < BASE * BASE * BASE;
    assert Pow(1) == BASE * Pow(0);
    assert Pow(2) == BASE * Pow(1);
    assert Pow(3) == BASE * Pow(2);
    assert Pow(3) == BASE * BASE * BASE;
  }
}
```

### A.8 Q08 verified wp (W2d with H8d–H10d's references) and P5dv's check

`probe/q08/wp2_d.dfy`

```dafny
module ProbeWp2 {
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr) | Minus(a: Expr, b: Expr)
  datatype BExp = Le(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)
  datatype Cmd = Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | If(b: BExp, c1: Cmd, c2: Cmd)
  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
    case Minus(a, b) => Eval(a, s) - Eval(b, s)
  }

  predicate Holds(p: BExp, s: State)
  {
    match p
    case Le(l, r) => Eval(l, s) <= Eval(r, s)
    case And(p1, p2) => Holds(p1, s) && Holds(p2, s)
    case Not(p1) => !Holds(p1, s)
    case Imp(p1, p2) => Holds(p1, s) ==> Holds(p2, s)
  }

  opaque function Update(s: State, x: nat, v: int): State
  {
    (y: nat) => if y == x then v else s(y)
  }

  lemma UpdateApply(s: State, x: nat, v: int, y: nat)
    ensures Update(s, x, v)(y) == if y == x then v else s(y)
  {
    reveal Update();
  }

  function Exec(c: Cmd, s: State): State
  {
    match c
    case Assign(x, e) => Update(s, x, Eval(e, s))
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
    case If(b, c1, c2) => if Holds(b, s) then Exec(c1, s) else Exec(c2, s)
  }

  function SubstE(t: Expr, x: nat, e: Expr): Expr
  {
    match t
    case Const(n) => Const(n)
    case Var(y) => if y == x then e else Var(y)
    case Plus(a, b) => Plus(SubstE(a, x, e), SubstE(b, x, e))
    case Minus(a, b) => Minus(SubstE(a, x, e), SubstE(b, x, e))
  }

  function SubstB(p: BExp, x: nat, e: Expr): BExp
  {
    match p
    case Le(l, r) => Le(SubstE(l, x, e), SubstE(r, x, e))
    case And(p1, p2) => And(SubstB(p1, x, e), SubstB(p2, x, e))
    case Not(p1) => Not(SubstB(p1, x, e))
    case Imp(p1, p2) => Imp(SubstB(p1, x, e), SubstB(p2, x, e))
  }

  function Wp(c: Cmd, q: BExp): BExp
  {
    match c
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Wp(c1, Wp(c2, q))
    case If(b, c1, c2) => And(Imp(b, Wp(c1, q)), Imp(Not(b), Wp(c2, q)))
  }

  lemma SubstEOk(t: Expr, x: nat, e: Expr, s: State)
    ensures Eval(SubstE(t, x, e), s) == Eval(t, Update(s, x, Eval(e, s)))
    decreases t
  {
    match t
    case Const(n) =>
    case Var(y) => UpdateApply(s, x, Eval(e, s), y);
    case Plus(a, b) => SubstEOk(a, x, e, s); SubstEOk(b, x, e, s);
    case Minus(a, b) => SubstEOk(a, x, e, s); SubstEOk(b, x, e, s);
  }

  lemma SubstEOkEmpty(t: Expr, x: nat, e: Expr, s: State)
    ensures Eval(SubstE(t, x, e), s) == Eval(t, Update(s, x, Eval(e, s)))
    decreases t
  {}

  lemma SubstBOk(p: BExp, x: nat, e: Expr, s: State)
    ensures Holds(SubstB(p, x, e), s) == Holds(p, Update(s, x, Eval(e, s)))
    decreases p
  {
    match p
    case Le(l, r) => SubstEOk(l, x, e, s); SubstEOk(r, x, e, s);
    case And(p1, p2) => SubstBOk(p1, x, e, s); SubstBOk(p2, x, e, s);
    case Not(p1) => SubstBOk(p1, x, e, s);
    case Imp(p1, p2) => SubstBOk(p1, x, e, s); SubstBOk(p2, x, e, s);
  }

  lemma WpSound(c: Cmd, q: BExp, s: State)
    requires Holds(Wp(c, q), s)
    ensures Holds(q, Exec(c, s))
    decreases c
  {
    match c
    case Assign(x, e) => SubstBOk(q, x, e, s);
    case Seq(c1, c2) =>
      WpSound(c1, Wp(c2, q), s);
      WpSound(c2, q, Exec(c1, s));
    case If(b, c1, c2) =>
      if Holds(b, s) {
        WpSound(c1, q, s);
      } else {
        assert Holds(Not(b), s);
        WpSound(c2, q, s);
      }
  }

  lemma WpSoundEmpty(c: Cmd, q: BExp, s: State)
    requires Holds(Wp(c, q), s)
    ensures Holds(q, Exec(c, s))
    decreases c
  {}

  function Swap(): Cmd
  {
    Seq(Assign(0, Plus(Var(0), Var(1))), Seq(Assign(1, Minus(Var(0), Var(1))), Assign(0, Minus(Var(0), Var(1)))))
  }

  // x0 <= x1 before the swap gives x1 <= x0 after it.
  lemma SwapOrders(s: State)
    requires s(0) <= s(1)
    ensures Exec(Swap(), s)(1) <= Exec(Swap(), s)(0)
  {
    var post := Le(Var(1), Var(0));
    assert Holds(Wp(Swap(), post), s);
    WpSound(Swap(), post, s);
  }
}
```

`probe/q08/wp_hand_d.dfy`

```dafny
module ProbeWpHand {
  // wp(x := x + 1; if x > 0 then y := x else y := 0, y > 0), by hand, against a direct semantics
  lemma Check(x: int)
    ensures (var x1 := x + 1; var y := if x1 > 0 then x1 else 0; y > 0) <==> x >= 0
  {}
}
```

### A.9 Q08 flagship references (agent twins)

*Revised: the Dafny statements are now methods (A.15 `m7_flag_statements.dfy`, `m7_flag_delivery.dfy`); `flag_v.rs`'s `high_limbs` below fails at the agent path on seeds 1–3, and A.15 gives the repaired proof.*

`probe/agent/flag_d.dfy`

```dafny
// candidate reference delivery for Q08's flagship (Dafny): limb shifts and splits
module {:disableNonlinearArithmetic} Q08_FlagProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod
  import Power = Std.Arithmetic.Power

  function Zeros(k: nat): seq<nat>
    decreases k
  {
    if k == 0 then [] else [0] + Zeros(k - 1)
  }

  // --- the learner's statements (signatures and lemmas) ---
  function ShiftLimbs(a: seq<nat>, k: nat): seq<nat>
  {
    if |a| == 0 then [] else Zeros(k) + a
  }

  function LowLimbs(a: seq<nat>, k: nat): seq<nat>
  {
    if k <= |a| then a[..k] else a
  }

  function HighLimbs(a: seq<nat>, k: nat): seq<nat>
  {
    if k <= |a| then a[k..] else []
  }

  // --- the contractor's proofs ---
  lemma {:induction false} ToNatAppendL(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
      LemmaMulBasics(ToNat(b));
    } else {
      assert (a + b)[1..] == a[1..] + b;
      ToNatAppendL(a[1..], b);
      LemmaMulIsAssociative(BASE, Pow(|a| - 1), ToNat(b));
      LemmaMulIsDistributive(BASE, ToNat(a[1..]), Pow(|a| - 1) * ToNat(b));
    }
  }

  lemma {:induction false} ZerosFacts(k: nat)
    ensures |Zeros(k)| == k && Valid(Zeros(k)) && ToNat(Zeros(k)) == 0
    decreases k
  {
    if k > 0 {
      ZerosFacts(k - 1);
      ToNatCons(0, Zeros(k - 1));
      ValidCons(0, Zeros(k - 1));
    }
  }

  lemma ShiftLimbsCorrect(a: seq<nat>, k: nat)
    requires Valid(a)
    ensures Valid(ShiftLimbs(a, k)) && ToNat(ShiftLimbs(a, k)) == ToNat(a) * Pow(k)
  {
    if |a| == 0 {
      LemmaMulBasics(Pow(k));
    } else {
      ZerosFacts(k);
      ToNatAppendL(Zeros(k), a);
      LemmaMulIsCommutative(ToNat(a), Pow(k));
      assert Valid(Zeros(k) + a);
    }
  }

  lemma SplitCorrect(a: seq<nat>, k: nat)
    requires Valid(a)
    ensures Valid(LowLimbs(a, k)) && Valid(HighLimbs(a, k))
    ensures ToNat(a) == ToNat(LowLimbs(a, k)) + Pow(k) * ToNat(HighLimbs(a, k))
    ensures ToNat(LowLimbs(a, k)) < Pow(k)
  {
    if k <= |a| {
      assert a == a[..k] + a[k..];
      ToNatAppendL(a[..k], a[k..]);
      ToNatBound(a[..k]);
    } else {
      ToNatBound(a);
      PowIsStdPow(|a|);
      PowIsStdPow(k);
      Power.LemmaPowStrictlyIncreases(BASE, |a|, k);
      LemmaMulBasics(Pow(k));
    }
  }
}
```

`probe/agent/flag_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

pub open spec fn zeros(k: nat) -> Seq<u64>
    decreases k,
{
    if k == 0 { Seq::empty() } else { zeros((k - 1) as nat).push(0u64) }
}

proof fn lemma_zeros(k: nat)
    ensures zeros(k).len() == k, seq_to_nat(zeros(k)) == 0,
    decreases k,
{
    if k > 0 {
        lemma_zeros((k - 1) as nat);
        lemma_seq_to_nat_push_zero(zeros((k - 1) as nat));
    }
}

proof fn lemma_weight_pos(k: nat)
    ensures weight(k) > 0,
{
    lemma_weight_zero();
    lemma_weight_mono(0, k);
}

/// Multiply by weight(k): k zero limbs below the value (zero stays empty).
pub fn shift_limbs(a: &BigNat, k: usize) -> (r: BigNat)
    requires a.wf(),
    ensures r.wf(), r.to_nat() == a.to_nat() * weight(k as nat),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    if n == 0 {
        proof { lemma_mul_basics(weight(k as nat) as int); }
        return BigNat { limbs: v };
    }
    let mut i: usize = 0;
    while i < k
        invariant i <= k, v@ =~= zeros(i as nat),
        decreases k - i,
    {
        v.push(0);
        i = i + 1;

    }
    let mut j: usize = 0;
    while j < n
        invariant j <= n, n == a@.len(), v@ =~= zeros(k as nat) + a@.subrange(0, j as int),
        decreases n - j,
    {
        v.push(a.limbs[j]);
        j = j + 1;
        proof { assert(v@ =~= zeros(k as nat) + a@.subrange(0, j as int)); }
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        lemma_zeros(k as nat);
        lemma_seq_to_nat_append(zeros(k as nat), a@);
        lemma_mul_is_commutative(weight(k as nat) as int, a.to_nat() as int);
    }
    BigNat { limbs: v }
}

/// Divide by weight(k): drop the k lowest limbs.
pub fn high_limbs(a: &BigNat, k: usize) -> (r: BigNat)
    requires a.wf(),
    ensures r.wf(), r.to_nat() == a.to_nat() / weight(k as nat),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    proof { lemma_weight_pos(k as nat); }
    if k >= n {
        proof {
            broadcast use group_bignat_bounds;
            lemma_weight_mono(n as nat, k as nat);
            lemma_basic_div_specific_divisor(weight(k as nat) as int);
        }
        return BigNat { limbs: v };
    }
    let mut j: usize = k;
    while j < n
        invariant k <= j <= n, n == a@.len(), v@ =~= a@.subrange(k as int, j as int),
        decreases n - j,
    {
        v.push(a.limbs[j]);
        j = j + 1;
    }
    proof {
        let lo = a@.subrange(0, k as int);
        let hi = a@.subrange(k as int, n as int);
        assert(lo + hi =~= a@);
        lemma_seq_to_nat_append(lo, hi);
        broadcast use group_bignat_bounds;
        assert(seq_to_nat(lo) < weight(k as nat));
        lemma_fundamental_div_mod_converse(a.to_nat() as int, weight(k as nat) as int, seq_to_nat(hi) as int, seq_to_nat(lo) as int);
        assert(v@ =~= hi);
    }
    BigNat { limbs: v }
}

} // verus!
```

### A.10 Q09 brittleness and trigger probes

`t1on_d.dfy` and `t1atton_d.dfy` are `t1_d.dfy` and `t1att_d.dfy` with the module attribute removed (modules `Q09T1DOn`, `Q09T1AttOn`). `var_d.dfy` (24 variants, 303 lines), `s1_d.dfy`, `s2_d.dfy`, `nl_d.dfy`, `loop_v.rs`, `loop20_v.rs`, `split_v.rs`, `trig5_v.rs`, `trig6_d.dfy` are summarized in §0.3 and not reproduced.

`probe/q09/h1_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q09H1D {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // the repair: library facts, one step each
  lemma ProductBelowSquare(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    LemmaMulLeftInequality(p, y, p);
    if x == 0 {
      LemmaMulBasics(y);
      LemmaMulStrictlyPositive(p, p);
    } else {
      LemmaMulLeftInequality(x, y, p);
      LemmaMulStrictInequality(x, p, p);
    }
  }
}
```

`probe/q09/h1_nl_d.dfy`

```dafny
module Q09H1DNl {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // the quoted attempt, under the module's default (nonlinear arithmetic on)
  lemma ProductBelowSquareAttempt(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= x * p;
  }
}
```

`probe/q09/s3_d.dfy`

```dafny
module Q09S3 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import Mul = Std.Arithmetic.Mul

  lemma P0(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {}

  lemma P1(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= x * p;
  }

  lemma P2(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= x * p;
    assert x * p < p * p;
  }

  lemma Q0(x: nat, y: nat, p: nat)
    requires x < p && y < p
    ensures x * y < p * p
  {}

  lemma Q1(x: nat, y: nat, p: nat)
    requires x < p && y < p
    ensures x * y < p * p
  {
    assert x * y <= x * p;
  }

  lemma R0(x: nat, y: nat, c: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && c < Pow(n)
    ensures x * y + c < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= x * (p - 1);
    assert x * (p - 1) <= (p - 1) * (p - 1);
  }

  lemma R1(x: nat, y: nat, c: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && c < Pow(n)
    ensures x * y + c < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= (p - 1) * (p - 1);
  }
}
```

`probe/q09/t1_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q09T1D {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  lemma GrowsAttempt(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k) * BASE <= Pow(k + 1) {
      PowAdd(k, 1);
    }
    if m + 1 < n {
      GrowsAttempt(m + 1, n);
    }
  }

  lemma GrowsRewrite(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k) * BASE <= Pow(k + 1) {
      assert Pow(k + 1) == BASE * Pow(k);
    }
    if m + 1 < n {
      GrowsRewrite(m + 1, n);
      PowAdd(m + 1, 0);
    }
  }
}
```

`probe/q09/t1att_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q09T1D {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  lemma GrowsAttempt(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k) * BASE <= Pow(k + 1) {
      PowAdd(k, 1);
    }
    if m + 1 < n {
      GrowsAttempt(m + 1, n);
    }
  }
}
```

`probe/q09/t1att_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub proof fn mono_strict_attempt(m: nat, n: nat)
    requires m < n,
    ensures weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| #[trigger] weight(k) < weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        mono_strict_attempt(m + 1, n);
    }
}

} // verus!
```

`probe/q09/trig_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// attempt: a quantified step whose trigger makes a new trigger term
pub proof fn mono_attempt(m: nat, n: nat)
    requires m < n,
    ensures weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| #[trigger] weight(k) < weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        mono_attempt(m + 1, n);
    }
}

// trigger rewritten on the successor term
pub proof fn mono_rewrite(m: nat, n: nat)
    requires m < n,
    ensures weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| weight(k) < #[trigger] weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        mono_rewrite(m + 1, n);
    }
}

// no quantifier: the one step this call needs
pub proof fn mono_explicit(m: nat, n: nat)
    requires m < n,
    ensures weight(m) < weight(n),
    decreases n - m,
{
    lemma_weight_succ(m);
    lemma_weight_mono(0, m);
    lemma_weight_zero();
    if m + 1 < n {
        mono_explicit(m + 1, n);
        lemma_weight_mono(m + 1, n);
    }
}

} // verus!
```

`probe/q09/trig3_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q09TrigD3 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import Power = Std.Arithmetic.Power

  lemma PowPos(k: nat)
    ensures Pow(k) > 0
  {
    PowIsStdPow(k);
    Power.LemmaPowPositive(BASE, k);
  }

  lemma MonoAttempt(m: nat, n: nat)
    requires m < n
    ensures Pow(m) < Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k) < Pow(k + 1) {
      PowPos(k);
    }
    if m + 1 < n {
      MonoAttempt(m + 1, n);
    }
  }

  lemma MonoRewrite(m: nat, n: nat)
    requires m < n
    ensures Pow(m) < Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k) < Pow(k + 1) {
      PowPos(k);
    }
    if m + 1 < n {
      MonoRewrite(m + 1, n);
    }
  }

  lemma MonoNoQuant(m: nat, n: nat)
    requires m < n
    ensures Pow(m) < Pow(n)
    decreases n - m
  {
    PowPos(m);
    if m + 1 < n {
      MonoNoQuant(m + 1, n);
    }
  }
}
```

`probe/q09/trig4_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

pub proof fn plus_two_attempt(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
        lemma_weight_succ(k);
    }
    assert(weight(n + 2) == weight(n + 1) * BASE);
    assert(weight(n + 1) == weight(n) * BASE);
}

pub proof fn plus_two_rewrite(n: nat)
    ensures weight(n + 2) == BASE * BASE * weight(n),
{
    assert forall|k: nat| weight(k) * BASE == #[trigger] weight(k + 1) by {
        lemma_weight_succ(k);
    }
    assert(weight(n + 2) == weight(n + 1) * BASE);
    assert(weight(n + 1) == weight(n) * BASE);
}

pub proof fn mono_strict_attempt(m: nat, n: nat)
    requires m < n,
    ensures weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| #[trigger] weight(k) < weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        mono_strict_attempt(m + 1, n);
    }
}

} // verus!
```

`probe/q09/h1v_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// Q09.H1v reference candidate
pub proof fn lemma_product_below_square(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y <= x * p) by (nonlinear_arith) requires y < p;
    assert(x * p < p * p) by (nonlinear_arith) requires x < p;
}

// Q09.H1v quoted attempt candidate
pub proof fn lemma_product_below_square_attempt(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y < p * p) by (nonlinear_arith);
}

} // verus!
```

`probe/q09/nl_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

proof fn v4(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(2 * n),
{
    let p = weight(n);
    lemma_weight_add(n, n);
    assert(x * y < p * y || y == 0) by (nonlinear_arith) requires x < p;
    assert(p * y <= p * p) by (nonlinear_arith) requires y < p;
}

proof fn v6(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(2 * n),
{
    let p = weight(n);
    lemma_weight_add(n, n);
    assert(x * y <= x * p) by (nonlinear_arith) requires y < p;
    assert(x * p < p * p) by (nonlinear_arith) requires x < p;
}

proof fn v7(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(2 * n),
{
    let p = weight(n);
    lemma_weight_add(n, n);
    assert(x * y < p * p) by (nonlinear_arith) requires x < p, y < p;
}

proof fn v8(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y < weight(2 * n),
{
    let p = weight(n);
    lemma_weight_add(n, n);
    assert(x * y < p * p) by (nonlinear_arith) requires x < p, y < p, x * y >= 0;
    assert(x * y + x + y < p * p + 2 * p) by (nonlinear_arith) requires x < p, y < p;
}

proof fn b1(x: u64, y: u64, c: u64, d: u64)
    ensures (x as nat) * (y as nat) + (c as nat) + (d as nat) < BASE * BASE,
{
    assert((x as nat) * (y as nat) <= 0xFFFF_FFFF_FFFF_FFFFnat * 0xFFFF_FFFF_FFFF_FFFFnat) by (nonlinear_arith)
        requires x <= 0xFFFF_FFFF_FFFF_FFFFu64, y <= 0xFFFF_FFFF_FFFF_FFFFu64;
}

} // verus!
```

`probe/q09/split2_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

pub proof fn sum_prod_one(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y + x + y < weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y + x + y < p * p) by (nonlinear_arith) requires x < p, y < p;
}

pub proof fn sum_prod_split(x: nat, y: nat, n: nat)
    requires x < weight(n), y < weight(n),
    ensures x * y + x + y < weight(n) * weight(n),
{
    let p = weight(n);
    assert((x + 1) * (y + 1) <= p * p) by (nonlinear_arith) requires x + 1 <= p, y + 1 <= p;
    assert((x + 1) * (y + 1) == x * y + x + y + 1) by (nonlinear_arith);
}

pub proof fn three_sum_prod_one(x: nat, y: nat, z: nat, p: nat)
    requires x < p, y < p, z < p,
    ensures x * y * z + x * y + y * z + x * z + x + y + z < p * p * p,
{
    assert(x * y * z + x * y + y * z + x * z + x + y + z < p * p * p) by (nonlinear_arith) requires x < p, y < p, z < p;
}

pub proof fn three_sum_prod_split(x: nat, y: nat, z: nat, p: nat)
    requires x < p, y < p, z < p,
    ensures x * y * z + x * y + y * z + x * z + x + y + z < p * p * p,
{
    assert((x + 1) * (y + 1) <= p * p) by (nonlinear_arith) requires x + 1 <= p, y + 1 <= p;
    assert((x + 1) * (y + 1) * (z + 1) <= p * p * p) by (nonlinear_arith) requires (x + 1) * (y + 1) <= p * p, z + 1 <= p;
    assert((x + 1) * (y + 1) * (z + 1) == x * y * z + x * y + y * z + x * z + x + y + z + 1) by (nonlinear_arith);
}

} // verus!
```

`probe/q09/hj_d.dfy`

```dafny
module ProbeHoleJsonD {
  lemma Proved(x: nat) ensures x + 0 == x {}
  lemma Open(x: nat) ensures x * 1 == x
}
```

`probe/q09/hj_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn proved(x: nat) ensures x + 0 == x, {}

proof fn open_one(x: nat) ensures x * 1 == x,
{
    #[verifier::proof_note("probe")]
    assume(false);
}

} // verus!
```

### A.11 Q09 red-team banks (agent twins)

`probe/agent/bank_d.dfy`

```dafny
module {:disableNonlinearArithmetic} Q09_BankProbe {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  function Max(x: nat, y: nat): nat { if x < y then y else x }

  lemma {:induction false} AddCLength(a: seq<nat>, b: seq<nat>, c: nat)
    ensures |AddC(a, b, c)| <= Max(|a|, |b|) + 1
    decreases |a| + |b|
  {
    reveal AddC();
    if |a| != 0 || |b| != 0 {
      var t := Head(a) + Head(b) + c;
      AddCLength(Tail(a), Tail(b), if t < BASE then 0 else 1);
    }
  }

  lemma AddLengthBound(a: seq<nat>, b: seq<nat>)
    ensures |Add(a, b)| <= Max(|a|, |b|) + 1
  {
    AddCLength(a, b, 0);
  }

  lemma MulLimbByZero(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(MulLimb(s, 0)) == 0
  {
    MulLimbCorrect(s, 0);
    MulZero(ToNat(s), 0);
  }

  lemma CmpAntisymmetric(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Cmp(a, b) == -Cmp(b, a)
  {
    CmpCorrect(a, b);
    CmpCorrect(b, a);
  }

  // the planted statement (false) and its refutation
  lemma {:fuel Cmp, 4} CmpZeroMeansEqualRefuted()
    ensures Valid([1, 0]) && Valid([1]) && Cmp([1, 0], [1]) == 0 && [1, 0] != [1]
  {
  }
}
```

`probe/agent/bank_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn lemma_canonical_value_positive(s: Seq<u64>)
    requires seq_wf(s), s.len() > 0,
    ensures seq_to_nat(s) > 0,
{
    broadcast use group_bignat_bounds;
    lemma_weight_zero();
    lemma_weight_mono(0, (s.len() - 1) as nat);
}

proof fn lemma_two_limbs_value(a: u64, b: u64)
    ensures seq_to_nat(seq![a, b]) == a + BASE * b,
{
    reveal_with_fuel(seq_to_nat, 3);
    assert(seq![a, b].drop_first() =~= seq![b]);
    assert(seq![b].drop_first() =~= Seq::<u64>::empty());
}

proof fn lemma_sum_le_add(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a) <= seq_to_nat(a + b),
{
    lemma_seq_to_nat_append(a, b);
}

// the planted statement (false) and its refutation
proof fn refute_equal_values_equal_limbs()
    ensures
        seq_to_nat(seq![1u64, 0u64]) == seq_to_nat(seq![1u64]),
        !(seq![1u64, 0u64] =~= seq![1u64]),
{
    reveal_with_fuel(seq_to_nat, 3);
    assert(seq![1u64, 0u64].drop_first() =~= seq![0u64]);
    assert(seq![0u64].drop_first() =~= Seq::<u64>::empty());
    assert(seq![1u64].drop_first() =~= Seq::<u64>::empty());
    assert(seq![1u64, 0u64].len() != seq![1u64].len());
}

} // verus!
```

### A.12 Q07 prediction probes

`fueloff_d.dfy` and `bvoff_d.dfy` are `fuel_d.dfy` and `bv_d.dfy` with `{:disableNonlinearArithmetic}` on the module (modules `ProbeFuelDOff`, `ProbeBvDOff`).

`probe/q07/fuel_d.dfy`

```dafny
module ProbeFuelD {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  lemma A2(a: nat, b: nat)
    ensures ToNat([a, b]) == a + BASE * b
  {}

  lemma A3(a: nat, b: nat, c: nat)
    ensures ToNat([a, b, c]) == a + BASE * (b + BASE * c)
  {}

  lemma {:fuel ToNat, 4} A3fuel(a: nat, b: nat, c: nat)
    ensures ToNat([a, b, c]) == a + BASE * (b + BASE * c)
  {}

  lemma A4(a: nat, b: nat, c: nat, d: nat)
    ensures ToNat([a, b, c, d]) == a + BASE * (b + BASE * (c + BASE * d))
  {}

  lemma {:fuel ToNat, 5} A4fuel(a: nat, b: nat, c: nat, d: nat)
    ensures ToNat([a, b, c, d]) == a + BASE * (b + BASE * (c + BASE * d))
  {}

  lemma T2(a: nat, b: nat, s: seq<nat>)
    ensures ToNat([a, b] + s) == a + BASE * (b + BASE * ToNat(s))
  {}

  lemma {:fuel ToNat, 3} T2fuel(a: nat, b: nat, s: seq<nat>)
    ensures ToNat([a, b] + s) == a + BASE * (b + BASE * ToNat(s))
  {}
}
```

`probe/q07/fuel_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn a2(a: u64, b: u64)
    ensures seq_to_nat(seq![a, b]) == a + BASE * b,
{
}

proof fn a2fuel(a: u64, b: u64)
    ensures seq_to_nat(seq![a, b]) == a + BASE * b,
{
    reveal_with_fuel(seq_to_nat, 3);
}

proof fn a3fuel(a: u64, b: u64, c: u64)
    ensures seq_to_nat(seq![a, b, c]) == a + BASE * (b + BASE * c),
{
    reveal_with_fuel(seq_to_nat, 4);
}

proof fn t2(a: u64, b: u64, s: Seq<u64>)
    ensures seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
{
}

proof fn t2fuel(a: u64, b: u64, s: Seq<u64>)
    ensures seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
{
    reveal_with_fuel(seq_to_nat, 3);
}

} // verus!
```

`probe/q07/div_d.dfy`

```dafny
module ProbeDivD {
  lemma DivNeg()
    ensures (-7) / 2 == -4 && (-7) % 2 == 1
  {}
  lemma DivNegAlt()
    ensures (-7) / 2 == -3
  {}
}
```

`probe/q07/div_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn spec_div()
    ensures (-7int) / 2 == -4, (-7int) % 2 == 1,
{
}

fn exec_div(x: i64) -> (r: i64)
    requires x == -7,
    ensures r == -3,
{
    x / 2
}

fn exec_div_spec(x: i64) -> (r: i64)
    requires x == -7,
    ensures r == x / 2,
{
    x / 2
}

} // verus!
```

`probe/q07/digit_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn split_nl(p: u128)
    ensures (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
{
    assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (nonlinear_arith);
}

proof fn split_bv(p: u128)
    ensures (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
{
    assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (bit_vector);
}

proof fn split_compute(p: u128)
    ensures (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
{
    assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (compute);
}

proof fn split_plain(p: u128)
    ensures (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
{
}

} // verus!
```

`probe/q07/bv_d.dfy`

```dafny
module ProbeBvD {
  import opened QG_L1_BigNat

  method SplitWide(x: bv128) returns (hi: bv64, lo: bv64)
    ensures (hi as nat) * BASE + (lo as nat) == x as nat
  {
    hi := (x >> 64) as bv64;
    lo := (x & 0xFFFF_FFFF_FFFF_FFFF) as bv64;
  }

  method SplitWideEmptyProof(x: bv128) returns (hi: bv64, lo: bv64)
    ensures hi as bv128 == x >> 64 && lo as bv128 == x & 0xFFFF_FFFF_FFFF_FFFF
  {
    hi := (x >> 64) as bv64;
    lo := (x & 0xFFFF_FFFF_FFFF_FFFF) as bv64;
  }

  lemma MaskIsMod(x: bv64)
    ensures x & 0xFF == x % 256
  {}

  lemma JoinBits(hi: bv64, lo: bv64)
    ensures ((hi as bv128) << 64) | (lo as bv128) == ((hi as bv128) << 64) + (lo as bv128)
  {}
}
```

`probe/q07/comm_d.dfy`

```dafny
module {:disableNonlinearArithmetic} ProbeCommD {
  lemma Comm(x: nat, y: nat)
    ensures x * y == y * x
  {}
  lemma Dist(x: nat, y: nat, z: nat)
    ensures x * (y + z) == x * y + x * z
  {}
}
```

`probe/q07/comm_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn comm(x: int, y: int)
    ensures x * y == y * x,
{
}

proof fn dist(x: int, y: int, z: int)
    ensures x * (y + z) == x * y + x * z,
{
}

} // verus!
```

`probe/q07/iso2_d.dfy`

```dafny
module ProbeIso2D {
  lemma Plain(x: nat)
    ensures true
  {
    assert x == 1;
    assert x == 2;
    assert x == 3;
  }

  lemma {:isolate_assertions} Isolated(x: nat)
    ensures true
  {
    assert x == 1;
    assert x == 2;
    assert x == 3;
  }

  lemma Marked(x: nat)
    ensures true
  {
    assert x == 1;
    assert {:isolate} x == 2;
    assert x == 3;
  }
}
```

`probe/q07/noiso_d.dfy`

```dafny
module {:disableNonlinearArithmetic} ProbeNoIso {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  // Compiled loop form of Add.
  method AddLoopNoIso(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Add(a, b) && Valid(r) && ToNat(r) == ToNat(a) + ToNat(b)
  {
    var n := if |a| < |b| then |b| else |a|;
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    while i < n
      invariant 0 <= i <= n
      invariant carry <= 1
      invariant r + AddC(Drop(a, i), Drop(b, i), carry) == Add(a, b)
      decreases n - i
    {
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      var t := x + y + carry;
      var digit := if t < BASE then t else t - BASE;
      var c: nat := if t < BASE then 0 else 1;
      AddCDropStep(a, b, i, carry);
      ghost var rest := AddC(Drop(a, i + 1), Drop(b, i + 1), c);
      assert r + ([digit] + rest) == (r + [digit]) + rest;
      r := r + [digit];
      carry := c;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    reveal AddC();
    AddCorrect(a, b);
  }


  // Compiled loop form of MulLimb.
  method MulLimbLoopNoIso(s: seq<nat>, d: nat) returns (r: seq<nat>)
    requires Valid(s) && d < BASE
    ensures r == MulLimb(s, d) && Valid(r) && ToNat(r) == ToNat(s) * d
  {
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert s[0..] == s;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant r + MulLimbC(s[i..], d, carry) == MulLimb(s, d)
      decreases |s| - i
    {
      MulNonneg(s[i], d);
      assert s[i..][1..] == s[i + 1..];
      var t := s[i] * d + carry;
      r := r + [t % BASE];
      carry := t / BASE;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    MulLimbCorrect(s, d);
  }
}
```

`probe/q07/rec_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub open spec fn top(s: Seq<u64>) -> u64
    recommends s.len() > 0,
{
    s[s.len() - 1]
}

pub open spec(checked) fn top_checked(s: Seq<u64>) -> u64
    recommends s.len() > 0,
{
    s[s.len() - 1]
}

proof fn r1(s: Seq<u64>)
    ensures top(s) == s[s.len() - 1],
{
}

proof fn r2(s: Seq<u64>)
    ensures top(s) > 0,
{
}

proof fn r3(s: Seq<u64>)
    requires s.len() > 0, seq_wf(s),
    ensures top(s) > 0,
{
}

proof fn r4(s: Seq<u64>)
    ensures top_checked(s) == s[s.len() - 1],
{
}

proof fn r5(s: Seq<u64>)
    requires s.len() > 0,
    ensures top_checked(s) == s[s.len() - 1],
{
}

} // verus!
```

`probe/q07/rec2_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub open spec fn top(s: Seq<u64>) -> u64
    recommends s.len() > 0,
{
    s[s.len() - 1]
}

pub open spec(checked) fn below_top_a(s: Seq<u64>) -> u64 {
    top(s.drop_last())
}

pub open spec(checked) fn below_top_b(s: Seq<u64>) -> u64
    recommends s.len() > 1,
{
    top(s.drop_last())
}

pub open spec(checked) fn below_top_c(s: Seq<u64>) -> u64
    recommends s.len() > 0,
{
    top(s.drop_last())
}

pub open spec(checked) fn raw_index(s: Seq<u64>, i: int) -> u64 {
    s[i]
}

pub open spec fn unchecked_index(s: Seq<u64>, i: int) -> u64 {
    s[i]
}

} // verus!
```

### A.13 Q08 prediction probes

`probe/q08/refadd_d.dfy`

```dafny
abstract module ProbeRefSpec {
  lemma Bound(x: nat)
    requires x < 10
    ensures x < 20
}
module ProbeRefEns refines ProbeRefSpec {
  lemma Bound(x: nat)
    ensures x < 15
  {
  }
}
```

`probe/q08/refreq_d.dfy`

```dafny
abstract module ProbeRefSpec2 {
  lemma Bound(x: nat)
    requires x < 10
    ensures x < 20
}
module ProbeRefReq refines ProbeRefSpec2 {
  lemma Bound(x: nat)
    requires x < 5
  {
  }
}
```

`probe/q08/p3d_d.dfy`

```dafny
// Q08.P3d scenario: a refining lemma that recurses with its own decreases clause
module {:disableNonlinearArithmetic} Q08P3dProbe refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat
  type BigNat = seq<nat>
  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }
  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L2.Normalize(L4.Add(a, b)) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }
  lemma ZeroCorrect() {}
  lemma FromNatCorrect(n: nat)
    decreases n
  {
    L3.FromNatCorrect(n);
    if n >= L1.BASE { FromNatCorrect(n / L1.BASE); }
  }
  lemma AddCorrect(a: BigNat, b: BigNat) { L4.AddCorrect(a, b); L3.NormalizeToNat(L4.Add(a, b)); L3.NormalizeCanonical(L4.Add(a, b)); }
  lemma CmpCorrect(a: BigNat, b: BigNat) { L4.CmpCorrect(a, b); }
}
```

`probe/q08/timpl_a_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub trait Counter: Sized {
    spec fn count(&self) -> nat;

    fn bump(&mut self)
        requires
            old(self).count() < 100,
        ensures
            final(self).count() == old(self).count() + 1,
    ;
}

pub struct Small {
    pub n: u64,
}

impl Counter for Small {
    open spec fn count(&self) -> nat {
        self.n as nat
    }

    fn bump(&mut self)
        ensures
            final(self).n == old(self).n + 1,
    {
        self.n = self.n + 1;
    }
}

} // verus!
```

`probe/q08/timpl_b_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub trait Counter: Sized {
    spec fn count(&self) -> nat;

    fn bump(&mut self)
        requires
            old(self).count() < 100,
        ensures
            final(self).count() == old(self).count() + 1,
    ;
}

pub struct Small {
    pub n: u64,
}

impl Counter for Small {
    open spec fn count(&self) -> nat {
        self.n as nat
    }

    fn bump(&mut self)
        requires
            old(self).n < 50,
    {
        self.n = self.n + 1;
    }
}

} // verus!
```

`probe/q08/lin_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell::*;
use qg_bignat_l4::*;

verus! {

proof fn consume(tracked p: PointsTo<u64>) {
}

fn twice() {
    let (cell, Tracked(perm)) = PCell::new(5u64);
    proof {
        consume(perm);
        consume(perm);
    }
}

} // verus!
```

`probe/q08/lin_ghost_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

proof fn look(g: Seq<u64>) {
}

fn twice_ghost() {
    let ghost s: Seq<u64> = seq![1u64, 2u64];
    proof {
        look(s);
        look(s);
    }
}

} // verus!
```

`probe/q08/term_d.dfy`

```dafny
module ProbeTermD {
  datatype Tree = Leaf | Node(l: Tree, r: Tree)
  function Size(t: Tree): nat
  {
    match t
    case Leaf => 1
    case Node(l, r) => Size(l) + Size(r) + 1
  }
}
```

`probe/q08/term_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub enum Tree { Leaf, Node(Box<Tree>, Box<Tree>) }

pub open spec fn size(t: Tree) -> nat
{
    match t {
        Tree::Leaf => 1,
        Tree::Node(l, r) => size(*l) + size(*r) + 1,
    }
}

} // verus!
```

`probe/q08/impl_client2_v.rs`

```rust
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub trait Counter: Sized {
    spec fn count(&self) -> nat;
    fn bump(&mut self)
        requires old(self).count() < 100,
        ensures final(self).count() > old(self).count();
}

pub struct Small { pub n: u64 }

impl Counter for Small {
    open spec fn count(&self) -> nat { self.n as nat }
    fn bump(&mut self)
        ensures final(self).n == old(self).n + 1,
    {
        self.n = self.n + 1;
    }
}

fn client_concrete(s: &mut Small)
    requires old(s).n == 5,
    ensures final(s).n == 6,
{
    s.bump();
}

fn client_generic<C: Counter>(c: &mut C)
    requires old(c).count() == 5,
    ensures final(c).count() == 6,
{
    c.bump();
}

} // verus!
```

### A.14 The lane's drivers

Scratch tools of the plan lane, not course tools; they only clamp the memory cap or name the other bundled solver, and run the wrappers or `dvl` unchanged otherwise.

`drv/capped.py`

```python
"""Run a course tool (scripts/<tool>) with every dvl solver job's memory cap clamped to 8 GB.
Usage: python3 capped.py <root> <tool> args...   (lane dv3b plan; CLAUDE.md §Resources)"""
import os, runpy, sys
root, tool, *args = sys.argv[1:]
sys.path.insert(0, os.path.join(root, "scripts"))
import dvl.common as common
_orig = common.run_capped
def run_capped(argv, mem_gb, timeout_s, *a, **k):
    return _orig(argv, min(float(mem_gb), 8.0), timeout_s, *a, **k)
common.run_capped = run_capped
os.chdir(root)
sys.argv = [os.path.join(root, "scripts", tool)] + args
runpy.run_path(sys.argv[0], run_name="__main__")
```

`drv/eb.py`

```python
"""Empty-body gate driver (lane dv3b plan): dvl.<lang>.empty_body on named symbols, every
solver job's cap clamped to 8 GB. Usage: eb.py d|v <target> <symbol>[,<symbol>...] [modes] [seeds]"""
import os, sys, json
ROOT = "/tmp/dvl0-plan3b4-dv3b/root"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["DVL_SCRATCH"] = "/tmp/dvl0-plan3b4-dv3b/dvl"
import dvl.common as common
_orig = common.run_capped
def run_capped(argv, mem_gb, timeout_s, *a, **k):
    return _orig(argv, min(float(mem_gb), 8.0), timeout_s, *a, **k)
common.run_capped = run_capped
os.chdir(ROOT)
lang, target, syms = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
modes = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] != "-" else None
seeds = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else None
if lang == "d":
    import dvl.dafny as D
    for s in syms:
        r = D.empty_body(target, s)
        print(s, "=>", getattr(r, "verdict", r), json.dumps(getattr(r, "per_symbol", None)), [getattr(f, "kind", f) for f in getattr(r, "findings", [])], flush=True)
else:
    import dvl.verus as V
    for s in syms:
        kw = {}
        if modes: kw["modes"] = modes
        if seeds: kw["seeds"] = seeds
        tb = None
        if "=" in s:
            s, tb = s.split("=", 1)
            kw["triv_body"] = tb
        r = V.empty_body(target, s, **kw)
        print(s, "=>", getattr(r, "verdict", r), json.dumps(getattr(r, "per_symbol", None)), [getattr(f, "message", f)[:120] for f in getattr(r, "findings", [])][:3], flush=True)
```

`drv/res2.py`

```python
"""Verify one probe at the course pins (manual induction, std) with both bundled Z3s; print per-symbol
outcome and resource count. 8 GB cap via dvl.common.run_capped. Usage: res2.py probe.dfy [layers=3]"""
import os, sys, csv, shutil, tempfile
AUTH = "/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0-authoring"
ROOT = "/tmp/dvl0-plan3b4-dv3b/root"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["DVL_SCRATCH"] = "/tmp/dvl0-plan3b4-dv3b/dvl"
import dvl.common as common
DAFNY = os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/dafny")
Z3 = {"4.12.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1"),
      "4.14.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1")}
probe = sys.argv[1]; nl = int(sys.argv[2]) if len(sys.argv) > 2 else 3
seeds = sys.argv[3].split(",") if len(sys.argv) > 3 else [None]
layers = [os.path.join(ROOT, f"dafny/given/Q/QG_L{k}_BigNat.dfy") for k in range(1, nl + 1)]
out = {}
for z in ("4.12.1", "4.14.1"):
  for sd in seeds:
    d = tempfile.mkdtemp(dir="/tmp/dvl0-plan3b4-dv3b/swap")
    for f in layers + [probe]: shutil.copy(f, d)
    argv = [DAFNY, "verify", "--resource-limit", "5000000", "--cores", "2", "--allow-warnings", "false",
            "--allow-axioms", "false", "--solver-path", Z3[z], "--standard-libraries", "--manual-lemma-induction",
            "--log-format", "csv;LogFileName=log.csv"]
    if sd is not None:
        argv += ["--boogie", f"/proverOpt:O:smt.random_seed={sd}"]
    argv += [os.path.basename(f) for f in layers + [probe]]
    rc, sop, sep = common.run_capped(argv, 8, 1800, env=common.default_env(), cwd=d)
    so = open(sop).read()
    print(f"== z3 {z} seed {sd}: exit {rc}: {so.strip().splitlines()[-1] if so.strip() else ''}")
    stem = os.path.splitext(os.path.basename(probe))[0]
    for row in csv.DictReader(open(os.path.join(d, "log.csv"))):
        n = row["TestResult.DisplayName"]
        if n.startswith("QG_L"): continue
        print(f"   {n:55s} {row['TestResult.Outcome']:14s} {int(row['TestResult.ResourceCount']):>10d}")
```

`drv/res3.py`

```python
# res3: as res2, seeds through measure-complexity --random-seed S --mutations 1 (as vcheck, Delta 17)
"""Verify one probe at the course pins (manual induction, std) with both bundled Z3s; print per-symbol
outcome and resource count. 8 GB cap via dvl.common.run_capped. Usage: res2.py probe.dfy [layers=3]"""
import os, sys, csv, shutil, tempfile
AUTH = "/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0-authoring"
ROOT = "/tmp/dvl0-plan3b4-dv3b/root"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["DVL_SCRATCH"] = "/tmp/dvl0-plan3b4-dv3b/dvl"
import dvl.common as common
DAFNY = os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/dafny")
Z3 = {"4.12.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1"),
      "4.14.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1")}
probe = sys.argv[1]; nl = int(sys.argv[2]) if len(sys.argv) > 2 else 3
seeds = sys.argv[3].split(",") if len(sys.argv) > 3 else [None]
layers = [os.path.join(ROOT, f"dafny/given/Q/QG_L{k}_BigNat.dfy") for k in range(1, nl + 1)]
out = {}
for z in ("4.12.1", "4.14.1"):
  for sd in seeds:
    d = tempfile.mkdtemp(dir="/tmp/dvl0-plan3b4-dv3b/swap")
    for f in layers + [probe]: shutil.copy(f, d)
    argv = [DAFNY, "verify" if sd is None else "measure-complexity", "--resource-limit", "5000000", "--cores", "2", "--allow-warnings", "false",
            "--allow-axioms", "false", "--solver-path", Z3[z], "--standard-libraries", "--manual-lemma-induction",
            "--log-format", "csv;LogFileName=log.csv"]
    if sd is not None:
        argv += ["--random-seed", str(sd), "--mutations", "1"]
    argv += [os.path.basename(f) for f in layers + [probe]]
    rc, sop, sep = common.run_capped(argv, 8, 1800, env=common.default_env(), cwd=d)
    so = open(sop).read()
    print(f"== z3 {z} seed {sd}: exit {rc}: {so.strip().splitlines()[-1] if so.strip() else ''}")
    stem = os.path.splitext(os.path.basename(probe))[0]
    for row in csv.DictReader(open(os.path.join(d, "log.csv"))):
        n = row["TestResult.DisplayName"]
        if n.startswith("QG_L"): continue
        print(f"   {n:55s} {row['TestResult.Outcome']:14s} {int(row['TestResult.ResourceCount']):>10d}")
```

`drv/swap_survey.py`

```python
"""Solver-swap survey (lane dv3b plan): every Dafny reference twin of Q01-Q06 and the
L1-L4 layers, verified at the course pins with the bundled Z3 4.12.1 and with 4.14.1.
Each run goes through dvl.common.run_capped with an 8 GB cap, one job at a time."""
import os, re, shutil, sys, json, tempfile
AUTH = "/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0-authoring"
ROOT = "/tmp/dvl0-plan3b4-dv3b/root"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dvl.common as common
DAFNY = os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/dafny")
Z3 = {"4.12.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1"),
      "4.14.1": os.path.join(AUTH, ".toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1")}
GIVEN = os.path.join(ROOT, "dafny/given/Q")
L = {k: os.path.join(GIVEN, f"QG_L{k}_BigNat.dfy") for k in (1, 2, 3, 4)}
OUT = "/tmp/dvl0-plan3b4-dv3b/swap"

def plan(rel):
    m = re.search(r"Q0(\d)", rel)
    q = int(m.group(1)) if m else 0
    txt = open(os.path.join(AUTH, rel)).read()
    layers = [k for k in (1, 2, 3, 4) if f"QG_L{k}_BigNat" in txt]
    if not layers and rel.startswith("dafny/given"):
        layers = []
    std = ("Std." in txt) or any(k >= 3 for k in layers)
    chain = list(range(1, max(layers) + 1)) if layers else []
    manual = q >= 3
    return chain, std, manual

def run(files, std, manual, z3):
    argv = [DAFNY, "verify", "--resource-limit", "5000000", "--cores", "2", "--allow-warnings", "false",
            "--allow-axioms", "false", "--solver-path", Z3[z3], "--log-format", "csv;LogFileName=log.csv"]
    if std: argv += ["--standard-libraries"]
    if manual: argv += ["--manual-lemma-induction"]
    d = tempfile.mkdtemp(dir=OUT)
    for f in files:
        shutil.copy(f, d)
    argv += [os.path.basename(f) for f in files]
    os.environ["DVL_SCRATCH"] = "/tmp/dvl0-plan3b4-dv3b/dvl"
    rc, sop, sep = common.run_capped(argv, 8, 1800, env=common.default_env(), cwd=d)
    so = open(sop).read()
    rows = []
    csvp = os.path.join(d, "log.csv")
    if os.path.exists(csvp):
        rows = open(csvp).read().splitlines()
    return rc, so, rows, d

def main():
    targets = sys.argv[1:]
    res = {}
    for rel in targets:
        if rel.startswith("dafny/given"):
            chain, std, manual = [], True, True
        else:
            chain, std, manual = plan(rel)
        files = [L[k] for k in chain] + ([os.path.join(AUTH, rel)] if not rel.startswith("dafny/given") else [])
        if rel.startswith("dafny/given"):
            files = [L[k] for k in range(1, int(re.search(r"L(\d)", rel).group(1)) + 1)]
            std = int(re.search(r"L(\d)", rel).group(1)) >= 3
            manual = True
        r = {}
        for z in ("4.12.1", "4.14.1"):
            rc, so, rows, d = run(files, std, manual, z)
            summ = [l for l in so.splitlines() if "verified" in l and "error" in l]
            fails = [l for l in rows[1:] if ",Failed," in l or "OutOfResource" in l or ",Inconclusive," in l or "TimedOut" in l]
            r[z] = {"rc": rc, "summary": summ[-1] if summ else so.strip().splitlines()[-1:] , "fails": fails[:20], "dir": d}
        res[rel] = r
        print(rel, "|", r["4.12.1"]["rc"], r["4.12.1"]["summary"], "|", r["4.14.1"]["rc"], r["4.14.1"]["summary"], flush=True)
        for f in r["4.14.1"]["fails"]:
            print("   4.14.1 FAIL:", f[:220], flush=True)
        for f in r["4.12.1"]["fails"]:
            print("   4.12.1 FAIL:", f[:220], flush=True)
    json.dump(res, open(os.path.join(OUT, "survey.json"), "w"), indent=1)

main()
```

### A.15 Revision probes (2026-10-06, after the plan review)

Scratch `/tmp/dvl0-plan3b4-dv3brev/` (not archived). Each file verbatim as run; §R.1 gives the commands and results. The probe placed at a Q07 path is named in §R.1. Variants that differ from a file below by one line are described, not reproduced.

**Drivers.** `drv/capped.py`, `drv/eb.py`, `drv/res3.py` are A.14's with the scratch root renamed; two were added:

`drv/vc.sh`

```bash
#!/bin/bash
# vc.sh <tool> args... : run a course tool in the scratch root, every dvl job clamped to 8 GB (lane dv3brev)
export DVL_SCRATCH=/tmp/dvl0-plan3b4-dv3brev/dvl
exec python3 /tmp/dvl0-plan3b4-dv3brev/drv/capped.py /tmp/dvl0-plan3b4-dv3brev/root "$@"
```

`drv/ft.py`

```python
"""firsttry internals on the scratch root (lane dv3brev): lint-hollow problems, static holes and
exit_run for one exit file; every dvl job clamped to 8 GB. Usage: ft.py <ID> <exit rel> [lint|exit]"""
import os, sys, runpy, importlib.util, importlib.machinery
ROOT = "/tmp/dvl0-plan3b4-dv3brev/root"
os.environ["DVL_SCRATCH"] = "/tmp/dvl0-plan3b4-dv3brev/dvl"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dvl.common as common
_orig = common.run_capped
def run_capped(argv, mem_gb, timeout_s, *a, **k):
    return _orig(argv, min(float(mem_gb), 8.0), timeout_s, *a, **k)
common.run_capped = run_capped
os.chdir(ROOT)
loader = importlib.machinery.SourceFileLoader("firsttry", os.path.join(ROOT, "scripts", "firsttry.py"))
spec = importlib.util.spec_from_loader("firsttry", loader)
ft = importlib.util.module_from_spec(spec); sys.modules["firsttry"] = ft; loader.exec_module(ft)
mid, rel, what = sys.argv[1], sys.argv[2], sys.argv[3]
ctx = ft.Ctx(ROOT, mid, lenient=True)
items = [i for i in ctx.items_in([rel])]
print("items:", [(i["id"], i["kind"], i["line_start"], i["line_end"]) for i in items])
if what == "lint":
    text = ctx.text(rel)
    for it in items:
        print(it["id"], "static_holes:", ft.static_holes(text, rel, it, ctx.root))
    for f in ft.lint_file(ctx.root, rel):
        print("lint:", f.line, f.kind)
    print("lint_hollow problems (whole module):")
    for p in ft.lint_hollow_module(ctx):
        if rel in p: print("  ", p)
else:
    xs = [i for i in items if i["kind"] == "X"]
    print(ft.exit_run(ctx, rel, xs))
```

**§R.1 #1: the refinement-hole form (Q08.X1d's new scaffold, and a second refiner).**


`probe/b1_exit_shipped.dfy`

```dafny
/*!
# probe (lane dv3brev): QPLAN §14.0's refinement hole in the `assume false` body form,
# two refiners of QG_L4_Spec in one learner file, at a learner exit path.
*/
module {:disableNonlinearArithmetic} Q08_ExitRev refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  // Given: reversal and its two lemmas.
  function Rev(x: seq<nat>): seq<nat>
    decreases |x|
  {
    if |x| == 0 then [] else Rev(x[1..]) + [x[0]]
  }

  lemma RevAppend(x: seq<nat>, y: seq<nat>)
    ensures Rev(x + y) == Rev(y) + Rev(x)
    decreases |x|
  {
    if |x| == 0 {
      assert x + y == y;
    } else {
      assert (x + y)[1..] == x[1..] + y;
      RevAppend(x[1..], y);
    }
  }

  lemma RevRev(x: seq<nat>)
    ensures Rev(Rev(x)) == x
    decreases |x|
  {
    if |x| != 0 {
      RevAppend(Rev(x[1..]), [x[0]]);
      RevRev(x[1..]);
      assert Rev([x[0]]) == [x[0]];
      assert [x[0]] + x[1..] == x;
    }
  }

  // Given: the limbs of n, most significant first, and their reversal.
  function FromNatMsf(n: nat): seq<nat>
    decreases n
  {
    if n == 0 then [] else FromNatMsf(n / L1.BASE) + [n % L1.BASE]
  }

  lemma FromNatMsfRev(n: nat)
    ensures Rev(FromNatMsf(n)) == L2.FromNat(n)
    decreases n
  {
    if n != 0 {
      FromNatMsfRev(n / L1.BASE);
      RevAppend(FromNatMsf(n / L1.BASE), [n % L1.BASE]);
      assert Rev([n % L1.BASE]) == [n % L1.BASE];
    }
  }

  ghost function Val(x: BigNat): nat { L1.ToNat(Rev(x)) }
  ghost predicate Wf(x: BigNat) { L1.Valid(Rev(x)) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { FromNatMsf(n) }
  function Add(a: BigNat, b: BigNat): BigNat { Rev(L4.Add(Rev(a), Rev(b))) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(Rev(a), Rev(b)) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    FromNatMsfRev(n);
    L3.FromNatCorrect(n);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(Rev(a), Rev(b));
  }

  // item: Q07.X1d S6
  /** **X1.** Prove the inherited statement:
      `Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)` for `Wf(a) && Wf(b)`. */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    assume false;
  }
}

module {:disableNonlinearArithmetic} Q08_CanonProbe refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>
  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L1.Valid(x) && L2.Canonical(x) }
  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.Normalize(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { L2.Normalize(L4.Add(a, b)) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L3.NormalizeToNat(L2.FromNat(n));
    L3.NormalizeCanonical(L2.FromNat(n));
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }

  // item: Q07.X2d S6
  /** **X2.** Prove the inherited statement for this refinement. */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    assume false;
  }
}
```

`probe/b1_exit_filled.dfy` is the same file with the two `assume false;` bodies replaced by the references: X1d (`Q08_ExitRev.AddCorrect`)

```dafny
    RevRev(L4.Add(Rev(a), Rev(b)));
    L4.AddCorrect(Rev(a), Rev(b));
```

and the canonical refiner's `AddCorrect` (H1d's reference, here as a probe)

```dafny
    L4.AddCorrect(a, b);
    L3.NormalizeToNat(L4.Add(a, b));
    L3.NormalizeCanonical(L4.Add(a, b));
```

The single-call variant replaces X1d's body by `L4.AddCorrect(Rev(a), Rev(b));` only.


**§R.1 #2: the red-team banks as correct deliveries.**


`probe/b2_bank_delivered.dfy`

```dafny
// probe (lane dv3brev): Q09's Dafny red-team bank as a correct delivery: three proved, the false
// lemma left exactly as shipped, a refutation under REFUTATIONS
module {:disableNonlinearArithmetic} Q09_AgentRedTeam {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  function Max(x: nat, y: nat): nat { if x < y then y else x }

  // BANK
  lemma AddLengthBound(a: seq<nat>, b: seq<nat>)
    ensures |Add(a, b)| <= Max(|a|, |b|) + 1
  {
    AddCLength(a, b, 0);
  }

  lemma MulLimbByZero(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(MulLimb(s, 0)) == 0
  {
    MulLimbCorrect(s, 0);
    MulZero(ToNat(s), 0);
  }

  lemma CmpAntisymmetric(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Cmp(a, b) == -Cmp(b, a)
  {
    CmpCorrect(a, b);
    CmpCorrect(b, a);
  }

  lemma CmpZeroMeansEqual(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Cmp(a, b) == 0 ==> a == b

  // REFUTATIONS
  lemma {:fuel Cmp, 4} CmpZeroMeansEqualRefuted()
    ensures Valid([1, 0]) && Valid([1]) && Cmp([1, 0], [1]) == 0 && [1, 0] != [1]
  {
  }

  // HELPERS
  lemma {:induction false} AddCLength(a: seq<nat>, b: seq<nat>, c: nat)
    ensures |AddC(a, b, c)| <= Max(|a|, |b|) + 1
    decreases |a| + |b|
  {
    reveal AddC();
    if |a| != 0 || |b| != 0 {
      var t := Head(a) + Head(b) + c;
      AddCLength(Tail(a), Tail(b), if t < BASE then 0 else 1);
    }
  }
}
```

`probe/b2_bank_shipped.dfy` (the freeze snapshot, `research/q09_bank.dfy`): the same header and `Max`, the four `BANK` lemmas bodyless, an empty `REFUTATIONS` section, no helper.


`probe/b2_bank_delivered.rs`

```rust
//! probe (lane dv3brev): Q09's Verus red-team bank as a correct delivery: three proved, the
//! false lemma left as shipped (its labelled assume), a refutation under REFUTATIONS
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// BANK
pub proof fn lemma_canonical_value_positive(s: Seq<u64>)
    requires seq_wf(s), s.len() > 0,
    ensures seq_to_nat(s) > 0,
{
    broadcast use group_bignat_bounds;
    lemma_weight_zero();
    lemma_weight_mono(0, (s.len() - 1) as nat);
}

pub proof fn lemma_two_limbs_value(a: u64, b: u64)
    ensures seq_to_nat(seq![a, b]) == a + BASE * b,
{
    reveal_with_fuel(seq_to_nat, 3);
    assert(seq![a, b].drop_first() =~= seq![b]);
    assert(seq![b].drop_first() =~= Seq::<u64>::empty());
}

pub proof fn lemma_sum_le_add(a: Seq<u64>, b: Seq<u64>)
    ensures seq_to_nat(a) <= seq_to_nat(a + b),
{
    lemma_seq_to_nat_append(a, b);
}

pub proof fn lemma_equal_values_equal_limbs(a: Seq<u64>, b: Seq<u64>)
    requires seq_to_nat(a) == seq_to_nat(b),
    ensures a =~= b,
{
    #[verifier::proof_note("Q09.A1v")] assume(false);
}

// REFUTATIONS
pub proof fn refute_equal_values_equal_limbs()
    ensures
        seq_to_nat(seq![1u64, 0u64]) == seq_to_nat(seq![1u64]),
        !(seq![1u64, 0u64] =~= seq![1u64]),
{
    reveal_with_fuel(seq_to_nat, 3);
    assert(seq![1u64, 0u64].drop_first() =~= seq![0u64]);
    assert(seq![0u64].drop_first() =~= Seq::<u64>::empty());
    assert(seq![1u64].drop_first() =~= Seq::<u64>::empty());
    assert(seq![1u64, 0u64].len() != seq![1u64].len());
}

} // verus!
```

`probe/b2_bank_shipped.rs` (`research/q09_bank.rs`): the same four statements, each body the one line `#[verifier::proof_note("Q09.A1v")] assume(false);`, an empty `REFUTATIONS` section.


**§R.1 #3: Q07's new refactor targets.**


`probe/m2_agent_mono.dfy`

```dafny
// probe (lane dv3brev): candidate shipped state of Q07's Dafny refactor file (monolithic)
module {:disableNonlinearArithmetic} Q07_AgentRefactor {
  import opened QG_L1_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // FROZEN

  // Two numbers scaled by one limb, then added: the sum scaled.
  lemma ScaledSum(s: seq<nat>, t: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && d < BASE
    ensures Valid(Add(MulLimb(s, d), MulLimb(t, d)))
    ensures ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == (ToNat(s) + ToNat(t)) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(t, d);
    assert Valid(MulLimb(t, d)) && ToNat(MulLimb(t, d)) == ToNat(t) * d;
    AddCorrect(MulLimb(s, d), MulLimb(t, d));
    assert ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == ToNat(s) * d + ToNat(t) * d;
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
    assert (ToNat(s) + ToNat(t)) * d == ToNat(s) * d + ToNat(t) * d;
  }

  // Three numbers scaled by one limb, then added left to right: the sum scaled.
  lemma ScaledSumThree(s: seq<nat>, t: seq<nat>, u: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && Valid(u) && d < BASE
    ensures Valid(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
    ensures ToNat(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
              == (ToNat(s) + ToNat(t) + ToNat(u)) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(t, d);
    assert Valid(MulLimb(t, d)) && ToNat(MulLimb(t, d)) == ToNat(t) * d;
    MulLimbCorrect(u, d);
    assert Valid(MulLimb(u, d)) && ToNat(MulLimb(u, d)) == ToNat(u) * d;
    AddCorrect(MulLimb(s, d), MulLimb(t, d));
    assert ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == ToNat(s) * d + ToNat(t) * d;
    AddCorrect(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d));
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
    assert (ToNat(s) + ToNat(t)) * d == ToNat(s) * d + ToNat(t) * d;
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s) + ToNat(t), ToNat(u));
    assert (ToNat(s) + ToNat(t) + ToNat(u)) * d == (ToNat(s) + ToNat(t)) * d + ToNat(u) * d;
  }

  // API

  // Scaling twice is scaling by the product.
  lemma ScaleTwice(s: seq<nat>, d: nat, e: nat)
    requires Valid(s) && d < BASE && e < BASE
    ensures Valid(MulLimb(MulLimb(s, d), e))
    ensures ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * (d * e)
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(MulLimb(s, d), e);
    assert ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * d * e;
    LemmaMulIsAssociative(ToNat(s), d, e);
  }

  // A number plus another scaled by one limb.
  lemma AddScaled(a: seq<nat>, s: seq<nat>, d: nat)
    requires Valid(a) && Valid(s) && d < BASE
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == ToNat(a) + ToNat(s) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    AddCorrect(a, MulLimb(s, d));
  }
}
```

`probe/m2_agent_refactored.dfy`

```dafny
// probe (lane dv3brev): a reference refactor of the candidate (helpers under HELPERS)
module {:disableNonlinearArithmetic} Q07_AgentRefactor {
  import opened QG_L1_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // FROZEN

  lemma ScaledSum(s: seq<nat>, t: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && d < BASE
    ensures Valid(Add(MulLimb(s, d), MulLimb(t, d)))
    ensures ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == (ToNat(s) + ToNat(t)) * d
  {
    MulLimbCorrect(s, d);
    AddScaledValue(MulLimb(s, d), t, d, ToNat(s) * d);
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
  }

  lemma ScaledSumThree(s: seq<nat>, t: seq<nat>, u: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && Valid(u) && d < BASE
    ensures Valid(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
    ensures ToNat(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
              == (ToNat(s) + ToNat(t) + ToNat(u)) * d
  {
    ScaledSum(s, t, d);
    AddScaledValue(Add(MulLimb(s, d), MulLimb(t, d)), u, d, (ToNat(s) + ToNat(t)) * d);
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s) + ToNat(t), ToNat(u));
  }

  // API

  lemma ScaleTwice(s: seq<nat>, d: nat, e: nat)
    requires Valid(s) && d < BASE && e < BASE
    ensures Valid(MulLimb(MulLimb(s, d), e))
    ensures ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * (d * e)
  {
    MulLimbCorrect(s, d);
    MulLimbCorrect(MulLimb(s, d), e);
    LemmaMulIsAssociative(ToNat(s), d, e);
  }

  lemma AddScaled(a: seq<nat>, s: seq<nat>, d: nat)
    requires Valid(a) && Valid(s) && d < BASE
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == ToNat(a) + ToNat(s) * d
  {
    AddScaledValue(a, s, d, ToNat(a));
  }

  // HELPERS

  lemma AddScaledValue(a: seq<nat>, s: seq<nat>, d: nat, v: int)
    requires Valid(a) && Valid(s) && d < BASE && ToNat(a) == v
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == v + ToNat(s) * d
  {
    MulLimbCorrect(s, d);
    AddCorrect(a, MulLimb(s, d));
  }
}
```

`probe/m2_agent_weak_api.dfy`: the refactor with `ScaleTwice`'s `ensures Valid(MulLimb(MulLimb(s, d), e))` line deleted. `probe/m2_agent_weak_frozen.dfy`: the refactor with `ScaledSum`'s `ensures Valid(Add(MulLimb(s, d), MulLimb(t, d)))` line deleted. `research/q07_frozen.dfy`: `m2_agent_mono.dfy` from its first line through the end of `ScaledSumThree`, then the module's closing brace.


`probe/m2_agent_mono.rs`

```rust
//! probe (lane dv3brev): candidate shipped state of Q07's Verus refactor file (monolithic)
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// FROZEN

/// Two numbers scaled by one word, then added: the sum scaled.
pub fn scaled_sum(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat()) * x,
{
    let sa = mul_limb(a, x);
    let sb = mul_limb(b, x);
    let r = big_add(&sa, &sb);
    proof {
        assert(sa.to_nat() == a.to_nat() * x);
        assert(sb.to_nat() == b.to_nat() * x);
        assert(r.to_nat() == a.to_nat() * x + b.to_nat() * x);
        lemma_mul_is_distributive_add_other_way(x as int, a.to_nat() as int, b.to_nat() as int);
    }
    r
}

/// Three numbers scaled by one word, then added left to right: the sum scaled.
pub fn scaled_sum_three(a: &BigNat, b: &BigNat, c: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        c.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat() + c.to_nat()) * x,
{
    let sa = mul_limb(a, x);
    let sb = mul_limb(b, x);
    let sc = mul_limb(c, x);
    let t = big_add(&sa, &sb);
    let r = big_add(&t, &sc);
    proof {
        assert(sa.to_nat() == a.to_nat() * x);
        assert(sb.to_nat() == b.to_nat() * x);
        assert(sc.to_nat() == c.to_nat() * x);
        assert(t.to_nat() == a.to_nat() * x + b.to_nat() * x);
        lemma_mul_is_distributive_add_other_way(x as int, a.to_nat() as int, b.to_nat() as int);
        assert(t.to_nat() == (a.to_nat() + b.to_nat()) * x);
        lemma_mul_is_distributive_add_other_way(
            x as int,
            (a.to_nat() + b.to_nat()) as int,
            c.to_nat() as int,
        );
    }
    r
}

// API

/// Scaling twice is scaling by the product.
pub fn scale_twice(a: &BigNat, x: u64, y: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * (x * y),
{
    let t = mul_limb(a, x);
    let r = mul_limb(&t, y);
    proof {
        assert(r.to_nat() == a.to_nat() * x * y);
        lemma_mul_is_associative(a.to_nat() as int, x as int, y as int);
    }
    r
}

/// A number plus another scaled by one word.
pub fn add_scaled(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + b.to_nat() * x,
{
    let sb = mul_limb(b, x);
    let r = big_add(a, &sb);
    proof {
        assert(sb.to_nat() == b.to_nat() * x);
    }
    r
}

} // verus!
```

`probe/m2_agent_refactored.rs`

```rust
//! probe (lane dv3brev): a reference refactor of the Verus candidate (helpers under HELPERS)
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// FROZEN

pub fn scaled_sum(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat()) * x,
{
    let sa = mul_limb(a, x);
    let r = add_scaled(&sa, b, x);
    proof { lemma_sum_scaled(a.to_nat(), b.to_nat(), x as nat); }
    r
}

pub fn scaled_sum_three(a: &BigNat, b: &BigNat, c: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        c.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat() + c.to_nat()) * x,
{
    let t = scaled_sum(a, b, x);
    let r = add_scaled(&t, c, x);
    proof { lemma_sum_scaled(a.to_nat() + b.to_nat(), c.to_nat(), x as nat); }
    r
}

// API

pub fn scale_twice(a: &BigNat, x: u64, y: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * (x * y),
{
    let t = mul_limb(a, x);
    let r = mul_limb(&t, y);
    proof { lemma_mul_is_associative(a.to_nat() as int, x as int, y as int); }
    r
}

pub fn add_scaled(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + b.to_nat() * x,
{
    let sb = mul_limb(b, x);
    big_add(a, &sb)
}

// HELPERS

pub proof fn lemma_sum_scaled(u: nat, v: nat, x: nat)
    ensures
        u * x + v * x == (u + v) * x,
{
    lemma_mul_is_distributive_add_other_way(x as int, u as int, v as int);
}

} // verus!
```

`research/q07_frozen.rs`: `m2_agent_mono.rs` through the end of `scaled_sum_three`, then `} // verus!`. The weak variants change `==` to `>=` in `scale_twice`'s (API) and in `scaled_sum`'s (FROZEN) value `ensures`.


**§R.1 #4: the flagship in the methods form, and the repaired Verus delivery.**


`probe/m7_flag_statements.dfy`

```dafny
// probe (lane dv3brev): Q08 flagship, the learner's committed statements (Dafny, methods form)
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import Power = Std.Arithmetic.Power

  // STATEMENTS

  method ShiftLimbs(a: seq<nat>, k: nat) returns (r: seq<nat>)
    requires Valid(a)
    ensures Valid(r) && ToNat(r) == ToNat(a) * Pow(k)

  method SplitLimbs(a: seq<nat>, k: nat) returns (lo: seq<nat>, hi: seq<nat>)
    requires Valid(a)
    ensures Valid(lo) && Valid(hi) && ToNat(a) == ToNat(lo) + Pow(k) * ToNat(hi) && ToNat(lo) < Pow(k)

  // WITNESSES

  method Witnesses()
  {
    var r := ShiftLimbs([5, 1], 2);
    assert ToNat(r) == ToNat([5, 1]) * Pow(2);
    var lo, hi := SplitLimbs([7, 8, 9], 1);
    assert ToNat(lo) < Pow(1);
    var lo2, hi2 := SplitLimbs([7], 3);
    assert ToNat([7]) == ToNat(lo2) + Pow(3) * ToNat(hi2);
  }

  // HELPERS
}
```

`probe/m7_flag_delivery.dfy`

```dafny
// probe (lane dv3brev): Q08 flagship, a reference delivery against the methods-form statements
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import Power = Std.Arithmetic.Power

  // STATEMENTS

  method ShiftLimbs(a: seq<nat>, k: nat) returns (r: seq<nat>)
    requires Valid(a)
    ensures Valid(r) && ToNat(r) == ToNat(a) * Pow(k)
  {
    r := Zeros(k) + a;
    ZerosFacts(k);
    ToNatAppendL(Zeros(k), a);
    LemmaMulIsCommutative(ToNat(a), Pow(k));
    assert Valid(Zeros(k) + a);
  }

  method SplitLimbs(a: seq<nat>, k: nat) returns (lo: seq<nat>, hi: seq<nat>)
    requires Valid(a)
    ensures Valid(lo) && Valid(hi) && ToNat(a) == ToNat(lo) + Pow(k) * ToNat(hi) && ToNat(lo) < Pow(k)
  {
    if k <= |a| {
      lo := a[..k];
      hi := a[k..];
      assert a == lo + hi;
      ToNatAppendL(lo, hi);
      ToNatBound(lo);
    } else {
      lo := a;
      hi := [];
      ToNatBound(a);
      PowIsStdPow(|a|);
      PowIsStdPow(k);
      Power.LemmaPowStrictlyIncreases(BASE, |a|, k);
      LemmaMulBasics(Pow(k));
    }
  }

  // WITNESSES

  method Witnesses()
  {
    var r := ShiftLimbs([5, 1], 2);
    assert ToNat(r) == ToNat([5, 1]) * Pow(2);
    var lo, hi := SplitLimbs([7, 8, 9], 1);
    assert ToNat(lo) < Pow(1);
    var lo2, hi2 := SplitLimbs([7], 3);
    assert ToNat([7]) == ToNat(lo2) + Pow(3) * ToNat(hi2);
  }

  // HELPERS

  function Zeros(k: nat): seq<nat>
    decreases k
  {
    if k == 0 then [] else [0] + Zeros(k - 1)
  }

  lemma {:induction false} ToNatAppendL(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
      LemmaMulBasics(ToNat(b));
    } else {
      assert (a + b)[1..] == a[1..] + b;
      ToNatAppendL(a[1..], b);
      LemmaMulIsAssociative(BASE, Pow(|a| - 1), ToNat(b));
      LemmaMulIsDistributive(BASE, ToNat(a[1..]), Pow(|a| - 1) * ToNat(b));
    }
  }

  lemma {:induction false} ZerosFacts(k: nat)
    ensures |Zeros(k)| == k && Valid(Zeros(k)) && ToNat(Zeros(k)) == 0
    decreases k
  {
    if k > 0 {
      ZerosFacts(k - 1);
      ToNatCons(0, Zeros(k - 1));
      ValidCons(0, Zeros(k - 1));
    }
  }
}
```

`probe/m7_flag_statements.rs`: A.9's `use` lines, the two fns as `#[verifier::external_body]` stubs with their `requires`/`ensures` and `unimplemented!()` bodies, and the witnesses fn below. `probe/m7_flag_delivery.rs`: A.9's `flag_v.rs` with `high_limbs` replaced by

```rust
/// Divide by weight(k): drop the k lowest limbs.
pub fn high_limbs(a: &BigNat, k: usize) -> (r: BigNat)
    requires a.wf(),
    ensures r.wf(), r.to_nat() == a.to_nat() / weight(k as nat),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    proof { lemma_weight_pos(k as nat); }
    if k >= n {
        proof {
            broadcast use group_bignat_bounds;
            lemma_weight_mono(n as nat, k as nat);
            lemma_basic_div_specific_divisor(weight(k as nat) as int);
        }
        return BigNat { limbs: v };
    }
    let mut j: usize = k;
    while j < n
        invariant k <= j <= n, n == a@.len(), v@ =~= a@.subrange(k as int, j as int),
        decreases n - j,
    {
        v.push(a.limbs[j]);
        j = j + 1;
    }
    proof {
        let lo = a@.subrange(0, k as int);
        let hi = a@.subrange(k as int, n as int);
        assert(lo + hi =~= a@);
        lemma_seq_to_nat_append(lo, hi);
        broadcast use group_bignat_bounds;
        assert(lo.len() == k);
        assert(seq_to_nat(lo) < weight(k as nat));
        lemma_mul_is_commutative(weight(k as nat) as int, seq_to_nat(hi) as int);
        assert(a.to_nat() == seq_to_nat(hi) * weight(k as nat) + seq_to_nat(lo));
        lemma_fundamental_div_mod_converse(a.to_nat() as int, weight(k as nat) as int, seq_to_nat(hi) as int, seq_to_nat(lo) as int);
        assert(v@ =~= hi);
    }
    BigNat { limbs: v }
}
```

and, before the closing `} // verus!`,

```rust
// WITNESSES
fn witnesses() {
    let a = BigNat { limbs: vec![5u64, 1u64] };
    proof { reveal_with_fuel(seq_to_nat, 3); assert(a@.drop_first() =~= seq![1u64]); assert(seq![1u64].drop_first() =~= Seq::<u64>::empty()); assert(a.wf()); }
    let r = shift_limbs(&a, 2);
    assert(r.to_nat() == a.to_nat() * weight(2));
    let h = high_limbs(&a, 1);
    assert(h.to_nat() == a.to_nat() / weight(1));
}
```

`research/q08_fn_statements.dfy` and `probe/m7_fn_delivery.dfy` (the function-form check):

```dafny
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  function ShiftLimbs(a: seq<nat>, k: nat): seq<nat>
}
```

```dafny
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  function ShiftLimbs(a: seq<nat>, k: nat): seq<nat>
  {
    if |a| == 0 then [] else a
  }
}
```


**§R.1 #5: a trait method that gains a specification.**

```rust
use vstd::prelude::*;
verus! {
pub trait Toggle {
    spec fn on(&self) -> bool;
    fn flip(&mut self);
}
}
```

```rust
use vstd::prelude::*;
verus! {
pub trait Toggle {
    spec fn on(&self) -> bool;
    fn flip(&mut self)
        ensures final(self).on() == !old(self).on();
}
}
```


**§R.1 #6: Q07's bit-vector items without the construct.**


`probe/m1_bv_cfree.rs`

```rust
//! probe (lane dv3brev): construct-free answers of Q07's bit-vector items, under and outside the
//! proposed `bv-exec` form (no `*`, `/` or `%` in exec code)
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// H6v contract; exec division and remainder by a constant (outside the form)
pub fn h6v_divmod(p: u128) -> (r: (u64, u64))
    ensures r.0 as nat * BASE + r.1 as nat == p as nat,
{
    ((p / 0x1_0000_0000_0000_0000u128) as u64, (p % 0x1_0000_0000_0000_0000u128) as u64)
}

// H6v contract; a shift and a truncating cast, no proof (inside the form)
pub fn h6v_shift_cast(p: u128) -> (r: (u64, u64))
    ensures r.0 as nat * BASE + r.1 as nat == p as nat,
{
    ((p >> 64u128) as u64, p as u64)
}

// H6v contract; a shift and a mask, no proof (inside the form)
pub fn h6v_shift_mask(p: u128) -> (r: (u64, u64))
    ensures r.0 as nat * BASE + r.1 as nat == p as nat,
{
    ((p >> 64u128) as u64, (p & 0xFFFF_FFFF_FFFF_FFFFu128) as u64)
}

// X1v contract; exec multiplication and addition (outside the form)
pub fn x1v_mul(hi: u64, lo: u64) -> (r: u128)
    ensures r as nat == hi as nat * BASE + lo as nat,
{
    (hi as u128) * 0x1_0000_0000_0000_0000u128 + (lo as u128)
}

// X1v contract; a shift and an or, no proof (inside the form)
pub fn x1v_shl_or(hi: u64, lo: u64) -> (r: u128)
    ensures r as nat == hi as nat * BASE + lo as nat,
{
    ((hi as u128) << 64u128) | (lo as u128)
}

// X1v contract; a shift and an addition, no proof (inside the form)
pub fn x1v_shl_plus(hi: u64, lo: u64) -> (r: u128)
    ensures r as nat == hi as nat * BASE + lo as nat,
{
    ((hi as u128) << 64u128) + (lo as u128)
}

} // verus!
```

**§R.1 #7: Q09's re-posed exits.**


`probe/m8_q09x_d.dfy`

```dafny
// probe (lane dv3brev): candidate re-posed Q09 Dafny exits (nonlinear arithmetic on, as the exit module)
module Q09_ExitProbe {
  import opened QG_L1_BigNat
  import opened Std.Arithmetic.Mul

  // X1d candidate: a product plus a carry stays below the square
  lemma X1Ref(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y + z < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    LemmaMulUpperBound(x, p - 1, y, p - 1);
    LemmaMulIsDistributiveSub(p - 1, p, 1);
    LemmaMulStrictInequality(p - 1, p, p);
  }

  lemma X1Empty(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y + z < Pow(n) * Pow(n)
  {
  }

  lemma X1OneStep(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y + z < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= (p - 1) * (p - 1);
  }

  // X2d candidate: a limb sum over four concatenated parts
  function LimbSum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + LimbSum(s[1..])
  }

  lemma LimbSumAppend(s: seq<nat>, t: seq<nat>)
    ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t)
    decreases |s|
  {
    if |s| == 0 {
      assert s + t == t;
    } else {
      assert (s + t)[1..] == s[1..] + t;
      LimbSumAppend(s[1..], t);
    }
  }

  lemma X2Attempt(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  {
    assert forall s: seq<nat>, t: seq<nat> {:trigger LimbSum(s), LimbSum(t)} ::
      LimbSum(s + t) == LimbSum(s) + LimbSum(t)
    by {
      forall s: seq<nat>, t: seq<nat> ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t) {
        LimbSumAppend(s, t);
      }
    }
  }

  lemma X2Ref(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  {
    assert forall s: seq<nat>, t: seq<nat> {:trigger LimbSum(s + t)} ::
      LimbSum(s + t) == LimbSum(s) + LimbSum(t)
    by {
      forall s: seq<nat>, t: seq<nat> ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t) {
        LimbSumAppend(s, t);
      }
    }
  }

  lemma X2Calls(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  {
    LimbSumAppend(a + b + c, d);
    LimbSumAppend(a + b, c);
    LimbSumAppend(a, b);
  }

  lemma X2Empty(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  {
  }
}
```

`probe/m8_q09x_v.rs`

```rust
//! probe (lane dv3brev): candidate re-posed Q09 Verus exits
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// X1v candidate: a product plus a carry stays below the square
pub proof fn x1v_ref(x: nat, y: nat, z: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
        z < weight(n),
    ensures
        x * y + z < weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y <= (p - 1) * (p - 1)) by (nonlinear_arith)
        requires x < p, y < p;
    assert((p - 1) * (p - 1) + (p - 1) < p * p) by (nonlinear_arith)
        requires p >= 1;
}

pub proof fn x1v_one_step(x: nat, y: nat, z: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
        z < weight(n),
    ensures
        x * y + z < weight(n) * weight(n),
{
    let p = weight(n);
    assert(x * y + z < p * p) by (nonlinear_arith)
        requires x < p, y < p, z < p;
}

pub proof fn x1v_empty(x: nat, y: nat, z: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
        z < weight(n),
    ensures
        x * y + z < weight(n) * weight(n),
{
}

// X2v candidate: a limb sum over four concatenated parts
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + limb_sum(s.drop_first())
    }
}

pub proof fn lemma_limb_sum_append(s: Seq<u64>, t: Seq<u64>)
    ensures
        limb_sum(s + t) == limb_sum(s) + limb_sum(t),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s + t =~= t);
    } else {
        assert((s + t).drop_first() =~= s.drop_first() + t);
        lemma_limb_sum_append(s.drop_first(), t);
    }
}

pub proof fn x2v_attempt(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
    assert forall|s: Seq<u64>, t: Seq<u64>|
        #![trigger limb_sum(s), limb_sum(t)]
        limb_sum(s + t) == limb_sum(s) + limb_sum(t) by {
        lemma_limb_sum_append(s, t);
    }
}

pub proof fn x2v_ref(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
    assert forall|s: Seq<u64>, t: Seq<u64>|
        #[trigger] limb_sum(s + t) == limb_sum(s) + limb_sum(t) by {
        lemma_limb_sum_append(s, t);
    }
}

pub proof fn x2v_calls(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
    lemma_limb_sum_append(a + b + c, d);
    lemma_limb_sum_append(a + b, c);
    lemma_limb_sum_append(a, b);
}

pub proof fn x2v_empty(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
}

} // verus!
```

`probe/m8_q09x_v_refs.rs`, `_att.rs` and `_one.rs` are this file reduced to the references (`x1v_ref`, `x2v_ref` and their helpers), to `x2v_attempt`, and to `x1v_one_step`, for the seed sweeps.


## Appendix B. Raw outputs

Not reproduced. §0 quotes the summary lines and per-symbol results the decisions rest on; the raw run directories (`dvl/runs/`, `swap/`) are lane scratch.
