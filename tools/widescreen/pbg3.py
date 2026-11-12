"""Reading files out of the game's PBG3 archives (.DAT), as in src/pbg3. Standard library only."""
import os
import sys


class Bits:
    def __init__(self, data, pos=0):
        self.d, self.pos, self.mask, self.cur = data, pos, 0x80, 0

    def bit(self):
        if self.mask == 0x80:
            self.cur = self.d[self.pos] if self.pos < len(self.d) else 0
            self.pos += 1
        b = self.cur & self.mask
        self.mask = (self.mask >> 1) or 0x80
        return 1 if b else 0

    def int(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v

    def varint(self):
        return self.int(((self.bit() << 1) | self.bit()) * 8 + 8)

    def string(self):
        s = bytearray()
        while (c := self.int(8)) != 0:
            s.append(c)
        return bytes(s)


def entries(data):
    b = Bits(data)
    assert bytes(b.int(8) for _ in range(4)) == b"PBG3", "not a PBG3 archive"
    n, table = b.varint(), b.varint()
    b = Bits(data, table)
    out = {}
    for _ in range(n):
        _, _, _, off, size = (b.varint() for _ in range(5))
        out[b.string().decode("ascii", "replace")] = (off, size)
    return out


def read(data, off, size):
    b, window, head, out = Bits(data, off), bytearray(0x2000), 1, bytearray()
    while len(out) < size:
        if b.bit():
            c = b.int(8)
            out.append(c)
            window[head] = c
            head = (head + 1) & 0x1FFF
        else:
            m = b.int(13)
            if m == 0:
                break
            for i in range(b.int(4) + 3):
                c = window[(m + i) & 0x1FFF]
                out.append(c)
                window[head] = c
                head = (head + 1) & 0x1FFF
    return bytes(out)


def open_archive(data_dir, part):
    """(archive bytes, {name: (offset, size)}) for 紅魔郷<part>.DAT, or KOUMAKYO_<part>.dat for English data."""
    for f in ("紅魔郷%s.DAT" % part, "KOUMAKYO_%s.dat" % part):
        path = os.path.join(data_dir, f)
        if os.path.exists(path):
            data = open(path, "rb").read()
            return data, entries(data)
    sys.exit("no 紅魔郷%s.DAT or KOUMAKYO_%s.dat in %s" % (part, part, data_dir))
