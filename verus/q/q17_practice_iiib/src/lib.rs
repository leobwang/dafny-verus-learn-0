//! # Q17 — Practice III-B: the Verus half (Exercises)
//!
//! Imports: the vstd prelude, nothing else. The crate depends on the given BigNat spine
//! crates `qg_bignat_l1`–`qg_bignat_l7`, as every crate of the tier does; Q17 uses none of
//! them. The crate's one exercise module is src/perm.rs (the module `perm`, declared
//! below), which also uses vstd's permissioned cells.
//!
//! How to work the crate: H2 in src/perm.rs, after H1 (the Dafny file's header,
//! dafny/Q/Q17_PracticeIIIB/std/Q17_PracticeIIIB.dfy, gives the module's order).
//! Done = `scripts/vcheck --gate verus/q/q17_practice_iiib` prints only the summary line
//! and exits 0, `scripts/vaudit verus/q/q17_practice_iiib` reports no finding, AND
//! `scripts/firsttry.sh Q17 --report --strict` exits 0. The crate's gate covers this file
//! and src/perm.rs together.
//!
//! This file ships with no hole and no item; src/perm.rs ships 2 holes.
#![allow(unused_imports)]
use vstd::prelude::*;

mod perm;

verus! {

} // verus!
