# Humor Genome evaluation dataset card

## Summary

`examples.jsonl` is a small synthetic dataset for engineering and human-evaluation experiments in Humor Genome Lab. It tests whether Gemma can analyze a short joke and produce counterfactual edits that change one requested comedy gene while preserving the premise and non-target mechanisms.

The initial seed release contains 10 English one- or two-sentence jokes:

- 4 calibrated `brevity` cases;
- 5 `misdirection` cases marked for revalidation after a local runtime update changed structured-output behavior;
- 1 deliberately experimental `specificity` case retained as a documented failure case.

This seed set is for pipeline calibration, not a statistically meaningful humor benchmark. The final evaluation target is 30–50 examples with a frozen held-out split.

## Provenance

Every row is project-original and AI-assisted. No external joke corpus, social-media post, stand-up transcript, or scraped text was used. Rows are labeled `source=project-original-ai-assisted` so they cannot be confused with naturally occurring audience data.

The examples are made available under `CC0-1.0`, as recorded per row. They contain no personal data and no claims about real people. Before the final public release, the repository owner should review the wording and confirm the dataset dedication.

## Schema

- `id`: stable unique identifier;
- `text`: source joke;
- `source`: provenance category;
- `license`: per-row reuse terms;
- `split`: `seed`, `evaluation`, or `demo`;
- `calibration_status`: `calibrated`, `revalidation`, or `experimental` under the current frozen runtime;
- `target_gene`: the single requested editing dimension;
- `expected_mechanisms`: hypotheses for error analysis, not ground-truth labels.

## Intended use

- structured-output and latency regression tests;
- comparison of the E2B interactive runtime with the 12B offline teacher;
- blind human A/B evaluation of controlled edits;
- transparent success, disagreement, and failure examples in the Kaggle write-up.

## Limitations

- Synthetic English jokes are not representative of global humor.
- Mechanism tags are hypotheses and may overlap.
- Model self-checks do not establish that only one gene changed.
- Passing a validator is not evidence that a variant is funnier.
- The seed set is too small for population-level conclusions.
