/* CONTRACT
goal: make this file verify by repairing its four planted bugs, each with a one-line body edit
allowed-files:
  - verus/r/r01_hello/src/agent.rs
acceptance:
  - `scripts/vcheck --gate verus/r/r01_hello/src/agent.rs` exits 0 and prints only the summary line
  - `git diff` changes only body lines: no signature, requires, ensures, decreases, heading or doc comment changed
  - every fix is one changed or added line per bug
  - re-verify after every edit with `scripts/vcheck verus/r/r01_hello/src/agent.rs`, never two edits between runs
  - zero tool-counted holes and no new assume, admit, external_body or verification attribute
  - `scripts/vaudit --compare expected/r01_hello_agent.audit verus/r/r01_hello/src/agent.rs` reports no difference
*/
//! R01 repairer, rung 1. Four independent bugs; zero holes. Read every diagnostic.
//! Never mod-declared: the wrapper builds this standalone with the crate's dependencies.
//! After /contract, audit the transcript, diff and assumption report yourself.
#![allow(unused_imports)]
use vstd::prelude::*;
verus! {

// item: R01.A1v
// ### Bug 1
/// Return the character at i, without wrapping or substituting another position.
fn pick_char(s: &Vec<char>, i: usize) -> (c: char)
    requires
        i < s.len(),
    ensures
        c == s@[i as int],
{
    s[(i + 1) % s.len()]
}

// ### Bug 2
/// Reserve the successor when it fits; keep MAX unchanged. No wrapping is allowed.
fn reserve_successor(n: u32) -> (r: u32)
    ensures
        if n < u32::MAX { r == n + 1 } else { r == n },
{
    if n <= u32::MAX {
        n + 1
    } else {
        n
    }
}

spec fn walk_length(s: Seq<char>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        1 + walk_length(s.drop_first())
    }
}

// ### Bug 3
/// Establish that walking the sequence visits every character.
proof fn lemma_walk_length_sound(s: Seq<char>)
    ensures
        walk_length(s) == s.len(),
    decreases s.len(),
{
    assert(walk_length(Seq::<char>::empty()) == 0);
    if s.len() == 1 {
        assert(s.drop_first() =~= Seq::<char>::empty());
    }
    if s.len() > 1 {
        lemma_walk_length_sound(s.subrange(0, s.len() - 1));
    }
}

// ### Bug 4
/// Room for these characters and one terminator, when that sum fits.
fn room_for_terminator(s: &Vec<char>) -> (n: usize)
    requires
        s.len() < usize::MAX,
    ensures
        n == s.len() + 1,
{
    s.len()
}

} // verus!
// TRANSCRIPT AUDIT: re-verified after each edit? only bodies? one line per bug? ...
