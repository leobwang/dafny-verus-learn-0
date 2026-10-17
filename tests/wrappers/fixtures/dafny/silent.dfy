// Wrapper fixture (tests/wrappers): Δ3's silent hole kinds. Each verifies with
// exit 0 and no warning; only the lint (and partly the audit) sees them.
module Fx_Silent {
  method NoEnsures(x: nat) returns (y: nat)

  lemma OnlyRequires(x: nat)
    requires x > 0

  function Oracle(x: nat): nat

  lemma {:axiom} Assumed(x: nat)
    ensures x > 100

  method AssumeAxiom(x: nat) returns (y: nat)
    ensures y > x
  {
    y := x;
    assume {:axiom} y > x;
  }

  method Forever()
    decreases *
  {
    while true
      decreases *
    {
    }
  }

  method ExpectOutsideTest(x: nat) returns (y: nat)
    ensures y > 100
  {
    y := x;
    expect y > 100;
  }

  trait Shape {
    lemma TraitHole(x: nat)
      ensures x > 100
  }
}

abstract module Fx_SilentAbstract {
  lemma AbstractHole(x: nat)
    ensures x > 100
}
