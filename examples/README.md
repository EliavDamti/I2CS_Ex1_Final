# Additional plane lists

These CSVs are the supplied inputs, moved here without changing coordinates
or row order. Both use the assignment's numbered-coordinate format.

| CSV | Local volume | Output |
|---|---|---|
| biscuit_cake.csv | data/biscuit_cake.nrrd | results/biscuit.mp4 |
| croissant.csv | data/croissant.nrrd | results/croissant.mp4 |

Run from the repository root:

```bash
python Ex0.py data/biscuit_cake.nrrd examples/biscuit_cake.csv results/biscuit.mp4
python Ex0.py data/croissant.nrrd examples/croissant.csv results/croissant.mp4
```

Large NRRDs are local inputs and are excluded from Git. Their dimensions,
types and source hashes are recorded in docs/DATASET.md and
results/examples-validation.json. Public MRI and synthetic alternatives are
available without these local inputs.

The croissant CSV contains 100 triangles with large viewpoint changes,
not a sequence of parallel neighboring cuts. Its abrupt video transitions
are expected. The biscuit list contains 120 equal-base trapezoids.
