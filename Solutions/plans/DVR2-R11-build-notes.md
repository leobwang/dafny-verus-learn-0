# DVR2 R11 construction — 2026-10-17 UTC

Worktree authoring-r11, parent98b7dad. R10 source/CI worktree stays clean and
STUDY. Pending R10 final validation and its reference-slot format correction
are inherited after CI; never infer completion from the source checkpoint.
No live actor, grade or calibrated learner time is inferred.

The old A4 V spike uses absolute split positions. Frozen A4 now uses relative
word splits, with an explicit slice alias, and D's checker is ghost. Port the
actual executable checker and proofs to that boundary before any exercise
activation. V completeness has a bounded word-length representability domain;
soundness does not require a stronger domain than actual validity.

Record and skip the already gated S2 PointsTo arena (three exec gates missing).
Use the original plan's Vec-index fallback only after its own four results,
without claiming PointsTo ownership/permission coverage. D45 and parked R03
remain recorded skips. Native lanes stay3×16GiB/48GiB aggregate, GATE_WORKERS=1;
R10 CI owns one lane, its STUDY workflow another, leaving one native probe lane.
PLAN§13 records intended items before activation; all minutes remain0/gated.


## Initial native feasibility

Against the actual frozen A1–A4 chain, private native prototypes pass at the
pins with0holes: checker/soundness/direct completeness D3/V6; complete witness
search D6/V4; streaming-prefix ledger D5/V5; Vec-arena fallback V4; independent
checkpoint D6/V5. None is an admitted exercise yet. Full source and hashes are
protected under drafts/R11/native-prototypes; scratch /tmp/dvl0-dvr2-r11.

V soundness/completeness use relative words, and the executable checker bounds
k<=hi-lo before lo+k. A char-slice equality initially failed; explicitly connect
slice length/index to the singleton model, then the full checker verifies.
V completeness explicitly requires word length<=usize::MAX. Tracked evidence
carries exactly the stated validity premise; it is not an unforgeable runtime
capability or cell permission. Two proof wrappers construct/consume it.

Search is stronger than the old V spike's termination-only producer: Some
implies fixed-model validity and None implies no match. Cat tries0..len and
Star positive chunks; checks at the final index precede increments, preventing
MAX-index overflow. V first termination attempt compared reference/owned
structural ranks incompatibly; use the same mathematical node-count rank in
all mutually recursive functions, plus word length and a finite phase rank.
No resource, trust or theorem statement is relaxed.

A2 already provides its whole-word loop. H4 instead computes every nonempty
prefix's match flag and final acceptance; this is a new ledger target. Its
uniform residual relation is wrapped in an opaque fixed predicate with small
step/observe helpers. The initial D base quantified equality failed and V hit
the pinned rlimit; isolated helpers verify both at unchanged pins. Preserve
that resource result as inconclusive, not a semantic counterexample.

The Vec fallback has fresh node/edge definitions independent of the later A5
VM. Append preserves old nodes and initializes absent targets; linking changes
one edge with exact other-node/label/second-edge frames. Target indices stay
in range. It proves vector/index invariants, not PointsTo permissions. Arena45
minutes still await empty/default/three-seed gates. X1 counts consumed character
leaves, distinct from hand soundness; X2 builds fixed-character Star witnesses
with a fresh loop and ghost word model, not the general search algorithm.

## Canonical admission and metatheory controls

Actual public configuration: 22/22 canonical empty/default/max-auto/three-seed
hole admissions pass, including the four independent exit items. Complete
core and exit references pass three seeds. Meaningful exec TRIV bodies fail.
D H2 and X1 need the printed `{:induction false}` lever: max-auto succeeds,
all three shipped induction-disabled empty bodies fail. This is an explicit
induction exercise, not evidence that automation cannot solve the theorem.
Reference counts D62/V19; learner core8/10 holes, check0, exit2/2, agent1/1.
Counts are pinned but the registry admission/minutes await complete local kit.

H3v initially returned a tracked record. A full proof verified, but canonical
empty bodies failed typechecking, which is not valid admission evidence.
Before activation it was changed to a tracked mutable output slot with the
same validity/result-domain guarantee. The canonical proof-note hole and its
empty variants now typecheck and fail at verification. No gate tool exception
or resource change was made. H2v explicitly moves the tracked input.

