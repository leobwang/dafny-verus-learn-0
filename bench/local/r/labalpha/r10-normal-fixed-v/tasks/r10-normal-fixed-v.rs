// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b"],"kind":"calls","callees":["normal_fixed_r10"]},{"name":"c2","identifiers":["a","b"],"kind":"calls","callees":["normal_fixed_r10"]},{"name":"c3","identifiers":["a"],"kind":"calls","callees":["normal_fixed_r10"]}]
// R12_SOURCE_SPANS: [{"symbol":"normal_fixed_r10","start":77,"end":95}]
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

// The task (R10.H3 normal_fixed_r10): a normal regex is a fixed point of norm.
proof fn normal_fixed_r10(r:Re)
 requires is_norm(r),
 ensures norm(r)==r,
 decreases r,
{
 reveal_with_fuel(norm,2);
 match r {
  Re::Alt(a,b)=>{
   /*R12_CALLS:c1*/
  },
  Re::Cat(a,b)=>{
   /*R12_CALLS:c2*/
  },
  Re::Star(a)=>{
   /*R12_CALLS:c3*/
  },
  _=>{},
 }
}

} // verus!
