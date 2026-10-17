//! Q04 checks — synthetic tools fixture (Reference Solution): the twin of
//! verus/q/q04_proof_craft/src/tests.rs, every value slot enabled.
use super::*;

// item: Q04.P10v S1 value
// **P10.** What does `twice(21)` return? Answer form: numeral
#[test]
fn p10() {
    assert_eq!(twice(21), 42);
}
