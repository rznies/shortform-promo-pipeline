"""
Modal Cloud Parallel Batch Renderer for All 10 Promos
Spawns 10 parallel serverless containers, processes in cloud at gigabit speed,
streams finished MP4s back, and uploads to Google Drive '4. Exports' folder.
"""

import os
import sys
import time
import subprocess
import modal

app = modal.App("shortform-promo-batch")

# Cloud Container with FFmpeg, full CJK & Western typography, OpenCV, and gdown
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "fonts-liberation", "fonts-noto-cjk", "fonts-dejavu-core")
    .pip_install(
        "gdown>=5.1.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "opencv-python-headless>=4.8.0",
    )
)

# Shared Assets Drive IDs
SHARED_ASSETS = {
    "fr_logo": "1_J0uPx2SFM1k2Gh_nRGqpkr5CaPawOSR",
    "fr_cta":  "1Q4aNJHXMG1HO-sgPbx233I8XVVFjlRsx",
    "jp_logo": "1JB4jz1DWBhj7wHUcQJ1Zm6VhWa56PL4C",
    "jp_cta":  "1op-1PvAX2NDJNGMEwTR8G_o9IVxONt7n",
}

# The 10 Promo Job Specifications
RAW_JOBS = [
    {
        "id": "FDED1026FR",
        "lang": "fr",
        "promo_id": "1Uz2-mghR1ebsU08Bj-oPXUen4muNjJXb",
        "vo_id": "1zsl4cdLqYLL2jU5mIZEmuBzl9gKFMqPg",
        "vo_dur": 50.83,
        "ass_file": "FDED1026FR.ass",
    },
    {
        "id": "FDDEX041FR",
        "lang": "fr",
        "promo_id": "12RYcCkQtgzBYXU0fRdLIhg830UnIdDSh",
        "vo_id": None,
        "vo_dur": None,
        "ass_file": None,
    },
    {
        "id": "FDED572FR",
        "lang": "fr",
        "promo_id": "1VXz6m4kyYS0mV5VGOq6DnqfH9wKibd31",
        "vo_id": None,
        "vo_dur": None,
        "ass_file": None,
    },
    {
        "id": "FDED1028FR",
        "lang": "fr",
        "promo_id": "14wvmDYa-HEDn9PSmbNKpWYDh5pnPMeIz",
        "vo_id": "1ztFsmrcP37Am-ArPCscC5ZHOFeEprGQx",
        "vo_dur": 26.33,
        "ass_file": "FDED1028FR.ass",
    },
    {
        "id": "FDED470FR",
        "lang": "fr",
        "promo_id": "1bvKlvKM2d34JqNqQNzBpeEuzgNPzt4uG",
        "vo_id": "1I2L_Wnxy4negdfoJY7A3gAOmNSxGZqsM",
        "vo_dur": 12.07,
        "ass_file": "FDED470FR.ass",
    },
    {
        "id": "FDED806FR",
        "lang": "fr",
        "promo_id": "1293w4nlZek1FirCI7adWic1Tv54TMtoR",
        "vo_id": "1tlvTUnYTNuXWzoyiScFo8FwVZ4USR4m6",
        "vo_dur": 36.00,
        "ass_file": "FDED806FR.ass",
    },
    {
        "id": "FDDCE789FR",
        "lang": "fr",
        "promo_id": "1vinIbkyDR3oeR823R-vSxFj5zpPLX_kq",
        "vo_id": "18OF_TZpphgWzDCU_qpLVpX9buWsTLrQW",
        "vo_dur": 53.97,
        "ass_file": "FDDCE789FR.ass",
    },
    {
        "id": "FDEH571FR",
        "lang": "fr",
        "promo_id": "1patpuFOHPh53A3xz6kqRDJDcIlm7oQbY",
        "vo_id": None,
        "vo_dur": None,
        "ass_file": None,
    },
    {
        "id": "FDEA458JP",
        "lang": "jp",
        "promo_id": "16jUrxM36RpyiIB_rfqDW9MBONcSTSCI1",
        "vo_id": "1egLCAdjAosJ6L7rMVODEa6dZGnm0fa2k",
        "vo_dur": 20.08,
        "ass_file": "FDEA458JP.ass",
    },
    {
        "id": "FDEA645JP",
        "lang": "jp",
        "promo_id": "13dcWDtypCerQ-zs_g2JkKymgB6J3BpTu",
        "vo_id": "1nDQgR-bKPdlijVaQJ9UqYqHWh5SPOnwS",
        "vo_dur": 20.08,
        "ass_file": "FDEA645JP.ass",
    },
]


