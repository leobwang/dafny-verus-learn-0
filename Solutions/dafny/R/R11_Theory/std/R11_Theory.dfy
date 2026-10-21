// Reference Solution.
/*!
# R11 — Theory (exercises)

Standalone R track. Import only the frozen layers A1 to A4; no earlier learner
file is needed. The paired exercise is verus/r/r11_theory/src/lib.rs; the
closed-book checkpoint is dafny/R/R11_Theory/exit/R11_Checkpoint.dfy.

Before reading the chapter, attempt T1 closed book (the first module below).
Fill the five predictions in slots/R11.slots (switched on by the two CHECK
lines of the prediction block), specimens/R11/P2v.rs.specimen,
specimens/R11/P4v.rs.specimen and dafny/checks/R11_checks.dfy, and record the
first attempts with scripts/firsttry.sh R11 --check before running their
scenarios. Eight typed holes ship in this language.

File order: the test-out (T1), the prediction block, the certificate kernel
(W2 the erased evidence, then H1 the checker, H2 soundness, H3 direct
completeness), the streaming matcher (W1 and W3 the residual facts, then H4),
and complete search (H5 with its two loops H6 and H7). A certificate is
ordinary data; its meaning is A4's CheckDeriv, and splits are relative to the
word the node owns.

Done: the unit gates with zero tool-counted holes, vaudit is clean,
specfreeze --check R11 passes and firsttry's strict report is OK. Preserve the
given contracts and implementations. /tutor R11 is available after an attempt.
*/

// =============================================================================
// Test-out (closed book)
// =============================================================================

module R11_WpReview {
  // specfreeze: frozen-imports

  // item: R11.T1d
  // pair: R11.T1v
  /** **T1.** Closed book: the one-step index update of a scanning loop. Which
      precondition makes both postconditions hold, and what is wp(next := i + 1,
      next == i + 1 && next <= len)? */
  method WpIndexStepR11(i: nat, len: nat) returns (next: nat)
    requires i < len
    ensures next == i + 1 && next <= len
  {
    // @hole-begin R11.T1d
    next := i + 1;
    // @hole-end R11.T1d
  }
  // Hint(1): substitute i + 1 for next in the postcondition; what is left must follow from i < len.
  // Hint(2): the assignment is the whole body.
  // Reference checks (enabled):
  // reference-only: enabled shipped check
  method WpIndexStepCheck()
  {
    var next := WpIndexStepR11(3, 4);
    assert next == 4;
  }
  // end reference checks
}

// =============================================================================
// Prediction block: do not run the scenarios until these slots are recorded
// =============================================================================

// item: R11.P3dv verdict
/** changed-rule checks a Star certificate under a rule that checks only its
    first chunk; original-rule checks the same tree and word under A4's rule.
    Predict both verdicts in each language.
    Answer form: D:<x>,<y> V:<x>,<y>, each ok, fail, timeout or err:<stage>. */
// CHECK P3dv
// item: R11.P5dv verdict
/** weak-producer promises only that a present certificate is valid;
    complete-producer also promises that absence means no match. Both return
    no certificate. Predict both verdicts in each language. Same form as P3dv. */
// CHECK P5dv

// =============================================================================
// The certificate kernel
// =============================================================================

module R11_Kernel {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A4_Norm

  // item: R11.W2d
  /** Erased evidence: a record of ghost fields that packs a regex, a word and
      a derivation together with the fact that the derivation checks. Packing
      needs the fact; using it is free. */
  datatype EvidenceR11 = EvidenceR11(ghost expression: RG_A1_Re.Re, ghost word: seq<char>, ghost tree: RG_A4_Norm.Derivation)

  ghost function PackEvidenceR11(r: RG_A1_Re.Re, s: seq<char>, d: RG_A4_Norm.Derivation): (out: EvidenceR11)
    requires RG_A4_Norm.CheckDeriv(r, s, d)
    ensures RG_A4_Norm.CheckDeriv(out.expression, out.word, out.tree)
  {
    EvidenceR11(r, s, d)
  }

