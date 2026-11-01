"""Reproducible MRI sweeps and a narrated-by-labels presentation video."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import nrrd
from PIL import Image, ImageDraw, ImageFont

from Ex0 import create_video, normalize_image, read_planes, center_frame
from projection import project_triangle, project_trapezoid, validate_volume

WIDTH, HEIGHT = 1280, 720
BACKGROUND = "#0b1420"
PANEL = "#111f2e"
WHITE = "#f1f5f9"
MUTED = "#a4b3c4"
ACCENT = "#69e5be"


def demo_planes(shape, per_section=20):
    """Three deterministic sequences; all coordinates are in voxel space."""
    if per_section < 1 or len(shape) != 3 or min(shape) < 8:
        raise ValueError("Demo requires three dimensions >= 8 and at least one plane per section")
    mx, my, mz = np.asarray(shape, dtype=float) - 1
    records = []
    for x in np.linspace(.22*mx, .78*mx, per_section):
        points = ((x, .08*my, .06*mz), (x, .92*my, .06*mz),
                  (x, .08*my, .94*mz), (x, .92*my, .94*mz))
        records.append(dict(section=1, title="Orthogonal sweep", kind="trapezoid",
                            detail=f"Voxel X = {x:.1f}", points=points))
    for y in np.linspace(.28*my, .72*my, per_section):
        points = ((.5*mx, y, .08*mz), (.1*mx, y, .92*mz), (.9*mx, y, .92*mz))
        records.append(dict(section=2, title="Triangle sweep", kind="triangle",
                            detail=f"Voxel Y = {y:.1f}", points=points))
    center = np.asarray([mx/2, my/2, mz/2])
    # Scale the lower half-width to keep the tilted plane within the volume.
    half_width = min(.36*mx, .80*(mz/2)/math.sin(math.radians(28)))
    v = np.asarray([0., 1., 0.])
    for angle in np.linspace(-28, 28, per_section):
        theta = math.radians(angle)
        u = np.asarray([math.cos(theta), 0., math.sin(theta)])
        points = (center-.44*half_width*u-.34*my*v,
                  center+.44*half_width*u-.34*my*v,
                  center-half_width*u+.34*my*v,
                  center+half_width*u+.34*my*v)
        records.append(dict(section=3, title="Oblique trapezoids", kind="trapezoid",
                            detail=f"Plane tilt = {angle:+.1f} deg", points=points))
    for index, record in enumerate(records, start=1):
        record["index"] = index
        record["points"] = [list(map(float, point)) for point in record["points"]]
    return records


def write_planes(records, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Number of Points (3 or 4)"] +
                        [f"{axis}{number}" for number in range(1, 5) for axis in "xyz"])
        for record in records:
            points = record["points"]
            coordinates = [format(coordinate, ".17g") for point in points for coordinate in point]
            writer.writerow([len(points)] + coordinates + [""]*(3*(4-len(points))))


def font(size, bold=False):
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def label(draw, position, text, size=18, color=MUTED, bold=False):
    draw.text(position, text, fill=color, font=font(size, bold))


def wireframe(canvas, shape, record):
    """Show the current polygon in a normalized isometric volume outline."""
    draw = ImageDraw.Draw(canvas)
    center = np.asarray([1028., 330.])
    def screen(point):
        x, y, z = 2*np.asarray(point)/(np.asarray(shape)-1)-1
        return tuple(center + [92*(x-.7*y), 72*(.4*x+.4*y-.9*z)])
    corners = [np.asarray([x, y, z])*(np.asarray(shape)-1)
               for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    for i, first in enumerate(corners):
        for second in corners[i+1:]:
            if np.count_nonzero(first != second) == 1:
                draw.line([screen(first), screen(second)], fill="#395068", width=2)
    points = record["points"]
    order = (0, 1, 2) if len(points) == 3 else (0, 1, 3, 2)
    polygon = [screen(points[index]) for index in order]
    overlay = Image.new("RGBA", canvas.size)
    painter = ImageDraw.Draw(overlay)
    painter.polygon(polygon, fill=(105, 229, 190, 60))
    painter.line(polygon+[polygon[0]], fill=ACCENT, width=3)
    canvas.paste(overlay, (0, 0), overlay)
    draw = ImageDraw.Draw(canvas)
    for name, point in zip(("X", "Y", "Z"), ((shape[0]-1, 0, 0), (0, shape[1]-1, 0), (0, 0, shape[2]-1))):
        px, py = screen(point)
        label(draw, (px+4, py-8), name, 14, WHITE, True)


def render_plane(image, record, shape, total):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    label(draw, (40, 23), "I2SE  /  EXERCISE 01", 15, ACCENT, True)
    label(draw, (40, 51), "From volume to plane", 40, WHITE, True)
    label(draw, (40, 108), "Real MRI  /  normalized unit steps  /  CSV list order", 18)
    draw.rounded_rectangle((40, 150, 790, 624), 16, fill=PANEL)
    draw.rounded_rectangle((814, 150, 1240, 624), 16, fill=PANEL)
    label(draw, (62, 166), record["title"].upper(), 17, WHITE, True)
    label(draw, (638, 166), f"{record['index']:02d} / {total:02d}", 17, ACCENT, True)
    source = Image.fromarray(image)
    scale = min(700/source.width, 390/source.height)
    source = source.resize((max(1, round(source.width*scale)), max(1, round(source.height*scale))),
                           Image.Resampling.NEAREST).convert("RGB")
    canvas.paste(source, (415-source.width//2, 410-source.height//2))
    wireframe(canvas, shape, record)
    draw = ImageDraw.Draw(canvas)
    label(draw, (838, 168), "PLANE IN THE VOLUME", 16, WHITE, True)
    label(draw, (838, 463), record["detail"], 25, ACCENT, True)
    label(draw, (838, 505), f"Shape: {record['kind']}", 19, WHITE)
    label(draw, (838, 537), f"Projection: {image.shape[0]} x {image.shape[1]} pixels", 17)
    label(draw, (838, 570), "Voxel indices / nearest neighbor", 16)
    for index, text in enumerate(("01  ORTHOGONAL", "02  TRIANGLES", "03  OBLIQUE")):
        label(draw, (40+index*407, 647), text, 15,
              ACCENT if record["section"] == index+1 else MUTED, True)
    draw.rounded_rectangle((40, 685, 1240, 690), 2, fill="#283a4e")
    draw.rounded_rectangle((40, 685, 40+round(1200*record["index"]/total), 690), 2, fill=ACCENT)
    return np.asarray(canvas)


def render_card(total, shape, closing=False):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    label(draw, (64, 54), "I2SE  /  EXERCISE 01", 18, ACCENT, True)
    label(draw, (64, 137), "Every plane has a place." if closing else "A volume. A plane. An image.",
          48, WHITE, True)
    label(draw, (64, 225), "Real MRHead MRI  |  triangles & trapezoids  |  Python", 23)
    if closing:
        items = [
            (f"{total} CSV records", f"{total} ordered projection frames"),
            ("Unit-distance sampling", "Source integer intensities preserved"),
            ("Repeat the experiment", "Inputs, tests and measured timings included"),
        ]
    else:
        items = [
            ("01  Orthogonal sweep", "Move a rectangular plane through the MRI"),
            ("02  Triangle sweep", "Extract isosceles triangular regions"),
            ("03  Oblique trapezoids", "Rotate a plane across the voxel axes"),
        ]
    for index, (title, subtitle) in enumerate(items):
        y = 316+index*88
        draw.rounded_rectangle((64, y, 1216, y+70), 12, fill=PANEL)
        label(draw, (87, y+9), title, 24, ACCENT, True)
        label(draw, (87, y+41), subtitle, 17)
    label(draw, (64, 636), f"NRRD {shape[0]} x {shape[1]} x {shape[2]}  ->  CSV  ->  2D projections  ->  MP4", 20, WHITE)
    return np.asarray(canvas)


def create_showcase(volume, records, output, poster, fps=12, title_seconds=3, hold_seconds=.5):
    """Presentation repeats images for readability; raw demo keeps one per row."""
    if fps < 1 or title_seconds < 0 or hold_seconds <= 0:
        raise ValueError("Showcase timing must be positive")
    repeats = max(1, round(fps*hold_seconds))
    title_frames = round(fps*title_seconds)
    low, high = min(float(volume.min()), 0.), max(float(volume.max()), 0.)
    with imageio.get_writer(str(output), format="FFMPEG", fps=fps, codec="libx264",
                            pixelformat="yuv420p", macro_block_size=1, quality=8) as writer:
        intro = render_card(len(records), volume.shape)
        for _ in range(title_frames):
            writer.append_data(intro)
        for record in records:
            function = project_triangle if record["kind"] == "triangle" else project_trapezoid
            projection = function(volume, *record["points"])
            frame = render_plane(normalize_image(projection, low, high), record, volume.shape, len(records))
            if record["index"] == max(1, len(records)//6):
                Image.fromarray(frame).save(poster)
            for _ in range(repeats):
                writer.append_data(frame)
        ending = render_card(len(records), volume.shape, closing=True)
        for _ in range(title_frames):
            writer.append_data(ending)
    return dict(frames=2*title_frames+len(records)*repeats, fps=fps,
                duration_seconds=(2*title_frames+len(records)*repeats)/fps,
                size=[HEIGHT, WIDTH], repeats_per_plane=repeats)


def build_demo(nrrd_path, output_dir, per_section=20, fps=12, title_seconds=3):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    volume, _ = nrrd.read(str(nrrd_path), index_order="F")
    validate_volume(volume)
    records = demo_planes(volume.shape, per_section)
    csv_path = output_dir / "demo_planes.csv"
    write_planes(records, csv_path)
    # Read back the serialized coordinates: both videos use the exact CSV data.
    parsed = read_planes(csv_path)
    for record, (kind, points) in zip(records, parsed):
        record["points"] = [list(point) for point in points]
    count, size = create_video(nrrd_path, csv_path, output_dir / "demo.mp4")
    showcase = create_showcase(volume, records, output_dir / "showcase.mp4",
                               output_dir / "demo-poster.png", fps, title_seconds)
    manifest = dict(source=Path(nrrd_path).name,
                    source_file_sha256=hashlib.sha256(Path(nrrd_path).read_bytes()).hexdigest(),
                    source_voxel_sha256_c_order=hashlib.sha256(volume.tobytes(order="C")).hexdigest(),
                    projection_sha256=hashlib.sha256(
                        (Path(__file__).parents[1] / "projection.py").read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest(),
                    volume_shape=list(volume.shape),
                    volume_dtype=str(volume.dtype), intensity_range=[int(volume.min()), int(volume.max())],
                    raw=dict(file="demo.mp4", frames=count, fps=2, size=list(size), duration_seconds=count/2),
                    showcase=dict(file="showcase.mp4", **showcase), planes=records)
    (output_dir / "demo-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    verification = verify_demo(nrrd_path, output_dir)
    (output_dir / "demo-validation.json").write_text(json.dumps(verification, indent=2)+"\n", encoding="utf-8")
    return manifest


def verify_demo(nrrd_path, output_dir):
    """Decode every video frame; compare raw frames with their ordered planes."""
    output_dir = Path(output_dir)
    manifest = json.loads((output_dir / "demo-manifest.json").read_text(encoding="utf-8"))
    volume, _ = nrrd.read(str(nrrd_path), index_order="F")
    planes = read_planes(output_dir / "demo_planes.csv")
    if len(planes) != manifest["raw"]["frames"] or len(planes) != len(manifest["planes"]):
        raise ValueError("CSV, manifest and raw video frame counts disagree")
    if hashlib.sha256(Path(nrrd_path).read_bytes()).hexdigest() != manifest["source_file_sha256"]:
        raise ValueError("NRRD source hash differs from the generated demonstration")
    code_hash = hashlib.sha256(
        (Path(__file__).parents[1] / "projection.py").read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
    if code_hash != manifest["projection_sha256"]:
        raise ValueError("Projection source changed; rebuild the demonstration")
    low, high = min(float(volume.min()), 0.), max(float(volume.max()), 0.)
    errors = []
    report = {}
    for key in ("raw", "showcase"):
        definition = manifest[key]
        count = 0
        with imageio.get_reader(str(output_dir / definition["file"]), format="FFMPEG") as reader:
            metadata = reader.get_meta_data()
            if metadata["codec"] != "h264" or abs(metadata["fps"]-definition["fps"]) > 1e-6:
                raise ValueError(f"{key}: unexpected codec or playback rate")
            for count, frame in enumerate(reader.iter_data(), start=1):
                if list(frame.shape[:2]) != definition["size"]:
                    raise ValueError(f"{key}: frame {count} has an unexpected size")
                if key == "raw":
                    if count > len(planes):
                        raise ValueError("Raw video has extra frames")
                    kind, points = planes[count-1]
                    function = project_triangle if kind == "triangle" else project_trapezoid
                    projection = function(volume, *points)
                    expected = center_frame(normalize_image(projection, low, high), *definition["size"])
                    error = float(np.abs(frame.astype(np.float64)-expected).mean())
                    if error > 8:
                        raise ValueError(f"Raw frame {count} does not match its CSV plane")
                    errors.append(error)
        if count != definition["frames"]:
            raise ValueError(f"{key}: decoded {count}, expected {definition['frames']} frames")
        report[key] = dict(decoded_frames=count, codec=metadata["codec"],
                           fps=metadata["fps"], size=definition["size"])
    report["raw"]["largest_mean_absolute_encoding_error"] = max(errors)
    report["raw"]["ordered_planes_compared"] = len(errors)
    report["status"] = "passed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nrrd_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--planes-per-section", type=int, default=20)
    parser.add_argument("--verify-only", action="store_true", help="Decode and verify existing demo outputs")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_demo(args.nrrd_file, args.output_dir), indent=2))
        return
    manifest = build_demo(args.nrrd_file, args.output_dir, args.planes_per_section)
    print(f"Raw demo: {manifest['raw']['frames']} frames, {manifest['raw']['duration_seconds']} seconds")
    print(f"Showcase: {manifest['showcase']['duration_seconds']} seconds at {WIDTH}x{HEIGHT}")
    print(f"Outputs: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
