// Reference Solution.
// item: R11.P3dv verdict
// Local changed rule then original canonical rule, D:<x>,<y> V:<x>,<y>.
// CHECK P3dv
// item: R11.P5dv verdict
// Success-only producer promise then complete rejection promise, D:<x>,<y> V:<x>,<y>.
// CHECK P5dv
/*! R11 — Theory. Standalone A1–A4, fixed relative certificate rules.
The core has T1 plus seven hand/project tasks in Dafny and nine in Verus;
the checkpoint has two tasks in each language. Preserve models and domains.
Compiled checks, metatheory and rule fidelity establish different properties.
Tracked evidence is proof data; runtime certificates are ordinary derivations.
*/
module R11_Kernel {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
// item: R11.W2d
 datatype EvidenceR11=EvidenceR11(ghost expression:RG_A1_Re.Re,ghost word:seq<char>,ghost tree:RG_A4_Norm.Derivation)
 ghost function PackEvidenceR11(r:RG_A1_Re.Re,s:seq<char>,d:RG_A4_Norm.Derivation):(out:EvidenceR11)
  requires RG_A4_Norm.CheckDeriv(r,s,d)
  ensures RG_A4_Norm.CheckDeriv(out.expression,out.word,out.tree)
 {EvidenceR11(r,s,d)}
 // item: R11.H2d
// pair: R11.H2v
lemma {:induction false} CheckSoundR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  {
 // did: implement the fixed R11.H2d model and its original domain.

    match d
    case DEps =>
    case DChr =>
    case DAltL(d1) =>
      CheckSoundR11(r.a, s, d1);
    case DAltR(d1) =>
      CheckSoundR11(r.b, s, d1);
    case DCat(k, d1, d2) =>
      CheckSoundR11(r.a, s[..k], d1);
      CheckSoundR11(r.b, s[k..], d2);
    case DStarNil =>
    case DStarCons(k, d1, d2) =>
      CheckSoundR11(r.r, s[..k], d1);
      CheckSoundR11(r, s[k..], d2);
  }
// item: R11.H3d
// pair: R11.H3v
lemma {:induction false} DirectCompleteR11(r: Re, s: seq<char>) returns (d: Derivation)
    requires Matches(r, s)
    ensures CheckDeriv(r, s, d)
    decreases r, |s|
  {
 // did: implement the fixed R11.H3d model and its original domain.

    match r
    case Eps =>
      d := DEps;
    case Chr(_) =>
      d := DChr;
    case Alt(a, b) =>
      if Matches(a, s) {
        var d1 := DirectCompleteR11(a, s);
        d := DAltL(d1);
      } else {
        var d1 := DirectCompleteR11(b, s);
        d := DAltR(d1);
      }
    case Cat(a, b) =>
      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(b, s[k..]);
      var d1 := DirectCompleteR11(a, s[..k]);
      var d2 := DirectCompleteR11(b, s[k..]);
      d := DCat(k, d1, d2);
    case Star(a) =>
      if s == [] {
        d := DStarNil;
      } else {
        var k :| 0 < k <= |s| && Matches(a, s[..k]) && Matches(Star(a), s[k..]);
        var d1 := DirectCompleteR11(a, s[..k]);
        var d2 := DirectCompleteR11(r, s[k..]);
        d := DStarCons(k, d1, d2);
      }
  }
// item: R11.H1d
// pair: R11.H1v
method CheckCertificateR11(r:Re,s:seq<char>,d:Derivation) returns (ok:bool)
 ensures ok==CheckDeriv(r,s,d)
 decreases d
{
 // did: implement the fixed R11.H1d model and its original domain.

 match d
 case DEps => ok:=r==Eps && s==[];
 case DChr => ok:=r.Chr? && s==[r.c];
 case DAltL(child) =>
  if !r.Alt? {return false;}
  ok:=CheckCertificateR11(r.a,s,child);
 case DAltR(child) =>
  if !r.Alt? {return false;}
  ok:=CheckCertificateR11(r.b,s,child);
 case DCat(k,left,right) =>
  if !r.Cat? || k>|s| {return false;}
  var a:=CheckCertificateR11(r.a,s[..k],left);
  var b:=false;if a {b:=CheckCertificateR11(r.b,s[k..],right);}
  ok:=a && b;
 case DStarNil => ok:=r.Star? && s==[];
 case DStarCons(k,left,right) =>
  if !r.Star? || k==0 || k>|s| {return false;}
  var a:=CheckCertificateR11(r.r,s[..k],left);
  var b:=false;if a {b:=CheckCertificateR11(r,s[k..],right);}
  ok:=a && b;
}
}
module R11_Streaming {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 opaque ghost predicate ResidualR11(r:Re,current:Re,prefix:seq<char>) {
  forall tail:seq<char> :: Matches(current,tail)<==>Matches(r,prefix+tail)
 }
 // item: R11.W1d
lemma ResidualStartR11(r:Re)
  ensures ResidualR11(r,r,[])
 {
  // did: unfold the fixed model for this constructor obligation.
  reveal ResidualR11();
  forall tail:seq<char> ensures Matches(r,tail)<==>Matches(r,[]+tail) {assert []+tail==tail;}
 }
 // item: R11.W3d
lemma ResidualStepR11(r:Re,current:Re,prefix:seq<char>,c:char)
  requires ResidualR11(r,current,prefix)
  ensures ResidualR11(r,Deriv(current,c),prefix+[c])
 {
  // did: unfold the fixed model for this constructor obligation.
  reveal ResidualR11();
  forall tail:seq<char>
   ensures Matches(Deriv(current,c),tail)<==>Matches(r,(prefix+[c])+tail)
  {DerivCorrect(current,c,tail);assert prefix+([c]+tail)==(prefix+[c])+tail;}
 }
 lemma ResidualObserveR11(r:Re,current:Re,prefix:seq<char>)
  requires ResidualR11(r,current,prefix)
  ensures Nullable(current)==Matches(r,prefix)
 {reveal ResidualR11();NullableCorrect(current);assert prefix+[]==prefix;}
 // item: R11.H4d
// pair: R11.H4v
method PrefixMatchesR11(r:Re,s:seq<char>) returns (accepted:bool,trace:seq<bool>)
  ensures accepted==Matches(r,s)
  ensures |trace|==|s|
  ensures forall j |0<=j<|s| :: trace[j]==Matches(r,s[..j+1])
 {
 // did: implement the fixed R11.H4d model and its original domain.

  var current:=r;var i:=0;trace:=[];
  assert s[..0]==[];ResidualStartR11(r);
  while i<|s|
   invariant 0<=i<=|s| && |trace|==i
   invariant ResidualR11(r,current,s[..i])
   invariant forall j |0<=j<i :: trace[j]==Matches(r,s[..j+1])
   decreases |s|-i
  {
   var c:=s[i];ResidualStepR11(r,current,s[..i],c);
   assert s[..i]+[c]==s[..i+1];
   current:=Deriv(current,c);i:=i+1;
   ResidualObserveR11(r,current,s[..i]);
   var bit:=Nullable(current);trace:=trace+[bit];
  }
  ResidualObserveR11(r,current,s[..i]);assert s[..i]==s;
  accepted:=Nullable(current);
 }
}
module R11_Search {
 // specfreeze: frozen-imports
 import opened RG_A1_Re
 import opened RG_A4_Norm
 datatype CertChoiceR11=NoCertR11|HasCertR11(value:Derivation)
 // item: R11.H5d
// pair: R11.H5v
method SearchR11(r:Re,s:seq<char>) returns (out:CertChoiceR11)
  ensures out.HasCertR11? ==> CheckDeriv(r,s,out.value)
  ensures out.NoCertR11? ==> !Matches(r,s)
  decreases r,|s|
 {
 // did: implement the fixed R11.H5d model and its original domain.

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
 // item: R11.H6d
// pair: R11.H6v
method SearchCatR11(a:Re,b:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires k<=|s|+1
  requires forall i |0<=i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(b,s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Cat(a,b),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Cat(a,b),s)
  decreases Cat(a,b),|s|,|s|+1-k
 {
 // did: implement the fixed R11.H6d model and its original domain.

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
 // item: R11.H7d
// pair: R11.H7v
method SearchStarR11(a:Re,s:seq<char>,k:nat) returns(out:CertChoiceR11)
  requires s!=[] && 1<=k<=|s|+1
  requires forall i |0<i<k && i<=|s| :: !(Matches(a,s[..i]) && Matches(Star(a),s[i..]))
  ensures out.HasCertR11? ==> CheckDeriv(Star(a),s,out.value)
  ensures out.NoCertR11? ==> !Matches(Star(a),s)
  decreases Star(a),|s|,|s|+1-k
 {
 // did: implement the fixed R11.H7d model and its original domain.

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
module R11_WpReview {
 // specfreeze: frozen-imports
 // item: R11.T1d
// pair: R11.T1v
method WpIndexStepR11(i:nat,len:nat) returns(next:nat)
  requires i<len
  ensures next==i+1 && next<=len
 {
 // did: implement the fixed R11.T1d model and its original domain.
next:=i+1;}
}
