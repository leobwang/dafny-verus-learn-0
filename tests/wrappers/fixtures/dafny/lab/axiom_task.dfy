// Test fixture (tests/wrappers): an invented lab task form that ships an
// assumption the done gate does not count (`assume {:axiom} false;`, the form
// of some public task sets before their transform). A delivery equal to it
// verifies with 0 holes and keeps every shipped lever; the lab gate's
// assumption audit (vaudit's rules, the user's decision D24) refuses it.
module {:disableNonlinearArithmetic} LabTask {
  function Count(n: nat): nat { if n == 0 then 0 else Count(n - 1) + 1 }

  lemma {:induction false} CountIsN(n: nat)
    ensures Count(n) == n
  {
    assume {:axiom} false;
  }
}
