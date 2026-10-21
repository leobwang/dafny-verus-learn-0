// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"}]
// R12_SOURCE_SPANS: [{"symbol":"RotateRight","start":4,"end":18}]
// R12 public task: dafnybench dafny-synthesis_task_id_743.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method RotateRight(l: seq<int>, n: int) returns (r: seq<int>)
    requires n >= 0
    ensures |r| == |l|
    ensures forall i :: 0 <= i < |l| ==> r[i] == l[(i - n + |l|) % |l|]
{
    var rotated: seq<int> := [];
    for i := 0 to |l|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        rotated := rotated + [l[(i - n + |l|) % |l|]];
    }
    return rotated;
}