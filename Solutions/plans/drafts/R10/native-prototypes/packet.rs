use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
pub tracked struct NormalEvidenceR10 {pub ghost pattern:Re}
pub struct NormPacketR10 {repr:NormRe,weight:Ghost<nat>,evidence:Tracked<NormalEvidenceR10>}
impl NormPacketR10 {
 #[verifier::type_invariant]
 spec fn coherent(&self)->bool {
  is_norm(self.repr.re()) && self.weight@==node_count(self.repr.re()) && self.evidence@.pattern==self.repr.re()
 }
 pub closed spec fn re(self)->Re {self.repr.re()}
 pub fn pattern_ref_r10(&self)->(out:&Re)
  ensures *out==self.re(),is_norm(*out),
 {proof {use_type_invariant(self);} self.repr.pattern_ref_r10()}
 pub fn into_pattern_r10(self)->(out:Re)
  ensures out==self.re(),is_norm(out),
 {proof {use_type_invariant(&self);} self.repr.into_pattern_r10()}
}
fn try_packet_r10(r:Re)->(res:Option<NormPacketR10>)
 ensures match res {Some(p)=>p.re()==r && is_norm(r),None=>!is_norm(r)},
{
 if !is_normal_exec_r10(&r) {return None;}
 let ghost weight=node_count(r);
 let tracked evidence=NormalEvidenceR10 {pattern:r};
 let repr=NormRe::from_normal_r10(r);
 Some(NormPacketR10 {repr,weight:Ghost(weight),evidence:Tracked(evidence)})
}
fn cat_packet_r10(a:NormPacketR10,b:NormPacketR10)->(out:NormPacketR10)
 ensures out.re()==mk_cat(a.re(),b.re()),
{
 proof {use_type_invariant(&a);use_type_invariant(&b);}
 let ghost left=a.re();let ghost right=b.re();
 let ghost cached=if left is Empty || right is Empty {1nat}
  else if left is Eps {b.weight@} else if right is Eps {a.weight@} else {1+a.weight@+b.weight@};
 proof {lemma_cat_shape_r10(left,right);assert(cached==node_count(mk_cat(left,right)));}
 let left_raw=a.into_pattern_r10();let right_raw=b.into_pattern_r10();
 let raw=mk_cat_exec(left_raw,right_raw);
 let tracked evidence=NormalEvidenceR10 {pattern:raw};
 let repr=NormRe::from_normal_r10(raw);
 NormPacketR10 {repr,weight:Ghost(cached),evidence:Tracked(evidence)}
}
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
proof fn norm_idempotent_r10(r:Re)
 ensures norm(norm(r))==norm(r),
 {lemma_norm_shape_r10(r);normal_fixed_r10(norm(r));}
fn normalize_packet_r10(r:&Re)->(out:NormPacketR10)
 ensures out.re()==norm(*r),
 decreases r,
{
 match r {
  Re::Empty | Re::Eps | Re::Chr(_)=>{
   let raw=copy_re(r);let result=try_packet_r10(raw);
   proof {assert(result is Some);}
   result.unwrap()
  },
  Re::Alt(a,b)=>{
   let left=normalize_packet_r10(a);let right=normalize_packet_r10(b);
   let left_raw=left.into_pattern_r10();let right_raw=right.into_pattern_r10();
   proof {lemma_alt_shape_r10(left_raw,right_raw);}
   let raw=mk_alt_exec(left_raw,right_raw);
   let result=try_packet_r10(raw);
   proof {assert(result is Some);}
   result.unwrap()
  },
  Re::Cat(a,b)=>{
   let left=normalize_packet_r10(a);let right=normalize_packet_r10(b);
   cat_packet_r10(left,right)
  },
  Re::Star(a)=>{
   let child=normalize_packet_r10(a);let child_raw=child.into_pattern_r10();
   proof {lemma_star_shape_r10(child_raw);}
   let raw=mk_star_exec(child_raw);
   let result=try_packet_r10(raw);
   proof {assert(result is Some);}
   result.unwrap()
  },
 }
}
}
