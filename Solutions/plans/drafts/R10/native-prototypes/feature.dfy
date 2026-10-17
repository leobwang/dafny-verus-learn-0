module R10_FeatureProbe {
 ghost function SuccessorModelR10(n:nat):nat {n+1}
 function SuccessorRuntimeR10(n:nat):nat {SuccessorModelR10(n)}
 by method {return n+1;}
 datatype CountedR10 = CountedR10(value:nat,ghost proofCount:nat)
 type WitnessedR10 = p:CountedR10 | p.proofCount==p.value+1 witness CountedR10(0,1)
 function BuildWitnessR10(n:nat):WitnessedR10 {CountedR10(n,n+1)}
 by method {
  ghost var proofValue:=SuccessorModelR10(n);
  return CountedR10(n,proofValue);
 }
}
