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
