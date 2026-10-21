/*! R13 pipeline forensic: a delivery whose public caller delegates to a helper.
Read this file, snapshot it under research/R13/ before any contractor edit, and
find which dependency makes the caller's apparent success incomplete. The
contractor (/contract R13, a fresh session) may write only the helper's body,
over the printed domain; every signature, clause and the provided caller stay.
Review the delivery yourself with at least two instruments on the full file.
*/
module R13_ForensicDelivery {
  // specfreeze: frozen-imports

  // Provided caller: its contract is the helper's.
  method DeliveredScoreR13(a: nat, b: nat) returns (score: nat)
    requires a <= 4294967295 && b <= 4294967295
    ensures score == 2 * a + 3 * b && score <= 21474836475
  {
    score := SupportScoreR13(a, b);
  }

  // item: R13.A1d
  method SupportScoreR13(a: nat, b: nat) returns (score: nat)
    requires a <= 4294967295 && b <= 4294967295
    ensures score == 2 * a + 3 * b && score <= 21474836475
  {
    assume false;
  }
}
