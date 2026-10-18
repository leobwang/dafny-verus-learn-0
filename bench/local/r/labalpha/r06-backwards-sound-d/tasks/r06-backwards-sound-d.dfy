// R12_HINT_SITES: [{"name":"h1","identifiers":["s"]},{"name":"c1","identifiers":["a","s"],"kind":"calls","callees":["BackwardsSound"]},{"name":"c2","identifiers":["b","s"],"kind":"calls","callees":["BackwardsSound"]},{"name":"c3","identifiers":["a","b","s","i"],"kind":"calls","callees":["BackwardsSound"]},{"name":"h2","identifiers":["s","i"]},{"name":"c4","identifiers":["s","i"],"kind":"calls","callees":["BackwardsStrAppend"]},{"name":"h3","identifiers":["w","j","BackwardsStr","s","i"]},{"name":"c5","identifiers":["a","s","i","Star","Backwards","BackwardsStr"],"kind":"calls","callees":["BackwardsSound","StarOne","StarConcat"]},{"name":"h4","identifiers":["s","i"]},{"name":"c6","identifiers":["s","i"],"kind":"calls","callees":["BackwardsStrAppend"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BackwardsSound","start":82,"end":113}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (Re, Matches, Backwards, BackwardsStr), copied verbatim.
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

  // The regex read backwards.
  function Backwards(r: Re): Re
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Eps
    case Chr(c) => Chr(c)
    case Alt(a, b) => Alt(Backwards(a), Backwards(b))
    case Cat(a, b) => Cat(Backwards(b), Backwards(a))
    case Star(a) => Star(Backwards(a))
  }

  // The string read backwards.
  function BackwardsStr(s: seq<char>): seq<char>
    decreases |s|
  {
    if s == [] then [] else BackwardsStr(s[1..]) + [s[0]]
  }

  // Provided facts, complete (not tasks).

  // RG06 BackwardsStrAppend (R06 decomposer reference), complete.
  lemma BackwardsStrAppend(u: seq<char>, v: seq<char>)
    ensures BackwardsStr(u + v) == BackwardsStr(v) + BackwardsStr(u)
    decreases |u|
  {
    if u == [] {
      assert u + v == v;
    } else {
      assert (u + v)[1..] == u[1..] + v;
      assert (u + v)[0] == u[0];
      BackwardsStrAppend(u[1..], v);
    }
  }

  // RG_A1b_Facts.StarOne, complete.
  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u)
  {
    if u != [] {
      assert u[..|u|] == u && u[|u|..] == [];
    }
  }

  // RG_A1b_Facts.StarConcat, complete.
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

  // The task.
  lemma BackwardsSound(r: Re, s: seq<char>)
    requires Matches(r, s)
    ensures Matches(Backwards(r), BackwardsStr(s))
    decreases r, |s|
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(c) =>
      assert /*R12_HINT:h1*/ true;
    case Alt(a, b) =>
      if Matches(a, s) {
        /*R12_CALLS:c1*/
      } else {
        /*R12_CALLS:c2*/
      }
    case Cat(a, b) =>
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b, s[i..]);
      /*R12_CALLS:c3*/
      assert /*R12_HINT:h2*/ true;
      /*R12_CALLS:c4*/
      var w := BackwardsStr(s);
      var j := |BackwardsStr(s[i..])|;
      assert /*R12_HINT:h3*/ true;
    case Star(a) =>
      if s != [] {
        var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
        /*R12_CALLS:c5*/
        assert /*R12_HINT:h4*/ true;
        /*R12_CALLS:c6*/
      }
  }
}
