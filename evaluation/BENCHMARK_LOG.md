# Runtime benchmark log

Measured locally on 11 July 2026.

## Environment

- Hardware: Apple M1 Pro, 10 CPU cores, 16 GB unified memory.
- Runtime: Ollama 0.30.7, 100% Metal/GPU execution.
- Model: `gemma4:12b`, quantized Ollama artifact, approximately 7.6 GB on disk and 8.0 GB loaded.
- Pipeline: versioned prompts, Pydantic JSON Schema, `think=false`, temperature 0.35.

## Measurements

| Run | Result | Wall time | Interpretation |
|---|---|---:|---|
| Minimal prompt: “Reply with exactly OK” | Completed, but produced extra thinking artifacts in CLI output | 27.35 s | 12B has too much base latency for the interactive path |
| Initial full flow, one joke | Failed at fenced JSON after repair | 264.145 s | Repair inference was triggered for a locally fixable Markdown wrapper |
| Optimized `analyze`, smart-fridge joke | Valid structured `HumorGenome` | 51.57 s | High quality, still too slow for live UX |

## Quality observation

The successful 12B analysis correctly identified:

- premise: a high-tech appliance gives technically healthy but practically absurd advice;
- strongest mechanisms: misdirection, incongruity, and irony;
- no unsupported cultural dependencies or safety risks;
- two plausible alternative readings: smart-device satire and self-deprecation.

## Decisions resulting from the spike

1. Use `gemma4:e2b` as the interactive candidate.
2. Keep `gemma4:12b` as an offline quality benchmark.
3. Strip Markdown fences locally before spending another model call on repair.
4. Limit output lists and set an explicit 1,200-token output budget.
5. Call `compare` only after the human makes a blind A/B choice.

These are engineering measurements on one machine, not final competition results. The same examples must be rerun on E2B and on the eventual hosted runtime.

