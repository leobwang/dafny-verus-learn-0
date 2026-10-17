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
#[verifier::external_body]
fn try_packet_r10(r:Re)->(res:Option<NormPacketR10>)
 ensures match res {Some(p)=>p.re()==r && is_norm(r),None=>!is_norm(r)},
{ unimplemented!() }
// item: R10.H2v
// pair: R10.H2d
// uses: type-invariant, ghost, tracked
#[verifier::external_body]
fn cat_packet_r10(a:NormPacketR10,b:NormPacketR10)->(out:NormPacketR10)
 ensures out.re()==mk_cat(a.re(),b.re()),
{ unimplemented!() }
// item: R10.H3v
// pair: R10.H3d
proof fn normal_fixed_r10(r:Re)
 requires is_norm(r),
 ensures norm(r)==r,
 decreases r,
{ #[verifier::proof_note("R10.H3v")] assume(false); }
proof fn norm_idempotent_r10(r:Re)
 ensures norm(norm(r))==norm(r),
 {lemma_norm_shape_r10(r);normal_fixed_r10(norm(r));}
// item: R10.H4v
// pair: R10.H4d
#[verifier::external_body]
fn normalize_packet_r10(r:&Re)->(out:NormPacketR10)
 ensures out.re()==norm(*r),
 decreases r,
{ unimplemented!() }
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
