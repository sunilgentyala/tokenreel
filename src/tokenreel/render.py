"""Frame rendering with Pillow (extra: render) and assembly through safe_ffmpeg.

Portrait 1080x1920 for Shorts and Reels. Each scene becomes one PNG; the concat list
and ffmpeg call stay inside a confined working directory.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from .safe_ffmpeg import run
from .segment import Scene
from .timing import estimate_timings

W, H = 1080, 1920
# kind -> (gradient top, gradient bottom, accent, badge label)
THEME = {
    "text": ((16, 18, 40), (44, 28, 84), (167, 139, 250), "EXPLAINER"),
    "code": ((8, 14, 24), (16, 40, 44), (52, 211, 153), "CODE"),
    "math": ((28, 14, 44), (74, 32, 64), (251, 191, 36), "MATH"),
    "flow": ((8, 22, 44), (14, 58, 92), (56, 189, 248), "FLOW"),
}
_SANS = ["segoeuib.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"]
_BODY = ["segoeui.ttf", "DejaVuSans.ttf", "arial.ttf"]
_MONO = ["consola.ttf", "DejaVuSansMono.ttf", "cour.ttf"]
_KW = {"def", "class", "return", "import", "from", "if", "else", "elif", "for", "while", "in",
       "const", "let", "var", "function", "async", "await", "try", "except", "with", "as", "None",
       "True", "False", "print", "self"}


def _font(names, size):
    from PIL import ImageFont

    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _gradient(top, bottom):
    from PIL import Image

    col = Image.linear_gradient("L").resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), bottom), Image.new("RGB", (W, H), top), col)


def _code_line(d, xy, line, font, accent):
    """Tiny highlighter: keywords accent, strings amber, comments grey, rest white."""
    import re

    x, y = xy
    for tok in re.findall(r"#.*|\"[^\"]*\"|'[^']*'|\w+|\W", line):
        if tok.startswith("#"):
            fill = (130, 140, 160)
        elif tok[0] in "\"'":
            fill = (251, 191, 36)
        elif tok in _KW:
            fill = accent
        else:
            fill = (232, 236, 244)
        d.text((x, y), tok, fill=fill, font=font)
        x += d.textlength(tok, font=font)


def draw_scene(scene: Scene, path: Path, index: int = 0, total: int = 1) -> None:
    from PIL import ImageDraw

    top, bottom, accent, label = THEME.get(scene.kind, THEME["text"])
    img = _gradient(top, bottom)
    d = ImageDraw.Draw(img, "RGBA")

    # badge
    f_badge = _font(_SANS, 40)
    bw = int(d.textlength(label, font=f_badge)) + 72
    d.rounded_rectangle((70, 110, 70 + bw, 190), 40, fill=(*accent, 255))
    d.text((106, 124), label, fill=(12, 12, 24), font=f_badge)
    d.text((W - 70, 124), f"{index + 1}/{total}", fill=(255, 255, 255, 150), font=f_badge, anchor="ra")

    # card
    card = (60, 260, W - 60, H - 380)
    d.rounded_rectangle((card[0] + 8, card[1] + 14, card[2] + 8, card[3] + 14), 48, fill=(0, 0, 0, 90))
    d.rounded_rectangle(card, 48, fill=(255, 255, 255, 22), outline=(*accent, 150), width=3)
    d.rounded_rectangle((card[0], card[1] + 40, card[0] + 14, card[3] - 40), 7, fill=(*accent, 255))

    if scene.kind == "code":
        f = _font(_MONO, 52)
        for dot, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
            d.ellipse((110 + dot * 56, 305, 140 + dot * 56, 335), fill=c)
        lines_ = scene.text.splitlines()[:14]
        y = max(390, (card[1] + card[3]) // 2 - len(lines_) * 78 // 2)
        for n, line in enumerate(lines_, 1):
            d.text((110, y), f"{n:>2}", fill=(110, 120, 140), font=f)
            _code_line(d, (190, y), line[:30], f, accent)
            y += 78
    elif scene.kind == "flow" and len(scene.steps) >= 2:
        f = _font(_BODY, 52)
        f_num = _font(_SANS, 46)
        n_steps = len(scene.steps)
        box_h, gap = 150, 70
        total_h = n_steps * box_h + (n_steps - 1) * gap
        y = (card[1] + card[3]) // 2 - total_h // 2
        for k, step in enumerate(scene.steps):
            x0, x1 = 130, W - 130
            d.rounded_rectangle((x0, y, x1, y + box_h), 36, fill=(255, 255, 255, 34), outline=(*accent, 230), width=3)
            d.ellipse((x0 + 28, y + 35, x0 + 108, y + 115), fill=(*accent, 255))
            d.text((x0 + 68, y + 76), str(k + 1), fill=(12, 12, 24), font=f_num, anchor="mm")
            label_s = textwrap.shorten(step, 34, placeholder="...")
            d.text((x0 + 140, y + 76), label_s, fill=(246, 247, 252), font=f, anchor="lm")
            if k < n_steps - 1:
                cx, ay = W // 2, y + box_h + 8
                d.polygon([(cx - 22, ay), (cx + 22, ay), (cx, ay + gap - 16)], fill=(*accent, 255))
            y += box_h + gap
    else:
        n = len(scene.text)
        size = 84 if n < 60 else 72 if n < 110 else 60
        f = _font(_BODY, size)
        width = {84: 18, 72: 22, 60: 28}[size]
        body = "\n".join(textwrap.wrap(scene.text, width))
        box = d.multiline_textbbox((0, 0), body, font=f, spacing=size // 2)
        y0 = (card[1] + card[3]) // 2 - (box[3] - box[1]) // 2
        d.multiline_text((120, y0), body, fill=(246, 247, 252), font=f, spacing=size // 2)

    # keyword chips
    f_chip = _font(_SANS, 38)
    x = 70
    for k in scene.keywords[:4]:
        label_k = f"#{k}"
        cw = int(d.textlength(label_k, font=f_chip)) + 48
        if x + cw > W - 70:
            break
        d.rounded_rectangle((x, H - 300, x + cw, H - 230), 35, fill=(255, 255, 255, 30), outline=(*accent, 200), width=2)
        d.text((x + 24, H - 290), label_k, fill=(*accent, 255), font=f_chip)
        x += cw + 18

    # progress bar
    d.rounded_rectangle((70, H - 130, W - 70, H - 112), 9, fill=(255, 255, 255, 40))
    d.rounded_rectangle((70, H - 130, 70 + int((W - 140) * (index + 1) / total), H - 112), 9, fill=(*accent, 255))
    img.save(path)


def scene_durations(scenes: list[Scene]) -> list[float]:
    return [max(1.5, estimate_timings(s.text)[-1].end) for s in scenes]


def render(scenes: list[Scene], workdir: str | Path, out_name: str = "out.mp4", audio: bool = False,
           align: bool = False, burn: bool = False):
    """Render scenes to mp4 and captions. With audio=True, narrate offline via Kokoro and
    time scenes and captions to the real clip lengths. align=True refines word times with a local
    recognizer (faster-whisper); burn=True renders captions into the video. Returns (mp4, srt)."""
    from .timing import spoken_form, to_srt

    work = Path(workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    words, durs, wavs, t0 = [], [], [], 0.0
    for i, sc in enumerate(scenes):
        # code scenes are shown on screen, not read aloud verbatim
        spoken = spoken_form("Here is some " + (sc.lang or "code") + "." if sc.kind == "code" else sc.text)
        if audio:
            from . import tts

            wav = work / f"scene{i:03}.wav"
            clip = tts.synth(spoken, wav)
            wavs.append(wav.name)
            dur = max(1.5, clip + 0.35)
            ws = None
            if align:
                from . import align as aligner

                ws = aligner.align(wav, spoken.split(), offset=t0)
            words += ws or tts.calibrated_words(spoken, clip, offset=t0)
        else:
            ws = estimate_timings(spoken, offset=t0)
            dur = max(1.5, ws[-1].end - t0)
            words += ws
        durs.append(dur)
        t0 += dur
    lines = []
    for i, (sc, dur) in enumerate(zip(scenes, durs)):
        name = f"scene{i:03}.png"
        draw_scene(sc, work / name, i, len(scenes))
        lines += [f"file '{name}'", f"duration {dur:.3f}"]
    lines.append(f"file 'scene{len(scenes) - 1:03}.png'")
    (work / "list.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-protocol_whitelist", "file",
           "-f", "concat", "-safe", "0", "-i", str(work / "list.txt")]
    if audio:
        alines = []
        for wav, dur in zip(wavs, durs):
            alines += [f"file '{wav}'", f"duration {dur:.3f}"]
        (work / "alist.txt").write_text("\n".join(alines) + "\n", encoding="utf-8")
        cmd += ["-protocol_whitelist", "file", "-f", "concat", "-safe", "0", "-i", str(work / "alist.txt"),
                "-c:a", "aac", "-shortest"]
    srt = work / "captions.srt"
    srt.write_text(to_srt(words), encoding="utf-8")
    vf = "format=yuv420p"
    if burn:
        # relative name + cwd=work avoids drive-letter escaping and keeps ffmpeg inside the workdir
        style = "FontName=Segoe UI,Bold=1,Fontsize=9,Outline=1,Shadow=0,MarginV=60,Alignment=2"
        vf = f"subtitles=captions.srt:original_size=1080x1920:force_style='{style}',format=yuv420p"
    cmd += ["-vf", vf, "-r", "30", out_name]
    run(cmd, cwd=work)
    return work / out_name, srt
