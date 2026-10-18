// R12_HINT_SITES: [{"name":"i1","identifiers":["Interleave","i","k","r","s1","s2","s3","seq"]},{"name":"i2","identifiers":["Interleave","i","k","r","s1","s2","s3","seq"]},{"name":"i3","identifiers":["Interleave","i","k","r","s1","s2","s3","seq"]}]
// R12_SOURCE_SPANS: [{"symbol":"Interleave","start":4,"end":17}]
// R12 public task: dafnybench dafny-synthesis_task_id_578.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method Interleave(s1: seq<int>, s2: seq<int>, s3: seq<int>) returns (r: seq<int>)
    requires |s1| == |s2| && |s2| == |s3|
    ensures |r| == 3 * |s1|
    ensures forall i :: 0 <= i < |s1| ==> r[3*i] == s1[i] && r[3*i + 1] == s2[i] && r[3*i + 2] == s3[i]
{
    r := [];
    for i := 0 to |s1|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        r := r + [s1[i], s2[i], s3[i]];
    }
}