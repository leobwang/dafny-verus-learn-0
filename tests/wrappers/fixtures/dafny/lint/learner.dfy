// Wrapper fixture (tests/wrappers): learner-mode lint cases. A trailing
// expect comment marks every line that must produce a finding, with its kinds;
// strings and comments that mention {:axiom}, assume or expect produce none.
include "elsewhere.dfy"  // expect: include

module {:options "--function-syntax:4"} Fx_Lint {  // expect: options-attribute
  const Unset: nat  // expect: uninitialized-const
  const Set: nat := 3

  function Oracle(x: nat): nat  // expect: bodyless-silent

  function Spec(x: nat): nat
    ensures Spec(x) >= x

  lemma Hole(x: nat)
    ensures x >= 0

  lemma TwoEnsures(x: nat)  // expect: multi-ensures-hole
    ensures x >= 0
    ensures x + 1 > 0

  lemma OnlyRequires(x: nat)  // expect: bodyless-silent
    requires x > 0

  method NoEnsures(x: nat) returns (y: nat)  // expect: bodyless-silent

  lemma {:axiom} Ax(x: nat) ensures x > 9  // expect: axiom-attribute

  @Axiom  // expect: axiom-attribute
  lemma Ax2(x: nat) ensures x > 9

  lemma {:verify false} Off() ensures true {}  // expect: verify-false

  @VerifyOnly  // expect: verify-only
  lemma Only() ensures true {}

  method {:extern} Ext(x: int) returns (y: int)  // expect: extern bodyless-silent

  lemma {:resource_limit 9000000} Costly() ensures true {}  // expect: resource-attribute

  lemma {:focus} Focused() ensures true {}  // expect: attribute-not-allowed

  lemma {:induction false} {:fuel Spec, 2} Levers(x: nat) ensures x >= 0 {}

  method Statements(x: nat) returns (y: nat)
    ensures y == x
  {
    y := x;
    assume y == x;
    assume {:axiom} y >= 0;  // expect: assume-axiom
    assert {:only} y >= 0;  // expect: verify-only
    expect y >= 0;  // expect: expect-outside-test
    var s := "assume {:axiom} expect include";
    // assume {:axiom} false; expect true; {:verify false}
    /* lemma {:axiom} Hidden() ensures false */
  }

  method Spin()
    decreases *  // expect: decreases-star
  {
    while true
      decreases *  // expect: decreases-star
    {
    }
  }

  method {:test} CurlyTest() {
    expect Set == 3;
  }

  @Test
  method AtTest() {
    expect Set == 3;
  }

  twostate lemma Labels(c: Cell)
    ensures old@Before(c.v) == c.v || true
  {
  }

  class Cell {
    var v: int
  }

  trait Shape {  // expect: trait
    lemma TraitHole(x: nat)  // expect: bodyless-abstract
      ensures x > 0
  }
}

abstract module Fx_LintAbstract {  // expect: abstract-module
  lemma AbstractHole(x: nat)  // expect: bodyless-abstract
    ensures x > 0
}
