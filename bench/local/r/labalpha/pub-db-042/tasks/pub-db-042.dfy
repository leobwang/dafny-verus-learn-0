// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"}]
// R12_SOURCE_SPANS: [{"symbol":"SharedElements","start":10,"end":28}]
// R12 public task: dafnybench dafny-synthesis_task_id_2.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
predicate InArray(a: array<int>, x: int)
    reads a
{
    exists i :: 0 <= i < a.Length && a[i] == x
}

method SharedElements(a: array<int>, b: array<int>) returns (result: seq<int>)
    // All elements in the output are in both a and b
    ensures forall x :: x in result ==> (InArray(a, x) && InArray(b, x))
    // The elements in the output are all different
    ensures forall i, j :: 0 <= i < j < |result| ==> result[i] != result[j]
{
    var res: seq<int> := [];
    for i := 0 to a.Length
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        if InArray(b, a[i]) && a[i] !in res
        {
            res := res + [a[i]];
        }
    }
    result := res;
}