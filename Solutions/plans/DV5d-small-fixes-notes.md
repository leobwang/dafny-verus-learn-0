# DV5d small open fixes (Δ217's low and medium list): notes for the integration lane

Author-only (reference class). Lane scratch was `/tmp/dvl0-dv5d-small/`, now removed. The
captures (the pcount before/after tables over every reference declaration, the Verus naming
probe, the Q16 twin's `--ref --brittleness` output, the `ci.sh --author --quick` logs) are
archived under `~/.cache/dafny-verus-learn-0/author-probes/dv5d/small/`. Every solver job ran
under a 16 GB `systemd-run --user --scope` (MemoryMax=16G, MemorySwapMax=0), and only when at
least 31 GB was available (95–97 GB was free each time). Nothing was killed.

## 1. What changed, item by item

1. **The plan's sha256 as a PREREG field** (Q12, Q15, Q18).
   - `paper/Q{12,15,18}_answers.tex` each gain one PREREG field, the last in B1's or B2's
     block: **Batch plan**. It asks for the plan file's path and its sha256 on a line of its
     own, as `plan-sha256: <64 hex>`, the value `sha256sum` prints.
   - `harness/fvh/prereg.py` gains `plan_fields(path)`, which returns the values the block
     names (case-insensitive hex, exactly 64 digits), and `check_plan(root, module,
     plan_sha256)`. `check_plan` refuses when the block names no plan, two different plans,
     or a plan other than this one.
   - `fvh.batch.Batch.open` calls `check_plan` on a lab plan right after `prereg.check`. The
     field sits inside the hashed block, so a changed plan needs a re-graded
     pre-registration.
   - `fvh resume` needs nothing new: it already re-checks the full PREREG hash and the plan
     copy's sha256.
   - Tests: `harness/tests/core/test_prereg.py` (6 new cases); `test_batch.py`'s two lab
     tests now write the field through a helper, `prereg_for`, and cover the refusals.
2. **Gate v2's container route for fixture copies.** I chose to reword the docstring rather
   than add a route.
   - `gate_v2.main`'s docstring, in the learner file and its twin, now says that the
     container is built from the course crate whose path the copy's path ends with. A plant
     is therefore a copy of a course crate (the capstone crate, a Lab 3 card's task). A copy
     of a `tests/q/fixtures/` crate raises RunnerUnavailable.
   - `specfreeze --pin Q18` rewrote `expected/Q18.freeze` byte-identically: docstrings are
     not part of a statement. `specfreeze --check Q18` reports 0 findings.
   - Test: `harness/tests/core/test_tools.py::test_a_plant_copied_from_a_fixture_crate_has_no_container_route`.
   - The real registry agrees: `ContainerRunner().course_rel` refuses
     `/tmp/x/harness/tests/q/fixtures/q18/K1` and maps `/tmp/x/verus/q/q18_practice_iiic`.
3. **Guard rule 2c refuses `fvh unseal` while a contract is active.**
   - In the hook, `RX_2C_AGENT`'s fvh list gains `unseal`.
   - While a contract runs, the 2c agent check now runs before rule 1c, so the contractor
     gets the contract's reason. With no contract, rule 1c still refuses `unseal`. The later
     duplicate check was removed.
   - The header's 2c paragraph and the block message name `fvh unseal`.
   - Fixtures: two `rule 2c` rows (`python3 -m fvh unseal Q18`; `cd harness && uv run …
     -m fvh unseal Q18`, both with a contract) and one `rule 1c` row (no contract).
   - A pre-existing failure was fixed on the way: the "cat of an author lane's scratch" row
     named `/tmp/dvl0-dv5c-q18/…`. A shell file operand is checked only when it exists, so
     the row passed only while that lane's scratch existed, and it failed after D19 cleared
     it.
   - `scripts/test_hooks.sh` now creates a throwaway lane directory
     (`/tmp/dvl0-dvhooks-XXXXXX`, one decoy file, removed on exit) as the placeholder
     `@LANE@`. The row uses `cat @LANE@/crate/src/lib.rs`, and `gen_hook_fixtures.py`'s
     docstring names the placeholder.
   - `test_hooks: 6790 passed, 0 failed` (before the pools lane's `bench.py --pin-pool`
     landed, §3).
4. **`pins.py --ref --module` on a module with nothing to check.**
   `tests/wrappers/test_tools_static.py::PinsStatic::test_ref_module_with_nothing_to_check`.
   The test strips the synthetic Q04's two verdict items and its slots. `--ref --module Q04`
   then passes loudly (exit 0, "nothing to check for it (passing loudly"), and `--ref` with
   no module fails (exit 1, "an empty set fails"). The tool needed no change: the DV5c gaps
   lane had already built the behaviour.
5. **Q18.H1v's shipped `cast_out`: not reworded.** DECISION NEEDED (§4). Any correct
   invariant for the top-down loop is a statement about the value of the processed suffix,
   and so is the delivered proof block the item hands the learner. Hiding that domain
   changes the item.
6. **pcount's hand corrections fixed in the tool** (`scripts/pcount.py`). Four changes:
   - A Dafny `ghost predicate` or `ghost function` counts its body as proof.
   - A ghost update counts as proof. In Dafny that is a `ghost var` field the file declares
     with no initializer, or a local `ghost var` of the counted body. In Verus it is an
     assignment whose value is `Ghost(…)` or `Tracked(…)`, never a `let` destructuring.
   - A Dafny call statement to a name the file declares as a method or constructor, and not
     as a lemma, counts as code.
   - An assertion's continuation lines count as proof until the statement ends (a line
     ending in `;`, `{` or `}`).
   - Also new: `constructor` is accepted as a declaration name.
   - Tests: `tests/wrappers/test_pcount_static.py::HandCorrections` (4 cases, invented
     toys).
   - **Every reference declaration before and after** (1,802 declarations):
     - Q17.H1d is **54**, now straight from the tool; its hand corrections are removed.
     - Q14.H5v is **19**, now from the tool (`push_front` 4); its "by hand" is removed.
     - Q17.H2v is **59, not 58**. The old hand count missed `grow`'s tracked field update
       (`self.perms = Tracked(…)`), which Q14's notes count. 59 is still inside the band
       (45–120), so its admission and its 50 minutes are unchanged.
     - Q11.H1d moves 0 → 1 and Q11.H2d 2 → 3 (the ghost update `Contents := …`). Both stay
       within the band (≤ 10).
     - Elsewhere only exits, checks, spikes and Q02–Q08 declarations that no note counts
       moved.
   - The Q17, Q14 and Q11 notes are updated.
7. **Verus brittleness symbol attribution** (`scripts/vcheck`).
   - A Verus run keys its resource counts `<crate>::<path>`, and it names a trait impl's
     method or a generic impl's method under the bare type. A probe on the pinned Verus gave
     `probe::S::t` and `probe::G::g`, where `symbol_sites` has `<S as T>::t` and `G<A>::g`.
     So `--ref --brittleness` printed "(a declaration outside the target's files)" for every
     Verus spread entry.
   - New `site_of` tries the symbol, the symbol without its crate prefix, and both against
     `verus_run_name` aliases of the sites (generic arguments dropped; `<Ty as Tr>::f` →
     `Ty::f`).
   - The output names are unchanged, so the pinned Q09 fences hold.
   - Live check on the Q16 twin: before, `widest spread (a declaration outside the target's
     files) 89803..124519 (CV 16.0%)`; after, `widest spread
     Solutions/verus/q/q16_practice_iiia/src/lib.rs:69 …` (`lemma_set_limb`, which the Q16
     notes had attributed by its counts; the note is updated).
   - Test: `tests/wrappers/test_forms_static.py::Sweep::test_verus_symbols_attributed_to_their_sites`.
8. **The secret scan's fallback form** (DV4-PLAN §5.7; `scripts/dvl/sandbox.py`).
   - `live_run(…, exact_secrets=())` takes the exact credential values a run was given. Each
     must be a string of at least 16 characters, kept in memory only and never recorded.
   - The values join the credential formats in every scan of what comes back: the returned
     files, the agent's event stream, `gate.log`, and (new, for both the formats and the
     values) each command's stdout and stderr.
   - A command output with a hit keeps neither stream. Its entry carries a `withheld` record
     (`command-<n>.log`: name, size, sha256, findings).
   - `rec["secret_scan"]` lists every withheld record and `exact_values`, the number of
     values matched against.
   - `mksandbox-run` gains no flag: a credential never goes on a command line.
   - Tests: `tests/sandbox/test_live_run.py`, 2 new cases (a returned file and a command log,
     the refusals, a clean run).
   - Claude in a container is still refused (step 4c). This is the scan that step 4c's
     fallback form needs, and the harness-executed exact-value scan (Δ215) is unchanged.

