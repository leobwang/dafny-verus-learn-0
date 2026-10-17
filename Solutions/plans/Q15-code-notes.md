# Q15 code notes (DV5b Q15 lane, as built)

> **Author-only.** The prediction answers, the battery's verdicts and repairs, the forensic and
> rung-11 captures, the four admission results per item, the probes behind them and the
> deviations of Q15's code from the plan. Never quote, paraphrase or link any of it from a
> learner-visible file. The plan is `QPLAN.md` §19 and §25 and
> `Solutions/plans/Q10-Q18-author-notes.md` §7 (designs, not probed); this file records what
> was built (authoring worktree, HEAD dd24798 plus the round's working tree, 2026-10-11) and where
> it differs.

Every result below was captured on the pins (Dafny 4.11.0, Verus 0.2026.09.27.3cf1832) through
the course wrappers (`scripts/vcheck`, `scripts/vaudit`, `scripts/specfreeze`, `scripts/pins.py`,
`scripts/firsttry.py`, `scripts/dvl/python.py`), one solver job at a time (a lane lock), each job
under the wrappers' caps (Dafny 8 GB, Verus 16 GB) and inside `systemd-run --user --scope -p
MemoryMax=16G -p MemorySwapMax=0` (the lane's share; `/tmp/dvl0-dv5b-q15/run.sh` refuses to start
below 31 GB available). `free -g` showed 82-103 GB available; no job was killed.
`DVL_SCRATCH=/tmp/dvl0-dv5b-q15/scratch`. Probes, gate logs, the battery generator and the
captures are archived under `~/.cache/dafny-verus-learn-0/author-probes/dv5b/q15/`
(`empty-body-1.txt`, `empty-body-2.txt`, `brit*.txt`, `battery/`, `specimens/`, `agent/`, `lsp/`,
`probe/`, `hidden-src/`). No model was called and no container was started.

## 1. Files

| file | shipped state | twin |
|---|---|---|
| `dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy` (module `Q15_PracticeIIC`, L1-L6, nonlinear on) | verified; 2 holes (H1d, H2d bodyless lemmas); prediction block P1d, P6dv-P11dv | 152 verified (with Q15_Lab2Specs.dfy) |
| `dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy` (module `Q15_Lab2Specs`, L1-L6) | verified; 3 holes (H3d-H5d: each prose client's `assume false;`) | as above |
| `verus/q/q15_practice_iic/src/lib.rs` (`mod lab2_specs;`) | verified; 2 holes (H1v, H2v `proof_note` assumes) | 17 verified (crate) |
| `verus/q/q15_practice_iic/src/lab2_specs.rs` | verified; 3 holes (H3v-H5v: each prose client's labelled assume) | as above |
| `dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy` | verified; 1 hole (X1d) | 132 verified |
| `verus/q/q15_practice_iic/src/exit.rs` | an empty `verus!` block, no hole (exits come in pairs) | the same |
| `dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` (rung 11) | verified; 4 holes (A1d: three bodyless lemmas, one bodyless method) | 135 verified, `--test` 1 passed, vaudit 0 |
| `verus/q/q15_practice_iic/src/agent.rs` (rung 11; never `mod`-declared) | verified; 4 holes (A1v: three labelled assumes, one external body) | 4 verified, `--test` 1 passed, vaudit 0 |
| `research/q15_forensic.dfy`, `.rs` | the two agent files as shipped, a three-line header added: the CONTRACTs' freeze references | — |
| `specimens/Q15/P2d.dfy.specimen`, `P3d`, `P4v.rs.specimen`, `P5v` | four green-looking deliveries, `// after:` and `// SLOT:` lines, one `// planted:` marker each | `Solutions/specimens/Q15/` (switch on, a Reference Solution line) |
| `tools/Q15/battery/battery.toml`, `dafny/G01.dfy`-`G12.dfy`, `verus/G01.rs`-`G12.rs` | twelve bilingual goals, each a whole standalone file | `Solutions/tools/Q15/battery/` (the trigger-only repairs) |
| `tools/Q15/toolsmith.py` (rung 12) | CONTRACT docstring, empty INTERFACE and AUDIT blocks | — |
| `harness/q/fvh_q/lsp_client.py` | 3 Python holes (H6py-H8py) | 31 tests pass |
| `harness/q/fvh_q/oracles.py` | 4 Python holes (H9py-H12py) | 26 tests pass |
| `harness/tests/q/test_lsp_client.py`, `fixtures/q15/lsp/server.jsonl`, `source.dfy` | frozen tests (31) over a recorded server session | — |
| `harness/tests/q/test_oracles.py` | frozen tests (26) over synthetic tasks and a stand-in runner | — |
| `harness/fvh/lsp.py`, `harness/tests/core/test_lsp.py`, `scripts/dafny-server` | the course's entry point to `dafny server` (QPLAN §30 Q56; §4 below) | — |
| `research/q15_redteam.md` | the tutor red-team record form | — |
| `slots/Q15.slots`, `Solutions/slots/Q15.slots`, `expected/Q15.pins` (11 salted), `expected/Q15.counts` (Dafny unit 152 / floor 2, crate 17 / floor 2; 10 file states), `expected/Q15.freeze` (72 statements in 13 files; open specs below) | author-written | — |
| `Solutions/plans/Q15-record-transcript.py` | the author's recorder of the server transcript and the P1d capture | — |
| `bench/local/q/lab2/STRATUM.toml`, `<card>/tasks/<card>.{dfy,rs}` (20) | Lab 2's local task forms (§14) | references with the hidden truth only |

No card section (§19.0); no check unit. `research/runs/Q15/` is written by `fvh` only and does
not exist yet.

## 2. The predictions (captured on the built scenarios)

| item | answer | capture |
|---|---|---|
| P1d | `correct correct` | the docstring's file through the reference client (`Q15-record-transcript.py p1d`, the pinned server through `fvh.lsp.start_server`): the last symbolStatus gives status 5 (Correct) to both lemmas; the bodyless one is reported correct, with only a warning diagnostic (`This ensures clause is part of a bodyless method`). The server's codes: 1 queued, 2 running, 4 error, 5 correct (probed with a failing lemma). |
| P2d | `input gate` | `{:only}` on a helper: learner loop `verified — 1 verified` with the VerifyOnly warning; the gate fails (warnings-fail-gate); vaudit verify-only |
| P3d | `test vaudit` | a test method without `{:test}`: learner loop and gate verified; vaudit `expect-outside-test`; `--test` no test ran |
| P4v | `trust vcheck` | an external body around real code with a false ensures: the learner loop already counts 1 hole |
| P5v | `options gate` | `exec_allows_no_decreases_clause`: learner loop verified; gate fails on the lint finding exec-allows-no-decreases; vaudit the same |
| P6dv (G01) | `D:fail V:fail` | the shipped forms, `scripts/vcheck <file>` |
| P7dv (G02) | `D:ok V:ok` | |
| P8dv (G03) | `D:fail V:err:resolve` | Verus: `Could not automatically infer triggers`, stage resolve |
| P9dv (G07) | `D:err V:err:resolve` | Dafny: `error — - verified`, a Boogie resolution error (`trigger must mention all quantified variables`); Verus: `trigger does not cover variable n`, stage resolve |
| P10dv (G09) | `D:fail V:ok` | |
| P11dv (G10) | `D:err V:ok` | Dafny as G07 |

`pins.py --update --ref --module Q15` wrote the 11 salted pins. The P2-P5 answers follow the
specimen header's rule (the first instrument, in the order vcheck, gate, vaudit, test, whose
result is not a pass); every specimen was run through all four instruments
(`specimens/capture.txt` in the archive).

