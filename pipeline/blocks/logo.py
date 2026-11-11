"""
Logo Overlay and Alpha Blending Block
"""

from typing import Tuple


def build_logo_overlay_filter(
    video_label: str = "clean_base",
    logo_label: str = "1:v",
    output_label: str = "logo_applied",
    x: int = 40,
    y: int = 100,
    scale: float = 1.0,
    shortest: int = 0,
) -> Tuple[str, str]:
    """
    Overlays an animated or static transparent logo (MOV/PNG) onto the video stream.

    If scale != 1.0, scale the logo stream first before overlaying.
    """
    if abs(scale - 1.0) > 0.01:
        scale_label = f"{logo_label}_scaled"
        scale_segment = f"[{logo_label}]scale=iw*{scale}:ih*{scale}[{scale_label}];"
        current_logo = scale_label
    else:
        scale_segment = ""
        current_logo = logo_label

    filter_str = (
        f"{scale_segment}"
        f"[{video_label}][{current_logo}]overlay=x={x}:y={y}:format=auto:shortest={shortest}[{output_label}]"
    )
    return filter_str, output_label
