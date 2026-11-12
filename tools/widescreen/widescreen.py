"""Make the outpainted side strips for the Vita's widescreen backgrounds (resources/vita/wide/*.png).

The strips are the only part that ships: the game puts the original background from the player's own data files in
the middle at load time (AnmManager.cpp, WidenWithOutpaintedStrips). Steps:

  widescreen.py extract DATA_DIR WORK/orig          backgrounds out of the player's .DAT files
  widescreen.py canvas  WORK/orig WORK/canvas       1536x1024 canvases, original in the middle, magenta around it
  codex_outpaint.sh     WORK NAME...                an image model fills the magenta -> WORK/codex_out/NAME.png
  widescreen.py strips  WORK/orig WORK/codex_out resources/vita/wide [--preview WORK/preview]

pic0.py makes the VPK's boot image from th06logo's strip at build time (standard library only).

Needs numpy, scipy and Pillow.
"""
import argparse
import io
import os
import tempfile

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, gaussian_filter1d

import pbg3
import pic0

BAR = 104  # PillarboxBarWidth() on the Vita: ceil(117 / (725 / 640))
FEATHER = 6  # must match WidenWithOutpaintedStrips
FALLOFF = 64  # how far into the bar the seam colour match fades out
CANVAS = (1536, 1024)  # the image model's output size

BACKGROUNDS = {
    "IN": ["th06logo"],
    "TL": ["title00", "select00", "music", "result"],
    "ED": ["end00", "end00b"] + ["end%02d" % i for i in range(1, 14)] + ["staff00"],
}


