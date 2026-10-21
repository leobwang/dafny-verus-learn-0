// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["CopiesUpToCorrect"]},{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"h4"},{"name":"c2","kind":"calls","callees":["CopiesUpToCorrect"]},{"name":"h5"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CopiesUpToCorrect","start":37,"end":79}]
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

  // Provided definitions: RG_A3_Syntax (layer A3), counted repetition, copied verbatim.
  function Copies(r: Re, k: nat): Re
    decreases r, k
  {
    if k == 0 then Eps else Cat(r, Copies(r, k - 1))
  }

  // Zero to j more copies.
  function CopiesUpTo(r: Re, j: nat): Re
    decreases r, j
  {
    if j == 0 then Eps else Alt(Eps, Cat(r, CopiesUpTo(r, j - 1)))
  }

  // The task (R09 CopiesUpToCorrect): CopiesUpTo(r, j) matches exactly 0..j copies.
  lemma CopiesUpToCorrect(r: Re, j: nat, s: seq<char>)
    ensures Matches(CopiesUpTo(r, j), s) <==> exists k | 0 <= k <= j :: Matches(Copies(r, k), s)
    decreases j
  {
    if j > 0 {
      var u := CopiesUpTo(r, j - 1);
      assert CopiesUpTo(r, j) == Alt(Eps, Cat(r, u));
      if Matches(CopiesUpTo(r, j), s) {
        if s != [] {
          assert !Matches(Eps, s);
          assert Matches(Cat(r, u), s);
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(u, s[i..]);
          /*R12_CALLS:c1*/
          var k :| 0 <= k <= j - 1 && Matches(Copies(r, k), s[i..]);
          assert /*R12_HINT:h1*/ true;
          assert /*R12_HINT:h2*/ true;
        } else {
          assert /*R12_HINT:h3*/ true;
        }
      }
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        if k > 0 {
          assert /*R12_HINT:h4*/ true;
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Copies(r, k - 1), s[i..]);
          /*R12_CALLS:c2*/
          assert exists k' | 0 <= k' <= j - 1 :: Matches(Copies(r, k'), s[i..]);
          assert /*R12_HINT:h5*/ true;
        } else {
          assert Copies(r, 0) == Eps;
        }
        assert Matches(CopiesUpTo(r, j), s);
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    } else {
      assert Copies(r, 0) == Eps;
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        assert k == 0;
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    }
  }
}
