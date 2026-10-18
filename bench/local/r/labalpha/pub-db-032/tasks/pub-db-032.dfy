// R12_HINT_SITES: [{"name":"i1","identifiers":["IsEven","IsEvenAtIndexEven","i","k","lst","result","seq"]},{"name":"i2","identifiers":["IsEven","IsEvenAtIndexEven","i","k","lst","result","seq"]}]
// R12_SOURCE_SPANS: [{"symbol":"IsEvenAtIndexEven","start":9,"end":23}]
// R12 public task: dafnybench dafny-synthesis_task_id_790.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
predicate IsEven(n: int)
{
    n % 2 == 0
}

method IsEvenAtIndexEven(lst: seq<int>) returns (result: bool)
    ensures result <==> forall i :: 0 <= i < |lst| ==> (IsEven(i) ==> IsEven(lst[i]))
{
    result := true;
    for i := 0 to |lst|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        if IsEven(i) && !IsEven(lst[i])
        {
            result := false;
            break;
        }
    }
}