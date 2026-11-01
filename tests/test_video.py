import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import imageio.v2 as imageio
import numpy as np
import nrrd

from Ex0 import create_video, normalize_image, center_frame
from tests.test_csv import NAMED, NUMBERED


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def inputs(self, dtype=np.uint8, numbered=False):
        volume = np.zeros((12, 12, 12), dtype=dtype)
        maximum = np.iinfo(dtype).max
        volume[:, :, 3] = maximum
        volume[:, :, 5] = maximum // 2
        nrrd_path = self.root / "volume.nrrd"
        nrrd.write(str(nrrd_path), volume, index_order="F")
        records = []
        for index, (z, size) in enumerate(((3, 8), (4, 6), (5, 4))):
            coordinates = f"1,1,{z},{size},1,{z},1,{size},{z},{size},{size},{z}"
            records.append((f"{index},4," if numbered else "trapezoid,") + coordinates)
        csv_path = self.root / "planes.csv"
        csv_path.write_text((NUMBERED if numbered else NAMED) + "\n" + "\n".join(records), encoding="utf-8")
        return nrrd_path, csv_path

    def check_video(self, path):
        with imageio.get_reader(str(path), format="FFMPEG") as reader:
            metadata = reader.get_meta_data()
            frames = list(reader.iter_data())
        self.assertEqual(len(frames), 3)
        self.assertEqual(metadata["fps"], 2)
        self.assertEqual({frame.shape for frame in frames}, {(8, 8, 3)})
        # Independently known planes: white at z=3, black z=4, half-scale z=5.
        for frame, expected in zip(frames, (255, 0, 127)):
            center = frame[3:5, 3:5]
            self.assertLessEqual(abs(float(center.mean()) - expected), 8)

    def test_real_nrrd_csv_mp4_for_all_unsigned_types(self):
        for dtype in (np.uint8, np.uint16, np.uint32):
            with self.subTest(dtype=dtype):
                nrrd_path, csv_path = self.inputs(dtype, numbered=dtype == np.uint16)
                output = self.root / f"{np.dtype(dtype).name}.mp4"
                count, size = create_video(nrrd_path, csv_path, output)
                self.assertEqual((count, size), (3, (8, 8)))
                self.check_video(output)

    def test_cli_success_and_invalid_record_exit(self):
        nrrd_path, csv_path = self.inputs(numbered=True)
        output = self.root / "cli.mp4"
        command = [sys.executable, str(Path(__file__).parents[1] / "Ex0.py"),
                   str(nrrd_path), str(csv_path), str(output)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.check_video(output)
        original = output.read_bytes()
        csv_path.write_text(NAMED + "\n,1,1,3,8,1,3,1,8,3,8,8,3\n", encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertIn("CSV row 2", result.stderr)
        self.assertEqual(output.read_bytes(), original)

    def test_encoder_failure_preserves_output_and_removes_temporary(self):
        nrrd_path, csv_path = self.inputs()
        output = self.root / "existing.mp4"
        output.write_bytes(b"existing output")
        with patch("Ex0.imageio.get_writer") as factory:
            factory.return_value.__enter__.return_value.append_data.side_effect = RuntimeError("encoder failed")
            with self.assertRaisesRegex(RuntimeError, "encoder failed"):
                create_video(nrrd_path, csv_path, output)
        self.assertEqual(output.read_bytes(), b"existing output")
        self.assertEqual(list(self.root.glob(".existing-*.mp4")), [])

    def test_missing_and_invalid_input_files(self):
        nrrd_path, csv_path = self.inputs()
        with self.assertRaises(OSError):
            create_video(self.root / "missing.nrrd", csv_path, self.root / "out.mp4")
        for volume in (np.zeros((2, 2), dtype=np.uint8), np.zeros((2, 2, 2), dtype=np.float32)):
            nrrd.write(str(nrrd_path), volume)
            with self.assertRaises(ValueError):
                create_video(nrrd_path, csv_path, self.root / "out.mp4")
        self.assertFalse((self.root / "out.mp4").exists())

    def test_normalization_and_centering(self):
        image = np.array([[0, 2**32-2, 2**32-1]], dtype=np.uint32)
        np.testing.assert_array_equal(normalize_image(image, 0, 2**32-1), [[0, 254, 255]])
        np.testing.assert_array_equal(normalize_image(np.zeros((2, 2)), 0, 0), np.zeros((2, 2)))
        np.testing.assert_array_equal(normalize_image(np.array([[-100, 0, 100]], dtype=np.int16), -100, 100), [[0, 127, 255]])
        frame = center_frame(np.array([[50]], dtype=np.uint8), 2, 2)
        self.assertEqual(frame.shape, (2, 2, 3))
        np.testing.assert_array_equal(frame[0, 0], [50, 50, 50])
        with self.assertRaises(ValueError):
            center_frame(np.ones((3, 3), dtype=np.uint8), 2, 2)


if __name__ == "__main__":
    unittest.main()
