// R12_HINT_SITES: [{"name":"c1","identifiers":["rs","c"],"kind":"calls","callees":["RangesClassLaw"]},{"name":"h1","identifiers":["rs","j"]},{"name":"h2","identifiers":["rs","j"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.RangesClassLaw","start":34,"end":50}]
module R12_LabCase {

  // Provided layer: RG_A2_Deriv (layer A2), imported as A2; the class API this task uses
  // (its contracts, verbatim from the layer; bodies hidden by the layer's export):
  //   function ClassEmpty(): (r: CharClass)
  //     ensures ClassValid(r) ensures forall c :: !InClass(r, c) ensures ClassRanges(r) == []
  //   function ClassUnion(a: CharClass, b: CharClass): (u: CharClass)
  //     requires ClassValid(a) && ClassValid(b)
  //     ensures ClassValid(u) ensures forall c :: InClass(u, c) <==> InClass(a, c) || InClass(b, c)
  //     ensures forall n: int :: ClassBelow(a, n) && ClassBelow(b, n) ==> ClassBelow(u, n)
  //   function ClassRange(lo: char, hi: char): (r: CharClass)
  //     ensures ClassValid(r) ensures forall c :: InClass(r, c) <==> lo <= c <= hi
  //   function ClassMember(cc: CharClass, c: char): (b: bool)
  //     ensures b == InClass(cc, c)
  import A2 = RG_A2_Deriv

  // Provided definitions (R08_RangeStarEngine, given), copied verbatim.
  // Given: c lies in one of the ranges.
  ghost predicate InSomeRange(rs: seq<(char, char)>, c: char)
  {
    exists j | 0 <= j < |rs| :: rs[j].0 <= c <= rs[j].1
  }

  // Given: the class of all the ranges, built with A2's class API.
  function RangesClass(rs: seq<(char, char)>): (cls: A2.CharClass)
    ensures A2.ClassValid(cls)
  {
    if rs == [] then A2.ClassEmpty() else A2.ClassUnion(A2.ClassRange(rs[0].0, rs[0].1), RangesClass(rs[1..]))
  }

  // The task (R08.H1 RangesClassLaw): the class the engine builds holds exactly the characters of the pattern's ranges.
  lemma {:induction false} RangesClassLaw(rs: seq<(char, char)>, c: char)
    ensures A2.InClass(RangesClass(rs), c) <==> InSomeRange(rs, c)
  {
    if rs != [] {
      /*R12_CALLS:c1*/
      if InSomeRange(rs[1..], c) {
        var j :| 0 <= j < |rs[1..]| && rs[1..][j].0 <= c <= rs[1..][j].1;
        assert /*R12_HINT:h1*/ true;
      }
      if InSomeRange(rs, c) {
        var j :| 0 <= j < |rs| && rs[j].0 <= c <= rs[j].1;
        if j > 0 {
          assert /*R12_HINT:h2*/ true;
        }
      }
    }
  }
}
