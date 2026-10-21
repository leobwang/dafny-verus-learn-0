// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"}]
// R12_SOURCE_SPANS: [{"symbol":"AllSequencesEqualLength","start":4,"end":23}]
// R12 public task: dafnybench dafny-synthesis_task_id_70.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method AllSequencesEqualLength(sequences: seq<seq<int>>) returns (result: bool)
    ensures result <==> forall i, j :: 0 <= i < |sequences| && 0 <= j < |sequences| ==> |sequences[i]| == |sequences[j]|
{
    if |sequences| == 0 {
        return true;
    }

    var firstLength := |sequences[0]|;
    result := true;

    for i := 1 to |sequences|
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        if |sequences[i]| != firstLength {
            result := false;
            break;
        }
    }
}