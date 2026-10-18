// item: R12.P3dv verdict
// Same source: selected good declaration then full target, D:<x>,<y> V:<x>,<y>.
// CHECK P3dv
// item: R12.P5dv verdict
// Synthetic fields-only then original-revision-bound consumer, D:<x>,<y> V:<x>,<y>.
// CHECK P5dv
/*!
# R12 — Driving the verifier + Lab α (Reference Solution)

The native holes are hint-site forms, the same kind of object Lab α's engine fills
by search: each lemma ships its proof skeleton, and the learner writes only what
goes at its sites. An `expr` site replaces its `R12_HINT` marker and `true` with one
boolean expression over the identifiers its `R12_HINT_SITES` entry lists; a
`calls` site replaces its `R12_CALLS` marker with calls to the proof declarations
it lists. Everything else (statements, skeleton, imports) is frozen.

Imports: the given regex spine A1 (`RG_A1_Re`: `Re`, `Matches`) and A3
(`RG_A3_Syntax`: `Copies`, `CopiesUpTo`); no earlier exercise file.

How to work this file:
1. Predictions first: fill the two verdict slots above (slots/R12.slots), then
   record the first tries with `scripts/firsttry.sh R12 --check`.
2. For each item, delete its `assume false;` line and fill its sites.
3. Done = `scripts/vcheck --gate dafny/R/R12_Driving/std` prints only the summary
   line and exits 0, `scripts/vaudit dafny/R/R12_Driving/std` reports no finding,
   `scripts/specfreeze --check R12` reports none, AND
   `scripts/firsttry.sh R12 --report --strict` exits 0.

This file ships with exactly 3 holes: T1, H1 and H2.
*/
// R12_HINT_SITES: [{"name":"t1","identifiers":["u","v"]},{"name":"h1a","identifiers":["r","n","m","u","v","i"],"kind":"calls","callees":["CopiesAppendR12"]},{"name":"h1b","identifiers":["u","v","i"]},{"name":"h2a","identifiers":["Matches","Cat","CopiesUpTo","r","j","w"]},{"name":"h2b","identifiers":["r","j","k","w","i"],"kind":"calls","callees":["UpToMonoR12"]}]
module R12_HintSites {
  import opened RG_A1_Re
  import opened RG_A3_Syntax

  // item: R12.T1d
  // pair: R12.T1v
  /** **T1.** A word of `a` followed by a word of `b` matches `Cat(a, b)`.

      Reference: the Cat existential needs its witness `i = |u|` named as two
      slice facts about `u + v`; the rest is the two hypotheses. */
  lemma CatWitnessR12(a: Re, b: Re, u: seq<char>, v: seq<char>)
    requires Matches(a, u) && Matches(b, v)
    ensures Matches(Cat(a, b), u + v)
  {
    // did: the split of u + v at |u|, which instantiates the Cat existential.
    assert /*R12_HINT:t1*/ (u + v)[..|u|] == u && (u + v)[|u|..] == v;
  }

  // item: R12.H1d
  // pair: R12.H1v
  /** **H1.** `n` copies then `m` copies make `n + m` copies.

      Reference: induction on `n`. The skeleton picks the split `i` of `u` from
      `Copies(r, n)`'s Cat existential. Site h1a is the induction call on the
      tail; site h1b says that the head, the tail and `v` regroup as `u + v`. */
  lemma CopiesAppendR12(r: Re, n: nat, m: nat, u: seq<char>, v: seq<char>)
    requires Matches(Copies(r, n), u) && Matches(Copies(r, m), v)
    ensures Matches(Copies(r, n + m), u + v)
    decreases n
  {
    if n > 0 {
      var i :| 0 <= i <= |u| && Matches(r, u[..i]) && Matches(Copies(r, n - 1), u[i..]);
      /*R12_CALLS:h1a*/ CopiesAppendR12(r, n - 1, m, u[i..], v);
      CatWitnessR12(r, Copies(r, n - 1 + m), u[..i], u[i..] + v);
      // did: regroup the head, the tail and v as u + v.
      assert /*R12_HINT:h1b*/ u[..i] + (u[i..] + v) == u + v;
    } else {
      assert u == [] && u + v == v;
    }
  }

  // item: R12.H2d
  // pair: R12.H2v
  /** **H2.** A word of at most `j` copies is a word of at most `k >= j` copies.

      Reference: induction on `j`. The empty word is the `Eps` branch's at every
      bound. A non-empty word is the Cat branch's (site h2a), and the induction
      call lifts its tail from `j - 1` to `k - 1` (site h2b). */
  lemma UpToMonoR12(r: Re, j: nat, k: nat, w: seq<char>)
    requires j <= k && Matches(CopiesUpTo(r, j), w)
    ensures Matches(CopiesUpTo(r, k), w)
    decreases j
  {
    if w != [] {
      assert j > 0;
      // did: a non-empty word is the Alt's second branch.
      assert /*R12_HINT:h2a*/ Matches(Cat(r, CopiesUpTo(r, j - 1)), w);
      var i :| 0 <= i <= |w| && Matches(r, w[..i]) && Matches(CopiesUpTo(r, j - 1), w[i..]);
      /*R12_CALLS:h2b*/ UpToMonoR12(r, j - 1, k - 1, w[i..]);
      CatWitnessR12(r, CopiesUpTo(r, k - 1), w[..i], w[i..]);
      assert w[..i] + w[i..] == w;
    }
  }
}
