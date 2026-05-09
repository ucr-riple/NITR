## Task

Extend the detector benchmark so it reports both the highest-accuracy model and
the best speed-adjusted model.

### Requirements
- Keep the existing accuracy-based benchmark behavior working.
- Add a speed-adjusted score computed as `average_precision * fps / 100.0`.
- Report both the accuracy winner and the speed-adjusted winner in the final
  benchmark summary.
- Preserve support for comparing D-FINE and RT-DETR benchmark rows.

### Constraints
- Do not modify `app/main.cc`.
- You may modify files under `src/` and add new files under `src/` if needed.
- Do not modify evaluator files.