def extract(data_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for part, names in BACKGROUNDS.items():
        data, entries = pbg3.open_archive(data_dir, part)
        for name in names:
            open(os.path.join(out_dir, name + ".jpg"), "wb").write(pbg3.read(data, *entries[name + ".jpg"]))
            print(name)


# --- canvases and strips ---


def layout(w, h):
    """Where the original sits on the canvas: scaled so the widened image just fits."""
    s = min(CANVAS[0] / (w + 2 * BAR), CANVAS[1] / h)
    ow, oh = round(w * s), round(h * s)
    return s, (CANVAS[0] - ow) // 2, (CANVAS[1] - oh) // 2, ow, oh


def canvas(orig_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for f in sorted(os.listdir(orig_dir)):
        im = Image.open(os.path.join(orig_dir, f)).convert("RGB")
        s, ox, oy, ow, oh = layout(*im.size)
        c = Image.new("RGB", CANVAS, (255, 0, 255))
        c.paste(im.resize((ow, oh), Image.LANCZOS), (ox, oy))
        c.save(os.path.join(out_dir, os.path.splitext(f)[0] + ".png"))


def register(gen, orig_up, ox, oy, r=24):
    """Integer shift that best lines the model's redraw of the original up with the original."""
    g, o = gen.mean(2), orig_up.mean(2)
    oh, ow = o.shape
    m = 32
    ref = o[m:oh - m, m:ow - m]

    def err(dx, dy):
        win = g[oy + m + dy:oy + oh - m + dy, ox + m + dx:ox + ow - m + dx]
        return np.abs(win - ref).mean() if win.shape == ref.shape else np.inf

    _, bx, by = min((err(dx, dy), dx, dy) for dy in range(-r, r + 1, 2) for dx in range(-r, r + 1, 2))
    return min((err(dx, dy), dx, dy) for dy in range(by - 1, by + 2) for dx in range(bx - 1, bx + 2))


def strips(orig_path, gen_path):
    """The strip image for one background, plus the shift and the model's error over the original (for review)."""
    orig_im = Image.open(orig_path).convert("RGB")
    orig = np.asarray(orig_im, dtype=np.float32)
    h, w = orig.shape[:2]
    gen_im = Image.open(gen_path).convert("RGB")
    if gen_im.size != CANVAS:
        gen_im = gen_im.resize(CANVAS, Image.LANCZOS)
    s, ox, oy, ow, oh = layout(w, h)
    orig_up = np.asarray(orig_im.resize((ow, oh), Image.LANCZOS), dtype=np.float32)
    e, dx, dy = register(np.asarray(gen_im, dtype=np.float32), orig_up, ox, oy)

    # Crop the widened area back out of the canvas (edge-padded: the shifted box may poke out by a pixel or two)
    pad = 40
    padded = Image.fromarray(np.pad(np.asarray(gen_im), ((pad, pad), (pad, pad), (0, 0)), mode="edge"))
    box = (pad + ox + dx - BAR * s, pad + oy + dy, pad + ox + dx + ow + BAR * s, pad + oy + dy + oh)
    wide = np.asarray(padded.resize((w + 2 * BAR, h), Image.LANCZOS, box=box), dtype=np.float32)

    # Per-row colour offset at each seam, kept through the feather columns and faded out across the bar
    x = np.arange(w + 2 * BAR)
    for seam, edge, weight in (
        (BAR, 0, np.where(x < BAR + FEATHER, np.clip(1 - np.maximum(0, BAR - 1 - x) / FALLOFF, 0, 1), 0)),
        (BAR + w - 1, w - 1,
         np.where(x >= BAR + w - FEATHER, np.clip(1 - np.maximum(0, x - BAR - w) / FALLOFF, 0, 1), 0)),
    ):
        delta = gaussian_filter1d(orig[:, edge, :] - wide[:, seam, :], 6, axis=0)
        wide += delta[:, None, :] * weight[None, :, None]

    wide = np.clip(wide + 0.5, 0, 255).astype(np.uint8)
    return np.concatenate([wide[:, :BAR + FEATHER], wide[:, BAR + w - FEATHER:]], axis=1), (dx, dy, e)


def compose(orig, strip):
    """What WidenWithOutpaintedStrips builds on the Vita, for previews."""
    h, w = orig.shape[:2]
    side = BAR + FEATHER
    o, s = orig.astype(np.int32), strip.astype(np.int32)
    out = np.concatenate([s[:, :BAR], o, s[:, side + FEATHER:]], axis=1)
    for i in range(FEATHER):
        a, b = i + 1, FEATHER - i
        out[:, BAR + i] = (a * o[:, i] + b * s[:, BAR + i] + (FEATHER + 1) // 2) // (FEATHER + 1)
        x = w - 1 - i
        out[:, BAR + x] = (a * o[:, x] + b * s[:, side + FEATHER - 1 - i] + (FEATHER + 1) // 2) // (FEATHER + 1)
    return out.astype(np.uint8)


def make_strips(orig_dir, gen_dir, out_dir, preview_dir):
    os.makedirs(out_dir, exist_ok=True)
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
    for f in sorted(os.listdir(gen_dir)):
        name = os.path.splitext(f)[0]
        orig_path = os.path.join(orig_dir, name + ".jpg")
        strip, (dx, dy, e) = strips(orig_path, os.path.join(gen_dir, f))
        Image.fromarray(strip).save(os.path.join(out_dir, name + ".png"), optimize=True)
        if preview_dir:
            orig = np.asarray(Image.open(orig_path).convert("RGB"))
            Image.fromarray(compose(orig, strip)).save(os.path.join(preview_dir, name + ".png"))
        print("%s: shift (%d, %d), model vs original mean abs diff %.1f" % (name, dx, dy, e))


def selftest():
    """compose() puts the original back untouched outside the feather columns and the strips in the bars."""
    rng = np.random.default_rng(0)
    orig = rng.integers(0, 256, (8, 40, 3), dtype=np.uint8)
    strip = rng.integers(0, 256, (8, 2 * (BAR + FEATHER), 3), dtype=np.uint8)
    out = compose(orig, strip)
    assert out.shape == (8, 40 + 2 * BAR, 3)
    assert (out[:, BAR + FEATHER:BAR + 40 - FEATHER] == orig[:, FEATHER:40 - FEATHER]).all()
    assert (out[:, :BAR] == strip[:, :BAR]).all() and (out[:, BAR + 40:] == strip[:, BAR + 2 * FEATHER:]).all()

    # pic0.py's stand-ins for Pillow: the same widening, and decoders that agree with Pillow's
    o, s = orig.tobytes(), strip.tobytes()
    assert bytes(pic0.widen(40, 8, o, s)[2]) == out.tobytes()
    im = Image.fromarray(gaussian_filter(rng.integers(0, 256, (48, 64, 3)).astype(float), (3, 3, 0)).astype(np.uint8))
    for subsampling in (0, 2):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90, subsampling=subsampling)
        w, h, rgb = pic0.decode_jpeg(buf.getvalue())
        ref = np.asarray(Image.open(buf).convert("RGB")).astype(int)
        mine = np.frombuffer(bytes(rgb), np.uint8).reshape(h, w, 3).astype(int)
        # 4:2:0 chroma is upsampled nearest-neighbour, not libjpeg's smoothed way; the game's JPEGs are 4:4:4
        assert np.abs(mine - ref).mean() < (0.25 if subsampling == 0 else 1.5), subsampling
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        im.save(f.name)
        assert bytes(pic0.read_png_rgb(f.name)[2]) == im.tobytes()
    print("selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("extract"); a.add_argument("data_dir"); a.add_argument("out_dir")
    a = sub.add_parser("canvas"); a.add_argument("orig_dir"); a.add_argument("out_dir")
    a = sub.add_parser("strips")
    a.add_argument("orig_dir"); a.add_argument("gen_dir"); a.add_argument("out_dir"); a.add_argument("--preview")
    sub.add_parser("selftest")
    args = p.parse_args()
    if args.cmd == "extract":
        extract(args.data_dir, args.out_dir)
    elif args.cmd == "canvas":
        canvas(args.orig_dir, args.out_dir)
    elif args.cmd == "strips":
        make_strips(args.orig_dir, args.gen_dir, args.out_dir, args.preview)
    else:
        selftest()
