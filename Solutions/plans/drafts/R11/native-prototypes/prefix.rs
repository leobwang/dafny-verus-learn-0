use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
verus! {
#[verifier::opaque]
pub open spec fn residual_r11(r:Re,current:Re,prefix:Seq<char>)->bool {
 forall|tail:Seq<char>| #[trigger] matches(current,tail)==matches(r,prefix+tail)
}
proof fn residual_start_r11(r:Re)
 ensures residual_r11(r,r,Seq::empty()),
{
 reveal(residual_r11);
 assert forall|tail:Seq<char>| #[trigger] matches(r,tail)==matches(r,Seq::empty()+tail) by {
  assert(Seq::<char>::empty()+tail=~=tail);
 }
}
proof fn residual_step_r11(r:Re,current:Re,prefix:Seq<char>,c:char)
 requires residual_r11(r,current,prefix),
 ensures residual_r11(r,deriv(current,c),prefix+seq![c]),
{
 reveal(residual_r11);
 assert forall|tail:Seq<char>| #[trigger] matches(deriv(current,c),tail)==matches(r,(prefix+seq![c])+tail) by {
  lemma_deriv_correct(current,c,tail);
  assert(prefix+(seq![c]+tail)=~=(prefix+seq![c])+tail);
 }
}
proof fn residual_observe_r11(r:Re,current:Re,prefix:Seq<char>)
 requires residual_r11(r,current,prefix),
 ensures nullable(current)==matches(r,prefix),
{
 reveal(residual_r11);lemma_nullable_correct(current);
 assert(prefix+Seq::<char>::empty()=~=prefix);
}
pub struct PrefixReportR11 {pub accepted:bool,pub trace:Vec<bool>}
fn prefix_matches_r11(r:&Re,s:&Vec<char>)->(out:PrefixReportR11)
 ensures out.accepted==matches(*r,s@),out.trace@.len()==s@.len(),
 forall|j:int| 0<=j<s@.len() ==> out.trace@[j]==matches(*r,s@.take(j+1)),
{
 let mut current=copy_re(r);let mut i:usize=0;let mut trace:Vec<bool>=Vec::new();
 proof {assert(s@.take(0)=~=Seq::<char>::empty());residual_start_r11(*r);}
 while i<s.len()
  invariant i<=s.len(),trace@.len()==i,residual_r11(*r,current,s@.take(i as int)),
   forall|j:int| 0<=j<i ==> trace@[j]==matches(*r,s@.take(j+1)),
  decreases s.len()-i,
 {
  let c=s[i];
  proof {residual_step_r11(*r,current,s@.take(i as int),c);assert(s@.take(i as int)+seq![c]=~=s@.take(i as int+1));}
  current=deriv_exec(&current,c);i=i+1;
  proof {residual_observe_r11(*r,current,s@.take(i as int));}
  let bit=is_nullable(&current);trace.push(bit);
 }
 proof {residual_observe_r11(*r,current,s@.take(i as int));assert(s@.take(i as int)=~=s@);}
 let accepted=is_nullable(&current);PrefixReportR11{accepted,trace}
}
}
