"""
Watermark Masking and Blurring Block
"""

from typing import Tuple


def build_watermark_blur_filter(
    input_label: str = "0:v",
    output_label: str = "clean_base",
    x: int = 40,
    y: int = 90,
    width: int = 640,
    height: int = 180,
    blur_radius: int = 18,
    blur_power: int = 3,
) -> Tuple[str, str]:
    """
    Generates an FFmpeg filtergraph segment to softly blur out an on-screen title or logo watermark.

    Filter chain:
      [in]split[base][mask];
      [mask]crop=w=640:h=180:x=40:y=90,boxblur=luma_radius=18:luma_power=3[blurred];
      [base][blurred]overlay=x=40:y=90[out]
    """
    filter_str = (
        f"[{input_label}]split[wm_base][wm_crop];"
        f"[wm_crop]crop=w={width}:h={height}:x={x}:y={y},"
        f"boxblur=luma_radius={blur_radius}:luma_power={blur_power}[wm_blurred];"
        f"[wm_base][wm_blurred]overlay=x={x}:y={y}[{output_label}]"
    )
    return filter_str, output_label
