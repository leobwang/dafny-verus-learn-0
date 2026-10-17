// Test fixture (tests/wrappers): a delivery of lab/task.dfy that switches
// automatic induction back on (the shipped `{:induction false}` is gone) and
// adds a VC-splitting lever.
module {:disableNonlinearArithmetic} LabTask {
  function Count(n: nat): nat { if n == 0 then 0 else Count(n - 1) + 1 }

  lemma {:vcs_split_on_every_assert} CountIsN(n: nat)
    ensures Count(n) == n
  {
  }
}
