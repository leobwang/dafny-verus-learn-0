// Topic (e) dev task pd-d101-q31d (Q31, public; QPLAN §33.4, D76).
// Source: dafnybench dafny-synthesis_task_id_603.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method LucidNumbers(n: int) returns (lucid: seq<int>)
    requires n >= 0
    ensures forall i :: 0 <= i < |lucid| ==> lucid[i] % 3 == 0
    ensures forall i :: 0 <= i < |lucid| ==> lucid[i] <= n
    ensures forall i, j :: 0 <= i < j < |lucid| ==> lucid[i] < lucid[j]
{
    lucid := [];
    var i := 0;
    while i <= n
        invariant 0 <= i <= n + 1
        invariant forall k :: 0 <= k < |lucid| ==> lucid[k] % 3 == 0
        invariant forall k :: 0 <= k < |lucid| ==> lucid[k] <= i - 1
        invariant forall k, l :: 0 <= k < l < |lucid| ==> lucid[k] < lucid[l]
    {
        if i % 3 == 0 {
            lucid := lucid + [i];
        }
        i := i + 1;
    }
}