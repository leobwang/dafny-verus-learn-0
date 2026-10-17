module R11_PrefixPrototype {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 opaque ghost predicate ResidualR11(r:Re,current:Re,prefix:seq<char>) {
  forall tail:seq<char> :: Matches(current,tail)<==>Matches(r,prefix+tail)
 }
 lemma ResidualStartR11(r:Re)
  ensures ResidualR11(r,r,[])
 {
  reveal ResidualR11();
  forall tail:seq<char> ensures Matches(r,tail)<==>Matches(r,[]+tail) {assert []+tail==tail;}
 }
 lemma ResidualStepR11(r:Re,current:Re,prefix:seq<char>,c:char)
  requires ResidualR11(r,current,prefix)
  ensures ResidualR11(r,Deriv(current,c),prefix+[c])
 {
  reveal ResidualR11();
  forall tail:seq<char>
   ensures Matches(Deriv(current,c),tail)<==>Matches(r,(prefix+[c])+tail)
  {DerivCorrect(current,c,tail);assert prefix+([c]+tail)==(prefix+[c])+tail;}
 }
 lemma ResidualObserveR11(r:Re,current:Re,prefix:seq<char>)
  requires ResidualR11(r,current,prefix)
  ensures Nullable(current)==Matches(r,prefix)
 {reveal ResidualR11();NullableCorrect(current);assert prefix+[]==prefix;}
 method PrefixMatchesR11(r:Re,s:seq<char>) returns (accepted:bool,trace:seq<bool>)
  ensures accepted==Matches(r,s)
  ensures |trace|==|s|
  ensures forall j |0<=j<|s| :: trace[j]==Matches(r,s[..j+1])
 {
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
