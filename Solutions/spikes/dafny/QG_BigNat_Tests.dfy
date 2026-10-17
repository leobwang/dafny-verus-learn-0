// QG_BigNat_Tests.dfy -- DV0 spike: concrete-value checks of the compiled
// BigNat code, run with `dafny test --target py --standard-libraries`.
// Expected values were computed independently with Python big integers
// (probe spike-dafny/expected-values). `expect` appears only inside
// {:test} methods.

module QG_BigNat_Tests {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  const M: nat := 18446744073709551615  // BASE - 1

  method {:test} TestAdd()
  {
    var r1 := AddLoop([M, M], [1]);
    expect r1 == [0, 0, 1];
    expect r1 == Add([M, M], [1]);
    expect ToNat(r1) == ToNat([M, M]) + 1;
    var r2 := AddLoop([M], [M]);
    expect r2 == [M - 1, 1];
    var r3 := AddLoop([], []);
    expect r3 == [];
    var r4 := AddLoop([5], [7, 9]);
    expect r4 == [12, 9];
    var r5 := AddLoop([M, 0, 3], [1]);
    expect r5 == [0, 1, 3];
    expect ToNat(r5) == 1020847100762815390408570566369014185984;
  }

  method {:test} TestMulLimb()
  {
    var r1 := MulLimbLoop([M, M], M);
    expect r1 == [1, M, M - 1];
    expect r1 == MulLimb([M, M], M);
    expect ToNat(r1) == ToNat([M, M]) * M;
    var r2 := MulLimbLoop([3], 5);
    expect r2 == [15];
    var r3 := MulLimbLoop([1, 2], 0);
    expect r3 == [0, 0];               // a non-canonical zero
    expect ToNat(r3) == 0;
    expect Normalize(r3) == [];
    var r4 := MulLimbLoop([], 7);
    expect r4 == [];
  }

  method {:test} TestMul()
  {
    expect Normalize(Mul([M, M], [M, M])) == [1, 0, M - 1, M];
    expect Normalize(Mul([3, 4], [5, 6])) == [15, 38, 24];
    expect ToNat(Mul([3, 4], [5, 6])) == ToNat([3, 4]) * ToNat([5, 6]);
  }

  method {:test} TestCmpNormalizeFromNat()
  {
    expect Cmp([0, 1], [M]) == 1;
    expect Cmp([M], [0, 1]) == -1;
    expect Cmp([5, 0], [5]) == 0;      // value order, not length order
    expect Cmp([4, 1], [5, 1]) == -1;
    expect Cmp([7, 2, 0], [9, 1]) == 1;
    var n1 := NormalizeLoop([5, 0, 0]);
    expect n1 == [5];
    expect n1 == Normalize([5, 0, 0]);
    expect FromNat(18446744073709551616) == [0, 1];
    expect FromNat(340282366920938463463374607431768211463) == [7, 0, 1];
    expect ToNat(FromNat(123456789012345678901234567890)) == 123456789012345678901234567890;
    expect AddLimb([M, M], 1) == [0, 0, 1];
  }
}