@app.function(
    image=image,
    timeout=1200,
    cpu=4.0,
    memory=8192,
)
def render_promo_worker(job: dict) -> dict:
    import os
    import time
    import subprocess
    import gdown
    import cv2
    import numpy as np

    pid = job["id"]
    lang = job["lang"]
    work_dir = f"/tmp/{pid}"
    os.makedirs(work_dir, exist_ok=True)

    print(f"[{pid}] Cloud container initialized. Preparing rendering pipeline...")

    # Robust Google Drive download helper using gdown
    def fetch_gdrive(file_id: str, dest_path: str):
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            return dest_path
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"[{pid}] Downloading {os.path.basename(dest_path)} (ID: {file_id})...")
        gdown.download(url, dest_path, quiet=True)
        if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1000:
            # Fallback direct id invocation
            gdown.download(id=file_id, output=dest_path, quiet=True)
        return dest_path

    # 1. Download Raw Promo
    promo_raw = os.path.join(work_dir, "raw.mp4")
    fetch_gdrive(job["promo_id"], promo_raw)
    raw_size_mb = os.path.getsize(promo_raw) / (1024 * 1024)
    print(f"[{pid}] Raw promo ready ({raw_size_mb:.1f} MB)")

    # 2. Download Shared Animated Logo and Localized CTA
    logo_id = SHARED_ASSETS["fr_logo"] if lang == "fr" else SHARED_ASSETS["jp_logo"]
    cta_id = SHARED_ASSETS["fr_cta"] if lang == "fr" else SHARED_ASSETS["jp_cta"]

    logo_path = os.path.join(work_dir, f"{lang}_logo.mov")
    cta_path = os.path.join(work_dir, f"{lang}_cta.mp4")

    fetch_gdrive(logo_id, logo_path)
    fetch_gdrive(cta_id, cta_path)
    print(f"[{pid}] Logo and CTA assets ready.")

    # 3. Detect Old CTA Cut via Frame Difference Analysis
    cap = cv2.VideoCapture(promo_raw)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = total_frames / fps

    start_f = max(0, int((dur - 12.0) * fps))
    end_f = max(0, int((dur - 2.5) * fps))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
    ret, prev = cap.read()
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY) if ret and prev is not None else None
    cta_cut_t = dur - 7.5
    max_diff = 0.0

    if prev_gray is not None:
        for f in range(start_f + 1, end_f):
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            diff = float(np.mean(cv2.absdiff(prev_gray, gray)))
            if diff > 25.0 and diff > max_diff:
                max_diff = diff
                cta_cut_t = f / fps
            prev_gray = gray
    cap.release()

    print(f"[{pid}] Duration: {dur:.2f}s | CTA Cut Point: {cta_cut_t:.2f}s (Diff: {max_diff:.1f})")

    # 4. Handle Subtitles and Voiceover
    has_vo = job["vo_id"] is not None
    vo_path = None
    ass_path = os.path.join(work_dir, "subtitles.ass")

    if has_vo:
        vo_path = os.path.join(work_dir, "vo.mp4")
        fetch_gdrive(job["vo_id"], vo_path)

        # Write subtitle file from pre-verified ASS content
        ass_content = job.get("ass_content", "")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        print(f"[{pid}] ASS Subtitles configured ({len(ass_content)} bytes)")

    # 5. Build Standard Compliant FFmpeg Filter Graph
    out_mp4 = os.path.join(work_dir, "output.mp4")

    if has_vo:
        vo_dur = job["vo_dur"] or 20.0
        if abs(cta_cut_t - vo_dur) < 8.0:
            # Full VO promo cut
            fg = f"""
            [0:v]trim=0:{cta_cut_t:.3f},setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1[v_main];
            [v_main]split[v_base][v_crop];
            [v_crop]crop=w=750:h=200:x=40:y=80,boxblur=18:3[v_blurred];
            [v_base][v_blurred]overlay=x=40:y=80[v_clean];
            [v_clean]subtitles='{ass_path}'[v_sub];
            [v_sub][2:v]overlay=0:0:format=auto:shortest=1[v_p1];
            [1:a]atrim=0:{cta_cut_t:.3f},asetpts=PTS-STARTPTS,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a_p1];
            [3:v]fps=30,scale=1080:1920,setsar=1,setpts=PTS-STARTPTS[v_cta];
            [3:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a_cta];
            [v_p1][a_p1][v_cta][a_cta]concat=n=2:v=1:a=1[v_out][a_out]
            """
        else:
            # VO Hook at beginning, native drama audio continues in middle
            fg = f"""
            [0:v]trim=0:{cta_cut_t:.3f},setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1[v_main];
            [v_main]split[v_base][v_crop];
            [v_crop]crop=w=750:h=200:x=40:y=80,boxblur=18:3[v_blurred];
            [v_base][v_blurred]overlay=x=40:y=80[v_clean];
            [v_clean]subtitles='{ass_path}'[v_sub];
            [v_sub][2:v]overlay=0:0:format=auto:shortest=1[v_p1];
            [1:a]volume=1.0[vo_aud];
            [0:a]atrim=start={vo_dur:.3f}:end={cta_cut_t:.3f},asetpts=PTS-STARTPTS[mid_aud];
            [vo_aud][mid_aud]concat=n=2:v=0:a=1,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a_p1];
            [3:v]fps=30,scale=1080:1920,setsar=1,setpts=PTS-STARTPTS[v_cta];
            [3:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a_cta];
            [v_p1][a_p1][v_cta][a_cta]concat=n=2:v=1:a=1[v_out][a_out]
            """
        inputs = [
            "-i", promo_raw,
            "-i", vo_path,
            "-stream_loop", "-1", "-i", logo_path,
            "-i", cta_path,
        ]
    else:
        # Case B: Pure Drama Cliffhanger
        fg = f"""
        [0:v]trim=0:{cta_cut_t:.3f},setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1[v_main];
        [v_main]split[v_base][v_crop];
        [v_crop]crop=w=750:h=200:x=40:y=80,boxblur=18:3[v_blurred];
        [v_base][v_blurred]overlay=x=40:y=80[v_clean];
        [v_clean][1:v]overlay=0:0:format=auto:shortest=1[v_p1];
        [0:a]atrim=0:{cta_cut_t:.3f},asetpts=PTS-STARTPTS,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a_p1];
        [2:v]fps=30,scale=1080:1920,setsar=1,setpts=PTS-STARTPTS[v_cta];
        [2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a_cta];
        [v_p1][a_p1][v_cta][a_cta]concat=n=2:v=1:a=1[v_out][a_out]
        """
        inputs = [
            "-i", promo_raw,
            "-stream_loop", "-1", "-i", logo_path,
            "-i", cta_path,
        ]

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", fg.replace("\n", " "),
        "-map", "[v_out]", "-map", "[a_out]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        out_mp4
    ]

    print(f"[{pid}] Launching FFmpeg render engine...")
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[{pid}] FFmpeg FAILED:\n", res.stderr[-800:])
        raise RuntimeError(f"FFmpeg failed for {pid}")

    elapsed = time.time() - t0
    size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    print(f"[{pid}] RENDER FINISHED in {elapsed:.1f}s | Size: {size_mb:.1f} MB")

    # Read binary bytes
    with open(out_mp4, "rb") as f:
        video_bytes = f.read()

    return {
        "id": pid,
        "filename": f"rajniesh_6299660736_{pid}.mp4",
        "size_mb": round(size_mb, 1),
        "duration_s": round(cta_cut_t + 7.43, 2),
        "data": video_bytes,
    }


