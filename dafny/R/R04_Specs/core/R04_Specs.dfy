/*! R04 — Specs as logic (exercises).
Standalone R, A1 only. No earlier learner exercise or later A1b is imported.
Six predictions precede the written work, audit drill and card demos. Commit
P1d/P2dv/P5d/P6dv in slots/R04.slots and P3d/P4v in their specimens; run
scripts/firsttry.sh R04 --check before enabling any prediction switch.
Complete T1 closed book before reading; record its first try before opening
worked material. Six holes per language (T1 and H1-H5), two test-outs in the pair.
File order: the given Occurs, T1, the prediction block, the worked examples
(W1, W2), the cards (C1 to C3), the holes (H1 to H5), the AUDIT block, then
the final divergence card (C5). Each hole comes after the cards its `uses:`
line names; chapter §2 teaches the witness and quantifier moves first.
Done includes zero-hole native gates, clean audit, freeze and strict report,
the written/audit/agent/bench-card reviews and the module viva.
*/
module R04_Specs {
  import opened RG_A1_Re

  // Given: some substring s[i..j] of s, the empty ones included, matches r.
  ghost predicate Occurs(r: Re, s: seq<char>)
  {
    exists i, j :: 0 <= i <= j <= |s| && Matches(r, s[i..j])
  }

  // item: R04.T1d
  // pair: R04.T1v
  // Closed book, before reading: give a witness of length 3 and prove the claim
  // (D64: the Dafny test-out asks for a three-character word; Verus's asks for any).
  lemma SomeWordMatches()
    ensures exists s :: |s| == 3 && Matches(Cat(Chr('o'), Star(Chr('k'))), s)
  // HOLE: write the proof body.

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

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: R04.W1d
  /** Introduce a universal claim: the `forall` statement fixes an arbitrary
      s that satisfies its range and proves the `ensures` for it. */
  lemma EpsOnlyEmpty()
    ensures forall s :: Matches(Eps, s) ==> s == []
  {
    forall s | Matches(Eps, s)
      ensures s == []
    {
    }
  }

  // item: R04.W2d
  /** Eliminate an existential: `:|` takes a split the premise guarantees,
      with every conjunct of its definition, and reasons about it. */
  lemma CatChrNonEmpty(b: Re, s: seq<char>)
    requires Matches(Cat(Chr('x'), b), s)
    ensures |s| >= 1
  {
    var i :| 0 <= i <= |s| && Matches(Chr('x'), s[..i]) && Matches(b, s[i..]);
    assert s[..i] == ['x'];
  }

  // ===========================================================================
  // Cards
  // ===========================================================================

  // item: R04.C1d write:forall-intro
  // EpsOnlyEmpty's forall statement proves an arbitrary qualifying s.
  // EXPECT: card-c1d.dfy.specimen fails: its claim does not hold for every s.
  // item: R04.C2d write:exists-elim
  // CatChrNonEmpty extracts a witness with :| and retains every bound.
  // EXPECT: card-c2d.dfy.specimen fails: no premise guarantees its witness.
  // item: R04.C3d recognise:expect
  // Recognise expect in the sealed RuntimePositive specimen; inspect only after predictions.

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R04.H1d
  // pair: R04.H1v
  /** **H1.** A positive witness: prove that `Cat(Chr('a'), Star(Chr('b')))`
      matches the whole string "abb". Which split of "abb" does the `Cat`
      need, and how many chunks does the `Star` take from the rest? */
  lemma WitnessAbb()
    ensures Matches(Cat(Chr('a'), Star(Chr('b'))), "abb")
  // HOLE: write the proof body.
  // Hint(1): a Star match on a non-empty string is one non-empty chunk and a
  //    Star match of the rest; work from the shortest rest upwards.
  // Hint(2): name each slice as a sequence ("abb"[..1] == "a"), the way
  //    chapter §2.3 names the slices of its witness.

  // item: R04.H2d
  // uses: forall-intro, exists-elim
  // pair: R04.H2v
  /** **H2.** A negative claim about every match: no string that
      `Cat(Chr('x'), Cat(Chr('y'), Star(Chr('z'))))` matches has 'x' in second
      place. Prove it for an arbitrary match with a `forall` statement (W1),
      and use the match through the splits it guarantees (W2). Which two
      splits does a match supply, and what does each `Chr` side force? */
  lemma NoXInSecondPlace()
    ensures forall s: seq<char> :: Matches(Cat(Chr('x'), Cat(Chr('y'), Star(Chr('z')))), s) ==> |s| >= 2 && s[1] != 'x'
  // HOLE: write the proof body.
  // Hint(1): a `forall s | <the match> ensures <the claim> { … }` statement
  //    fixes one arbitrary match; the rest of the proof is about that `s`.
  // Hint(2): take the outer split with `:|`, then the split of its suffix;
  //    each `Chr` side pins one character.

