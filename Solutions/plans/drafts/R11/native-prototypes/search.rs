use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
proof fn slice_split_r11(s:Seq<char>,lo:int,hi:int,k:int)
 requires 0<=lo<=hi<=s.len(),0<=k<=hi-lo,
 ensures s.subrange(lo,hi).take(k)==s.subrange(lo,lo+k),
 s.subrange(lo,hi).skip(k)==s.subrange(lo+k,hi),
{
 assert(s.subrange(lo,hi).take(k)=~=s.subrange(lo,lo+k));
 assert(s.subrange(lo,hi).skip(k)=~=s.subrange(lo+k,hi));
}
fn search_r11(r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,*r,s@,lo as int,hi as int),None=>!matches(*r,s@.subrange(lo as int,hi as int))},
 decreases node_count(*r),hi-lo,1nat,
{
 proof {reveal_with_fuel(valid_word_r10,2);}
 match r {
  Re::Empty=>None,
  Re::Eps=>if lo==hi {Some(Derivation::DEps)} else {None},
  Re::Chr(c)=>{
   if lo<hi && hi-lo==1 && s[lo]==*c {
    proof {assert(s@.subrange(lo as int,hi as int)=~=seq![*c]);}
    Some(Derivation::DChr)
   } else {None}
  },
  Re::Alt(a,b)=>{
   match search_r11(a,s,lo,hi) {
    Some(d)=>Some(Derivation::DAltL(Box::new(d))),
    None=>match search_r11(b,s,lo,hi) {
     Some(d)=>Some(Derivation::DAltR(Box::new(d))),None=>None,
    },
   }
  },
  Re::Cat(a,b)=>search_cat_r11(a,b,s,lo,hi),
  Re::Star(a)=>{
   if lo==hi {Some(Derivation::DStarNil)} else {search_star_r11(a,s,lo,hi)}
  },
 }
}
#[verifier::loop_isolation(false)]
fn search_cat_r11(a:&Re,b:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Cat(Box::new(*a),Box::new(*b)),s@,lo as int,hi as int),None=>!matches(Re::Cat(Box::new(*a),Box::new(*b)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Cat(Box::new(*a),Box::new(*b))),hi-lo,0nat,
{
 let ghost word=s@.subrange(lo as int,hi as int);
 let n=hi-lo;let mut k:usize=0;
 loop
  invariant lo<=hi<=s.len(),n==hi-lo,k<=n,
   forall|j:int| 0<=j<k ==> !(matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int))),
  decreases n-k,
 {
  let mid=lo+k;
  proof {slice_split_r11(s@,lo as int,hi as int,k as int);}
  match search_r11(a,s,lo,mid) {
   Some(left)=>{
    match search_r11(b,s,mid,hi) {
     Some(right)=>{
      proof {
       reveal_with_fuel(valid_word_r10,2);
       assert(valid_word_r10(Derivation::DCat(k,Box::new(left),Box::new(right)),Re::Cat(Box::new(*a),Box::new(*b)),word));
      }
      return Some(Derivation::DCat(k,Box::new(left),Box::new(right)));
     },
     None=>{},
    }
   },
   None=>{},
  }
  proof {
   assert(!(matches(*a,word.subrange(0,k as int)) && matches(*b,word.subrange(k as int,word.len() as int))));
   assert forall|j:int| 0<=j<=k implies !(matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int))) by {
    if j<k {} else {assert(j==k);}
   }
  }
  if k==n {
   proof {
    if matches(Re::Cat(Box::new(*a),Box::new(*b)),word) {
     let j=choose|j:int| 0<=j<=word.len() && matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int));
     assert(j<=k);assert(false);
    }
   }
   return None;
  }
  k=k+1;
 }
}
#[verifier::loop_isolation(false)]
fn search_star_r11(a:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Star(Box::new(*a)),s@,lo as int,hi as int),None=>!matches(Re::Star(Box::new(*a)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Star(Box::new(*a))),hi-lo,0nat,
{
 let ghost word=s@.subrange(lo as int,hi as int);
 let parent=Re::Star(Box::new(copy_re(a)));
 let n=hi-lo;let mut k:usize=1;
 loop
  invariant lo<hi<=s.len(),n==hi-lo,1<=k<=n,
   parent==Re::Star(Box::new(*a)),
   forall|j:int| 0<j<k ==> !(matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int))),
  decreases n-k,
 {
  let mid=lo+k;
  proof {slice_split_r11(s@,lo as int,hi as int,k as int);}
  match search_r11(a,s,lo,mid) {
   Some(left)=>{
    match search_r11(&parent,s,mid,hi) {
     Some(right)=>{
      proof {
       reveal_with_fuel(valid_word_r10,2);
       assert(valid_word_r10(Derivation::DStarCons(k,Box::new(left),Box::new(right)),parent,word));
      }
      return Some(Derivation::DStarCons(k,Box::new(left),Box::new(right)));
     },
     None=>{},
    }
   },
   None=>{},
  }
  proof {
   assert(!(matches(*a,word.subrange(0,k as int)) && matches(parent,word.subrange(k as int,word.len() as int))));
   assert forall|j:int| 0<j<=k implies !(matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int))) by {
    if j<k {} else {assert(j==k);}
   }
  }
  if k==n {
   proof {
    if matches(parent,word) {
     let j=choose|j:int| 0<j<=word.len() && matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int));
     assert(j<=k);assert(false);
    }
   }
   return None;
  }
  k=k+1;
 }
}
}