  // item: R11.H1d
  // pair: R11.H1v
  /** **H1.** The executable checker: return exactly CheckDeriv(r, s, d) by
      recursion on the derivation. Which constructor checks does each rule need
      before its children are checked, and which split bound must be tested
      before a slice is taken? */
  method CheckCertificateR11(r: Re, s: seq<char>, d: Derivation) returns (ok: bool)
    ensures ok == CheckDeriv(r, s, d)
    decreases d
  {
    // @hole-begin R11.H1d
    match d
    case DEps =>
      ok := r == Eps && s == [];
    case DChr =>
      ok := r.Chr? && s == [r.c];
    case DAltL(child) =>
      if !r.Alt? {
        return false;
      }
      ok := CheckCertificateR11(r.a, s, child);
    case DAltR(child) =>
      if !r.Alt? {
        return false;
      }
      ok := CheckCertificateR11(r.b, s, child);
    case DCat(k, left, right) =>
      if !r.Cat? || k > |s| {
        return false;
      }
      var a := CheckCertificateR11(r.a, s[..k], left);
      var b := false;
      if a {
        b := CheckCertificateR11(r.b, s[k..], right);
      }
      ok := a && b;
    case DStarNil =>
      ok := r.Star? && s == [];
    case DStarCons(k, left, right) =>
      if !r.Star? || k == 0 || k > |s| {
        return false;
      }
      var a := CheckCertificateR11(r.r, s[..k], left);
      var b := false;
      if a {
        b := CheckCertificateR11(r, s[k..], right);
      }
      ok := a && b;
    // @hole-end R11.H1d
  }
  // Hint(1): one case per Derivation constructor, read off A4's CheckDeriv clause by clause.
  // Hint(2): CheckDeriv's DCat and DStarCons clauses state k <= |s| (and 0 < k) before s[..k] means anything.

  // item: R11.H2d
  // pair: R11.H2v
  /** **H2.** Soundness: a derivation that checks proves the match. Prove it by
      induction on the derivation (the lever {:induction false} is shipped).
      Which rules have children, and which slices of s are the children's words? */
  lemma {:induction false} CheckSoundR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  {
    // @hole-begin R11.H2d
    match d
    case DEps =>
    case DChr =>
    case DAltL(d1) =>
      CheckSoundR11(r.a, s, d1);
    case DAltR(d1) =>
      CheckSoundR11(r.b, s, d1);
    case DCat(k, d1, d2) =>
      CheckSoundR11(r.a, s[..k], d1);
      CheckSoundR11(r.b, s[k..], d2);
    case DStarNil =>
    case DStarCons(k, d1, d2) =>
      CheckSoundR11(r.r, s[..k], d1);
      CheckSoundR11(r, s[k..], d2);
    // @hole-end R11.H2d
  }
  // Hint(1): the leaves follow from CheckDeriv and Matches alone; each child is the hypothesis on its own slice.
  // Hint(2): the split k in a DCat or DStarCons node is the witness Matches' existential needs.

  // item: R11.H3d
  // pair: R11.H3v
  /** **H3.** Direct completeness: from a match, build a derivation that checks.
      The lemma returns the tree it builds. Which split does Matches' Cat and Star
      case give you, and how do you take it out of the existential? */
  lemma {:induction false} DirectCompleteR11(r: Re, s: seq<char>) returns (d: Derivation)
    requires Matches(r, s)
    ensures CheckDeriv(r, s, d)
    decreases r, |s|
  {
    // @hole-begin R11.H3d
    match r
    case Eps =>
      d := DEps;
    case Chr(_) =>
      d := DChr;
    case Alt(a, b) =>
      if Matches(a, s) {
        var d1 := DirectCompleteR11(a, s);
        d := DAltL(d1);
      } else {
        var d1 := DirectCompleteR11(b, s);
        d := DAltR(d1);
      }
    case Cat(a, b) =>
      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(b, s[k..]);
      var d1 := DirectCompleteR11(a, s[..k]);
      var d2 := DirectCompleteR11(b, s[k..]);
      d := DCat(k, d1, d2);
    case Star(a) =>
      if s == [] {
        d := DStarNil;
      } else {
        var k :| 0 < k <= |s| && Matches(a, s[..k]) && Matches(Star(a), s[k..]);
        var d1 := DirectCompleteR11(a, s[..k]);
        var d2 := DirectCompleteR11(r, s[k..]);
        d := DStarCons(k, d1, d2);
      }
    // @hole-end R11.H3d
  }
  // Hint(1): the measure is (r, |s|): a child regex, or the same Star on a strictly shorter suffix.
  // Hint(2): `var k :| …` takes the split out of Matches' existential; Empty has no case (it never matches).
}

// =============================================================================
// The streaming matcher
// =============================================================================

module R11_Streaming {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  import opened RG_A2_Deriv

  // The loop's relation: after reading prefix, current matches exactly the
  // tails that complete prefix to a word of r. Opaque: revealed where it is used.
  opaque ghost predicate ResidualR11(r: Re, current: Re, prefix: seq<char>)
  {
    forall tail: seq<char> :: Matches(current, tail) <==> Matches(r, prefix + tail)
  }

  // item: R11.W1d
  /** The relation holds before the loop: nothing read, current is r. */
  lemma ResidualStartR11(r: Re)
    ensures ResidualR11(r, r, [])
  {
    // did: unfold the fixed model for this constructor obligation.
    reveal ResidualR11();
    forall tail: seq<char>
      ensures Matches(r, tail) <==> Matches(r, [] + tail)
    {
      assert [] + tail == tail;
    }
  }

