// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"},{"name":"i5"},{"name":"i6"},{"name":"i7"},{"name":"i8"}]
// R12_SOURCE_SPANS: [{"symbol":"IncrementMatrix","start":4,"end":27}]
// R12 public task: dafnybench Dafny_Verify_tmp_tmphq7j0row_AI_agent_verify_examples_IncrementMatrix.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method IncrementMatrix(a: array2<int>)
    modifies a
    ensures forall i, j :: 0 <= i < a.Length0 && 0 <= j < a.Length1 ==> a[i,j] == old(a[i,j]) + 1
{
    var m := 0;
    while m != a.Length0
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
    {
        var n := 0;
        while n != a.Length1
            invariant /*R12_HINT:i4*/ true
            invariant /*R12_HINT:i5*/ true
            invariant /*R12_HINT:i6*/ true
            invariant /*R12_HINT:i7*/ true
            invariant /*R12_HINT:i8*/ true
        {
            a[m,n] := a[m,n] + 1;
            n := n + 1; 
        }
        m := m + 1; 
    }
}