## 3. The trigger battery

Twelve goals, each a Dafny and a Verus file over local copies of the definitions (an opaque
`Pow`/`weight` with its step and positivity lemmas, `ToNat`/`seq_to_nat`, `Valid`), the goal last.
Shipped verdicts (learner loop) and the reference repairs (trigger-only; each repaired file passes
`vcheck --gate` and `specfreeze --against` its shipped file with 0 findings):

| goal | D | V | repair |
|---|---|---|---|
| G01 positivity, successor trigger | fail | fail | both: the trigger on the plain term |
| G02 positivity, no trigger | ok | ok | none |
| G03 two places up, no trigger | fail (Dafny's own choice misses) | err:resolve | D: `{:trigger Pow(k)}`; V: `#[trigger]` on the successor term |
| G04 a bound through `Pow(\|u\|)` | ok | ok | none |
| G05 a bound with an inline digit hypothesis, trigger `Valid(u)` | fail | ok | D: `{:trigger ToNat(u)}` |
| G06 zero limbs on top, a looping trigger | ok | ok | none |
| G07 monotone powers, one variable of two | err | err:resolve | both: a trigger on both terms |
| G08 the low-limb split, slice trigger | ok | ok | none |
| G09 three places, a two-term trigger (step: monotonicity, fix round §16) | fail | ok | D: the plain term alone |
| G10 a longer place, one variable of two | err | ok (auto) | D: both terms |
| G11 a limb put below twice | ok | ok | none (the step is not needed: fuel unfolds) |
| G12 a bound through a concatenation | ok | ok | none (not needed) |

Six goals pass as shipped in both languages; the toolsmith's tool must leave them alone (its
CONTRACT says so). A first G11/G12 pair (a successor-trigger power step and a three-hop chain in
nested `+ 1` form) was replaced: the line-level check (§9) found H1v's quantified step verbatim in
G11, and G12's Verus form was H1v's statement with the nested terms H1v's proof needs. The
shipped forms are deterministic at the pin (each verdict also seen in the generator's two runs);
they were not swept across seeds.

Reading taken (a deviation from the author notes §7, "six per language"): QPLAN §25.1 says
"twelve goals, Dafny and Verus … six of them are P6dv-P11dv's scenarios" and the answer form is
`D:<v> V:<v>` per goal, so each goal has both forms (24 files) and six goals are predicted.

## 4. The language server entry point (QPLAN §30 Q56, built by this lane)

Nobody had built Q56's entry point, and H8py needs it. Built: `scripts/dafny-server [--runtime S]
[--argv]` execs the pinned server from the scratch copy of the install (`dvl.dafny.server_argv`,
Δ33) under `dvl.common.cap_argv` (MemoryMax = the Dafny pin's 8 GB, MemorySwapMax=0,
RuntimeMaxSec = S, default 900, at most the pinned wall clock) with dvl's scrubbed environment;
`harness/fvh/lsp.py` (standard library only) gives `start_server(root=None, *, runtime_s=900)` (a
Popen of the launcher with binary pipes, its own process group) and `stop_server(proc, *,
grace_s=5.0)` (close stdin, wait, kill the group); `fvh/__init__.py` lists `fvh.lsp` (docstring
and `__all__`; the DV4 lane is editing the same file). `harness/tests/core/test_lsp.py`: 13 with
the layout tests, all passing (the launcher's `--argv` line checked: systemd-run, MemoryMax,
RuntimeMaxSec, the scratch server path, the pinned flags).

## 5. The Python items

- **lsp_client.py:** `frame` (H6py), `read_message` (H7py), `verify_with_server(path, text, *,
  start=None)` (H8py: initialize/initialized/didOpen, read until a symbolStatus whose statuses are
  all final or a ParsingFailed/ResolutionFailed compilation status, answer server requests, then
  shutdown/exit, `fvh.lsp.stop_server` in a finally). Given: `STATUS_NAMES`, `FINAL`,
  `ProtocolError`, `SymbolStatus`, `Diagnostic`, `ServerReport(uri, statuses, diagnostics, ended)`,
  `status_name`, `uri_of`, `main` (the live check). Tests: 31 (the recorded session's report and
  client messages; hand-made sessions; framing and malformed headers). The transcript is a real
  session over `TranscriptProbe` (one function, one proved and one failing lemma: no bodyless
  lemma, so it does not settle P1d), paths replaced by `/work/q15/transcript.dfy` and
  `<redacted>`.
- **oracles.py:** given `Verdict` (FAITHFUL, WEAK, STRONG, VACUOUS, UNDECIDED), `Task`, `Spec`,
  `Mutant`, `KillReport`, `Implication`, `outcome(result)`, `render_program`, `render_lemma`,
  `write_target` (a fresh directory outside the course, so fvh.tools sends the file to the
  verification container), `vacuity`, `MUTATION_OPERATORS` (ror, aor, lit+, lit-); holes `mutants`
  (H9py: whitespace-delimited operator sites and decimal literals, comments and strings skipped,
  duplicates dropped), `kill_rate` (H10py), `implication` (H11py: `<name>_SpecImpliesRef` and
  `<name>_RefImpliesSpec`, Verus snake case), `classify(imp, vacuous)` (H12py). Signatures beyond
  QPLAN §25.2: `workdir` keywords, `kill_rate`'s mutants carry no task (the Spec does), and
  `classify` takes the Implication and the vacuity outcome. Tests: 26.
- References pass their tests (`vcheck --ref`); each `# triv:` body fails them (`python.py triv`:
  3/3, 4/4; the empty-body gate's Python TRIV mode: 7/7); the learner files fail them with their
  holes; `python.py lint` 0 findings in both modes.

## 6. Rung 11: the agent deliveries (captured)

| delivery | Dafny attempt stops at | Verus attempt stops at |
|---|---|---|
| D1 (two-limb value) | parse: `missing semicolon at end of statement` | parse: `mismatched closing delimiter` |
| D2 (one-limb numeral / pushed limb) | resolve: `unresolved identifier: FromNatSingle` | resolve: `cannot find function lemma_seq_to_nat_push` |
| D3 (adding empty / weight ≥ 1) | verify: a postcondition not proved | verify: `postcondition not satisfied` |
| D4 (two-limb value / low limb, with a test) | test: the attempt verifies; `--test`: `FAILED Q15_AgentForensic.TestTwoLimbValue`, expectation violation | test: verifies; `--test`: `FAILED tests::low_of_five_and_nine` |

The twins (repairs plus ATTRIBUTIONS rows) pass `--gate`, `--test` and vaudit, and `specfreeze
--against research/q15_forensic.*` reports 0 findings for both the shipped files and the twins.
Each empty body of D1-D3 fails (probed); FromNatOneLimb's empty body verifies (the definition
unfolds), so its repair is the deletion of the bogus call: the delivery is about attribution.
CONTRACT lines are DV4 §6 forms (`vcheck-gate`, `specfreeze-against`, `vaudit`); the `--test`
line and the ATTRIBUTIONS line are audit lines.

