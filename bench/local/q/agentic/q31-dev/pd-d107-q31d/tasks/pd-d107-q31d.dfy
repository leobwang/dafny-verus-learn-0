// Topic (e) dev task pd-d107-q31d (Q31, public; QPLAN §33.4, D76).
// Source: dafnybench dafny-synthesis_task_id_804.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
predicate IsEven(n: int)
{
    n % 2 == 0
}

method IsProductEven(a: array<int>) returns (result: bool)
    ensures result <==> exists i :: 0 <= i < a.Length && IsEven(a[i])
{
    result := false;
    for i := 0 to a.Length
    {
        if IsEven(a[i])
        {
            result := true;
            break;
        }
    }
}