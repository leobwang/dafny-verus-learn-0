// R12_HINT_SITES: [{"name":"i1","identifiers":["FindEvenNumbers","IsEven","Length","arr","array","evenList","i","in","k","seq"]},{"name":"i2","identifiers":["FindEvenNumbers","IsEven","Length","arr","array","evenList","i","in","k","seq"]},{"name":"i3","identifiers":["FindEvenNumbers","IsEven","Length","arr","array","evenList","i","in","k","seq"]},{"name":"i4","identifiers":["FindEvenNumbers","IsEven","Length","arr","array","evenList","i","in","k","seq"]}]
// R12_SOURCE_SPANS: [{"symbol":"FindEvenNumbers","start":9,"end":27}]
// R12 public task: dafnybench dafny-synthesis_task_id_629.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
predicate IsEven(n: int)
{
    n % 2 == 0
}

method FindEvenNumbers(arr: array<int>) returns (evenList: seq<int>)
    // All numbers in the output are even and exist in the input 
    ensures forall i :: 0 <= i < |evenList| ==> IsEven(evenList[i]) && evenList[i] in arr[..]
    // All even numbers in the input are in the output
    ensures forall i :: 0 <= i < arr.Length && IsEven(arr[i]) ==> arr[i] in evenList
{
    evenList := [];
    for i := 0 to arr.Length
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
        invariant /*R12_HINT:i4*/ true
    {
        if IsEven(arr[i])
        {
            evenList := evenList + [arr[i]];
        }
    }
}
