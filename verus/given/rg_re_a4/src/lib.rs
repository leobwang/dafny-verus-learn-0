//! A4 frozen normal-form definitions (PROVIDED, frozen). Do not open before R02, R03, R05 and
//! R06 are done (it depends on A1b and A2, which re-supply their answers); semantics are later work.
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
pub open spec fn equiv(a: Re, b: Re) -> bool {
    forall|s: Seq<char>| #[trigger] matches(a, s) == matches(b, s)
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
pub fn eq_re(a: &Re, b: &Re) -> (e: bool)
    ensures
        e == (*a == *b),
    decreases a,
{
    match (a, b) {
        (Re::Empty, Re::Empty) => true,
        (Re::Eps, Re::Eps) => true,
        (Re::Chr(c), Re::Chr(d)) => *c == *d,
        (Re::Alt(a1, a2), Re::Alt(b1, b2)) => eq_re(a1, b1) && eq_re(a2, b2),
        (Re::Cat(a1, a2), Re::Cat(b1, b2)) => eq_re(a1, b1) && eq_re(a2, b2),
        (Re::Star(a1), Re::Star(b1)) => eq_re(a1, b1),
        _ => false,
    }
}

pub fn mk_alt_exec(a: Re, b: Re) -> (out: Re)
    ensures
        out == mk_alt(a, b),
{
    if let Re::Empty = a {
        b
    } else if let Re::Empty = b {
        a
    } else if eq_re(&a, &b) {
        a
    } else {
        Re::Alt(Box::new(a), Box::new(b))
    }
}

pub fn mk_cat_exec(a: Re, b: Re) -> (out: Re)
    ensures
        out == mk_cat(a, b),
{
    if let Re::Empty = a {
        Re::Empty
    } else if let Re::Empty = b {
        Re::Empty
    } else if let Re::Eps = a {
        b
    } else if let Re::Eps = b {
        a
    } else {
        Re::Cat(Box::new(a), Box::new(b))
    }
}

pub fn mk_star_exec(a: Re) -> (out: Re)
    ensures
        out == mk_star(a),
{
    match a {
        Re::Empty => Re::Eps,
        Re::Eps => Re::Eps,
        Re::Star(x) => Re::Star(x),
        _ => Re::Star(Box::new(a)),
    }
}
pub open spec fn nderiv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => mk_alt(nderiv(*a, c), nderiv(*b, c)),
        Re::Cat(a, b) => if nullable(*a) {
            mk_alt(mk_cat(nderiv(*a, c), *b), nderiv(*b, c))
        } else {
            mk_cat(nderiv(*a, c), *b)
        },
        Re::Star(a) => mk_cat(nderiv(*a, c), r),
    }
}

/// The normalizing derivative has the derivative's language and keeps normal forms.

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
pub proof fn lemma_nderiv_shape_r10(r:Re,c:char)
 requires is_norm(r),
 ensures is_norm(nderiv(r,c)),
 decreases r,
{
 match r {
  Re::Alt(a,b)=>{
   lemma_nderiv_shape_r10(*a,c);lemma_nderiv_shape_r10(*b,c);
   lemma_alt_shape_r10(nderiv(*a,c),nderiv(*b,c));
  },
  Re::Cat(a,b)=>{
   lemma_nderiv_shape_r10(*a,c);lemma_cat_shape_r10(nderiv(*a,c),*b);
   if nullable(*a) {lemma_nderiv_shape_r10(*b,c);lemma_alt_shape_r10(mk_cat(nderiv(*a,c),*b),nderiv(*b,c));}
  },
  Re::Star(a)=>{lemma_nderiv_shape_r10(*a,c);lemma_cat_shape_r10(nderiv(*a,c),r);},
  _=>{},
 }
}

