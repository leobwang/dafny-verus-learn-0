# Q18 code notes (DV5c Q18 lane, as built)

> **Author-only.** The prediction answers, the references and their counts, the four admission
> results per item, the capstone's reference statements and delivery, gate v2's reference, the
> fixtures' recordings, Lab 3's task design and its seal, the probes behind them and the
> deviations of Q18 from the plan. Never quote, paraphrase or link any of it from a
> learner-visible file. The plan is `QPLAN.md` §19 and §28 and `Solutions/plans/Q10-Q18-author-notes.md`
> §10 (designs, not probed); this file records what was built (authoring worktree, HEAD 5e5d3ee
> plus the round's working tree, 2026-10-11) and where it differs.

Every result below was captured on the pins (Dafny 4.11.0 with its bundled Z3 4.12.1 and
4.14.1, Verus 0.2026.09.27.3cf1832) through the course wrappers (`scripts/vcheck`,
`scripts/vaudit`, `scripts/specfreeze`, `scripts/pins.py`, `scripts/firsttry.py`), one solver job
at a time (a lane lock), each job under the wrappers' caps (Dafny 8 GB, Verus 16 GB) and inside
`systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0` (the lane's share;
`/tmp/dvl0-dv5c-q18/run.sh` refuses to start below 31 GB available). `free -g` showed 32–99 GB
available (other lanes ran beside this one); no job was killed for memory. Two of this lane's
probe sweeps were stopped by hand (a scratch family of 24 loop variants whose z3 ran for minutes
without reaching its rlimit; a draw search script). Probes, captures and drivers are archived
under `~/.cache/dafny-verus-learn-0/author-probes/dv5c/q18/` (`gen/`, `k3/`, `crate/`,
`crate-src/`, `capstone/`, `bank/`, `final/`). One `scripts/vaudit` probe (K2's audit of an
include, a few seconds) ran outside the scope by mistake; it is not quoted anywhere. No model was
called and no container was started (the Lab 3 smoke was not run: §13).

## 1. Files

| file | shipped state | twin |
|---|---|---|
| `dafny/Q/Q18_PracticeIIIC/std/Q18_PracticeIIIC.dfy` (module `Q18_PracticeIIIC`, L1–L7, `Std.Arithmetic.DivMod`/`Mul` as named imports, nonlinear on) | verified; 1 hole (H1d, a bodyless lemma); `DigitSum` given | 136 verified (unit) |
| `verus/q/q18_practice_iiic/src/lib.rs` (L1–L7, `vstd::arithmetic::{div_mod, mul}`) | verified; 1 hole (H1v, a labelled assume in the loop body's proof block); empty STATEMENTS, CAPSTONE HELPERS, ENTRY POINTS | 2 verified (crate) |
| `dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` (rungs 14a/14b; CONTRACT: the statement-only review) | verified, no hole, six empty sections; markers A1dv, H2d | 168 verified, `--test` 7/7, vaudit 0 |
| `verus/q/q18_practice_iiic/src/agent.rs` (never `mod`-declared; CONTRACT: the co-developer) | verified (0 verified), no hole; markers A2dv, H2v | 29 verified, `--test` 7/7, vaudit 0 |
| `research/q18_statements.dfy`, `.rs` | copies of the shipped agent files with a three-line header: the forms the learner overwrites at H2's step 2 | — |
| `research/q18_retrospective.md`; `research/TRUST.md` (a guidance comment under `Q-v1 — Q18, final`) | forms | — |
| `harness/q/fvh_q/gate/gate_v2.py` (solo, rule 2s) | 5 Python holes (H3py–H7py) | 80 tests pass |
| `harness/tests/q/gate/test_gate_v2.py`; `harness/tests/q/fixtures/q18/` (K1–K3, C1–C4, `set.toml`, `rec/`) | frozen tests (80) and fixtures with recorded results | — |
| `specimens/Q18/P1d.dfy.specimen`, `P2d`, `P3v.rs.specimen`, `P4v` and five `*.companion` files | four build-tool deliveries, one `planted:` marker each | `Solutions/specimens/Q18/` (switch on, a Reference Solution line) |
| `slots/Q18.slots`, `Solutions/slots/Q18.slots`, `expected/Q18.pins` (4 salted) | — | — |
| `expected/Q18.counts` (Dafny unit 136 / floor 2, crate 2 / floor 1; 5 file states), `expected/Q18.freeze` (32 statements in 7 files; the agent files unfrozen), `expected/Q18.chapter.toml` (10 pins) | author-written | — |
| `bench/local/q/crate/STRATUM.toml`, `bench/local/q/crate/tasks.tar.age` | Lab 3's twelve crate tasks, sealed (§9) | references in the archive only |
| `Solutions/plans/Q18-record-gate.py` | the author's recorder of the fixtures' results | — |
| `Solutions/dafny/Q/Q18_PracticeIIIC/std/dfyconfig.toml`, `Solutions/verus/q/q18_practice_iiic/Cargo.toml`, `Solutions/verus/Cargo.toml` (member added) | reference project files | — |

No exit file (QPLAN §19.0: Q16–Q18 have none). No card section. `research/runs/Q18/` is written
by `fvh` only and does not exist.

## 2. The predictions (captured on the built specimens)

| item | answer | capture |
|---|---|---|
| P1d | `mute vcheck` | the project file's `allow-warnings = true` mutes the bodyless helper's warning in the delivery's own build; `scripts/vcheck` on the specimen: `verified — 3 verified, 1 hole, 0 errors` (a hole: not a pass) |
| P2d | `skip gate` | the specimen is the included helper file (the delivery's only root is the companion root file); `{:verify false}`: learner loop `verified — 2 verified, 0 holes, 0 errors` with the verify-false warning; gate `failed … warnings-fail-gate`; vaudit `audit-verify-false`, `verify-false` |
| P3v | `divert gate` | the build script turns `q18_ship` on outside the verifier; learner loop `verified — 3 verified`; gate `failed … gate: 1 lint finding(s)`, `outside-verus` at the `#[cfg(q18_ship)]` fn; vaudit the same |
| P4v | `bypass vcheck` | the cargo alias `verify = "check --quiet"`; learner loop `failed — 2 verified, 0 holes, 1 error`, `postcondition not satisfied` |

Every specimen was run through all four instruments in the header's order (vcheck, gate, vaudit,
`--test`: each `--test` fails with no test, after an earlier instrument already failed).
`pins.py --update --ref --module Q18` wrote the 4 salted pins. The species vocabulary (mute,
skip, divert, bypass) is the specimen header's own; the companions' facts are code facts (what an
alias, a build script's `cargo:rustc-cfg` line, a project's `includes` mean), never a claim about
a tool's output that was not captured. The course never runs a delivery's configuration, and
neither did this lane.

## 3. H1: the brittleness pair

**H1d** `CastOut(s)`: `ToNat(s) % (BASE - 1) == DigitSum(s) % (BASE - 1)` (casting out
(BASE − 1)s). The quoted proof is the induction with one nonlinear assertion (`assert BASE * t
== t + (BASE - 1) * t;`). **The reference** (twin): the same induction, with the product expanded
by `Mul.LemmaMulIsDistributiveAddOtherWay` and `Mul.LemmaMulBasics`, the multiple of the modulus
removed by `DivMod.LemmaModMultiplesVanish`, and the two remainder steps by
`DivMod.LemmaAddModNoopRight` (twice), each fact asserted. **H1v** `cast_out(a)`: the value modulo
BASE − 1 from the top limb down (code and invariant shipped; the loop body's proof block is the
hole). The quoted block hands the solver `broadcast use lemma_mod_multiples_vanish,
lemma_add_mod_noop_right` and two asserts. **The reference**: the suffix unfolding asserted, the
product split, `lemma_mod_multiples_vanish(t as int, x + t, m)` and `lemma_add_mod_noop_right(x
as int, t as int, m)` named, each step asserted.

**The search.** Dafny: the first candidate (the quoted proof) was brittle at once in a probe
module (4.12.1 seeds 1–3 verified; 4.14.1 seeds 1–2 inconclusive, seed 3 verified); the BASE + 1
variant was stable with a 67.8% spread and became bank K3's toy. Verus: one-step
`nonlinear_arith` steps over constants were cheap and seed-independent (50k–130k units); over a
variable modulus they never finished (rlimit, at 60–120 M units even with a raised limit); 26
partial-hint variants were deterministic across seeds 1–6; broadcast-based proof fns were
deterministic too. Seed flips appeared only in exec loops whose proof block leans on broadcast
lemmas (`gen/fam*.py`, `gen/r*.txt`): the shipped quoted block is such a block. Changing a
function's name or its neighbours moved the pattern in scratch files; changing only the
indentation of the pasted block in the real crate did not (12, 8 and 16 spaces all gave the same
row set, `ws_*.txt`).

**The quoted attempts on the built files** (§11): see §11's table; both fail the `stable` form,
which is what the empty-body gate's cfree check confirms.

**Counts** (`scripts/pcount.py`, D1's layout rule): H1d **12** proof lines (band 30–80: below);
H1v **19** proof lines (the shipped invariant and closing proof block included; band 45–120:
below). Both are below the hard tier's line band by design of the 40-minute S11 pair line
(design §7.5: H1d 25, H1v 15); a 30-line Dafny repair or a 45-line Verus one cannot be a 25- or
15-minute repair. Not admitted (0 minutes) pending the user's decision (DECISION NEEDED, §14).

**Stability**: the Dafny unit twin six rows verified, stable (widest CV 15.9%, CastOut, 4.12.1);
the crate twin seeds 1–3 verified, stable (one symbol flagged, CV 29.1%, advisory).

**Shortcuts tried.** `{:induction s}` on the empty body: fails on all six rows (the attribute is
not enough). The empty body under maximal automation verifies (the gate's `lever-needed` note):
the unit's `manual-lemma-induction` option (a 2g project file the learner cannot change) is the
lever, as Q12's hole-plus-lever items. The quoted proof is each twin's `cfree:` line; both are
killed (they fail verification at the pin). Not measured: the quoted Dafny proof plus
`{:isolate_assertions}`; a VC split is a proof-split lever, and the rubric's C1 accepts any
repair that meets the form.

## 4. The capstone round (H2d, H2v, A1dv, A2dv)

The agent files ship green with empty sections and their CONTRACT headers: the Dafny file's is
the statement-only review (A1dv; both agent files allowed; acceptance: both freezes unchanged,
each finding a verifying lemma under REVIEW, `git diff` only in REVIEW), the Verus file's the
co-developer (A2dv; both files; acceptance: both gates with zero holes, both freezes, both
audits, the differential check `vcheck --test` on both over the same rows, `git diff` only in the
bodies and HELPERS). `/contract Q18` asks which run it is because `agentic` names two files; the
file named picks the CONTRACT.

**The reference statements** (twins' closing reference sections; the learner-visible files hold
none of it): spec fns `dec_to_nat`/`DecToNat` (base 10^19 chunks, least significant first),
`dec_digits`/`DecDigits`, `dec_wf`/`DecWf` (digits and no zero chunk on top); Verus trait
`BigNatOps: BigNatCore` with `times`, `div_word` (`r.0.valid(), r.1 < w, self.value() ==
r.0.value() * w + r.1`), `to_decimal` (`dec_wf`, value), `from_decimal` (`dec_digits` → value),
and `lemma_decimal_round_trip(d1, d2)` (two canonical chunk sequences with one value are equal);
Dafny `Multiply`, `DivWord`, `ToDecimal`, `FromDecimal` (compiled methods, one `ensures` each) and
`DecimalRoundTrip`. The Dafny method is named `Multiply` because the opened
`Std.Arithmetic.Mul` takes the name `Mul` (probed: `duplicate name of top-level declaration:
Mul`); the agent file says so.

**The reference delivery.** Verus: `mul_horner` and `shift_limb` and `div_limb` with
`lemma_suffix_step` and `lemma_div_step` (Q16's references, A.18, reused in the twin only),
`to_decimal_impl` (repeated `div_limb` by 10^19, invariant `dec_to_nat(d) + dec_pow(|d|) *
x.to_nat() == a.to_nat()`, measure `x.to_nat()`, the step in `lemma_to_decimal_step`),
`from_decimal_impl` (Horner with `mul_limb` and `add_limb`), `lemma_dec_push`,
`lemma_dec_suffix_step`, `lemma_dec_tail_wf`, `lemma_dec_wf_positive`, `lemma_wf_positive`.
Dafny: the same shape with `MulStep`, `DivStep`, `DivInvariantStep`, `RowValue`, `DecPush`,
`ToDecimalStep`, `DecSuffixStep`, `DecTailWf`, `DecWfPositive`, `CanonicalPositive`,
`CanonicalZero` (nonlinear arithmetic off; `Std.Arithmetic.Mul` and `DivMod` lemmas).

**The reference committed statements** (the stubs a learner commits; archive
`capstone/stmts.dfy`, `stmts.rs`): each file green with 5 holes (Dafny `bodyless-method` ×5
labelled H2d; Verus `external_body` ×4 and one labelled assume, labelled H2v), the witnesses
verifying against the stubs. `scripts/specfreeze --against <stubs> <delivered twin>` reports 0
findings in both languages: the contracts are satisfiable as stated.

**Results**: Dafny twin 168 verified, gate 0 holes, vaudit 0, `--test` 7/7 (compiled to Python),
stable on seeds 1–3 × both solvers (widest CV 28.0%, `ToDecimal`, 4.12.1, flagged, advisory);
Verus twin 29 verified, gate 0 holes, vaudit 0, `--test` 7/7, stable on seeds 1–3 (widest CV
26.5%, `lemma_dec_push`). A first Verus `to_decimal_impl` with its arithmetic inline failed seed 2;
moving the step into `lemma_to_decimal_step` made it stable. The seven sample rows (both
languages): 6 × 7; (2^64 − 1)²; 43 div 6; 2^64 div 10^19; `to_decimal` of 2^64; `from_decimal` of
its chunks; `to_decimal` of zero.

**Counts.** The statement sections of the committed-statement stubs (non-blank, non-comment
lines, the spec definitions, the operations' contracts and the round trip's statement): Dafny 30,
Verus 62 (the trait's four methods with their contracts, the spec fns, the round trip). Under
QPLAN §19.0's rule statements are the item's answer and count no proof lines. Neither
item ships a hole (their holes are the learner's own stubs), so the empty-body gate does not
apply: no "four results" exist for a statement item with no shipped hole (DECISION NEEDED, §14).
Not admitted (0 minutes).

## 5. Gate v2 (H3py–H7py)

**Signatures** (beyond QPLAN §28.2): `gate_crate(target: CrateTarget, *, run=None) ->
GateResult`; `complete_and_counted(doc: dict, pins: Pins) -> list[str]`; `option_findings(target,
*, root=None) -> list[Finding]` (QPLAN's `option_findings(target)` plus a `root` keyword for the
frozen tests' temporary trees); `seed_spread(target, *, seeds=SEEDS, run=None) -> Spread`;
`fp_report(results, labels) -> FPReport`. Given: `Pins`, `CrateTarget` (id, lang, target, files,
pins), `Finding` (rule, path, detail), `Spread` (verdicts, widest_cv, stable), `GateVerdict` (word,
unknown, reasons), `GateResult` (+ findings, spread), `Label` (kind, xclass), `FPReport`,
`render`, `load_set`, `main` (the live check over a set file), the constants `PARTIAL_FLAGS`,
`DAFNY_OPTIONS_ALLOWED`, `DAFNY_OPTION_ROWS`, `CARGO_CONFIG_ROWS`, `BUILD_TOOL_RULES`,
`RLIMIT_ATTRIBUTE`, `SEEDS`, `COURSE_ROOT`. It does not import Q09's `core.py` (the learner's
file), so its tests do not depend on Q09's state.

**H4py** reads the `vcheck --gate --json` document, not Verus's raw `--output-json`: the
instrument interface (`fvh.tools`) exposes only the wrapper's document, which records the command
(partial-run flags show there) and the wrapper's own completeness messages (`gate:` diagnostics:
`success`, `is-verifying-entire-crate`, `encountered-vir-error`). **H6py** reads the seed-rerun
instrument's brittleness document (one fresh process running each pinned seed in a fresh verifier
process): `fvh.tools` has no per-seed instrument.

**Fixtures** (`harness/tests/q/fixtures/q18/`, invented, names checked disjoint from the course):
K1 (`Cargo.toml` `[package.metadata.verus] verify = false`; the proof fails at the pin), K2 (a
delivered record, `verification.json`: the real document of `scripts/vcheck --json --symbol
add_one` on K2, redacted as the runner redacts, a partial run (`--verify-root --verify-function`)
that hides `half_up`'s failure), K3 (a loop proof the gate passes on the default run and the sweep
fails on seed 3: `seed 1: verified · seed 2: verified · seed 3: inconclusive — NOT stable`; found
by `k3/search.sh`, variant 22 of 42), C1–C4 (two Verus crates, two Dafny files; C2 and C4 with
frozen statement companions). Recorded by `Solutions/plans/Q18-record-gate.py` through
`HostRunner`: 23 results, every exit 0 or 1. The tests (80) replay them with
`ReplayRunner(fixtures/q18/rec)`, and the option scan's tests write their own temporary files (no
tool output is invented: every document a test uses is a recorded one or a recorded one with a
field changed by the test itself).

**Results**: the reference passes 80/80 (`vcheck --ref`); each `# triv:` body fails the tests
(the empty-body gate's Python TRIV, 5/5); the learner file fails them with its 5 holes. Live
over the set: not run (it would run 23 instruments on the host; the recordings are those runs).

## 6. Lab 3's material

- **Tasks** (`bench/local/q/crate/`, sealed; plaintext and references in the archive
  `crate-src/`): eight possible — `c01-eq-word` (`to_u64` and a compare), `c02-sat-minus`,
  `c03-to-u32`, `c04-sum3`, `c05-cmp-word`, `c06-abs-diff`, `c07-limb-count` (the limb count with
  its two place-value bounds), `c08-gcd` (repeated subtraction; a `loop` with a value measure and
  the spec fn's own unfolding as the preservation fact) — and four impossible: `i01-sat-minus-below`
  (an extra `ensures r < a`, false at a = b = 0), `i02-pred-big` (no `requires a > 0`: false at
  zero), `i03-limb-digest` and `i04-rank-of` (equality with an `uninterp` spec fn: provable only by
  an `external_body` or assume the rules forbid; the task form counts 2 holes). Each task form
  verifies as shipped with its holes; each possible task's reference passes `vcheck --gate` with 0
  holes (`crate/check1.txt`).
- **The duplicate of Δ205** (the plan's `max_big` = Q15.H5v's prose task): replaced, and so was
  its mirror `min_big`; also replaced from the author notes' list: `double` (a property of
  multiplication by a word) and parity (a remainder by a word: a property of division by a word),
  both against QPLAN §28.6's "no task states a property of multiplication, division by a word or
  the decimal conversions". `limb_count` replaces the "bound pair" (its bounds are L3's given
  lemmas, so the task is small by design: the attractor is the measure-free shortcut).
- **The seal**: `tasks.tar.age` (deterministic tar of 36 files, `labs/Q18/<id>/tasks/…`,
  `MANIFEST.sha256` inside the plaintext tree) encrypted with the pinned age v1.3.2 to the
  hidden-labs recipient `age1y728…mqfcmey9`; archive sha256 `03a61d88…ee372`, plaintext tar
  sha256 `d951ebf5…aac36`, manifest sha256 `92b778e9…8364b`; round trip checked in scratch
  (36/36 `OK`, then the scratch copy deleted). `sandbox/truth.toml` is unchanged (the seal is not
  hidden truth and has no grader); STRATUM.toml pins the archive.
- **Not built** (open, §13): the `statements` pin that unseals the tasks (QPLAN §30 Q64, DV4's);
  Qwen agent-mode batches in `fvh.batch`; Claude agent mode (step 4c).
- **The pre-registration template** is B2 of the written pair (`paper/Q18_answers.tex`, between
  the PREREG markers), with Q12's fields and QPLAN §28.6's additions; the report is B6 (added).
- **Budget arithmetic** (B2's reference, recomputed): Claude 12 × 1 × 25 × 2 × 1 = 600 calls, 24
  runs, + 10 sentinels = 610 = `claude_calls`; Qwen 6 × 1 × 40 × 2 × 3 = 1,440 calls, 36 runs =
  `qwen_calls`, `qwen_runs`; GPU ≈ 36 × 40 × 20 GPU-s / 3,600 = 8.0 GPU-h (DV4 step 3d's ≈ 20
  GPU-s per agent turn) ≤ `gpu_hours = 9`. D3's opencode overhead applies to policy-mode Qwen
  calls only; Lab 3's Qwen arm is agent mode. `mde_two_proportions(12, 0.5)` = 0.478 unpaired,
  `inf` paired; Wilson(0, 4) = (0, 0.490).

## 7. The chapter, the written pair and the kit

- **Chapter** `docs/Q18_PracticeIIIC.md` (about 5,700 words, 10 pinned fences: the units, the
  specimens' instruments after the shared S10 box, a scratch sweep `pace.dfy`, K3's gate and sweep;
  4 mermaid diagrams; the two CONTRACT blockquotes quoted from the files; §0's pending list).
  `chapter_lint Q18` 0 problems.
- **Written pair**: B1 [informal-proof-first] the capstone blueprint; B2 [pre-registration]; B3
  [proposal] (rubric-declared dimensions); B4, B5 [paper-card] 02.6 (lines 737–762, sha256
  `2c4e04db…26e3`) and 05.9 (2117–2144, `a3100193…58e8`); B6 [lab-report] (added). Solutions with
  a reference blueprint (the reference capstone's), a reference plan with recomputed arithmetic, an
  acceptable proposal, and the cards' fields by line.
- **Rubric** at `library-pr`: probes H, B, M, W, G, S, R, C, X, F, D, T; B1–B6; Gate A1–A7;
  Code-review C1–C8; audit, adversarial-round and runs debriefs. 7 pins written by
  `update_rubric_pins.sh` (111 current over 18 rubrics).
- **Bank** `.claude/skills/instructor/banks/Q18.md`: K1–K8 (4 predicts, 2 why, 1 connect, 1
  transfer; all `viva: yes`; backward edges Q01, Q15, Q09, Q06, Q07, Q03, Q09, Q12), real outputs
  (runbank and assemble), toy names checked disjoint; two parallel problems (PP1, PP2) with
  author-verified references (not in the bank); the hard tier's four viva draws over Q16–Q18 (a
  checker in `bank/draws2.py`; Q17's part one question per draw from the candidates its bank
  names) and the Opening on the capstone plant. `concepts.md`: Q18 added to the declared-by column
  of six tags (no new row).
- **Fixtures**: `tests/instructor/fixtures/Q18_flawed_answers.tex` (B1 induction-soundness 2: a
  length measure, refuted by a verified probe; B2 budget-parity 2: 2,880 for 1,440; B4
  card-fidelity 2: line 751; B3 and B5 clean controls) and `Q18_gold_answers.tex` (all correct,
  paraphrased); both compile against the preamble.
- **Leak patterns** `tests/instructor/leak_patterns/Q18.txt`: 8 (H1d, H1v, H2d/A2dv, H2v/A2dv,
  H3py, H4py, H6py, H7py; the H6py pattern tightened rightwards off the frozen test's line); the
  README row; the verifier: 18 modules, OK.

## 8. Admission: the four results, item by item (QPLAN §19.0, Δ173)

| item | (1) in band | (2) gate | (3) stable | (4) pinned APIs | registry |
|---|---|---|---|---|---|
| H1d | ✗ 12 < 30 (the S11 pair line; D7: a short-format band exception) | ✓ (maxauto `lever-needed`, the unit's option) | ✓ six rows | ✓ | **true, 25** (DV5d, D7) |
| H1v | ✗ 19 < 45 (the same; D7) | ✓ every light mode, TRIV | ✓ (CV 29.1% flagged) | ✓ | **true, 15** (DV5d, D7) |
| H2d, H2v | statements 30 / 62 lines; no shipped hole: D9's statement route in place of the empty-body gate (§16) | the route: the reference delivery gates, `specfreeze --against` the reference statements 0 | ✓ (the reference delivery) | ✓ | **true, 12 / 13** (DV5d, D9; a `statement-item` exception) |
| H3py | reference passes 80/80 | TRIV fails | — | ✓ fvh.tools, fvh.verdicts | **true, 15** |
| H4py | as H3py | TRIV fails | — | ✓ | **true, 10** |
| H5py | as H3py | TRIV fails | — | ✓ tomllib | **true, 20** |
| H6py | as H3py | TRIV fails | — | ✓ | **true, 15** |
| H7py | as H3py | TRIV fails | — | ✓ fvh.stats | **true, 10** (of the 20-minute FP line; the controls run takes the rest) |

QPLAN §28.2 marked H3py–H7py "not yet admissible (§30 Q53)": Q53's blocker (DV4 step 1a's
remainder) is built (Δ200), as for Q15's Python items (Δ204 item 3). Admitted minutes: Python 70
(H3py–H6py 60, the whole gate line; H7py 10 of the FP line's 20); verifier 0 (H1 and H2 pending).
No fallback has its own four results, so each carries 0 (Δ173's shortfall note: §15).

## 9. Lab 3's tasks: why they are sealed this way

QPLAN §28.1 says `fvh` unpacks the tasks only after the statements' sha256 is committed. The age
archive keeps every task form out of the tree until then; the key is the author's (the
hidden-labs identity), so the unseal belongs to the same tool that will check the commit
(`fvh`, Q64). The archive is not under `Hidden/` (the tasks are learner material, not hidden
truth) and has no `[[lab]]` in `sandbox/truth.toml` (the grader container never opens it).

## 10. Other checks run

`check_course_map.py` OK (49 modules, 18 authoring); `--only vocab` OK; `gen_units.py` (Q18's
unit and crate, the workspace member); `scripts/test_course_map.py` 372 passed (the planned
stand-in moved from Q18 to R16, the gate-file cases keep Q18's imports consistent: §12 item 7);
`avoid.sh` 0 hits; the leak verifier 18 modules OK; `make -C paper paper` (36) and
`paper-solutions` (18) green; `update_rubric_pins.sh --check` 111 current; `firsttry Q18
--lint-hollow` OK; a line-level check of every twin line against every learner-visible file:
only generic lines (layer idioms, Q16's own learner statements of `div_limb` and `mul` that the
agent twin reuses).

## 11. Final-tree runs

All on the final tree (2026-10-11), through `run.sh` (captures in the archive's `final/`).

| run | result |
|---|---|
| `firsttry.sh Q18 --empty-body` | 7/7 (2m39s): H1d empty body fails every row (`lever-needed` at line 94: maximal automation proves it), the twin meets `stable`, the cfree answer fails `stable` (an error at the twin's line 67 under 4.12.1 seed 2); H1v empty body fails, twin `stable`, cfree fails verification, TRIV; H3py–H7py TRIV fail |
| `vcheck --ref --gate` | unit twin 136 verified; crate twin 2; Dafny agent twin 168; Verus agent twin 29; gate twin 80 passed; all 0 holes |
| `vaudit --ref` | 0 findings on all four verifier twins |
| `vcheck --ref --brittleness` | unit twin (`--solvers`) stable, widest CV 15.2%; crate twin stable (CV 29.1% flagged); Dafny agent twin stable (CV 28.0% flagged); Verus agent twin stable (CV 26.5% flagged) |
| `vcheck --shipped Q18` | 5 files, 0 problems |
| `specfreeze --check Q18` | 0 findings |
| `pins.py --ci` / `--ref` / `--chapter Q18` | 25 pins 0 problems / 4 checks 0 / 10 pins 0 |
| `firsttry.sh Q18 --report` | unfilled 4 of 4 slots (the learner's), forms not met 0, banned 0 (`--strict` needs filled slots: not run) |
| `firsttry.sh Q18 --lint-hollow` | OK, 7 files |
| others | `reference_lint` 0 (141 twins); `check_course_map` OK (49 modules, 18 authoring) and `--only vocab` OK; `gen_units --check` 37 units match; `avoid.sh` 0 hits; `chapter_lint Q18` 0; leak verifier 18 modules OK; `update_rubric_pins --check` 111 current; `make -C paper paper` 36, `paper-solutions` 18; `test_course_map.py` 372 passed |

**The delivered proofs, pasted into the shipped files** (what a learner's first sweep shows):

- **H1d.** Pasted below the `decreases` line of the exercise file (the HOLE and hint comments
  kept): `scripts/vcheck` fails (the postcondition and `assertion might not hold` at the quoted
  assertion), and `--brittleness --solvers` fails on all six rows (twice, identical; widest
  spread on `CastOut` 0.16 M–5.45 M, CV 122.8%, 4.14.1). The same proof in a minimal module (the
  same module name, `DigitSum`, L1–L7, no comments; `bis_v4.dfy`): 4.12.1 seeds 1, 3 verified,
  seed 2 inconclusive; 4.14.1 seeds 1–2 inconclusive, seed 3 verified. In the first probe module
  (`p1.dfy`): 4.12.1 seeds 1–3 verified, 4.14.1 seeds 1–2 inconclusive. In the twin: an error
  under 4.12.1 seed 2. The verdicts move with the text around the lemma (Boogie's labels carry
  source positions), so the learner-visible text states none of them: the item and the chapter
  ask the learner to fill the table from their own sweep. A learner who pastes it sees red on
  every row, not a solver-swap flip (open issue, §13).
- **H1v.** Pasted at 12 spaces in place of the hole: `scripts/vcheck` inconclusive (`while loop:
  Resource limit (rlimit) exceeded`), the sweep `seed 1: inconclusive · seed 2: verified · seed 3:
  verified — NOT stable` (CV 59.4%). The chapter's "whether it verifies depends on the seed"
  holds.

## 12. Deviations from the plan

1. **H1's items** are the casting-out pair (a remainder congruence, Dafny lemma and Verus exec
   loop); the plan's "a hard-tier BigNat lemma" and "a large `nonlinear_arith` step" (author notes
   §10) became, in Verus, a broadcast-based proof block: one-step `nonlinear_arith` proofs were
   never seed-dependent on the pins (§3).
2. **H1's line counts** are below the hard band (§3, §8); not admitted.
3. **H2d/H2v markers sit in the agent files** (the statements are written there and copied to
   `research/`), with no shipped hole; H2d's `uses:` is `witness` (QPLAN's `refines` is not used by
   the capstone's statements).
4. **Two contracts, one per agent file**: the Dafny file's header is the review, the Verus file's
   the co-developer, each allowing both files; the skill's "which run is this" question picks one.
5. **Gate v2's signatures** add the given types and `option_findings`'s `root` keyword; H4py
   reads the wrapper's gate document, H6py the brittleness document (§5).
6. **Lab 3's tasks**: four of the author notes' candidates replaced (§6); the tasks are crates
   under `bench/local/q/crate/<id>/tasks/`, sealed with age (§9).
7. **Tools touched**: `scripts/test_course_map.py` (the planned stand-in is now R16; Q18's two
   gate-file cases rewrite Q18's imports with its harness list; `tomllib` imported). No other
   script changed.
8. **Written pair**: B6, Lab 3's report, added (QPLAN §28.1 lists none, §28.7 has "report 40");
   B1–B5 keep QPLAN's order.
9. **No A3dv marker** (Lab 3's runs are `fvh` batches, not an item of a file).
10. **The CLI**: verified entry points only (ENTRY POINTS section); the binary target and its
    build route are not built (QPLAN §30 Q59; DECISION NEEDED).
11. **The specimens' companions** are `*.companion` files (never live project files).

## 13. Open issues

See §14 for the user's decisions. Others: the `statements` pin and the unseal (DV4, high: before
Lab 3); Qwen agent-mode batches (DV4/fvh lane, high: before Lab 3); step 4c (DV4, with the user);
the CLI's build route (tools owner, medium: before the ship step); H1d's delivered proof fails
every row when pasted into the shipped file (§11): the DV5c fix round retitled the item ("a
repair that must hold under a solver swap and a seed sweep") and says so in the docstring and
the chapter; a visible flip would need a re-plan of the S11 line (§14 item 1, amended); `calibrate.py` covers Q01–Q15
(calibration owner: add Q18's tutor holes and budget); the skill simulations of Q16–Q18 with
`/viva Q18`'s Opening and draw A (simulations owner); the Lab 3 smoke through `fvh run` was not
run (it composes harness-executed runs on a task file; a crate task is a directory, and the
tasks are sealed).

## 14. DECISION NEEDED (for the user) — decided 2026-10-12 (D7, D9, D16; §16)

1. **H1d/H1v below the hard band** (12 and 19 proof lines; band 30–80 / 45–120). Options: (a)
   admit at 25 and 15 as a declared short-format band exception (as D2 did for Q15's S11 pair);
   (b) keep them at 0 and re-plan the S11 line; (c) admit only H1d. Recommendation: (a).
   **Amended by the DV5c fix round (read before deciding):** H1d as built is a plain
   failing-proof repair under `form: stable`, not a solver-swap flip. Pasted into the shipped
   file, the quoted proof fails all six rows (the claims review's re-run, and this round's:
   the quoted proof and ten variants of it that name no library lemma, each written into the
   docstring and pasted below the `decreases` line, all `failed` on every row; archive
   `dv5c/fix/h1d/`). The docstring's title and the chapter (§0, §3) were corrected to say the
   delivered proof may fail in some rows or in all of them; the S11 lesson that one solver or
   seed finds a step another misses is shown by the chapter's pace sweep, bank K3 and H1v (a
   seed flip on the shipped crate), not by H1d. So option (a) admits H1d as a 25-minute repair
   of a failing proof to a stable one. H1d stays false/0 until the user decides.
2. **H2d/H2v have no shipped hole**, so the empty-body gate does not apply. Options: (a) admit
   them on the reference statements, the reference delivery and the satisfiability check
   (`specfreeze --against` 0 on both), as statement items; (b) keep 0 and count the 25 minutes in
   the capstone round's paper grading only; (c) add a shipped client per language and gate it.
   Recommendation: (a).
3. **The CLI's build route** (QPLAN §30 Q59). Options: (a) a `[[bin]]` target generated for Q18
   by `gen_units.py` and a `vcheck --build-bin` route through the pinned `verus --compile`; (b) the
   CLI as a `#[cfg(test)]` driver run by `vcheck --test` only (no binary); (c) defer the binary to
   the challenge phase. Recommendation: (a).

## 15. Draft DELTAS entry (for the records lane to number)

**Δ2xx — DV5c Q18 lane: Q18 armed (Practice III-C + Lab 3 material + capstone).** Q18 is
`authoring` (QPLAN §28.8's files). Built: the unit and crate (H1d `CastOut`, H1v `cast_out`, the
brittleness pair over casting out (BASE − 1)s; the crate's empty capstone sections), the two
agent files with their CONTRACT headers (A1dv the review, Dafny file; A2dv the co-developer,
Verus file; H2d/H2v markers there), `research/q18_statements.{dfy,rs}` and
`q18_retrospective.md`, gate v2 (`harness/q/fvh_q/gate/gate_v2.py`, H3py–H7py, 80 frozen tests
over recorded fixtures K1–K3 and C1–C4), four build-tool specimens (P1d mute vcheck, P2d skip
gate, P3v divert gate, P4v bypass vcheck), the chapter (10 pins), the written pair B1–B6 (B6
Lab 3's report, added), solutions, rubric, bank (K1–K8, PP1–PP2, the hard tier's four viva
draws), instructor fixtures, leak patterns (8), Lab 3's twelve crate tasks sealed with age
(`bench/local/q/crate/`), with the pre-registration template and budget arithmetic. The capstone's
reference statements and delivery (both languages, `--test` 7/7 on the same rows, stable) live
in the agent twins. **Δ205 resolved**: Lab 3's `max_big` (= Q15.H5v) replaced, with `min_big`,
`double` and parity (properties of multiplication or division by a word). **Admitted**: H3py
15, H4py 10, H5py 20, H6py 15, H7py 10 (Q53's blocker built, Δ200); H1d, H1v, H2d, H2v 0
pending the user (below the hard band; statement items with no shipped hole). **Tools**:
`scripts/test_course_map.py`'s planned stand-in moved from Q18 to R16. **Open**: the statements
pin and unseal (Q64), Qwen agent-mode batches, step 4c, the CLI's build route (Q59),
`calibrate.py` coverage of Q16–Q18. Notes: `Solutions/plans/Q18-code-notes.md`.

## 16. DV5d: the user's decisions D7, D9, D10, D16, D17 and D18 (2026-10-12)

Applied by DV5d's decisions lane: one solver job at a time, each under the wrappers' caps
inside `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0` (the lane's share;
`/tmp/dvl0-dv5d-decisions/run.sh` refuses below 31 GB available; `free -g` showed 97–98 GB
available). Captures: `~/.cache/dafny-verus-learn-0/author-probes/dv5d/decisions/`. The lane's
notes, with the DELTAS-ready text: `Solutions/plans/DV5d-decisions-notes.md`.

- **D7: H1d 25 and H1v 15, admitted under the short-format band exception** (§14 item 1, option
  (a)): each entry carries `exception = "short-format band: the S11 pair line is short by
  design (12 / 19 proof lines, below 30 / 45) …; the user's decision D7"`. H1d is described as a
  repair that must hold under a solver swap and a seed sweep (the docstring's title since the
  DV5c fix round; now also the chapter's §3 H1d paragraph, QPLAN §28's header, §28.2's H1d and
  H1v rows and §28.7's H1 line, and design §7.5's Q18 row). QPLAN §28.8's registry block is the
  plan's snapshot and is left as planned (the registry and DELTAS supersede it). The four
  results stand as §8 and §11 recorded them; re-gated on this tree: `firsttry.sh Q18
  --empty-body` H1d ✓ (empty body fails in every run, `lever-needed` at line 97; the twin
  meets `stable`; the cfree answer fails `stable`, an error at line 70 under 4.12.1 seed 2),
  H1v ✓ (empty body fails, twin `stable`, cfree fails verification).
- **D9: H2d 12 and H2v 13, admitted as statement items** (§14 item 2, option (a)), each with
  `exception = "statement-item: …"`. The split is the plan's: with it, the hard tier's admitted
  hole minutes are Dafny 187 and Verus 163, QPLAN's own per-language totals (Δ216's Dafny 115 +
  Q17.H3d 35 + H1d 25 + H2d 12; Verus 135 + H1v 15 + H2v 13). **The admission route** (a tool,
  `scripts/firsttry.py`'s `statement_route`, run by `firsttry.sh <ID> --empty-body` after the
  hole gates for every admitted `statement-item` that holds no hole):
  1. the item's file's CONTRACT names exactly one `scripts/specfreeze --against <statements>
     <the file>` acceptance line (`statements_path`): `research/q18_statements.dfy` /
     `.rs`;
  2. the **reference statements** are that path's twin, new in this round:
     `Solutions/research/q18_statements.dfy` and `.rs` (the archive's `capstone/stmts.dfy`
     and `stmts.rs`, §4, under a three-line Reference Solution header: the agent files with
     the reference statements, witnesses and test rows, every statement a stub); they must add
     at least one statement to the file as shipped (`new_statements`: 17 Dafny, 14 Verus);
  3. the **reference delivery** (the agent file's twin) passes the reference gate with zero
     holes (`delivery_gate`, as `vcheck --ref --gate`): Dafny 168 verified, Verus 29;
  4. `specfreeze --against` the reference statements reports 0 findings on the delivery, the
     lever freeze included (`specfreeze.against_findings` + `dvl.levers.off_lever_findings`).
  Result on this tree: `Q18 statement items: 2/2 pass the statement route` (exit 0, after
  `Q18 empty-body: 7/7 hole(s) pass the gate`). `--eb-modes` runs the route only when it names
  `STMT`. A statement item that holds a hole (Q17.H3d, a prose item) keeps its hole's gates.
  `scripts/check_course_map.py` accepts the `statement-item` kind only on an admitted H item
  whose block is a prose item or sits in an agentic file (Q18.H2d/H2v are in the agent files).
  Static tests: `tests/wrappers/test_capstone_routes_static.py` `StatementRoute` (7 cases:
  the contract line, the selection, a frozen delivery passes, a changed statement fails
  `freeze-changed`, a failing or holed delivery fails, statements that add nothing fail,
  missing pieces are named).
- **D10: Lab 3's Claude arms run harness-executed; step 4c waits until R16 needs agent mode.**
  B2's template (`paper/Q18_answers.tex`): the arms field says both Claude arms are
  harness-executed (the harness executes every proposed action; no Lab 3 run puts Claude Code
  in a container) and asks what an arm-G `Verify` runs, when a `Stop` is refused and when a
  run ends; the disclosure field says every Claude run acted through `fvh`'s action schema.
  The solutions' B2 gains an *Arms and routes* item; rubric DI.a asks for it (a plan that puts
  a Claude arm in agent mode scores ≤2). The chapter's §0 *What is pending* drops the Claude
  agent-mode item and the CLI item (one item left: Qwen's agent-mode batches, D8's lane) and
  §5 says both Claude arms run harness-executed. The two calibration fixtures' B2 arms lines
  say the same (both still compile as drop-ins; their EXPECTED lines are unchanged).
- **D16: the capstone CLI's build route** (§14 item 3, option (a); QPLAN §30 Q59).
  `scripts/gen_units.py` emits one `[[bin]]` (`bignat`, `src/main.rs`) for the capstone crate
  (`CRATE_BINS`; the generated `verus/q/q18_practice_iiic/Cargo.toml` changed, `--check`
  clean) and reports a missing root. The learner file `verus/q/q18_practice_iiic/src/main.rs`
  ships as a stub (its header: the ship step, trusted code outside `verus!`, the route; it
  keeps `use vstd::prelude::*;`, which Verus needs in a crate root: without it the bin's
  compile failed with "The verus_builtin crate was not imported"); it prints a usage line and
  exits 2. It holds no item and no hole, is declared in `[module.imports]` (`arithmetic`) and
  `check_course_map.py` accepts a crate's binary root there (`crate_bin_roots`). **The route**:
  `scripts/vcheck --bin <crate> [-- <args>]` → `dvl.verus.run_bin`: the layer chain verified
  and exported, the library verified (normal mode, as `--test`) and compiled to an rlib, the
  `[[bin]]` root compiled by `verus --crate-type=bin --compile` against it, the binary run once
  with the arguments, all under the cap; refused for a non-crate, zero or several bins, a
  missing root, a root that is a library module, reference material, and with any other mode.
  Probes: the shipped crate prints `built — 2 verified; ran `bignat mul 6 7`: exit 2` and the
  usage line (vcheck exit 1; now the chapter's pinned fence `bin-shipped`); a scratch copy of
  the crate with two invented base-API entry points (`probe_add`, `probe_cmp`) and a `main.rs`
  over them built through the whole L1–L7 chain and printed `None` for `add 2^64−1 1` and `-1`
  for `cmp 6 7` (`cliprobe-*.txt`). Tests: `tests/wrappers/test_capstone_routes_tool.py` (an
  invented crate `tcli` over the chain fixture's `tla`, `tests/wrappers/fixtures/verus/cli/`:
  `tally sum 2 40` prints 42; a non-zero exit; a crate with no binary refused) and the static
  `BinTarget` cases. Not built: a reference CLI (the twin's capstone sections are empty, as the
  learner's: the ship step has no reference) and a `[[bin]]` in the reference crate's
  `Cargo.toml` (it mirrors the library; `twin_context` uses the learner manifest).
- **D17: arm G as built** (Δ215): every `Verify` runs gate v2's `gate_crate` on the work copy
  (each instrument in a verification container), a `Stop` is refused until the gate has passed
  the current work copy, the run ends at the first pass (`gate-pass`) or its budget; the outcome
  is the plain lab gate's verdict in both arms. The chapter's §5 and the solutions say so, the
  rubric gains CA.d (a plan that counts arm G's own pass or an agent's claim as the outcome
  scores ≤2) and runs-debrief D14.
- **D18: simulation case g** grades Q18's flawed fixture as a drop-in with the plain
  `/grade-paper Q18` (tests/instructor/simulations/README.md says so; `calibrate.py`'s
  `Q18-flawed` case already does).
- Runs on this tree: `chapter_lint Q18` 0 problems (11 pinned fences); `pins.py --update
  --chapter Q18 --entry bin-shipped`, then `pins.py --ci --module Q18` 26 pins, 0 problems;
  `update_rubric_pins.sh` (the solutions pin re-written) then `--check` 111 current; `vcheck
  --shipped Q18` 0 problems; `specfreeze --check Q18` 0; `firsttry.sh Q18 --lint-hollow` OK;
  `reference_lint --module Q18` 0; `make -C paper paper` (36) and `paper-solutions` (18); the
  leak verifier OK (18 modules, 1,608 public files).

## 17. DV5e: the user's decisions D23 and D24 (2026-10-13)

Applied by DV5e's decisions lane (16 GB scope, one solver job at a time; captures under
`~/.cache/dafny-verus-learn-0/author-probes/dv5e/decisions/`; detail and DELTAS-ready text in
`Solutions/plans/DV5e-decisions-notes.md`).

- **D23: a declared later-tier overlap; H1v does not change** (DV5d's small-fixes notes §4,
  option (a)). H1v's shipped `cast_out` (`verus/q/q18_practice_iiic/src/lib.rs`) is a complete
  top-down loop whose shipped invariant, and the delivered proof block the item hands the
  learner, state the domain of the invariant Q16.H2v asks the learner to find (DV5c's
  tier-disjointness sweep, the gaps notes §4: a structural overlap, no answer line). It is
  declared, not removed: Q18 follows Q16 in the track, and the learner norms keep later
  modules' files closed until a module's predictions are committed (`README.md`'s *Predictions
  first*, repeated in this file's header). The record is here and beside the leak README's
  tier exemption (`tests/instructor/leak_patterns/README.md`, rule 2, the *Declared later-tier
  overlap* bullet). No pattern matches it, so the leak verifier has nothing to list: it ran OK
  (18 modules, 1,618 public files). Nothing in H1v, its count (19), its admission (15, D7) or
  its pins changed.
- **D24 and Lab 3:** the lab gate (`vcheck --gate --lab-task`) now also applies vaudit's
  assumption rules to a delivery. On a scratch root with the twelve tasks staged from DV5c's
  plaintext (`dv5c/q18/crate-src/`): the eight possible tasks' reference deliveries pass the
  new lab gate (verified, 0 findings; 11.5–13.5 s each against 4.6 s before: the audit's
  `--no-cheating` runs over the crate and its L1–L7 dependencies), the four impossible tasks
  delivered as shipped fail (1 or 2 holes, as before); c01's reference passes it in a Verus
  verification container too (`ContainerRunner`, `--mem-gb 16`). The impossible tasks' trust
  escapes (`external_body` stubs) were already counted by the gate, so D24 changes no Lab 3
  verdict; it closes the shipped-assumption route for Dafny task forms (the vericoding finding,
  Δ221).
