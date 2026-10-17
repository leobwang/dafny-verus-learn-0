// Test fixture (tests/wrappers): an invented lab task form that ships a
// verification lever the lever check allows because the task form ships it
// (`{:axiom}` on a bodyless lemma the task's lemma calls). A delivery equal to
// it verifies with 0 holes; the assumption audit reports the axiom, so the lab
// gate (D24) refuses it.
module {:disableNonlinearArithmetic} LabTask {
  function Count(n: nat): nat { if n == 0 then 0 else Count(n - 1) + 1 }

  lemma {:axiom} CountStep(n: nat)
    ensures Count(n) == n

  lemma {:induction false} CountIsN(n: nat)
    ensures Count(n) == n
  {
    CountStep(n);
  }
}
