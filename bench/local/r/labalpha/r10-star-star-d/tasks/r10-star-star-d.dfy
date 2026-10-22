// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["StarStar","StarConcat"]},{"name":"h1"},{"name":"c2","kind":"calls","callees":["StarOne"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.StarStar","start":48,"end":60}]
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

  // Provided facts (RG_A1b_Facts.StarOne, StarConcat), complete, copied verbatim.
  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u)
  {
    if u != [] {
      assert u[..|u|] == u && u[|u|..] == [];
    }
  }

  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(Star(a), v)
    ensures Matches(Star(a), u + v)
    decreases |u|
  {
    if u == [] {
      assert u + v == v;
    } else {
      var i :| 0 < i <= |u| && Matches(a, u[..i]) && Matches(Star(a), u[i..]);
      StarConcat(a, u[i..], v);
      assert (u + v)[..i] == u[..i];
      assert (u + v)[i..] == u[i..] + v;
    }
  }

  // The task (R10 agent StarStar): a star of a star is the star.
  lemma StarStar(a: Re, s: seq<char>)
    ensures Matches(Star(Star(a)), s) <==> Matches(Star(a), s)
    decreases |s|
  {
    if Matches(Star(Star(a)), s) && s != [] {
      var i :| 0 < i <= |s| && Matches(Star(a), s[..i]) && Matches(Star(Star(a)), s[i..]);
      /*R12_CALLS:c1*/
      assert /*R12_HINT:h1*/ true;
    }
    if Matches(Star(a), s) && s != [] {
      /*R12_CALLS:c2*/
    }
  }
}
