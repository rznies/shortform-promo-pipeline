"""
Audio and Voiceover Swapping Block
"""

from typing import Tuple


def build_vo_swap_filter(
    promo_audio_label: str = "0:a",
    vo_audio_label: str = "1:a",
    vo_duration_seconds: float = 24.0,
    vo_volume: float = 1.0,
    output_label: str = "final_audio",
) -> Tuple[str, str]:
    """
    Substitutes the starting hook audio of the promo with the localized voiceover,
    resuming original promo episode audio after vo_duration_seconds.

    Filter chain:
      [vo_audio]volume=1.0[vo_scaled];
      [promo_audio]atrim=start=DURATION,asetpts=PTS-STARTPTS[rest_aud];
      [vo_scaled][rest_aud]concat=n=2:v=0:a=1[final_audio]
    """
    filter_str = (
        f"[{vo_audio_label}]volume={vo_volume:.2f}[vo_scaled];"
        f"[{promo_audio_label}]atrim=start={vo_duration_seconds:.3f},asetpts=PTS-STARTPTS[rest_aud];"
        f"[vo_scaled][rest_aud]concat=n=2:v=0:a=1[{output_label}]"
    )
    return filter_str, output_label
