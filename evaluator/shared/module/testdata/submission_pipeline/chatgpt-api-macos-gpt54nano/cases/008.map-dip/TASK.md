## Task Description
Refactor the implementation to satisfy DIP **without changing the observable behavior** for existing layers.

### Behavioral requirements
- `map_snapshot` reads a JSON config from a file path argument.
- It reads all stdin as the input payload string.
- It outputs the exact stable text snapshot format expected by the tests, including the header line.

### Constraints
You **must not** modify:
- `app/main.cc`
- The public signature of `MapSnapshotService::BuildSnapshot(...)`

You **may**:
- Add new files/classes
- Modify files under `src/`
- Introduce a registry/factory mechanism

### Plugin requirement (killer DIP test)
The evaluator will compile an extra translation unit that registers a new layer type:
- `reverse_payload` — reverses the stdin payload string and returns it as a layer.

Your solution must pass this test **without modifying** the snapshot core logic.
Built-in layer support must also avoid hardcoded concrete provider construction inside the snapshot core.
