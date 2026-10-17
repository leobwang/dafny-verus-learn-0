/*! R11 — Theory. Standalone A1–A4, fixed relative certificate rules.
The core has T1 plus seven hand/project tasks in Dafny and nine in Verus;
the checkpoint has two tasks in each language. Preserve models and domains.
Compiled checks, metatheory and rule fidelity establish different properties.
Tracked evidence is proof data; runtime certificates are ordinary derivations.
*/
module R11_Checkpoint {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
 function CharacterLeavesR11(d:Derivation):nat decreases d {
  match d
  case DEps=>0
  case DChr=>1
  case DAltL(child)=>CharacterLeavesR11(child)
  case DAltR(child)=>CharacterLeavesR11(child)
  case DCat(_,left,right)=>CharacterLeavesR11(left)+CharacterLeavesR11(right)
  case DStarNil=>0
  case DStarCons(_,left,right)=>CharacterLeavesR11(left)+CharacterLeavesR11(right)
 }
 // item: R11.X1d
// pair: R11.X1v
lemma {:induction false} CertificateLengthR11(r:Re,s:seq<char>,d:Derivation)
  requires CheckDeriv(r,s,d)
  ensures |s|==CharacterLeavesR11(d)
  decreases d
 { assume false; }
 ghost function UniformWordR11(c:char,n:nat):seq<char> {seq(n,i=>c)}
 lemma UniformStepR11(c:char,n:nat)
  requires n>0
  ensures UniformWordR11(c,n)[..1]==[c]
  ensures UniformWordR11(c,n)[1..]==UniformWordR11(c,n-1)
 {
  assert UniformWordR11(c,n)[..1]==[c];
  assert UniformWordR11(c,n)[1..]==UniformWordR11(c,n-1);
 }
 // item: R11.X2d
// pair: R11.X2v
method RepeatCertificateR11(c:char,n:nat) returns(out:Derivation)
  ensures CheckDeriv(Star(Chr(c)),UniformWordR11(c,n),out)
 { assume false; }
}
