include "/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0-r13-authoring/dafny/given/R/RG_A1_Re.dfy"
module R13_Repairs {
 import opened RG_A1_Re
 // specfreeze: frozen-imports
 // item: R13.T1d
 // pair: R13.T1v
 method ClampIndexR13(i:nat,bound:nat) returns(at:nat)
  requires bound>0
  ensures at<bound && at==(if i<bound then i else bound-1)
 {// did: retain an in-range index and clamp only the out-of-range case.
  at:=if i<bound then i else bound-1;}
 // item: R13.H1d
 // pair: R13.H1v
 method SaturatingSumR13(a:nat,b:nat) returns(out:nat)
  requires a<=18446744073709551615 && b<=18446744073709551615
  ensures out==(if a+b<=18446744073709551615 then a+b else 18446744073709551615)
 {// did: compare against the remaining headroom before adding.
  if a<=18446744073709551615-b {out:=a+b;} else {out:=18446744073709551615;}}
 // item: R13.H2d
 // pair: R13.H2v
 method RangeFitsR13(pos:nat,need:nat,limit:nat) returns(fits:bool)
  ensures fits <==> pos+need<=limit
 {// did: guard the subtraction, preserving the mathematical sum predicate.
  fits:=pos<=limit && need<=limit-pos;}
 // item: R13.H3d
 // pair: R13.H3v
 method PairWitnessR13(c:char,d:char) returns(s:seq<char>)
  ensures |s|==2 && Matches(Cat(Chr(c),Chr(d)),s)
 {// did: supply executable data and a concrete semantic split witness.
  s:=[c,d];
  assert s[..1]==[c] && s[1..]==[d];
  assert Matches(Chr(c),s[..1]) && Matches(Chr(d),s[1..]);
  assert exists i | 0<=i<=|s| :: Matches(Chr(c),s[..i]) && Matches(Chr(d),s[i..]);}
}
