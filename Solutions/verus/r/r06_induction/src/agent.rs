/* CONTRACT — R06 decomposer, R-v0
goal: prove the one top statement by decomposition, preserving its contract
allowed-files:
  - verus/r/r06_induction/src/agent.rs
acceptance:
  - first add each new helper as a typed hole; rerun green with only leaf holes before proving a helper
  - after every edit scripts/vcheck verus/r/r06_induction/src/agent.rs shows no error; holes are allowed only until the final delivery
  - scripts/vcheck --gate verus/r/r06_induction/src/agent.rs exits 0 with zero counted holes on the whole file
  - scripts/specfreeze --against <snapshot> verus/r/r06_induction/src/agent.rs keeps the original top statement unchanged
  - scripts/vaudit verus/r/r06_induction/src/agent.rs reports no finding; no new assumptions or weakened claims
  - retain the transcript, each green leaf stage and the delivered dependency tree
*/
/* R06 decomposer (Reference Solution). Save the original snapshot before /contract R06.
A1/A1b only; no earlier learner file is imported. */
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
verus! {


pub proof fn lemma_backwards_str_append(u: Seq<char>,v: Seq<char>)
    ensures backwards_str(u+v) == backwards_str(v)+backwards_str(u),
    decreases u.len(),
{
    if u.len() == 0 {
        assert(u+v =~= v);
    } else {
        assert((u+v).subrange(1,(u+v).len() as int) =~= u.subrange(1,u.len() as int)+v);
        assert((u+v)[0] == u[0]);
        lemma_backwards_str_append(u.subrange(1,u.len() as int),v);
        assert((backwards_str(v)+backwards_str(u.subrange(1,u.len() as int)))+seq![u[0]] =~= backwards_str(v)+(backwards_str(u.subrange(1,u.len() as int))+seq![u[0]]));
    }
}

pub proof fn lemma_backwards_str_involution(s: Seq<char>)
    ensures backwards_str(backwards_str(s)) == s,
    decreases s.len(),
{
    if s.len() > 0 {
        let tail=s.subrange(1,s.len() as int);
        lemma_backwards_str_append(backwards_str(tail),seq![s[0]]);
        assert(seq![s[0]].subrange(1,1) =~= Seq::<char>::empty());
        assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
        assert(backwards_str(seq![s[0]]) == backwards_str(seq![s[0]].subrange(1,1))+seq![s[0]]);
        assert(backwards_str(seq![s[0]]) =~= seq![s[0]]);
        lemma_backwards_str_involution(tail);
        assert(s =~= seq![s[0]]+tail);
    }
}

pub proof fn lemma_backwards_involution(r: Re)
    ensures backwards(backwards(r)) == r,
    decreases r,
{
    match r {
        Re::Alt(a,b) => { lemma_backwards_involution(*a);lemma_backwards_involution(*b); },
        Re::Cat(a,b) => { lemma_backwards_involution(*a);lemma_backwards_involution(*b); },
        Re::Star(a) => { lemma_backwards_involution(*a); },
        _ => { },
    }
}

pub proof fn lemma_backwards_sound(r: Re,s: Seq<char>)
    requires matches(r,s),
    ensures matches(backwards(r),backwards_str(s)),
    decreases r,s.len(),
{
    match r {
        Re::Empty => { },
        Re::Eps => { assert(s =~= Seq::<char>::empty()); },
        Re::Chr(c) => {
            assert(s.len() == 1 && s[0] == c);
            assert(s.subrange(1,s.len() as int) =~= Seq::<char>::empty());
            assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
            assert(backwards_str(s) == backwards_str(s.subrange(1,s.len() as int))+seq![s[0]]);
            assert(backwards_str(s) =~= seq![c]);
        },
        Re::Alt(a,b) => {
            if matches(*a,s) { lemma_backwards_sound(*a,s); }
            else { lemma_backwards_sound(*b,s); }
        },
        Re::Cat(a,b) => {
            let i=choose|i:int| 0 <= i <= s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(*b,s.subrange(i,s.len() as int));
            let u=s.subrange(0,i);let v=s.subrange(i,s.len() as int);
            lemma_backwards_sound(*a,u);lemma_backwards_sound(*b,v);
            assert(s =~= u+v);
            lemma_backwards_str_append(u,v);
            let w=backwards_str(s);let j=backwards_str(v).len() as int;
            assert(w.subrange(0,j) =~= backwards_str(v));
            assert(w.subrange(j,w.len() as int) =~= backwards_str(u));
        },
        Re::Star(a) => {
            if s.len() > 0 {
                let i=choose|i:int| 1 <= i <= s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(r,s.subrange(i,s.len() as int));
                let u=s.subrange(0,i);let v=s.subrange(i,s.len() as int);
                lemma_backwards_sound(*a,u);
                lemma_star_one(backwards(*a),backwards_str(u));
                lemma_backwards_sound(r,v);
                lemma_star_concat(backwards(*a),backwards_str(v),backwards_str(u));
                assert(s =~= u+v);
                lemma_backwards_str_append(u,v);
            } else {
                assert(backwards_str(s) =~= Seq::<char>::empty());
            }
        },
    }
}

// item: R06.A1v
pub proof fn lemma_backwards_correct(r: Re,s: Seq<char>)
    ensures matches(backwards(r),backwards_str(s)) <==> matches(r,s),
{
    if matches(r,s) { lemma_backwards_sound(r,s); }
    if matches(backwards(r),backwards_str(s)) {
        lemma_backwards_sound(backwards(r),backwards_str(s));
        lemma_backwards_involution(r);
        lemma_backwards_str_involution(s);
    }
}
}

/* DECOMPOSITION — learner-owned,22 min after the run.
   Draw helper nodes and caller edges. For every helper state its job and the
   transcript step when it first appeared as a hole. Mark any edit after which
   verification was not green, and the final full gate's count and scope.
   Delete one helper/step in an independent scratch copy to test necessity;
   record the actual observation without claiming unique minimality.
   AGENT DASHBOARD — goal / leaf stages / final gate / audit / freeze /
   transcript / correction: ...
*/
