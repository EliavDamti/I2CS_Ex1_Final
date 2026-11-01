import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import nrrd

from Ex0 import read_planes
from projection import project_triangle, project_trapezoid
from scripts.generate_datasets import generate_datasets
from scripts.download_mri import download_mri


class DatasetTests(unittest.TestCase):
    def test_generate_and_reload_unsigned_nrrds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = generate_datasets(root)
            self.assertEqual(manifest, json.loads((root / "manifest.json").read_text()))
            planes = read_planes(root / "planes.csv")
            self.assertEqual(len(planes), 3)
            for item in manifest["datasets"]:
                volume, _ = nrrd.read(str(root / item["file"]), index_order="F")
                self.assertEqual(volume.shape, (16, 16, 16))
                self.assertEqual(str(volume.dtype), item["dtype"])
                self.assertEqual(int(volume.min()), 0)
                self.assertEqual(int(volume.max()), np.iinfo(volume.dtype).max)
                self.assertEqual(hashlib.sha256(volume.tobytes(order="C")).hexdigest(),
                                 item["voxel_sha256_c_order"])
                self.assertEqual(int(volume[1, 2, 3]),
                                 (1+16*2+256*3) * np.iinfo(volume.dtype).max // 4095)
                for kind, points in planes:
                    function = project_triangle if kind == "triangle" else project_trapezoid
                    self.assertTrue(function(volume, *points).size)

    def test_mri_downloader_verifies_hash_and_preserves_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "MRI.nrrd"
            with patch("scripts.download_mri.urllib.request.urlopen", return_value=io.BytesIO(b"invalid")):
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    download_mri(target)
            self.assertFalse(target.exists())
            target.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                download_mri(target)
            self.assertEqual(target.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
