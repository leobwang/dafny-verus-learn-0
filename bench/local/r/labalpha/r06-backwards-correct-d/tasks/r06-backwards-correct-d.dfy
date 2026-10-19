// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["r","s"],"kind":"calls","callees":["BackwardsSound"]},{"name":"c2","identifiers":["r","s","Backwards","BackwardsStr"],"kind":"calls","callees":["BackwardsSound","BackwardsInvolution","BackwardsStrInvolution"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BackwardsCorrect","start":157,"end":166}]
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

  // R06 BackwardsStrInvolution (R06 decomposer reference), complete.
  lemma BackwardsStrInvolution(s: seq<char>)
    ensures BackwardsStr(BackwardsStr(s)) == s
    decreases |s|
  {
    if s != [] {
      BackwardsStrAppend(BackwardsStr(s[1..]), [s[0]]);
      assert BackwardsStr([s[0]]) == [s[0]] by {
        assert [s[0]][1..] == [];
      }
      BackwardsStrInvolution(s[1..]);
      assert s == [s[0]] + s[1..];
    }
  }

  // R06 BackwardsInvolution (R06 decomposer reference), complete.
  lemma BackwardsInvolution(r: Re)
    ensures Backwards(Backwards(r)) == r
    decreases r
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      BackwardsInvolution(a);
      BackwardsInvolution(b);
    case Cat(a, b) =>
      BackwardsInvolution(a);
      BackwardsInvolution(b);
    case Star(a) =>
      BackwardsInvolution(a);
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

  // R06 BackwardsSound (R06 decomposer reference), complete.
  lemma BackwardsSound(r: Re, s: seq<char>)
    requires Matches(r, s)
    ensures Matches(Backwards(r), BackwardsStr(s))
    decreases r, |s|
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(c) =>
      assert s[1..] == [];
    case Alt(a, b) =>
      if Matches(a, s) {
        BackwardsSound(a, s);
      } else {
        BackwardsSound(b, s);
      }
    case Cat(a, b) =>
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b, s[i..]);
      BackwardsSound(a, s[..i]);
      BackwardsSound(b, s[i..]);
      assert s == s[..i] + s[i..];
      BackwardsStrAppend(s[..i], s[i..]);
      var w := BackwardsStr(s);
      var j := |BackwardsStr(s[i..])|;
      assert w[..j] == BackwardsStr(s[i..]) && w[j..] == BackwardsStr(s[..i]);
    case Star(a) =>
      if s != [] {
        var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
        BackwardsSound(a, s[..i]);
        StarOne(Backwards(a), BackwardsStr(s[..i]));
        BackwardsSound(Star(a), s[i..]);
        StarConcat(Backwards(a), BackwardsStr(s[i..]), BackwardsStr(s[..i]));
        assert s == s[..i] + s[i..];
        BackwardsStrAppend(s[..i], s[i..]);
      }
  }

  // The task.
  lemma BackwardsCorrect(r: Re, s: seq<char>)
    ensures Matches(Backwards(r), BackwardsStr(s)) <==> Matches(r, s)
  {
    if Matches(r, s) {
      /*R12_CALLS:c1*/
    }
    if Matches(Backwards(r), BackwardsStr(s)) {
      /*R12_CALLS:c2*/
    }
  }
}
