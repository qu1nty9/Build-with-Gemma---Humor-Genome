# Evaluation

`examples.jsonl` contains original CC0 test jokes and the comedy gene selected for controlled editing. It is intentionally small during the vertical-slice phase and must grow to 30–50 licensed examples before final evaluation.

Run the current model over the dataset:

```bash
.venv/bin/python evaluation/run_smoke.py \
  --input evaluation/examples.jsonl \
  --output evaluation/results/gemma4-12b-smoke.jsonl
```

Each output row records:

- example and model identifiers;
- wall-clock latency;
- success or structured failure;
- the complete validated flow result.

Use `--ids calendar_001` for a focused regression run without repeating the entire dataset.

Generated results should only be committed after the model, prompt version, runtime, and sampling configuration have been frozen.

Compare the analysis stage across the interactive and benchmark models:

```bash
.venv/bin/python evaluation/compare_models.py \
  --models gemma4:e2b gemma4:12b \
  --input evaluation/examples.jsonl \
  --output evaluation/results/model-comparison.jsonl
```

The script reports latency and Jaccard agreement between the sets of detected comedy mechanisms. Agreement is a diagnostic, not a ground-truth humor metric.

Create a machine-readable summary and a table ready for the Kaggle write-up:

```bash
.venv/bin/python evaluation/summarize_results.py \
  --input evaluation/results/gemma4-e2b-full.jsonl \
  --output-json evaluation/reports/summary.json \
  --output-md evaluation/reports/summary.md
```

The summary reports completion rate, controlled-mutation pass rate, variant self-check rate, p50/p95 latency, per-stage latency, target-gene coverage, and dataset-license coverage. It deliberately does not treat model agreement or self-assessment as a measure of whether a joke is funny; blind human A/B preference is a separate evaluation layer.
