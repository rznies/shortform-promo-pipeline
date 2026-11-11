"""
Recipe: Voiceover Hook Promo (Archetype A)
Combines: Watermark Mask + Logo Overlay + VO Swap + Subtitles + CTA Stitch
"""

import os
import subprocess
from typing import Dict, Any
from ..blocks.watermark import build_watermark_blur_filter
from ..blocks.logo import build_logo_overlay_filter
from ..blocks.audio import build_vo_swap_filter
from ..blocks.subtitles import extract_text_from_docx, generate_ass_subtitles, build_subtitle_filter
from ..blocks.cta import build_cta_concat_filter
from ..manifest import PromoJob


def render_vo_promo(job: PromoJob, work_dir: str = "./workspace") -> str:
    """
    Renders an Archetype A promo with voiceover hook, styled subtitles, logo, and CTA.
    Returns path to finished output MP4.
    """
    os.makedirs(work_dir, exist_ok=True)
    out_path = os.path.join(work_dir, job.output_filename)

    # 1. Prepare Subtitles
    script_text = ""
    if job.subtitles and job.subtitles.script_path and os.path.exists(job.subtitles.script_path):
        script_text = extract_text_from_docx(job.subtitles.script_path)

    vo_duration = (job.audio_vo.duration_seconds if job.audio_vo and job.audio_vo.duration_seconds else 24.0)

    ass_path = os.path.join(work_dir, f"{job.promo_id}_subtitles.ass")
    if script_text:
        generate_ass_subtitles(
            text=script_text,
            total_duration_seconds=vo_duration,
            output_path=ass_path,
            font_size=job.subtitles.font_size if job.subtitles else 64,
            margin_v=job.subtitles.margin_v if job.subtitles else 420,
        )

    # 2. Build FFmpeg command
    inputs = ["-i", job.input_promo_path]
    current_idx = 1

    vo_idx = None
    if job.audio_vo and job.audio_vo.file_path:
        inputs.extend(["-i", job.audio_vo.file_path])
        vo_idx = current_idx
        current_idx += 1

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

    # Filter graph construction
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

    # Subtitles burn
    if script_text and os.path.exists(ass_path):
        sub_filter, cur_v = build_subtitle_filter(ass_path, input_label=cur_v, output_label="v_sub")
        filters.append(sub_filter)

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

    # Audio swap
    if vo_idx is not None:
        audio_filter, cur_a = build_vo_swap_filter(
            promo_audio_label="0:a",
            vo_audio_label=f"{vo_idx}:a",
            vo_duration_seconds=vo_duration,
            vo_volume=job.audio_vo.volume if job.audio_vo else 1.0,
            output_label="a_main",
        )
        filters.append(audio_filter)
    else:
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

    print(f"[render_vo_promo] Running command for {job.promo_id}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed for {job.promo_id}: {res.stderr}")

    return out_path
