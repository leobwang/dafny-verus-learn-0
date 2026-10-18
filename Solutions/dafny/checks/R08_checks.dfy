/*!
# R08 — value prediction P1d (Reference Solution)

The alternative-set engine's two given functions, printed here so that this check
needs nothing from the exercise file. Fill the slot, then record the first try with
`scripts/firsttry.sh R08 --check` before you run this file.
*/
module R08_PredictParts {
  import opened RG_A1_Re
  import A2 = RG_A2_Deriv

  function Parts(r: Re): seq<Re>
  {
    match r
    case Empty => []
    case Alt(a, b) => Parts(a) + Parts(b)
    case _ => [r]
  }

  function FeedAll(st: seq<Re>, c: char): seq<Re>
  {
    if st == [] then [] else Parts(A2.Deriv(st[0], c)) + FeedAll(st[1..], c)
  }
}

module R08_Checks {
  import opened RG_A1_Re
  import P = R08_PredictParts

  // item: R08.P1d value
  // The state [Cat(Chr('a'), Chr('b')), Star(Chr('a'))] reads the character 'b'.
  // How many alternatives does the next state hold? Answer form: a natural number.
  @Test
  method StateSizeAfterB()
  {
    var st := P.FeedAll([Cat(Chr('a'), Chr('b')), Star(Chr('a'))], 'b');
    expect |st| == 2;
  }
}
