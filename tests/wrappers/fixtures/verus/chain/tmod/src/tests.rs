//! Test fixture (tests/wrappers): tests outside verus! (Δ42).
use super::*;

#[test]
fn adds_two() {
    assert_eq!(add_two(3), 5);
}
