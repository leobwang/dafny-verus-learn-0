/*! # Q04 checks — synthetic tools fixture (Reference Solution): the twin of
    dafny/checks/Q04_checks.dfy, every value slot enabled. */
module Q04_Checks {
  import opened QG_L1_BigNat

  function Twice(n: nat): nat { n + n }

  // item: Q04.P8d S1 value
  // **P8.** What does `Twice(21)` return? Answer form: numeral
  method {:test} P8() {
    expect Twice(21) == 42;
  }

  // item: Q04.P9d S1 value
  // **P9.** What does `Twice(0)` return? Answer form: numeral
  method {:test} P9() {
    expect Twice(0) == 0;
  }
}
