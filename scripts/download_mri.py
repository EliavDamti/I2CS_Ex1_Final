"""Download Slicer's canonical MRHead NRRD and verify its published SHA256."""
import argparse
import hashlib
from pathlib import Path
import urllib.request

SHA256 = "cc211f0dfd9a05ca3841ce1141b292898b2dd2d3f08286affadf823a7e58df93"
URL = "https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/" + SHA256


def download_mri(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to replace existing dataset: {path}")
    with urllib.request.urlopen(URL, timeout=60) as response:
        contents = response.read()
    if hashlib.sha256(contents).hexdigest() != SHA256:
        raise ValueError("Downloaded MRHead SHA256 does not match Slicer's published hash")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as file:
        file.write(contents)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/MRHead-canonical.nrrd"))
    args = parser.parse_args()
    print(f"Saved verified MRI dataset: {download_mri(args.path)}")


if __name__ == "__main__":
    main()