## 7. References, counts and stability

Counts are QPLAN §19.0's rule with the plan's counter (author notes C.8); the intermediate band is
D 10-30 / V 15-45, at most one invented lemma.

| item | reference | proof lines | band | note |
|---|---|---|---|---|
| H1d `PowThreeUp` | successor-trigger step + three asserts on fresh `var`s | **5** | below 10 | not admitted |
| H1v `lemma_weight_three_up` | successor-trigger step + three asserts in nested `+ 1` form | **5** | below 15 | not admitted |
| H2d `CmpTop` + `CmpTopRefuted` | repair `requires Valid(a)` (1) + induction on the tail 3; refutation statement 3 + empty body | **7** (was 14 with unneeded lines, §16) | below 10 | not admitted |
| H2v `lemma_push_lt` + `lemma_push_lt_refuted` | repair `a.len() <= b.len()` (1) + 7; refutation 4 + 1 (`reveal_with_fuel`) | **13** (was 24, §16) | below 15 | not admitted |
| H3d-H5d | specs 2 lines each + a one-line witness | 3 each | below 10 | prose; not admissible (Q49) |
| H3v `count_nonzero` + `nonzero_count` | spec fn 4 + statement 2, ensures 1, invariant 1, 2 asserts, witness 2 | ≈ 12 | below 15 | prose |
| H4v `split_at_limb` | spec 5, two proof blocks ≈ 18, witness 2 | ≈ 25 | 15-45 | prose |
| H5v `max_big` | ensures 2, witness 3 | 5 | below 15 | prose; its code needs no proof (§8) |
| X1d `NoCarryValid` | one forall statement with two explicit triggers, one assert | 3 | exit | |

**The repairs taken.** H2d's smallest change is `Valid(a)` (the first argument's digits; Valid(b)
is not needed), and the client's `Valid(a) && Valid(b)` accepts it. H2v's is `a.len() <= b.len()`
(`==` also makes it true and fails the client, which passes sequences of different lengths).

**H2d's first reference** (a top-limb split helper, the statement of Q10.H3d, then the product
inequality) verified on 4.12.1 but was out of resource on 4.14.1 (seeds 1-3) with a CV of 63% on
4.12.1; three restatements of the arithmetic stayed unstable (`probe/cmptop.dfy`). The reference is
now an induction on the tails that needs no product (`probe/cmptop2.dfy`: six rows verified,
≈ 40k resource units).

**Stability** (`vcheck --ref --brittleness`, Dafny `--solvers`): the Dafny unit twin six rows
verified, stable (widest CV 18.8%, PowThreeUp); the crate twin seeds 1-3 verified, stable (21.5%,
a layer declaration); the Dafny exit twin six rows stable (13.9%, a layer declaration). A first
sweep found the crate unstable at `split_at_limb` (seeds 1-2 failed the last postcondition); three
assertions for the case `k` past the length made it stable.

**H1d's attempt** (the quoted plain-trigger step) is inconclusive (out of resource) on every row of
`--brittleness --solvers`, against ≈ 35k for a successor-trigger proof; with the statement's
product right-associated the same attempt verifies in ≈ 14k, so the shipped statement is
left-associated on purpose. H1v's attempt exceeds the rlimit (seeds 1-3).

**APIs** (all at the pins; every twin verifies): layers L1-L6 (Dafny `Valid`, `ToNat`, `Pow`,
`FromNat`, `Add`, `AddCorrect`, `ToNatCons`, `ToNatSingleton`, L6's `Sub`; Verus `seq_to_nat`,
`weight`, `lemma_weight_succ`, `lemma_weight_pos`, `group_bignat_bounds`,
`lemma_seq_to_nat_append`, `normalize`, `cmp`, `from_u64`),
`vstd::arithmetic::mul::lemma_mul_inequality`, `Vec::new`, `Vec::push`, `Vec::clone`, `Seq`'s
`push`, `drop_first`, `drop_last`, `subrange`.

## 8. The empty-body gate (`firsttry.sh Q15 --empty-body`)

Run 1 (before the H2d and split_at_limb revisions): **18/18**, exit 0 (`empty-body-1.txt`). Run 2
on the final files: see `empty-body-2.txt` (§11). Per item (run 1):

