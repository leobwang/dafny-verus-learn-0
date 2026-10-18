# DVR4 R12 native rebuild — build notes (author only)

## DVR4 step 3: native holes as hint-site forms (plan §2.4), 2026-10-18

Objective-to-hole table (written before the code). The plan's objective for R12's native
part: the learner fills by hand what Lab α's engine fills by search, reading each site's
content off the failing obligation.

| objective | item | sites | why not trivial |
|---|---|---|---|
| name an existential's witness from the obligation | T1d/T1v `CatWitnessR12` / `lemma_cat_witness_r12` | t1 (expr): the split of `u + v` at `|u|` | site `true` fails at the Cat existential (both languages); a length fact fails too |
| two dependent sites in an induction skeleton | H1d/H1v `CopiesAppendR12` / `lemma_copies_append_r12` (A3 `Copies`) | h1a (calls): the induction call on the tail; h1b (expr): the regrouping of head, tail and `v` | each site empty fails; a call on the whole word fails (3 errors in Dafny) |
| read the branch the obligation reports | H2d/H2v `UpToMonoR12` / `lemma_up_to_mono_r12` (A3 `CopiesUpTo`) | h2a (expr): the `Alt`'s Cat branch for a non-empty word; h2b (calls): the call with `j - 1, k - 1` on the tail | each site empty fails; a call on the whole word fails |

Minutes unchanged (T1 5, H1 10, H2 10 per language). The old flags items (`RemainingBudgetR12`,
`CountAcceptedR12`, `FirstRejectionR12`, the worked `AcceptedCountR12` / `AcceptedStepR12`)
are retired; the predictions P1–P5, the specimens, the Python holes and the Lab α sections
are unchanged.

Probe findings:
- Plan H1's two sites as written (the head/tail split, then the call) left the split
  fact unnecessary: Dafny proves the sequence identity itself. The sites became the call
  and the regrouping equation, both necessary in both languages.
- H1's `n = 0` branch needs `u == [] && u + v == v` (provided skeleton); H2's
  non-empty branch needs `j > 0` (provided) and, in Verus, `!matches(Re::Eps, w)` and the
  `j == 0` unfolding (provided), because Verus's default fuel does not open the inner
  `matches`.
- `tools/R12/admit_forms.py` (static) accepts the shipped forms with the counted holes
  in place; it checks forms (each site once), not completed files.
- `tools/R12/check_clients.py` (the Lab α lane's tool) compiles the retired flags
  methods; it no longer applies to R12's native items (reported to the coordinator).

## Admission (the four results)

| item | ref seeds 1-3 | empty body (shipped) | maximal automation | TRIV |
|---|---|---|---|---|
| T1d / T1v | verified ×3 / ×3 | fails | fails | n/a (lemma) |
| H1d / H1v | verified ×3 / ×3 | fails | fails | n/a |
| H2d / H2v | verified ×3 / ×3 | fails | fails | n/a |

Source: `scripts/vcheck --ref --brittleness` on both twins; `scripts/firsttry.sh R12 --empty-body`
11/11 (the six native items and the five Python TRIV controls). Site necessity: each site
emptied (or the call given the whole word) fails, probed per site in both languages.
