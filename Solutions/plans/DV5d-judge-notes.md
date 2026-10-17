# DV5d: the grader's judging step (author-only notes)

The judging lane of DV5d (2026-10-12): `truthcheck`'s `judge` mode (DV4-PLAN §5.9, QPLAN §30
Q49), its host half and report hook, the three sealed archives re-sealed with the frozen
reference oracles, the grader image rebuilt by digest, and the sealed prose references of Q13,
Q15 and Q17 judged in the container against themselves and against recorded wrong statements.
Memory: 16 GB share, one container at a time (a Dafny verification container at its own 11.5 GB
bound, a Verus one capped with `--mem-gb 16`), `free -g` checked before each (`runall.sh`'s
wait), host solver jobs only through the wrappers inside a 16 GB `systemd-run` scope. No model
was called. Archive: `~/.cache/dafny-verus-learn-0/author-probes/dv5d/judge/` (`hidden-src/`
the re-sealed plaintext, `build/` the two image builds, `container/` every judging run's host
output, `container/pass1-ea42d4a1/` the first pass on the intermediate image, `scratch/` the
candidate files, specs, expected verdicts and the lane's driver scripts, `q15/` the
empty-body re-run). Like Δ195-Δ217 this file is reference-class: it names the recorded wrong
statements, which no learner-visible file may.

## 1. What was built

- **`truthcheck judge <LAB>`** (`sandbox/image/truthcheck.py`, in the image at
  `/opt/dvl/bin/truthcheck`). It unseals the bound archive in memory (as `manifest` does), reads
  `/work/judge/candidates.json` (staged inline by the host), loads the archive's
  `labs/<LAB>/judge/oracles.py` (the frozen reference oracles, a byte copy of
  `Solutions/harness/q/fvh_q/oracles.py`, sha256 `e168aaed…7665d`) as a module with a stand-in
  `fvh.tools`, and judges each candidate:
  - a host refusal code (`parse`, `freeze`, `task-form`) or a signature other than the
    reference's: `mismatch`; the candidate's definitions alone must verify (a base lemma;
    else `context`);
  - **a Lab 2 card**: the oracles' own `implication`, `vacuity` and `classify` (QPLAN §25.5's
    hidden verdict, the one the learner's oracles are compared with), each lemma written over
    the staged task form and gated there (`vcheck --gate --json <form>`), the form restored
    after each run;
  - **a prose item** (QPLAN §19.0's hidden equivalence check): a two-way refinement by four
    lemmas over the item's parameters and results (`req_from_ref`: the reference's requires
    give the candidate's; `ens_to_ref`: with the candidate's requires and ensures they give the
    reference's ensures; `req_to_ref`; `ens_from_ref`), plus the oracles' vacuity lemma:
    faithful both ways, strong (claims or demands more), weak (says less), vacuous, undecided;
    each lemma a probe of the lab's module (`vcheck --gate --json --module <LAB> <probe>`);
  - the reference's own definitions (Q15.H3v's spec fn) enter renamed `dvl_ref_<name>`, unless
    the candidate's file states the same definition word for word (comments and layout aside):
    then the candidate's is used as it stands.
  Output: one JSON object, per candidate only its id, item or card, a verdict word, outcome
  words and a fixed reason (`_clean` whitelists every field); nothing on stderr; every
  exception a fixed message (`entry` turns an escaping one into a fixed refusal, exit 3).
  Exit 0 every candidate judged, 1 one could not be, 2 usage, 3 refused.
- **Why the prose items use their own lemmas, not the oracles' implication.** H11's formula
  reads a specification as its requires and ensures together inside the reference's requires
  (`spec_implies_ref`: ref.req ∧ spec.req ∧ spec.ens ⇒ ref.ens; `ref_implies_spec`: ref.req ∧
  ref.ens ⇒ spec.req ∧ spec.ens). A statement that drops a hypothesis is then faithful (nothing
  outside ref.req is judged: the Q17 plausible-but-wrong statement would pass), and one that
  adds a hypothesis is "strong" (its requires sits in `ref_implies_spec`'s conclusion), the
  opposite of H11's own gloss ("strong: correct behaviours fail it"). For Lab 2's cards the
  oracles' verdict is kept as built (it is what the learner's oracles are measured against;
  most cards ship no requires); the gloss disagreement is §6's decision item 2. The prose
  check's four lemmas and its truth table are not H11's or H12's answers (other lemmas, other
  table) and sit in the learner-visible `truthcheck.py`; H11's and H12's reference answers
  stay sealed (`judge/oracles.py` exists only in the archives and the reference tree).
