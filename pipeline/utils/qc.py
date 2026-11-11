"""
Quality Control (QC) and Verification Utilities
"""

import os
import subprocess
from typing import Dict, Any, List


def inspect_media_properties(video_path: str) -> Dict[str, Any]:
    """Inspects video resolution, duration, and audio stream using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=width,height,r_frame_rate,codec_name,sample_rate,channels",
        "-of", "json",
        video_path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        return json.loads(res.stdout)
    except Exception as e:
        return {"error": str(e)}


def generate_qc_contact_sheet(
    video_path: str,
    output_png: str,
    timestamps_seconds: List[float] = [2.0, 10.0, 25.0, 45.0],
) -> str:
    """
    Extracts verification frames across timestamps and tiles them into a single contact strip.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
    temp_frames = []
    base_dir = os.path.dirname(output_png)

    for i, t in enumerate(timestamps_seconds):
        frame_path = os.path.join(base_dir, f"qc_frame_{i:02d}.png")
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(t),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            frame_path,
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(frame_path):
            temp_frames.append(frame_path)

    if not temp_frames:
        return ""

    # Tile horizontally or vertically
    inputs = []
    for f in temp_frames:
        inputs.extend(["-i", f])

    filter_str = f"hstack=inputs={len(temp_frames)}"
    cmd_tile = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        output_png,
    ]
    subprocess.run(cmd_tile, capture_output=True)

    # Clean up temp frames
    for f in temp_frames:
        try:
            os.remove(f)
        except OSError:
            pass

    return output_png
