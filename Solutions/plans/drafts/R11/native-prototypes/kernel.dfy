module R11_KernelPrototype {
 import opened RG_A1_Re
 import opened RG_A4_Norm
lemma {:induction false} CheckSoundR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  {
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
lemma {:induction false} DirectCompleteR11(r: Re, s: seq<char>) returns (d: Derivation)
    requires Matches(r, s)
    ensures CheckDeriv(r, s, d)
    decreases r, |s|
  {
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
method CheckCertificateR11(r:Re,s:seq<char>,d:Derivation) returns (ok:bool)
 ensures ok==CheckDeriv(r,s,d)
 decreases d
{
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
