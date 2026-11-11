import pytest
from pipeline.manifest import JobManifest, PromoJob, RecipeType, WatermarkConfig, LogoConfig


def test_manifest_validation():
    job = PromoJob(
        promo_id="FDED1026FR",
        show_name="Rent A Boyfriend",
        language="fr",
        recipe=RecipeType.VO_PROMO,
        output_filename="test_FDED1026FR.mp4",
        watermark=WatermarkConfig(x=40, y=90, width=640, height=180),
        logo=LogoConfig(x=40, y=100),
    )
    manifest = JobManifest(project_name="Test Project", jobs=[job])

    assert len(manifest.jobs) == 1
    assert manifest.jobs[0].recipe == RecipeType.VO_PROMO
    assert manifest.jobs[0].watermark.width == 640


def test_manifest_yaml_roundtrip(tmp_path):
    import yaml
    job = PromoJob(
        promo_id="FDED572FR",
        show_name="Rent A Boyfriend",
        language="fr",
        recipe=RecipeType.CLIFFHANGER,
        output_filename="test_FDED572FR.mp4",
    )
    manifest = JobManifest(project_name="Roundtrip Test", jobs=[job])
    yaml_file = tmp_path / "test_jobs.yaml"

    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(manifest.model_dump(mode="json"), f)

    with open(yaml_file, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    loaded_manifest = JobManifest.model_validate(loaded)
    assert loaded_manifest.jobs[0].promo_id == "FDED572FR"
