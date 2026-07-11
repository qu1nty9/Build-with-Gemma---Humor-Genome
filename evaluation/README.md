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

Generated results should only be committed after the model, prompt version, runtime, and sampling configuration have been frozen.

