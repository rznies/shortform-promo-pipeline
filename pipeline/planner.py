"""
Automated Assignment Auditor and Planner
Inspects Drive folders or local inputs, pairs assets, categorizes promo archetypes, and emits jobs.yaml.
"""

import os
import re
import yaml
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table

from .manifest import (
    JobManifest,
    PromoJob,
    RecipeType,
    WatermarkConfig,
    LogoConfig,
    AudioVOConfig,
    SubtitleConfig,
    CTAConfig,
)
from .utils.gdrive import extract_id_from_url, list_folder_contents

console = Console()


def audit_and_plan(
    drive_url_or_path: str,
    output_manifest_path: str = "jobs.yaml",
    project_name: str = "Promo Batch",
    user_name: str = "editor",
    phone_number: str = "0000000000",
) -> JobManifest:
    """
    Audits a project folder structure and generates a complete JobManifest.
    """
    console.print(f"[bold cyan]🔍 Auditing project source:[/] {drive_url_or_path}")

    is_drive = "drive.google.com" in drive_url_or_path or len(drive_url_or_path) in [28, 33, 44]
    folder_id = extract_id_from_url(drive_url_or_path) if is_drive else None

    promos: List[Dict[str, str]] = []
    vo_assets: List[Dict[str, str]] = []
    export_folder_id = None

    if is_drive:
        root_items = list_folder_contents(folder_id)
        subfolders = {item["name"]: item["id"] for item in root_items if item.get("mimeType") == "application/vnd.google-apps.folder"}

        # Check for 1. Promo
        promo_folder_id = subfolders.get("1. Promo") or subfolders.get("1.Promo")
        if promo_folder_id:
            promos = list_folder_contents(promo_folder_id)

        # Check for 2. VO logo cta
        vo_folder_id = subfolders.get("2. VO logo cta") or subfolders.get("2. VO CTA LOGO and Subtitles")
        if vo_folder_id:
            vo_assets = list_folder_contents(vo_folder_id)

        export_folder_id = subfolders.get("4. Exports") or subfolders.get("4.Exports")
    else:
        # Local filesystem directory audit
        promo_dir = os.path.join(drive_url_or_path, "1. Promo")
        if os.path.exists(promo_dir):
            for f in os.listdir(promo_dir):
                promos.append({"name": f, "path": os.path.join(promo_dir, f)})

        vo_dir = os.path.join(drive_url_or_path, "2. VO logo cta")
        if os.path.exists(vo_dir):
            for f in os.listdir(vo_dir):
                vo_assets.append({"name": f, "path": os.path.join(vo_dir, f)})

    # Match assets
    jobs: List[PromoJob] = []
    anomalies: List[str] = []

    # Map logos and CTAs by language or show
    logos = [f for f in vo_assets if "logo" in f["name"].lower() and f["name"].endswith((".mov", ".png"))]
    ctas = [f for f in vo_assets if "cta" in f["name"].lower() and f["name"].endswith((".mp4", ".mov"))]
    dubs = [f for f in vo_assets if any(k in f["name"].lower() for k in ["dubbed", "vo"]) and f["name"].endswith((".mp4", ".wav", ".m4a"))]
    scripts = [f for f in vo_assets if f["name"].endswith((".docx", ".txt"))]

    # Flag junk files
    for item in vo_assets:
        if "_de_" in item["name"].lower() or "german" in item["name"].lower():
            anomalies.append(f"Ignored foreign/stray asset: [yellow]{item['name']}[/]")

    for p in promos:
        p_name = p["name"]
        if not p_name.lower().endswith((".mp4", ".mov")):
            continue

        promo_code = os.path.splitext(p_name)[0].strip()

        # Detect language suffix
        lang = "en"
        if promo_code.upper().endswith("FR"):
            lang = "fr"
        elif promo_code.upper().endswith("JP"):
            lang = "jp"
        elif promo_code.upper().endswith("GR") or promo_code.upper().endswith("DE"):
            lang = "de"
        elif promo_code.upper().endswith("ES"):
            lang = "es"

        # Find matching VO and Script
        matching_vo = next((v for v in dubs if promo_code[:7].lower() in v["name"].lower()), None)
        matching_script = next((s for s in scripts if promo_code[:7].lower() in s["name"].lower()), None)

        # Find matching logo & CTA by language
        matching_logo = next((l for l in logos if (lang == "fr" and any(k in l["name"].lower() for k in ["french", "loue", "ami"])) or (lang == "jp" and any(k in l["name"] for k in ["傷ついた", "兵士"]))), logos[0] if logos else None)
        matching_cta = next((c for c in ctas if (lang == "fr" and any(k in c["name"].lower() for k in ["french", "loue", "ami"])) or (lang == "jp" and any(k in c["name"] for k in ["傷ついた", "兵士"]))), ctas[0] if ctas else None)

        recipe = RecipeType.VO_PROMO if matching_vo else RecipeType.CLIFFHANGER

        # Build output filename following assignment convention: <Name>_<Phone>_<Code>.mp4
        output_filename = f"{user_name}_{phone_number}_{promo_code}.mp4"

        job = PromoJob(
            promo_id=promo_code,
            show_name="Rent A Boyfriend" if lang == "fr" else "I Married a Broken Soldier",
            language=lang,
            recipe=recipe,
            input_promo_path=p.get("path"),
            input_promo_drive_id=p.get("id"),
            output_filename=output_filename,
            watermark=WatermarkConfig(enabled=True, x=40, y=90, width=640, height=180),
            logo=LogoConfig(
                file_path=matching_logo.get("path") if matching_logo else None,
                drive_id=matching_logo.get("id") if matching_logo else None,
                x=40,
                y=100,
            ),
            audio_vo=AudioVOConfig(
                file_path=matching_vo.get("path") if matching_vo else None,
                drive_id=matching_vo.get("id") if matching_vo else None,
            ) if matching_vo else None,
            subtitles=SubtitleConfig(
                script_path=matching_script.get("path") if matching_script else None,
                drive_id=matching_script.get("id") if matching_script else None,
            ) if matching_script else None,
            cta=CTAConfig(
                file_path=matching_cta.get("path") if matching_cta else None,
                drive_id=matching_cta.get("id") if matching_cta else None,
            ) if matching_cta else None,
        )
        jobs.append(job)

    manifest = JobManifest(
        project_name=project_name,
        drive_folder_id=folder_id,
        export_folder_id=export_folder_id,
        jobs=jobs,
    )

    # Save to yaml
    with open(output_manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest.model_dump(mode="json"), f, sort_keys=False, allow_unicode=True)

    console.print(f"[bold green]✓ Generated manifest saved to:[/] {output_manifest_path}")

    # Display Rich Audit Table
    table = Table(title=f"Batch Audit: {len(jobs)} Promos Detected", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Promo ID", style="bold")
    table.add_column("Lang", justify="center")
    table.add_column("Archetype", style="cyan")
    table.add_column("VO File", style="green")
    table.add_column("Script", style="blue")
    table.add_column("Logo")
    table.add_column("CTA")

    for i, j in enumerate(jobs, 1):
        table.add_row(
            str(i),
            j.promo_id,
            j.language.upper(),
            "VO Hook (A)" if j.recipe == RecipeType.VO_PROMO else "Cliffhanger (B)",
            "✓ Attached" if j.audio_vo else "— Native Audio",
            "✓ Found" if j.subtitles and j.subtitles.script_path else ("(Drive ID)" if j.subtitles and j.subtitles.drive_id else "—"),
            "✓ Assigned" if j.logo and (j.logo.file_path or j.logo.drive_id) else "Missing",
            "✓ Assigned" if j.cta and (j.cta.file_path or j.cta.drive_id) else "Missing",
        )

    console.print(table)

    if anomalies:
        console.print("\n[bold yellow]⚠️  Anomalies Flagged:[/]")
        for a in anomalies:
            console.print(f"  • {a}")

    return manifest
