// R12_HINT_SITES: [{"name":"i1","identifiers":["Length","array","i","j","mfirstCero","v"]},{"name":"i2","identifiers":["Length","array","i","j","mfirstCero","v"]}]
// R12_SOURCE_SPANS: [{"symbol":"mfirstCero","start":5,"end":16}]
// R12 public task: dafnybench Dafny-Exercises_tmp_tmpjm75muf__Session4Exercises_ExercisefirstZero.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.

method mfirstCero(v:array<int>) returns (i:int)
ensures 0 <=i<=v.Length
ensures forall j:: 0<=j<i ==> v[j]!=0 
ensures i!=v.Length ==> v[i]==0  
{
 i:=0;
 while (i<v.Length && v[i]!=0)
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
   decreases v.Length -i
  {i:=i+1;}
}
