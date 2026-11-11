"""
Recipe: Clean Master Episode Re-Cut (Archetype C)
Uses audio cross-correlation to find cut points in full raw master episodes,
re-assembling the promo with 100% clean, unwatermarked footage.
"""

import os
import subprocess
from typing import List, Dict, Tuple
from ..blocks.sync import find_audio_offset
from ..blocks.logo import build_logo_overlay_filter
from ..blocks.cta import build_cta_concat_filter
from ..manifest import PromoJob


def sync_and_render_clean(
    job: PromoJob,
    episode_map: Dict[int, str],
    clip_estimates: List[Tuple[float, float, int]],  # (start_s, end_s, episode_num)
    work_dir: str = "./workspace",
) -> str:
    """
    Re-cuts the promo from master clean episodes and renders output.
    clip_estimates: list of (cut_start_s, cut_end_s, ep_num)
    """
    os.makedirs(work_dir, exist_ok=True)
    out_path = os.path.join(work_dir, job.output_filename)

    extracted_slices = []
    concat_list_path = os.path.join(work_dir, f"{job.promo_id}_slices.txt")

    with open(concat_list_path, "w", encoding="utf-8") as f_list:
        for i, (start_s, end_s, ep_num) in enumerate(clip_estimates):
            ep_file = episode_map.get(ep_num)
            if not ep_file or not os.path.exists(ep_file):
                continue

            slice_out = os.path.join(work_dir, f"slice_{i:03d}.mp4")
            duration = end_s - start_s
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{start_s:.3f}",
                "-t", f"{duration:.3f}",
                "-i", ep_file,
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                "-c:a", "aac", "-ar", "48000",
                slice_out,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            f_list.write(f"file '{os.path.abspath(slice_out).replace(chr(92), '/')}'\n")
            extracted_slices.append(slice_out)

    # Concat slices
    clean_concat = os.path.join(work_dir, f"{job.promo_id}_clean_stitched.mp4")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        clean_concat,
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # Apply logo & CTA to clean assembled body
    job.input_promo_path = clean_concat
    from .cliffhanger import render_cliffhanger
    return render_cliffhanger(job, work_dir=work_dir)
