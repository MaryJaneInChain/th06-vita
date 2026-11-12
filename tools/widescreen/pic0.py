"""The VPK's boot image (sce_sys/pic0.png): the game's loading screen, widened like the game widens it.

  pic0.py DATA_DIR STRIP OUT.png

DATA_DIR holds the player's 紅魔郷IN.DAT (or KOUMAKYO_IN.dat), STRIP is resources/vita/wide/th06logo.png. The build
runs this when TH06_DATA_DIR is set, inside the VitaSDK image, which has no Pillow: standard library only, and
integer maths throughout so the output depends only on the inputs (and zlib).
"""
import math
import re
import sys
import zlib

import pbg3

BAR, FEATHER = 104, 6  # as in WidenWithOutpaintedStrips
SCREEN = (960, 544)

# --- baseline JPEG ---

ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7,
          14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46,
          53, 60, 61, 54, 47, 55, 62, 63]
# IDCT basis scaled by 2^12; rounded once here, so libm differences can't reach the output
IDCT = [[round((math.sqrt(0.5) if u == 0 else 1) * math.cos((2 * x + 1) * u * math.pi / 16) * 2048) for x in range(8)]
        for u in range(8)]


class BitReader:
    def __init__(self, data):
        self.d, self.p, self.acc, self.n = data, 0, 0, 0

    def bits(self, k):
        while self.n < k:
            self.acc = (self.acc << 8) | (self.d[self.p] if self.p < len(self.d) else 0)
            self.p += 1
            self.n += 8
        self.n -= k
        v = self.acc >> self.n
        self.acc &= (1 << self.n) - 1
        return v

    def huff(self, table):
        code = 0
        for length in range(1, 17):
            code = (code << 1) | self.bits(1)
            if (length, code) in table:
                return table[length, code]
        raise ValueError("bad Huffman code")

    def receive(self, t):
        if t == 0:
            return 0
        v = self.bits(t)
        return v if v >= 1 << (t - 1) else v - (1 << t) + 1


def idct(f):
    rows = []
    for v in range(8):
        r = f[v * 8:v * 8 + 8]
        rows.append([sum(r[u] * IDCT[u][x] for u in range(8) if r[u]) for x in range(8)] if any(r) else [0] * 8)
    out = []
    for y in range(8):
        for x in range(8):
            s = sum(rows[v][x] * IDCT[v][y] for v in range(8))
            out.append(min(255, max(0, ((s + (1 << 23)) >> 24) + 128)))
    return out


