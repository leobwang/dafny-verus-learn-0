// Reference Solution.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a4::*;
verus! {
// reference-only
pub proof fn lemma_star_star_r10_ref(x: Re, s: Seq<char>)
    ensures
        matches(Re::Star(Box::new(Re::Star(Box::new(x)))), s) == matches(Re::Star(Box::new(x)), s),
    decreases s.len(),
{
    let st = Re::Star(Box::new(x));
    let stst = Re::Star(Box::new(st));
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
    if s.len() > 0 {
        if matches(st, s) {
            assert(matches(st, s.subrange(0, s.len() as int)));
            assert(matches(stst, s.subrange(s.len() as int, s.len() as int)));
        }
        if matches(stst, s) {
            let i = choose|i: int|
                1 <= i <= s.len() && matches(st, #[trigger] s.subrange(0, i)) && matches(
                    stst,
                    s.subrange(i, s.len() as int),
                );
            lemma_star_star_r10_ref(x, s.subrange(i, s.len() as int));
            lemma_star_concat(x, s.subrange(0, i), s.subrange(i, s.len() as int));
            assert(s.subrange(0, i) + s.subrange(i, s.len() as int) =~= s);
        }
    }
}
// reference-only
pub proof fn lemma_mk_alt_r10_ref(a: Re, b: Re, s: Seq<char>)
    ensures
        matches(mk_alt(a, b), s) == matches(Re::Alt(Box::new(a), Box::new(b)), s),
        is_norm(a) && is_norm(b) ==> is_norm(mk_alt(a, b)),
{
    assert(!matches(Re::Empty, s));
}
// reference-only
pub proof fn lemma_mk_cat_r10_ref(a: Re, b: Re, s: Seq<char>)
    ensures
        matches(mk_cat(a, b), s) == matches(Re::Cat(Box::new(a), Box::new(b)), s),
        is_norm(a) && is_norm(b) ==> is_norm(mk_cat(a, b)),
{
    let cat = Re::Cat(Box::new(a), Box::new(b));
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
    if matches(cat, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(
                b,
                s.subrange(i, s.len() as int),
            );
        if a is Eps {
            assert(i == 0);
        } else if b is Eps {
            assert(i == s.len());
        }
    }
    if a is Eps && !(b is Empty) && matches(b, s) {
        assert(matches(a, s.subrange(0, 0)));
    }
    if b is Eps && !(a is Empty) && !(a is Eps) && matches(a, s) {
        assert(matches(a, s.subrange(0, s.len() as int)));
    }
}
// reference-only
pub proof fn lemma_mk_star_r10_ref(a: Re, s: Seq<char>)
    ensures
        matches(mk_star(a), s) == matches(Re::Star(Box::new(a)), s),
        is_norm(a) ==> is_norm(mk_star(a)),
{
    if a is Empty || a is Eps {
        if s.len() > 0 && matches(Re::Star(Box::new(a)), s) {
            let i = choose|i: int|
                1 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(
                    Re::Star(Box::new(a)),
                    s.subrange(i, s.len() as int),
                );
            assert(matches(a, s.subrange(0, i)));
        }
    } else if a is Star {
        lemma_star_star_r10_ref(*a->Star_0, s);
    }
}
// item: R10.A1v
fn build_alt_r10(a:NormRe,b:NormRe)->(out:NormRe)
 ensures equiv(out.re(),Re::Alt(Box::new(a.re()),Box::new(b.re()))),
{
 let ar=a.into_pattern_r10();
 let br=b.into_pattern_r10();
 proof {
  lemma_alt_shape_r10(ar,br);
  assert forall|s:Seq<char>| #[trigger] matches(mk_alt(ar,br),s)==matches(Re::Alt(Box::new(ar),Box::new(br)),s) by {lemma_mk_alt_r10_ref(ar,br,s);}
 }
 let raw=mk_alt_exec(ar,br);
 NormRe::from_normal_r10(raw)
}

fn build_cat_r10(a:NormRe,b:NormRe)->(out:NormRe)
 ensures equiv(out.re(),Re::Cat(Box::new(a.re()),Box::new(b.re()))),
{
 let ar=a.into_pattern_r10();
 let br=b.into_pattern_r10();
 proof {
  lemma_cat_shape_r10(ar,br);
  assert forall|s:Seq<char>| #[trigger] matches(mk_cat(ar,br),s)==matches(Re::Cat(Box::new(ar),Box::new(br)),s) by {lemma_mk_cat_r10_ref(ar,br,s);}
 }
 let raw=mk_cat_exec(ar,br);
 NormRe::from_normal_r10(raw)
}

fn build_star_r10(a:NormRe)->(out:NormRe)
 ensures equiv(out.re(),Re::Star(Box::new(a.re()))),
{
 let ar=a.into_pattern_r10();
 
 proof {
  lemma_star_shape_r10(ar);
  assert forall|s:Seq<char>| #[trigger] matches(mk_star(ar),s)==matches(Re::Star(Box::new(ar)),s) by {lemma_mk_star_r10_ref(ar,s);}
 }
 let raw=mk_star_exec(ar);
 NormRe::from_normal_r10(raw)
}
}
