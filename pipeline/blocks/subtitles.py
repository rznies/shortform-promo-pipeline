"""
Subtitle Extraction, Formatting (SRT/ASS), and Burning Block
"""

import os
import re
from typing import List, Tuple
from docx import Document


def extract_text_from_docx(docx_path: str) -> str:
    """Read full text from a Word (.docx) document."""
    if not os.path.exists(docx_path):
        return ""
    doc = Document(docx_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return " ".join(lines)


def split_text_into_chunks(text: str, max_chars_per_line: int = 36, max_lines: int = 2) -> List[str]:
    """Break a long narrative text into rhythmic subtitle blocks (max lines and chars)."""
    words = text.split()
    chunks = []
    current_lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if len(test_line) <= max_chars_per_line:
            current_line.append(word)
        else:
            if current_line:
                current_lines.append(" ".join(current_line))
            current_line = [word]

            if len(current_lines) == max_lines:
                chunks.append("\\N".join(current_lines))
                current_lines = []

    if current_line:
        current_lines.append(" ".join(current_line))
    if current_lines:
        chunks.append("\\N".join(current_lines))

    return chunks


def generate_ass_subtitles(
    text: str,
    total_duration_seconds: float,
    output_path: str,
    font_name: str = "Arial",
    font_size: int = 64,
    margin_v: int = 420,
) -> str:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file styled for 9:16 vertical video.
    """
    chunks = split_text_into_chunks(text)
    if not chunks:
        chunks = [" "]

    # Distribute timing proportionally by character count
    total_chars = sum(len(c.replace("\\N", " ")) for c in chunks) or 1
    start_time = 0.5
    available_duration = max(1.0, total_duration_seconds - 0.8)

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    current_sec = start_time
    for chunk in chunks:
        chunk_len = len(chunk.replace("\\N", " "))
        duration = max(1.2, (chunk_len / total_chars) * available_duration)
        end_sec = min(total_duration_seconds, current_sec + duration)

        start_str = _format_ass_time(current_sec)
        end_str = _format_ass_time(end_sec)
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{chunk}")
        current_sec = end_sec

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events) + "\n")

    return output_path


def _format_ass_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"


def build_subtitle_filter(ass_path: str, input_label: str = "video_in", output_label: str = "video_subbed") -> Tuple[str, str]:
    """Generates FFmpeg filter string to burn in ASS subtitles."""
    # Escape backslashes and colons for FFmpeg filter syntax
    safe_path = ass_path.replace("\\", "/").replace(":", "\\:")
    return f"[{input_label}]subtitles='{safe_path}'[{output_label}]", output_label