  // item: R04.H3d
  // uses: forall-intro, exists-elim
  // pair: R04.H3v
  /** **H3.** Anchoring: a whole-string match of `Cat(Cat(Chr('a'),
      Star(Chr('b'))), Chr('c'))` begins with 'a' and ends with 'c'; an
      occurrence would pin neither end. Prove it for every matching string,
      from the splits a match guarantees (W2). Which split pins the last
      character, and which pins the first? */
  lemma WitnessAnchored()
    ensures forall s: seq<char> :: Matches(Cat(Cat(Chr('a'), Star(Chr('b'))), Chr('c')), s) ==> |s| >= 2 && s[0] == 'a' && s[|s| - 1] == 'c'
  // HOLE: write the proof body.
  // Hint(1): the outer split's right side is `Chr('c')`, which matches one
  //    string only; the left side is itself a `Cat`, whose split you take next.
  // Hint(2): W2 takes a split out of a premise with `:|`; here the premise is
  //    the antecedent of the `forall`, inside a `forall` statement (W1).

  // item: R04.H4d
  // pair: R04.H4v
  /** **H4.** From prose: `PrefixMatch(r, s)` is true exactly when some prefix
      of `s`, the empty prefix included, matches `r`. Supply the definition,
      then uncomment the three checks below; their proofs are given and
      verify only with an adequate definition. Which bounds may the prefix's
      end take, and which may its start? (The benign `ensures true` only
      makes the missing definition a tool-counted hole.) */
  ghost predicate PrefixMatch(r: Re, s: seq<char>)
    ensures true
  // HOLE: write the definition body.
  // Hint(1): `Occurs` above chooses both ends of a substring; a prefix fixes one.
  // Hint(2): the empty prefix is `s[..0]`, so the end's lower bound decides
  //    the third check.
  // Uncomment as you go:
  // lemma PrefixPositive()
  // {
  //   assert "ab"[..1] == "a";
  //   assert PrefixMatch(Chr('a'), "ab");
  // }
  // lemma PrefixNegative()
  // {
  //   forall i | 0 <= i <= 2
  //     ensures !Matches(Chr('b'), "ab"[..i])
  //   {
  //     if i == 0 {
  //       assert "ab"[..i] == [];
  //     } else if i == 1 {
  //       assert "ab"[..i] == "a";
  //     } else {
  //       assert "ab"[..i] == "ab";
  //     }
  //   }
  //   assert !PrefixMatch(Chr('b'), "ab");
  // }
  // lemma PrefixEmpty(s: seq<char>)
  // {
  //   assert s[..0] == [];
  //   assert PrefixMatch(Eps, s);
  // }

  // item: R04.H5d
  // pair: R04.H5v
  /** **H5.** A mutant-kill witness: a mutant `Find` returns `Nullable(r)`
      instead of `Occurs(r, s)`. For `r := Cat(Chr('a'), Chr('b'))`, prove that
      some string tells the two apart. Which string makes the occurrence true,
      and which facts name it? (D64: the Dafny statement fixes `r`; Verus's
      leaves both free.) */
  lemma MutantKilled()
    ensures exists s: seq<char> :: Nullable(Cat(Chr('a'), Chr('b'))) != Occurs(Cat(Chr('a'), Chr('b')), s)
  // HOLE: write the proof body.
  // Hint(1): `Cat(Chr('a'), Chr('b'))` is not nullable, so the string must
  //    contain an occurrence.
  // Hint(2): `Occurs` is an existential: name its two indices by a slice
  //    fact, and the occurrence's own split, the way §3.3's witness does.

  /* AUDIT — learner-owned, 20 min, after recording P5d.
     Run the three supplied deliveries; classify gate and audit observations,
     the assumptions each instrument sees and what remains for a human review.
     Record actual commands, exits, findings and their scope:
     clean delivery: ...
     expect delivery: ...
     assume delivery: ...

     CALIBRATION — estimate / actual / correction and observation: ...
  */

  // item: R04.C5dv diverge:r04-c5
  // FINAL CARD: runtime checks and proof obligations. The paired sealed
  // demos require recorded P1d and P5d; read them last.
}
