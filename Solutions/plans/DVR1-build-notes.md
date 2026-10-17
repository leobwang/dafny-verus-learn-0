# DVR1 build checkpoint — 2026-10-17 UTC

Author-only coordination; no live model validation is claimed.

## Worktrees and release dependency

- Q authoring: `/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0-authoring`, branch `authoring`, `ec2a60a` records D45. Its full model-free author CI continues in `build/ci/20261017T003253Z-2536741/`; study CI follows automatically on success. Driver logs are in `/tmp/dvl0-dv7-freeze/`. Do not remove that scratch while the driver writes it.
- Q candidate: `../dafny-verus-learn-0-basic-candidate`, branch `basic-candidate`, amended candidate `fb2b6b8`, exactly one commit atop design-only main. Q01–Q18 shipped metadata; R/challenges planned. History checker, course map and 18-chapter lint pass. Candidate static CI `build/ci/20261017T032721Z-61186/` passes (417 s), including the four shipped-aware synthetic fixture repairs in Q authoring commit `40a9b5a`. Final source leak audit passes (18 modules, 1,643 public files), and the D42 history check passes. Full Q author/study CI is still required before promotion. Candidate README/CLAUDE are coherent about the Q release candidate, planned R and D45 debt. Keep main unchanged.
- This worktree: `../dafny-verus-learn-0-r-authoring`, branch `authoring-r`, based on `ec2a60a`. R changes are staged/unstaged, not committed yet. Study mode restored before focused CI; do not commit an authoring settings change. This branch must be transplanted onto the initial Basic squash; never merge its old authoring ancestry into Basic. Preserve all work first.
- User instruction: “record the blocker and skip. continue to build.” D45 defers Claude-dependent guard acceptance, simulations, grading calibration, capstone and contractor transcripts as validation debt; no provider override, reserve release or model call. Local proof/CI/leak/history checks still apply. After Q release, continue R on Basic, then challenges later.

## Built here

- Transplanted the reconciled DVR0 A1, A1b and A2 layers to frozen public given paths in both languages. A1 definitions only; A1b owned by future R06; A2 owned by future R07. Declared their import ownership on planned R02/R06/R07 records. Removed spike-only headers and gate-region markers; semantic payload retained. All six layers gate and audit clean; three seeds each pass (`seeds/results.json`, first 18 entries). Do not ship later A3–A5 yet; their remaining DVR2/DVR3 decisions still apply.
- R01 exercise and reference pair, given-only value check, two verdict slots, 32 specimens (predictions, scenarios, WRITE cards, false friends, triage), two four-bug agent files and complete twins, paper pair/reference/rubric, flawed/gold card fixtures, 12-question bank and two bilingual parallel problems, eight leak patterns, expected count/freeze/prediction/chapter pins. Registry R01 authoring; other R modules planned. Chapter about 6k words, four diagrams, six predict boxes, 14 live captured output fences.
- Planned census fallback adopted: singleton lemma proves empty, so T1 uses two characters. Two declarations per code test-out, still five typed holes per language. Source/reference census checks now state the concrete slice fact and call the requested pair lemma; all enabled checks verify.
- Agents: four independent primary diagnostics and zero holes in each shipped file, four single-line repairs; reference twins verify and audit. Wrong recursive prefix is used for the Dafny plant because the originally proposed two-position suffix legitimately proved the length claim by two-step unfolding. Verus base facts supplied in both copies.
- R01.P6v uses the existing native compiled `assert_eq!` value door; ordinary Verus proof assert is not a supported value-slot form. `Answer form: numeral` is the supported literal form, including signed integers. Every reference switch is enabled and headers say Reference Solution. Reference-only helper checks are labelled for the reference lint; their heading is not the learner's Uncomment header.
- R01 bank has 12 rather than the minimum 8 questions so two six-question vivas are disjoint. Both referee probes and all four completed parallel variants checked, gate/audit clean; raw source and commands in private cache. No course-hole answer exposed in bank/chapter.

## Tool fixes and regressions

