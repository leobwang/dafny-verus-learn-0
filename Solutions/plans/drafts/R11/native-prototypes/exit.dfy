module R11_ExitPrototype {
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
 lemma {:induction false} CertificateLengthR11(r:Re,s:seq<char>,d:Derivation)
  requires CheckDeriv(r,s,d)
  ensures |s|==CharacterLeavesR11(d)
  decreases d
 {
  match d
  case DAltL(child)=>CertificateLengthR11(r.a,s,child);
  case DAltR(child)=>CertificateLengthR11(r.b,s,child);
  case DCat(k,left,right)=>CertificateLengthR11(r.a,s[..k],left);CertificateLengthR11(r.b,s[k..],right);
  case DStarCons(k,left,right)=>CertificateLengthR11(r.r,s[..k],left);CertificateLengthR11(r,s[k..],right);
  case _=>
 }
 ghost function UniformWordR11(c:char,n:nat):seq<char> {seq(n,i=>c)}
 lemma UniformStepR11(c:char,n:nat)
  requires n>0
  ensures UniformWordR11(c,n)[..1]==[c]
  ensures UniformWordR11(c,n)[1..]==UniformWordR11(c,n-1)
 {
  assert UniformWordR11(c,n)[..1]==[c];
  assert UniformWordR11(c,n)[1..]==UniformWordR11(c,n-1);
 }
 method RepeatCertificateR11(c:char,n:nat) returns(out:Derivation)
  ensures CheckDeriv(Star(Chr(c)),UniformWordR11(c,n),out)
 {
  var done:=0;out:=DStarNil;
  while done<n
   invariant 0<=done<=n
   invariant CheckDeriv(Star(Chr(c)),UniformWordR11(c,done),out)
   decreases n-done
  {
   UniformStepR11(c,done+1);
   out:=DStarCons(1,DChr,out);done:=done+1;
  }
 }
}
