module TranscriptProbe {
  function Triple(x: nat): nat { 3 * x }

  lemma TripleGrows(x: nat)
    ensures x <= Triple(x)
  {
  }

  lemma TripleBelow(x: nat)
    ensures Triple(x) < 2 * x + 1
  {
  }
}
