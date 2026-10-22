// Topic (e) dev task pd-d101-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench dafny-synthesis_task_id_401.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method IndexWiseAddition(a: seq<seq<int>>, b: seq<seq<int>>) returns (result: seq<seq<int>>)
    requires |a| > 0 && |b| > 0
    requires |a| == |b|
    requires forall i :: 0 <= i < |a| ==> |a[i]| == |b[i]|
    ensures |result| == |a|
    ensures forall i :: 0 <= i < |result| ==> |result[i]| == |a[i]|
    ensures forall i :: 0 <= i < |result| ==> forall j :: 0 <= j < |result[i]| ==> result[i][j] == a[i][j] + b[i][j]
{
    result := [];
    for i := 0 to |a|
    {
        var subResult := [];
        for j := 0 to |a[i]|
        {
            subResult := subResult + [a[i][j] + b[i][j]];
        }
        result := result + [subResult];
    }
}