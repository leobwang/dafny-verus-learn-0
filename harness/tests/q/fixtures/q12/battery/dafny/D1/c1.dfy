// Battery goal D1, candidate 1 (a whole file; it stands alone).
module Battery_D1 {
  const BASE: nat := 18446744073709551616

  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // A zero limb put below s shifts its value up by one limb.
  lemma ToNatZeroCons(s: seq<nat>)
    ensures ToNat([0] + s) == BASE * ToNat(s)
  {
    assert ([0] + s)[1..] == s;
  }
}