- **Host half** `scripts/dvl/judge.py` (new): candidate extraction through the course parsers
  (`dvl.dafny.parse_source`, `dvl.verus_spec.parse`): the declaration's parameters, results,
  requires and ensures as written (Verus: one entry per clause keyword, the whole list, so a
  `forall|i: int, j: int|` binder never splits), and its file's definitions (methods, lemmas,
  constructors, iterators, exec/proof/axiom fns, `assume_specification`, broadcast items and
  `mod x;` removed; Verus doc comments made plain) split at the declaration into header and
  footer; `prose_item` (the `// item:`/`// prose:` markers of the module's exercise files),
  `lab_cards` (the strata), `freeze_ok` (a prose candidate's file against its module's freeze
  pin, `specfreeze --check`'s rule for that file, open specs included), `lab_ok` (a card
  candidate's context keeps every statement of its task form's context, and the lab gate's
  lever check finds nothing: the lab gate's statement freeze cannot be used, since writing the
  task's spec changes its statement: `specfreeze --lab` reports `freeze-changed` on every
  reference program), `load_spec` (TOML `[[candidate]]` or JSON `{"candidates": …}`),
  `candidates` (a malformed spec is refused; a bad delivery is a stub row, never a refused
  batch), `build_judge` (the verify manifest: the module's given chain, project files, tools
  and pins read-only, each card's task form editable inline, `judge/candidates.json` inline
  with role `task`, the `[truth]` table, the one command `truthcheck judge <LAB>`, one language
  per run).
- **`scripts/mksandbox-run --truth ARCHIVE --truth-check judge --judge SPEC [--mem-gb N]`**;
  `dvl.sandbox.TRUTH_MODES` gains `judge` (`build_truth` refuses it: `dvl.judge` builds that
  manifest).
- **`python -m fvh report <ID> --judge RUN|all --truth ARCHIVE [--mem-gb N]`** (new frozen
  module `fvh.judging`, `__main__` and `__init__` edits): every lab run whose apparatus names a
  lab card's task form, its returned copy (else its staged input), one judging run per
  language; prints one verdict line per run, writes nothing into a run directory. The archive
  must be named on the line and equal the pin, so guard rule 1c refuses the line in a study
  session, as it refuses `mksandbox-run --truth` (the learner runs the grader themselves).
- **The archives re-sealed** (`sandbox/seal_hidden.py`, the pinned age, the key on this
  machine): each gains `judge/oracles.py`; Q15's also a `DVLCANARY` (Q13's and Q17's had one);
  `SEALING.md` says why. Q13 4 files (sha256 `5c115021…9253`), Q15 52 (`062885c4…bde2`), Q17 4
  (`255683f6…3ecb`); `sandbox/truth.toml` re-pinned by the tool (and its header comment).
- **Images rebuilt by digest** (only `truthcheck.py` changed): `dvl-toolchain@sha256:ee8b0f7c…03de`,
  `dvl-agent@sha256:bb5b5439…c79e`; `sandbox/images.lock` sha256 `9d491d55…6976` pinned in
  `sandbox/apparatus.toml`; `build-images.sh --check` OK; `fvh apparatus --check` matches;
  VERSIONS.md §1.4 two rows; `sandbox/README.md` rows.
- **Tests**: `tests/sandbox/test_truth_judge.py` (17: extraction in both languages, stubs and
  refusals, the manifest, the command-line pairing, truthcheck's judge in-process over a
  stand-in archive whose reference carries a canary token, with the canary absent from stdout
  and stderr when the run judges, when a candidate's oracle call raises with the canary in its
  message, when the reference is malformed, when the sealed module raises or does not parse,
  and when `main` raises; the definitions rule; the guard refusing three judge command lines
  in a study session); `harness/tests/core/test_judging.py` (4).

## 2. The judging runs (the final image; host output in `container/`)

Specs: the reference twins copied to scratch (the twin's declaration is the reference
statement) and variants of them, each edit inside the declaration's header only; the Lab 2
reference programs from the plaintext tree. `expected.json` records each expectation before
the run.

| run | candidates | result | wall |
|---|---|---|---|
| `manifest` Q13, Q15, Q17 | — | unsealed, manifest ok (4, 52, 4 files) | < 1 s each |
| `judge` Q17 (Dafny) | Q17.H3d: the reference; the recorded plausible-but-wrong statement (side conditions in the start state only: **strong**); the precondition dropped (strong); `fuel > 0` added (weak); total correctness (strong); `requires false` (vacuous) | 6 of 6 as expected | 50 s |
| `judge` Q13 (Verus, 16 GB) | Q13.H3v: the reference; the four recorded statements of the Q13 notes §5 (equal length: weak; `<=`: weak; `requires false`: vacuous; canonical first argument: weak); the agreement hypothesis dropped (strong); a stronger conclusion (strong) | 7 of 7 | 166 s |
| `judge` Q15 (Dafny) | H3d, H4d, H5d: each the reference, a weaker, a stronger and a vacuous statement | 12 of 12 | 395 s |
| `judge` Q15 (Verus, 16 GB) | H3v, H4v, H5v: each the reference, a weaker, a stronger and a vacuous statement; H3v also a disjunct added (weak) and an equal count defined from the front (undecided) | 13 of 14: H3v's `n <= a@.len()` is **undecided**, expected weak (its weakness needs an induction over the count, which no empty lemma does; unfaithful either way) | 270 s |
| `judge` Q15 cards (Dafny) | the ten reference programs; d01: a weaker, a stronger, a vacuous delivery, a renamed parameter, a changed definition | 15 of 15 (10 faithful; weak, strong, vacuous; two `mismatch`) | 37 s |
| `judge` Q15 cards (Verus, 16 GB) | the ten reference programs; v07: weaker, stronger, vacuous | 13 of 13 | 57 s |

The first pass on the intermediate image (`dvl-toolchain@sha256:ea42d4a1…f55f`) agreed
everywhere except Q15.H3v's reference, which was then undecided: the reference's spec fn and
the twin's own (the learner's, word for word the same) were compared as two functions, which
needs an induction; the definitions rule above fixed it, and the image was rebuilt.

