//! R02 references over layer A1 (PLAN §6.2: R02.H2v, R02.H3v): structural lemmas on
//! `node_count`, `nullable` and `backwards`. Module references, never layer code.
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;

verus! {

pub proof fn lemma_node_count_backwards(r: Re)
    ensures
        node_count(r) >= 1 && node_count(backwards(r)) == node_count(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_node_count_backwards(*a);
            lemma_node_count_backwards(*b);
        },
        Re::Cat(a, b) => {
            lemma_node_count_backwards(*a);
            lemma_node_count_backwards(*b);
        },
        Re::Star(a) => {
            lemma_node_count_backwards(*a);
        },
        _ => {},
    }
}

pub proof fn lemma_nullable_backwards(r: Re)
    ensures
        nullable(backwards(r)) == nullable(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_backwards(*a);
            lemma_nullable_backwards(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_backwards(*a);
            lemma_nullable_backwards(*b);
        },
        Re::Star(a) => {
            lemma_nullable_backwards(*a);
        },
        _ => {},
    }
}

} // verus!
