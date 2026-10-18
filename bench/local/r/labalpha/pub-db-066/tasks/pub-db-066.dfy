// R12_HINT_SITES: [{"name":"i1","identifiers":["AddLists","a","b","i","k","result","seq"]},{"name":"i2","identifiers":["AddLists","a","b","i","k","result","seq"]},{"name":"i3","identifiers":["AddLists","a","b","i","k","result","seq"]}]
// R12_SOURCE_SPANS: [{"symbol":"AddLists","start":4,"end":17}]
// R12 public task: dafnybench dafny-synthesis_task_id_728.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method AddLists(a: seq<int>, b: seq<int>) returns (result: seq<int>)
    requires |a| == |b|
    ensures |result| == |a|
    ensures forall i :: 0 <= i < |result| ==> result[i] == a[i] + b[i]
{
    result := [];
    for i := 0 to |a|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        result := result + [a[i] + b[i]];
    }
}