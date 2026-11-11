"""
Job Manifest Schema and Validation Models
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RecipeType(str, Enum):
    VO_PROMO = "vo_promo"          # Hook VO + Subtitles + Logo + Blur + CTA
    CLIFFHANGER = "cliffhanger"    # Continuous Drama + Logo + Blur + CTA
    CLEAN_SYNC = "clean_sync"      # Waveform Cross-Correlation Master Recut


class WatermarkConfig(BaseModel):
    enabled: bool = True
    x: int = 40
    y: int = 90
    width: int = 640
    height: int = 180
    blur_radius: int = 18


class LogoConfig(BaseModel):
    file_path: Optional[str] = None
    drive_id: Optional[str] = None
    x: int = 40
    y: int = 100
    scale: float = 1.0
    opacity: float = 1.0


class AudioVOConfig(BaseModel):
    file_path: Optional[str] = None
    drive_id: Optional[str] = None
    duration_seconds: Optional[float] = None
    volume: float = 1.0


class SubtitleConfig(BaseModel):
    enabled: bool = True
    script_path: Optional[str] = None
    drive_id: Optional[str] = None
    font_name: str = "Arial"
    font_size: int = 64
    primary_color: str = "&H00FFFFFF"     # White
    outline_color: str = "&H00000000"     # Black
    outline_width: int = 3
    margin_v: int = 420                  # Distance from bottom (safe zone)
    max_lines: int = 2
    max_chars_per_line: int = 36


class CTAConfig(BaseModel):
    file_path: Optional[str] = None
    drive_id: Optional[str] = None
    transition_duration: float = 0.5


class PromoJob(BaseModel):
    promo_id: str
    show_name: str
    language: str                        # fr, jp, de, es, en
    recipe: RecipeType
    input_promo_path: Optional[str] = None
    input_promo_drive_id: Optional[str] = None
    output_filename: str
    watermark: WatermarkConfig = Field(default_factory=WatermarkConfig)
    logo: LogoConfig = Field(default_factory=LogoConfig)
    audio_vo: Optional[AudioVOConfig] = None
    subtitles: Optional[SubtitleConfig] = None
    cta: Optional[CTAConfig] = None
    status: str = "pending"               # pending, rendering, completed, failed


class JobManifest(BaseModel):
    project_name: str
    drive_folder_id: Optional[str] = None
    export_folder_id: Optional[str] = None
    output_directory: str = "./exports"
    jobs: List[PromoJob] = Field(default_factory=list)
