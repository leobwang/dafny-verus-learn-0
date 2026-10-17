/*! R04 — Specs as logic (exercises).
Standalone R, A1 only. No earlier learner exercise or later A1b is imported.
Six predictions precede the written work, audit drill and card demos. Commit
P1d/P2dv/P5d/P6dv in slots/R04.slots and P3d/P4v in their specimens; run
scripts/firsttry.sh R04 --check before enabling any prediction switch.
T1 is closed book before reading: keep its supplied check commented for the
first try. Six holes per language (T1 and H1-H5), two test-outs in the pair.
Done includes zero-hole native gates, clean audit, freeze and strict report,
the written/audit/agent/bench-card reviews and the module viva.
*/
module R04_Specs {
  import opened RG_A1_Re
  ghost predicate Occurs(r: Re, s: seq<char>) {
    exists i,j :: 0 <= i <= j <= |s| && Matches(r,s[i..j])
  }

  // item: R04.T1d
  // pair: R04.T1v
  // Closed book, before reading: give a witness and prove the claim.
  lemma SomeWordMatches()
    ensures exists s :: Matches(Cat(Chr('o'),Star(Chr('k'))),s)

  // item: R04.P1d verdict
  // RuntimePositive(x) has expect x > 0; y := x; and ensures y > 0, outside a test.
  // Predict the verification verdict of its exact specimen, D:<v>.
  // SLOT: CHECK P1d
  // item: R04.P2dv verdict
  // For r := Star(Chr('a')), s := "b", which Find postconditions force true?
  // [a] b <==> Occurs(r,s); [b] b <==> Matches(r,s);
  // [c] b ==> Occurs(r,s); [d] b <==> exists i :: 0 <= i <= |s| && Matches(r,s[i..]).
  // Answer labels separated by single spaces, or none; same in both languages.
  // SLOT: CHECK P2dv
  // P5d is the RuntimePositive delivery in specimens/R04/P5d.dfy.specimen.
  // item: R04.P6dv verdict
  // FindNone always returns false, checked separately against [a]-[d] above.
  // Which verify? D:<labels> V:<labels>, labels in order or none.
  // SLOT: CHECK P6dv

  // item: R04.W1d
  lemma EpsOnlyEmpty()
    ensures forall s :: Matches(Eps,s) ==> s == []
  {
    forall s | Matches(Eps,s) ensures s == [] { }
  }

  // item: R04.W2d
  lemma CatChrNonEmpty(b: Re, s: seq<char>)
    requires Matches(Cat(Chr('x'),b),s)
    ensures |s| >= 1
  {
    var i :| 0 <= i <= |s| && Matches(Chr('x'),s[..i]) && Matches(b,s[i..]);
    assert s[..i] == ['x'];
  }

  // item: R04.C1d write:forall-intro
  // EpsOnlyEmpty's forall statement proves an arbitrary qualifying s.
  // item: R04.C2d write:exists-elim
  // CatChrNonEmpty extracts a witness with :| and retains every bound.
  // item: R04.C3d recognise:expect
  // Recognise expect in the sealed RuntimePositive specimen; inspect only after predictions.

  // item: R04.H1d
  // pair: R04.H1v
  lemma WitnessAbb()
    ensures Matches(Cat(Chr('a'),Star(Chr('b'))),"abb")

  // item: R04.H2d
  // uses: forall-intro, exists-elim
  // pair: R04.H2v
  lemma WitnessNotBa()
    ensures !Matches(Cat(Chr('a'),Star(Chr('b'))),"ba")

  // item: R04.H3d
  // uses: forall-intro, exists-elim
  // pair: R04.H3v
  lemma WitnessAnchored()
    ensures !Matches(Chr('a'),"ba") && Matches(Cat(Star(Chr('b')),Chr('a')),"ba")

  // item: R04.H4d
  // pair: R04.H4v
  /** FROM PROSE: true exactly when some prefix of s, including the empty
      prefix, matches r. Supply the definition and enable all three checks.
      The benign ensures only makes this definition hole tool-counted; it
      supplies no semantic relationship. The given checks stay fixed. */
  ghost predicate PrefixMatch(r: Re, s: seq<char>)
    ensures true

  // Uncomment as you go:
  // lemma PrefixPositive() { assert "ab"[..1] == "a"; assert PrefixMatch(Chr('a'),"ab"); }
  // lemma PrefixNegative() { forall i | 0 <= i <= 2 ensures !Matches(Chr('b'),"ab"[..i]) { if i == 0 { assert "ab"[..i] == []; } else if i == 1 { assert "ab"[..i] == "a"; } else { assert "ab"[..i] == "ab"; } } assert !PrefixMatch(Chr('b'),"ab"); }
  // lemma PrefixEmpty(s: seq<char>) { assert s[..0] == []; assert PrefixMatch(Eps,s); }

  // item: R04.H5d
  // pair: R04.H5v
  // Find's mutant returns Nullable(r). Refute that implementation's equivalence.
  lemma MutantKilled()
    ensures exists r: Re, s: seq<char> :: Nullable(r) != Occurs(r,s)

  /* AUDIT — learner-owned,20 min, after recording P5d.
     Run the three supplied deliveries; classify gate and audit observations,
     the assumptions each instrument sees and what remains for a human review.
     Record actual commands, exits, findings and their scope: ...
     CALIBRATION — estimate / actual / correction and observation: ...
  */
  // item: R04.C5dv diverge:r04-c5
  // FINAL CARD: runtime checks and proof obligations. The paired sealed
  // demos require recorded P1d and P5d; read them last.
}
