// Topic (e) course-local task cl-d9-twos-pos (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `TwosPos` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d9_twos_pos {
  function Twos(n: nat): nat
    decreases n
  {
    if n == 0 then 1 else 2 * Twos(n - 1)
  }

  // Every power of two is at least n + 1.
  lemma {:induction false} TwosPos(n: nat)
    ensures Twos(n) >= n + 1
    decreases n
  {
    if n > 0 {
      TwosPos(n - 1);
    }
  }
}
