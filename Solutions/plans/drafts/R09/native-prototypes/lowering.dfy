module R09_LoweringPrototype {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 method RangeLowerExecR09(lo:char,hi:char) returns (out:Re)
  requires lo<=hi && (hi as int)<ClassMax
  ensures out==RangeRe(lo,hi)
 {
  var low:=lo as int;var n:=hi as int;out:=Chr(hi);
  while n>low
   invariant 0<=low<=n<=hi as int<ClassMax
   invariant low==lo as int
   invariant out==RangeRe(n as char,hi)
   decreases n-low
  {
   n:=n-1;
   out:=Alt(Chr(n as char),out);
  }
 }
 method ClassLowerExecR09(cc:RG_A2_Deriv.CharClass) returns (out:Re)
  requires ClassLowered(cc)
  ensures out==ClassToRe(cc)
 {
  var i:nat:=|cc|;out:=Empty;
  while i>0
   invariant i<=|cc|
   invariant out==ClassToRe(cc[i..])
   decreases i
  {
   i:=i-1;
   var first:=RangeLowerExecR09(cc[i].lo,cc[i].hi);
   assert cc[i..][1..]==cc[i+1..];
   out:=Alt(first,out);
  }
 }
 method CopiesLowerExecR09(r:Re,k:nat) returns (out:Re)
  ensures out==Copies(r,k)
 {
  var i:nat:=0;out:=Eps;
  while i<k
   invariant i<=k && out==Copies(r,i)
   decreases k-i
  {out:=Cat(r,out);i:=i+1;}
 }
 method OptionalLowerExecR09(r:Re,k:nat) returns (out:Re)
  ensures out==CopiesUpTo(r,k)
 {
  var i:nat:=0;out:=Eps;
  while i<k
   invariant i<=k && out==CopiesUpTo(r,i)
   decreases k-i
  {out:=Alt(Eps,Cat(r,out));i:=i+1;}
 }
 method LoweringExecR09(t:Syn,len:nat) returns (out:Re)
  requires WF(t,len)
  ensures out==Lower(t,len)
  decreases t
 {
  match t
  case SEps(_,_) => out:=Eps;
  case SChr(c,_,_) => out:=Chr(c);
  case SClass(cc,_,_) => out:=ClassLowerExecR09(cc);
  case SAlt(a,b,_,_) =>
   var left:=LoweringExecR09(a,len);var right:=LoweringExecR09(b,len);out:=Alt(left,right);
  case SCat(a,b,_,_) =>
   var left:=LoweringExecR09(a,len);var right:=LoweringExecR09(b,len);out:=Cat(left,right);
  case SStar(a,_,_) => var child:=LoweringExecR09(a,len);out:=Star(child);
  case SPlus(a,_,_) => var child:=LoweringExecR09(a,len);out:=Cat(child,Star(child));
  case SOpt(a,_,_) => var child:=LoweringExecR09(a,len);out:=Alt(Eps,child);
  case SGroup(a,_,_) => out:=LoweringExecR09(a,len);
  case SRep(a,n,m,_,_) =>
   if m==0 {out:=Cat(Eps,Eps);}
   else {
    var child:=LoweringExecR09(a,len);
    var fixed:=CopiesLowerExecR09(child,n);var optional:=OptionalLowerExecR09(child,m-n);
    out:=Cat(fixed,optional);
   }
 }
}
