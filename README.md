# Humor Genome Lab

**Edit one comedy gene at a time—and see why the joke changes.**

Humor Genome Lab uses Gemma to turn a joke into a structured map of comedic mechanisms, create counterfactual variants that change one mechanism at a time, and compare the resulting trade-offs without pretending to predict an objective audience reaction.

## Current status

The repository contains the first text-first vertical slice:

1. `analyze` converts a joke and its context into a validated `HumorGenome`.
2. `mutate` creates controlled variants for one selected comedy gene.
3. `compare` describes the differences and uncertainties between variants.
4. The responsive web UI visualizes the genome and reveals model trade-offs only after a blind A/B choice.

The default interactive runtime is `gemma4:e2b` through Ollama. `gemma4:12b` is reserved for slower offline quality comparisons. The model adapter is isolated from the domain pipeline so it can later be replaced by an official Hugging Face or hosted Gemma runtime.

On the reference M1 Pro environment, E2B completed the validated `analyze → mutate → compare` flow in 45.8 seconds. Reproducible engineering measurements and known failure cases are recorded in [`evaluation/BENCHMARK_LOG.md`](evaluation/BENCHMARK_LOG.md).

## Quickstart

Requirements: Python 3.11+ and Ollama.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
ollama pull gemma4:e2b
ollama serve
```

Run the API:

```bash
.venv/bin/uvicorn app.api:app --reload
```

Then open `http://127.0.0.1:8000/`. The interactive API documentation remains available at `http://127.0.0.1:8000/docs`.

Run the complete text flow:

```bash
.venv/bin/humor-genome flow \
  --text "I told my therapist I worry about money. She said we can discuss it next session—for the usual fee." \
  --target-gene brevity
```

Run analysis only:

```bash
.venv/bin/humor-genome analyze --text "My smart fridge sends me health tips."
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## API

- `POST /v1/analyze`
- `POST /v1/mutate`
- `POST /v1/compare`
- `POST /v1/flow`
- `POST /v1/feedback` — stores the joke and blind choice only after explicit UI opt-in

The web UI deliberately calls `analyze` and `mutate` first. It calls `compare` only after the user makes a blind choice, avoiding unnecessary model latency before human input. `flow` remains available for offline evaluation.

`brevity` and `misdirection` are the currently calibrated demo genes. The UI labels the remaining genes as experimental until they pass the planned multi-example human or teacher audit; known failures are reported in the benchmark log.

## Tests

```bash
.venv/bin/pytest
```

## Safety and scope

- The tool does not claim to know what an audience will find objectively funny.
- Model confidence is exposed and alternative readings are preserved.
- API keys and model credentials must remain server-side.
- Public evaluation examples must be original, public domain, or permissively licensed.
- A/B material is persisted locally only when the user explicitly selects the evaluation opt-in checkbox.

The full hackathon strategy is documented in [`HACKATHON_PLAN_RU.md`](HACKATHON_PLAN_RU.md).
