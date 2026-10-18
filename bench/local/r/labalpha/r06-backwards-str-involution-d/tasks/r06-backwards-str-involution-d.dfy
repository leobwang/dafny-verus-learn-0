// R12_HINT_SITES: [{"name":"c1","identifiers":["BackwardsStr","s"],"kind":"calls","callees":["BackwardsStrAppend"]},{"name":"h1","identifiers":["s"]},{"name":"c2","identifiers":["s"],"kind":"calls","callees":["BackwardsStrInvolution"]},{"name":"h2","identifiers":["s"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BackwardsStrInvolution","start":31,"end":43}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (BackwardsStr), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

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

  // The task.
  lemma BackwardsStrInvolution(s: seq<char>)
    ensures BackwardsStr(BackwardsStr(s)) == s
    decreases |s|
  {
    if s != [] {
      /*R12_CALLS:c1*/
      assert BackwardsStr([s[0]]) == [s[0]] by {
        assert /*R12_HINT:h1*/ true;
      }
      /*R12_CALLS:c2*/
      assert /*R12_HINT:h2*/ true;
    }
  }
}