  // item: R11.W3d
  /** The relation is kept by one derivative step (A2's DerivCorrect). */
  lemma ResidualStepR11(r: Re, current: Re, prefix: seq<char>, c: char)
    requires ResidualR11(r, current, prefix)
    ensures ResidualR11(r, Deriv(current, c), prefix + [c])
  {
    // did: unfold the fixed model for this constructor obligation.
    reveal ResidualR11();
    forall tail: seq<char>
      ensures Matches(Deriv(current, c), tail) <==> Matches(r, (prefix + [c]) + tail)
    {
      DerivCorrect(current, c, tail);
      assert prefix + ([c] + tail) == (prefix + [c]) + tail;
    }
  }

  // The relation gives the observation: current is nullable exactly when the prefix matches.
  lemma ResidualObserveR11(r: Re, current: Re, prefix: seq<char>)
    requires ResidualR11(r, current, prefix)
    ensures Nullable(current) == Matches(r, prefix)
  {
    reveal ResidualR11();
    NullableCorrect(current);
    assert prefix + [] == prefix;
  }

  // item: R11.H4d
  // pair: R11.H4v
  /** **H4.** The streaming matcher: read s left to right with derivatives,
      record for every nonempty prefix whether it matches, and return whether s
      does. What must the loop invariant say about current, about trace, and
      about the prefix read so far, and which W lemma keeps each part? */
  method PrefixMatchesR11(r: Re, s: seq<char>) returns (accepted: bool, trace: seq<bool>)
    ensures accepted == Matches(r, s)
    ensures |trace| == |s|
    ensures forall j | 0 <= j < |s| :: trace[j] == Matches(r, s[..j + 1])
  {
    // @hole-begin R11.H4d
    var current := r;
    var i := 0;
    trace := [];
    assert s[..0] == [];
    ResidualStartR11(r);
    while i < |s|
      invariant 0 <= i <= |s| && |trace| == i
      invariant ResidualR11(r, current, s[..i])
      invariant forall j | 0 <= j < i :: trace[j] == Matches(r, s[..j + 1])
      decreases |s| - i
    {
      var c := s[i];
      ResidualStepR11(r, current, s[..i], c);
      assert s[..i] + [c] == s[..i + 1];
      current := Deriv(current, c);
      i := i + 1;
      ResidualObserveR11(r, current, s[..i]);
      var bit := Nullable(current);
      trace := trace + [bit];
    }
    ResidualObserveR11(r, current, s[..i]);
    assert s[..i] == s;
    accepted := Nullable(current);
    // @hole-end R11.H4d
  }
  // Hint(1): the invariant has three parts: bounds and |trace| == i, the residual relation on s[..i], and the trace facts.
  // Hint(2): ResidualStartR11 before the loop, ResidualStepR11 and ResidualObserveR11 in the body; s[..i] + [c] == s[..i + 1].
}

// =============================================================================
// Complete search
// =============================================================================

module R11_Search {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A4_Norm

  datatype CertChoiceR11 = NoCertR11 | HasCertR11(value: Derivation)

  // item: R11.H5d
  // pair: R11.H5v
  /** **H5.** Complete search: return a certificate that checks, or none
      only when r does not match s. Recurse on the structure; Cat and Star hand
      their split search to H6 and H7. Which clause rules out a search that
      always answers none? */
  method SearchR11(r: Re, s: seq<char>) returns (out: CertChoiceR11)
    ensures out.HasCertR11? ==> CheckDeriv(r, s, out.value)
    ensures out.NoCertR11? ==> !Matches(r, s)
    decreases r, |s|
  {
    // @hole-begin R11.H5d
    match r
    case Empty =>
      return NoCertR11;
    case Eps =>
      return if s == [] then HasCertR11(DEps) else NoCertR11;
    case Chr(c) =>
      return if s == [c] then HasCertR11(DChr) else NoCertR11;
    case Alt(a, b) =>
      var left := SearchR11(a, s);
      if left.HasCertR11? {
        return HasCertR11(DAltL(left.value));
      }
      var right := SearchR11(b, s);
      return if right.HasCertR11? then HasCertR11(DAltR(right.value)) else NoCertR11;
    case Cat(a, b) =>
      out := SearchCatR11(a, b, s, 0);
    case Star(a) =>
      if s == [] {
        return HasCertR11(DStarNil);
      }
      out := SearchStarR11(a, s, 1);
    // @hole-end R11.H5d
  }
  // Hint(1): the two ensures clauses are the checker's and the matcher's halves; the leaves decide both directly.
  // Hint(2): H6 and H7 start from the first split (0 for Cat, 1 for a non-empty Star word) with an empty exclusion.

