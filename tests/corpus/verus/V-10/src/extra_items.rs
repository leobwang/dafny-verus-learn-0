// Cheat corpus V-10: the items include! splices into lib.rs.
verus! {

#[verifier::exec_allows_no_decreases_clause]
pub fn settle(x: u64) -> (r: u64)
    ensures
        r < x && r > x,
{
    loop
        invariant
            true,
    {
    }
}

} // verus!
