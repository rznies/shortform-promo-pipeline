"""
Serverless Modal Cloud Backend for Parallel Video Rendering
"""

import os
import modal

app = modal.App("shortform-promo-pipeline")
vol = modal.Volume.from_name("promo-cache-vol", create_if_missing=True)

# Container image with FFmpeg, core fonts, and python dependencies
container_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "fonts-liberation", "fonts-dejavu-core")
    .pip_install(
        "pydantic>=2.5.0",
        "pyyaml>=6.0.1",
        "python-docx>=1.1.0",
        "scipy>=1.11.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
    )
)


@app.function(
    image=container_image,
    volumes={"/cache": vol},
    timeout=900,
    cpu=4.0,
    memory=8192,
)
def render_single_job_cloud(job_dict: dict) -> dict:
    """
    Renders a single promo job in a serverless Modal container.
    """
    from pipeline.manifest import PromoJob, RecipeType
    from pipeline.recipes.vo_promo import render_vo_promo
    from pipeline.recipes.cliffhanger import render_cliffhanger

    job = PromoJob.model_validate(job_dict)
    work_dir = f"/tmp/{job.promo_id}"
    os.makedirs(work_dir, exist_ok=True)

    print(f"[Modal Cloud] Starting render for {job.promo_id} ({job.recipe})...")

    if job.recipe == RecipeType.VO_PROMO:
        out_file = render_vo_promo(job, work_dir=work_dir)
    else:
        out_file = render_cliffhanger(job, work_dir=work_dir)

    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"[Modal Cloud] Completed {job.promo_id}: {file_size_mb:.2f} MB")

    return {
        "promo_id": job.promo_id,
        "output_filename": job.output_filename,
        "status": "success",
        "size_mb": round(file_size_mb, 2),
        "local_path": out_file,
    }


@app.function(image=container_image, timeout=1200)
def batch_render_cloud(jobs: list[dict]) -> list[dict]:
    """
    Executes all jobs in parallel across multiple serverless containers.
    """
    print(f"[Modal Cloud] Spawning parallel batch for {len(jobs)} promo jobs...")
    results = list(render_single_job_cloud.map(jobs))
    return results
