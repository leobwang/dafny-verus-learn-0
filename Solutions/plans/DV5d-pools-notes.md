# DV5d pools lane: the public pools, HumanEval-Verus's stripping step, the attestation scan and the cards' attestation

Author-only notes (reference class). The lane's brief: QPLAN §30 Q57 and Δ217's DV5 item
(the public pools' validation, the HumanEval-Verus stripping step, the attestation scan's
recalibration, the cards' attestation). Like Δ195–Δ217, nothing here names an answer: the
leak-scan and calibration results are given as counts and kinds, never as answer text.
Memory share 32 GB (one `systemd-run --user --scope -p MemoryMax=32G -p MemorySwapMax=0`
scope per validation run; each solver job under the wrapper's own cap, Dafny 8 GB, Verus
16 GB; workers × cap ≤ 32 GB). Scratch `/tmp/dvl0-dv5d-pools/` (removed at the end);
archive `~/.cache/dafny-verus-learn-0/author-probes/dv5d/pools/`.

## 1. What was built

| file | what |
|---|---|
| `scripts/dvl/benchstrip.py` (new) | the content transforms of get_bench's normalizer: `verus-drop-main`, `verus-strip-proofs` (HumanEval-Verus's stripping step), `dafny-axiom-assume-to-hole`; `proof_residue` (an independent token check of a stripped file) |
| `scripts/dvl/bench.py` | a layout row's `transform` (validated against the registry, applied at normalization, recorded in CHANGES with the number of files it changed); `--validate` rebuilt (§2); `--pin-pool` and `bench/public/POOLS.toml` (§4); `DVL_BENCH_TMP` for its temporary trees; log lines flushed |
| `scripts/get_bench.sh` | unchanged (a thin front end; its header lists the forms) |
| `bench/manifest.toml` | humaneval-verus: two layout rows (answers through `verus-drop-main`, tasks through `verus-strip-proofs`), notes, new digest; vericoding: `dafny-axiom-assume-to-hole` on the Dafny task forms, `verus-drop-main` on the Verus task forms and answers, notes, new digest; the header names `transform` |
| `bench/public/POOLS.toml` (new, committed: `bench/public/` is rule 2f and the file is not gitignored) | the pinned pools (§4) |
| `scripts/dvl/sandbox.py` | the attestation scan recalibrated (§5): `_course_code_files`, `visible_shingles`, `_twin_pairs` (the lab cards' references in `Solutions/bench/local/` are twins now), `answer_spans`, `author_scan` (whole spans, visible text excluded), `attest_data` (attest given bytes, with an optional `source`; `attest` calls it) |
| `sandbox/attested.toml` | 78 entries: Lab 1's 22 cards, Lab 2's 20, Lab 3's 36 sealed crate files; the header says how the scan works |
| `tests/bench/test_benchstrip.py` (new, 13 cases) | the stripper on invented Verus text, the residue check, the Dafny transform, and (skipped unless installed) the check that no installed HumanEval-Verus task keeps a proof body and that each task is its answer stripped |
| `tests/bench/test_get_bench.py` | 10 new cases: a layout transform applied and recorded, an unknown transform refused, `--validate` with fake vcheck and vaudit (the rule and the header), a killed job retried by the next run, SIGTERM stops and the same command resumes (the stopped job's process gone), another selection needs `--restart`, a seeded sample recorded and reproducible, workers must fit the share, the pool pinned and checked, the sample's allocation |
| `tests/sandbox/test_sandbox.py` | `AttestRecalibrated` (5 cases): a card that copies definitions is attested (and shares shingles with the twin under the old unit), a planted answer line is still caught, a shared fragment is no hit, a lab reference is a twin, `attest_data` records a sealed card |

## 2. `get_bench.sh --validate` as built

    get_bench.sh --validate SET [--only NAME...] [--sample N --seed S]
                 [--workers N --mem-gb SHARE] [--restart]

- **The pool rule.** A row per answer file. The answer passes the done check: `vcheck --gate
  --json` verified with 0 holes, and `vaudit --json` with no finding (Δ4: done = gate AND
  audit; the first `--validate` ran the gate only). Its task form, delivered unchanged, fails
  the lab gate: `vcheck --gate --json` on the task form is not verified-with-0-holes (an
  unchanged delivery has no lever finding, so this is the lab gate's verdict), at the verify
  stage (a task form that does not parse or resolve poses no task). Reasons for a non-pool
  row: `answer-not-verified`, `answer-holes`, `answer-audit:<kinds>`, `no-task-form`,
  `task-form-does-not-resolve`, `task-form-passes-the-gate`, `answer-equals-task-form` (a
  shared support file, or a task with nothing removed); `retry:<verdict>` for a job that is no
  verdict.
- **Never a verdict:** exit 137/143 (`killed(memory)`), 124 (`timeout`, the wall-clock net) and
  a job with no JSON document (`no-json`); such rows are re-run by the next invocation, also
  after a finished run (it continues from `validation.jsonl`). A tool's own `error` verdict
  is a result (DafnyBench's one file whose name holds a space).
- **Resume-safe.** Rows go to `SET/validation.partial.jsonl` (fsync per row) under a header
  that names the set digest, the tool pins' digest and the selection; the same command
  continues; a partial of another selection, digest or pins needs `--restart`. Each
  invocation appends a segment line (start, end, rows, workers, why it stopped); the final
  header's `wall_s` is the sum over segments.
- **Stoppable.** SIGINT or SIGTERM stops submitting, sends SIGTERM to the running tool
  processes (the wrapper's lifeline then kills their scopes), keeps the finished rows and
  exits 1 naming the resume command.
- **Memory.** `--workers` 1..4 (default 1: DV4-PLAN §7.2's one job at a time when run bare);
  `--mem-gb` the lane's share (default one job's cap); refused when workers × the language's
  cap exceeds the share; refused unless MemAvailable ≥ share + 15 GB at the start; before each
  job MemAvailable ≥ cap + 15 GB, else it waits (up to 30 min, then stops with the rows kept).
  The children's `DVL_SCRATCH` is the run's scratch (their slots and raw directories stay in
  it; each raw directory is removed once read).
- **Sampling** (when a pool would take more than 6 h; not needed this round): a seeded
  stratified sample, strata by `language/source` from the subset index (vericoding) or by
  language; proportional allocation by largest remainder, at least one per stratum when n
  allows; `random.Random(f"{seed}:{stratum}")` over the stratum's sorted paths; the header
  records n, the seed, the rule, the strata's sizes and draws, and the drawn list's sha256.
- **The pre-registration of this round** (written before any full run;
  archive `logs/PREREG.txt`): each pool whole unless its projection from the first 200 rows
  exceeded 6 h, then `--sample 400 --seed dv5d-2026-10-12-<SET>`; Dafny-only sets 4 workers,
  sets with Verus 2.

## 3. Normalization: the stripping step and two more transforms

- **HumanEval-Verus** (`verus-strip-proofs`; QPLAN §22.6's "proofs removed, specification and
  code kept"). Removed: proof fns (a proof fn that a kept line still names, for example through
  a `use`, keeps its signature and an empty body), `broadcast group` items, a module-level
  `broadcast use` naming a removed item, and in exec code the statements `assert(..)` (also
  `assert .. by`, `assert forall .. by`), `proof { .. }`, the proof macros (`calc!`,
  `assert_seqs_equal!`, `assert_by_contradiction!` and the like), `let ghost`/`let tracked`,
  `reveal`/`reveal_with_fuel`/`hide`, `broadcast use`, and a loop's `invariant`,
  `invariant_except_break`, `invariant_ensures` and `ensures`; comment and attribute lines
  attached above a removed item or statement go with it. Kept: spec fns, every fn's signature
  (requires, ensures, recommends, decreases), the exec code, Rust's runtime `assert!` family,
  every other comment (the prompt, the canonical Python solution and the tests are comments
  outside `verus!`), and **a loop's `decreases`**: Verus refuses a loop without one before it
  verifies anything ("loop must have a decreases clause", a VIR error at the resolve stage),
  so the first build, which removed it, left 28 of the first 89 rows `task-form-does-not-resolve`
  (stopped, fixed, re-pinned). The answers lose only the top-level `fn main` outside `verus!`
  (`verus-drop-main`: the course gate's V9 lint refused all 167 answers as installed, the
  author notes §4.2's finding), whatever its body (150 are `fn main() {}`; 17 are `pub` or hold runtime tests or comments).
  Over the 167 files the step removes 206 assert statements, 120 loop clauses, 121 proof fns,
  68 proof blocks, 32 ghost lets and 9 reveals; `proof_residue` finds nothing in any task,
  and the step is idempotent.
- **vericoding, Dafny task forms** (`dafny-axiom-assume-to-hole`, 2,251 files): `assume {:axiom}
  false;` becomes `assume false;`. The finding behind it: `vcheck --gate` passes a Dafny file
  whose only gap is `assume {:axiom} false;` (verified, 0 holes; only `vaudit` reports it), and
  the lab gate's lever check allows a lever the task form ships, so `vcheck --gate --lab-task T
  T` on an unchanged vericoding task form exits 0 (probed: archive `probes/lt2/`; a delivery that adds the same line is refused `lab-lever-added`, `probes/lt/`). After the
  transform the task forms carry a hole the gate counts. Task forms that still ship an
  `{:axiom}` declaration pass the gate as shipped and leave the pool by the rule
  (`task-form-passes-the-gate`).
- **vericoding, Verus files** (`verus-drop-main`): 2,272 task forms and 832 answers lose their
  `fn main` outside `verus!`.
- Digests re-pinned (`get_bench.sh --pin`, fetched from the pinned commits): humaneval-verus
  `02c465b1…` → `89d53507eab46676c83e960dc3745bda555c4469953476bd7ea6fa7c5e9f9866`; vericoding
  `a88622df…` → `0eb0ae378c7594cefb549373bf70364f993fd5fe72e8384058e114e81d7c2101`. The
  canary tokens derive from name and commit, so `sandbox/canaries.sha256` is unchanged.

## 4. The pools (validation results)

Each set validated whole (no projection came near 6 h, so no sample was drawn), under the
rule of §2 (schema 3), one `systemd-run` scope of 32 GB, `free -g` 96–97 GB available at
each start; `retry_left` 0 everywhere (no job was killed by memory or by the net).

| set | rows | pool | workers | wall | job time | the non-pool rows |
|---|---|---|---|---|---|---|
| DafnyBench | 785 | **303** | 4 | 363 s | 1,444 s | answer not verified 279 (170 fail only through the gate's warnings rule, 33 inconclusive at the pinned resource limit, 75 failed, 1 a tool error on a file name with a space), answer equals task form 102, task form passes the gate as shipped 54, answer audit 23 (axioms, bodyless declarations, `decreases *`, `{:verify false}`, …), task form does not parse 18, answer changes a statement 6, no task form 1 |
| HumanEval-Verus | 167 | **83** | 2 | 188 s | 376 s | answer equals task form 80 (78 upstream files are TODO stubs; 2 need no proof), answer not verified 2 (both `rlimit-inflation`), answer adds a lever 2 (`#[verifier::spinoff_prover]` on a lemma the task form no longer has) |
| vericoding | 2,683 | **2,264** | 2 | 3,902 s | 7,780 s | answer not verified 211 (164 failed, 47 inconclusive), task form does not resolve 105 (its specification names a helper only the answer defines), answer audit 63 (35 hold `assume {:axiom}`: the gate alone would have admitted them), task form passes the gate as shipped 21, answer changes or drops a statement 18, answer adds a lever 1 |
| MINIF2F-DAFNY | 12 | **0** | 4 | 5 s | 17 s | answer not verified 10 (6 through the warnings rule, 4 inconclusive), answer equals task form 2 (`definitions.dfy`, `library.dfy`); the 10 example solutions have no task forms in the set either: not a pool (QPLAN §22.6) |
| LemmaScript | — | — | — | — | — | not validated: no tasks or answers installed; not a pool (QPLAN §30 Q57) |

vericoding's pool by stratum (language/source): Dafny apps 420/563, dafnybench 287/330,
**humaneval 143/151** (Lab 2's public Dafny source), numpy_simple 37/44, numpy_triple 312/335,
verified_cogen 163/165, verina 107/137; Verus apps 196/208, dafnybench 94/153, humaneval 40/42,
numpy_simple 21/22, numpy_triple 281/324, verified_cogen 91/134, verina 72/75.

Against the labs' needs: Lab 1's public strata draw 20 DafnyBench and 20 HumanEval-Verus
tasks after a pilot on twice that (40 each): pools 303 and 83. Lab 2 draws 5 HumanEval-Verus
and 5 vericoding humaneval Dafny tasks: pools 83 and 143, in Lab 1's task form; Lab 2's own
form is not built (§7). Two runs of vericoding (the first under the schema-2 rule, archived
`validation/schema2/`) differ in one answer's verdict (inconclusive, then verified: an answer
at the resource limit's edge). The first rule (no static half) admitted 2,280 vericoding and
307 DafnyBench tasks where the final rule admits 2,264 and 303; HumanEval-Verus's first-rule
run was stopped when the static half was added (the half refuses 2 of its answers).

`bench/public/POOLS.toml` records each pool (the set digest and tool pins it was validated
on, the selection, the counts by reason and stratum, the wall time, the members' paths and
the sha256 of their sorted list); `get_bench.sh --check` compares an installed `validation.jsonl` with it
and flags a pin made on another set digest or other tool pins. The `validation.jsonl` files
are archived under `validation/`.

## 5. The attestation scan, recalibrated

- **Diagnosis** (Δ208 §11.4). The first scan refused a file that shared any one 7-token shingle
  with a twin's answer lines (the lines a twin holds that its learner file does not). Every
  lab card failed: Lab 1's 22 shared 8–272 shingles each, Lab 2's 20 shared 35–64. Two causes:
  (1) a card copies its definitions from the course (layers, other modules' shipped files),
  and a twin that copies the same definitions where its learner file imports them makes them
  "answer lines"; (2) short structural fragments recur (an argument list `(a[1..], b[1..])`, a
  parameter list, a guard `if |a| == 0 {`), so a single shingle is no evidence.
- **The rule as built** (`author_scan`): (1) a shingle that any learner-visible course code
  file shows (git's tracked and untracked-not-ignored `.dfy/.rs/.py` under `dafny/`, `verus/`,
  `harness/`; never `bench/`) is no answer; (2) a hit is a whole span of a twin's answer lines,
  that is, a minimal run of consecutive answer lines with at least `SPAN_TOKENS` = 10 tokens
  showing at least one non-visible shingle, every one of whose 7-token shingles the file holds
  (whitespace and comments aside). The lab cards' references (`Solutions/bench/local/<t>/<lab>/
  <card>/<f>`, learner file `bench/local/<t>/<lab>/<card>/tasks/<f>`) are twins too. The leak
  patterns are unchanged.
- **Calibration** (2026-10-12): with (1) alone 12 of 42 cards still hit, on 1–10 structural
  shingles each. With (2), all 42 Lab 1/2 cards and Lab 3's 36 sealed files pass at 9 tokens
  and above; at 8, one twin's answer line `if |a| == 0 {` (8 tokens) meets card d08's code.
  `SPAN_TOKENS` = 10 keeps one token of margin. **Catch rate:** every one of the 2,934 twin
  answer lines of at least 10 tokens that no learner-visible file shows, planted alone into a
  Lab 2 card, is caught; of the 626 such lines of 7–9 tokens, 5 are caught alone (a known
  limit: a short answer line is caught only inside a longer copied run; the leak patterns and
  the pools' task-form check remain).
- **Attested** (`sandbox/attested.toml`, 78 entries): Lab 1's 22 and Lab 2's 20 cards with
  `mksandbox-run --author --attest` (42 attested, 0 refused); Lab 3's 36 crate files from the
  sealed archive: decrypted with the pinned age and the key into lane scratch (mode 0700),
  archive sha256 `03a61d88…` and its manifest `92b778e9…` as STRATUM.toml pins, every file
  checked against the manifest, scanned and attested with `attest_data` at the path
  `fvh unseal Q18` writes (each entry's `source` says so); the plaintext was removed at once.
  Lab 1's cards are not strictly needed by the plan (Lab 1's policy runs and the lab gate stage
  the work copy and the task form inline), but QPLAN §6's "attested task cards" and DV4-PLAN
  §5.4 item 3 mean every lab card; attesting them costs nothing.
- **Real-tool check:** agent manifests built with `mksandbox-run --build-agent` for Lab 2's d01
  and v01 and Lab 1's dh4 (each staged by src) pass `--selftest-only` (attestation 1 card,
  public answers against every installed set's answers, closure, canaries) and, for d01,
  `--author --selftest-only` (the author check ran, 0 problems). Archive `selftest/`.

## 6. The leak scan of the fetched answers (Q57)

Every fetched public answer (DafnyBench 785, HumanEval-Verus 167, vericoding 2,683,
MINIF2F-DAFNY 12) against every twin's answer spans (the rule of §5): 64 files hold a whole
span (DafnyBench 6, HumanEval-Verus 3, vericoding 55, MINIF2F 0), over 42 distinct spans, all
generic idioms (loop-bound invariants such as an index between 0 or 1 and a length, a
counter's initialisation and loop head, the sequence-split assertion, a recursion guard on an
empty sequence); none is a course-specific answer. Archive `leak/leak-scan.json` (paths only).
The sets stay `fetch`; the manifest's `leak_scan` field is left empty (moving a set to
`vendor` is its own DELTAS entry).

## 7. Open items

1. **Lab 2's public task forms (kits lane or the next DV5 lane; high: before Lab 2's runs).**
   QPLAN §25.6 draws 5 HumanEval-Verus tasks (prose: the docstring; reference: the task's
   specification) and 5 HumanEval-Dafny tasks from vericoding's `humaneval` source. This lane
   built Lab 1's form (proofs removed, specification and code kept); Lab 2's form (the
   specification removed, the prose and the code kept, an empty witness, as the local cards)
   and its reference statements are not built. The pools exist: HumanEval-Verus 83,
   vericoding `dafny/humaneval` 143. A second transform beside `verus-strip-proofs` is the
   natural route.
2. **The lab gate and shipped assumptions (tools owner; medium).** `vcheck --gate` does not
   count `assume {:axiom}` (only `vaudit` reports it), and the lever check allows a lever the
   task form ships, so a delivery equal to a task form that ships one passes the lab gate.
   The course's pools are safe (the vericoding transform and the pool rule's
   `task-form-passes-the-gate`), but any later task source with a shipped assumption is not.
   Options: (a) the lab gate also applies vaudit's assumption rules to a delivery;
   (b) count `assume {:axiom}` as a hole in the gate; (c) leave it to each pool's validation.
   Recommendation: (a).
3. **Records (kits and records lanes; low).** Learner-visible sentences that call the pools
   pending: `docs/Q12_PracticeIC.md` §0 (line ~65), `docs/Q15_PracticeIIC.md` (lines ~81 and
   ~629; Lab 2's public forms stay pending, item 1), `bench/local/q/lab1/STRATUM.toml` (lines
   27–29), `bench/local/q/lab2/STRATUM.toml` (line 21); re-capture any chapter pins.
   QPLAN §22.6 (the strata sentence: the pool rule as built; the public row: "a loop's
   decreases kept"), §30 Q57 (closed). DV4-PLAN §5.4 items 3 and 5 (the scan as built), §7.1
   (`transform`, CHANGES), §7.2 (`--validate`'s rule and flags, `--pin-pool`, POOLS.toml,
   `DVL_BENCH_TMP`), §7.3's humaneval-verus and vericoding rows (the normalization).
   CLAUDE.md's Not-built line: drop "the public strata's validated pools, HumanEval-Verus's
   stripping step and the lab cards' attestation".
4. **The draws (kits lane; medium).** Draw from `bench/public/POOLS.toml`'s members (the
   pre-registration can name its `pool_sha256`). One vericoding answer changed verdict
   between two runs (inconclusive, then verified): a drawn task's answer near the resource
   limit can flip, so the pre-registration may check the drawn answers with
   `vcheck --brittleness` or name a redraw rule.
5. **The scan's known limit (tools owner; low).** An answer line of 7–9 tokens planted alone
   is caught in 5 of 626 cases (every line of 10 tokens or more is caught): a short answer
   line is caught only inside a longer copied run.
6. **Lab 3's attestation, not exercised live (the author; low).** The 36 entries match the
   sealed manifest's sha256; an agent batch's preflight after `fvh unseal Q18` (which needs
   the statements pin) will be their first live use.
7. **The merge (orchestrator).** `bench/public/POOLS.toml` is the one tracked file under
   `bench/public/` (the set directories are gitignored; rule 2f covers it by path); commit it
   with `bench/manifest.toml`, whose two digests changed.

## 8. DELTAS-ready text

### Δ2xx · The public pools validated and pinned; HumanEval-Verus's stripping step; get_bench's transforms and resumable `--validate`; the attestation scan recalibrated and 78 lab card files attested — adopted (DV5d, 2026-10-12)
- **Status:** QPLAN §30 Q57 and Δ217's DV5 item (high: before Lab 1's and Lab 2's runs); Δ208 §11.4's attestation item; the agent-mode lane's open item on Lab 3's 36 crate files. Like Δ195–Δ217 it names no answer. Detail: `Solutions/plans/DV5d-pools-notes.md`.
- **Change:**
  - **`get_bench.sh --validate`** (`scripts/dvl/bench.py`). The pool rule: the answer passes the done check (`vcheck --gate`, verified with 0 holes; `vaudit`, no finding), passes the lab gate's static half as a delivery for its task form (`specfreeze --lab`, 0 findings: no statement changed or missing, no lever added or dropped), and its task form fails `vcheck --gate` as shipped at the verify stage; an answer equal to its task form is no task. A job killed by memory (137/143), stopped by the net (124) or without JSON is never a verdict: its row is re-run by the next invocation. Resume-safe (`validation.partial.jsonl`; the same command continues; another selection, set digest or tool pins needs `--restart`), stoppable (SIGINT/SIGTERM keep the finished rows), `--workers` 1..4 (default 1) within `--mem-gb` (workers × cap ≤ the share; MemAvailable ≥ share + 15 GB at the start and cap + 15 GB before each job, else it waits), a pre-registered seeded stratified `--sample N --seed S`; `validation.jsonl` schema 3 opens with a header (set digest, pins digest, selection, wall time, counts by reason and stratum). `DVL_BENCH_TMP` places get_bench's temporary trees.
  - **`get_bench.sh --pin-pool`** (author-only) writes **`bench/public/POOLS.toml`** (new, tracked; rule 2f by path): per set the pool's members, their list's sha256, the counts, the set digest and the tool pins; `--check` compares an installed `validation.jsonl` with it and flags a pin made on another digest or other pins.
  - **Transforms** (`scripts/dvl/benchstrip.py`, new; a layout row's `transform`, recorded in each set's CHANGES): `verus-strip-proofs`, HumanEval-Verus's stripping step (proof fns, proof statements, ghost lets, reveals and loop invariants removed; the specification, the code and each loop's `decreases` kept, since Verus refuses a loop without one before it verifies; a proof fn a kept line names keeps its signature); `verus-drop-main` (the top-level `fn main` outside `verus!`, which the gate's V9 lint refuses: HumanEval-Verus's answers, vericoding's Verus files); `dafny-axiom-assume-to-hole` (vericoding's Dafny task forms: `assume {:axiom} false;` becomes `assume false;`, a hole the gate counts). humaneval-verus re-pinned `89d53507…`, vericoding `0eb0ae37…`.
  - **The attestation scan** (`author_scan`, `scripts/dvl/sandbox.py`): text that any learner-visible course code file shows never counts, and a hit is a whole span of a twin's answer lines of at least 10 tokens; the lab cards' references (`Solutions/bench/local/`) are twins. `attest_data` attests given bytes and records a `source`.
  - **Attested** (`sandbox/attested.toml`, 78 entries): Lab 1's 22 and Lab 2's 20 cards; Lab 3's 36 sealed crate files, from the author's decrypted copy (the archive's and its manifest's sha256 as STRATUM.toml pins, each file against the manifest), at the paths `fvh unseal Q18` writes.
- **Why:** the pools (whole sets, no sample needed, one 32 GB scope, no job killed): DafnyBench 303 of 785 (363 s, 4 workers), HumanEval-Verus 83 of 167 (188 s, 2; 78 upstream files are TODO stubs), vericoding 2,264 of 2,683 (3,902 s, 2; its `dafny/humaneval` stratum 143 of 151), MINIF2F-DAFNY 0 of 12 (not a pool). What the rule's parts caught: `vcheck --gate` passed a Dafny file whose only gap is `assume {:axiom}`, and the lever check allows a shipped lever, so an unchanged vericoding task form passed the lab gate (probed; closed for the pools); 35 vericoding answers hold `assume {:axiom}` (vaudit); 24 answers change or drop a statement and 3 add a lever (the static half); 18 DafnyBench task forms do not parse and 105 vericoding task forms name a helper only the answer defines. The scan: the first unit (one 7-token shingle) refused every lab card (Lab 2's 35–64 shingles each, on copied definitions and structural fragments); as built, the 42 cards and the 36 sealed files pass at 9 tokens and above, and each of the 2,934 twin answer lines of 10 tokens or more that no learner-visible file shows is caught when planted into a card. The leak scan of the 3,647 fetched answers: 64 files hold a whole twin answer span, over 42 distinct spans, all generic idioms (loop bounds, sequence splits), none course-specific; the sets stay `fetch`. Agent manifests staging Lab 2's d01 and v01 and Lab 1's dh4 by src pass `mksandbox-run --selftest-only` and `--author --selftest-only`. Tests: `tests/bench` 34 (23 new: the stripper, its residue check, the installed set's tasks, the transforms, `--validate`'s rule, retry, stop and resume, sample, share and `--pin-pool`), `tests/sandbox` 5 new (a card copying definitions attested, a planted answer line caught, a fragment no hit, a lab reference as a twin, `attest_data`); `ci.sh --author --job harness` PASS (core 541, sandbox 164, bench 34) and `--job static` PASS; the leak verifier 18 modules, 1,613 public files OK.
- **Touches:** Δ103, Δ152, Δ182, Δ208, Δ215, Δ217; DV4-PLAN §5.4 items 3 and 5, §7.1–§7.3; QPLAN §22.6, §25.6, §30 Q57, Q63; CLAUDE.md's Not-built line; `scripts/dvl/{bench,benchstrip,sandbox}.py`, `bench/manifest.toml`, `bench/public/POOLS.toml`, `sandbox/attested.toml`, `tests/bench/`, `tests/sandbox/test_sandbox.py`.
- **Owner:** DV5d's pools lane.
- **Open:** Lab 2's public task forms and references (kits lane, high); the lab gate and shipped assumptions (tools owner, medium); the draws' brittleness check (kits lane, medium); the learner-visible "pending" sentences and the plan records (kits and records lanes, low); short answer lines in the scan (tools owner, low).