def decode_jpeg(data):
    """(w, h, RGB bytes) of a baseline, 3-component JPEG like the game's backgrounds."""
    pos, qt, ht, comps, interval = 2, {}, {}, [], 0
    while True:
        marker, length = data[pos + 1], (data[pos + 2] << 8) | data[pos + 3]
        seg, pos = data[pos + 4:pos + 2 + length], pos + 2 + length
        if marker == 0xDB:
            i = 0
            while i < len(seg):
                assert seg[i] >> 4 == 0, "16-bit quantisation table"
                qt[seg[i] & 15] = seg[i + 1:i + 65]
                i += 65
        elif marker == 0xC4:
            i = 0
            while i < len(seg):
                key, counts, i, code, table = (seg[i] >> 4, seg[i] & 15), seg[i + 1:i + 17], i + 17, 0, {}
                for length_, n in enumerate(counts, 1):
                    for _ in range(n):
                        table[length_, code] = seg[i]
                        i, code = i + 1, code + 1
                    code <<= 1
                ht[key] = table
        elif marker == 0xC0:
            h, w = (seg[1] << 8) | seg[2], (seg[3] << 8) | seg[4]
            comps = [(seg[6 + 3 * k], seg[7 + 3 * k] >> 4, seg[7 + 3 * k] & 15, seg[8 + 3 * k]) for k in range(seg[5])]
        elif marker == 0xDD:
            interval = (seg[0] << 8) | seg[1]
        elif 0xC1 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            raise ValueError("not a baseline JPEG")
        elif marker == 0xDA:
            tables = {seg[1 + 2 * k]: (seg[2 + 2 * k] >> 4, seg[2 + 2 * k] & 15) for k in range(seg[0])}
            break
    assert len(comps) == 3 and len(tables) == 3, "expected one interleaved YCbCr scan"

    end = re.compile(rb"\xff[^\x00\xd0-\xd7]").search(data, pos).start()
    segments = [s.replace(b"\xff\x00", b"\xff") for s in re.split(rb"\xff[\xd0-\xd7]", data[pos:end])]
    hmax, vmax = max(c[1] for c in comps), max(c[2] for c in comps)
    mcux, mcuy = -(-w // (8 * hmax)), -(-h // (8 * vmax))
    planes = [bytearray(mcux * hs * 8 * mcuy * vs * 8) for _, hs, vs, _ in comps]
    per_segment = interval or mcux * mcuy
    for mcu in range(mcux * mcuy):
        if mcu % per_segment == 0:
            bits, pred = BitReader(segments[mcu // per_segment]), [0, 0, 0]
        my, mx = divmod(mcu, mcux)
        for ci, (cid, hs, vs, tq) in enumerate(comps):
            dc_table, ac_table = ht[0, tables[cid][0]], ht[1, tables[cid][1]]
            q, stride = qt[tq], mcux * hs * 8
            for by in range(vs):
                for bx in range(hs):
                    f = [0] * 64
                    pred[ci] += bits.receive(bits.huff(dc_table))
                    f[0] = pred[ci] * q[0]
                    k = 1
                    while k < 64:
                        rs = bits.huff(ac_table)
                        if rs == 0:
                            break
                        k += rs >> 4
                        if rs & 15:
                            f[ZIGZAG[k]] = bits.receive(rs & 15) * q[k]
                        k += 1
                    block, x0, y0 = idct(f), (mx * hs + bx) * 8, (my * vs + by) * 8
                    for y in range(8):
                        planes[ci][(y0 + y) * stride + x0:(y0 + y) * stride + x0 + 8] = bytes(block[y * 8:y * 8 + 8])

    rgb = bytearray(w * h * 3)
    strides = [mcux * hs * 8 for _, hs, _, _ in comps]
    for y in range(h):
        rows = [(y * vs // vmax) * s for (_, _, vs, _), s in zip(comps, strides)]
        for x in range(w):
            yy, cb, cr = (planes[i][rows[i] + x * comps[i][1] // hmax] for i in range(3))
            cb, cr = cb - 128, cr - 128
            o = (y * w + x) * 3
            # JFIF YCbCr -> RGB in 16.16 fixed point
            rgb[o] = min(255, max(0, yy + ((91881 * cr + 32768) >> 16)))
            rgb[o + 1] = min(255, max(0, yy + ((-22554 * cb - 46802 * cr + 32768) >> 16)))
            rgb[o + 2] = min(255, max(0, yy + ((116130 * cb + 32768) >> 16)))
    return w, h, rgb


# --- PNG ---


def read_png_rgb(path):
    """(w, h, RGB bytes) of an 8-bit RGB PNG, like the strips."""
    d, pos, idat = open(path, "rb").read(), 8, b""
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    while pos < len(d):
        n, kind = int.from_bytes(d[pos:pos + 4], "big"), d[pos + 4:pos + 8]
        body, pos = d[pos + 8:pos + 8 + n], pos + 12 + n
        if kind == b"IHDR":
            w, h = int.from_bytes(body[0:4], "big"), int.from_bytes(body[4:8], "big")
            assert body[8:10] == b"\x08\x02" and body[12] == 0, "expected 8-bit RGB, not interlaced"
        elif kind == b"IDAT":
            idat += body
    raw, stride = zlib.decompress(idat), w * 3
    out, prev = bytearray(), bytearray(stride)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - 3] if i >= 3 else 0
            b, c = prev[i], prev[i - 3] if i >= 3 else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out += line
        prev = line
    return w, h, out


def png_chunk(kind, body):
    return len(body).to_bytes(4, "big") + kind + body + zlib.crc32(kind + body).to_bytes(4, "big")


def write_png_indexed(path, w, h, palette, indices):
    raw = b"".join(b"\0" + bytes(indices[y * w:(y + 1) * w]) for y in range(h))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", w.to_bytes(4, "big") + h.to_bytes(4, "big") +
                                                          b"\x08\x03\0\0\0") +
                           png_chunk(b"PLTE", bytes(c for p in palette for c in p)) +
                           png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b""))


# --- the image ---


def widen(w, h, orig, strip):
    """What WidenWithOutpaintedStrips builds on the Vita (and widescreen.compose)."""
    side, ww, out = BAR + FEATHER, w + 2 * BAR, bytearray()
    sw = 2 * side
    for y in range(h):
        o, s = orig[y * w * 3:(y + 1) * w * 3], strip[y * sw * 3:(y + 1) * sw * 3]
        row = bytearray(s[:BAR * 3] + o + s[(side + FEATHER) * 3:])
        for i in range(FEATHER):
            a, b, x = i + 1, FEATHER - i, w - 1 - i
            for c in range(3):
                row[(BAR + i) * 3 + c] = (a * o[i * 3 + c] + b * s[(BAR + i) * 3 + c] + (FEATHER + 1) // 2) // (FEATHER + 1)
                row[(BAR + x) * 3 + c] = (a * o[x * 3 + c] + b * s[(side + FEATHER - 1 - i) * 3 + c] +
                                          (FEATHER + 1) // 2) // (FEATHER + 1)
        out += row
    return ww, h, out


def resize(w, h, src, nw, nh):
    """Bilinear, pixel centres aligned, weights in 1/256."""
    def taps(n, nn):
        t = []
        for i in range(nn):
            p = max(0, (2 * i + 1) * n * 128 // nn - 128)  # source position in 1/256
            i0 = min(p >> 8, n - 1)
            t.append((i0, min(i0 + 1, n - 1), p & 255))
        return t
    xs, ys, out = taps(w, nw), taps(h, nh), bytearray(nw * nh * 3)
    for y, (y0, y1, fy) in enumerate(ys):
        r0, r1 = y0 * w * 3, y1 * w * 3
        for x, (x0, x1, fx) in enumerate(xs):
            for c in range(3):
                top = src[r0 + x0 * 3 + c] * (256 - fx) + src[r0 + x1 * 3 + c] * fx
                bot = src[r1 + x0 * 3 + c] * (256 - fx) + src[r1 + x1 * 3 + c] * fx
                out[(y * nw + x) * 3 + c] = (top * (256 - fy) + bot * fy + 32768) >> 16
    return out


def quantize(rgb, n=256):
    """Median cut over 6-bit-per-channel colours: (palette, index per pixel). Vita LiveArea images are 8-bit indexed."""
    hist = {}
    for i in range(0, len(rgb), 3):
        k = (rgb[i] >> 2, rgb[i + 1] >> 2, rgb[i + 2] >> 2)
        e = hist.get(k)
        if e is None:
            hist[k] = e = [0, 0, 0, 0]
        e[0] += 1
        e[1] += rgb[i]
        e[2] += rgb[i + 1]
        e[3] += rgb[i + 2]
    def score(b):
        spread = max(max(k[c] for k in b) - min(k[c] for k in b) for c in range(3))
        return spread * sum(hist[k][0] for k in b)

    boxes = [(score(sorted(hist)), sorted(hist))]
    while len(boxes) < n:
        i = max(range(len(boxes)), key=lambda i: (boxes[i][0], -i))
        s, box = boxes[i]
        if s == 0:
            break
        c = max(range(3), key=lambda c: max(k[c] for k in box) - min(k[c] for k in box))
        box = sorted(box, key=lambda k: (k[c], k))
        half, run, cut = sum(hist[k][0] for k in box) / 2, 0, 1
        for j, k in enumerate(box[:-1]):
            run += hist[k][0]
            if run >= half:
                cut = j + 1
                break
        boxes[i:i + 1] = [(score(box[:cut]), box[:cut]), (score(box[cut:]), box[cut:])]
    palette, index = [], {}
    for _, b in boxes:
        total = [sum(hist[k][j] for k in b) for j in range(4)]
        palette.append(tuple((total[j] + total[0] // 2) // total[0] for j in (1, 2, 3)))
        for k in b:
            index[k] = len(palette) - 1
    return palette, bytes(index[rgb[i] >> 2, rgb[i + 1] >> 2, rgb[i + 2] >> 2] for i in range(0, len(rgb), 3))


def make_pic0(data_dir, strip_path, out_path):
    data, entries = pbg3.open_archive(data_dir, "IN")
    w, h, orig = decode_jpeg(pbg3.read(data, *entries["th06logo.jpg"]))
    sw, sh, strip = read_png_rgb(strip_path)
    if (sw, sh) == (2 * (BAR + FEATHER), h):
        w, h, wide = widen(w, h, orig, strip)
    else:
        sys.exit("%s doesn't fit this th06logo.jpg (%dx%d)" % (strip_path, w, h))
    palette, indices = quantize(resize(w, h, wide, *SCREEN))
    write_png_indexed(out_path, *SCREEN, palette, indices)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    make_pic0(*sys.argv[1:])
