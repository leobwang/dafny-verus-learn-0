// R12_HINT_SITES: [{"name":"c1","identifiers":["child","r","Alt_0","s","from","to"],"kind":"calls","callees":["rename_transport_r11"]},{"name":"c2","identifiers":["child","r","Alt_1","s","from","to"],"kind":"calls","callees":["rename_transport_r11"]},{"name":"c3","identifiers":["left","right","r","Cat_0","Cat_1","s","take","skip","k","as","int","from","to"],"kind":"calls","callees":["rename_split_r11","rename_transport_r11"]},{"name":"c4","identifiers":["left","right","r","Star_0","s","take","skip","k","as","int","from","to"],"kind":"calls","callees":["rename_split_r11","rename_transport_r11"]}]
// R12_SOURCE_SPANS: [{"symbol":"rename_transport_r11","start":66,"end":89}]
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

// Provided definitions (R11 agent file), copied verbatim; qualified layer names read locally.
pub open spec fn rename_char_r11(c:char,from:char,to:char)->char {if c==from {to} else {c}}
pub open spec fn rename_word_r11(s:Seq<char>,from:char,to:char)->Seq<char> {Seq::new(s.len(),|i:int| rename_char_r11(s[i],from,to))}
pub open spec fn rename_pattern_r11(r:Re,from:char,to:char)->Re
 decreases r,
{
 match r {
  Re::Empty=>Re::Empty,Re::Eps=>Re::Eps,Re::Chr(c)=>Re::Chr(rename_char_r11(c,from,to)),
  Re::Alt(a,b)=>Re::Alt(Box::new(rename_pattern_r11(*a,from,to)),Box::new(rename_pattern_r11(*b,from,to))),
  Re::Cat(a,b)=>Re::Cat(Box::new(rename_pattern_r11(*a,from,to)),Box::new(rename_pattern_r11(*b,from,to))),
  Re::Star(a)=>Re::Star(Box::new(rename_pattern_r11(*a,from,to))),
 }
}
pub open spec fn rules_r11(d: Derivation,r: Re,s:Seq<char>)->bool {
 valid_word_r10(d,r,s)
}

// Provided fact (R11 agent rename_split_r11), complete.
proof fn rename_split_r11(s:Seq<char>,k:int,from:char,to:char)
 requires 0<=k<=s.len(),
 ensures rename_word_r11(s,from,to).len()==s.len(),
 rename_word_r11(s,from,to).take(k)==rename_word_r11(s.take(k),from,to),
 rename_word_r11(s,from,to).skip(k)==rename_word_r11(s.skip(k),from,to),
{
 assert(rename_word_r11(s,from,to).take(k)=~=rename_word_r11(s.take(k),from,to));
 assert(rename_word_r11(s,from,to).skip(k)=~=rename_word_r11(s.skip(k),from,to));
}

// The task (R11.A1 rename_transport_r11): renaming a character transports a certificate.
proof fn rename_transport_r11(d: Derivation,r: Re,s:Seq<char>,from:char,to:char)
 requires rules_r11(d,r,s),
 ensures rules_r11(d,rename_pattern_r11(r,from,to),rename_word_r11(s,from,to)),
 decreases d,
{
 reveal_with_fuel(valid_word_r10,2);
 reveal_with_fuel(rename_pattern_r11,2);
 match d {
  Derivation::DChr=>{assert(rename_word_r11(s,from,to)=~=seq![rename_char_r11(r->Chr_0,from,to)]);},
  Derivation::DAltL(child)=>{
   /*R12_CALLS:c1*/
  },
  Derivation::DAltR(child)=>{
   /*R12_CALLS:c2*/
  },
  Derivation::DCat(k,left,right)=>{
   /*R12_CALLS:c3*/
  },
  Derivation::DStarCons(k,left,right)=>{
   /*R12_CALLS:c4*/
  },
  _=>{},
 }
}

} // verus!
