//! # Q18 — the capstone's command-line tool `bignat` (learner-owned; the ship step)
//!
//! The crate's binary target (verus/q/q18_practice_iiic/Cargo.toml's `[[bin]]`, generated).
//! At the ship step (the chapter's §1) this file reads `bignat add|sub|mul|div|cmp <a> <b>`,
//! calls the matching fn of src/lib.rs's ENTRY POINTS section and prints the result. It is
//! code outside `verus!`: trusted, never verified, so list what it trusts (the parsing of
//! its arguments, the printing of its results) in research/TRUST.md. Keep it thin: every
//! computation belongs to a verified entry point.
//!
//! Build and run it only through the pinned route (the same `verus` the gate runs, with
//! `--compile`, under the memory cap):
//!
//!     scripts/vcheck --bin verus/q/q18_practice_iiic -- <command> <a> <b>
//!
//! As shipped it prints a usage line and exits 2. Verus compiles this file as a crate root,
//! so it keeps the vstd prelude import below; `use q18_practice_iiic::*;` brings the
//! library's entry points.
#![allow(unused_imports)]
use vstd::prelude::*;

fn main() {
    eprintln!("usage: bignat add|sub|mul|div|cmp <a> <b> (not written yet: the ship step)");
    std::process::exit(2);
}
