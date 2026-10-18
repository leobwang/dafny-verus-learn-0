# Lab alpha public slice: the pre-registered walk (DVR4 plan section 3.5)

Written 2026-10-18 by corpus lane L4, before any member was taken. Author-side.

## Population and order

- Sets: `dafnybench` (Dafny, commit 0cd28fe, set sha256 0c1a4218c81f2dfd..., pool sha256
  18cefeb571ec51b4...) and `humaneval-verus` (Verus, commit bbe93f7, set sha256
  89d53507eab46676..., pool sha256 efbaf9020c11f2af...), as installed and checked by
  `scripts/get_bench.sh --check`.
- Members: `scripts/get_bench.sh --members SET --lab R12` (the pinned pool less other labs'
  draws): 303 dafnybench, 78 humaneval-verus. `vericoding` is not walked (its Dafny HumanEval
  rows were Q15's stratum; jetbrains/verified_cogen rows have no licence).
- Seed `R12-labalpha-public-20261018`. Per set: the sorted members shuffled by
  `random.Random(seed + ":" + set)`. The walk interleaves the two orders, dafnybench first
  (db[0], hev[0], db[1], hev[1], ...), and continues with the longer order when the shorter
  ends. The resulting order is ORDER.json (sha256
  dd0c91c3e3af1647b8abe2d7df71b51d3b1ad64a63719e1bda90d81c16d47482).
- Stop: 45 admitted clusters, or 160 members walked, whichever comes first.

## The checks, in order (the first failing one is recorded; the member is skipped: redraw rule)

- C0 licence: recorded MIT or Apache-2.0 provenance. humaneval-verus: MIT (the set) and the
  HumanEval prompts MIT. dafnybench: the set's recorded Apache-2.0; its programs were collected
  from earlier public repositories whose per-file licences the manifest records as "not
  recorded". The walk accepts dafnybench on the set licence and FLAGS each such member
  (`c0_flag: per-file upstream licence not recorded`) for the lane's owner to rule on.
- C1 form: one task. The upstream verified answer materializes into a hint-site form: inside
  one target declaration, every removed proof annotation becomes a site (a Dafny `invariant`
  or `assert` line of the dafnybench task-form diff; a Verus `invariant` clause or a plain
  `assert(..);` of the target exec fn), the marker on one line; every other byte is the
  answer's. Annotations outside the target, call statements in exec code, `decreases`, and
  annotations the frozen hint grammar cannot express (quotes, braces, `#`, `=~=`, triggers in
  Dafny braces, `by` blocks) stay in the skeleton as provided text; a Verus `#[trigger]` inside
  a removed clause is dropped from the reference hint (recorded). The form must keep at least
  one site. Site vocabulary: the identifiers of the target declaration's text and of the
  reference hints, plus the file's function and predicate names (never only the hint's own
  words). Prefer lemma-shaped tasks: recorded as a flag (lemma target, or sequence/string/
  recursion obligations), not a filter.
- C2 prose: humaneval-verus: the file's HumanEval prompt (its PROMPT/docstring block) exists;
  dafnybench: not applicable (recorded n/a).
- C3 distinct: no HumanEval problem shared across languages or with any earlier draw: the
  `he<N>` cards of every `[[draw]]` in bench/public/POOLS.toml (Q15), R12's prior reservation
  (bench/local/r/labalpha-smoke/UNUSED_PUBLIC.json: its excluded ids and its 10 selected
  tasks), and earlier accepted members of this walk (`human_eval_NNN[ab]` and dafnybench's
  `llm-verified-eval_..._dafny_N` read as HumanEval/N); a dafnybench file is distinct by name
  and by answer sha256.