- `scripts/vcheck::frame_symbols`: a header learner region covering requires and no modifies routes to open_specs. Ordinary frames remain frames; mixed modifies+requires still fails closed. This closes PLAN R11 on the real R01 requires-only annotation hole. New integration test pins, fills and checks one, then rejects a weakened shipped ensures; boundary test covers a requires-expression-only region and existing/mixed frames.
- Existing open-frame refusal test now actually tests mixed modifies+requires; a requires-only region is the newly supported open-spec form.
- `scripts/chapter_lint.py`: no given-layer path is required when the registry's layer is empty (R01). Regression preserves the requirement for a layered module.
- Protected leak verifier remains only in its README, now includes R01 in its module table and handles A1b ordering. Ten explicit cross-track/equal/above/below/unknown-layer boundary checks pass. Final source-leak repeat after public status/tool edits passes: 19 modules, 1,704 public files. No public script opens patterns.
- `scripts/firsttry.py`: pure Verus contract annotations with supplied exec code use TRIV plus RGN by default. Recognition requires every reference region to lie in the contract and the raw reference body to equal the shipped E0 projection by tokens; additional implementation or proof work retains the ordinary modes. Explicit mode selection is preserved. Tests reject different bodies, added proof work, absent/broken/body regions and a proof declaration; routing tests keep RGN necessary. Final forms suite: 63 tests pass. Full tool-free static sweep passed 409 tests (one skip; before removing five duplicate inherited cases).
- R01 activation repairs: the field-order regression preserves the actual R01 status; the empty-range list case uses the explicitly planned stand-in. N1 remains approved in PLAN §5.4 but its future R16 Split row is commented until that declaration exists; an unused active row is stale once any R module is armed. No collision is waived in the meantime. Initial static CI caught these cases; the rerun is required.
- Static suites: 41 practice-tools tests pass; 114 tools tests pass, one skip. All 19 modules map cleanly (150 import files); R01 lint and hollow checks clean; source-leak verifier 19 modules, 1,704 public files, OK; avoid gate clean after renaming three toy demo names that collided with Q. Native source/header/declaration parity lint is clean.

## Private evidence and active checks

Everything under `/tmp/dvl0-dvr1-build/`, to archive under guarded `~/.cache/dafny-verus-learn-0/author-probes/dvr1/` after local checks. Preserve canonical final logs; failed setup attempts are not verdict evidence.

- `r01-counts-final.log`: reference counts 22 Dafny tasks / 17 Verus functions; 11 contracted symbols pinned in each unit. Shipped exercise units verified with 5 holes each; both agents failed with 4 errors and zero holes.
- `reference-lint.log`: zero findings after reference-only check labels. Refresh if later reference comments change.
- `r01-pins-final.log`, `r01-chapter-pins-final.log`: two verdict pins and 14 chapter captures. P6 native compiled value path captured.
- `workflow-final.log`, `workflow-results.json`, `workflow-firsttry.log`, `workflow-strict.log`: completed-reference input in disposable study checkout, no model: all 11 workflow checks pass. Six predictions and two code test-outs record and pass, then strict report OK; both code/agent gates and all audits pass. Clone removed. This is a scripted author smoke, not F3–F6 model validation.
- `core-stability-{d,v}-final.log`: current reference units, including enabled checks, stable on seeds 1–3. `r01-reference-stability.log`: agent twins stable on seeds 1–3. Initial `seeds/` attempted --ref --seed calls are invalid CLI setup, not proof failures; the --brittleness logs supersede them.
- `bank-final.log`, `bank-probes/results.json`: all expected outcomes and four completed gate/audits pass. Earlier PP1 missing-pub trial is superseded.
- `r01-empty-body-final.log`: 8/8 grouped hole items pass before the final reference-check enablement. `r01-empty-body-release.log` found a real H3v tool mismatch (7/8): overlaying the missing precondition makes the already-given body verify under E0, as expected. The pure-annotation routing repair is above; `r01-empty-body-release-fixed.log` is the final repeat: all eight grouped hole items pass; H3v runs TRIV and its mandatory RGN sweep on seeds 1–3. Do not count the earlier failed run as admission. `census-exec.log` already has six passing counterchecks (the two census exec bodies replaced by zero, three seeds each), ensuring both census holes are substantive.
- `paper-checks/`: R01 reference, flawed fixture and gold fixture all compile. Learner-facing 38 documents already compile. R01 focused static CI is running in study state under 4 GiB, without solvers.
- Candidate pure static CI passed under 4 GiB, no solver. Q native lane 32 GiB plus this R native lane 16 GiB stays within the 48 GiB solver budget. Host has about 95 GiB available. Before every new sweep check free memory again.

