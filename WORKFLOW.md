# WORKFLOW.md — Video Processing Architecture & FFmpeg Filter-Graphs

This document specifies the technical design, mathematical formulas, and FFmpeg filter chains executed by the modular building blocks in `pipeline/blocks/`.

---

## 1. Coordinate & Canvas Specifications

All shortform drama promos target vertical social feeds:
* **Canvas Resolution:** $1080 \times 1920$ (9:16 vertical) or $720 \times 1280$
* **Frame Rate:** 30.0 fps progressive
* **Color Space:** Rec.709, YUV420p
* **Audio:** AAC-LC 48000 Hz, 192 kbps, Stereo

### Vertical Screen Regions:
```
Y = 0      ┌────────────────────────────────────────────────────────┐
           │ Top Safe Zone (System status bar / platform UI)        │
Y = 110    ├────────────────────────────────────────────────────────┤
           │ Show Title & Watermark Area (Height ~180px)           │
           │ [Left: Show Logo .mov]       [Right: Channel Badge]    │
Y = 290    ├────────────────────────────────────────────────────────┤
           │                                                        │
           │ Main Drama Visual Action (Actors' faces & action)      │
           │                                                        │
Y = 1350   ├────────────────────────────────────────────────────────┤
           │ Subtitle Safe Zone (Max 2 lines, bold, 3px outline)   │
Y = 1620   ├────────────────────────────────────────────────────────┤
           │ Bottom Overlay Safe Zone (TikTok / Reels sound, title) │
Y = 1920   └────────────────────────────────────────────────────────┘
```

---

## 2. Block Specifications & FFmpeg Filter Chains

### Block 1: Watermark Masker (`pipeline.blocks.watermark`)
* **Objective:** Remove the original English title watermark stamped at the top left without leaving harsh box edges.
* **Technique:** Soft-feathered Gaussian Blur or Delogo patch.
* **Filter Chain:**
  ```text
  [0:v]split[base][mask];
  [mask]crop=w=640:h=180:x=40:y=90,boxblur=luma_radius=18:luma_power=3[blurred];
  [base][blurred]overlay=x=40:y=90[clean_base]
  ```

### Block 2: Logo Overlay (`pipeline.blocks.logo`)
* **Objective:** Overlay the localized animated show logo (`.mov` ProRes/QuickTime with alpha channel).
* **Target Coordinates:** Typically positioned at $X \approx 40\text{px}$, $Y \approx 100\text{px}$ (in 1080x1920) or centered at the top.
* **Filter Chain:**
  ```text
  [clean_base][1:v]overlay=x=40:y=100:format=auto:shortest=0[logo_applied]
  ```

### Block 3: Audio & VO Swapper (`pipeline.blocks.audio`)
* **Objective:** Replace the original English speech hook with the new French or Japanese dubbed VO (`.mp4`/`.wav`), while preserving the remainder of the video's dramatic episode dialogue.
* **Filter Chain:**
  ```text
  [1:a]volume=1.0[vo_aud];
  [0:a]atrim=start=DURATION_VO,asetpts=PTS-STARTPTS[rest_aud];
  [vo_aud][rest_aud]concat=n=2:v=0:a=1[final_a]
  ```

### Block 4: Auto-Subtitler (`pipeline.blocks.subtitles`)
* **Objective:** Generate legible, mobile-optimized subtitles from `.docx` or raw text aligned to the voiceover.
* **Styling Rules:**
  - Font: Bold Condensed Grotesque (Arial Bold, Helvetica Bold, or Trebuchet MS)
  - Size: 64–72px (1080x1920)
  - Color: Stark White (`&H00FFFFFF`)
  - Outline: 3px Black border (`&H00000000`)
  - Alignment: Bottom Center (Alignment 2 in ASS), positioned at $Y \approx 1450\text{px}$
  - Constraints: Max 2 lines per screen, max 36 characters per line.
* **FFmpeg Filter:**
  ```text
  subtitles=subtitles.ass:fontsdir=/usr/share/fonts
  ```

### Block 5: Outro CTA Stitcher (`pipeline.blocks.cta`)
* **Objective:** Append the translated CTA outro card (`.mp4`) cleanly to the end of the video with seamless audio transition.
* **Filter Chain:**
  ```text
  [main_v][main_a][cta_v][cta_a]concat=n=2:v=1:a=1[v_out][a_out]
  ```

---

## 3. Advanced Block: Waveform Cross-Correlation (`pipeline.blocks.sync`)

For Archetype C (re-syncing raw full episodes):
1. **Audio Fingerprinting:** Downsample promo audio and episode audio tracks to 16 kHz mono.
2. **Normalized Cross-Correlation:**
   $$\rho(\tau) = \frac{\sum (x[t] - \bar{x})(y[t+\tau] - \bar{y})}{\sqrt{\sum (x[t]-\bar{x})^2 \sum (y[t+\tau]-\bar{y})^2}}$$
3. Using `scipy.signal.correlate`, find peak correlation index $\tau_{\max}$ within $< 5$ seconds of compute time.
4. Extract the exact frame slice from the high-resolution clean episode and substitute it into the timeline.
