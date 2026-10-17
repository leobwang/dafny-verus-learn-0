# Tools fixtures (tests/wrappers/test_tools_*.py)

Fixtures for the DV1b tools (`scripts/vcheck`, `scripts/vaudit`, `scripts/specfreeze`,
`scripts/firsttry.py`, `scripts/pins.py`, `scripts/reference_lint.py`). Every file here
is an invented toy program written for these tests: none is course content, an exercise,
an answer, or text from the reference tree.

- `overlay/` is copied over the synthetic armed Q04 (`tests/course_map/armed/tree/`) by
  `test_tools_common.build_root()`, which also adds two files to Q04's record
  (`dafny/checks/Q04_checks.dfy`, `verus/q/q04_proof_craft/src/tests.rs`). It adds one
  slot of every format in both languages: obligation and error specimens
  (`specimens/Q04/P4d`, `P5d`, `P6v`, `P7v`), a card with an author `EXPECT` pin (`C2d`),
  value slots in a given-only Dafny check unit (`P8d`, `P9d`), a Verus `#[test]` (`P10v`)
  and a Verus `by (compute_only)` assert (`P11v`), and verdict slots (`P1dv`, `P2dv`).
  It also adds hole items with a real hole (`H3d`, `H3v`: an induction the empty body
  cannot close) beside trivial ones (`H1d`, `H1v`), and hollow exit files (`X1d`, `X2d`,
  `X1v`, `X2v`).
- `reference/` holds invented hole-free twins of those files for the reference lint,
  `pins.py --ref` and `vcheck --ref --pin-counts` (copied to `<root>/Solutions/` of a
  throwaway root, never into this checkout's reference tree): the same markers, names and
  statements, every slot enabled, one twin-only test and one `// did:` receipt, plus twins
  of the armed tree's two agent files, each with one `reference-only` declaration so that
  its reference gate counts a task (scripts/ci.sh gates exit, check and agent twins in an
  author run). No count pin
  (`expected/Q04.counts`) is a fixture: the tool tests write it from these twins with
  `vcheck --ref --pin-counts Q04` and assert on what that run prints.

The expectations in the tests (failing labels, diagnostic lines, verdicts, counts) were
observed on real runs of the pinned Dafny 4.11.0 and Verus 0.2026.09.27.3cf1832.
