"""Generate small unsigned NRRD inputs and valid planes, without downloads."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import nrrd


def generate_datasets(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    x, y, z = np.indices((16, 16, 16), dtype=np.uint64)
    encoded = x + 16*y + 256*z
    manifest = {"formula": "floor((x+16*y+256*z)*dtype_max/4095)",
                "index_order": "F", "datasets": []}
    for dtype in (np.uint8, np.uint16, np.uint32):
        maximum = np.iinfo(dtype).max
        volume = (encoded * maximum // 4095).astype(dtype)
        path = directory / f"synthetic-{np.dtype(dtype).name}.nrrd"
        nrrd.write(str(path), volume, index_order="F")
        manifest["datasets"].append({
            "file": path.name, "shape": list(volume.shape), "dtype": str(volume.dtype),
            "minimum": int(volume.min()), "maximum": int(volume.max()),
            "voxel_sha256_c_order": hashlib.sha256(volume.tobytes(order="C")).hexdigest(),
        })
    (directory / "planes.csv").write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
        "3,2,2,3,2,10,3,10,2,3,,,\n"
        "4,3,3,6,9,3,6,2,10,6,10,10,6\n"
        "3,2,2,8,2,10,8,10,2,8,,,\n", encoding="utf-8")
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path("data/generated"))
    args = parser.parse_args()
    manifest = generate_datasets(args.directory)
    print(f"Generated {len(manifest['datasets'])} NRRD files, planes.csv and manifest.json in {args.directory}")


if __name__ == "__main__":
    main()
