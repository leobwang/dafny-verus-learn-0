module R11_SearchPrototype {
 import opened RG_A1_Re
 import opened RG_A4_Norm
 datatype CertChoiceR11=NoCertR11|HasCertR11(value:Derivation)
 method SearchR11(r:Re,s:seq<char>) returns (out:CertChoiceR11)
  ensures out.HasCertR11? ==> CheckDeriv(r,s,out.value)
  ensures out.NoCertR11? ==> !Matches(r,s)
  decreases r,|s|
 {
  match r
  case Empty => return NoCertR11;
  case Eps => return if s==[] then HasCertR11(DEps) else NoCertR11;
  case Chr(c) => return if s==[c] then HasCertR11(DChr) else NoCertR11;
  case Alt(a,b) =>
   var left:=SearchR11(a,s);
   if left.HasCertR11? {return HasCertR11(DAltL(left.value));}
   var right:=SearchR11(b,s);
   return if right.HasCertR11? then HasCertR11(DAltR(right.value)) else NoCertR11;
  case Cat(a,b) => out:=SearchCatR11(a,b,s,0);
  case Star(a) =>
   if s==[] {return HasCertR11(DStarNil);}
   out:=SearchStarR11(a,s,1);
 }
 method SearchCatR11(a:Re,b:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires k<=|s|+1
  requires forall i |0<=i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(b,s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Cat(a,b),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Cat(a,b),s)
  decreases Cat(a,b),|s|,|s|+1-k
 {
  if k>|s| {return NoCertR11;}
  var left:=SearchR11(a,s[..k]);
  var right:=NoCertR11;
  if left.HasCertR11? {right:=SearchR11(b,s[k..]);}
  if left.HasCertR11? && right.HasCertR11? {return HasCertR11(DCat(k,left.value,right.value));}
  forall i |0<=i<k+1 && i<=|s|
   ensures !(Matches(a,s[..i]) && Matches(b,s[i..]))
  {if i<k {} else {assert i==k;}}
  out:=SearchCatR11(a,b,s,k+1);
 }
 method SearchStarR11(a:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires s!=[] && 1<=k<=|s|+1
  requires forall i |0<i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(Star(a),s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Star(a),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Star(a),s)
  decreases Star(a),|s|,|s|+1-k
 {
  if k>|s| {return NoCertR11;}
  var left:=SearchR11(a,s[..k]);
  var right:=NoCertR11;
  if left.HasCertR11? {right:=SearchR11(Star(a),s[k..]);}
  if left.HasCertR11? && right.HasCertR11? {return HasCertR11(DStarCons(k,left.value,right.value));}
  forall i |0<i<k+1 && i<=|s|
   ensures !(Matches(a,s[..i]) && Matches(Star(a),s[i..]))
  {if i<k {} else {assert i==k;}}
  out:=SearchStarR11(a,s,k+1);
 }
}
