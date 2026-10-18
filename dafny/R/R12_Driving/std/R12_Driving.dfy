// item: R12.P3dv verdict
// Same source: selected good declaration then full target, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P3dv
// item: R12.P5dv verdict
// Synthetic fields-only then original-revision-bound consumer, D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P5dv
/*!
# R12 — Driving the verifier + Lab α (Exercises)

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
      The failing obligation is `Matches`'s Cat existential: which split of
      `u + v` is its witness, and how do you name it with slice facts only? */
  // Hint(1): site t1 is one boolean expression over u and v.
  // Hint(2): two slices of u + v, each equal to one of the words.
  lemma CatWitnessR12(a: Re, b: Re, u: seq<char>, v: seq<char>)
    requires Matches(a, u) && Matches(b, v)
    ensures Matches(Cat(a, b), u + v)
  {
    assume false;
    assert /*R12_HINT:t1*/ true;
  }

  // item: R12.H1d
  // pair: R12.H1v
  /** **H1.** `n` copies then `m` copies make `n + m` copies. The skeleton
      chooses the split `i` of `u`. Which call does the tail need (site h1a),
      and which equation turns the provided Cat witness into `u + v` (h1b)? */
  // Hint(1): h1a is one call of CopiesAppendR12 itself, on a smaller n.
  // Hint(2): h1b is an equation between sequences built from u[..i], u[i..] and v.
  lemma CopiesAppendR12(r: Re, n: nat, m: nat, u: seq<char>, v: seq<char>)
    requires Matches(Copies(r, n), u) && Matches(Copies(r, m), v)
    ensures Matches(Copies(r, n + m), u + v)
    decreases n
  {
    assume false;
    if n > 0 {
      var i :| 0 <= i <= |u| && Matches(r, u[..i]) && Matches(Copies(r, n - 1), u[i..]);
      /*R12_CALLS:h1a*/
      CatWitnessR12(r, Copies(r, n - 1 + m), u[..i], u[i..] + v);
      assert /*R12_HINT:h1b*/ true;
    } else {
      assert u == [] && u + v == v;
    }
  }

  // item: R12.H2d
  // pair: R12.H2v
  /** **H2.** A word of at most `j` copies is a word of at most `k >= j`
      copies. For a non-empty word, which branch of `CopiesUpTo(r, j)`'s `Alt`
      holds (site h2a), and which bounds does the induction call need (h2b)? */
  // Hint(1): h2a names a Matches fact about the Alt's second operand.
  // Hint(2): h2b lowers both bounds by one, on the tail chosen by the skeleton.
  lemma UpToMonoR12(r: Re, j: nat, k: nat, w: seq<char>)
    requires j <= k && Matches(CopiesUpTo(r, j), w)
    ensures Matches(CopiesUpTo(r, k), w)
    decreases j
  {
    assume false;
    if w != [] {
      assert j > 0;
      assert /*R12_HINT:h2a*/ true;
      var i :| 0 <= i <= |w| && Matches(r, w[..i]) && Matches(CopiesUpTo(r, j - 1), w[i..]);
      /*R12_CALLS:h2b*/
      CatWitnessR12(r, CopiesUpTo(r, k - 1), w[..i], w[i..]);
      assert w[..i] + w[i..] == w;
    }
  }
}
