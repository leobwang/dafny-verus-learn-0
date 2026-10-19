// R12_HINT_SITES: [{"name":"h1","identifiers":["k","s"]},{"name":"h2","identifiers":["A2","InClass","cc","s","i","k"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.ClassCoversR13","start":20,"end":34}]
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

  // The task (R13.H2 ClassCoversR13): every character of s lies in the class cc, a verified loop over A2's class API.
  method ClassCoversR13(cc: A2.CharClass, s: seq<char>) returns (b: bool)
    ensures b == (forall i | 0 <= i < |s| :: A2.InClass(cc, s[i]))
  {
    var k := 0;
    while k < |s|
      invariant /*R12_HINT:h1*/ true
      invariant /*R12_HINT:h2*/ true
    {
      if !A2.ClassMember(cc, s[k]) {
        return false;
      }
      k := k + 1;
    }
    return true;
  }
}