A1 is forward character replacement, including noninjective replacements,
not inverse reflection or preservation of normal form. Private deliberate
wrong-rule controls drop the Star tail validity check: transport still native
verifies D/V with0holes. The independent model-only rule consumer verifies
original bindings and rejects changed bindings at verify stage in both
languages. It assumes no transport theorem. Default public tool also proves
the learner's original rule binding. These are author controls, not live actor
sessions, and do not discharge the recorded D45 skip.

## Source kit and reproducible materials

Actual default rule bindings prove D/V; deliberate changed bindings fail both
with the public tool. Original-source snapshot comparisons accept complete body
proofs and reject model edits. Initial comparison naming Solutions directly was
correctly refused as reference material; private delivery copies then exercised
the supported original-source comparison. No reference-access guard was changed.

Compiled actual reference roots pass D149/V151 tests:120patterns×11words,
29explicit certificate cases, plus V invalid-slice and arena frame checks.
Runtime derivations remain ordinary data. Default learner holes stop the runtime
tool at the gate before compilation. No included Dafny implementation is assumed:
actual implementation text is embedded in the verified root. Exact evidence is
under /tmp/dvl0-dvr2-r11/{runtime-reference,agent-delivery-remaining}.

P2's full Seq-based compute-only value exceeded native computation recursion
depth. Ordinary SMT proved it after slice identities, but that is not the course's
value-slot grammar. Before publication P2 was narrowed explicitly to a ghost
root-split bound/progress model, not full certificate validity; its native
compute-only literal passes. Full validity still has arbitrary-subject native
proofs and actual compiled tests. Initial outcomes are retained in predictions/
and prediction-value-final/; final correction in value-final-second.log.

The5341-prose-word chapter has5boxes,3diagrams and14actual captures. Five V
nonprediction sidecars include4scenario seals; D scenarios are contextual real
extension copies only. All reference prediction slots pass, final chapter and
reference lint pass, the course map/generated units/hook fixtures are current.
BankK2/K8 live controls and all four PP reference completions give intended native
outcomes. All5written documents compile. Initial frozen leak scan:28modules,
2109public files, OK; repeat after the source checkpoint's final edits. Six native
reference audits and final pins are still running; focused CI/STUDY workflow
await a clean STUDY source checkpoint. Nothing here is a live actor result.


## Final local construction result

R11 is locally complete, remains authoring/not shipped. Focused author CI run
20261017T151421Z-724805 on clean STUDY source d9ae1b1 passes6/6in1350s:
static677, R-D311, R-V249, paper40, rubric0, harness73seconds. CI used its
single default pool lane with no DVL_VERUS_JOBS override. Full release CI and
Basic shipment remain later work; R12–R16 are unfinished, R03 remains parked.

Final pins:32/32overR11,0problems. Six complete core/exit/agent reference audits
are clean. Initial audit invocation passed learner paths with --ref and was
correctly rejected; corrected reference paths pass. No tool bypass occurred.
Four core/exit references and two agent references pass their three seeds.
Canonical22/22admission includes the independently gated Vec fallback and four
checkpoint items; source counts D8/V10core,0check,2/2exit,1/1agent are pinned.
D/V full compiled references pass149/151tests; default learner holes stop before
compilation. Actual default rule bindings pass and deliberate wrong bindings
fail with the public independent consumer in both languages.

The clean-source scripted STUDY workflow passes all25commands,5prediction plus
2test-out receipts and4exit receipts. The checkpoint records4/4with required
threshold3/4and≥1perlanguage. Original snapshots precede agent proof delivery;
both default actual-source tools and all delivered gates/audits pass. The initial
driver wrongly expected26commands after25had passed and all11receipts had been
validated. Correct the orchestration count from retained evidence, without
rerunning successful native commands; retain the original assertion failure.
The successful stand-in clone was cleaned after saving receipts, snapshots and
final file hashes. These are author workflow checks, not actual closed-book
learner, calibrated grading or live contractor sessions.

Frozen STUDY source leak scan:28modules,2113public files,OK. Eight R11patterns
match their own reference sources and no public file; no new R answer enters a
provided layer. D45 live sessions and the S2 PointsTo arena remain recorded skips;
the Vec fallback proves only its stated index/frame properties. No quotas,
reserve releases, grades or provider retry is fabricated.

Final immutable evidence archive:
~/.cache/dafny-verus-learn-0/author-probes/dvr2/r11-final-20261017/
It retains construction scratch, public/private CI logs, available referenced
native raw trees, source hashes and PROVENANCE.json. Archive provenance records
the final metadata commit and any unavailable external raw paths explicitly.
