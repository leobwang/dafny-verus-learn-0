// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["b","s"],"kind":"calls","callees":["CatEpsLeft"]},{"name":"c2","identifiers":["a","s"],"kind":"calls","callees":["CatEpsRight"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.MkCatCorrect","start":68,"end":77}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  ghost predicate Matches(r: Re, s: seq<char>)
    decreases r, |s|
  {
    match r
    case Empty => false
    case Eps => s == []
    case Chr(c) => s == [c]
    case Alt(a, b) => Matches(a, s) || Matches(b, s)
    case Cat(a, b) => exists i | 0 <= i <= |s| :: Matches(a, s[..i]) && Matches(b, s[i..])
    case Star(a) => s == [] || exists i | 0 < i <= |s| :: Matches(a, s[..i]) && Matches(Star(a), s[i..])
  }

  // Provided definitions: RG_A4_Norm (layer A4), copied verbatim.
  predicate Normal(r: Re)
    decreases r
  {
    match r
    case Empty => true
    case Eps => true
    case Chr(_) => true
    case Alt(a, b) => a != Empty && b != Empty && a != b && Normal(a) && Normal(b)
    case Cat(a, b) => a != Empty && b != Empty && a != Eps && b != Eps && Normal(a) && Normal(b)
    case Star(a) => a != Empty && a != Eps && !a.Star? && Normal(a)
  }

  type NormRe = r: Re | Normal(r) witness Empty

  function MkCat(a: NormRe, b: NormRe): NormRe
  {
    if a == Empty || b == Empty then Empty
    else if a == Eps then b
    else if b == Eps then a
    else Cat(a, b)
  }

  // Provided facts (RG_A1b_Facts.CatEpsLeft, CatEpsRight), complete, copied verbatim.
  lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert s[..0] == [] && s[0..] == s;
    }
  }

  lemma CatEpsRight(r: Re, s: seq<char>)
    ensures Matches(Cat(r, Eps), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert s[..|s|] == s && s[|s|..] == [];
    }
    if Matches(Cat(r, Eps), s) {
      var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Eps, s[i..]);
      assert i == |s|;
      assert s[..i] == s;
    }
  }

  // The task (R10 agent MkCatCorrect): the smart concatenation keeps the language.
  lemma MkCatCorrect(a: NormRe, b: NormRe, s: seq<char>)
    ensures Matches(MkCat(a, b), s) <==> Matches(Cat(a, b), s)
  {
    if a == Empty || b == Empty {
    } else if a == Eps {
      /*R12_CALLS:c1*/
    } else if b == Eps {
      /*R12_CALLS:c2*/
    }
  }
}
