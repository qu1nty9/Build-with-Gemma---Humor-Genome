# Runtime benchmark log

Measured locally on 11 July 2026.

## Environment

- Hardware: Apple M1 Pro, 10 CPU cores, 16 GB unified memory.
- Runtime: Ollama 0.30.7, 100% Metal/GPU execution.
- Models: `gemma4:e2b` for the interactive path and `gemma4:12b` for the offline comparison, both served as quantized Ollama artifacts.
- Pipeline: versioned prompts, Pydantic JSON Schema, `think=false`, temperature 0.35.

## Measurements

| Run | Result | Wall time | Interpretation |
|---|---|---:|---|
| Minimal prompt: “Reply with exactly OK” | Completed, but produced extra thinking artifacts in CLI output | 27.35 s | 12B has too much base latency for the interactive path |
| Initial full flow, one joke | Failed at fenced JSON after repair | 264.145 s | Repair inference was triggered for a locally fixable Markdown wrapper |
| Optimized `analyze`, smart-fridge joke | Valid structured `HumorGenome` | 51.57 s | High quality, still too slow for live UX |
| E2B `analyze`, therapy-fee joke | Valid structured `HumorGenome` | 22.476 s | First measured E2B run; suitable for progressive UI |
| E2B warm `analyze`, same joke | Valid structured `HumorGenome` | 15.644 s | Warm-state interactive latency is acceptable |
| 12B `analyze`, same comparison run | Valid structured `HumorGenome` | 58.422 s | Approximately 2.6× slower than the paired E2B run |
| E2B full flow after mutation fixes | Valid `analyze → mutate → compare` result | 45.828 s | Meets the MVP target of a complete flow in under 60 seconds |

## Quality observation

The successful 12B analysis correctly identified:

- premise: a high-tech appliance gives technically healthy but practically absurd advice;
- strongest mechanisms: misdirection, incongruity, and irony;
- no unsupported cultural dependencies or safety risks;
- two plausible alternative readings: smart-device satire and self-deprecation.

On the therapy-fee comparison, E2B identified `irony`, `incongruity`, and `understatement`; 12B identified `irony` and `misdirection`. The exact mechanism-set Jaccard score was 0.25, but both analyses agreed on the central transactional irony. This illustrates why mechanism agreement is a diagnostic rather than ground truth.

The first E2B brevity mutation attempts failed the semantic gate in about 23 seconds because the model interpreted any surface wording change as a second comedy gene and returned three variants when two were requested. This produced two concrete fixes:

- “one gene” is now defined as one intentional editing dimension; necessary wording changes are allowed when premise, mechanism, punchline meaning, and voice remain stable;
- extra variants are deterministically trimmed to the requested count before quality validation.

After these fixes, the same E2B configuration completed the full therapy-fee flow successfully. It produced exactly two `brevity` variants, marked both as changing only the requested gene, preserved the premise and author voice, and passed the independent mutation validator. Stage latency was 22.404 seconds for analysis, 10.441 seconds for mutation, and 12.979 seconds for comparison.

## Decisions resulting from the spike

1. Use `gemma4:e2b` as the interactive candidate.
2. Keep `gemma4:12b` as an offline quality benchmark.
3. Strip Markdown fences locally before spending another model call on repair.
4. Limit output lists and set an explicit 1,200-token output budget.
5. Call `compare` only after the human makes a blind A/B choice.
6. Keep model self-assessment in the output, but enforce it in an independent deterministic validator with explicit regeneration feedback.
7. Promote E2B from interactive candidate to the primary MVP runtime after the successful sub-60-second full flow.

These are engineering measurements on one machine, not final competition results. The same examples must be rerun on E2B and on the eventual hosted runtime.
