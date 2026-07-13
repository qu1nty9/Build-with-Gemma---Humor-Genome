# Evaluation

`examples.jsonl` contains 10 project-original, AI-assisted CC0 seed jokes and the comedy gene selected for controlled editing. Two `brevity` rows are pilot-validated, two more brevity rows and five `misdirection` rows are under revalidation, and one `specificity` row is retained as an explicit failure case. See [`DATASET_CARD.md`](DATASET_CARD.md) for provenance and limitations. The set must still grow to 30–50 licensed examples before final evaluation.

Validate schema, provenance metadata, uniqueness, license allowlist, and calibration labels before any model run:

```bash
.venv/bin/python evaluation/validate_dataset.py \
  --input evaluation/examples.jsonl \
  --min-examples 10
```

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

Run the deliberately weaker one-shot baseline without HumorGenome analysis, explicit invariants, or semantic feedback/regeneration. It shares only transport-level JSON repair with the main pipeline:

```bash
GEMMA_MODEL=gemma4:e2b .venv/bin/python evaluation/run_baseline.py \
  --input evaluation/examples.jsonl \
  --output evaluation/results/e2b-baseline.jsonl
```

Audit pipeline or baseline variants with the slower 12B Gemma model:

```bash
.venv/bin/python evaluation/run_teacher_audit.py \
  --input evaluation/results/e2b-pipeline.jsonl evaluation/results/e2b-baseline.jsonl \
  --output evaluation/results/teacher-audit.jsonl \
  --teacher-model gemma4:12b

.venv/bin/python evaluation/summarize_teacher_audit.py \
  --input evaluation/results/teacher-audit.jsonl \
  --output-json evaluation/reports/teacher-summary.json \
  --output-md evaluation/reports/teacher-summary.md
```

The teacher rubric measures target-gene isolation, premise preservation, non-target-mechanism preservation, and whether the edit is meaningful. It never scores funniness and must be reported as a model-based diagnostic rather than ground truth.
