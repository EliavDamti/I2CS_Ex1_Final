# Submitted outputs

These files are outputs and verification evidence; they are not prerequisites
for running Ex0.py. See the root README for setup and reproduction commands.

| File | Purpose |
|---|---|
| demo.mp4 | Required MRI demo: one frame per row in demo_planes.csv |
| showcase.mp4 | Supplemental labeled 720p presentation |
| demo_planes.csv | Exact 60 ordered MRI planes |
| demo-manifest.json | Source hashes, planes and presentation metadata |
| demo-validation.json | Full MRI video decoding and frame-comparison summary |
| demo-poster.png | Preview of the presentation |
| biscuit.mp4 | 120 planes from examples/biscuit_cake.csv |
| croissant.mp4 | 100 planes from examples/croissant.csv |
| examples-validation.json | Source hashes and all-frame checks for both examples |
| synthetic-uint32.mp4 | Three-frame unsigned-32 generator example |
| benchmark.json | One benchmark of the final source, including raw timings |

The benchmark JSON is intentionally detailed so the concise FPS table in
docs/RESULTS.md can be audited. Earlier reports are available in Git history.
Other local generated videos/images are ignored. The local/ directory, when
present, preserves pre-submission exploratory outputs and is not committed.
