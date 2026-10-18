// R12_HINT_SITES: [{"name":"h1","identifiers":["u","v"]},{"name":"h2","identifiers":["u","v"]},{"name":"h3","identifiers":["u","v"]},{"name":"c1","identifiers":["u","v"],"kind":"calls","callees":["BackwardsStrAppend"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BackwardsStrAppend","start":15,"end":26}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (BackwardsStr), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  // The string read backwards.
  function BackwardsStr(s: seq<char>): seq<char>
    decreases |s|
  {
    if s == [] then [] else BackwardsStr(s[1..]) + [s[0]]
  }

  // The task.
  lemma BackwardsStrAppend(u: seq<char>, v: seq<char>)
    ensures BackwardsStr(u + v) == BackwardsStr(v) + BackwardsStr(u)
    decreases |u|
  {
    if u == [] {
      assert /*R12_HINT:h1*/ true;
    } else {
      assert /*R12_HINT:h2*/ true;
      assert /*R12_HINT:h3*/ true;
      /*R12_CALLS:c1*/
    }
  }
}
