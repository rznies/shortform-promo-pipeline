import os
from pipeline.blocks.subtitles import split_text_into_chunks, generate_ass_subtitles


def test_split_text_into_chunks():
    sample_text = (
        "Le Black Friday des petits amis. Les plus beaux mecs sont partis en quelques secondes "
        "et Nathalie n'est meme pas sur liste d'attente. Sa propre soeur lui a carrement ri au nez."
    )
    chunks = split_text_into_chunks(sample_text, max_chars_per_line=36, max_lines=2)

    assert len(chunks) > 0
    for chunk in chunks:
        lines = chunk.split("\\N")
        assert len(lines) <= 2
        for line in lines:
            assert len(line) <= 45  # allow slight slack for long individual words


def test_generate_ass_subtitles(tmp_path):
    sample_text = "Attendez, mais l'accord ne tenait que pour une nuit."
    out_file = str(tmp_path / "test.ass")

    res = generate_ass_subtitles(sample_text, total_duration_seconds=10.0, output_path=out_file)
    assert os.path.exists(res)

    with open(res, "r", encoding="utf-8") as f:
        content = f.read()

    assert "[Script Info]" in content
    assert "PlayResY: 1920" in content
    assert "Dialogue:" in content
