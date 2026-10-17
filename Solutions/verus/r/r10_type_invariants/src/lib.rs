// Reference Solution.
/*! R10 — Invariants in types. Frozen A1–A4 interfaces.
The packet carries a normal regex with erased node-count evidence.
H1 accepts precisely normal inputs; H2 rebuilds packet evidence; H3 proves
normal fixed points; H4 supplies compiled normalization for the ghost model.
Shape, exact normalization, and language preservation are separate promises.
Commit predictions before enabling checks. Original statements stay frozen.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
// item: R10.W1v
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
// item: R10.H1v
// pair: R10.H1d
// uses: type-invariant, ghost, tracked
fn try_packet_r10(r:Re)->(res:Option<NormPacketR10>)
 ensures match res {Some(p)=>p.re()==r && is_norm(r),None=>!is_norm(r)},
{
 // did: implement the fixed R10.H1v contract and preserve its model.

 if !is_normal_exec_r10(&r) {return None;}
 let ghost weight=node_count(r);
 let tracked evidence=NormalEvidenceR10 {pattern:r};
 let repr=NormRe::from_normal_r10(r);
 Some(NormPacketR10 {repr,weight:Ghost(weight),evidence:Tracked(evidence)})
}
// item: R10.H2v
// pair: R10.H2d
// uses: type-invariant, ghost, tracked
fn cat_packet_r10(a:NormPacketR10,b:NormPacketR10)->(out:NormPacketR10)
 ensures out.re()==mk_cat(a.re(),b.re()),
{
 // did: implement the fixed R10.H2v contract and preserve its model.

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
// item: R10.H3v
// pair: R10.H3d
proof fn normal_fixed_r10(r:Re)
 requires is_norm(r),
 ensures norm(r)==r,
 decreases r,
{
 // did: unfold the fixed normalization model before structural induction.
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
// item: R10.H4v
// pair: R10.H4d
fn normalize_packet_r10(r:&Re)->(out:NormPacketR10)
 ensures out.re()==norm(*r),
 decreases r,
{
 // did: implement the fixed R10.H4v contract and preserve its model.

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
// item: R10.W2v
fn runtime_shape_r10(r:&Re)->(out:bool)
 ensures out==is_norm(*r),
 {is_normal_exec_r10(r)}
// item: R10.W3v
proof fn replace_right_r10(a:Re,b1:Re,b2:Re,s:Seq<char>)
 requires equiv(b1,b2),
 ensures matches(Re::Cat(Box::new(a),Box::new(b1)),s)==matches(Re::Cat(Box::new(a),Box::new(b2)),s),
 {lemma_cat_cong(a,a,b1,b2,s);}
}