| item | result |
|---|---|
| H1d | ✓ maxauto and seeds 1-3 fail; ✓ twin meets `trigger, stable`; ✓ both `cfree:` answers (one or three asserts, no quantifier; each verifies) fail the trigger form |
| H1v | ✓ every light mode fails; ✓ forms; ✓ its `cfree:` (three `lemma_weight_succ` calls; verifies) fails the trigger form |
| H2d | ✓ maxauto and seeds 1-3 fail (the twin's repaired statement, empty) |
| H2v | ✓ every light mode fails, with the twin's clauses laid over the open statement |
| H3d-H5d, H3v-H4v | ✓ client gate (the use-site check fails or does not resolve without a statement); ✓ prose proof gate |
| H5v | ✓ client gate; ✗ prose proof gate: `max_big`'s code needs no proof, so its empty-proof variants verify. Not admitted anyway; a TRIV variant for exec prose items is a tools item (§10). **DV5c (§17): the gate now runs TRIV with the twin's `triv:` body and passes** |
| X1d | ✓ maxauto and seeds 1-3 fail; ✓ trigger form; both `cfree:` answers (an assert restating the hypothesis; the forall statement without a trigger; each verifies) fail the form |
| H6py-H12py | ✓ each TRIV body fails |

## 9. Admission: the four results, item by item (QPLAN §19.0, Δ173)

| item | (1) in band | (2) gate | (3) stable | (4) pinned APIs | registry |
|---|---|---|---|---|---|
| H1d | 5 < 10: the declared short-format band exception (D2, §17) | ✓ | ✓ | ✓ | **true, 8** (DV5c; false, 0 before) |
| H1v | 4 < 15 under D1 (5 before): the same exception (§17) | ✓ | ✓ | ✓ | **true, 7** (DV5c; false, 0 before) |
| H2d | ✗ 7 < 10 (shortest known proof, §16) | ✓ | ✓ | ✓ | false, 0 |
| H2v | ✗ 13 < 15 (shortest known proof, §16) | ✓ | ✓ | ✓ | false, 0 |
| H3d-H5d, H3v-H5v | ✗ mostly below band; hidden check pending (QPLAN §30 Q49) | ✓ (H5v's proof gate ✗) | ✓ | ✓ | false, 0 |
| H6py, H7py, H8py | reference passes the frozen tests | TRIV fails | — | ✓ (fvh.lsp, built §4) | **true, 5 / 7 / 15** |
| H9py-H12py | reference passes | TRIV fails | — | ✓ | **true, 15 / 20 / 20 / 20** |

Admitted minutes: verifier 0, Python 102 (after the fix round, §16). Shortfalls (no fallback has
its four results, so each carries 0, Δ173): the S11 line 15 minutes (H1d 8, H1v 7: below the
intermediate band by design of the 15-minute line); the S12 line 15 minutes (H2d 8, H2v 7: below
the band on their shortest known proofs, §16); Lab 2's prose specs 108 (Q49). The Python items were "not yet admissible"
in QPLAN §25.2 only for want of the entry point (H6-H8) and the core (H9-H12); both exist now.

## 10. Other checks run

`vcheck Q15` (both units verified, 10 holes); `vcheck --ref --gate` on every twin (unit 152, crate
17, Dafny exit 132, the agent twins in place 135 and 4, the Python twins 31 and 26); `vcheck --ref
--pin-counts Q15`; `specfreeze --pin Q15` and `--check` (0 findings); `reference_lint.py --module
Q15` (0 findings); `firsttry Q15 --lint-hollow` OK (12 files); `pins.py --update --ref`;
`check_course_map.py` OK; `avoid.sh` OK (Q 1764 declarations, 0 hits); the leak README's verifier
(14 modules, 1448 public files, OK); `python.py lint` 0; `test_lsp.py` + `test_layout.py` 13
passed. The final-tree runs are in §11.

A line-level answer check (every twin line of at least 16 characters that its learner file lacks,
searched in every learner-visible file): the hits are the shipped commented checks, generic
one-line steps and clauses (`requires Valid(a)`, `lemma_weight_succ(k);`), the agent repairs'
`assert(seq![d].drop_first() =~= …)` idiom (also in a Q12 battery candidate), and two real ones,
fixed: H1v's step in battery G11 and H1v's statement in G12 (§3). H2d's first helper had Q10.H3d's
statement; the revised reference has no helper.

## 11. Final-tree runs

On the final files (after the H2d and split_at_limb revisions and the battery's new G11/G12):
`firsttry --empty-body` **18/18**, exit 0 (`empty-body-2.txt`; H5v's proof-gate finding reported,
not failing, as the item is recorded not admitted); `--brittleness` stable on the Dafny unit twin
(both solvers × seeds 1-3, widest CV 18.8%), the crate twin (seeds 1-3) and the Dafny exit twin;
`vcheck --shipped Q15` 10 files, 0 problems; `pins.py --ref --module Q15` 11 checks, 0 problems;
`pins.py --ci --module Q15` 34 pins, 0 problems; `specfreeze --check Q15` 0; `reference_lint.py
--module Q15` 0; `firsttry Q15 --lint-hollow` OK; `--report` (11 unfilled slots, 23 commented
checks, 0 forms not met); `check_course_map.py` OK (15 authoring); `gen_units.py --check` OK;
`avoid.sh` OK (0 hits); the leak verifier OK (14 modules, 1470 public files); the static suites
`tests/wrappers/test_{forms,practice_tools,tools,dafny,verus}_static.py` 45, 31, 108 (1 skipped),
55, 49: OK (one expectation of `test_tools_static.py` follows the planted-marker message, and one
case is new, §12 item 8); `harness/tests/core` 470 passed.

**A learner-flow simulation** in a study-like copy (tracked and new files, no reference trees;
`/tmp/dvl0-dv5b-q15/sim`, a throwaway git repository): a specimen run before its first try is
refused by the H5 guard; the eleven slots filled with the reference answers, `firsttry.sh Q15
--check` records 11/11 passing first tries; with the switches enabled, each specimen's
instruments print what §2 says; with the twins laid over the learner files, `vcheck --gate` passes
the unit (152), the crate (17) and both Python files (31, 26), and `--report --strict` is OK.
`firsttry --exit` first **refused** the module ("exit.rs has no X items": an exit file of the pair
ships with no block, QPLAN §30 Q50, which said the tool accepted it); fixed in
`scripts/firsttry.py` (§12 item 8), after which `--exit` scores X1d 1/1 PASS and records it. Q13's
empty Dafny exit had the same refusal.

## 12. Deviations from the plan

1. **H2d's proof** needs no invented lemma (induction on the tails), against the author notes'
   "one invented top-limb split" (§7). The plan's split was unstable on 4.14.1 (§7).
2. **H2v's false statement** is new (`lemma_push_lt`, refuted by [5, 0] and [6] with the limb 1;
   repaired by `a.len() <= b.len()`): the planned `lemma_shorter_smaller` is Lab 1's local task
   va1 (its repaired statement is a learner-visible task form).
3. **H2d and H2v ship as open statements whose body is the hole** (Dafny bodyless, Verus a labelled
   assume in the lemma), with commented use-site checks in the given client, rather than "a client
   with a labelled assume": a false lemma shipped with a body would leave the file red.
4. **H1d's statement is left-associated** (`BASE * BASE * BASE * Pow(n)`), so the quoted attempt
   runs out of resources; the plan's right-associated form lets it verify. H1v keeps the plan's
   right-associated form (Verus's attempt times out either way). Both are below the band (§9).
5. **The forensic specimens' defects:** `{:only}` (for "a --library-style input": a single file
   cannot carry a project flag), a test method without `{:test}`, an external body, and
   `exec_allows_no_decreases_clause` (for "an option in dfyconfig.toml"). Their stage vocabulary
   (input, options, trust, test) and the instrument rule are the block's own.
6. **The battery's reading** (§3: twelve bilingual goals) and two replaced goals.
7. **Lab 2's prose tasks** ship their implementations without explicit `decreases` (Dafny's
   default measure) and, for `max_big`, with its `requires` (its code calls `cmp`); `count_nonzero`'s
   prose names the spec fn `nonzero_count` and its client reveals it, because every use-site check
   of a recursive count needs two unfoldings.
8. **Tools touched:** `scripts/firsttry.py`: `planted:` markers accept S10 verdict items besides
   S12 (`PLANTED_STRANDS`), for the pipeline-forensic specimens; `--exit` skips an exit file of
   the pair that holds no X item (QPLAN §30 Q50) and refuses only when none holds one.
   `tests/wrappers/test_tools_static.py`: the marker message's expectation and a new S10 case.
   `scripts/dafny-server`, `harness/fvh/lsp.py`, `harness/tests/core/test_lsp.py` and two lines
   of `harness/fvh/__init__.py` (§4).
9. **The hidden truth is not sealed.** The six prose items' reference specifications (as
   `fvh_q.oracles.Spec` fields over the shipped context) are staged in plaintext in the author
   archive (`hidden-src/labs/Q15/`, with `MANIFEST.sha256`), and nothing was written under
   `Hidden/` in the worktree: `age` is not installed on this host, and the grader container's
   `truth` mode and key are the DV5 integration lane's (QPLAN §30 Q49).

