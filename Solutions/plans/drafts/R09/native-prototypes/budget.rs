use vstd::prelude::*;
use vstd::arithmetic::div_mod::{lemma_fundamental_div_mod,lemma_mod_bound};
use vstd::arithmetic::mul::lemma_mul_is_commutative;
verus! {
proof fn quotient_product_guard_r09(b:int,q:int,r:int,d:int)
 requires d>0,0<=r<d,
 ensures (b<=q)==(b*d<=q*d+r),
{
 assert((b<=q)==(b*d<=q*d+r)) by (nonlinear_arith)
  requires d>0,0<=r<d;
}
proof fn division_budget_guard_r09(base:int,space:int,copies:int)
 requires base>=0,space>=0,copies>0,
 ensures (base<=space/copies)==(base*copies<=space),
{
 lemma_fundamental_div_mod(space,copies);
 lemma_mod_bound(space,copies);
 quotient_product_guard_r09(base,space/copies,space%copies,copies);
 lemma_mul_is_commutative(copies,space/copies);
}

fn repeat_expansion_budget_r09(base:u32,lo:u32,hi:u32,cap:u32)->(res:Option<u32>)
 requires lo<=hi<=9,
 ensures match res {
  Some(cost) => cost<=cap && (cost as int)==3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int)),
  None => 3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))>(cap as int),
 },
{
 let overhead:u32=3+lo+3*(hi-lo);
 if overhead>cap {return None;}
 proof {
  if hi>0 { division_budget_guard_r09(base as int,(cap-overhead) as int,hi as int); }
 }
 if hi>0 && base>(cap-overhead)/hi {return None;}
 let cost:u32=base*hi+overhead;
 Some(cost)
}
}
