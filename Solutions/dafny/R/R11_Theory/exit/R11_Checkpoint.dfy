// Reference Solution.
/*! R11 — Theory: the closed-book checkpoint. Standalone A1–A4, fixed relative
certificate rules. Two tasks per language; attempt them with the book closed and
score them with scripts/firsttry.sh R11 --exit. Preserve models and domains.
*/
module R11_Checkpoint {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A4_Norm

  function CharacterLeavesR11(d: Derivation): nat
    decreases d
  {
    match d
    case DEps => 0
    case DChr => 1
    case DAltL(child) => CharacterLeavesR11(child)
    case DAltR(child) => CharacterLeavesR11(child)
    case DCat(_, left, right) => CharacterLeavesR11(left) + CharacterLeavesR11(right)
    case DStarNil => 0
    case DStarCons(_, left, right) => CharacterLeavesR11(left) + CharacterLeavesR11(right)
  }

  // item: R11.X1d
  // pair: R11.X1v
  /** **X1.** A certificate that checks has exactly one character leaf per
      scalar of its word. Prove it by induction on the derivation. */
  lemma {:induction false} CertificateLengthR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures |s| == CharacterLeavesR11(d)
    decreases d
  {
    // @hole-begin R11.X1d
    match d
    case DAltL(child) =>
      CertificateLengthR11(r.a, s, child);
    case DAltR(child) =>
      CertificateLengthR11(r.b, s, child);
    case DCat(k, left, right) =>
      CertificateLengthR11(r.a, s[..k], left);
      CertificateLengthR11(r.b, s[k..], right);
    case DStarCons(k, left, right) =>
      CertificateLengthR11(r.r, s[..k], left);
      CertificateLengthR11(r, s[k..], right);
    case _ =>
    // @hole-end R11.X1d
  }

  ghost function UniformWordR11(c: char, n: nat): seq<char>
  {
    seq(n, i => c)
  }

  lemma UniformStepR11(c: char, n: nat)
    requires n > 0
    ensures UniformWordR11(c, n)[..1] == [c]
    ensures UniformWordR11(c, n)[1..] == UniformWordR11(c, n - 1)
  {
    assert UniformWordR11(c, n)[..1] == [c];
    assert UniformWordR11(c, n)[1..] == UniformWordR11(c, n - 1);
  }

  // item: R11.X2d
  // pair: R11.X2v
  /** **X2.** Build, with a loop, a certificate of Star(Chr(c)) for the word of
      n copies of c. */
  method RepeatCertificateR11(c: char, n: nat) returns (out: Derivation)
    ensures CheckDeriv(Star(Chr(c)), UniformWordR11(c, n), out)
  {
    // @hole-begin R11.X2d
    var done := 0;
    out := DStarNil;
    while done < n
      invariant 0 <= done <= n
      invariant CheckDeriv(Star(Chr(c)), UniformWordR11(c, done), out)
      decreases n - done
    {
      UniformStepR11(c, done + 1);
      out := DStarCons(1, DChr, out);
      done := done + 1;
    }
    // @hole-end R11.X2d
  }

  // Given (not an item): the use-site check of X2, through its contract.
  method RepeatCertificateClientR11()
  {
    var out := RepeatCertificateR11('a', 2);
    assert UniformWordR11('a', 2) == ['a', 'a'];
    assert CheckDeriv(Star(Chr('a')), ['a', 'a'], out);
  }
}
