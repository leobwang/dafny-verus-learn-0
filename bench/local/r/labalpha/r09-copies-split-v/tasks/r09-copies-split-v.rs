// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_cat_eps_left"]},{"name":"c2","kind":"calls","callees":["lemma_cat_assoc"]},{"name":"c3","kind":"calls","callees":["lemma_copies_join_r09"]},{"name":"c4","kind":"calls","callees":["lemma_cat_right_context_r09"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_copies_join_r09","start":145,"end":160}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

pub open spec fn matches(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches(*a, s) || matches(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            ),
    }
}

// Provided definitions: rg_re_a3 (layer A3), counted repetition, copied verbatim.
pub open spec fn copies(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(r), Box::new(copies(r, (k - 1) as nat)))
    }
}

pub open spec fn copies_up_to(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(r), Box::new(copies_up_to(r, (k - 1) as nat)))))
    }
}

// Provided fact (rg_re_a1b::lemma_cat_eps_left), complete.
pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s),
{
    let e = Re::Cat(Box::new(Re::Eps), Box::new(r));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(0, 0) =~= Seq::<char>::empty());
        assert(matches(Re::Eps, s.subrange(0, 0)));
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(Re::Eps, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            );
        assert(s.subrange(0, i).len() == 0);
    }
}

// Provided fact (rg_re_a1b::lemma_cat_assoc), complete.
pub proof fn lemma_cat_assoc(a: Re, b: Re, c: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s)
            <==> matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
{
    let ab = Re::Cat(Box::new(a), Box::new(b));
    let bc = Re::Cat(Box::new(b), Box::new(c));
    if matches(Re::Cat(Box::new(ab), Box::new(c)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(ab, #[trigger] s.subrange(0, i)) && matches(
                c,
                s.subrange(i, s.len() as int),
            );
        let u = s.subrange(0, i);
        let k = choose|k: int|
            0 <= k <= u.len() && matches(a, #[trigger] u.subrange(0, k)) && matches(
                b,
                u.subrange(k, u.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, i - k));
        assert(v.subrange(i - k, v.len() as int) =~= s.subrange(i, s.len() as int));
        assert(matches(bc, v));
    }
    if matches(Re::Cat(Box::new(a), Box::new(bc)), s) {
        let k = choose|k: int|
            0 <= k <= s.len() && matches(a, #[trigger] s.subrange(0, k)) && matches(
                bc,
                s.subrange(k, s.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        let j = choose|j: int|
            0 <= j <= v.len() && matches(b, #[trigger] v.subrange(0, j)) && matches(
                c,
                v.subrange(j, v.len() as int),
            );
        let u = s.subrange(0, k + j);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, j));
        assert(v.subrange(j, v.len() as int) =~= s.subrange(k + j, s.len() as int));
        assert(matches(ab, u));
    }
}

// Provided fact (R09 reference helper lemma_cat_right_context_r09), complete.
proof fn lemma_cat_right_context_r09(a:Re,b:Re,c:Re,s:Seq<char>)
 requires forall|t:Seq<char>| matches(b,t)==matches(c,t),
 ensures matches(Re::Cat(Box::new(a),Box::new(b)),s)==matches(Re::Cat(Box::new(a),Box::new(c)),s),
{
 if matches(Re::Cat(Box::new(a),Box::new(b)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(b,s.subrange(i,s.len() as int));
  assert(matches(c,s.subrange(i,s.len() as int)));
 }
 if matches(Re::Cat(Box::new(a),Box::new(c)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(c,s.subrange(i,s.len() as int));
  assert(matches(b,s.subrange(i,s.len() as int)));
 }
}

// The task (R09.W4 copies join): a + b copies split into a then b copies.
proof fn lemma_copies_join_r09(r:Re,a:nat,b:nat,s:Seq<char>)
 ensures matches(copies(r,a+b),s)==matches(Re::Cat(Box::new(copies(r,a)),Box::new(copies(r,b))),s),
 decreases a,
{
 if a==0 {
  /*R12_CALLS:c1*/
 } else {
  let aa=(a-1) as nat;
  /*R12_CALLS:c2*/
  let x=copies(r,aa+b);let y=Re::Cat(Box::new(copies(r,aa)),Box::new(copies(r,b)));
  assert forall|t:Seq<char>| matches(x,t)==matches(y,t) by {
   /*R12_CALLS:c3*/
  }
  /*R12_CALLS:c4*/
 }
}

} // verus!