  // item: R11.H6d
  // pair: R11.H6v
  /** **H6.** The split loop of a concatenation, as a recursion on k: every split
      below k is known to fail; try k, and on failure recurse on k + 1. What does
      the precondition for k + 1 need that the call at k established? */
  method SearchCatR11(a: Re, b: Re, s: seq<char>, k: nat) returns (out: CertChoiceR11)
    requires k <= |s| + 1
    requires forall i | 0 <= i < k && i <= |s| :: !(Matches(a, s[..i]) && Matches(b, s[i..]))
    ensures out.HasCertR11? ==> CheckDeriv(Cat(a, b), s, out.value)
    ensures out.NoCertR11? ==> !Matches(Cat(a, b), s)
    decreases Cat(a, b), |s|, |s| + 1 - k
  {
    // @hole-begin R11.H6d
    if k > |s| {
      return NoCertR11;
    }
    var left := SearchR11(a, s[..k]);
    var right := NoCertR11;
    if left.HasCertR11? {
      right := SearchR11(b, s[k..]);
    }
    if left.HasCertR11? && right.HasCertR11? {
      return HasCertR11(DCat(k, left.value, right.value));
    }
    forall i | 0 <= i < k + 1 && i <= |s|
      ensures !(Matches(a, s[..i]) && Matches(b, s[i..]))
    {
      if i < k {
      } else {
        assert i == k;
      }
    }
    out := SearchCatR11(a, b, s, k + 1);
    // @hole-end R11.H6d
  }
  // Hint(1): past the last split the exclusion covers every index, which is exactly !Matches(Cat(a, b), s).
  // Hint(2): a forall statement extends the exclusion from k to k + 1; the new index is the one just tried.

  // item: R11.H7d
  // pair: R11.H7v
  /** **H7.** The first-chunk loop of a star, as H6 with chunks of length at
      least 1. Which bound on k differs from H6, and why? */
  method SearchStarR11(a: Re, s: seq<char>, k: nat) returns (out: CertChoiceR11)
    requires s != [] && 1 <= k <= |s| + 1
    requires forall i | 0 < i < k && i <= |s| :: !(Matches(a, s[..i]) && Matches(Star(a), s[i..]))
    ensures out.HasCertR11? ==> CheckDeriv(Star(a), s, out.value)
    ensures out.NoCertR11? ==> !Matches(Star(a), s)
    decreases Star(a), |s|, |s| + 1 - k
  {
    // @hole-begin R11.H7d
    if k > |s| {
      return NoCertR11;
    }
    var left := SearchR11(a, s[..k]);
    var right := NoCertR11;
    if left.HasCertR11? {
      right := SearchR11(Star(a), s[k..]);
    }
    if left.HasCertR11? && right.HasCertR11? {
      return HasCertR11(DStarCons(k, left.value, right.value));
    }
    forall i | 0 < i < k + 1 && i <= |s|
      ensures !(Matches(a, s[..i]) && Matches(Star(a), s[i..]))
    {
      if i < k {
      } else {
        assert i == k;
      }
    }
    out := SearchStarR11(a, s, k + 1);
    // @hole-end R11.H7d
  }
  // Hint(1): H6's shape, with Star(a) in place of b and the exclusion starting above 0.
  // Hint(2): the recursive call on Star(a) and a shorter suffix is allowed by SearchR11's measure (r, |s|).
}

// =============================================================================
// Given (not an item): the compiled use-site check
// =============================================================================

module R11_Clients {
  import opened RG_A1_Re
  import opened RG_A4_Norm
  import opened R11_WpReview
  import opened R11_Kernel
  import opened R11_Streaming
  import opened R11_Search

  // Given (not an item): the compiled use-site check of T1, H1, H4 and H5 to H7.
  // It runs your method bodies; `scripts/vcheck --test` executes it once they are done.
  @Test
  method CertificateSampleTest()
  {
    var next := WpIndexStepR11(2, 5);
    expect next == 3;
    var ab := Cat(Chr('a'), Star(Chr('b')));
    var good := CheckCertificateR11(ab, ['a', 'b'], DCat(1, DChr, DStarCons(1, DChr, DStarNil)));
    expect good;
    var bad := CheckCertificateR11(ab, ['a', 'b'], DCat(2, DChr, DStarNil));
    expect !bad;
    var accepted, trace := PrefixMatchesR11(ab, ['a', 'b', 'a']);
    expect !accepted;
    expect trace == [true, true, false];
    var pattern := Cat(Star(Chr('a')), Chr('b'));
    var found := SearchR11(pattern, ['a', 'a', 'b']);
    expect found.HasCertR11?;
    var checked := CheckCertificateR11(pattern, ['a', 'a', 'b'], found.value);
    expect checked;
    var missing := SearchR11(pattern, ['a', 'a']);
    expect missing.NoCertR11?;
  }
}
