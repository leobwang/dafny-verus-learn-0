use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
pub open spec fn character_leaves_r11(d:Derivation)->nat
 decreases d,
{
 match d {
  Derivation::DEps|Derivation::DStarNil=>0,
  Derivation::DChr=>1,
  Derivation::DAltL(child)|Derivation::DAltR(child)=>character_leaves_r11(*child),
  Derivation::DCat(_,left,right)|Derivation::DStarCons(_,left,right)=>character_leaves_r11(*left)+character_leaves_r11(*right),
 }
}
proof fn certificate_length_r11(d:Derivation,r:Re,s:Seq<char>)
 requires valid_word_r10(d,r,s),
 ensures s.len()==character_leaves_r11(d),
 decreases d,
{
 reveal_with_fuel(valid_word_r10,2);reveal_with_fuel(character_leaves_r11,2);
 match d {
  Derivation::DAltL(child)=>{certificate_length_r11(*child,*r->Alt_0,s);},
  Derivation::DAltR(child)=>{certificate_length_r11(*child,*r->Alt_1,s);},
  Derivation::DCat(k,left,right)=>{certificate_length_r11(*left,*r->Cat_0,s.take(k as int));certificate_length_r11(*right,*r->Cat_1,s.skip(k as int));},
  Derivation::DStarCons(k,left,right)=>{certificate_length_r11(*left,*r->Star_0,s.take(k as int));certificate_length_r11(*right,r,s.skip(k as int));},
  _=>{},
 }
}
pub open spec fn uniform_word_r11(c:char,n:nat)->Seq<char> {Seq::new(n,|i:int| c)}
proof fn uniform_step_r11(c:char,n:nat)
 requires n>0,
 ensures uniform_word_r11(c,n).take(1)==seq![c],
 uniform_word_r11(c,n).skip(1)==uniform_word_r11(c,(n-1) as nat),
{
 assert(uniform_word_r11(c,n).take(1)=~=seq![c]);
 assert(uniform_word_r11(c,n).skip(1)=~=uniform_word_r11(c,(n-1) as nat));
}
fn repeat_certificate_r11(c:char,n:usize)->(out:Derivation)
 ensures valid_word_r10(out,Re::Star(Box::new(Re::Chr(c))),uniform_word_r11(c,n as nat)),
{
 let mut done:usize=0;let mut out=Derivation::DStarNil;
 proof {reveal_with_fuel(valid_word_r10,2);}
 while done<n
  invariant done<=n,valid_word_r10(out,Re::Star(Box::new(Re::Chr(c))),uniform_word_r11(c,done as nat)),
  decreases n-done,
 {
  proof {uniform_step_r11(c,done as nat+1);}
  out=Derivation::DStarCons(1,Box::new(Derivation::DChr),Box::new(out));done=done+1;
  proof {reveal_with_fuel(valid_word_r10,2);}
 }
 out
}
}