**Verdict-only output, checked:** the 36 sealed clauses and definitions of at least 12
characters and the archives' canary token, searched (also with whitespace removed) in all 37
host output files of the lane's container runs: 0 hits. No run directory is left under
`$XDG_RUNTIME_DIR/dvl-runs/` and no `dvl.run` container.

## 3. The prose items' admissions (Δ173's four results; QPLAN §19.0's instrument)

- **Q13.H3v** (admitted 25 since Δ195): the hidden equivalence check now holds on the built
  files (§2). No minute moves. QPLAN §23.5's and the Q13 code notes' "still waits on the
  grader's judging step" are superseded.
- **Q17.H3d** (admitted 35 by DV5d's decisions lane under D6's `statement-item` exception):
  the check holds (§2), including the recorded plausible-but-wrong statement, which the
  oracles' own two-way implication would have called faithful (§1). No minute moves.
- **Q15.H4v**: in the intermediate Verus band (34 proof lines by `pcount.py`; statement 8),
  client gate and prose proof gate passing (`firsttry Q15 --empty-body`, re-run on this tree:
  see `q15/emptybody.log` and §5), stable (Δ197), pinned APIs only, and now its hidden check
  (§2): **admitted at 18**, QPLAN §25.7's planned minutes (6 × 18 for the six prose specs).
- **Q15.H3d, H4d, H5d, H3v, H5v**: their hidden checks hold (§2), but they stay below the
  intermediate band (Dafny 0 proof lines each, the learner writes a 1-3 line specification and
  a one-line witness; H3v 7 proof lines with a 4-line spec fn; H5v 0), so Δ173 admits none
  without a band exception: **a decision for the user** (§6 item 1). Until then 0.

## 4. DELTAS-ready text (for the integration lane to number)

