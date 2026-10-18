// Reference Solution.
// item: R13.P3dv verdict
// Predict exact proof verdict/stage in each language.
// CHECK P3dv
// item: R13.P6dv verdict
// Selected then full scope, exact D/V verdict and stage pairs.
// CHECK P6dv
/*!
# R13 — Pipelines and trust (Reference Solution)

Imports: the given regex spine A1–A4 (`RG_A1_Re`, `RG_A1b_Facts`, `RG_A2_Deriv`, …);
nothing else: no earlier exercise file.

Each item below comes with a fake delivery, shown and run in the chapter (§8): a
version of the same task that some instrument reports as fine (a learner-loop
summary, a gate that does not read statements) while it is not. For each item:
1. Run the fake delivery's instruments, name the stage or the instrument that
   exposes it, and write that attribution in `research/r13_forensics.md`.
2. Then replace the hole with the honest proof. The statement stays as shipped.

Done = `scripts/vcheck --gate dafny/R/R13_Pipelines/std` prints only the summary
line and exits 0, `scripts/vaudit dafny/R/R13_Pipelines/std` reports no finding,
`scripts/specfreeze --check R13` reports none, AND
`scripts/firsttry.sh R13 --report --strict` exits 0.

This file ships with exactly 4 holes: T1 (closed-book test-out) and H1–H3.
*/
module R13_Repairs {
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv
  // specfreeze: frozen-imports

  // Given: the derivative by every character of u, in order.
  function Derivs(r: Re, u: seq<char>): Re
    decreases |u|
  {
    if u == [] then r else Derivs(A2.Deriv(r, u[0]), u[1..])
  }

  // item: R13.T1d
  // pair: R13.T1v
  /** **T1.** (closed book) An executable matcher with the regex semantics as its
      contract.

      Reference: a compiled method cannot call the ghost `Matches`; A2's
      `DerivMatch` is the compiled matcher with exactly this postcondition. */
  method AcceptsR13(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
  {
    b := A2.DerivMatch(r, s);
  }

  // item: R13.H1d
  // pair: R13.H1v
  /** **H1.** Taking derivatives by `u + v` is taking them by `u`, then by `v`.

      Reference: induction on `|u|`. For `u == []`, `[] + v == v`. Otherwise the
      first character of `u + v` is `u[0]` and the rest is `u[1..] + v`; with
      those two facts stated, `Derivs` unfolds once on each side and the
      induction hypothesis at `(Deriv(r, u[0]), u[1..], v)` closes it. */
  lemma {:induction false} DerivsCatR13(r: Re, u: seq<char>, v: seq<char>)
    ensures Derivs(r, u + v) == Derivs(Derivs(r, u), v)
    decreases |u|
  {
    if u == [] {
      assert u + v == v;
    } else {
      assert (u + v)[0] == u[0];
      assert (u + v)[1..] == u[1..] + v;
      DerivsCatR13(A2.Deriv(r, u[0]), u[1..], v);
    }
  }

  // item: R13.H2d
  // pair: R13.H2v
  /** **H2.** Every character of `s` lies in the class `cc`: a verified loop over
      A2's class API.

      Reference: the invariant is the `forall` over the prefix read so far; a
      character outside the class ends the loop with `false`, and its index is
      the witness that the postcondition's `forall` fails. */
  method ClassCoversR13(cc: A2.CharClass, s: seq<char>) returns (b: bool)
    ensures b == (forall i | 0 <= i < |s| :: A2.InClass(cc, s[i]))
  {
    var k := 0;
    while k < |s|
      invariant 0 <= k <= |s|
      invariant forall i | 0 <= i < k :: A2.InClass(cc, s[i])
    {
      if !A2.ClassMember(cc, s[k]) {
        return false;
      }
      k := k + 1;
    }
    return true;
  }

  // item: R13.H3d
  // pair: R13.H3v
  /** **H3.** A word matches exactly when its derivatives end in a nullable regex.

      Reference: induction on `|u|`. For `u == []` it is NullableCorrect. Otherwise
      the induction hypothesis at `(Deriv(r, u[0]), u[1..])` and DerivCorrect at
      `(r, u[0], u[1..])` chain, once `[u[0]] + u[1..] == u` is stated. */
  lemma {:induction false} NullableDerivsR13(r: Re, u: seq<char>)
    ensures Nullable(Derivs(r, u)) <==> Matches(r, u)
    decreases |u|
  {
    if u == [] {
      B.NullableCorrect(r);
    } else {
      NullableDerivsR13(A2.Deriv(r, u[0]), u[1..]);
      A2.DerivCorrect(r, u[0], u[1..]);
      assert [u[0]] + u[1..] == u;
    }
  }
}
