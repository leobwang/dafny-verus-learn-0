/*!
# R16 — Capstone: the statements (Exercises)

The file in which you state what it means for the emitter to be correct. You
write the two definitions below (H1), have them reviewed statement-only
(`/review R16 --statements`), then commit them: from that commit on they are
frozen. The registry lists this file under R16's `statements` (pending until
your commit), `scripts/specfreeze --check R16` compares every later change with
your committed statements, and Lab γ's crate tasks unpack only after it.

The paired statement file is verus/r/r16_capstone/src/statements.rs. The
proofs (H2, H3) and the whole-program theorem (H5) are in R16_Capstone.dfy;
nothing else goes in this file.
*/

module R16_Statements {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A5_VM

  // item: R16.H1d
  // pair: R16.H1v
  /** **H1.** State the emitter's two correctness facts for the code of `r`
      placed at `pc` inside a larger program `p`, with whatever code follows it
      left free. Completeness: when `r` matches `u` and the code after `r`'s
      accepts `v` from its first address, the code of `r` accepts `u + v` from
      `pc`. Soundness, the converse: when `r`'s code accepts `w` from `pc`, `w`
      splits into a part `r` matches and a rest the following code accepts. Use
      A5's `CodeAt`, `Emit` and `AcceptsFrom` (never the fuelled `Accepts`).
      Why must neither statement say that the program ends after `r`'s code,
      and what does the soundness split have to bound? (The benign `ensures
      true` only makes each missing definition a tool-counted hole.) */
  ghost predicate EmitCompleteStatement(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>)
    ensures true
  // HOLE: write the definition body.

  ghost predicate EmitSoundStatement(p: Prog, r: Re, pc: int, w: seq<char>)
    ensures true
  // HOLE: write the definition body.
  // Hint(1): each statement is one implication over all programs `p` that hold `Emit(r, pc)` at `pc`; the continuation is whatever starts at `pc + |Emit(r, pc)|`.
  // Hint(2): read A5's `EmitProg` and `LayoutProg`: the whole program is the special case whose continuation is one `IMatch`; your statements must give back `EmitCorrect` (H5) there, and a split point needs both ends of its range.
}
