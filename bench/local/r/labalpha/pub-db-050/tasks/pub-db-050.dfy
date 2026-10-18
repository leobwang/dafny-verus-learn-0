// R12_HINT_SITES: [{"name":"i1","identifiers":["DeepCopySeq","copy","i","k","newSeq","s","seq"]},{"name":"i2","identifiers":["DeepCopySeq","copy","i","k","newSeq","s","seq"]},{"name":"i3","identifiers":["DeepCopySeq","copy","i","k","newSeq","s","seq"]}]
// R12_SOURCE_SPANS: [{"symbol":"DeepCopySeq","start":4,"end":17}]
// R12 public task: dafnybench dafny-synthesis_task_id_307.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method DeepCopySeq(s: seq<int>) returns (copy: seq<int>)
    ensures |copy| == |s|
    ensures forall i :: 0 <= i < |s| ==> copy[i] == s[i]
{
    var newSeq: seq<int> := [];
    for i := 0 to |s|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        newSeq := newSeq + [s[i]];
    }
    return newSeq;
}