use vstd::prelude::*;
verus! {
pub proof fn trigger_probe_r14(values:Seq<int>)
 requires values.len()>=3,forall|i:int| 0<=i<values.len() ==> values[i]>=0,
 ensures values[2]>0,
 {}
}
