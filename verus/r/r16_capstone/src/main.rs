//! # R16 — the capstone's command-line tool `rexc` (learner-owned; the ship step)
//!
//! The crate's binary target (verus/r/r16_capstone/Cargo.toml's `[[bin]]`, generated). At the
//! ship step (the chapter's §7) this file reads `rexc match <pattern> <text>`, parses the
//! pattern with A5's `frontend_r09` (an error prints its position), calls src/lib.rs's
//! `rexc_match` on the lowered regex and prints `match`, `no match` or `too large`; and
//! `rexc trust-report <delivery>` calls src/trust_report.rs (your solo gate, the chapter's
//! §9). It is code outside `verus!`: trusted, never verified, so list what it trusts (the
//! reading of its arguments, the printing of its answers) in research/TRUST.md. Keep it thin:
//! every computation on a regex belongs to a verified function.
//!
//! Build and run it only through the pinned route (the same `verus` the gate runs, with
//! `--compile`, under the memory cap):
//!
//!     scripts/vcheck --bin verus/r/r16_capstone -- match 'a(b|c)*' abcb
//!
//! As shipped it prints a usage line and exits 2. Verus compiles this file as a crate root,
//! so it keeps the vstd prelude import below; `use r16_capstone::*;` brings the library.
#![allow(unused_imports)]
use vstd::prelude::*;

mod trust_report;

fn main() {
    eprintln!("usage: rexc match <pattern> <text> | rexc trust-report <delivery> (not written yet: the ship step)");
    std::process::exit(2);
}