- C4 resolves: the form reaches the verify stage (the admission tool's baseline run).
- C5 stable: the reference verifies under seeds 1, 2, 3 (tool: reference-three-seeds).
- C6 gate: the reference passes the lab gate as a delivery of its form (tool: reference-gate,
  `vcheck --gate --lab-task FORM`).
- C7 faithful: statement-preserving materialization, checked statically by the tool's frame
  control (statement table, models and executable skeleton equal between form and
  reference). No Claude judging runs (D45).
- Then the tool's remaining controls: baseline-proof-fails, audit-clean, max-auto-empty-fails,
  wrong-hints-fail (tools/R12/admit_forms.py --admit; all seven must pass).
- A solver job killed by memory (137/143) or the net is re-run once; a second stop skips the
  member as `retry`.

## Contamination

Every public task is treated as possibly seen in training (2023-2025 public repositories);
the by-source stratum (regex vs public) is reported. Static checks: C3's distinctness and
prior-draw exclusions.

Deferred (design note only; no model call may touch a non-pilot cluster): the perturbation
probe per public cluster. Protocol: an alpha-renamed variant (every identifier the file
declares renamed by a fixed seeded map, `R12-labalpha-perturb-20261018`) and a
statement-preserving reordering of independent top-level declarations; the variant is
re-admitted by the same seven controls; the probe compares the model's baseline success on the
original and the variant (same seeds, same B); a cluster whose success changes beyond the
pre-registered tolerance (any change of solved-at-call-1 or never-solved status in a majority
of repeats) is kept but flagged. It runs only where model calls are allowed (pilot clusters,
or the confirmatory run as a descriptive line).

## Records

C0-C7.jsonl (one line per walked member: set, task, result, the first failing check and its
reason, flags), families/pub-*.json per admitted cluster, the forms and ADMISSION.json under
bench/local/r/labalpha/<task>/, hint data and evidence under lab-corpus-v2/<task>/.

## Amendment 1 (2026-10-18, before any selection; the order and the checks are unchanged)

Original text sha256 531ee015c1c92c19bee3194c6562cd1014c4cb42386a314af1990845fe2d34c3 (the
text above this section). C1's rule "a Verus `#[trigger]` inside a removed clause is dropped
from the reference hint" is replaced by: a Verus clause or assert holding `#[trigger]` (or any
`#` attribute) stays in the skeleton as provided text, like every other annotation the hint
grammar cannot express. Reason: the first admission run showed that a trigger-stripped
reference can fail to resolve (human_eval_001: "Could not automatically infer triggers"), so
the dropped-trigger reference is not the upstream proof. Admission results produced under the
original rule were discarded and the materialization was re-run before selection.

## Amendment 2 (2026-10-18, before any member after position 59 was taken)

Text before this section: sha256 1d4b3b5e7df488fc6f8d3bf9e9569b743cebdb35e4626341f663b88295ea5e4e. Requested by the Lab alpha lane (the coordinator
prefers lemma-shaped tasks; two admitted clusters, pub-db-052 and pub-hev-023, now have the
pilot role and do not count toward the public slice's target).

- Stop rule, replacing "45 admitted or 160 walked": 70 admitted clusters not counting the two
  pilot clusters (72 admitted in all), or 220 members walked, whichever comes first.
- Order for walk positions 60 and later (positions 0-59 and their results are unchanged): the
  members not yet walked keep their per-set seeded order from ORDER.json and are stably
  partitioned, lemma-shaped first, then the rest. "Lemma-shaped" is materialize.py's static
  `lemma_shaped` flag (Dafny: the target is a lemma, or its text holds `seq<`, `string` or
  `decreases`; Verus: the target's text holds `Seq<`, `seq`, `String`, `str` or
  `decreases`); a member that does not materialize counts as not lemma-shaped. The two
  partitioned orders are interleaved dafnybench first, as before. order2.py (sha256
  cdf22892a4f870ec5a5a1131ccd7a44eee98884882f559dece4f272ff9844b0a) writes the result,
  ORDER2.json (sha256 58cfb31a4ac13f1b051905bac0fbd163ca37500287cfd05090a67200bd174177):
  137 of 273 remaining dafnybench and 27 of 48 remaining humaneval-verus members are
  lemma-shaped. The flags were computed by the static materialization only (no solver run),
  before any new member was taken.
- Exclusion recorded: vericoding's answer DD0070 stays out of the walk (a known calibration
  overlap with R06's core file). vericoding is not walked by this rule in any case.
- Solver slots: the pilot holds one of the two Verus slots, so the walk's Verus jobs run one
  at a time.
