// R12_HINT_SITES: [{"name":"c1","identifiers":["child","r","Alt_0","s"],"kind":"calls","callees":["sound_word_r11"]},{"name":"c2","identifiers":["child","r","Alt_1","s"],"kind":"calls","callees":["sound_word_r11"]},{"name":"c3","identifiers":["left","right","r","Cat_0","Cat_1","s","take","skip","k","as","int"],"kind":"calls","callees":["sound_word_r11"]},{"name":"c4","identifiers":["left","right","r","Star_0","s","take","skip","k","as","int"],"kind":"calls","callees":["sound_word_r11"]}]
// R12_SOURCE_SPANS: [{"symbol":"sound_word_r11","start":58,"end":83}]
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

// Provided definitions: rg_re_a4 (layer A4), copied verbatim.
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

// The task (R11.H2 sound_word_r11): an accepted certificate proves the match.
proof fn sound_word_r11(d:Derivation,r:Re,s:Seq<char>)
 requires valid_word_r10(d,r,s),
 ensures matches(r,s),
 decreases d,
{
 reveal_with_fuel(valid_word_r10,2);
 match d {
  Derivation::DAltL(child)=>{
   /*R12_CALLS:c1*/
  },
  Derivation::DAltR(child)=>{
   /*R12_CALLS:c2*/
  },
  Derivation::DCat(k,left,right)=>{
   /*R12_CALLS:c3*/
   assert(s.take(k as int)=~=s.subrange(0,k as int));
   assert(s.skip(k as int)=~=s.subrange(k as int,s.len() as int));
  },
  Derivation::DStarCons(k,left,right)=>{
   /*R12_CALLS:c4*/
   assert(s.take(k as int)=~=s.subrange(0,k as int));
   assert(s.skip(k as int)=~=s.subrange(k as int,s.len() as int));
  },
  _=>{},
 }
}

} // verus!
