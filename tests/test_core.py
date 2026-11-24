import itertools

import pytest

from tokenreel.safe_ffmpeg import UnsafePath, build_cmd, confine
from tokenreel.segment import plan


def test_plan_detects_code_and_math():
    text = "Intro sentence here. Then we compute x = y^2 today.\n```python\nprint(1)\n```\n"
    kinds = [s.kind for s in plan(text)]
    assert "code" in kinds and ("math" in kinds or "flow" in kinds)


def test_confine_blocks_traversal(tmp_path):
    with pytest.raises(UnsafePath):
        confine("../../etc/passwd.png", tmp_path)


def test_confine_blocks_bad_suffix(tmp_path):
    with pytest.raises(UnsafePath):
        confine("a.sh", tmp_path)


def test_cmd_whitelists_file_protocol(tmp_path):
    (tmp_path / "a.png").write_bytes(b"x")
    cmd = build_cmd(["a.png"], "o.mp4", tmp_path)
    i = cmd.index("-protocol_whitelist")
    assert cmd[i + 1] == "file"


def test_per_sentence_kinds():
    kinds = [s.kind for s in plan("A hash map stores keys. Lookup is O(1) where load = n / m.")]
    assert kinds == ["text", "math"]


def test_timing_and_srt():
    from tokenreel.timing import estimate_timings, spoken_form, to_srt

    assert "equals" in spoken_form("x = 2")
    w = estimate_timings("one two three four five")
    assert all(a.end <= b.start + 1e-6 for a, b in itertools.pairwise(w))
    assert "-->" in to_srt(w)


def test_draw_scene(tmp_path):
    pytest.importorskip("PIL")
    from tokenreel.render import draw_scene
    from tokenreel.segment import Scene

    draw_scene(Scene("code", "print(1)", ["print"]), tmp_path / "a.png")
    assert (tmp_path / "a.png").stat().st_size > 0


def test_flow_steps_drop_connectors():
    from tokenreel.segment import steps

    assert steps("First hash the key. Then jump to the bucket.") == ["Hash the key", "Jump to the bucket"]


def test_flow_scene_has_steps_and_draws(tmp_path):
    pytest.importorskip("PIL")
    from tokenreel.render import draw_scene

    flow = [s for s in plan("First hash the key. Then jump to the bucket. Finally compare the key.") if s.kind == "flow"]
    assert flow and len(flow[0].steps) == 3
    draw_scene(flow[0], tmp_path / "f.png", 0, 1)
    assert (tmp_path / "f.png").stat().st_size > 0


def test_mcp_tools_and_limits(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    import asyncio

    from tokenreel import mcp_server as m

    monkeypatch.setenv("TOKENREEL_OUT", str(tmp_path))
    names = {t.name for t in asyncio.run(m.mcp.list_tools())}
    assert {"plan_scenes", "make_captions", "render_video"} <= names
    assert m.plan_scenes("First hash the key. Then jump to the bucket.")[0]["kind"] == "flow"
    with pytest.raises(ValueError):
        m.plan_scenes("x" * (m.MAX_CHARS + 1))
    with pytest.raises(ValueError):
        m.render_video("hello world", name="../evil")
    with pytest.raises(ValueError):
        m.render_video("hello world", exact_timings=True)
