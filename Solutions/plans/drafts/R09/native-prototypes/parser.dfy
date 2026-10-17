module R09_ParserPrototype {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 import opened RG_A3_Syntax
 lemma LiteralAppendR09(a:Re,u:seq<char>,c:char)
  requires Matches(a,u)
  ensures Matches(Cat(a,Chr(c)),u+[c])
 {
  var w:=u+[c];assert w[..|u|]==u && w[|u|..]==[c];
 }
 method Counted(s:seq<char>,a:Syn,j:nat) returns (res:Res<(Syn,nat)>)
  requires j<|s| && s[j]=='{' && WF(a,|s|) && a.hi==j && a.lo<j
  ensures res.Ok? ==> j<res.value.1<=|s| && WF(res.value.0,|s|) && res.value.0.lo==a.lo && res.value.0.hi==res.value.1
  ensures res.Err? ==> res.pos<=|s|
  ensures forall n:nat,m:nat,k:nat :: CountedAt(s,j,n,m,k) ==> res==Ok((SRep(a,n,m,a.lo,k),k))
 {
  if j+1>=|s| {res:=Err(j+1,"expected a bound");}
  else if !BoundChar(s[j+1]) {res:=Err(j+1,"expected a bound '0'..'9'");}
  else if j+2>=|s| {res:=Err(j+2,"expected '}' or ','");}
  else if s[j+2]=='}' {var n:=BoundVal(s[j+1]);res:=Ok((SRep(a,n,n,a.lo,j+3),j+3));}
  else if s[j+2]!=',' {res:=Err(j+2,"expected '}' or ','");}
  else if j+3>=|s| || !BoundChar(s[j+3]) {res:=Err(j+3,"expected a bound '0'..'9'");}
  else if j+4>=|s| || s[j+4]!='}' {res:=Err(j+4,"expected '}'");}
  else {
   var n:=BoundVal(s[j+1]);var m:=BoundVal(s[j+3]);
   if m<n {res:=Err(j+3,"upper bound below lower bound");}
   else {res:=Ok((SRep(a,n,m,a.lo,j+5),j+5));}
  }
 }
 method ClassItems(s:seq<char>,i:nat,acc:CharClass) returns (res:Res<(CharClass,nat)>)
  requires i<=|s| && ClassValid(acc) && ClassLowered(acc)
  ensures res.Ok? ==> i<res.value.1<=|s| && ClassValid(res.value.0) && ClassLowered(res.value.0)
  ensures res.Err? ==> res.pos<=|s|
  ensures forall k:nat :: SimpleClassBody(s,i,k) ==> res.Ok? && res.value.1==k+1
 {
  var j:=i;var ranges:=acc;
  while j<|s|
   invariant i<=j<=|s| && ClassValid(ranges) && ClassLowered(ranges)
   invariant forall k:nat :: SimpleClassBody(s,i,k) ==> SimpleClassBody(s,j,k)
   decreases |s|-j
  {
   if s[j]==']' {res:=Ok((ranges,j+1));return;}
   var escaped:=s[j]=='\\' && j+1<|s|;
   var c:=if escaped then s[j+1] else s[j];
   var k:=if escaped then j+2 else j+1;
   if k+1<|s| && s[k]=='-' && s[k+1]!=']' {
    var d:=s[k+1];
    if d<c {res:=Err(k+1,"empty range");return;}
    if d as int>=ClassMax {res:=Err(k+1,"class character out of range");return;}
    var next:=ClassInsert(ranges,CRange(c,d));
    assert ClassLowered(next) by {
     forall q | 0<=q<|next| ensures next[q].lo<=next[q].hi && (next[q].hi as int)<ClassMax {
      assert InClass(next,next[q].hi) by {assert InRange(next[q],next[q].hi);}
      if !InRange(CRange(c,d),next[q].hi) {var p :| 0<=p<|ranges| && InRange(ranges[p],next[q].hi);}
     }
    }
    ranges:=next;j:=k+2;
   } else {
    if c as int>=ClassMax {res:=Err(j,"class character out of range");return;}
    var next:=ClassInsert(ranges,CRange(c,c));
    assert ClassLowered(next) by {
     forall q | 0<=q<|next| ensures next[q].lo<=next[q].hi && (next[q].hi as int)<ClassMax {
      assert InClass(next,next[q].hi) by {assert InRange(next[q],next[q].hi);}
      if !InRange(CRange(c,c),next[q].hi) {var p :| 0<=p<|ranges| && InRange(ranges[p],next[q].hi);}
     }
    }
    ranges:=next;j:=k;
   }
  }
  res:=Err(j,"unclosed class");
 }
 method ParseAlt(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<=|s|
  ensures res.Ok? ==> i<=res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res.Ok? && res.value.j==|s| && Matches(Lower(res.value.t,|s|),s[i..])
  decreases |s|-i,3
 {
  var p :- ParseCat(s,i);var x:=p.t;var j:=p.j;
  while j<|s| && s[j]=='|'
   invariant i<=j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant NoSpecialFrom(s,i) ==> j==|s| && Matches(Lower(x,|s|),s[i..])
   decreases |s|-j
  {
   var q :- ParseCat(s,j+1);
   x:=SAlt(x,q.t,i,q.j);j:=q.j;
  }
  res:=Ok(PR(x,j));
 }
 method ParseCat(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<=|s|
  ensures res.Ok? ==> i<=res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res.Ok? && res.value.j==|s| && Matches(Lower(res.value.t,|s|),s[i..])
  decreases |s|-i,2
 {
  var x:=SEps(i,i);var j:=i;var first:=true;
  while j<|s| && s[j]!=')' && s[j]!='|'
   invariant i<=j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant first ==> j==i
   invariant NoSpecialFrom(s,i) ==> NoSpecialFrom(s,j) && Matches(Lower(x,|s|),s[i..j])
   decreases |s|-j
  {
   var q :- ParsePost(s,j);
   if NoSpecialFrom(s,i) {
    assert q.t==SChr(s[j],j,j+1) && q.j==j+1;
    assert s[i..j+1]==s[i..j]+[s[j]];
    LiteralAppendR09(Lower(x,|s|),s[i..j],s[j]);
   }
   x:=if first then q.t else SCat(x,q.t,i,q.j);first:=false;j:=q.j;
  }
  if NoSpecialFrom(s,i) { assert j==|s|; assert s[i..j]==s[i..]; }
  res:=Ok(PR(x,j));
 }
 method ParsePost(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<|s|
  ensures res.Ok? ==> i<res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res==Ok(PR(SChr(s[i],i,i+1),i+1))
  decreases |s|-i,1
 {
  var p :- ParseAtom(s,i);var x:=p.t;var j:=p.j;
  while j<|s| && (s[j]=='*' || s[j]=='+' || s[j]=='?' || s[j]=='{')
   invariant i<j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant NoSpecialFrom(s,i) ==> x==SChr(s[i],i,i+1) && j==i+1
   decreases |s|-j
  {
   var c:=s[j];
   if c=='{' {var q :- Counted(s,x,j);x:=q.0;j:=q.1;}
   else {
    x:=if c=='*' then SStar(x,i,j+1) else if c=='+' then SPlus(x,i,j+1) else SOpt(x,i,j+1);
    j:=j+1;
   }
  }
  res:=Ok(PR(x,j));
 }
 method ParseAtom(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<|s|
  ensures res.Ok? ==> i<res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res==Ok(PR(SChr(s[i],i,i+1),i+1))
  decreases |s|-i,0
 {
  var c:=s[i];
  if c=='(' {
   var p :- ParseAlt(s,i+1);
   if p.j<|s| && s[p.j]==')' {res:=Ok(PR(SGroup(p.t,i,p.j+1),p.j+1));}
   else {res:=Err(p.j,"expected ')'");}
  } else if c=='[' {
   var cc :- ClassItems(s,i+1,[]);res:=Ok(PR(SClass(cc.0,i,cc.1),cc.1));
  } else if c=='\\' {
   if i+1<|s| {res:=Ok(PR(SChr(s[i+1],i,i+2),i+2));}
   else {res:=Err(i+1,"dangling escape");}
  } else if Special(c) {res:=Err(i,"unexpected special character");}
  else {res:=Ok(PR(SChr(c,i,i+1),i+1));}
 }
 method Parse(s:seq<char>) returns (res:Res<Syn>)
  ensures res.Ok? ==> WF(res.value,|s|) && res.value.lo==0 && res.value.hi==|s|
  ensures NoSpecialFrom(s,0) ==> res.Ok? && Matches(Lower(res.value,|s|),s)
  ensures res.Err? ==> res.pos<=|s|
 {
  var p :- ParseAlt(s,0);
  if p.j==|s| {res:=Ok(p.t);} else {res:=Err(p.j,"unexpected ')'");}
 }
}
