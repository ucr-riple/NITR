# Submission Pipeline Fixtures

This directory contains a small set of vendored generated-case fixtures copied
from local `.submit-output/` runs.

Purpose:

- provide deterministic integration coverage for
  `evaluator/run_evaluation_pipeline.py`
- keep submit-style regression samples under version control
- make it easy to add more samples without editing test logic

The fixture manifest is `manifest.json`.

Each sample is stored as:

```text
<backend>/cases/<case_slug>/
```

When adding a new sample:

1. copy the generated case directory from `.submit-output/<backend>/cases/<case_slug>/`
2. remove local-only noise such as `.DS_Store`
3. add one manifest entry in `manifest.json`
4. run `python3 -m unittest evaluator.shared.module.tests.test_submission_pipeline_integration -v`

Test behavior:

- defaults to this directory as its fixture root
- can be pointed at another root with `NITR_SUBMIT_OUTPUT_ROOT`
- fails if the manifest is empty
- skips cleanly when the configured fixture root or manifest does not exist
