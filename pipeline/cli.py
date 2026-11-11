"""
CLI Entrypoint and Command Handler for Shortform Promo Pipeline
"""

import argparse
import sys
import yaml
from rich.console import Console

from .planner import audit_and_plan
from .manifest import JobManifest, RecipeType
from .recipes.vo_promo import render_vo_promo
from .recipes.cliffhanger import render_cliffhanger
from .utils.qc import inspect_media_properties, generate_qc_contact_sheet

console = Console()


def cmd_plan(args):
    manifest = audit_and_plan(
        drive_url_or_path=args.source,
        output_manifest_path=args.output,
        project_name=args.project_name or "Promo Production Batch",
        user_name=args.name,
        phone_number=args.phone,
    )
    console.print(f"[bold green]Planning complete![/] Ready to execute with: [cyan]python -m pipeline run --jobs {args.output}[/]")


def cmd_run(args):
    with open(args.jobs, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = JobManifest.model_validate(data)

    console.print(f"[bold cyan]🚀 Launching batch execution for:[/] {manifest.project_name} ({len(manifest.jobs)} jobs)")
    console.print(f"Backend selected: [bold]{args.backend}[/]")

    if args.backend == "modal":
        try:
            from .modal_backend.app import batch_render_cloud
            job_dicts = [j.model_dump() for j in manifest.jobs]
            console.print("[yellow]Spawning Modal serverless containers...[/]")
            results = batch_render_cloud.remote(job_dicts)
            console.print("[bold green]✓ Cloud batch execution finished![/]")
            for r in results:
                console.print(f"  • {r['promo_id']}: {r['status']} ({r.get('size_mb')} MB)")
        except Exception as e:
            console.print(f"[bold red]Modal cloud execution failed:[/] {e}")
            console.print("[yellow]Falling back to local FFmpeg execution...[/]")
            _run_local(manifest)
    else:
        _run_local(manifest)


def _run_local(manifest: JobManifest):
    for i, job in enumerate(manifest.jobs, 1):
        console.print(f"\n[bold][{i}/{len(manifest.jobs)}] Processing {job.promo_id} ({job.recipe})...[/]")
        try:
            if job.recipe == RecipeType.VO_PROMO:
                out = render_vo_promo(job, work_dir=manifest.output_directory)
            else:
                out = render_cliffhanger(job, work_dir=manifest.output_directory)
            console.print(f"  [green]✓ Finished:[/] {out}")
        except Exception as e:
            console.print(f"  [red]✗ Failed:[/] {e}")


def cmd_verify(args):
    with open(args.jobs, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    manifest = JobManifest.model_validate(data)

    console.print(f"[bold cyan]🔍 Verifying {len(manifest.jobs)} outputs in {manifest.output_directory}...[/]")
    for job in manifest.jobs:
        import os
        out_path = os.path.join(manifest.output_directory, job.output_filename)
        if not os.path.exists(out_path):
            console.print(f"  [red]✗ Missing output file:[/] {out_path}")
            continue

        props = inspect_media_properties(out_path)
        console.print(f"  [green]✓ {job.promo_id}:[/] File verified ({props.get('format', {}).get('duration', 'N/A')}s)")


def main():
    parser = argparse.ArgumentParser(description="Short-Form Promo Localization & Video Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan
    p_plan = subparsers.add_parser("plan", help="Audit project folder and generate jobs.yaml")
    p_plan.add_argument("source", help="Google Drive URL, folder ID, or local directory path")
    p_plan.add_argument("--output", "-o", default="jobs.yaml", help="Output path for manifest file")
    p_plan.add_argument("--project-name", default="Promo Localization Batch", help="Name of project batch")
    p_plan.add_argument("--name", default="editor", help="Editor name for export filename")
    p_plan.add_argument("--phone", default="0000000000", help="Phone number for export filename")
    p_plan.set_defaults(func=cmd_plan)

    # run
    p_run = subparsers.add_parser("run", help="Execute promo rendering")
    p_run.add_argument("--jobs", "-j", default="jobs.yaml", help="Path to jobs.yaml manifest")
    p_run.add_argument("--backend", choices=["modal", "local"], default="modal", help="Compute backend")
    p_run.set_defaults(func=cmd_run)

    # verify
    p_verify = subparsers.add_parser("verify", help="Run automated QC and contact sheet generation")
    p_verify.add_argument("--jobs", "-j", default="jobs.yaml", help="Path to jobs.yaml manifest")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