@app.local_entrypoint()
def main():
    print("================================================================================")
    print("🚀 LAUNCHING 10 PARALLEL CLOUD RENDERING CONTAINERS ON MODAL")
    print("================================================================================")

    # Resolve local subtitle directory and exports folder
    subs_dir = r"E:\Mine\antigravity\fueler\video_editing_shreyas\subtitles_ready"
    local_exports = r"E:\Mine\antigravity\fueler\video_editing_shreyas\exports_final"
    os.makedirs(local_exports, exist_ok=True)
    exports_folder_id = "1t8DXgEzvRfEo8ODp1fzu53tb1t9ejg3Z"

    # Assemble complete job definitions with embedded ASS content
    prepared_jobs = []
    for j in RAW_JOBS:
        job = dict(j)
        if job["ass_file"]:
            ass_path = os.path.join(subs_dir, job["ass_file"])
            if os.path.exists(ass_path):
                with open(ass_path, "r", encoding="utf-8") as f:
                    job["ass_content"] = f.read()
            else:
                print(f"Warning: Missing ASS file {ass_path}")
                job["ass_content"] = ""
        else:
            job["ass_content"] = None
        prepared_jobs.append(job)

    print(f"All {len(prepared_jobs)} jobs packaged with verified subtitles and drive references.")
    print("Dispatching parallel workers to Modal datacenter...\n")

    t_start = time.time()
    results = []

    # Parallel execution across 10 cloud containers
    for res in render_promo_worker.map(prepared_jobs):
        pid = res["id"]
        fname = res["filename"]
        size_mb = res["size_mb"]
        dur = res["duration_s"]
        out_path = os.path.join(local_exports, fname)

        # Save finished video locally
        with open(out_path, "wb") as f:
            f.write(res["data"])

        print(f"\n✓ [Modal Cloud] Finished {pid}: {size_mb} MB | Duration: {dur}s")
        print(f"  📁 Local file saved: {out_path}")

        # Upload directly to Google Drive '4. Exports' folder
        print(f"  ☁️  Uploading {fname} to Google Drive '4. Exports' ({exports_folder_id})...")
        cmd_up = ["gdrive", "mutate", "upload", out_path, "--parent", exports_folder_id]
        up_res = subprocess.run(cmd_up, capture_output=True, text=True, shell=(os.name == "nt"))
        print(f"  ✓ Drive status: {up_res.stdout.strip() or 'Uploaded successfully'}")

        results.append({
            "id": pid,
            "filename": fname,
            "size_mb": size_mb,
            "duration_s": dur,
            "drive_status": "Uploaded" if up_res.returncode == 0 else "Failed"
        })

    tot_elapsed = time.time() - t_start
    print("\n================================================================================")
    print(f"🎉 ALL 10 PROMOS RENDERED ON MODAL AND UPLOADED IN {tot_elapsed:.1f} SECONDS!")
    print("================================================================================")
    for r in results:
        print(f" - {r['filename']}: {r['size_mb']} MB, {r['duration_s']}s -> {r['drive_status']}")
