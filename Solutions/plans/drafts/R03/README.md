# R03 parked draft — not a release module

Blocker: native prototypes verify, but the scalar-neighbour implementation
uses vstd UTF-8/string infrastructure before OD8 permits those imports.
Direct and A1-transitive packaging both fail the existing tier gate. No
exception is adopted. R03 remains planned; no module CI or completion is claimed.

This directory preserves original relative paths, a provisional registry,
plan/delta checkpoint and kit files. Do not copy the checkpoint registry over
a newer tree: reconcile only R03 after resolving the primitive placement.
Native prototypes/evidence stay in the guarded R03 author-probe archive.

Known unfinished kit checks: chapter skeleton headings/separators/table;
remove after markers from main files (valid only in specimens); canonical
counts/freeze/prediction/chapter pins; leak patterns; admission; seed stability;
study workflow; focused CI; align A2 re-supply. The paper/gold/flawed fixtures
are drafted but not yet compiled. Paper/rubric pins predate later adapter edits.

The draft's A1 adapter layout is a rejected attempt, not adopted public code.
Keep the existing public A1 unchanged. The original inline reference that
passed native gate/audit is preserved in /tmp/dvl0-dvr1-r03/agent-v-reference.rs.

## D48 step 2 (2026-10-17): API core references rebuilt on u32

The two API core references are rebuilt on u32 code-point ranges (DVR4 plan
§1.2–1.3, DELTAS Δ274):

- `Solutions/dafny/R/R03_Modules/core/R03_Modules.dfy`: `newtype Cp`,
  `CRange(lo: Cp, hi: Cp)`, `Code(c)`, separated validity (`hi + 1 < lo'`),
  merge of overlapping and adjacent ranges; the export adds `reveals Cp, Code`.
- `Solutions/verus/r/r03_modules/src/lib.rs`: private `Vec<(u32, u32)>`,
  `class_insert(lo: u32, hi: u32)`, `separated`; `class_range` and
  `class_of_string` compare codes. One statement per line throughout.

Both gate at zero holes and audit clean in scratch units (A1 only for Dafny,
`rg_re_a1` for Verus); evidence in
`~/.cache/dafny-verus-learn-0/author-probes/dvr4-step2/`. A2 re-supplies this
API with a read-only range accessor. Everything else in this directory (learner
files, agent files with `CharPrev`/`CharNext`, `char_scalar.rs`, specimens,
chapter, bank, paper) is still the char-based draft and is rebuilt in plan
step 8; the UTF-8 adapter is no longer needed by the core.
