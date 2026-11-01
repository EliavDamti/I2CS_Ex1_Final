import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import nrrd

from Ex0 import read_planes
from projection import project_triangle, project_trapezoid
from scripts.create_demo import demo_planes, write_planes, build_demo, verify_demo


class DemonstrationTests(unittest.TestCase):
    def test_all_sixty_serialized_mri_planes_are_valid_and_ordered(self):
        records = demo_planes((256, 256, 130))
        self.assertEqual(len(records), 60)
        self.assertEqual([record["section"] for record in records], [1]*20+[2]*20+[3]*20)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "planes.csv"
            write_planes(records, path)
            planes = read_planes(path)
            volume = np.ones((1, 1, 1), dtype=np.uint8)
            for index, (kind, points) in enumerate(planes):
                self.assertEqual(kind, records[index]["kind"])
                function = project_triangle if kind == "triangle" else project_trapezoid
                self.assertTrue(function(volume, *points).size)
        self.assertNotEqual(records[0]["points"], records[19]["points"])
        self.assertNotEqual(records[40]["points"], records[59]["points"])

    def test_full_demo_generation_and_decoding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            x, y, z = np.indices((16, 16, 16))
            source = root / "source.nrrd"
            nrrd.write(str(source), (x+16*y+256*z).astype(np.uint16), index_order="F")
            output = root / "demo"
            manifest = build_demo(source, output, per_section=1, fps=2, title_seconds=.5)
            self.assertEqual(manifest["raw"]["frames"], 3)
            self.assertEqual(manifest["showcase"]["frames"], 5)
            self.assertEqual(manifest["showcase"]["duration_seconds"], 2.5)
            self.assertTrue((output / "demo-poster.png").exists())
            report = json.loads((output / "demo-validation.json").read_text())
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["raw"]["ordered_planes_compared"], 3)
            self.assertEqual(report["showcase"]["decoded_frames"], 5)
            # A manifest mismatch must be reported, never presented as success.
            manifest["raw"]["frames"] = 4
            (output / "demo-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "counts disagree"):
                verify_demo(source, output)

    def test_demo_rejects_empty_or_degenerate_sweeps(self):
        for shape, count in (((1, 10, 10), 20), ((10, 10, 10), 0)):
            with self.assertRaises(ValueError):
                demo_planes(shape, count)


if __name__ == "__main__":
    unittest.main()
