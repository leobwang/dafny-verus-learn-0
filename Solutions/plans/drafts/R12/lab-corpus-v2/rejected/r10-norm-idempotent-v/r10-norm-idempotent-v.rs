// R12_HINT_SITES: [{"name":"c1","identifiers":["norm","r"],"kind":"calls","callees":["lemma_norm_shape_r10","normal_fixed_r10"]}]
// R12_SOURCE_SPANS: [{"symbol":"norm_idempotent_r10","start":117,"end":121}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1) and rg_re_a4 (layer A4), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

pub open spec fn mk_alt(a: Re, b: Re) -> Re {
    if a is Empty {
        b
    } else if b is Empty {
        a
    } else if a == b {
        a
    } else {
        Re::Alt(Box::new(a), Box::new(b))
    }
}

pub open spec fn mk_cat(a: Re, b: Re) -> Re {
    if a is Empty || b is Empty {
        Re::Empty
    } else if a is Eps {
        b
    } else if b is Eps {
        a
    } else {
        Re::Cat(Box::new(a), Box::new(b))
    }
}

pub open spec fn mk_star(a: Re) -> Re {
    if a is Empty || a is Eps {
        Re::Eps
    } else if a is Star {
        a
    } else {
        Re::Star(Box::new(a))
    }
}

/// The normal form the smart constructors maintain.
pub open spec fn is_norm(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Alt(a, b) => !(*a is Empty) && !(*b is Empty) && *a != *b && is_norm(*a) && is_norm(*b),
        Re::Cat(a, b) => !(*a is Empty) && !(*b is Empty) && !(*a is Eps) && !(*b is Eps) && is_norm(
            *a,
        ) && is_norm(*b),
        Re::Star(a) => !(*a is Empty) && !(*a is Eps) && !(*a is Star) && is_norm(*a),
        _ => true,
    }
}

pub open spec fn norm(r:Re)->Re
 decreases r,
{
 match r {
  Re::Empty=>Re::Empty,Re::Eps=>Re::Eps,Re::Chr(c)=>Re::Chr(c),
  Re::Alt(a,b)=>mk_alt(norm(*a),norm(*b)),
  Re::Cat(a,b)=>mk_cat(norm(*a),norm(*b)),
  Re::Star(a)=>mk_star(norm(*a)),
 }
}

// Provided facts (rg_re_a4 shape lemmas), complete, copied verbatim.
pub proof fn lemma_alt_shape_r10(a:Re,b:Re)
 requires is_norm(a),is_norm(b),
 ensures is_norm(mk_alt(a,b)),
{}
pub proof fn lemma_cat_shape_r10(a:Re,b:Re)
 requires is_norm(a),is_norm(b),
 ensures is_norm(mk_cat(a,b)),
{}
pub proof fn lemma_star_shape_r10(a:Re)
 requires is_norm(a),
 ensures is_norm(mk_star(a)),
{}
pub proof fn lemma_norm_shape_r10(r:Re)
 ensures is_norm(norm(r)),
 decreases r,
{
 match r {
  Re::Alt(a,b)=>{lemma_norm_shape_r10(*a);lemma_norm_shape_r10(*b);lemma_alt_shape_r10(norm(*a),norm(*b));},
  Re::Cat(a,b)=>{lemma_norm_shape_r10(*a);lemma_norm_shape_r10(*b);lemma_cat_shape_r10(norm(*a),norm(*b));},
  Re::Star(a)=>{lemma_norm_shape_r10(*a);lemma_star_shape_r10(norm(*a));},
  _=>{},
 }
}

// Provided fact (R10.H3 normal_fixed_r10, reference proof), complete.
proof fn normal_fixed_r10(r:Re)
 requires is_norm(r),
 ensures norm(r)==r,
 decreases r,
{
 reveal_with_fuel(norm,2);
 match r {
  Re::Alt(a,b)=>{normal_fixed_r10(*a);normal_fixed_r10(*b);},
  Re::Cat(a,b)=>{normal_fixed_r10(*a);normal_fixed_r10(*b);},
  Re::Star(a)=>{normal_fixed_r10(*a);},
  _=>{},
 }
}

// The task (R10 norm_idempotent_r10): normalization is idempotent.
proof fn norm_idempotent_r10(r:Re)
 ensures norm(norm(r))==norm(r),
{
 /*R12_CALLS:c1*/
}

} // verus!
