// Param math — computed from spec shapes, NEVER hand-written numbers in UI text.
// Ported VERBATIM from viz/src/engine/params.ts (dense section) so flow and
// viz stay in exact agreement; integer anchors below are unit-tested.

/** Dense shape inputs — locally declared so flow has no viz/ coupling. */
export interface DenseShape {
  layers: number;
  d: number;
  heads: number;
  kv: number;
  ffn: number;
  vocab: number;
}

// Dense anchors (unit-tested): nano_SLMs 226,526,208 · SmolLM2-135M 134,515,008.
// Norm accounting: pre-norm ×2 per layer + 1 final norm = (2L+1)·d — counted ONCE.
export function headDim(s: { d: number; heads: number }): number {
  return Math.floor(s.d / s.heads);
}
export function kvDim(s: { d: number; heads: number; kv: number }): number {
  return s.kv * headDim(s);
}
export function pEmbed(s: { d: number; vocab: number }): number {
  return s.vocab * s.d;
}
export function pAttentionDense(s: { d: number; heads: number; kv: number }): number {
  const kv = kvDim(s);
  return 2 * s.d * s.d + 2 * s.d * kv; // WQ,WO (square) + WK,WV (d×kvdim)
}
export function pFFNDense(s: { d: number; ffn: number }): number {
  return 3 * s.d * s.ffn; // gate + up + down (SwiGLU, no bias)
}
export function pNorms(s: { d: number; layers: number }): number {
  return (2 * s.layers + 1) * s.d;
}
export function pLayerDense(s: { d: number; heads: number; kv: number; ffn: number }): number {
  return pAttentionDense(s) + pFFNDense(s) + 2 * s.d; // + per-layer weight of the two norms counted via pNorms? no — norms counted separately
}
// pTotal — norms counted exactly once (NOT inside the per-layer loop):
export function pTotalDense(s: DenseShape): number {
  return pEmbed(s) + s.layers * (pAttentionDense(s) + pFFNDense(s)) + pNorms(s);
}
