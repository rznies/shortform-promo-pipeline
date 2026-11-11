"""
Recipe: Cliffhanger / Continuous Drama Promo (Archetype B)
Combines: Watermark Mask + Logo Overlay + Native Audio + CTA Stitch
"""

import os
import subprocess
from ..blocks.watermark import build_watermark_blur_filter
from ..blocks.logo import build_logo_overlay_filter
from ..blocks.cta import build_cta_concat_filter
from ..manifest import PromoJob


def render_cliffhanger(job: PromoJob, work_dir: str = "./workspace") -> str:
    """
    Renders an Archetype B promo (pure dramatic dialogue, logo replacement, watermark blur, and CTA).
    Returns path to finished output MP4.
    """
    os.makedirs(work_dir, exist_ok=True)
    out_path = os.path.join(work_dir, job.output_filename)

    inputs = ["-i", job.input_promo_path]
    current_idx = 1

    logo_idx = None
    if job.logo and job.logo.file_path:
        inputs.extend(["-i", job.logo.file_path])
        logo_idx = current_idx
        current_idx += 1

    cta_idx = None
    if job.cta and job.cta.file_path:
        inputs.extend(["-i", job.cta.file_path])
        cta_idx = current_idx
        current_idx += 1

    filters = []

    # Watermark blur
    wm = job.watermark
    wm_filter, cur_v = build_watermark_blur_filter(
        input_label="0:v",
        output_label="v_clean",
        x=wm.x,
        y=wm.y,
        width=wm.width,
        height=wm.height,
        blur_radius=wm.blur_radius,
    )
    filters.append(wm_filter)

    # Logo overlay
    if logo_idx is not None:
        logo = job.logo
        logo_filter, cur_v = build_logo_overlay_filter(
            video_label=cur_v,
            logo_label=f"{logo_idx}:v",
            output_label="v_logo",
            x=logo.x,
            y=logo.y,
            scale=logo.scale,
        )
        filters.append(logo_filter)

    cur_a = "0:a"

    # CTA concat
    if cta_idx is not None:
        cta_filter, final_v, final_a = build_cta_concat_filter(
            main_v_label=cur_v,
            main_a_label=cur_a,
            cta_v_label=f"{cta_idx}:v",
            cta_a_label=f"{cta_idx}:a",
            out_v_label="out_v",
            out_a_label="out_a",
        )
        filters.append(cta_filter)
    else:
        final_v, final_a = cur_v, cur_a

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{final_v}]",
        "-map", f"[{final_a}]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        out_path,
    ]

    print(f"[render_cliffhanger] Running command for {job.promo_id}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed for {job.promo_id}: {res.stderr}")

    return out_path