## Next

1. Final R01 admission repeat passes 8/8. Final static CI passes: `build/ci/20261017T035010Z-167293/`, 446 s, 396/396 course-map regressions. It includes seven R given files in fixture counts and clears both tracks when testing a truly empty module glob. Native CI `20261017T034242Z-135612` passed verify-r-dafny (15 s), verify-r-verus (31 s), paper (10 s) and harness (73 s), but found two stale reference hashes in R01's rubric. Refreshing those is validated by `20261017T034624Z-155495/`: rubric passes, all 118 pins current. Targeted R01 pins CI passes 25 checks with zero problems. No native code changed after these passes. Re-pin freeze after final source/check changes, refresh rubric hashes and source/chapter pins only where stale, compile R01 reference and two fixtures.
2. Run model-free focused R CI in study mode: static, verify-r-dafny, verify-r-verus, paper, rubric, harness; targeted R01 pins check. Needed before checkpointing R01. Keep the Q verification tree isolated. No additional solver lane while R's 16 GiB lane is active.
3. Final 19-module leak scan after staging, diff check, restore study settings, commit R work. Add numbered DELTAS entries only when integrating with the Q release, to avoid Δ248 collision (candidate already reserves it).
4. Advance R02 from PLAN §6.2 and existing reconciled references while full Q CI completes. Before promoting Q, finish candidate static/leak checks and record the full author/study summaries. Promote as D42, preserve old branches and transplant R commits onto the new Basic baseline. Never push externally or update the primary checkout during author orchestration.

## Final R01 checkpoint

- Initial content/tool checkpoint: `ddd1f7a`. The following evidence/fix commit preserves all native payloads and closes the static fixtures and rubric metadata. Study mode is the committed state.
- Final admission: `r01-empty-body-release-fixed.log`, 8/8. All given layers and reference units/agents have the seeded evidence listed above. Completed-reference study workflow is 11/11; no model.
- Final full source-leak audit is repeated after staging. Evidence copied under the guarded `author-probes/dvr1/r01-final-20261017/` directory, including failed setup attempts explicitly superseded by the final runs.
- R02 development is isolated in `../dafny-verus-learn-0-r02-authoring`, branch `authoring-r02`, initially at `ddd1f7a`. Carry this final R01 evidence/fix commit forward there before arming R02. Its registry stays planned while prototypes and remaining kit are prepared. Do not copy the R01 active CI state into the Q release tree.


## Basic transplant checkpoint — 2026-10-17 UTC

Initial Q release39ba47b is local basic/basic-candidate, sole parent main6f453d0.
Full author14/14 and final study12pass+2expectedskip; final leak18modules/1642
public files, course map and history pass. Archived authoring40a9b5a is now
authoring-q-archive-20261017. No push. Canonical authoring starts at Basic.

Transplants: R01 ddd1f7a->151bfa0, final6bd5fab->9366fd9; R02
34b33b5->0d275c7, finalb354945->687e538; R03 tooling/private parked draft
659b565->cad7034. README retained released Q status; Δ248–250 remain before
Δ251. No legacy ancestry merged. R01/R02 candidate status is shipped for
combined-tree verification; Basic waits for focused integration CI/pins/leak.
R03's OD8 primitive-packaging blocker remains recorded and skipped, planned.
Active R04 draft still lives in ../dafny-verus-learn-0-r04-authoring, with
standalone native paired source/ref cores; source6holes/errors0 each, refs
17/17 native tasks, zero holes/errors. Admission/predictions/kit are in progress.
Live Claude debt remains deferred under D45.
