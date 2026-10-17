/*! R11 — Theory. Standalone A1–A4, fixed relative certificate rules.
The core has T1 plus seven hand/project tasks in Dafny and nine in Verus;
the checkpoint has two tasks in each language. Preserve models and domains.
Compiled checks, metatheory and rule fidelity establish different properties.
Tracked evidence is proof data; runtime certificates are ordinary derivations.
*/
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
// item: R11.X1v
// pair: R11.X1d
proof fn certificate_length_r11(d:Derivation,r:Re,s:Seq<char>)
 requires valid_word_r10(d,r,s),
 ensures s.len()==character_leaves_r11(d),
 decreases d,
{ #[verifier::proof_note("R11.X1v")] assume(false); }
pub open spec fn uniform_word_r11(c:char,n:nat)->Seq<char> {Seq::new(n,|i:int| c)}
proof fn uniform_step_r11(c:char,n:nat)
 requires n>0,
 ensures uniform_word_r11(c,n).take(1)==seq![c],
 uniform_word_r11(c,n).skip(1)==uniform_word_r11(c,(n-1) as nat),
{
 assert(uniform_word_r11(c,n).take(1)=~=seq![c]);
 assert(uniform_word_r11(c,n).skip(1)=~=uniform_word_r11(c,(n-1) as nat));
}
// item: R11.X2v
// pair: R11.X2d
#[verifier::external_body]
fn repeat_certificate_r11(c:char,n:usize)->(out:Derivation)
 ensures valid_word_r10(out,Re::Star(Box::new(Re::Chr(c))),uniform_word_r11(c,n as nat)),
{ unimplemented!() }
}
