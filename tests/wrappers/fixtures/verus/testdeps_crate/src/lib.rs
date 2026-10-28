// Fixture (D98, Δ316): a compiled test that uses the pinned `regex` dev-dependency,
// and a plain-Rust hole inside #[cfg(test)] (`todo!("<item>")`, hole kind test-todo).
use vstd::prelude::*;

verus! {

pub fn double(x: u32) -> (r: u32)
    requires
        x < 1000,
    ensures
        r == 2 * x,
{
    x + x
}

} // verus!

#[cfg(test)]
mod tests {
    use super::*;

    fn pattern_of(n: u32) -> String {
        todo!("FX.H2v")
    }

    #[test]
    fn regex_agrees() {
        let re = regex::Regex::new("^(?:a*)$").unwrap();
        assert!(re.is_match("aaaa"));
        assert!(!re.is_match("ab"));
        assert_eq!(double(21), 42);
    }

    #[test]
    fn hole_panics() {
        assert_eq!(pattern_of(2), "aa");
    }
}
