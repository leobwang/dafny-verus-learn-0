// Battery goal D6, candidate 3 (a whole file; it stands alone).
module Battery_D6 {
  const BASE: nat := 18446744073709551616

  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // Two zero limbs put below s shift its value up by two limbs.
  lemma ToNatTwoZerosCons(s: seq<nat>)
    ensures ToNat([0, 0] + s) == BASE * (BASE * ToNat(s))
  {
    assume ToNat([0, 0] + s) == BASE * (BASE * ToNat(s));
  }
}
