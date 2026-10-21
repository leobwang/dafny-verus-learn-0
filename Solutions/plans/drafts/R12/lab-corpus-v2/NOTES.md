# Lab α corpus notes (author-only)

## Declared later-tier overlap: the a1b-* forms (2026-10-19; DELTAS Δ294)

The twelve a1b-* task forms restate layer A1b's facts (NullableCorrect, CatEpsLeft, CatEpsRight,
CatAssoc, StarOne, StarConcat) over A1's definitions. Their fixed skeletons keep the reference
proofs' structure, which shows parts of the answers to R02's holes (H1's case split of
NullableCorrect, H4v's `choose` skeleton of CatEpsLeft) and to R05's band-1 facts, as A1b itself
does. The coordinator's decision (option (a)): declare them a later-tier overlap with A1b's
standing. Every a1b-* form now begins with A1b's "do not open before R02 and R05 are done"
header (five comment lines, so their R12_SOURCE_SPANS moved by five lines); all twelve were
re-admitted from scratch under the seven controls (the earlier evidence is kept as
`<task>/evidence-v1-before-header/` and `<task>/ADMISSION-v1-before-header.json`), and the
stratum and the freeze re-bind the new hashes through the stratum amendment
`A1B_HEADER_AMENDMENT.json` (old and new source sha256 per task). The overlap is recorded beside
D23's in `tests/instructor/leak_patterns/README.md`. Two of these clusters are pilot clusters
(a1b-cat-assoc, a1b-nullable-correct): the pilot and the re-pilot ran on the forms' earlier bytes
(their runs record those inputs); the header changes no statement, site or skeleton.

## Extended to the whole learner-visible corpus (2026-10-19; Δ294)

The leak verifier showed the same reading across the corpus: forms that include A1b's facts
as complete helpers (r08-alt-feed/final, r09-copies-split, r09-rep-range, r10-mk-cat,
r11-residual-step/observe) and forms whose statement is an earlier hole's answer
(r06-star-unfold's precondition is R06.H4's repair). The coordinator chose option (a): every
learner-visible regex form now begins with three `// [R12 header]` lines ("DO NOT OPEN
BEFORE R11 IS DONE"), replacing the a1b forms' five-line A1b header; all 66 were re-admitted
from scratch (D55 tasks with `--shipped-induction`); `HEADER_AMENDMENT.json` records each
task's source sha256 before and after and the sha256 of the source as a request carries it
(`fvh.labalpha.strip_header` turns the header lines into bare `//` lines, so the model never
sees the notice and line numbers stay aligned with the verifier's diagnostics). The pilot and
the re-pilot ran on the forms without any header (their runs' inputs.sha256 record those
bytes, the "before" hashes here).
