// Test fixture (tests/wrappers): an invented lab task form for the lever check
// (QPLAN §30 Q63). The lemma ships bodyless with its induction switched off.
module {:disableNonlinearArithmetic} LabTask {
  function Count(n: nat): nat { if n == 0 then 0 else Count(n - 1) + 1 }

  lemma {:induction false} CountIsN(n: nat)
    ensures Count(n) == n
}
