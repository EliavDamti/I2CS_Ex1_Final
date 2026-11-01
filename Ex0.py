"""Read ordered CSV planes and encode their NRRD projections as an MP4."""

import argparse
import csv
import os
from pathlib import Path
import tempfile

import imageio.v2 as imageio
import numpy as np
import nrrd

from projection import project_triangle, project_trapezoid, validate_volume


def read_planes(csv_path):
    """Read the assignment's point-count CSV or the original named-point CSV."""
    planes = []
    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        headers = [(name or "").strip().lstrip("\ufeff") for name in (reader.fieldnames or [])]
        if not headers:
            raise ValueError("CSV has no header")
        if len(set(headers)) != len(headers):
            raise ValueError("CSV contains duplicate column names")
        reader.fieldnames = headers
        if "type" in headers and "Number of Points (3 or 4)" in headers:
            raise ValueError("CSV must use one shape schema, not both")
        if "type" in headers:
            kind_column = "type"
            coordinate_columns = [[f"{letter}{axis}" for axis in "xyz"] for letter in "abcd"]
        elif "Number of Points (3 or 4)" in headers:
            kind_column = "Number of Points (3 or 4)"
            coordinate_columns = [[f"{axis}{number}" for axis in "xyz"] for number in range(1, 5)]
        else:
            raise ValueError("CSV needs 'type' or 'Number of Points (3 or 4)'")
        required = [name for point in coordinate_columns[:3] for name in point]
        missing = [name for name in required if name not in headers]
        if missing:
            raise ValueError(f"Missing CSV columns: {missing}")

        for row in reader:
            line_number = reader.line_num
            if all(value is None or not str(value).strip() for key, value in row.items() if key is not None) and None not in row:
                continue
            try:
                if None in row:
                    raise ValueError("too many fields")
                kind = (row[kind_column] or "").strip().lower()
                if kind_column == "Number of Points (3 or 4)":
                    kind = {"3": "triangle", "4": "trapezoid"}.get(kind)
                if kind not in ("triangle", "trapezoid"):
                    raise ValueError("shape must be triangle/3 or trapezoid/4; blank shape is invalid")
                count = 3 if kind == "triangle" else 4
                points = []
                for names in coordinate_columns[:count]:
                    point = tuple(float(row[name]) for name in names)
                    if not all(np.isfinite(point)):
                        raise ValueError("coordinates must be finite")
                    points.append(point)
                planes.append((kind, tuple(points)))
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f"Invalid CSV row {line_number}: {error}") from error
    if not planes:
        raise ValueError("CSV does not contain any planes")
    return planes


def normalize_image(image, volume_min, volume_max):
    """Global display normalization, with float64 preserving uint32 precision."""
    image = image.astype(np.float64)
    if volume_max > volume_min:
        image = (image - volume_min) / (volume_max - volume_min) * 255.0
    else:
        image.fill(0)
    return np.clip(image, 0, 255).astype(np.uint8)


def center_frame(image, height, width):
    """Center a 2D uint8 image in a fixed-size RGB canvas."""
    h, w = image.shape
    if height < h or width < w:
        raise ValueError("Frame must be at least as large as the projection")
    frame = np.zeros((height, width), dtype=np.uint8)
    top, left = (height - h) // 2, (width - w) // 2
    frame[top:top+h, left:left+w] = image
    return np.repeat(frame[:, :, None], 3, axis=2)


def create_video(nrrd_path, csv_path, mp4_path):
    """Compute all planes before atomically replacing the completed output."""
    output_path = Path(mp4_path)
    if output_path.suffix.lower() != ".mp4":
        raise ValueError("Output filename must end in .mp4")
    if output_path.resolve() in (Path(nrrd_path).resolve(), Path(csv_path).resolve()):
        raise ValueError("Output must not overwrite an input file")
    volume, _ = nrrd.read(str(nrrd_path), index_order="F")
    validate_volume(volume)
    planes = read_planes(csv_path)
    projections = []
    for index, (kind, points) in enumerate(planes, start=1):
        function = project_triangle if kind == "triangle" else project_trapezoid
        try:
            projections.append(function(volume, *points))
        except ValueError as error:
            raise ValueError(f"Plane {index} ({kind}): {error}") from error
    height = max(2, max(p.shape[0] for p in projections))
    width = max(2, max(p.shape[1] for p in projections))
    height += height % 2
    width += width % 2
    display_min = min(float(volume.min()), 0.0)
    display_max = max(float(volume.max()), 0.0)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output_path.stem}-",
                                            suffix=".mp4", dir=output_path.parent)
    os.close(descriptor)
    try:
        with imageio.get_writer(temporary, format="FFMPEG", fps=2,
                                codec="libx264", pixelformat="yuv420p",
                                macro_block_size=1) as writer:
            for projection in projections:
                image = normalize_image(projection, display_min, display_max)
                writer.append_data(center_frame(image, height, width))
        os.replace(temporary, output_path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return len(projections), (height, width)


def main():
    parser = argparse.ArgumentParser(description="Convert 3D NRRD plane projections to MP4")
    parser.add_argument("nrrd_file", help="Input NRRD volume")
    parser.add_argument("csv_file", help="Ordered CSV plane definitions")
    parser.add_argument("mp4_file", help="Output MP4 video")
    args = parser.parse_args()
    try:
        count, size = create_video(args.nrrd_file, args.csv_file, args.mp4_file)
    except (ValueError, OSError, RuntimeError, nrrd.NRRDError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(f"Video saved: {Path(args.mp4_file).resolve()}")
    print(f"Total frames: {count}; frame size: {size[1]}x{size[0]}; playback: 2 FPS")


if __name__ == "__main__":
    main()