## 2. Runs

| run | result |
|---|---|
| `harness/tests/core` (pytest) | 541 passed |
| `tests/sandbox` (unittest) | 164 OK |
| `tests/wrappers` static suites: tools, forms, pcount, verus, dafny, practice_tools, capstone_routes | all OK (tools: 1 skipped, as before) |
| `scripts/test_hooks.sh` | 6790 passed, 0 failed (before the pools lane's change, §3) |
| `scripts/ci.sh --author --quick` | static PASS (412 s); hook-test FAIL, 1 of 6791: the pools lane's new `bench.py --pin-pool` (§3) |
| `specfreeze --check Q18`; `pins.py --ci --module Q18` | 0 findings; 26 pins, 0 problems |
| leak verifier (README) | 18 modules, 1,613 public files, OK |
| `make -C paper paper` | 36 documents, green |
| `vcheck --ref --brittleness` Q16 twin (live) | stable; widest spread located at `src/lib.rs:69` |

## 3. Open (owner, severity)

- **The pools lane (medium; before the merge).** `scripts/dvl/bench.py` gained
  `--pin-pool` while this lane ran. `test_hooks.sh`'s author-only pass reports
  `'scripts/dvl/bench.py --pin-pool Q04' is not author-only, yet the hook refuses it`. The hook's
  `bench.py … --p(i|in)?` prefix rule now also matches `--pin-pool`. Either the option is
  author-only, in which case it goes into test_hooks' AUTHOR_OPTS for bench.py and into rule
  1b's message, or the hook's prefix rule must spare it. The hook, `test_hooks.sh`, the
  fixture generator and `tests/hooks/` carry this lane's edits too (§1.3), so merge on top of
  them.
- **The records lane (low).** CLAUDE.md's guard paragraph (rule 2c's list: add "and `fvh
  unseal`") and DV4-PLAN's rule table row 2c (the same). Also DV4-PLAN §5.7: the fallback
  form's exact-value scan is built (the bullet "Secret scan").
- **The kits lane (low, optional).** The Q12, Q15 and Q18 chapters could name the Batch plan
  field where they introduce the pre-registration. The rubrics do not grade the field. The
  drop-in gold and flawed answers fixtures (Q12, Q15, Q18) do not carry it: leave them, or
  add the field if a rubric line ever requires it.
- **The user** (via the orchestrator): Q18.H1v's `cast_out` (§4).

## 4. DECISION NEEDED: Q18.H1v's shipped invariant domain

Q18.H1v ships `cast_out`'s complete top-down loop with the invariant
`r == seq_to_nat(a@.subrange(i, n)) % M`, and the delivered proof block it hands the learner
unfolds the same suffix. The suffix-value domain is what Q16.H2v asks the learner to find. No
rewording of the shipped text removes it without changing the item. Options:

- (a) **Accept it as a later-tier overlap** (recommended). Q18 comes after Q16 in both
  tracks, and Q18's file header already says not to open later files before committing
  predictions. Record it as a declared tier overlap in the Q18 notes, and next to the leak
  README's tier exemption.
- (b) **Restate H1v over a recursive spec of the loop**, with no suffix value. The
  `BASE * t` step that makes the delivered block brittle goes away, so the item has to be
  re-probed, re-counted and re-admitted.
- (c) **Hand the domain back to Q16.H2v's prompt** (the hint Q16's chapter removed). That
  lowers Q16.H2v's difficulty.

## 5. DELTAS-ready text (for the integration lane to number)

### Δ2xx · DV5d small fixes: the plan's sha256 in the pre-registration, `fvh unseal` under rule 2c, pcount's hand corrections, Verus brittleness attribution, the fallback form's exact-value scan — adopted (DV5d, 2026-10-12)
- **Status:** built and tested by DV5d's small-fixes lane. Δ217's low and medium items. Like
  Δ195–Δ217, it names no answer (the detail is in `Solutions/plans/DV5d-small-fixes-notes.md`).
- **Change:**
  - **The plan in the pre-registration.**
    - `paper/Q{12,15,18}_answers.tex` gain a PREREG field, **Batch plan**:
      `plan-sha256: <the plan file's sha256>`.
    - `fvh.prereg.plan_fields` and `check_plan` read it. A lab batch opens only when the
      graded block names exactly one plan and it is the plan's (`fvh.batch.Batch.open`).
  - **Rule 2c:**
    - `fvh unseal` is refused while a contract is active, and the contract's reason comes
      first (rule 1c still refuses it in every study session).
    - `scripts/test_hooks.sh` makes its own throwaway lane directory (`@LANE@`). Its
      lane-scratch row no longer depends on another lane's scratch.
  - **Gate v2's container route:**
    - `gate_v2.main`'s docstring (learner file and twin) says that a plant runs in the
      container only as a copy of a course crate. A copy of a fixture crate raises
      RunnerUnavailable.
    - No route was added (the freeze is unchanged; a test pins the refusal).
  - **`scripts/pcount.py`:**
    - A Dafny ghost predicate's or ghost function's body, a ghost or tracked update, and an
      assertion's continuation lines count as proof. An exec method's call statement counts
      as code.
    - `constructor` is a lookup name.
    - The Q17 and Q14 notes' hand corrections are gone, and their figures are the tool's:
      Q17.H1d 54, Q14.H5v 19. Q17.H2v is 59, where the hand count said 58 (the missed
      update is a tracked field's), still in its band and admitted at 50. Q11.H1d and H2d
      count 1 and 3 (in band).
  - **Verus brittleness attribution:** `vcheck --ref --brittleness` locates a Verus spread or
    differs entry by its run name (crate prefix, trait and generic impls; `site_of`,
    `verus_run_name`). The printed names are unchanged.
  - **The secret scan's fallback form** (DV4-PLAN §5.7):
    - `dvl.sandbox.live_run(…, exact_secrets=…)` matches the exact values a run was given,
      in memory only, in the returned files, the event stream, `gate.log` and each
      command's output.
    - A command output with a credential format or a value is withheld like a returned
      file.
    - Claude in a container stays step 4c's.
  - **`pins.py --ref --module`** on a module with nothing to check: a test (the behaviour is
    Δ215's).
- **Why:** this lane's runs:
  - `harness/tests/core` 541 passed; `tests/sandbox` 164 OK; the wrapper static suites OK.
  - `test_hooks.sh` 6790 passed, 0 failed.
  - `specfreeze --check Q18` 0; `pins.py --ci --module Q18` 0 problems.
  - The leak verifier OK over 1,613 public files; `make -C paper paper` 36 documents.
  - A live `vcheck --ref --brittleness` on Q16's Verus twin (its widest spread now located).
  - A Verus naming probe (scratch).
  - Captures: `~/.cache/dafny-verus-learn-0/author-probes/dv5d/small/`.
- **Touches:** Δ91, Δ173, Δ192, Δ207, Δ214, Δ215, Δ217;
  - `harness/fvh/{prereg,batch}.py` and `harness/tests/core/{test_prereg,test_batch,test_tools}.py`;
  - `paper/Q{12,15,18}_answers.tex`;
  - `harness/q/fvh_q/gate/gate_v2.py` and its twin;
  - `.claude/hooks/spoiler-guard.sh`, `scripts/test_hooks.sh`, `scripts/gen_hook_fixtures.py`, `tests/hooks/`;
  - `scripts/pcount.py`, `scripts/vcheck`, `scripts/dvl/sandbox.py`, and the tests in
    `tests/wrappers/` and `tests/sandbox/`;
  - the Q11, Q14, Q16 and Q17 code notes.
- **Owner:** DV5d's small-fixes lane. Open:
  - Q18.H1v's invariant domain awaits the user (notes §4).
  - The pools lane reconciles `bench.py --pin-pool` with the hook's author-only rule.
  - The records lane updates CLAUDE.md's and DV4-PLAN's rule 2c lists and DV4-PLAN §5.7.
