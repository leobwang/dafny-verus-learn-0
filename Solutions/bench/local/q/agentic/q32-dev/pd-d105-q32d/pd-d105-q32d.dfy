// Topic (e) dev task pd-d105-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench dafny-synthesis_task_id_3.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method IsNonPrime(n: int) returns (result: bool)
    requires n >= 2
    ensures result <==> (exists k :: 2 <= k < n && n % k == 0)
{
    result := false;
    var i := 2;
    while i <= n/2
        invariant 2 <= i
        invariant result <==> (exists k :: 2 <= k < i && n % k == 0)
    {
        if n % i == 0
        {
            result := true;
            break;
        }
        i := i + 1;
    }
}