"""
Audio Waveform Cross-Correlation Synchronization Block (scipy.signal)
"""

import numpy as np
from scipy import signal
from scipy.io import wavfile
from typing import Tuple, Optional


def find_audio_offset(
    promo_wav_path: str,
    episode_wav_path: str,
    search_window_seconds: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Finds the exact temporal offset (in seconds) of a promo audio slice within a full episode track
    using normalized cross-correlation.

    Returns:
      (offset_seconds, correlation_score)
    """
    sr_p, y_p = wavfile.read(promo_wav_path)
    sr_e, y_e = wavfile.read(episode_wav_path)

    # Convert to mono if stereo
    if len(y_p.shape) > 1:
        y_p = y_p.mean(axis=1)
    if len(y_e.shape) > 1:
        y_e = y_e.mean(axis=1)

    # Normalize waveforms
    y_p = (y_p - np.mean(y_p)) / (np.std(y_p) + 1e-8)
    y_e = (y_e - np.mean(y_e)) / (np.std(y_e) + 1e-8)

    if search_window_seconds:
        max_samples = int(search_window_seconds * sr_e)
        y_e = y_e[:max_samples]

    # Fast Fourier Transform cross-correlation
    correlation = signal.correlate(y_e, y_p, mode="valid", method="fft")
    peak_idx = np.argmax(correlation)
    peak_score = float(correlation[peak_idx]) / len(y_p)

    offset_sec = float(peak_idx) / sr_e
    return offset_sec, peak_score