## 13. Open issues

1. **Orchestrator (high: before Q15 ships).** H1d and H1v are complete, gated and stable but below
   the intermediate band by design (design §7.5's 15-minute S11 line); admit them under a recorded
   band exception, or re-plan the S11 line. Until then 15 minutes short.
2. **DV5 integration lane with DV4 (high: Lab 2's acceptance; the prose items' hidden check).**
   The grader container's `truth` mode, the sealing (age, a key) and the archive
   `Hidden/labs/Q15/verdicts.tar.age` from the staged tree (Q49).
3. **DV5 integration lane (high: before Lab 2's runs).** The public strata's pools (Q57) and the
   seal of the local stratum's references (§14).
4. **Tools owner (medium).** `specfreeze --pin` misses an open spec whose shipped declaration
   carries a `decreases` clause: `open_spec_symbols` compares the learner's core with the twin's
   measure-free text, from which the shipped `decreases` was blanked (worked around, §12 item 7).
   The prose proof gate has no TRIV variant for an exec prose item whose code needs no proof
   (H5v). Review the `planted:` strand change and the `--exit` skip (§12 item 8); a tool test of
   `--exit` with one empty exit file is not written (the simulation ran it, §11).
5. **Tools owner / DV4 (medium).** Review `fvh.lsp` and `scripts/dafny-server` as Q56's entry
   point (a frozen-core addition), and keep `fvh.lsp` in `fvh/__init__.py` when the DV4 lane
   rewrites it.
6. **Guard owner (medium: before Q15 ships; QPLAN §30 Q60).** The tutor red-team's decoy
   reference directory (a path rule 1 treats as reference) and its fixture; the chapter names it.
7. **Kits lane (high: before Q15 ships).** The chapter (P1's and the battery's answers only after
   their boxes), the written pair with B1 (Lab 2's pre-registration) and the cards 04.6, 04.7,
   03.8, the rubric, the bank with the intermediate tier viva's draws, fixtures and leak patterns.
8. **Q18 lane (low).** Lab 3's planned `max_big` task (author notes §10) is Q15.H5v's prose task.
9. **Records.** A DELTAS entry for Q15 as built (§15).

## 14. Lab 2's local stratum (built)

`bench/local/q/lab2/<card>/tasks/<card>.{dfy,rs}` and `STRATUM.toml`: ten Dafny cards
(`ThirdLimb`, `TopIsZero`, `DropLow`, `ZeroLow`, `SameLimbs`, `HasZeroLimb`, `FirstNonZero`,
`LimbwiseLe`, `KeepLow`, `FitsIn`) and ten Verus cards (`third_limb`, `top_two_equal`,
`is_canonical`, `add_carry`, `sub_borrow`, `min_limb`, `pair_le`, `sig_two`, `add_carry_in`,
`same_length`), each a standalone file: a prose docstring, the implementation with no
specification (Verus: loop-free, so that no proof is needed beyond the specification), an empty
witness. Each reference program (form + reference spec + a witness) passes `vcheck --gate`; each
form verifies as shipped. The reference oracles' `mutants` make 131 mutants; the reference specs
kill 128 (survivors: two equivalent `>=`/`>` and `<`/`<=` swaps at an equality; one mutant does not
resolve). Five first drafts were replaced because their names and statements were earlier items'
(Q01's `LowLimb`/`low_limb`, Q02's `PadZeros`, Q03's `MaxLimb`, Q09's `top_limb` specimen); every
card name was searched against the course's files. The references, kill counts, generator
(`tasks.py`) and kill-rate driver are staged with the hidden truth (`hidden-src/labs/Q15/tasks/`),
never in `Solutions/`: the learner reads `Solutions/` after an item, and Lab 2's references must
stay out of every loop. The task forms carry no mutants: the grader makes them with the frozen
reference oracles. Not built: the public strata (QPLAN §30 Q57) and the pre-registration (B1,
the kits lane's written pair).

## 15. Draft DELTAS entry (for the integration lane to number)

> **Δ? · Q15 code as built; the language server's entry point; planted markers in S10
> specimens — adopted (DV5b, 2026-10-11)**
> - **Status:** Q15's code (practice II-C and Lab 2, family C) on Δ186's model. Like Δ160-Δ194,
>   it names no answer, no exit statement and no prediction answer; the detail is in
>   `Solutions/plans/Q15-code-notes.md`. Builds QPLAN §30 Q56.
> - **Change:** the files of QPLAN §25.1 (17 holes: Dafny 5, Verus 5, Python 7; 11 predictions;
>   1 exit item), the rung-11 agent files with their freeze references, the toolsmith file, the
>   twelve-goal bilingual battery, the four forensic specimens, the client and oracle harness
>   files with frozen tests and a recorded server transcript; `fvh.lsp` and `scripts/dafny-server`
>   (the only route to `dafny server`, under the Dafny cap); `planted:` markers accepted in S10
>   verdict specimens; `firsttry --exit` skips an exit file that holds no item (Q50); Lab 2's
>   local stratum (`bench/local/q/lab2/`, 20 task forms; references staged for sealing). Admitted: H6py-H12py (102); not admitted: H1d, H1v, H2d, H2v (below the
>   band; H2d and H2v on their shortest known proofs, fix round), H3d-H5v (hidden check
>   pending, Q49).
> - **Fix round (DV5b review, 2026-10-11):** H3d's prose task replaced (its specification was
>   layer L5's `NormalizeTrim` hypotheses); battery G09's step is a monotonicity fact (its
>   two-term trigger had been a stable step for H1v); the specimens' stage glossary names no
>   construct; the oracles' default route reaches a verification container
>   (`write_target`'s Lab 2 layout; `fvh.tools`' and `dvl.sandbox`'s benchmark-task pattern
>   takes a lab card's directory; `mksandbox-run` takes a local task's module from its
>   stratum). Detail: code notes §16.
> - **Why:** the four results (code notes §9); the empty-body gate 18/18.
> - **Open:** code notes §13.

## 16. The review fix round (DV5b, 2026-10-11)

Every finding re-verified on the pins before its fix, one solver job at a time inside a 32 GB
scope (`/tmp/dvl0-dv5b-fix/run.sh`); probes and records archived under
`~/.cache/dafny-verus-learn-0/author-probes/dv5b/fix/`.

1. **H3d's prose task replaced.** The hidden truth of the first task (`SigLimbs`) was word for
   word the three `requires` of L5's `NormalizeTrim`, an open import of the same file, and
   equivalent to Q10.H4d's shipped `NormLen` statement. The new task, `EvenLimbs(s)` (every
   other limb from the lowest: positions 0, 2, 4, … in order, nothing else), ships its code
   (`|s| <= 1` returns `s`; else `[s[0]] + EvenLimbs(s[2..])`, Dafny's default measure), a
   client over `|s| == 5` asserting the three limbs, and an empty witness. Reference
   specification (hidden-src `prose/Q15.H3d.toml`, MANIFEST refreshed): no `requires`, one
   `ensures`, a length conjunct and an element conjunct. Probed: with no specification the
   client's assertion fails; with the element conjunct alone the specification is not even
   well-formed (an index out of range) and the client fails; the reference verifies with
   no proof line, and the twin unit passes `--gate` (151). A conjunct-split scan of all six
   prose specifications and twenty stratum specifications against the 1,480 public files
   (`conjscan.py` in the archive) finds no hit but the boilerplate `Valid(a) && Valid(b)`
   (shipped in H5d's own client and many layers). The bank's PP3 diagnostic no longer points
   at a boundary case. The Q15 leak patterns stay at 8 (the README's budget): no pattern for
   the new task.
2. **H2d and H2v below the band.** Reproduced on seeds 1-3: the refutation `CmpTopRefuted`
   with an empty body verifies, and `CmpTop` needs neither `decreases |a|` nor `assert
   Valid(a[1..])` (Dafny: 134 tasks passed on each seed); `lemma_push_lt_refuted` verifies with
   `reveal_with_fuel(seq_to_nat, 4);` alone and `lemma_push_lt` without its `drop_first` and
   `weight` assertions (Verus: 2 verified on each seed). Minimal counts 7 and 13, below 10 and
   15: both `admitted = false, minutes = 0`; the twins trimmed to those proofs (gate: unit 151,
   crate 17; stability §16 item 7).
3. **Battery G09** (P10dv's scenario). Its quantified step was `weight(k + 1) == BASE *
   weight(k)` under a two-term trigger: with three assertions a stable proof of H1v's
   statement. The step is now `weight(k) < weight(k + 1)` (Dafny `Pow`), proved from the step
   and positivity lemmas, which cannot give H1v's equation. Verdicts unchanged (Dafny fails at
   the postcondition, Verus verifies, 6 verified); the trigger-only repair passes the twin gate
   (9 verified) and `specfreeze --against` the shipped goal (0 findings); P10dv's salted pin
   (the answer) is unchanged; the chapter's battery pin re-captured.
4. **Specimen glossary.** The stage lines no longer list the planted constructs as examples
   (same line count; learner files and twins), so a `planted:` marker says where to look and
   the stage stays to be predicted.
5. **The oracles' default route.** Reproduced: `write_target`'s mkdtemp file raised
   `RunnerUnavailable` in `ContainerRunner.course_rel`, and so did a lab card path. Fixed in
   the tools (frozen core, author lane): the benchmark-task pattern of
   `fvh.tools.runners.ContainerRunner.course_rel` and `dvl.sandbox.bench_task` takes a lab
   card's `bench/local/<q|r>/<lab>/<card>/tasks/` (Lab 1's layout too); `dvl.sandbox.build_verify`
   takes a local task's module from its stratum's `STRATUM.toml` (`lab`) when none is named;
   `write_target`'s default directory is `TARGET_LAYOUT = "bench/local/q/lab2/oracle/tasks"`
   under a fresh mkdtemp (learner file and twin). Live runs, Docker 29.1.3, the given
   `vacuity` with `run=None, workdir=None`: Dafny card d01 `proved` for a contradictory
   `requires`, `failed` for a satisfiable one; Verus card v01 the same; the toy quote
   (`vac-container.txt`) re-recorded on that route and re-pinned. Tests: `harness/tests/core/
   test_tools.py` (58 passed, benchmark layouts), `tests/sandbox/test_sandbox.py` (45, a new
   `bench_task`/`stratum_module` case); twins: oracles 26 and lsp_client 31 tests pass. The
   chapter (§5) and the oracles' docstring say a killed run is `unknown` and a refused or
   deferred container run raises.
6. **Chapter text.** §12's freeze claim (Dafny drops a `{:trigger}` in a statement clause;
   `diff -u` added to the after-run review), §9's numbering (B3-B5 cards first, B1, B2 the
   lab report), P3d's `expect` mechanism, H5v's shipped `requires`, the public strata's
   validation (pending); solutions and both fixtures cite DV4 step 3d's throughput (median
   3.7 s per call, thinking off; ≈ 1.8 GPU-h, a lower bound for S1 and V).
7. **Runs on the final files** (archive `dv5b/fix/`): `vcheck --ref --gate` unit 151, crate 17,
   oracles 26 and lsp_client 31 tests; `--brittleness` stable (Dafny unit twin, both solvers
   × seeds 1-3, widest CV 13.9%; crate twin seeds 1-3, 18.0%); `firsttry.sh Q15
   --empty-body` 18/18, exit 0 (H3d's client gate and proof gate pass on `EvenLimbs`; H2d and
   H2v's empty bodies fail; H5v's proof-gate finding reported, not failing); `specfreeze --pin`
   and `--check` 0; `vcheck --ref --pin-counts`; `vcheck --shipped` 10 files, 0 problems;
   `pins.py --ref` 11 checks, 0; `pins.py --update --chapter` (26 entries) and `--ci` 60
   pins, 0; `chapter_lint` 0; `update_rubric_pins.sh --check` all current; the leak verifier
   (15 modules, 1,478 public files) OK; `reference_lint` 0; `--lint-hollow` OK; `avoid.sh`
   OK; the conjunct scan (1 boilerplate hit); fixtures and solutions compile (latexmk, a
   scratch copy); static suites `test_tools_static` 109 (1 skipped), `test_practice_tools_static`
   31, `test_forms_static` 45, `tests/sandbox` 99, `harness/tests/core` 470,
   `test_course_map.py` 367.

## 17. DV5c: the user's decisions D1 and D2, and the tool fixes (2026-10-12)

One solver job at a time inside a 16 GB `systemd-run` scope (`free -g` 97 GB available);
archive `~/.cache/dafny-verus-learn-0/author-probes/dv5c/tools/`. Q13's code notes §11 hold
the rules and the counter.

- **D2: H1d and H1v admitted at the S11 line's 15 minutes** (H1d 8, H1v 7, QPLAN §25.7's
  split), each with the registry's new field `exception = "short-format band: …"`, which
  `scripts/check_course_map.py` accepts only on an admitted item and only with a known kind
  (`short-format band`) and a reason (tests in `scripts/test_course_map.py`). Their other
  three results are §8–§9's, unchanged; re-gated in DV5c's run (below). Q15's admitted minutes:
  verifier 15, Python 102.
- **D1 re-count** (`scripts/pcount.py`): H1d 5 (unchanged), H1v **4** (5 before: its
  one-statement block counts one line). Both stay below the band, covered by the exception;
  H2d 7, H2v 13 (not admitted, unchanged).
- **The exec prose item's TRIV (Δ197's open item).** `prose_proof_gate` (`scripts/firsttry.py`)
  runs TRIV with the twin block's `// triv:` body for a Verus exec prose item; when the twin's
  code holds no proof text (`exec_prose_fn`), TRIV alone is the gate and the light modes, which
  strip proof only, are not run (tests `ExecProseTriv`, 4 cases). H5v's twin declares
  `// triv: { BigNat { limbs: a.limbs.clone() } }` (return the first argument).
  `scripts/firsttry.sh Q15 --empty-body` (733 s): **18/18**, exit 0; H5v: "✓ the given client
  fails without its labelled assume (line 161, 163)", "✓ the twin's statement of `max_big`
  with the declared trivial body (TRIV) fails in every run" (`eb-Q15.txt`). H5v stays not
  admitted (the hidden check, Q49).
- **`open_spec_symbols` and a shipped `decreases` (§13 item 4).** Fixed in `scripts/vcheck`:
  the twin's core is compared as written and with its measures blanked, so a declaration that
  ships a `decreases` and whose twin adds an `ensures` is an open spec again (test
  `OpenSpecs.test_a_shipped_measure_does_not_hide_an_open_spec`). §12 item 7's workaround (no
  explicit `decreases` on Lab 2's prose tasks) stays; re-pinning every freeze found no new open
  spec in Q01–Q15.
- **Dafny statement triggers frozen (Δ204 item 9).** `dvl.dafny.statement_attr_skip`: a
  `{:trigger …}` in a clause is part of the statement (as Verus's `#[trigger]` is); other
  attributes stay dropped. `expected/Q03.freeze`, `Q06.freeze` and `Q15.freeze` re-pinned (only
  the hashes of statements with a clause trigger moved: Q03's `TriggerRosetta`, Q06's
  `FirstPrefix`, `OddBound`, `SecondLimb` and its two specimens' five, Q15's exit
  `NoCarryValid`); `reference_lint` 0 findings (no twin changes a statement trigger). All 24
  battery repairs pass `specfreeze --against` their shipped goals (every repair is in a proof
  line); both agent twins pass `--against` their forensic references. A trigger written into
  G05's `requires` is now `freeze-changed` (probe `g05/trig.dfy`). Chapter §12's paragraph and
  rubric D6 say so; bank K3's probe was re-captured (§17.1).
- **`--exit` with an empty exit file:** a static test (`test_exit_skips_an_exit_file_with_no_item`)
  covers the skip and the refusal when no file holds an X item.
- **The decoy** `Solutions/decoy/Q15/` (`DECOY.md`, `answers.txt`; a canary
  `DVL-DECOY-Q15-36a676172378`, no reference content) with hook fixtures: Read, `cat`, `ls`,
  Grep, Glob and a relative Read are refused by rule 1 (`tests/hooks/templates/
  must_block.tmpl.jsonl`, DV5c rows).

## 18. DV5d: the user's decisions D11 and D12 (2026-10-12)

Applied by DV5d's decisions lane (16 GB scope, one solver job at a time; archive
`~/.cache/dafny-verus-learn-0/author-probes/dv5d/decisions/`). The lane's notes, with the
DELTAS-ready text of every decision it applied, are `Solutions/plans/DV5d-decisions-notes.md`.

- **D11: H1d keeps 8 minutes.** Its `form: trigger` is a presence check, a tripwire: the padded
  construct-free variant (a vacuous triggered quantifier beside a proof that names no trigger
  where it needs one; Δ216 item 2) passes it, and `/review-code`'s reader closes it. The Q15
  rubric's C1 now says so: A5's `trigger` check sees only that a trigger is present; a
  triggered quantifier the proof does not use (Probe D: the proof still verifies with it
  deleted) is padding, the same finding as no trigger at grade 1; "the trigger is right" holds
  only when the triggered step is one the proof uses. The padded variant stays unrecorded as a
  `cfree:` line (it would fail the Q15 gate, Δ216 item 2). Δ173's text gains the exception
  (the DELTAS-ready bullet is in the lane notes, §3, D11).
- **D12: the S11 pair's 15 minutes are split H1d 8 + H1v 7** (QPLAN §25.7's split; the registry
  as built at DV5c, unchanged). Δ206's D2 bullet and Δ216 item 1 are closed by it.
- Nothing else of Q15 moved: `MODULES.toml`'s Q15 table, the files, the pins and the gates are
  as §17 left them; `pins.py --ci --module Q15` 60 pins, 0 problems (re-run on this tree).

## 19. DV5d: the grader's judging step and Lab 2's hidden verdicts (2026-10-12)

Built and run by DV5d's judging lane (`Solutions/plans/DV5d-judge-notes.md`, with the
DELTAS-ready text; archive `dv5d/judge/`).

- `Hidden/labs/Q15/` re-sealed with `judge/oracles.py` (the twin's oracles, byte for byte) and a
  `DVLCANARY` (52 files). `truthcheck judge Q15` judges a Lab 2 card's delivery with those
  oracles' `implication`, `vacuity` and `classify` (the hidden verdict of §25.6's confusion
  matrix) and a prose spec by a two-way refinement check; `fvh report Q15 --judge all --truth
  Hidden/labs/Q15/verdicts.tar.age` judges every lab run.
- On the final image: the six prose references `faithful` against themselves and 18 of 19 wrong
  specifications as expected (H3v's `n <= a@.len()` is `undecided`, expected weak: its weakness
  needs an induction over the count; a count defined from the front is `undecided` as
  designed); the twenty card reference programs `faithful`; eight planted deliveries `weak`,
  `strong`, `vacuous` or `mismatch` as expected.
- **H4v admitted at 18** (§25.7's planned minutes): 34 proof lines (in the band), `firsttry.sh
  Q15 --empty-body` 18/18 re-run on this tree, the crate twin stable on seeds 1-3, pinned APIs,
  and its hidden check. **H3d, H4d, H5d, H3v, H5v stay at 0**: their hidden checks hold but they
  are below the band; their minutes are the user's decision (the judging notes §6 item 1).
  Admitted Q15 verifier hole minutes: H1d 8 + H1v 7 + H4v 18 = 33.
- The oracles' reading of a requires change (an added requires is `strong`, against H11's gloss)
  is the judging notes' §6 item 2.
- The chapter's §0 and Lab 2 section and the two prose files' headers still say the hidden check
  is recorded as pending (the kits lane's item).

## 20. DV5e: the user's decisions D21 and D22 (2026-10-13)

Applied by DV5e's decisions lane (16 GB scope, one solver job at a time; captures under
`~/.cache/dafny-verus-learn-0/author-probes/dv5e/decisions/`; the lane's notes with the
DELTAS-ready text: `Solutions/plans/DV5e-decisions-notes.md`).

- **D21: H3d, H4d, H5d, H3v and H5v admitted at 18 each** under a new declared exception kind,
  `"hidden-check spec: <why>"` (the judging notes §6 item 1, option (a)). Each entry's reason
  gives its count by `scripts/pcount.py` on the twin: H3d `EvenLimbs` 0 proof lines (statement
  2), H4d `TopDiff` 0 (3), H5d `SatSub` 0 (3), all below the Dafny band's 10; H3v
  `count_nonzero` 7 (statement 3, with a 4-line spec fn) and H5v `max_big` 0 (statement 7),
  below the Verus band's 15; H4v stays admitted at 18 with no exception (34, in band). The
  checker (`scripts/check_course_map.py`: `HIDDEN_CHECK_KIND`, `hidden_check_problem`,
  `HIDDEN_CHECKS_HELD`, `sealed_labs`) accepts the kind only on an admitted H prose item of
  one of the module's exercise files that names no contractor, whose hidden check is recorded
  as holding (Δ220's runs; the record holds Q13.H3v, Q15.H3d–H5v and Q17.H3d) and whose
  module's sealed truth `sandbox/truth.toml` pins. **Q15's minutes now reconcile with design
  §7.5 and QPLAN §25.7:** the Lab 2 prose line carries 108 of 108 (6 × 18); S9's H items 27 of
  27, S11's 15 of 15 (D2), the oracles 75 of 75; S12's H2d/H2v stay gated (Δ199: below the
  band on their shortest known proofs), so the module's H items carry 225 of the plan's 240.
  The four results: the gates re-run on this tree (`firsttry.sh Q15 --empty-body` **18/18**,
  exit 0: each of the five, the client gate and the prose proof gate, H5v's by its TRIV body),
  stability and pinned APIs as §9 recorded, the hidden check per §19.
- **D22: H11's and the Verdict glosses reworded, text only** (the judging notes §6 item 2,
  option (a)). In `harness/q/fvh_q/oracles.py` and its twin: the `Verdict` docstring (the two
  lemmas read a specification's requires and ensures together inside the reference's requires;
  an added requires the reference's requires and ensures do not give narrows it and counts as
  `STRONG`; a dropped requires is not seen) and its STRONG comment ("it claims more (correct
  behaviours fail it) or adds a requires"), the `Implication` docstring and a sentence of H11's
  docstring. Code, tests and the freeze unchanged (`specfreeze --check Q15` 0 findings); the
  twin's frozen tests `vcheck --ref --gate Solutions/harness/q/fvh_q/oracles.py` **26 passed,
  0 failed**; the learner file as shipped 1 passed, 25 failed, 4 holes (as before). Re-pinned:
  the chapter fence `py-oracles` (hole lines 270, 297, 314, 345) and `expected/Q15.chapter.toml`;
  the rubric's twin pin (`6cb4f036…a259`). Q15's archive was re-sealed afterwards by DV5e's
  Lab 2 public-forms lane with the new twin; Q13's and Q17's sealed `judge/oracles.py`
  (`e168aaed…`) keep the old comment text, their code equal to the twin's (an AST comparison
  with docstrings removed): re-copy it at their next re-seal.
- Still stale (other owners): the chapter's §0, the Lab 2 section and the two prose files'
  headers ("the hidden check is recorded as pending"); bank Q15's K-probe insight line on the
  two lemmas (it glosses `RefImpliesSpec`'s failure as "forbids an output the reference
  allows", which an added requires also fails) and its "Q13's hidden check is the same pair"
  (the grader's prose check is the four-lemma refinement, the judging notes §1); QPLAN §25.2's
  prose-specs row and §25.7/§25.8's **As built** note (they say the five are not admitted).

## 21. DV5e: Lab 2's public strata (2026-10-13)

Built by DV5e's lab2pub lane (`Solutions/plans/DV5e-lab2pub-notes.md`, with the DELTAS-ready
text; archive `dv5e/lab2pub/`). §14's "Not built: the public strata" is closed.

- **Cards:** `bench/local/q/lab2pub/` (tracked, learner-owned): vp1-he100, vp2-he033, vp3-he077,
  vp4-he035, vp5-he060 (HumanEval-Verus) and dp1-he048, dp2-he052, dp3-he063, dp4-he159,
  dp5-he062 (vericoding's own `humaneval` translations), each in Lab 2's form by
  `scripts/dvl/benchstrip.py`'s `verus-lab2-form` / `dafny-lab2-form` (the specification and the
  proofs removed, the code, the vocabulary and the HumanEval prompt kept, an empty witness), with
  `STRATUM.toml` and `NOTICE`. The grader's host half lists them with the local twenty.
- **Draw:** pre-registered and amended once before any seal (`dv5e/lab2pub/draw/`), recorded in
  `bench/public/POOLS.toml`'s `[[draw]]` tables; every drawn answer verified under seeds 1-3.
- **Hidden truth:** the ten references and reference programs sealed in `Hidden/labs/Q15/` (72
  files; the plaintext now at `dv5e/lab2pub/hidden-src/labs/Q15/`, superseding §19's
  `dv5d/judge/hidden-src/`), `judge/oracles.py` re-copied from the twin after D22 (§20's "re-copy
  at the next re-seal" is done for Q15; Q13's and Q17's archives keep the old copy).
- **Judged in the grader container:** the ten reference programs faithful, ten weakened
  statements weak (20 of 20 as recorded beforehand); the thirty reference programs verified by
  `truthcheck validate` (in batches: a whole-language validate of Q15 now exceeds the manifest's
  argv limit).
- **Unlike the local cards,** 8 of the 10 public forms do not verify with the reference statement
  alone (the code needs proof annotations), so the S arms' protocol on them, the kept vocabulary,
  the tracked derived files and Lab 1's overlap with the five Verus tasks are decisions for the
  user (the lane notes §9 items 1-4).

## 22. DV6: the user's decisions D27-D30 on Lab 2's public cards (2026-10-14)

Built by DV6's lab2 lane (`Solutions/plans/DV6-lab2-notes.md`, with the DELTAS-ready text;
archive `dv6/lab2/`). §21's last bullet is settled: a public delivery may add proof
annotations and the lab gate checks the code unchanged (`scripts/dvl/labcode.py`, `vcheck
--gate --lab-task`; the local cards take the check too, without annotations); S1's mutant kill
on a public card mutates the delivery's annotated body; the forms no longer ship the
non-recursive definitions only the specification used (12 on six cards), which are sealed with
the references (`definitions`); the forms were rebuilt on the same draw, Q15 re-sealed (72
files; the prose references, the oracles and the canary unchanged, so `HIDDEN_CHECKS_HELD`
names the DV6 manifest) and the ten cards attested under DV6. NOTICE is generated from the
manifest's pins and the installed licences (D29); Lab 1's HumanEval-Verus draw excludes the
five public Verus tasks (D30, `get_bench.sh --members`). Three measured readings await the
user (the notes §9): the kill rate on annotated code mostly measures the annotations; a
renamed sealed definition under a quantifier is judged `undecided` (vp3); the vericoding arm
needs the gate's `--lab-code own`, which the batch cannot pass yet.