// A provided runtime predicate, not the normalizer implementation.
pub fn is_normal_exec_r10(r:&Re)->(b:bool)
 ensures b==is_norm(*r),
 decreases r,
{
 match r {
  Re::Alt(a,b)=>{
   let left_ok=match &**a {Re::Empty=>false,_=>true};
   let right_ok=match &**b {Re::Empty=>false,_=>true};
   left_ok && right_ok && !eq_re(a,b) && is_normal_exec_r10(a) && is_normal_exec_r10(b)
  },
  Re::Cat(a,b)=>{
   let left_ok=match &**a {Re::Empty|Re::Eps=>false,_=>true};
   let right_ok=match &**b {Re::Empty|Re::Eps=>false,_=>true};
   left_ok && right_ok && is_normal_exec_r10(a) && is_normal_exec_r10(b)
  },
  Re::Star(a)=>{
   let child_ok=match &**a {Re::Empty|Re::Eps|Re::Star(_)=>false,_=>true};
   child_ok && is_normal_exec_r10(a)
  },
  _=>true,
 }
}
// The type boundary exports shape and exact views, not language preservation.
pub struct NormRe {r:Re}
impl NormRe {
 #[verifier::type_invariant]
 spec fn normal_shape(&self)->bool {is_norm(self.r)}
 pub closed spec fn re(self)->Re {self.r}
 pub fn shape_view_r10(&self)
  ensures is_norm(self.re()),
 {proof {use_type_invariant(self);}}
 pub fn from_normal_r10(r:Re)->(out:NormRe)
  requires is_norm(r),
  ensures out.re()==r,
 {NormRe {r}}
 pub fn into_pattern_r10(self)->(out:Re)
  ensures out==self.re(),is_norm(out),
 {proof {use_type_invariant(&self);} self.r}
 pub fn pattern_ref_r10(&self)->(out:&Re)
  ensures *out==self.re(),is_norm(*out),
 {proof {use_type_invariant(self);} &self.r}
}
// Definitions only: no soundness, completeness, executable checker or search.
pub enum Derivation {
 DEps,DChr,DAltL(Box<Derivation>),DAltR(Box<Derivation>),
 DCat(usize,Box<Derivation>,Box<Derivation>),DStarNil,DStarCons(usize,Box<Derivation>,Box<Derivation>),
}
pub open spec fn valid_word_r10(d:Derivation,r:Re,s:Seq<char>)->bool
 decreases d,
{
 match d {
  Derivation::DEps=>r is Eps && s.len()==0,
  Derivation::DChr=>r is Chr && s==seq![r->Chr_0],
  Derivation::DAltL(d1)=>r is Alt && valid_word_r10(*d1,*r->Alt_0,s),
  Derivation::DAltR(d1)=>r is Alt && valid_word_r10(*d1,*r->Alt_1,s),
  Derivation::DCat(k,d1,d2)=>r is Cat && k<=s.len() && valid_word_r10(*d1,*r->Cat_0,s.take(k as int)) && valid_word_r10(*d2,*r->Cat_1,s.skip(k as int)),
  Derivation::DStarNil=>r is Star && s.len()==0,
  Derivation::DStarCons(k,d1,d2)=>r is Star && 0<k<=s.len() && valid_word_r10(*d1,*r->Star_0,s.take(k as int)) && valid_word_r10(*d2,r,s.skip(k as int)),
 }
}
pub open spec fn valid(d:Derivation,r:Re,s:Seq<char>,lo:int,hi:int)->bool {
 0<=lo<=hi<=s.len() && valid_word_r10(d,r,s.subrange(lo,hi))
}
pub proof fn lemma_cat_cong(a1: Re, a2: Re, b1: Re, b2: Re, s: Seq<char>)
    requires
        equiv(a1, a2),
        equiv(b1, b2),
    ensures
        matches(Re::Cat(Box::new(a1), Box::new(b1)), s) == matches(Re::Cat(Box::new(a2), Box::new(b2)), s),
{
    if matches(Re::Cat(Box::new(a1), Box::new(b1)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a1, #[trigger] s.subrange(0, i)) && matches(
                b1,
                s.subrange(i, s.len() as int),
            );
        assert(matches(a2, s.subrange(0, i)) && matches(b2, s.subrange(i, s.len() as int)));
    }
    if matches(Re::Cat(Box::new(a2), Box::new(b2)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a2, #[trigger] s.subrange(0, i)) && matches(
                b2,
                s.subrange(i, s.len() as int),
            );
        assert(matches(a1, s.subrange(0, i)) && matches(b1, s.subrange(i, s.len() as int)));
    }
}

pub proof fn lemma_cat_cong_right_r10(a:Re,b1:Re,b2:Re,s:Seq<char>)
 requires equiv(b1,b2),
 ensures matches(Re::Cat(Box::new(a),Box::new(b1)),s)==matches(Re::Cat(Box::new(a),Box::new(b2)),s),
 {lemma_cat_cong(a,a,b1,b2,s);}
pub proof fn lemma_star_of_eps_r10(a:Re,s:Seq<char>)
 requires forall|t:Seq<char>| #[trigger] matches(a,t) ==> t.len()==0,
 ensures matches(Re::Star(Box::new(a)),s)==(s.len()==0),
{
 if s.len()>0 && matches(Re::Star(Box::new(a)),s) {
  let i=choose|i:int| 0<i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(Re::Star(Box::new(a)),s.subrange(i,s.len() as int));
  assert(s.subrange(0,i).len()==i);
 }
}
}
