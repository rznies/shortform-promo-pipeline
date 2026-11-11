"""
Call-To-Action (CTA) Outro Concatenation Block
"""

from typing import Tuple


def build_cta_concat_filter(
    main_v_label: str = "main_v",
    main_a_label: str = "main_a",
    cta_v_label: str = "cta_v",
    cta_a_label: str = "cta_a",
    out_v_label: str = "final_v",
    out_a_label: str = "final_a",
) -> Tuple[str, str, str]:
    """
    Concatenates the main promo video stream and CTA outro stream into final output streams.

    Filter chain:
      [main_v][main_a][cta_v][cta_a]concat=n=2:v=1:a=1[final_v][final_a]
    """
    filter_str = f"[{main_v_label}][{main_a_label}][{cta_v_label}][{cta_a_label}]concat=n=2:v=1:a=1[{out_v_label}][{out_a_label}]"
    return filter_str, out_v_label, out_a_label
