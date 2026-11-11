# Short-Form Vertical Promo Localization Pipeline 🎬

An automated, cloud-accelerated production pipeline for vertical (9:16) video drama promo localization and editing. Designed for autonomous AI coding agents and human video engineers.

---

## ⚡ Quickstart for Coding Agents

If you are an AI coding agent assigned a new video batch, see **[AGENTS.md](AGENTS.md)** for your step-by-step operating playbook.

### 1. Plan & Audit an Assignment
Pass the Google Drive folder link (or local input directory) to the automated planner:
```bash
python -m pipeline plan "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
```
The planner audits the assets, detects promo archetypes, matches VOs/logos/CTAs, flags anomalies, and creates `jobs.yaml`.

### 2. Execute Batch Render
Launch parallel cloud rendering via Modal (or local FFmpeg fallback):
```bash
# Cloud-first (Recommended: parallel serverless rendering)
python -m pipeline run --jobs jobs.yaml --backend modal

# Local rendering
python -m pipeline run --jobs jobs.yaml --backend local
```

### 3. Verify Quality (QC)
Generate contact sheet previews and verify mobile safe-zones:
```bash
python -m pipeline verify --jobs jobs.yaml
```

---

## 🏗️ Architecture

```
shortform-promo-pipeline/
├── AGENTS.md                  # Complete playbook for autonomous coding agents
├── WORKFLOW.md                # Video geometry, safe zones & FFmpeg filter graphs
├── pipeline/
│   ├── __main__.py            # CLI entrypoint
│   ├── cli.py                 # Commands: plan, run, verify, sync
│   ├── planner.py             # Automated folder auditor & manifest generator
│   ├── manifest.py            # Pydantic schema & validation for jobs.yaml
│   ├── recipes/               # Pre-assembled promo recipes
│   │   ├── vo_promo.py        # VO Hook + Subtitles + Logo + Blur + CTA
│   │   ├── cliffhanger.py     # Continuous Drama + Logo + Blur + CTA
│   │   └── clean_sync.py      # Waveform cross-correlation master re-cut
│   ├── blocks/                # Modular video processing building blocks
│   │   ├── watermark.py       # Soft-feathered watermark masking
│   │   ├── logo.py            # Transparent MOV/PNG positioning
│   │   ├── audio.py           # Dubbed VO swapping & normalization
│   │   ├── subtitles.py       # DOCX parsing & styled ASS/SRT burning
│   │   ├── sync.py            # Scipy audio cross-correlation sync
│   │   └── cta.py             # Outro stitching with audio crossfades
│   ├── modal_backend/         # Serverless cloud rendering on Modal
│   │   └── app.py
│   └── utils/
│       ├── gdrive.py          # Google Drive scraper & uploader
│       └── qc.py              # Frame extraction & verification
└── examples/
    └── job_sample.yaml        # Reference manifest
```

---

## 📦 Setup & Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# (Optional) Authenticate Modal for cloud acceleration
modal setup
```

---

## 🔒 License & Ownership
Private repository for video localization and automation pipelines.