**Δ2xx · The grader's judging step as built: `truthcheck judge`, its host half and `fvh report
--judge`; the archives re-sealed with the frozen oracles; the image rebuilt; the prose
references judged; Q15.H4v admitted — adopted (DV5d, 2026-10-12)**
- **Status:** closes Δ208's and Δ217's open item (DV4: a `truthcheck` judging mode, the image
  rebuild, the prose references judged in the container), Δ195's (Q13.H3v's hidden check),
  Δ197's and Δ199's pending hidden check of Q15's prose items, and QPLAN §30 Q49's last part.
  Like Δ195-Δ217 it names no answer, no reference statement and no wrong statement; the detail
  is in `Solutions/plans/DV5d-judge-notes.md`.
- **Change:**
  - **`truthcheck judge <LAB>`** (`sandbox/image/truthcheck.py`): judges every candidate the host
    stages (`judge/candidates.json`) against its sealed reference, with the frozen reference
    oracles each archive now carries (`judge/oracles.py`, never in an image or a learner-visible
    file). A Lab 2 card gets the oracles' own implication, vacuity and classification (QPLAN
    §25.5's hidden verdict). A prose item gets a two-way refinement check (four lemmas: each
    side's requires gives the other's, and each side's ensures, under them, gives the other's;
    plus the vacuity lemma): faithful, strong, weak, vacuous or undecided. `mismatch` for a
    changed signature or a delivery the host refused (a changed frozen statement, a changed
    task-form definition or lever, an unreadable declaration); `context` when the candidate's
    own definitions do not verify. A reference definition the candidate states word for word is
    the candidate's; another is renamed. Output: verdict and outcome words per candidate,
    fixed reasons, nothing on stderr, every exception a fixed message.
  - **Host half and commands:** `scripts/dvl/judge.py` (extraction through the course parsers,
    the freeze and task-form checks, the manifest); `scripts/mksandbox-run --truth ARCHIVE
    --truth-check judge --judge SPEC`; `dvl.sandbox.TRUTH_MODES` gains `judge`; `python -m fvh
    report <ID> --judge RUN|all --truth ARCHIVE` (new frozen module `fvh.judging`: a lab's runs'
    deliveries, one container per language, verdicts printed, nothing written into a run
    directory; the archive is named on the line so that guard rule 1c refuses it in a study
    session). Stable-interface additions (DV4-PLAN §13): the `judge` mode and `fvh.judging`.
  - **Re-sealed:** `Hidden/labs/Q13/`, `Q15/`, `Q17/` (each with `judge/oracles.py`; Q15 also with
    a `DVLCANARY`), `sandbox/truth.toml` re-pinned. **Images rebuilt:**
    `dvl-toolchain@sha256:ee8b0f7c…03de`, `dvl-agent@sha256:bb5b5439…c79e`; `images_lock_sha256`
    re-pinned in `sandbox/apparatus.toml`; `VERSIONS.md` §1.4.
  - **Admissions:** Q15.H4v admitted at 18 (QPLAN §25.7's planned minutes; its four results and
    the hidden check). Q13.H3v (25) and Q17.H3d (35, D6) keep their minutes; their hidden checks
    now hold. Q15.H3d, H4d, H5d, H3v and H5v stay at 0 (below the band; the user's decision).
- **Why:** the lane's runs (16 GB, one container at a time; archive `dv5d/judge/`): manifest
  round trips 3/3; on the final image every sealed prose reference judged faithful against
  itself (Q13.H3v, Q15.H3d-H5v, Q17.H3d) and every recorded or planted wrong statement
  classified as expected (Q13 6, Q17 5, Q15 18 of 19: one weak statement whose weakness needs an
  induction is undecided, unfaithful either way); the twenty Lab 2 reference programs
  faithful, eight planted wrong deliveries weak, strong, vacuous or mismatch as expected; the
  sealed clauses and the canary token absent from every host output (0 of 37 files);
  `tests/sandbox/test_truth_judge.py` 17 OK (the canary never reaches stdout or stderr on any
  path; the guard refuses the judging lines in a study session); `harness/tests/core` with
  `test_judging.py`; `tests/sandbox` and the static checks (§5).
- **Touches:** Δ173, Δ195, Δ197, Δ199, Δ208, Δ215, Δ217; QPLAN §19.0, §23.5, §25.2, §25.5-§25.7,
  §30 Q49; DV4-PLAN §5.9, §13; `CLAUDE.md`'s **Not built yet** line (drop "the grader
  container's judging step"); `MODULES.toml` (Q15.H4v); the files above.
- **Owner:** DV5d's judging lane.
- **Open** (owner, severity): the user (medium): the five below-band Q15 prose specs' minutes and
  the gloss of the oracles' strong/weak for requires changes (the round's report); the kits and
  records lane (medium): the learner-visible "the hidden check is recorded as pending" sentences
  (`docs/Q15_PracticeIIC.md` §0 and the Lab 2 section, the headers of `Q15_Lab2Specs.dfy` and
  `lab2_specs.rs`, rubric A7/C5 of Q13, the Q13 and Q17 chapters' grader sentences) and QPLAN
  §23.5, §25.2's row and §30 Q49; the author (low): a pre-registered Lab 2 run judged with `fvh
  report --judge` once the public pools exist.

## 5. Re-runs on this tree

- `firsttry.sh Q15 --empty-body` (16 GB scope): **18/18** hole(s) pass the gate (H4v: the
  client gate and the prose proof gate) (`q15/emptybody.log`); `vcheck --ref --brittleness
  Solutions/verus/q/q15_practice_iic`: seeds 1-3 verified, **stable** (widest spread CV 18.0%,
  advisory) (`q15/brittleness.log`).
- `check_course_map.py` OK and `--only vocab` OK; `scripts/test_course_map.py` 381 passed.
- `tests/sandbox/test_truth_judge.py` 17 OK; `tests/sandbox` (pytest) 157 passed;
  `harness/tests/core` 535 passed.
- `scripts/ci.sh --author --job harness`: PASS (63 s; `tests/core` 535, `tests/harness_adapter`
  50, `tests/sandbox` 157, `tests/bench` 11); `--job static`: PASS (406 s).
- `tests/acceptance/sandbox_doors.py access images controls canary return secret` on the
  final images: 39 passed, 0 failed (`doors/`). The parity section was not re-run: the images'
  inputs other than `truthcheck.py` are unchanged, and the judging runs themselves verified
  Dafny and Verus targets in the rebuilt verification container.
- The leak README's verifier: 18 modules, 1,611 public files, OK; `avoid.sh` OK; a line check of
  the oracles twin's answer lines (H9py-H12py, 50 lines beyond the learner file's) against the
  five new public files: 0 hits; `check_single_route.py` 0 outside the allowlist; `build-images.sh
  --check` OK; `fvh apparatus --check` matches.
- **The oracles' requires reading, run:** a d01 delivery whose spec adds `requires |s| >= 3`
  to the reference's ensures (a wrong implementation on short sequences passes it) is judged
  `strong` (`spec_implies_ref` proved, `ref_implies_spec` failed) (`container/judge-Q15d-quirk.out`).
  In the lane's first host dry run (the oracles' implication plus a domain lemma, before the
  refinement check replaced it; output superseded in the archive) the Q17 plausible-but-wrong
  statement had both oracle lemmas proved.

## 6. Decisions for the user — decided 2026-10-13 (D21, D22; applied by DV5e's decisions lane)

1. **The five below-band Q15 prose specifications** (H3d, H4d, H5d, H3v, H5v; QPLAN §25.7 plans
   18 minutes each, 90 in all). The `statement-item` kind did not cover them (D6 defines it as
   statements a contractor proves; these items name no contractor). **Decided (D21, option
   (a)):** a new exception kind, `"hidden-check spec: <why>"`, for a prose specification below
   its band whose grade is its hidden check in the grader container. `scripts/check_course_map.py`
   (`HIDDEN_CHECK_KIND`, `hidden_check_problem`, `HIDDEN_CHECKS_HELD`, `sealed_labs`) accepts it
   only on an admitted H prose item (`// prose: <name>`) of one of the module's exercise files
   that names no contractor (one that does is a statement item), whose hidden check is recorded
   as holding (this lane's §2 runs: the record cites Δ220) and whose module's sealed truth is
   pinned in `sandbox/truth.toml`; it refuses the kind on a plain block, a prose block naming a
   contractor, an agentic-file item, an item outside the exercise files, an unrecorded item and
   a module with no sealed truth (`scripts/test_course_map.py`). Each of the five is admitted at
   18 under it; Q15's Lab 2 prose line carries 108 of 108 (design §7.5, QPLAN §25.7).
2. **The oracles' strong/weak for requires changes** (Q15.H11py/H12py as frozen). **Decided
   (D22, option (a)):** the glosses say the built reading, text only, tests unchanged: the
   `Verdict` docstring and its STRONG comment, the `Implication` docstring and H11's docstring
   (learner file and twin) now say the two lemmas read a specification's requires and ensures
   together inside the reference's requires, so an added requires (one the reference's requires
   and ensures do not give) narrows the specification and counts as `STRONG`, and a dropped
   requires is not seen. The formula, the tests and the classification are unchanged. Q15's
   archive was re-sealed afterwards with the new twin (`6cb4f036…a259`, DV5e's Lab 2
   public-forms lane); Q13's and Q17's sealed `judge/oracles.py` (`e168aaed…7665d`) keep the
   old comment text and are otherwise the twin's code (§1's byte-copy rule: re-copy at their
   next re-seal).
