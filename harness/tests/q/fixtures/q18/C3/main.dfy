// Gate v2 fixture C3: the sum of the first n odd numbers.
module Gate2C3 {
  function OddSum(n: nat): nat
    decreases n
  {
    if n == 0 then 0 else (2 * n - 1) + OddSum(n - 1)
  }

  lemma OddSumSquare(n: nat)
    ensures OddSum(n) == n * n
    decreases n
  {
    if n > 0 {
      OddSumSquare(n - 1);
    }
  }
}
