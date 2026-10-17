// DVR0 spike: candidate exercise items outside the layers (author-only).
// R04 witness items and R08's refinement obligation, over the layers.
module RX_Witness {
  import opened RG_A1_Re

  // A positive witness: the splits must be named.
  lemma WitnessAbb()
    ensures Matches(Cat(Chr('a'), Star(Chr('b'))), "abb")
  {
    // @hole-begin X.WitnessAbb
    var s := "abb";
    assert s[..1] == "a" && s[1..] == "bb";
    var t := "bb";
    assert t[..1] == "b" && t[1..] == "b";
    var u := "b";
    assert u[..1] == "b" && u[1..] == [];
    assert Matches(Star(Chr('b')), u);
    // @hole-end X.WitnessAbb
  }

  // A negative item: no split works.
  lemma WitnessNotBa()
    ensures !Matches(Cat(Chr('a'), Star(Chr('b'))), "ba")
  {
    // @hole-begin X.WitnessNotBa
    var s := "ba";
    if Matches(Cat(Chr('a'), Star(Chr('b'))), s) {
      var i :| 0 <= i <= |s| && Matches(Chr('a'), s[..i]) && Matches(Star(Chr('b')), s[i..]);
      assert s[..i] == "a";
      assert s[0] == 'b';
    }
    // @hole-end X.WitnessNotBa
  }

  // Anchoring: whole-string matching rejects a match inside the string.
  lemma WitnessAnchored()
    ensures !Matches(Chr('a'), "ba") && Matches(Cat(Star(Chr('b')), Chr('a')), "ba")
  {
    // @hole-begin X.WitnessAnchored
    var s := "ba";
    assert s[..1] == "b" && s[1..] == "a";
    var t := "b";
    assert t[..1] == "b" && t[1..] == [];
    assert Matches(Star(Chr('b')), t);
    // @hole-end X.WitnessAnchored
  }
}

abstract module RX_MatcherSpec {
  import opened RG_A1_Re

  method Match(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
}

module RX_DerivMatcher refines RX_MatcherSpec {
  import opened RG_A2_Deriv

  method Match(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
  {
    // @hole-begin X.Match
    b := DerivMatch(r, s);
    // @hole-end X.Match
  }
}
