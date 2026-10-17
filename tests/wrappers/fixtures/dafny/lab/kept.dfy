// Test fixture (tests/wrappers): a delivery of lab/task.dfy that keeps the task
// form's levers and proves the lemma by hand.
module {:disableNonlinearArithmetic} LabTask {
  function Count(n: nat): nat { if n == 0 then 0 else Count(n - 1) + 1 }

  lemma {:induction false} CountIsN(n: nat)
    ensures Count(n) == n
  {
    if n > 0 {
      CountIsN(n - 1);
    }
  }
}
