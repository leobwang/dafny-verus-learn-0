# DVR1 R03 author checkpoint — 2026-10-17 UTC

Private coordination and evidence index. No live model validation is claimed.

## Deferred blocker (D45)

The user explicitly instructed: “record the blocker and skip. continue to build”. Live Claude guard acceptance, coaching/contractor sessions, grading calibration and transcripts remain unvalidated because the approved quota sentinel rejected calls at its seven-day limit. Record this as validation debt; it does not block the current Basic build or initial release. Do not call Claude, retry the sentinel or override the reserve. Scripted controls and completed-reference workflows do not count as model validation. See docs/design/BASIC-RELEASE.md and the Q author notes for the canonical debt inventory.

## Isolation and state

Worktree ../dafny-verus-learn-0-r03-authoring, branch authoring-r03, starts at 34b33b5 and carries R02 final evidence as 60b5792 (equivalent to b354945). Main remains design-only and untouched. Q candidate is fb2b6b8, one content commit atop main, pending full study CI after full author CI passed14/14. Restore study mode before staging, committing or release CI. No external push.

R03 is still planned in the registry. Initial paired core and protected references exist; the remaining module kit is being authored before activation. PLAN §6.3 and Solutions/plans/R-author-notes.md §4 govern this work. A1 only; no A2 import. Reserve Δ250 for Q release; Δ251 records R01/R02 validation, the delegated R03–R16 manual-lemma-induction option and the new export freeze before R03 activation.

## Completed core controls

- Local Dafny opaque datatype API and Verus private-field/ISet view API, worked insertion and independent mini-span API. Five hand holes per language. Completed client checks are enabled only in the private references.
- Dafny exports include a ghost ClassRank contract to state public recursive measures without exposing private ranges. Source holes each have one ensures clause so native bodyless warnings count exactly five. Verus module shells live inside the outer verus! block; no audit exception was added.
- Native prototype captures under /tmp/dvl0-dvr1-r03/: core-d-cards-reference.log15 verified/zero holes/errors; core-d-cards-source.log14 verified/five holes/zero errors; core-v-cards-reference.log21 verified/zero holes/errors; core-v-cards-source.logfive holes/zero errors. These standalone probes precede generated-unit checks.
- core-controls.log and core-controls/results.json:21/21 controls fail as required. Dafny contract-free candidates at seeds1–3, H4 empty-method control, all five Verus TRIV controls. Canonical module admission still required after pins/registration.
- A final Vec membership assertion needed its explicit index witness; the reference and commented learner check use the same given intermediate fact. Early failed setup logs are superseded by the four cards captures above.

## Export freeze

scripts/dvl/dafny.py records export declarations using the existing declaration boundary. specfreeze optionally pins module exports under a frozen-exports marker. Original provides/reveals/extends and export sets are fixed; the only new provides entries allowed are names of pinned open-body definitions in that module. Hidden helpers, datatype revelation, wildcard syntax, changed opacity and removed markers cannot bypass it. Unmarked modules retain existing behavior. Against-snapshot checks enforce the same boundary.

DafnyExports regressions cover legal completion, nine boundary mutations, against without a module pin, and marker scope. exports-regressions-final.log:45 practice-tool tests pass. all-static.log:408 tests pass, one skip. export-native.log: two native tasks pass. units-before-r03.log:41 generated units unchanged before R03 activation. Final module/static/native checks remain required.

## Next

Author and capture predictions/cards without including completed learner targets; then agent API pair, paper03.2, bank/parallel prompts, chapter and pins. Gate actual shipped units, firsttry admission, completed-reference study workflow, seed stability, leak audit and focused CI. Reconcile A2's re-supplied R03 API after R03 validates. Preserve private evidence under guarded author-probes/dvr1 before scratch cleanup.

Initial generator scripts in /tmp/dvl0-dvr1-r03 are stale after native fixes. Do not rerun them. One native R lane at16GiB may run beside Q's32GiB lane, within the48GiB combined solver budget; check host free memory before each sweep.

## Packaging blocker — recorded and skipped, 2026-10-17 UTC

The completed standalone agent prototypes gate and audit clean: Dafny16 tasks,
Verus18 functions, zero holes/findings. Source agents verify with two holes
and two audit findings each. Four completed parallel problems gate/audit;
K2 verifies, K7 reaches verification and fails its assertion (the gate also
adds its summary diagnostic). P1/P2 fail only labels c/d, P3/P4 both languages
fail verification; four cards distinguish verify/resolve, final divergence
D verifies/V fails. Final native logs supersede missing-import setup attempts.

R03 cannot be activated under the current import boundary: Verus scalar
neighbours need a safe Unicode conversion. Pinned char::from_u32 is unsupported;
a proved UTF-8 adapter works with existing vstd assumptions but imports
utf8/string before OD8's R07 boundary. An all-tier agent was correctly rejected.
Moving it into A1 was also rejected by the transitive tier check. Both attempts
are discarded, not exceptions. Public A1 and registry/workspace are restored.

Per the user's record-and-skip instruction, park all R03 artifacts privately at
Solutions/plans/drafts/R03 and continue R04. R03 remains planned. The draft has
paired cores/agents, twelve specimens, four predictions, paper03.2 pair plus
reference/rubric/gold/flawed, twelve bank questions/two draws/two bilingual
parallels, and a draft chapter (~5,929 lint words, four diagrams, sixteen
capture entries). No final module CI, complete pins, leak check or release is
claimed. The draft README lists remaining mechanical work. A2 re-supply is
unchanged until the R03 interface is accepted. No source gate or OD8 rule was
weakened. Do not resurrect the rejected A1 adapter automatically.

Parked-tree validation: course map OK49 modules/155 imports (R01/R02 authoring,
R03 planned), generated units unchanged,408 static tests pass/one skip in70s,
protected source-leak verifier20 modules/1,737 public files/OK. All draft code
is behind Solutions; no new public module or given primitive is shipped.
Private evidence archived at author-probes/dvr1/r03-parked-20261017, with
tracked-tree hashes and the original prototype drivers/results. Restore study
before commit. The next author worktree may start R04 from this checkpoint.
