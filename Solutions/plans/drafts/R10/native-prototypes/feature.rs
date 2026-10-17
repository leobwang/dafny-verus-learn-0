use vstd::prelude::*;
verus! {
pub tracked struct EvidenceR10 {pub ghost count:nat}
pub struct CacheFeatureR10 {number:u32,evidence:Tracked<EvidenceR10>,model:Ghost<nat>}
impl CacheFeatureR10 {
 #[verifier::type_invariant]
 spec fn cache_valid(&self)->bool {self.number>0 && self.evidence@.count==self.number && self.model@==self.number}
}
fn cache_feature_r10(n:u32)->(out:CacheFeatureR10)
 requires n>0,
 ensures out.number==n,
{
 let tracked witness=EvidenceR10 {count:n as nat};
 CacheFeatureR10 {number:n,evidence:Tracked(witness),model:Ghost(n as nat)}
}
fn read_cache_feature_r10(c:&CacheFeatureR10)->(n:u32)
 ensures n>0 && n==c.number,
{
 proof {use_type_invariant(c);}
 c.number
}
}
