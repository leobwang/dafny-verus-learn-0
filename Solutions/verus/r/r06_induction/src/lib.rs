/*! R06 — Induction and loops (Reference Solution).
Standalone R, A1/A1b only. The given Deriv and deriv_exec are complete;
no A2 or earlier learner proof is imported. Five holes in each hand file
(T1 and H1-H4); two code test-outs, six predictions and four unseen exits.
T1 is closed book before the worked examples. Record all prediction/test-out
first tries with scripts/firsttry.sh R06 --check before enabling switches.
H1 needs your measure. H2 retains its loop, decreasing measure and proof call;
supply invariants and connecting facts. H4 opens only its requires clause:
repair with the weakest hypothesis, not an arbitrary sufficient restriction.
Done: complete zero-hole native gates, audit, freeze, strict report, checkpoint,
written work, decomposer review, fifth bench card, viva and calibration.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use rg_re_a1::*;
use rg_re_a1b::*;
verus! {
// GIVEN: specification and proved executable derivative.
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}
pub fn deriv_exec(r: &Re, c: char) -> (out: Re)
    ensures
        out == deriv(*r, c),
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == *d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv_exec(a, c)), Box::new(deriv_exec(b, c))),
        Re::Cat(a, b) => if is_nullable(a) {
            Re::Alt(
                Box::new(Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))),
                Box::new(deriv_exec(b, c)),
            )
        } else {
            Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))
        },
        Re::Star(a) => Re::Cat(Box::new(deriv_exec(a, c)), Box::new(Re::Star(Box::new(copy_re(a))))),
    }
}

// item: R06.T1v
// pair: R06.T1d
// uses: invariant
// Closed book before reading; implement with a while loop.
pub fn all_nullable(rs: &Vec<Re>) -> (b: bool)
    ensures b == (forall|i:int| 0 <= i < rs.len() ==> nullable(#[trigger] rs@[i])),
{
    // @impl-begin R06.T1v
    let mut b=true;let mut i:usize=0;
    while i < rs.len()
        invariant i <= rs.len(),
            b == (forall|j:int| 0 <= j < i ==> nullable(#[trigger] rs@[j])),
        decreases rs.len()-i,
    {
        b = b && is_nullable(&rs[i]);
        i=i+1;
    }
    b
    // @impl-end R06.T1v
}

// item: R06.W1v
pub proof fn lemma_deriv_base(r: Re,c: char,s: Seq<char>)
    requires r is Empty || r is Eps || r is Chr,
    ensures matches(deriv(r,c),s) <==> matches(r,seq![c]+s),
{
    match r {
        Re::Chr(d) => { assert((seq![c]+s)[0] == c); },
        _ => { },
    }
}
// item: R06.W2v
pub fn all_same(s: &Vec<char>,c: char) -> (b: bool)
    ensures b == (forall|j:int| 0 <= j < s.len() ==> #[trigger] s@[j] == c),
{
    let mut b=true;let mut i:usize=0;
    while i < s.len()
        invariant i <= s.len(),b == (forall|j:int| 0 <= j < i ==> #[trigger] s@[j] == c),
        decreases s.len()-i,
    { b = b && s[i] == c; i=i+1; }
    b
}
// item: R06.C1v write:calc
// calc! states its relation and each justified intermediate expression.
// item: R06.C2v write:invariant
// The invariant relates the visited prefix to the accumulator.
// item: R06.C3v write:lemma-decreases
// A recursive proof fn gives a well-founded decreasing measure.

// item: R06.H1v
// pair: R06.H1d
// uses: lemma-decreases, calc
// The measure is yours; prove every constructor.
pub proof fn lemma_deriv_correct(r: Re,c: char,s: Seq<char>)
    ensures matches(deriv(r,c),s) <==> matches(r,seq![c]+s),
    decreases r,
{
    // @hole-begin R06.H1v
    calc! {
      (==)
      matches(deriv(r,c),s); {

    let w = seq![c] + s;
    assert(w.len() == s.len() + 1);
    match r {
        Re::Chr(d) => {
            assert(w[0] == c);
        },
        Re::Alt(a, b) => {
            lemma_deriv_correct(*a, c, s);
            lemma_deriv_correct(*b, c, s);
        },
        Re::Cat(a, b) => {
            let da = deriv(*a, c);
            let cat = Re::Cat(Box::new(da), b);
            lemma_nullable_correct(*a);
            assert(w.subrange(0, 0) =~= Seq::<char>::empty());
            assert(w.subrange(0, w.len() as int) =~= w);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        *b,
                        w.subrange(i, w.len() as int),
                    );
                if i == 0 {
                    lemma_deriv_correct(*b, c, s);
                } else {
                    lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                    assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                    assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                    assert(matches(da, s.subrange(0, i - 1)));
                    assert(matches(cat, s));
                }
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(cat, s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        *b,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
            if nullable(*a) && matches(deriv(*b, c), s) {
                lemma_deriv_correct(*b, c, s);
                assert(matches(*a, w.subrange(0, 0)));
            }
        },
        Re::Star(a) => {
            let da = deriv(*a, c);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                assert(matches(da, s.subrange(0, i - 1)));
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(deriv(r, c), s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        r,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
        },
        _ => {},
    }

      }
      matches(r,seq![c]+s);
    }
    // @hole-end R06.H1v
}

// item: R06.H2v
// pair: R06.H2d
// uses: invariant
pub fn deriv_match(r: &Re,s: &Vec<char>) -> (b: bool)
    ensures b == matches(*r,s@),
{
    // @hole-begin R06.H2v
    assert(s@.subrange(0,s@.len() as int) =~= s@);
    // @hole-end R06.H2v
    let mut cur=copy_re(r);let mut i:usize=0;
    while i < s.len()
        // @hole-begin R06.H2v
        invariant i <= s.len(),
            matches(cur,s@.subrange(i as int,s@.len() as int)) == matches(*r,s@),
        // @hole-end R06.H2v
        decreases s.len()-i,
    {
        proof {
            lemma_deriv_correct(cur,s@[i as int],s@.subrange(i+1,s@.len() as int));
            // @hole-begin R06.H2v
            assert(seq![s@[i as int]]+s@.subrange(i+1,s@.len() as int) =~= s@.subrange(i as int,s@.len() as int));
            // @hole-end R06.H2v
        }
        cur=deriv_exec(&cur,s[i]);
        i=i+1;
    }
    // @hole-begin R06.H2v
    proof { lemma_nullable_correct(cur); assert(s@.subrange(i as int,s@.len() as int) =~= Seq::<char>::empty()); }
    // @hole-end R06.H2v
    is_nullable(&cur)
}

// item: R06.H3v
// pair: R06.H3d
pub proof fn lemma_star_unfold_refuted()
    ensures exists|a:Re,s:Seq<char>| matches(Re::Star(Box::new(a)),s) && !matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s),
{
    // @hole-begin R06.H3v
    let a=Re::Chr('x');let s=Seq::<char>::empty();
    assert(s.subrange(0,0) =~= Seq::<char>::empty());
    assert(matches(Re::Star(Box::new(a)),s));
    assert forall|i:int| 0 <= i <= s.len() implies !matches(a,#[trigger] s.subrange(0,i)) by { }
    assert(!matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s));
    // @hole-end R06.H3v
}

// item: R06.H4v
// pair: R06.H4d
// uses: calc
// REPAIR: add the weakest sufficient requires; retain the exact postcondition.
pub proof fn lemma_star_unfold(a: Re,s: Seq<char>)
    requires s.len() > 0 || nullable(a),
    ensures matches(Re::Star(Box::new(a)),s) <==> matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s),
{
    // @hole-begin R06.H4v

    calc! {
      (==)
      matches(Re::Star(Box::new(a)),s); {
        let st=Re::Star(Box::new(a));
        if s.len() == 0 {
          lemma_nullable_correct(a);
          assert(s.subrange(0,0) =~= Seq::<char>::empty());
          assert(s =~= Seq::<char>::empty());
          assert(matches(a,s.subrange(0,0)));
        }
        if matches(st,s) && s.len() > 0 {
          let i=choose|i:int| 1 <= i <= s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(st,s.subrange(i,s.len() as int));
          assert(matches(Re::Cat(Box::new(a),Box::new(st)),s));
        }
        if matches(Re::Cat(Box::new(a),Box::new(st)),s) {
          let i=choose|i:int| 0 <= i <= s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(st,s.subrange(i,s.len() as int));
          if i == 0 { assert(s.subrange(i,s.len() as int) =~= s); }
          else { assert(matches(st,s)); }
        }
      }
      matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s);
    }
    // @hole-end R06.H4v
}
} // verus!
